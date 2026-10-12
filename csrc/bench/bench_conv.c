// SPDX-License-Identifier: GPL-2.0-or-later
// I9 (never materialise permutations) + pass fusion: cyclic convolution y = x (*) h, n = 2^k.
//
//   mkl         : MKL forward, pointwise, MKL backward (natural order everywhere)
//   fftw        : FFTW_MEASURE forward / backward, pointwise
//   ours_nat    : rec4 forward (natural order), pointwise+conj, rec4 forward, conj      (5-6 sweeps)
//   ours_fused  : 3 sweeps, spectrum never leaves the transposed (k1-major) order:
//       P1  columns of x: FFT_N1, twiddle  -> W   (strided reads of x, row writes)
//       P2  rows of W   : FFT_N2 -> (k1,k2) spectrum, *H', conj, FFT_N2, twiddle -> W (in place, rows)
//       P3  columns of W: FFT_N1, conj -> y   (W is padded, so strided reads are conflict-free)
// Usage: bench_conv N [mintime]   -> CSV rows: variant,n,t_med_ns,rel_err_vs_mkl
#include <fftw3.h>
#include <mkl_dfti.h>
#include "../common/wisdom.h"
#include "../dft/rec4.h"

typedef struct {
    int64_t n, N1, N2, Bc, G, ws;
    sh_plan *c1, *r2;         // batched FFT_N1 (batch Bc), FFT_N2 (batch G)
    double *Tlo, *Thi; int64_t L1;
    double *W, *H, *buf, *buf2, *tw;
} fused_t;

static inline void tw2(const fused_t *F, int64_t e, double *re, double *im) {
    int64_t hi = e / F->L1, lo = e - hi * F->L1;
    double ar = F->Thi[2 * hi], ai = F->Thi[2 * hi + 1], br = F->Tlo[2 * lo], bi = F->Tlo[2 * lo + 1];
    *re = ar * br - ai * bi; *im = ar * bi + ai * br;
}

static fused_t *fused_create(int64_t n, const double *Hnat /* natural-order spectrum of h, already /n */) {
    fused_t *F = calloc(1, sizeof(fused_t));
    int lg = 0; while ((1LL << lg) < n) lg++;
    F->n = n; F->N1 = 1LL << (lg / 2); F->N2 = n / F->N1; F->Bc = 8; F->G = 8; F->ws = F->N2 + 4;
    F->c1 = sh_plan_create(F->N1, F->Bc, 16, 0);
    F->r2 = sh_plan_create(F->N2, F->G, 16, 0);
    int64_t L1 = 1; while (L1 * L1 < n) L1++;
    F->L1 = L1;
    F->Tlo = xmalloc(16 * L1); F->Thi = xmalloc(16 * (n / L1 + 2));
    for (int64_t i = 0; i < L1; i++) twiddle(i, n, F->Tlo + 2 * i, F->Tlo + 2 * i + 1);
    for (int64_t i = 0; i < n / L1 + 2; i++) twiddle(i * L1, n, F->Thi + 2 * i, F->Thi + 2 * i + 1);
    F->W = xmalloc(16 * F->N1 * F->ws);
    // H' in (k1, k2) layout with the same padded row stride
    F->H = xmalloc(16 * F->N1 * F->ws);
    for (int64_t k1 = 0; k1 < F->N1; k1++)
        for (int64_t k2 = 0; k2 < F->N2; k2++) {
            F->H[2 * (k1 * F->ws + k2)] = Hnat[2 * (k1 + F->N1 * k2)];
            F->H[2 * (k1 * F->ws + k2) + 1] = Hnat[2 * (k1 + F->N1 * k2) + 1];
        }
    int64_t bs = F->N1 * F->Bc > F->N2 * F->G ? F->N1 * F->Bc : F->N2 * F->G;
    F->buf = xmalloc(16 * bs); F->buf2 = xmalloc(16 * bs);
    F->tw = xmalloc(16 * (F->N2 > F->Bc ? F->N2 : F->Bc));
    return F;
}

