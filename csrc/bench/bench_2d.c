// SPDX-License-Identifier: GPL-2.0-or-later
// I8: Nussbaumer-Quandalle polynomial transform for the N x N 2-D DFT ("synthetic roots": twiddles are
// signed shifts in C[z]/(z^M + 1), M = N/2) vs row-column FFT, FFTW 2-D and MKL 2-D.
//
// One level of the reduction z^N - 1 = (z^M - 1)(z^M + 1):
//   even k2 : x mod (z^M - 1)  -> N x M 2-D DFT by row-column
//   odd  k2 : x mod (z^M + 1)  -> polynomial transform P_m(z) = sum_n1 o_n1(z) z^{n1 m} (adds + negacyclic
//             shifts only), then P_m(W^{k2}) for odd k2 = twiddle W^r + length-M FFT;  X[k2 m mod N][k2] = P_m(W^k2)
// Usage: bench_2d N [mintime] -> CSV rows variant,N,t_med_ns,mflops(5 N^2 log2 N^2 / t),rel_err_vs_fftw
#include <fftw3.h>
#include <mkl_dfti.h>
#include "../common/wisdom.h"
#include "../dft/stockham.h"

static int cmpd(const void *a, const void *b) { double x = *(double *)a, y = *(double *)b; return (x > y) - (x < y); }
#define TIMEIT(expr, out_med)                                                                   \
    do {                                                                                        \
        expr; double _s[400]; int _k = 0; double _t0 = now_sec();                               \
        while (_k < 400 && (_k < 5 || now_sec() - _t0 < mintime)) { double _a = now_sec(); expr; _s[_k++] = now_sec() - _a; } \
        qsort(_s, _k, sizeof(double), cmpd); out_med = _s[_k / 2];                              \
    } while (0)

// ---- row-column with our batched Stockham: rows one by one, columns in strips of 8 ----
typedef struct { int64_t R, C; sh_plan *pr, *pc; double *buf, *buf2, *work; } rc_t;
static rc_t *rc_create(int64_t R, int64_t C) {
    rc_t *h = calloc(1, sizeof(rc_t)); h->R = R; h->C = C;
    h->pr = sh_plan_create(C, 1, 16, 0); h->pc = sh_plan_create(R, 8, 16, 0);
    h->buf = xmalloc(16 * R * 8); h->buf2 = xmalloc(16 * R * 8); h->work = xmalloc(16 * C);
    return h;
}
// in (R x C) -> out (R x C), 2-D DFT
static void rc_exec(const rc_t *h, const double *in, double *out) {
    const int64_t R = h->R, C = h->C;
    for (int64_t r = 0; r < R; r++) sh_exec_oop(h->pr, in + 2 * r * C, out + 2 * r * C, h->work);
    for (int64_t c0 = 0; c0 < C; c0 += 8) {
        for (int64_t r = 0; r < R; r++) memcpy(h->buf + 16 * r, out + 2 * (r * C + c0), 128);
        const double *res = sh_exec(h->pc, h->buf, h->buf2);
        for (int64_t r = 0; r < R; r++) memcpy(out + 2 * (r * C + c0), res + 16 * r, 128);
    }
}

