// SPDX-License-Identifier: GPL-2.0-or-later
// Recursive batched four-step FFT ("rec4").
//
// fft_batched(n, Bt): Bt interleaved transforms of length n, element (b, i) at b + Bt*i.
// If the working set n*Bt fits a cache budget -> Stockham leaf.  Otherwise n = N1*N2 and
//   Step A  for each strip of Bc columns: gather N1 x (Bc*Bt) block (contiguous segments),
//           batched length-N1 FFT (recursive), multiply twiddles w_n^{i2 k1}, scatter to W.
//   Step B  for each strip of G rows: gather G rows into interleaved layout (an in-cache
//           transpose), batched length-N2 FFT (recursive), write strip of out viewed N2 x N1.
// Ideas exercised:
//   I1/I14  address interchanges (transposes) are never separate passes; they are fused into the
//           gather/scatter of the strips that are anyway loaded into cache.
//   I3      every sub-transform is executed as one wide batched call (Bc*Bt or G*Bt lanes),
//           never as many narrow ones (Bc = G = 1 recovers the unbatched variant).
//   I4/I5   N1 x N2 split (balanced or "small inner dimension"), recursion = multi-level tensor.
//   I9      option to leave the output in transposed (k1-major) order for convolution use.
//   I11     scratch reuse: per-level buffers are allocated once and reused by all strips.
#pragma once
#ifdef _OPENMP
#include <omp.h>
#endif
#include "stockham.h"

typedef struct rec4_node rec4_node;
struct rec4_node {
    int64_t n, Bt;
    int leaf;
    sh_plan *sp;                 // leaf
    int64_t N1, N2, Bc, G;       // inner
    rec4_node *colc, *rowc;      // children: (N1, Bc*Bt) and (N2, G*Bt)
    double *WJ;                  // [k1][j] w_n^{j k1}, j < Bc
    double *Tlo, *Thi; int64_t L1;  // two-level table for w_n^{e}
    double *buf, *buf2, *W;      // strip buffers and intermediate full array
    int64_t ws;                  // W row stride in complex (N2*Bt + pad): avoids 2^k-stride conflicts
    double *trow;                // twiddle row scratch (Bc complex)
    int pf;                      // software-prefetch the next strip
    int64_t stage;               // staged columns per super-strip (top level only), 0 = off
    double *stg, *stg2;          // staging buffer(s) N1 x stage x Bt complex (stg2: second buffer, threaded)
    int only;                    // diagnostics: run only step A (1) or B (2)
    int sep;                     // top level: separate transpose passes instead of fused gathers/scatters
    double *T1, *T2;             // sep: two full-size scratch arrays for the explicit transposes
    int ceil;                    // diagnostics (top level): see rec4_params.ceil
};

typedef struct {
    int64_t budget;   // max complex elements for a Stockham leaf (n*Bt)
    int64_t Bc, G;    // strip widths (in units of columns/rows); 0 = auto
    int split;        // 0 = balanced (sqrt), 1 = small inner N1 (= leaf-sized), 2 = large inner
    int rmax, mode;   // Stockham leaf parameters
    int nt;           // non-temporal stores on top-level output writes
    int pf;           // prefetch next strip at top level (hurts; kept for the ablation).  Prefetching the
                      // next strip spread through the strip's FFT was also tried: gather time unchanged,
                      // FFT 7-20 ms slower at 2^24 (the strided gather is limited by L2 set aliasing, not latency)
    int64_t N1top;    // force top-level N1 (0 = use split policy)
    int64_t pad;      // complex padding per row of intermediate W
    int64_t stage;    // top level, step A: stage `stage` columns per input row (>= 4 KB) into an L3-resident
                      // buffer with long contiguous reads, then cut the Bc-wide strips from it (0 = off).
                      // Strided 128-byte gathers alias in the L2 sets under huge pages (~10 GB/s); 4 KB runs stream at 16-18 GB/s.
    int only;         // diagnostics (top level): 1 = run step A only, 2 = step B only (output invalid)
    int threads;      // > 1: OpenMP top level (needs leaf children; otherwise runs single-threaded)
    int stage2;       // threaded + stage: double-buffered (pipelined) staging
    int sep;          // top level (ablation "transposition: separate"): the three address interchanges are
                      // explicit blocked transpose passes over full arrays (six-step structure), and both FFT
                      // passes read and write contiguous rows; the kernels, strips and twiddles are unchanged
    int ceil;         // diagnostics (top level, output invalid): ceilings that keep the exact access pattern
                      // 1 = no sub-FFTs (movement + twiddle multiplies), 2 = no sub-FFTs and no twiddles (pure
                      // movement), 3 = sub-FFTs only, on cache-resident strip buffers (no gathers / scatters),
                      // 4 = the two-pass ideal at streaming speed: two sequential NT copy passes in -> W -> out
} rec4_params;

