// SPDX-License-Identifier: GPL-2.0-or-later
// Benchmark driver.  Usage:
//   bench_dft --impl NAME [--params k=v,...] --n N1,N2,... [--check] [--mintime S] [--header] [--startat T]
// --startat T: after planning/warm-up, wait until wall-clock time T (Unix epoch seconds) before timing,
//              so concurrent processes measure in overlapping windows (bandwidth-scaling tests).
// --barrier DIR K: after planning/warm-up, create DIR/<pid> and wait until DIR holds K entries
//              (all concurrent processes are ready), then start timing.
// --perf-ctl CTL,ACK: perf-stat control FIFOs (perf stat --control fifo:CTL,ACK --delay=-1).  Counters are
//              enabled only around the timed loop; "timed_s=<s> calls=<k>" is printed to stderr so that
//              counts can be normalised per transform (scripts/mem_traffic.py).
// --plan-lock FILE: hold an exclusive flock on FILE while planning, so concurrent processes plan one at a
//              time (planning needs ~1.6x the steady-state memory, and plans are not disturbed by each other).
// Also prints to stderr, per size, "mem n=<n> lib_bytes=<b> plan_peak_bytes=<b> plan=<desc>": resident memory the
// implementation added beyond the caller's in/out arrays (plan, twiddles, scratch; measured after planning and
// one warm-up call, glibc free memory trimmed), the resident peak above that baseline during planning and the
// warm-up call, and the implementation's own description of the chosen plan ("-" if it has none).
// Protocol-sensitivity modes (scripts/fairness.py; the defaults are the protocol of every other result):
// --cold       flush the caches (read a 256 MB buffer) before every timed call; one call per sample
// --fresh-alloc  every sample allocates new input and output arrays (input copied from the master copy,
//              output untouched, so first-touch page faults are inside the timed call), then frees them
// $BENCH_INPLACE=1  in-place transforms, exec(plan, buf, buf) (see impl.h); the data are rescaled by an exact
//              power of two between samples so that repeated unnormalised transforms cannot overflow
// $BENCH_NO_THP=1   prctl(PR_SET_THP_DISABLE): standard 4 KB pages for every allocation in the process
// and always prints "fair n=<n> t_first_ns=<t> anon_huge_bytes=<b> samples=<k>": the time of the first call of
// the plan (after planning, before any other call) and the process's resident transparent-huge-page memory.
// --samples   also print every sample to stderr, "samples n=<n> inner=<k> t_ns=<t1>,<t2>,..." in measurement
//              order (each sample is the mean over `inner` back-to-back calls), for scripts/repro.py
// --curve R   cost-curve mode (scripts/overhead.py): right after planning, make R calls (stopping early after
//              --curve-max seconds) and print "curve n=<n> init_s=<s> plan_s=<s> cum=1:<s>,2:<s>,5:<s>,..." with the
//              cumulative execution time after 1, 2, 5, 10, 20, 50, 100, ... calls (the first call included)
// Always prints "mem2 n=<n> after_plan_bytes=<b> exec_peak_bytes=<b>": resident memory added by planning alone
// (glibc free memory trimmed) and the resident peak above that during the first call (execution scratch).
// Prints one CSV row per size:
//   impl,params,n,plan_s,t_med_ns,t_min_ns,mflops,rms_err,max_err,reps
// mflops follows the benchFFT convention 5 n log2 n / t (for every n).
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <dirent.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/file.h>
#include <malloc.h>
#include <sys/prctl.h>
#include "impl.h"
#include "../common/common.h"
#include "../ref/ref.h"

