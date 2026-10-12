// SPDX-License-Identifier: GPL-2.0-or-later
// Baselines: FFTW 3.3.10 (estimate / measure / patient, wisdom cached) and Intel MKL DFTI.
#include <fftw3.h>
#include <mkl_dfti.h>
#include <mkl_service.h>
#include "../common/wisdom.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "impl.h"

double param_get(const char *params, const char *key, double dflt) {
    if (!params) return dflt;
    size_t kl = strlen(key);
    const char *p = params;
    while (*p) {
        if (strncmp(p, key, kl) == 0 && p[kl] == '=') return atof(p + kl + 1);
        p = strchr(p, ',');
        if (!p) break;
        p++;
    }
    return dflt;
}

// ---------------- FFTW ----------------
static int wisdom_loaded = 0;
typedef struct { fftw_plan p; } fftw_h;

static void *fftw_plan_gen(int64_t n, unsigned flags) {
#ifdef BENCH_MT
    // threaded build: FFTW's OpenMP planner with $BENCH_THREADS threads (wisdom is per thread count)
    static int thr_init = 0;
    if (!thr_init) { fftw_init_threads(); thr_init = 1; }
    fftw_plan_with_nthreads(bench_threads());
#endif
    if (!wisdom_loaded) {
        // reported so that requested planner flags can be told apart from planning actually done: with imported
        // wisdom (which may come from a more rigorous mode, e.g. PATIENT answering a MEASURE request) plan_s ~ 0
        int ok = fftw_import_wisdom_from_filename(wisdom_path());
        fprintf(stderr, "fftw wisdom_file=%s imported=%d writable=%d\n", wisdom_path(), ok, wisdom_writable());
        wisdom_loaded = 1;
    }
    // bound MEASURE/PATIENT planning (75+ min observed on some smooth sizes); $FFTW_TIMELIMIT overrides the 60 s default
    const char *tl = getenv("FFTW_TIMELIMIT");
    fftw_set_timelimit(tl && *tl ? atof(tl) : 60.0);
    fftw_complex *a = fftw_alloc_complex(n), *b = fftw_alloc_complex(n);
    fftw_h *h = malloc(sizeof(fftw_h));
    h->p = fftw_plan_dft_1d((int)n, a, bench_inplace() ? a : b, FFTW_FORWARD, flags);
    fftw_free(a); fftw_free(b);
    if (flags != FFTW_ESTIMATE && wisdom_writable()) fftw_export_wisdom_to_filename(wisdom_path());
    return h;
}
static void *fftw_plan_e(int64_t n, const char *p) { (void)p; return fftw_plan_gen(n, FFTW_ESTIMATE); }
static void *fftw_plan_m(int64_t n, const char *p) { (void)p; return fftw_plan_gen(n, FFTW_MEASURE); }
static void *fftw_plan_p(int64_t n, const char *p) { (void)p; return fftw_plan_gen(n, FFTW_PATIENT); }
static void fftw_exec_(void *h, const double *in, double *out) {
    fftw_execute_dft(((fftw_h *)h)->p, (fftw_complex *)in, (fftw_complex *)out);
}
static void fftw_destroy_(void *h) { fftw_destroy_plan(((fftw_h *)h)->p); free(h); }
// FFTW plan structure, compacted to the solver names in nesting order, e.g. "dft-ct-dit/16>dftw-direct-16>..."
static const char *fftw_describe(void *h) {
    static char buf[160];
    char *s = fftw_sprint_plan(((fftw_h *)h)->p);
    int o = 0;
    for (const char *c = s; c && *c && o < (int)sizeof buf - 40; c++) {
        if (*c != '(') continue;
        int k = 0; char nm[48];
        for (c++; *c && *c != ' ' && *c != ')' && *c != '\n' && k < 47; c++) nm[k++] = *c;
        nm[k] = 0;
        if (k && strchr(nm, '-')) o += snprintf(buf + o, sizeof buf - o, "%s%s", o ? ">" : "", nm);
        if (!*c) break;
    }
    if (!o) snprintf(buf, sizeof buf, "?");
    free(s);
    return buf;
}

const dft_impl impl_fftw_estimate = {"fftw_estimate", fftw_plan_e, fftw_exec_, fftw_destroy_, fftw_describe};
const dft_impl impl_fftw_measure = {"fftw_measure", fftw_plan_m, fftw_exec_, fftw_destroy_, fftw_describe};
const dft_impl impl_fftw_patient = {"fftw_patient", fftw_plan_p, fftw_exec_, fftw_destroy_, fftw_describe};

// ---------------- MKL ----------------
typedef struct { DFTI_DESCRIPTOR_HANDLE d; } mkl_h;
static void *mkl_plan(int64_t n, const char *p) {
    (void)p;
    mkl_h *h = malloc(sizeof(mkl_h));
    MKL_LONG st = DftiCreateDescriptor(&h->d, DFTI_DOUBLE, DFTI_COMPLEX, 1, (MKL_LONG)n);
    static int said = 0;
    if (!said) {   // the code path MKL dispatched to (e.g. "... AVX2 ... enabled processors")
        MKLVersion v; mkl_get_version(&v);
        fprintf(stderr, "mkl version=%d.%d.%d isa=%s\n", v.MajorVersion, v.MinorVersion, v.UpdateVersion, v.Processor);
        said = 1;
    }
    st |= DftiSetValue(h->d, DFTI_PLACEMENT, bench_inplace() ? DFTI_INPLACE : DFTI_NOT_INPLACE);
#ifdef BENCH_MT
    mkl_set_num_threads(bench_threads());
    st |= DftiSetValue(h->d, DFTI_THREAD_LIMIT, (MKL_LONG)bench_threads());   // linked against threaded MKL
#else
    st |= DftiSetValue(h->d, DFTI_THREAD_LIMIT, 1);                          // linked against sequential MKL
#endif
    st |= DftiCommitDescriptor(h->d);
    if (st) { fprintf(stderr, "MKL plan failed: %s\n", DftiErrorMessage(st)); free(h); return NULL; }
    return h;
}
static void mkl_exec(void *h, const double *in, double *out) {
    if (in == out) DftiComputeForward(((mkl_h *)h)->d, out);
    else DftiComputeForward(((mkl_h *)h)->d, (void *)in, out);
}
static void mkl_destroy(void *h) { DftiFreeDescriptor(&((mkl_h *)h)->d); free(h); }
const dft_impl impl_mkl = {"mkl", mkl_plan, mkl_exec, mkl_destroy};