static void rec4_tw(const rec4_node *N, int64_t e, double *re, double *im) {
    // w_n^e = Thi[e / L1] * Tlo[e % L1]
    int64_t hi = e / N->L1, lo = e - hi * N->L1;
    double ar = N->Thi[2 * hi], ai = N->Thi[2 * hi + 1], br = N->Tlo[2 * lo], bi = N->Tlo[2 * lo + 1];
    *re = ar * br - ai * bi; *im = ar * bi + ai * br;
}

static int64_t rec4_choose_n1(int64_t n, int64_t Bt, const rec4_params *p) {
    // candidates: divisors of n; prefer powers of two / smooth.
    int64_t best = 0; double bestscore = 1e300;
    for (int64_t d = 2; d * 2 <= n; d++) {
        if (n % d) continue;
        int rad[SH_MAXPASS];
        if (!sh_factor(d, 16, rad) || !sh_factor(n / d, 16, rad)) continue;
        double score;
        double ld = log((double)d), ln = log((double)n);
        if (p->split == 0) score = fabs(ld - ln / 2);
        else if (p->split == 1) {
            // inner dimension as large as fits the leaf budget together with a 8-wide strip
            int64_t target = p->budget / (8 * Bt); if (target < 2) target = 2;
            score = fabs(ld - log((double)target)) + (d > target ? 5 : 0);
        } else score = fabs(ld - 2 * ln / 3);
        // both factors should hold full strips (8 complex = 128 B per row segment for Bt = 1): an odd N1 forces
        // G = 1 in step B, i.e. 16-byte non-temporal stores scattered with stride N1 (10^7 = 3125 x 3200 ran 1.7x
        // slower on the i7 and 5.8x slower on a Xeon Gold 6234 than 5000 x 2000)
        const int64_t w = Bt < 8 ? 8 / Bt : 1;
        if (w > 1 && (d % w || (n / d) % w)) score += 1.0;
        if (score < bestscore) { bestscore = score; best = d; }
    }
    return best;
}

static rec4_node *rec4_build(int64_t n, int64_t Bt, const rec4_params *p, int top) {
    rec4_node *N = (rec4_node *)calloc(1, sizeof(rec4_node));
    N->n = n; N->Bt = Bt;
    int64_t N1 = (n * Bt <= p->budget || n < 64) ? 0 : rec4_choose_n1(n, Bt, p);
    if (top && N1 && p->N1top > 1 && n % p->N1top == 0) N1 = p->N1top;
    if (N1 == 0) {
        N->leaf = 1;
        N->sp = sh_plan_create(n, Bt, p->rmax, p->mode);
        if (!N->sp) { free(N); return NULL; }
        return N;
    }
    int64_t N2 = n / N1;
    N->N1 = N1; N->N2 = N2;
    // strip widths: want Bc*Bt complex per row segment >= 8 (128 bytes) unless forced
    int64_t Bc = p->Bc, G = p->G;
    if (Bc <= 0) { Bc = 8 / Bt; if (Bc < 1) Bc = 1; }
    if (G <= 0) { G = 8 / Bt; if (G < 1) G = 1; }
    while (Bc > 1 && (N2 % Bc || (Bc * Bt) % 2)) Bc--;  // divide N2, keep lanes even
    while (G > 1 && (N1 % G || (G * Bt) % 2)) G--;
    N->Bc = Bc; N->G = G;
    N->colc = rec4_build(N1, Bc * Bt, p, 0);
    N->rowc = rec4_build(N2, G * Bt, p, 0);
    N->WJ = (double *)xmalloc(sizeof(double) * 2 * N1 * Bc);
    for (int64_t k1 = 0; k1 < N1; k1++)
        for (int64_t j = 0; j < Bc; j++) twiddle(j * k1, n, N->WJ + 2 * (k1 * Bc + j), N->WJ + 2 * (k1 * Bc + j) + 1);
    int64_t L1 = 1; while (L1 * L1 < n) L1++;
    N->L1 = L1;
    int64_t nh = (n + L1 - 1) / L1 + 1;
    N->Tlo = (double *)xmalloc(sizeof(double) * 2 * L1);
    N->Thi = (double *)xmalloc(sizeof(double) * 2 * nh);
    for (int64_t i = 0; i < L1; i++) twiddle(i, n, N->Tlo + 2 * i, N->Tlo + 2 * i + 1);
    for (int64_t i = 0; i < nh; i++) twiddle(i * L1, n, N->Thi + 2 * i, N->Thi + 2 * i + 1);
    int64_t bsz = N1 * Bc * Bt; if (N2 * G * Bt > bsz) bsz = N2 * G * Bt;
    N->buf = (double *)xmalloc(sizeof(double) * 2 * bsz);
    N->buf2 = (double *)xmalloc(sizeof(double) * 2 * bsz);
    N->ws = N2 * Bt + p->pad;
    N->W = (double *)xmalloc(sizeof(double) * 2 * N1 * N->ws);
    N->trow = (double *)xmalloc(sizeof(double) * 2 * (Bc + 2));
    N->pf = top ? p->pf : 0;
    if (top && p->sep && Bt == 1) {
        N->sep = 1;
        N->T1 = (double *)xmalloc(sizeof(double) * 2 * n);
        N->T2 = (double *)xmalloc(sizeof(double) * 2 * n);
    }
    N->only = top ? p->only : 0;
    N->ceil = top ? p->ceil : 0;
    if (N->ceil == 3)   // compute-only ceiling: the strip buffers hold fixed, normal (non-denormal) data
        for (int64_t i = 0; i < 2 * bsz; i++) N->buf[i] = N->buf2[i] = 1e-3 * (double)((i * 7919) % 1000 + 1);
    if (N->only == 2) memset(N->W, 0x3f, sizeof(double) * 2 * N1 * N->ws);  // B-only: make W real memory
    if (top && p->stage > Bc && N2 % p->stage == 0 && p->stage % Bc == 0) {
        N->stage = p->stage;
        N->stg = (double *)xmalloc(sizeof(double) * 2 * N1 * (N->stage * Bt + 4));
    }
    return N;
}