static void fused_exec(const fused_t *F, const double *x, double *y) {
    const int64_t n = F->n, N1 = F->N1, N2 = F->N2, Bc = F->Bc, G = F->G, ws = F->ws;
    double *W = F->W, *buf = F->buf, *buf2 = F->buf2, *tw = F->tw;
    const V cm = _mm256_set_pd(-0.0, 0.0, -0.0, 0.0);
    // ---- P1: columns of x ----
    for (int64_t c0 = 0; c0 < N2; c0 += Bc) {
        for (int64_t i1 = 0; i1 < N1; i1++) memcpy(buf + 2 * i1 * Bc, x + 2 * (i1 * N2 + c0), 16 * Bc);
        const double *res = sh_exec(F->c1, buf, buf2);
        for (int64_t k1 = 0; k1 < N1; k1++) {
            double br, bi, sr, si;
            tw2(F, (c0 * k1) & (n - 1), &br, &bi); tw2(F, k1 & (n - 1), &sr, &si);
            for (int64_t j = 0; j < Bc; j++) {  // w^{(c0+j) k1} = w^{c0 k1} * (w^{k1})^j, 8 steps
                tw[2 * j] = br; tw[2 * j + 1] = bi;
                double nr = br * sr - bi * si; bi = br * si + bi * sr; br = nr;
            }
            double *dst = W + 2 * (k1 * ws + c0);
            for (int64_t j = 0; j < Bc; j += 2) _mm256_stream_pd(dst + 2 * j, vcmul(VLOAD(res + 2 * (k1 * Bc + j)), VLOAD(tw + 2 * j)));
        }
    }
    _mm_sfence();
    // ---- P2: rows of W: FFT, *H, conj, FFT, twiddle, back to W (in place) ----
    for (int64_t r0 = 0; r0 < N1; r0 += G) {
        for (int64_t g = 0; g < G; g += 2) {      // gather G rows interleaved (2x2 register transposes)
            const double *a = W + 2 * (r0 + g) * ws, *b = W + 2 * (r0 + g + 1) * ws;
            for (int64_t i2 = 0; i2 < N2; i2 += 2) {
                V va = VLOAD(a + 2 * i2), vb = VLOAD(b + 2 * i2);
                VSTORE(buf + 2 * (i2 * G + g), _mm256_permute2f128_pd(va, vb, 0x20));
                VSTORE(buf + 2 * ((i2 + 1) * G + g), _mm256_permute2f128_pd(va, vb, 0x31));
            }
        }
        double *res = sh_exec(F->r2, buf, buf2);              // res[(k2*G + g)] spectrum of row r0+g
        double *oth = res == buf ? buf2 : buf;
        for (int64_t k2 = 0; k2 < N2; k2++)
            for (int64_t g = 0; g < G; g += 2) {
                V h = _mm256_set_m128d(_mm_load_pd(F->H + 2 * ((r0 + g + 1) * ws + k2)), _mm_load_pd(F->H + 2 * ((r0 + g) * ws + k2)));
                VSTORE(oth + 2 * (k2 * G + g), _mm256_xor_pd(vcmul(VLOAD(res + 2 * (k2 * G + g)), h), cm));
            }
        double *r2 = sh_exec(F->r2, oth, res);                 // FFT over k2 of conj(P): r2[(i2*G+g)]
        for (int64_t g = 0; g < G; g += 2) {                   // twiddle w_n^{i2 k1}, scatter rows back
            const int64_t k1a = r0 + g, k1b = r0 + g + 1;
            double *da = W + 2 * k1a * ws, *db = W + 2 * k1b * ws;
            double ar, ai, br, bi, war = 1, wai = 0, wbr = 1, wbi = 0;
            tw2(F, k1a % n, &ar, &ai); tw2(F, k1b % n, &br, &bi);
            for (int64_t i2 = 0; i2 < N2; i2 += 2) {
                // re-anchor twiddles every 64 steps for accuracy
                if ((i2 & 15) == 0) { tw2(F, (i2 * k1a) & (n - 1), &war, &wai); tw2(F, (i2 * k1b) & (n - 1), &wbr, &wbi); }
                double w1ar = war * ar - wai * ai, w1ai = war * ai + wai * ar;
                double w1br = wbr * br - wbi * bi, w1bi = wbr * bi + wbi * br;
                V p0 = VLOAD(r2 + 2 * (i2 * G + g)), p1 = VLOAD(r2 + 2 * ((i2 + 1) * G + g));
                V t0 = vcmul(p0, _mm256_setr_pd(war, wai, wbr, wbi)), t1 = vcmul(p1, _mm256_setr_pd(w1ar, w1ai, w1br, w1bi));
                VSTORE(da + 2 * i2, _mm256_permute2f128_pd(t0, t1, 0x20));
                VSTORE(db + 2 * i2, _mm256_permute2f128_pd(t0, t1, 0x31));
                double nar = w1ar * ar - w1ai * ai, nai = w1ar * ai + w1ai * ar;
                double nbr = w1br * br - w1bi * bi, nbi = w1br * bi + w1bi * br;
                war = nar; wai = nai; wbr = nbr; wbi = nbi;
            }
        }
    }
    // ---- P3: columns of W -> y (natural order), conj ----
    for (int64_t c0 = 0; c0 < N2; c0 += Bc) {
        for (int64_t k1 = 0; k1 < N1; k1++) memcpy(buf + 2 * k1 * Bc, W + 2 * (k1 * ws + c0), 16 * Bc);
        const double *res = sh_exec(F->c1, buf, buf2);
        for (int64_t i1 = 0; i1 < N1; i1++)
            for (int64_t j = 0; j < Bc; j += 2) _mm256_stream_pd(y + 2 * (i1 * N2 + c0 + j), _mm256_xor_pd(VLOAD(res + 2 * (i1 * Bc + j)), cm));
    }
    _mm_sfence();
}

