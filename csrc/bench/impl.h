// SPDX-License-Identifier: GPL-2.0-or-later
// Common interface every DFT implementation exposes to the benchmark driver.
// Forward complex DFT, sign -1, unnormalised, out-of-place; exec must not modify `in`.
#pragma once
#include <stdint.h>
#include <stdlib.h>
#ifdef __cplusplus
extern "C" {
#endif

typedef struct {
    const char *name;
    void *(*plan)(int64_t n, const char *params);  // NULL if size unsupported
    void (*exec)(void *plan, const double *in, double *out);
    void (*destroy)(void *plan);
    // optional: short description of what the planner chose (written into a static buffer), or NULL
    const char *(*describe)(void *plan);
} dft_impl;

// key=value lookup in "k1=v1,k2=v2"
double param_get(const char *params, const char *key, double dflt);

// Thread count for multithreaded runs: $BENCH_THREADS (default 1).  pmfft_mt / rec4 threads=, and, in the
// bench_dft_mt build (threaded MKL + FFTW-OpenMP), MKL and FFTW all use it.
static inline int bench_threads(void) {
    const char *e = getenv("BENCH_THREADS");
    int t = e && *e ? atoi(e) : 1;
    return t > 0 ? t : 1;
}

// In-place mode for the protocol-sensitivity suite (scripts/fairness.py): $BENCH_INPLACE=1 makes the driver call
// exec(plan, buf, buf), and the library wrappers plan for in-place data (FFTW in-place plan, DFTI_INPLACE, ducc0
// without its copy).  Implementations without an in-place algorithm must still give the right result for in == out.
static inline int bench_inplace(void) {
    const char *e = getenv("BENCH_INPLACE");
    return e && *e == '1';
}

extern const dft_impl impl_fftw_estimate, impl_fftw_measure, impl_fftw_patient;
extern const dft_impl impl_mkl, impl_ducc;
extern const dft_impl *ours_impls[];
extern const dft_impl *ours_impls2[];
extern const dft_impl *ours_impls3[];
extern const dft_impl *ours_impls4[];
extern const dft_impl *ours_impls5[];

#ifdef __cplusplus
}
#endif