static void rec4_free(rec4_node *N) {
    if (!N) return;
    if (N->leaf) sh_plan_free(N->sp);
    else {
        rec4_free(N->colc); rec4_free(N->rowc);
        free(N->T1); free(N->T2);
        free(N->WJ); free(N->Tlo); free(N->Thi); free(N->buf); free(N->buf2); free(N->W); free(N->trow); free(N->stg);
        free(N->stg2);
    }
    free(N);
}

static void rec4_exec(const rec4_node *N, const double *in, double *out, int nt);
#ifdef REC4_PROF
static double rp_t[6];
#define RP_MARK(i) do { double _t = now_sec(); rp_t[i] += _t - rp_last; rp_last = _t; } while (0)
#else
#define RP_MARK(i) do {} while (0)
#endif

// run child transform on buf (in) -> returns pointer to result (buf or buf2)
static inline const double *rec4_child(const rec4_node *C, double *buf, double *buf2) {
    if (C->leaf) return sh_exec(C->sp, buf, buf2);
    rec4_exec(C, buf, buf2, 0);
    return buf2;
}

static inline void copy_seg(double *restrict d, const double *restrict s, int64_t ncplx, int nt) {
    // segments shorter than a cache line: ordinary stores.  Non-temporal stores that fill only part of a line, scattered
    // with a large stride (unbatched strips, e.g. an odd N1 forcing G = 1), are slow and erratic: at 10^7 with
    // N1 = 3125 the output scatter took 739-945 ms on a Xeon Gold 6234 and 47-249 ms on the i7, against 188 / 46 ms
    // with ordinary stores
    if (nt && ncplx * 16 < 64) { memcpy(d, s, sizeof(double) * 2 * ncplx); return; }
    if (nt && ((uintptr_t)d % 32 == 0) && (ncplx % 2 == 0)) {
        for (int64_t i = 0; i < ncplx; i += 2) _mm256_stream_pd(d + 2 * i, VLOADU(s + 2 * i));
    } else if (nt && ((uintptr_t)d % 16 == 0)) {
        // short or odd segments (unbatched strips): 16-byte non-temporal stores, i.e. partial cache lines
        for (int64_t i = 0; i < ncplx; i++) _mm_stream_pd(d + 2 * i, _mm_loadu_pd(s + 2 * i));
    } else memcpy(d, s, sizeof(double) * 2 * ncplx);
}

// ---- separate-transpose variant (ablation): explicit passes over full arrays ----
// out[c * ldo + r] = in[r * ldi + c] for an R x C complex matrix, 16 x 16 blocks, 2 x 2 register transposes;
// non-temporal 32-byte stores when nt
static void rec4_transpose(const double *in, int64_t ldi, double *out, int64_t ldo, int64_t R, int64_t C, int nt) {
    const int64_t T = 16;
    for (int64_t r0 = 0; r0 < R; r0 += T)
        for (int64_t c0 = 0; c0 < C; c0 += T) {
            const int64_t r1 = r0 + T < R ? r0 + T : R, c1 = c0 + T < C ? c0 + T : C;
            if (r1 - r0 == T && c1 - c0 == T) {
                // four source rows at a time: each destination row receives 4 complex = one full 64-byte line,
                // written by two back-to-back 32-byte stores (full-line write combining for NT stores)
                for (int64_t r = r0; r < r1; r += 4)
                    for (int64_t c = c0; c < c1; c += 2) {
                        V a0 = VLOADU(in + 2 * (r * ldi + c)), a1 = VLOADU(in + 2 * ((r + 1) * ldi + c));
                        V a2 = VLOADU(in + 2 * ((r + 2) * ldi + c)), a3 = VLOADU(in + 2 * ((r + 3) * ldi + c));
                        V lo01 = _mm256_permute2f128_pd(a0, a1, 0x20), hi01 = _mm256_permute2f128_pd(a0, a1, 0x31);
                        V lo23 = _mm256_permute2f128_pd(a2, a3, 0x20), hi23 = _mm256_permute2f128_pd(a2, a3, 0x31);
                        double *d0 = out + 2 * (c * ldo + r), *d1 = out + 2 * ((c + 1) * ldo + r);
                        if (nt && (uintptr_t)d0 % 32 == 0 && (uintptr_t)d1 % 32 == 0) {
                            _mm256_stream_pd(d0, lo01); _mm256_stream_pd(d0 + 4, lo23);
                            _mm256_stream_pd(d1, hi01); _mm256_stream_pd(d1 + 4, hi23);
                        } else { VSTOREU(d0, lo01); VSTOREU(d0 + 4, lo23); VSTOREU(d1, hi01); VSTOREU(d1 + 4, hi23); }
                    }
            } else
                for (int64_t r = r0; r < r1; r++)
                    for (int64_t c = c0; c < c1; c++) {
                        out[2 * (c * ldo + r)] = in[2 * (r * ldi + c)];
                        out[2 * (c * ldo + r) + 1] = in[2 * (r * ldi + c) + 1];
                    }
        }
    if (nt) _mm_sfence();
}

