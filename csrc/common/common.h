// SPDX-License-Identifier: GPL-2.0-or-later
// Shared helpers: aligned allocation, timing, complex AVX2 primitives, accurate twiddles.
#pragma once
#include <immintrin.h>
#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <sys/mman.h>

#define ALIGN 64
#define likely(x) __builtin_expect(!!(x), 1)
#define unlikely(x) __builtin_expect(!!(x), 0)

static inline void *xmalloc(size_t bytes) {
    void *p = NULL;
    size_t b = (bytes + ALIGN - 1) / ALIGN * ALIGN;
    if (b == 0) b = ALIGN;
    size_t al = b >= (4u << 20) ? (2u << 20) : ALIGN;  // big arrays: 2 MB aligned + THP hint
    if (posix_memalign(&p, al, b)) { fprintf(stderr, "alloc %zu failed\n", bytes); exit(1); }
    if (al > ALIGN) madvise(p, b, MADV_HUGEPAGE);
    return p;
}

static inline double now_sec(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return ts.tv_sec + 1e-9 * ts.tv_nsec;
}

// exp(-2*pi*i*k/n) computed accurately: reduce k mod n, use symmetry, long double sincos.
static inline void twiddle(int64_t k, int64_t n, double *re, double *im) {
    k %= n; if (k < 0) k += n;
    // map to first octant for accuracy
    long double x = (long double)k / (long double)n;   // fraction of full turn
    long double a = 2.0L * 3.141592653589793238462643383279502884L * x;
    *re = (double)cosl(a);
    *im = (double)(-sinl(a));
    if (4 * k == n) { *re = 0; *im = -1; }
    else if (2 * k == n) { *re = -1; *im = 0; }
    else if (4 * k == 3 * n) { *re = 0; *im = 1; }
    else if (k == 0) { *re = 1; *im = 0; }
}

// ---------- AVX2 complex helpers: one __m256d = 2 interleaved complex doubles ----------
typedef __m256d V;
#define VLOAD(p) _mm256_load_pd(p)
#define VLOADU(p) _mm256_loadu_pd(p)
#define VSTORE(p, v) _mm256_store_pd(p, v)
#define VSTOREU(p, v) _mm256_storeu_pd(p, v)

static inline V vadd(V a, V b) { return _mm256_add_pd(a, b); }
static inline V vsub(V a, V b) { return _mm256_sub_pd(a, b); }
// a * w (both interleaved complex)
static inline V vcmul(V a, V w) {
    V wr = _mm256_movedup_pd(w);            // (wr, wr)
    V wi = _mm256_permute_pd(w, 0xF);       // (wi, wi)
    V as = _mm256_permute_pd(a, 0x5);       // (ai, ar)
    return _mm256_fmaddsub_pd(a, wr, _mm256_mul_pd(as, wi)); // (ar wr - ai wi, ai wr + ar wi)
}
// a * conj(w)
static inline V vcmulc(V a, V w) {
    V wr = _mm256_movedup_pd(w);
    V wi = _mm256_permute_pd(w, 0xF);
    V as = _mm256_permute_pd(a, 0x5);
    return _mm256_fmsubadd_pd(a, wr, _mm256_mul_pd(as, wi));
}
// a * (-i)  : (ar, ai) -> (ai, -ar)
static inline V vmul_mi(V a) {
    V s = _mm256_permute_pd(a, 0x5);
    return _mm256_xor_pd(s, _mm256_set_pd(-0.0, 0.0, -0.0, 0.0));
}
// a * (+i)  : (ar, ai) -> (-ai, ar)
static inline V vmul_pi(V a) {
    V s = _mm256_permute_pd(a, 0x5);
    return _mm256_xor_pd(s, _mm256_set_pd(0.0, -0.0, 0.0, -0.0));
}
static inline V vscale(V a, double c) { return _mm256_mul_pd(a, _mm256_set1_pd(c)); }
static inline V vbroadcast_c(const double *w) { return _mm256_broadcast_pd((const __m128d *)w); }

// scalar complex
typedef struct { double re, im; } cd;
static inline cd cmul(cd a, cd b) { return (cd){a.re * b.re - a.im * b.im, a.re * b.im + a.im * b.re}; }
static inline cd cadd(cd a, cd b) { return (cd){a.re + b.re, a.im + b.im}; }
static inline cd csub(cd a, cd b) { return (cd){a.re - b.re, a.im - b.im}; }

static inline uint64_t rng_next(uint64_t *s) { // splitmix64
    uint64_t z = (*s += 0x9E3779B97F4A7C15ULL);
    z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9ULL;
    z = (z ^ (z >> 27)) * 0x94D049BB133111EBULL;
    return z ^ (z >> 31);
}
static inline double rng_unif(uint64_t *s) { return (rng_next(s) >> 11) * 0x1.0p-53 * 2.0 - 1.0; }