// ---- Nussbaumer one level ----
typedef struct {
    int64_t N, M;
    rc_t *even;          // N x M row-column
    sh_plan *pm;         // length-M FFT
    double *e, *Ee, *o, *ob, *tw, *work, *row;
    int32_t *brev;
} nq_t;
static nq_t *nq_create(int64_t N) {
    nq_t *h = calloc(1, sizeof(nq_t));
    h->N = N; h->M = N / 2;
    int64_t M = h->M;
    h->even = rc_create(N, M);
    h->pm = sh_plan_create(M, 1, 16, 0);
    h->e = xmalloc(16 * N * M); h->Ee = xmalloc(16 * N * M); h->o = xmalloc(16 * N * M); h->ob = xmalloc(16 * N * M);
    h->tw = xmalloc(16 * M);
    for (int64_t r = 0; r < M; r++) twiddle(r, N, h->tw + 2 * r, h->tw + 2 * r + 1);  // W^r
    h->work = xmalloc(16 * M); h->row = xmalloc(16 * M);
    h->brev = xmalloc(4 * N);
    int lg = 0; while ((1LL << lg) < N) lg++;
    for (int64_t i = 0; i < N; i++) { int64_t r = 0; for (int b = 0; b < lg; b++) if (i >> b & 1) r |= 1LL << (lg - 1 - b); h->brev[i] = (int32_t)r; }
    return h;
}
// dst = src * z^e  mod (z^M + 1), polynomials of M complex
static inline void negashift_add(double *restrict a, double *restrict b, int64_t M, int64_t e) {
    // butterfly: a' = a + b ; b' = (a - b) * z^e
    // (a-b) z^e : coefficient r moves to r+e; wrap (r+e >= M) flips sign.  Done via temp row.
    static __thread double tmp[2 * 8192];
    for (int64_t r = 0; r < M; r += 2) {
        V va = VLOAD(a + 2 * r), vb = VLOAD(b + 2 * r);
        VSTORE(a + 2 * r, vadd(va, vb));
        VSTORE(tmp + 2 * r, vsub(va, vb));
    }
    const V neg = _mm256_set1_pd(-0.0);
    int64_t cut = M - e;   // source r < cut -> dest r+e ; r >= cut -> dest r+e-M with sign flip
    memcpy(b + 2 * e, tmp, 16 * cut);
    int64_t r = 0;
    for (; r + 1 < e; r += 2) VSTOREU(b + 2 * r, _mm256_xor_pd(VLOADU(tmp + 2 * (cut + r)), neg));
    for (; r < e; r++) { b[2 * r] = -tmp[2 * (cut + r)]; b[2 * r + 1] = -tmp[2 * (cut + r) + 1]; }
}
static void nq_exec(const nq_t *h, const double *x, double *X) {
    const int64_t N = h->N, M = h->M;
    // split rows
    for (int64_t n1 = 0; n1 < N; n1++) {
        const double *xr = x + 2 * n1 * N;
        double *er = h->e + 2 * n1 * M, *orr = h->o + 2 * n1 * M;
        for (int64_t r = 0; r < M; r += 2) {
            V a = VLOAD(xr + 2 * r), b = VLOAD(xr + 2 * (r + M));
            VSTORE(er + 2 * r, vadd(a, b)); VSTORE(orr + 2 * r, vsub(a, b));
        }
    }
    // even part: N x M 2-D DFT -> X[k1][2 k2']
    rc_exec(h->even, h->e, h->Ee);
    for (int64_t k1 = 0; k1 < N; k1++)
        for (int64_t k = 0; k < M; k++) { X[2 * (k1 * N + 2 * k)] = h->Ee[2 * (k1 * M + k)]; X[2 * (k1 * N + 2 * k) + 1] = h->Ee[2 * (k1 * M + k) + 1]; }
    // odd part: polynomial transform (radix-2 DIF over polynomials), root z (order N), in place on o
    double *o = h->o;
    for (int64_t len = N, step = 1; len >= 2; len >>= 1, step <<= 1) {
        int64_t half = len / 2;
        for (int64_t base = 0; base < N; base += len)
            for (int64_t j = 0; j < half; j++) {
                int64_t e = j * step;  // twiddle z^{j * (N/len)} ; exponent < N/2 = M ... reduce
                double *a = o + 2 * (base + j) * M, *b = o + 2 * (base + j + half) * M;
                if (e < M) negashift_add(a, b, M, e);
                else { negashift_add(a, b, M, e - M); for (int64_t r = 0; r < 2 * M; r++) b[r] = -b[r]; }
            }
    }
    // P_m sits at index brev(m); evaluate at odd k2: twiddle W^r, FFT_M -> value at k2 = 2j+1
    for (int64_t idx = 0; idx < N; idx++) {
        int64_t m = h->brev[idx];
        const double *p = o + 2 * idx * M;
        for (int64_t r = 0; r < M; r += 2) VSTORE(h->row + 2 * r, vcmul(VLOAD(p + 2 * r), VLOAD(h->tw + 2 * r)));
        sh_exec_oop(h->pm, h->row, h->ob, h->work);
        for (int64_t j = 0; j < M; j++) {
            int64_t k2 = 2 * j + 1, k1 = (k2 * m) & (N - 1);
            X[2 * (k1 * N + k2)] = h->ob[2 * j]; X[2 * (k1 * N + k2) + 1] = h->ob[2 * j + 1];
        }
    }
}

int main(int argc, char **argv) {
    int64_t N = argc > 1 ? atoll(argv[1]) : 256;
    double mintime = argc > 2 ? atof(argv[2]) : 0.3;
    int64_t n = N * N;
    double *x = xmalloc(16 * n), *y = xmalloc(16 * n), *ref = xmalloc(16 * n);
    uint64_t seed = 3; for (int64_t i = 0; i < 2 * n; i++) x[i] = rng_unif(&seed);
    double flops = 5.0 * n * log2((double)n), t;
    fftw_import_wisdom_from_filename(wisdom_path());
    fftw_plan p = fftw_plan_dft_2d((int)N, (int)N, (fftw_complex *)x, (fftw_complex *)ref, FFTW_FORWARD, FFTW_MEASURE);
    if (wisdom_writable()) fftw_export_wisdom_to_filename(wisdom_path());
    seed = 3; for (int64_t i = 0; i < 2 * n; i++) x[i] = rng_unif(&seed);  // MEASURE planning clobbers arrays
    TIMEIT(fftw_execute(p), t);
    printf("fftw_measure_2d,%ld,%.1f,%.1f,0\n", N, t * 1e9, flops / t / 1e6);
    DFTI_DESCRIPTOR_HANDLE d; MKL_LONG dims[2] = {N, N};
    DftiCreateDescriptor(&d, DFTI_DOUBLE, DFTI_COMPLEX, 2, dims);
    DftiSetValue(d, DFTI_PLACEMENT, DFTI_NOT_INPLACE); DftiSetValue(d, DFTI_THREAD_LIMIT, 1); DftiCommitDescriptor(d);
    TIMEIT(DftiComputeForward(d, x, y), t);
    double num = 0, den = 0;
#define ERR() (num = den = 0, ({ for (int64_t i = 0; i < 2 * n; i++) { num += (y[i] - ref[i]) * (y[i] - ref[i]); den += ref[i] * ref[i]; } }), sqrt(num / den))
    printf("mkl_2d,%ld,%.1f,%.1f,%.3e\n", N, t * 1e9, flops / t / 1e6, ERR());
    rc_t *rc = rc_create(N, N);
    TIMEIT(rc_exec(rc, x, y), t);
    printf("ours_rowcol,%ld,%.1f,%.1f,%.3e\n", N, t * 1e9, flops / t / 1e6, ERR());
    nq_t *nq = nq_create(N);
    TIMEIT(nq_exec(nq, x, y), t);
    printf("ours_nussbaumer1,%ld,%.1f,%.1f,%.3e\n", N, t * 1e9, flops / t / 1e6, ERR());
    return 0;
}