// buf[i * R + j] = src[(r0 + j) * ld + i]: R contiguous rows of length L interleaved for a batched kernel
static inline void rec4_interleave(const double *src, int64_t ld, int64_t r0, int64_t R, int64_t L, double *buf) {
    if (R == 1) { memcpy(buf, src + 2 * r0 * ld, sizeof(double) * 2 * L); return; }
    for (int64_t j = 0; j + 1 < R; j += 2) {
        const double *a = src + 2 * (r0 + j) * ld, *b = a + 2 * ld;
        for (int64_t i = 0; i + 1 < L; i += 2) {
            V x = VLOADU(a + 2 * i), y = VLOADU(b + 2 * i);
            VSTOREU(buf + 2 * (i * R + j), _mm256_permute2f128_pd(x, y, 0x20));
            VSTOREU(buf + 2 * ((i + 1) * R + j), _mm256_permute2f128_pd(x, y, 0x31));
        }
    }
    if (R % 2) {
        const double *a = src + 2 * (r0 + R - 1) * ld;
        for (int64_t i = 0; i < L; i++) { buf[2 * (i * R + R - 1)] = a[2 * i]; buf[2 * (i * R + R - 1) + 1] = a[2 * i + 1]; }
    }
}

// dst[(r0 + j) * ld + i] = res[i * R + j]: the inverse, writing R contiguous rows (non-temporal when nt)
static inline void rec4_deinterleave(const double *res, int64_t R, int64_t L, double *dst, int64_t ld, int64_t r0, int nt) {
    for (int64_t j = 0; j < R; j++) {
        double *d = dst + 2 * (r0 + j) * ld;
        int64_t i = 0;
        for (; i + 1 < L; i += 2) {
            V v = _mm256_set_m128d(_mm_loadu_pd(res + 2 * ((i + 1) * R + j)), _mm_loadu_pd(res + 2 * (i * R + j)));
            if (nt && (uintptr_t)(d + 2 * i) % 32 == 0) _mm256_stream_pd(d + 2 * i, v); else VSTOREU(d + 2 * i, v);
        }
        for (; i < L; i++) { d[2 * i] = res[2 * (i * R + j)]; d[2 * i + 1] = res[2 * (i * R + j) + 1]; }
    }
}

// ---- per-strip building blocks (shared by the serial and the multithreaded top level) ----