static const dft_impl *find_impl(const char *name) {
    const dft_impl *ext[] = {&impl_fftw_estimate, &impl_fftw_measure, &impl_fftw_patient, &impl_mkl, &impl_ducc};
    for (size_t i = 0; i < sizeof(ext) / sizeof(ext[0]); i++) if (!strcmp(ext[i]->name, name)) return ext[i];
    for (int i = 0; ours_impls[i]; i++) if (!strcmp(ours_impls[i]->name, name)) return ours_impls[i];
    for (int i = 0; ours_impls2[i]; i++) if (!strcmp(ours_impls2[i]->name, name)) return ours_impls2[i];
    for (int i = 0; ours_impls3[i]; i++) if (!strcmp(ours_impls3[i]->name, name)) return ours_impls3[i];
    for (int i = 0; ours_impls4[i]; i++) if (!strcmp(ours_impls4[i]->name, name)) return ours_impls4[i];
    for (int i = 0; ours_impls5[i]; i++) if (!strcmp(ours_impls5[i]->name, name)) return ours_impls5[i];
    return NULL;
}

// Send one command to a perf-stat control FIFO pair "CTL,ACK" and wait for the acknowledgement.
// The FIFOs stay open for the whole run (closing the write end would signal EOF to perf).
static void perf_ctl(const char *spec, const char *cmd) {
    static FILE *f = NULL, *a = NULL;
    if (!f) {
        char ctl[2048], ack[2048];
        const char *c = strchr(spec, ',');
        if (!c) { fprintf(stderr, "--perf-ctl needs CTL,ACK\n"); exit(1); }
        snprintf(ctl, sizeof ctl, "%.*s", (int)(c - spec), spec);
        snprintf(ack, sizeof ack, "%s", c + 1);
        f = fopen(ctl, "w"); a = fopen(ack, "r");
        if (!f || !a) { fprintf(stderr, "cannot open perf control fifos\n"); exit(1); }
    }
    fprintf(f, "%s\n", cmd); fflush(f);
    char buf[64];
    if (!fgets(buf, sizeof buf, a)) fprintf(stderr, "no ack from perf\n");
}

// resident set size and its peak (bytes) from /proc/self/status
static void rss_now(int64_t *rss, int64_t *hwm) {
    FILE *f = fopen("/proc/self/status", "r");
    char line[256];
    *rss = *hwm = 0;
    if (!f) return;
    while (fgets(line, sizeof line, f)) {
        if (!strncmp(line, "VmRSS:", 6)) *rss = atoll(line + 6) * 1024;
        else if (!strncmp(line, "VmHWM:", 6)) *hwm = atoll(line + 6) * 1024;
    }
    fclose(f);
}
static void rss_reset_peak(void) {
    FILE *f = fopen("/proc/self/clear_refs", "w");     // "5" resets VmHWM to the current RSS (Linux >= 4.0)
    if (f) { fputs("5", f); fclose(f); }
}

static int64_t anon_huge_bytes(void) {
    FILE *f = fopen("/proc/self/smaps_rollup", "r");
    char line[256];
    int64_t b = -1;
    if (!f) return -1;
    while (fgets(line, sizeof line, f)) if (!strncmp(line, "AnonHugePages:", 14)) b = atoll(line + 14) * 1024;
    fclose(f);
    return b;
}

// read (not write) a buffer much larger than the LLC, so the caches hold only clean, unrelated lines
static double flush_caches(const double *fl, size_t cnt) {
    __m256d acc = _mm256_setzero_pd();
    for (size_t i = 0; i < cnt; i += 8) acc = _mm256_add_pd(acc, _mm256_load_pd(fl + i));
    double t[4]; _mm256_storeu_pd(t, acc);
    return t[0] + t[1] + t[2] + t[3];
}

// multiply by 2^-e (exact): keeps repeated in-place transforms inside the exponent range
static void rescale(double *x, int64_t n, int e) {
    double f = ldexp(1.0, -e);
    for (int64_t i = 0; i < 2 * n; i++) x[i] *= f;
}

static int cmp_d(const void *a, const void *b) { double x = *(double *)a, y = *(double *)b; return (x > y) - (x < y); }