// natural-order path with our rec4
typedef struct { rec4_plan *p; double *X, *H; int64_t n; } nat_t;
static void nat_exec(const nat_t *N, const double *x, double *y) {
    const V cm = _mm256_set_pd(-0.0, 0.0, -0.0, 0.0);
    rec4_plan_exec(N->p, x, N->X, 1);
    for (int64_t i = 0; i < N->n; i += 2) VSTORE(N->X + 2 * i, _mm256_xor_pd(vcmul(VLOAD(N->X + 2 * i), VLOAD(N->H + 2 * i)), cm));
    rec4_plan_exec(N->p, N->X, y, 1);
    for (int64_t i = 0; i < N->n; i += 2) VSTORE(y + 2 * i, _mm256_xor_pd(VLOAD(y + 2 * i), cm));
}

static int cmpd(const void *a, const void *b) { double x = *(double *)a, y = *(double *)b; return (x > y) - (x < y); }
#define TIMEIT(expr, out_med)                                                                   \
    do {                                                                                        \
        expr; double _s[200]; int _k = 0; double _t0 = now_sec();                               \
        while (_k < 200 && (_k < 5 || now_sec() - _t0 < mintime)) { double _a = now_sec(); expr; _s[_k++] = now_sec() - _a; } \
        qsort(_s, _k, sizeof(double), cmpd); out_med = _s[_k / 2];                              \
    } while (0)

static double relerr(const double *a, const double *b, int64_t n) {
    double num = 0, den = 0;
    for (int64_t i = 0; i < 2 * n; i++) { num += (a[i] - b[i]) * (a[i] - b[i]); den += b[i] * b[i]; }
    return sqrt(num / den);
}

int main(int argc, char **argv) {
    int64_t n = argc > 1 ? atoll(argv[1]) : (1 << 20);
    double mintime = argc > 2 ? atof(argv[2]) : 0.5;
    double *x = xmalloc(16 * n), *h = xmalloc(16 * n), *y = xmalloc(16 * n), *yref = xmalloc(16 * n), *X = xmalloc(16 * n), *H = xmalloc(16 * n);
    uint64_t seed = 7;
    for (int64_t i = 0; i < 2 * n; i++) { x[i] = rng_unif(&seed); h[i] = rng_unif(&seed); }
    // ---- MKL ----
    DFTI_DESCRIPTOR_HANDLE d;
    DftiCreateDescriptor(&d, DFTI_DOUBLE, DFTI_COMPLEX, 1, (MKL_LONG)n);
    DftiSetValue(d, DFTI_PLACEMENT, DFTI_NOT_INPLACE); DftiSetValue(d, DFTI_THREAD_LIMIT, 1);
    DftiSetValue(d, DFTI_BACKWARD_SCALE, 1.0 / n);
    DftiCommitDescriptor(d);
    DftiComputeForward(d, h, H);
    double t;
#define MKL_CONV do { DftiComputeForward(d, x, X); for (int64_t i = 0; i < n; i += 2) VSTORE(X + 2 * i, vcmul(VLOAD(X + 2 * i), VLOAD(H + 2 * i))); DftiComputeBackward(d, X, yref); } while (0)
    TIMEIT(MKL_CONV, t);
    printf("mkl,%ld,%.1f,0\n", n, t * 1e9); fflush(stdout);
    // ---- FFTW ----
    fftw_import_wisdom_from_filename(wisdom_path());
    fftw_plan pf = fftw_plan_dft_1d((int)n, (fftw_complex *)x, (fftw_complex *)X, FFTW_FORWARD, FFTW_MEASURE);
    fftw_plan pb = fftw_plan_dft_1d((int)n, (fftw_complex *)X, (fftw_complex *)y, FFTW_BACKWARD, FFTW_MEASURE);
    if (wisdom_writable()) fftw_export_wisdom_to_filename(wisdom_path());
    seed = 7; for (int64_t i = 0; i < 2 * n; i++) { x[i] = rng_unif(&seed); h[i] = rng_unif(&seed); }  // MEASURE clobbers
    const double sc = 1.0 / n;
#define FFTW_CONV do { fftw_execute(pf); for (int64_t i = 0; i < n; i += 2) VSTORE(X + 2 * i, vscale(vcmul(VLOAD(X + 2 * i), VLOAD(H + 2 * i)), sc)); fftw_execute(pb); } while (0)
    TIMEIT(FFTW_CONV, t);
    printf("fftw_measure,%ld,%.1f,%.3e\n", n, t * 1e9, relerr(y, yref, n)); fflush(stdout);
    // ---- ours natural ----
    double *Hs = xmalloc(16 * n);
    for (int64_t i = 0; i < 2 * n; i++) Hs[i] = H[i] / n;
    rec4_params rp = {.budget = 131072, .Bc = 8, .G = 8, .split = 0, .rmax = 16, .mode = 0, .nt = 1, .pad = 4};
    nat_t N = {rec4_plan_create(n, &rp), xmalloc(16 * n), Hs, n};
    TIMEIT(nat_exec(&N, x, y), t);
    printf("ours_natural,%ld,%.1f,%.3e\n", n, t * 1e9, relerr(y, yref, n)); fflush(stdout);
    // ---- ours fused (3 sweeps, transposed spectrum) ----
    fused_t *F = fused_create(n, Hs);
    TIMEIT(fused_exec(F, x, y), t);
    printf("ours_fused3,%ld,%.1f,%.3e\n", n, t * 1e9, relerr(y, yref, n)); fflush(stdout);
    return 0;
}