// Step A, after the column FFT of strip c0 (result `res`, N1 x seg): multiply by the twiddles w_n^{k1 (c0 + j)}
// and scatter row k1 into the intermediate W (non-temporal when nt).  trow: Bc complex scratch.
static inline void rec4_twiddle_scatter(const rec4_node *N, const double *res, int64_t c0, double *trow, int nt) {
    const int64_t n = N->n, Bt = N->Bt, N1 = N->N1, Bc = N->Bc, seg = Bc * Bt;
    double *W = N->W;
    // twiddle exponent e = c0*k1 mod n, kept as (hi, lo) with e = hi*L1 + lo and advanced incrementally
    // (no integer division in the row loop)
    const int64_t L1 = N->L1, dhi = c0 / L1, dlo = c0 - dhi * L1;
    int64_t hi = 0, lo = 0;
    for (int64_t k1 = 0; k1 < N1; k1++) {
        double br, bi;
        {
            const double ar = N->Thi[2 * hi], ai = N->Thi[2 * hi + 1], cr = N->Tlo[2 * lo], ci = N->Tlo[2 * lo + 1];
            br = ar * cr - ai * ci; bi = ar * ci + ai * cr;
            hi += dhi; lo += dlo;
            if (lo >= L1) { lo -= L1; hi++; }
            if (hi * L1 + lo >= n) { int64_t e = hi * L1 + lo - n; hi = e / L1; lo = e - hi * L1; }  // rare wrap
        }
        const double *wj = N->WJ + 2 * k1 * Bc;
        double *tr = trow;
        for (int64_t j = 0; j < Bc; j++) {
            tr[2 * j] = br * wj[2 * j] - bi * wj[2 * j + 1];
            tr[2 * j + 1] = br * wj[2 * j + 1] + bi * wj[2 * j];
        }
        const double *src = res + 2 * k1 * seg;
        double *dst = W + 2 * (k1 * N->ws + Bt * c0);
        if (Bt == 1) {
            int64_t j = 0;
            if (nt && ((uintptr_t)dst % 32 == 0))
                for (; j + 1 < Bc; j += 2) _mm256_stream_pd(dst + 2 * j, vcmul(VLOADU(src + 2 * j), VLOADU(tr + 2 * j)));
            for (; j + 1 < Bc; j += 2) VSTOREU(dst + 2 * j, vcmul(VLOADU(src + 2 * j), VLOADU(tr + 2 * j)));
            if (nt && Bc * 16 >= 64 && ((uintptr_t)dst % 16 == 0))   // odd tail of a wide strip: 16-byte NT stores
                for (; j < Bc; j++) {
                    double xr = src[2 * j], xi = src[2 * j + 1];
                    _mm_stream_pd(dst + 2 * j, _mm_set_pd(xr * tr[2 * j + 1] + xi * tr[2 * j], xr * tr[2 * j] - xi * tr[2 * j + 1]));
                }
            for (; j < Bc; j++) {
                double xr = src[2 * j], xi = src[2 * j + 1];
                dst[2 * j] = xr * tr[2 * j] - xi * tr[2 * j + 1];
                dst[2 * j + 1] = xr * tr[2 * j + 1] + xi * tr[2 * j];
            }
        } else {
            for (int64_t j = 0; j < Bc; j++) {
                V t = vbroadcast_c(tr + 2 * j);
                for (int64_t b = 0; b < Bt; b += 2)
                    VSTOREU(dst + 2 * (j * Bt + b), vcmul(VLOADU(src + 2 * (j * Bt + b)), t));
            }
        }
    }
}

// Step B gather of rows r0..r0+G-1 of W into buf (interleaved, in-cache transpose):
// buf[(i2*G + g)*Bt + b] = W[b + Bt*((r0+g)*N2 + i2)]
static inline void rec4_gather_rows(const rec4_node *N, int64_t r0, double *buf) {
    const int64_t Bt = N->Bt, N2 = N->N2, G = N->G, gs = G * Bt;
    const double *W = N->W;
    for (int64_t g = 0; g < G; g++) {
        const double *row = W + 2 * ((r0 + g) * N->ws);
        double *d = buf + 2 * g * Bt;
        if (Bt == 1 && G % 2 == 0 && N2 % 2 == 0) {
            if (g % 2) continue;  // rows handled in pairs: 2x2 complex transposes in registers
            const double *row1 = row + 2 * N->ws;
            for (int64_t i2 = 0; i2 < N2; i2 += 2) {
                V a = VLOADU(row + 2 * i2), b = VLOADU(row1 + 2 * i2);
                VSTOREU(d + 2 * i2 * gs, _mm256_permute2f128_pd(a, b, 0x20));
                VSTOREU(d + 2 * (i2 + 1) * gs, _mm256_permute2f128_pd(a, b, 0x31));
            }
        } else if (Bt == 1) {
            for (int64_t i2 = 0; i2 < N2; i2++) { d[2 * i2 * gs] = row[2 * i2]; d[2 * i2 * gs + 1] = row[2 * i2 + 1]; }
        } else {
            for (int64_t i2 = 0; i2 < N2; i2++) memcpy(d + 2 * i2 * gs, row + 2 * Bt * i2, sizeof(double) * 2 * Bt);
        }
    }
}

// Step B output: out viewed as N2 x N1 (times Bt): out[b + Bt*(k2*N1 + r0 + g)] = res[(k2*G+g)*Bt + b]
static inline void rec4_scatter_out(const rec4_node *N, const double *res, int64_t r0, double *out, int nt) {
    const int64_t Bt = N->Bt, N1 = N->N1, N2 = N->N2, gs = N->G * Bt;
    for (int64_t k2 = 0; k2 < N2; k2++) copy_seg(out + 2 * Bt * (k2 * N1 + r0), res + 2 * k2 * gs, gs, nt);
}