// Caller-owned arrays (input, output, pristine copy).  $BENCH_CALLER_PAGES selects how they are paged:
//   unset / "huge": xmalloc (2 MB aligned + MADV_HUGEPAGE), the headline protocol;
//   "plain": 64-byte aligned, no advice, i.e. what an ordinary malloc'ing caller gets under the system THP mode;
//   "4k":    64-byte aligned + MADV_NOHUGEPAGE (4 KB pages even when THP is "always").
// Library-internal memory is not affected (unlike BENCH_NO_THP, which disables THP for the whole process).
static void *caller_alloc(size_t bytes) {
    const char *e = getenv("BENCH_CALLER_PAGES");
    if (!e || !strcmp(e, "huge")) return xmalloc(bytes);
    void *p = NULL;
    size_t b = (bytes + 63) / 64 * 64;
    if (posix_memalign(&p, 64, b ? b : 64)) { fprintf(stderr, "alloc %zu failed\n", bytes); exit(1); }
    if (!strcmp(e, "4k")) madvise((void *)((uintptr_t)p & ~(uintptr_t)4095), b + 4096, MADV_NOHUGEPAGE);
    return p;
}

int main(int argc, char **argv) {
    const char *iname = NULL, *params = "", *nlist = NULL;
    const char *bdir = NULL, *plock = NULL, *pctl = NULL; int bk = 0;
    int check = 0, header = 0, cold = 0, fresh = 0, dump = 0, curve = 0; double curve_max = 20; double mintime = 0.3, startat = 0;
    int64_t check_max = 1 << 22;
    for (int i = 1; i < argc; i++) {
        if (!strcmp(argv[i], "--impl")) iname = argv[++i];
        else if (!strcmp(argv[i], "--params")) params = argv[++i];
        else if (!strcmp(argv[i], "--n")) nlist = argv[++i];
        else if (!strcmp(argv[i], "--check")) check = 1;
        else if (!strcmp(argv[i], "--check-max")) check_max = atoll(argv[++i]);
        else if (!strcmp(argv[i], "--mintime")) mintime = atof(argv[++i]);
        else if (!strcmp(argv[i], "--header")) header = 1;
        else if (!strcmp(argv[i], "--startat")) startat = atof(argv[++i]);
        else if (!strcmp(argv[i], "--barrier")) { bdir = argv[++i]; bk = atoi(argv[++i]); }
        else if (!strcmp(argv[i], "--plan-lock")) plock = argv[++i];
        else if (!strcmp(argv[i], "--perf-ctl")) pctl = argv[++i];
        else if (!strcmp(argv[i], "--cold")) cold = 1;
        else if (!strcmp(argv[i], "--fresh-alloc")) fresh = 1;
        else if (!strcmp(argv[i], "--samples")) dump = 1;
        else if (!strcmp(argv[i], "--curve")) curve = atoi(argv[++i]);
        else if (!strcmp(argv[i], "--curve-max")) curve_max = atof(argv[++i]);
    }
    if (header) printf("impl,params,n,plan_s,t_med_ns,t_min_ns,mflops,rms_err,max_err,reps\n");
    if (!iname || !nlist) { if (!header) fprintf(stderr, "need --impl and --n\n"); return header ? 0 : 1; }
    const dft_impl *I = find_impl(iname);
    if (!I) { fprintf(stderr, "unknown impl %s\n", iname); return 1; }
    if (getenv("BENCH_NO_THP") && *getenv("BENCH_NO_THP") == '1' && prctl(PR_SET_THP_DISABLE, 1, 0, 0, 0))
        perror("PR_SET_THP_DISABLE");
    const int inplace = bench_inplace();
    // one-time library initialisation (MKL's global state, FFTW's planner) is not attributed to the first size
    double init_s = now_sec();
    { double *a = xmalloc(16 * 64), *b = xmalloc(16 * 64); memset(a, 0, 16 * 64);
      void *P = I->plan(64, params); if (P) { I->exec(P, a, inplace ? a : b); I->destroy(P); } free(a); free(b); }
    if (inplace && fresh) { fprintf(stderr, "--fresh-alloc is out-of-place only\n"); return 1; }
    const size_t flcnt = (size_t)32 << 20;          // 256 MB of doubles for --cold
    double *fl = NULL, flsink = 0;
    if (cold) { fl = xmalloc(8 * flcnt); for (size_t i = 0; i < flcnt; i++) fl[i] = 1e-300 * (double)(i & 7); }
    init_s = now_sec() - init_s;                 // one-time library initialisation (warm-up plan + call)
    char *nl = strdup(nlist);
    for (char *tok = strtok(nl, ","); tok; tok = strtok(NULL, ",")) {
        int64_t n = atoll(tok);
        double *in = caller_alloc(16 * n), *out = inplace ? in : caller_alloc(16 * n), *src = in;
        uint64_t seed = 12345 + n;
        for (int64_t i = 0; i < 2 * n; i++) in[i] = rng_unif(&seed);
        if (inplace || fresh) { src = caller_alloc(16 * n); memcpy(src, in, 16 * n); }   // pristine input
        if (!inplace) memset(out, 0, 16 * n);
        int lfd = plock ? open(plock, O_CREAT | O_RDWR, 0644) : -1;
        if (lfd >= 0) flock(lfd, LOCK_EX);
        int64_t rss0, hwm, rss1;
        malloc_trim(0);
        rss_reset_peak();
        rss_now(&rss0, &hwm);
        double t0 = now_sec();
        void *P = I->plan(n, params);
        double plan_s = now_sec() - t0;
        if (lfd >= 0) { flock(lfd, LOCK_UN); close(lfd); }
        if (!P) {
            printf("%s,\"%s\",%ld,,,,,,,0\n", iname, params, n); fflush(stdout);
            free(in); if (!inplace) free(out); if (src != in) free(src);
            continue;
        }
        double rms = NAN, mx = NAN;
        int64_t rssp, hwmp;
        malloc_trim(0);
        rss_now(&rssp, &hwmp);                   // after planning only
        rss_reset_peak();
        t0 = now_sec();
        I->exec(P, in, out);
        double t_first = now_sec() - t0;
        int64_t rsse, hwme;
        rss_now(&rsse, &hwme);
        fprintf(stderr, "mem2 n=%ld after_plan_bytes=%ld exec_peak_bytes=%ld\n", (long)n, (long)(rssp - rss0),
                (long)(hwme - rssp));
        if (curve > 0) {                         // cumulative cost of the first R calls
            fprintf(stderr, "curve n=%ld init_s=%.6f plan_s=%.6f cum=1:%.6f", (long)n, init_s, plan_s, t_first);
            double cum = t_first;
            int next = 2;
            for (int r = 2; r <= curve && cum < curve_max; r++) {
                if (inplace && r % 8 == 0) rescale(in, n, (int)(4 * log2((double)n)));
                double a = now_sec();
                I->exec(P, in, out);
                cum += now_sec() - a;
                if (r == next || r == curve) {
                    fprintf(stderr, ",%d:%.6f", r, cum);
                    // checkpoints 1, 2, 5, 10, 20, 50, 100, ...
                    int d = next, m = 1;
                    while (d >= 10) { d /= 10; m *= 10; }
                    next = (d == 1 ? 2 : d == 2 ? 5 : 10) * m;
                }
            }
            fputc('\n', stderr);
        }
        malloc_trim(0);
        rss_now(&rss1, &hwm);
        fprintf(stderr, "mem n=%ld lib_bytes=%ld plan_peak_bytes=%ld plan=%s\n", (long)n, (long)(rss1 - rss0),
                (long)((hwmp > hwme ? hwmp : hwme) - rss0), I->describe ? I->describe(P) : "-");
        if (check && n <= check_max) {
            qc *ref = malloc(sizeof(qc) * n);
            ref_dft(src, n, ref);
            ref_errors(out, ref, n, &rms, &mx);
            free(ref);
        }
        // in-place: every call multiplies the magnitude by ~sqrt(n) (F^2 x = n x reversed); track it in bits
        const double grow = inplace ? 0.5 * log2((double)n) : 0;
        double bits = grow;
        // calibrate inner loop count so each sample takes >= ~2 ms (or 1 call for big n)
        double ts = now_sec(); I->exec(P, in, out); double one = now_sec() - ts;
        bits += grow;
        int inner = one > 2e-3 ? 1 : (int)(2e-3 / (one + 1e-9)) + 1;
        if (cold || fresh) inner = 1;
        if (inplace && inner * grow > 300) inner = (int)(300 / grow) > 1 ? (int)(300 / grow) : 1;
        int maxs = 1000; double *samp = malloc(sizeof(double) * maxs); int ns = 0;
        if (bdir) {
            char fn[4096]; snprintf(fn, sizeof fn, "%s/%d", bdir, (int)getpid());
            FILE *f = fopen(fn, "w"); if (f) fclose(f);
            for (;;) {
                int cnt = 0; DIR *d = opendir(bdir); struct dirent *e;
                if (d) { while ((e = readdir(d))) if (e->d_name[0] != '.') cnt++; closedir(d); }
                if (cnt >= bk) break;
                struct timespec sl = {0, 200000}; nanosleep(&sl, NULL);
            }
        }
        if (startat > 0) {
            struct timespec rt;
            for (;;) {
                clock_gettime(CLOCK_REALTIME, &rt);
                double left = startat - (rt.tv_sec + 1e-9 * rt.tv_nsec);
                if (left <= 0) break;
                struct timespec sl = {0, left > 1e-3 ? 500000 : 20000};
                nanosleep(&sl, NULL);
            }
        }
        if (pctl) perf_ctl(pctl, "enable");
        double tstart = now_sec(), timed = 0;
        // default mode: wall time ~ timed time; cold / fresh modes add untimed work, so bound the wall time too
        while (ns < maxs && (ns < 5 || (timed < mintime && now_sec() - tstart < 20 * mintime + 10))) {
            double *xi = in, *xo = out;
            if (inplace && bits > 300) { rescale(in, n, (int)bits); bits = 0; }
            if (fresh) { xi = caller_alloc(16 * n); memcpy(xi, src, 16 * n); xo = caller_alloc(16 * n); }
            if (cold) flsink += flush_caches(fl, flcnt);
            double a = now_sec();
            for (int k = 0; k < inner; k++) I->exec(P, xi, xo);
            double dt = now_sec() - a;
            samp[ns++] = dt / inner;
            timed += dt;
            bits += inner * grow;
            if (fresh) { free(xi); free(xo); }
        }
        if (pctl) {
            double tw = now_sec() - tstart;
            perf_ctl(pctl, "disable");
            fprintf(stderr, "timed_s=%.6f calls=%ld\n", cold || fresh ? timed : tw, (long)ns * inner);
        }
        fprintf(stderr, "fair n=%ld t_first_ns=%.1f anon_huge_bytes=%ld samples=%d inplace=%d cold=%d fresh=%d\n",
                (long)n, t_first * 1e9, (long)anon_huge_bytes(), ns, inplace, cold, fresh);
        if (dump) {
            fprintf(stderr, "samples n=%ld inner=%d t_ns=", (long)n, inner);
            for (int k = 0; k < ns; k++) fprintf(stderr, k ? ",%.1f" : "%.1f", samp[k] * 1e9);
            fputc('\n', stderr);
        }
        qsort(samp, ns, sizeof(double), cmp_d);
        double med = samp[ns / 2], mn = samp[0];
        double mflops = 5.0 * n * log2((double)n) / med * 1e-6;
        printf("%s,\"%s\",%ld,%.4f,%.1f,%.1f,%.1f,%.3e,%.3e,%d\n", iname, params, n, plan_s, med * 1e9, mn * 1e9,
               mflops, rms, mx, ns * inner);
        fflush(stdout);
        free(samp);
        I->destroy(P);
        free(in); if (!inplace) free(out); if (src != in) free(src);
    }
    if (fl) { free(fl); if (flsink == 12345.678) puts(""); }
    free(nl);
    return 0;
}