// Separate-transpose top level (Bt = 1): five passes over full arrays instead of two,
//   T1 = in^T [i2][i1];  A: rows of T1 (Bc at a time) -> FFT_N1, twiddle -> T2 [i2][k1];  W = T2^T [k1][i2];
//   B: rows of W (G at a time) -> FFT_N2 -> T1 [k1][k2];  out = T1^T [k2][k1].
static void rec4_exec_sep(const rec4_node *N, const double *in, double *out, int nt) {
    const int64_t N1 = N->N1, N2 = N->N2, Bc = N->Bc, G = N->G;
    double *T1 = N->T1, *T2 = N->T2;
    rec4_transpose(in, N2, T1, N1, N1, N2, nt);
    for (int64_t c0 = 0; c0 < N2; c0 += Bc) {
        rec4_interleave(T1, N1, c0, Bc, N1, N->buf);
        double *res = (double *)rec4_child(N->colc, N->buf, N->buf2);
        // twiddles w_n^{k1 (c0 + j)} exactly as in rec4_twiddle_scatter (incremental base w_n^{k1 c0} x WJ)
        const int64_t L1 = N->L1, dhi = c0 / L1, dlo = c0 - dhi * L1;
        int64_t hi = 0, lo = 0;
        for (int64_t k1 = 0; k1 < N1; k1++) {
            const double ar = N->Thi[2 * hi], ai = N->Thi[2 * hi + 1], cr = N->Tlo[2 * lo], ci = N->Tlo[2 * lo + 1];
            const double br = ar * cr - ai * ci, bi = ar * ci + ai * cr;
            hi += dhi; lo += dlo;
            if (lo >= L1) { lo -= L1; hi++; }
            if (hi * L1 + lo >= N->n) { int64_t e = hi * L1 + lo - N->n; hi = e / L1; lo = e - hi * L1; }
            const double *wj = N->WJ + 2 * k1 * Bc;
            double *x = res + 2 * k1 * Bc;
            for (int64_t j = 0; j < Bc; j++) {
                const double wr = br * wj[2 * j] - bi * wj[2 * j + 1], wi = br * wj[2 * j + 1] + bi * wj[2 * j];
                const double xr = x[2 * j], xi = x[2 * j + 1];
                x[2 * j] = xr * wr - xi * wi; x[2 * j + 1] = xr * wi + xi * wr;
            }
        }
        rec4_deinterleave(res, Bc, N1, T2, N1, c0, nt);
    }
    if (nt) _mm_sfence();
    rec4_transpose(T2, N1, N->W, N->ws, N2, N1, nt);
    for (int64_t r0 = 0; r0 < N1; r0 += G) {
        rec4_interleave(N->W, N->ws, r0, G, N2, N->buf);
        const double *res = rec4_child(N->rowc, N->buf, N->buf2);
        rec4_deinterleave(res, G, N2, T1, N2, r0, nt);
    }
    if (nt) _mm_sfence();
    rec4_transpose(T1, N2, out, N1, N1, N2, nt);
}

// ceil = 2: the twiddle scatter without the multiplies (same rows, same NT stores)
static inline void rec4_copy_scatter(const rec4_node *N, const double *res, int64_t c0, int nt) {
    const int64_t seg = N->Bc * N->Bt;
    for (int64_t k1 = 0; k1 < N->N1; k1++) copy_seg(N->W + 2 * (k1 * N->ws + N->Bt * c0), res + 2 * k1 * seg, seg, nt);
}

static void rec4_exec(const rec4_node *N, const double *in, double *out, int nt) {
    if (N->leaf) { fprintf(stderr, "rec4_exec on leaf\n"); exit(1); }
    if (N->sep) { rec4_exec_sep(N, in, out, nt); return; }
    if (N->ceil == 4) {   // two sequential passes (4 S) at streaming speed, NT stores
        const int64_t n = N->n * N->Bt;
        copy_seg(N->W, in, n, nt); if (nt) _mm_sfence();
        copy_seg(out, N->W, n, nt); if (nt) _mm_sfence();
        return;
    }
    const int cl = N->ceil;
    const int64_t Bt = N->Bt, N1 = N->N1, N2 = N->N2, Bc = N->Bc, G = N->G;
#ifdef REC4_PROF
    double rp_last = now_sec();
#endif
    // ---- Step A: columns ----
    const int64_t seg = Bc * Bt;  // complex per row segment
    for (int64_t c0 = 0; c0 < (N->only == 2 ? 0 : N2); c0 += Bc) {
        if (cl == 3) {
        } else if (N->stage) {
            // staged gather: at the start of each super-strip copy N1 rows x stage columns with long runs,
            // then cut this strip from the (cache-resident) staging buffer
            const int64_t S = N->stage, cs = c0 - c0 % S, rowc = S * Bt, rs = rowc + 4;  // +64 B: no 2^k stride
            if (c0 == cs)
                for (int64_t i1 = 0; i1 < N1; i1++)
                    memcpy(N->stg + 2 * i1 * rs, in + 2 * Bt * (i1 * N2 + cs), sizeof(double) * 2 * rowc);
            const double *sb = N->stg + 2 * Bt * (c0 - cs);
            for (int64_t i1 = 0; i1 < N1; i1++) memcpy(N->buf + 2 * i1 * seg, sb + 2 * i1 * rs, sizeof(double) * 2 * seg);
        } else if (N->pf == 1 && c0 + Bc < N2) {
            // gather this strip and prefetch the next one; the prefetches complete during this strip's FFT
            const int64_t lines = (seg * 16 + 63) / 64;
            for (int64_t i1 = 0; i1 < N1; i1++) {
                const char *nx = (const char *)(in + 2 * Bt * (i1 * N2 + c0 + Bc));
                for (int64_t l = 0; l < lines; l++) _mm_prefetch(nx + 64 * l, _MM_HINT_T1);
                memcpy(N->buf + 2 * i1 * seg, in + 2 * Bt * (i1 * N2 + c0), sizeof(double) * 2 * seg);
            }
        } else
            for (int64_t i1 = 0; i1 < N1; i1++) memcpy(N->buf + 2 * i1 * seg, in + 2 * Bt * (i1 * N2 + c0), sizeof(double) * 2 * seg);
        RP_MARK(0);
        const double *res = (cl == 1 || cl == 2) ? N->buf : rec4_child(N->colc, N->buf, N->buf2);
        RP_MARK(1);
        if (cl == 2) rec4_copy_scatter(N, res, c0, nt);
        else if (cl != 3) rec4_twiddle_scatter(N, res, c0, N->trow, nt);
        RP_MARK(2);
    }
    if (nt) _mm_sfence();
    // ---- Step B: rows (with in-cache transpose) ----
    for (int64_t r0 = 0; r0 < (N->only == 1 ? 0 : N1); r0 += G) {
        if (N->pf == 1 && r0 + G < N1) {
            for (int64_t g = 0; g < G; g++) {
                const char *nx = (const char *)(N->W + 2 * ((r0 + G + g) * N->ws));
                for (int64_t off = 0; off < N2 * Bt * 16; off += 64) _mm_prefetch(nx + off, _MM_HINT_T1);
            }
        }
        if (cl != 3) rec4_gather_rows(N, r0, N->buf);
        RP_MARK(3);
        const double *res = (cl == 1 || cl == 2) ? N->buf : rec4_child(N->rowc, N->buf, N->buf2);
        RP_MARK(4);
        if (cl != 3) rec4_scatter_out(N, res, r0, out, nt);
        RP_MARK(5);
    }
    if (nt) _mm_sfence();
}

// ---- multithreaded top level (OpenMP) ----
// Strips of step A and row groups of step B are independent; each thread has its own strip buffers, while
// the in-cache child plans (Stockham leaves, read-only) and the twiddle tables are shared.  With staging,
// the threads first copy one staged block together (rows split across threads: long sequential runs), then
// split its Bc-wide strips: one 8 MB staging buffer serves all threads (cf. REPORT §11, where per-process
// staging buffers overflowed the shared L3).
typedef struct { double *buf, *buf2, *trow; } rec4_tbuf;

static int rec4_mt_ok(const rec4_node *N) { return N && !N->leaf && !N->sep && !N->ceil && N->colc->leaf && N->rowc->leaf; }

static void rec4_exec_mt(const rec4_node *N, const double *in, double *out, int nt, int T, rec4_tbuf *tb) {
    const int64_t Bt = N->Bt, N1 = N->N1, N2 = N->N2, Bc = N->Bc, G = N->G, seg = Bc * Bt;
#pragma omp parallel num_threads(T)
    {
#ifdef _OPENMP
        const int tid = omp_get_thread_num();
#else
        const int tid = 0;
#endif
        double *buf = tb[tid].buf, *buf2 = tb[tid].buf2, *trow = tb[tid].trow;
        if (N->stage) {
            // pipelined staging with two buffers: while block k (in cur) is transformed, block k+1 is staged
            // into nxt; sub-strip tasks and staging-chunk tasks are interleaved in one work-sharing loop,
            // so DRAM streaming overlaps with computation; one barrier per block
            const int64_t S = N->stage, rowc = S * Bt, rs = rowc + 4, nblk = N2 / S, nsub = S / Bc;
            const int64_t nch = 32, rch = (N1 + nch - 1) / nch;   // staging chunks of rch rows
            double *sbuf[2] = {N->stg, N->stg2 ? N->stg2 : N->stg};
            const int pipe = N->stg2 != NULL;
#pragma omp for schedule(static)
            for (int64_t i1 = 0; i1 < N1; i1++)
                memcpy(sbuf[0] + 2 * i1 * rs, in + 2 * Bt * i1 * N2, sizeof(double) * 2 * rowc);
            for (int64_t k = 0; k < nblk; k++) {
                double *cur = sbuf[pipe ? k & 1 : 0], *nxt = sbuf[pipe ? (k + 1) & 1 : 0];
                const int64_t cs = k * S, nst = (pipe && k + 1 < nblk) ? nch : 0, ntask = nsub + nst;
#pragma omp for schedule(dynamic, 1)
                for (int64_t t = 0; t < ntask; t++) {
                    // interleave: s0 c0 s1 c1 ... (s = sub-strip, c = staging chunk), then the remaining tail
                    const int64_t m = nsub < nst ? nsub : nst;
                    int64_t sub = -1, ch = -1;
                    if (t < 2 * m) { if (t % 2 == 0) sub = t / 2; else ch = t / 2; }
                    else if (nsub > m) sub = m + (t - 2 * m);
                    else ch = m + (t - 2 * m);
                    if (sub >= 0) {
                        const int64_t c0 = cs + sub * Bc;
                        const double *sb = cur + 2 * Bt * (c0 - cs);
                        for (int64_t i1 = 0; i1 < N1; i1++) memcpy(buf + 2 * i1 * seg, sb + 2 * i1 * rs, sizeof(double) * 2 * seg);
                        const double *res = sh_exec(N->colc->sp, buf, buf2);
                        rec4_twiddle_scatter(N, res, c0, trow, nt);
                    } else {
                        const int64_t r1 = ch * rch, r2 = r1 + rch < N1 ? r1 + rch : N1;
                        for (int64_t i1 = r1; i1 < r2; i1++)
                            memcpy(nxt + 2 * i1 * rs, in + 2 * Bt * (i1 * N2 + cs + S), sizeof(double) * 2 * rowc);
                    }
                }
                if (!pipe && k + 1 < nblk) {   // single buffer: stage the next block after the barrier
#pragma omp for schedule(static)
                    for (int64_t i1 = 0; i1 < N1; i1++)
                        memcpy(sbuf[0] + 2 * i1 * rs, in + 2 * Bt * (i1 * N2 + cs + S), sizeof(double) * 2 * rowc);
                }
            }
        } else {
#pragma omp for schedule(dynamic, 1)
            for (int64_t c0 = 0; c0 < N2; c0 += Bc) {
                for (int64_t i1 = 0; i1 < N1; i1++) memcpy(buf + 2 * i1 * seg, in + 2 * Bt * (i1 * N2 + c0), sizeof(double) * 2 * seg);
                const double *res = sh_exec(N->colc->sp, buf, buf2);
                rec4_twiddle_scatter(N, res, c0, trow, nt);
            }
        }
        if (nt) _mm_sfence();   // make this thread's NT stores to W visible before others read W
#pragma omp barrier
#pragma omp for schedule(dynamic, 1)
        for (int64_t r0 = 0; r0 < N1; r0 += G) {
            rec4_gather_rows(N, r0, buf);
            const double *res = sh_exec(N->rowc->sp, buf, buf2);
            rec4_scatter_out(N, res, r0, out, nt);
        }
        if (nt) _mm_sfence();
    }
}

typedef struct { rec4_node *root; double *work; int T; rec4_tbuf *tb; } rec4_plan;

static rec4_plan *rec4_plan_create(int64_t n, const rec4_params *p) {
    rec4_plan *P = (rec4_plan *)calloc(1, sizeof(rec4_plan));
    P->root = rec4_build(n, 1, p, 1);
    if (!P->root) { free(P); return NULL; }
    P->work = (double *)xmalloc(sizeof(double) * 2 * n);
#ifdef _OPENMP
    P->T = p->threads > 1 && rec4_mt_ok(P->root) ? p->threads : 1;
#else
    P->T = 1;   // built without -fopenmp: single-threaded
#endif
    if (P->T > 1) {
        rec4_node *N = P->root;
        if (N->stage && p->stage2)   // second staging buffer: pipelined staging (see rec4_exec_mt)
            N->stg2 = (double *)xmalloc(sizeof(double) * 2 * N->N1 * (N->stage * N->Bt + 4));
        int64_t bsz = N->N1 * N->Bc * N->Bt; if (N->N2 * N->G * N->Bt > bsz) bsz = N->N2 * N->G * N->Bt;
        P->tb = (rec4_tbuf *)calloc(P->T, sizeof(rec4_tbuf));
        for (int t = 0; t < P->T; t++) {
            P->tb[t].buf = (double *)xmalloc(sizeof(double) * 2 * bsz);
            P->tb[t].buf2 = (double *)xmalloc(sizeof(double) * 2 * bsz);
            P->tb[t].trow = (double *)xmalloc(sizeof(double) * 2 * (N->Bc + 2));
        }
    }
    return P;
}

static void rec4_plan_exec(const rec4_plan *P, const double *in, double *out, int nt) {
    if (P->root->leaf) sh_exec_oop(P->root->sp, in, out, P->work);
    else if (P->T > 1) rec4_exec_mt(P->root, in, out, nt, P->T, P->tb);
    else rec4_exec(P->root, in, out, nt);
}

static void rec4_plan_free(rec4_plan *P) {
    for (int t = 0; P->tb && t < P->T; t++) { free(P->tb[t].buf); free(P->tb[t].buf2); free(P->tb[t].trow); }
    free(P->tb); rec4_free(P->root); free(P->work); free(P);
}
