// SPDX-License-Identifier: GPL-2.0-or-later
// STREAM-like background memory load for the contention experiments (scripts/contention.py).
//
//   stream_load --cpus 1,2,3 [--kernel triad|copy|read] [--mb 128] [--duty 1.0] [--log FILE]
//
// One thread per listed CPU (pinned), each streaming over its own arrays of --mb MB (far larger than the LLC):
//   triad  a[i] = b[i] + s * c[i]   (2 reads + 1 write, ordinary stores: the write also costs a read-for-ownership)
//   copy   a[i] = b[i]              (1 read + 1 write)
//   read   sum += b[i]              (1 read)
// --duty d < 1 throttles each thread: after every 2 MB chunk it sleeps (1 - d) / d times the chunk's run time,
// so the intensity can be set below one full thread.  Runs until SIGTERM / SIGINT.  Every 100 ms the main thread
// appends "<unix time> <logical bytes so far>" to --log (bytes the kernel reads and writes in the program's own
// accounting, read-for-ownership not included), so the achieved background bandwidth over any time window can
// be computed; the DRAM bandwidth actually used is measured separately with the memory-controller counters.
#define _GNU_SOURCE
#include <pthread.h>
#include <sched.h>
#include <signal.h>
#include <stdatomic.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>

static volatile sig_atomic_t stop = 0;
static atomic_long total_bytes;
static int kernel = 0;            // 0 triad, 1 copy, 2 read
static size_t elems;              // doubles per array
static double duty = 1.0;

static void on_sig(int s) { (void)s; stop = 1; }
static double now(void) { struct timespec t; clock_gettime(CLOCK_REALTIME, &t); return t.tv_sec + 1e-9 * t.tv_nsec; }

typedef struct { int cpu; double sink; } targ;

static void *worker(void *p) {
    targ *a = p;
    cpu_set_t cs; CPU_ZERO(&cs); CPU_SET(a->cpu, &cs);
    pthread_setaffinity_np(pthread_self(), sizeof cs, &cs);
    double *A = aligned_alloc(64, elems * 8), *B = aligned_alloc(64, elems * 8), *C = aligned_alloc(64, elems * 8);
    for (size_t i = 0; i < elems; i++) { A[i] = 0; B[i] = 1.0 + (double)(i & 15); C[i] = 0.5; }
    const size_t chunk = (2u << 20) / 8;   // 2 MB of each array per step
    const long per = kernel == 0 ? 24 : kernel == 1 ? 16 : 8;
    double s = 0;
    size_t off = 0;
    while (!stop) {
        double t0 = duty < 1 ? now() : 0;
        size_t e = off + chunk < elems ? off + chunk : elems;
        if (kernel == 0) for (size_t i = off; i < e; i++) A[i] = B[i] + 3.0 * C[i];
        else if (kernel == 1) for (size_t i = off; i < e; i++) A[i] = B[i];
        else for (size_t i = off; i < e; i++) s += B[i];
        atomic_fetch_add_explicit(&total_bytes, (long)(e - off) * per, memory_order_relaxed);
        off = e == elems ? 0 : e;
        if (duty < 1) {
            double run = now() - t0, slp = run * (1 - duty) / duty;
            struct timespec ts = {(time_t)slp, (long)((slp - (time_t)slp) * 1e9)};
            nanosleep(&ts, NULL);
        }
    }
    a->sink = s + A[elems / 2];
    free(A); free(B); free(C);
    return NULL;
}

int main(int argc, char **argv) {
    const char *cpus = NULL, *log = NULL;
    double mb = 128;
    for (int i = 1; i < argc; i++) {
        if (!strcmp(argv[i], "--cpus")) cpus = argv[++i];
        else if (!strcmp(argv[i], "--kernel")) { const char *k = argv[++i]; kernel = !strcmp(k, "copy") ? 1 : !strcmp(k, "read") ? 2 : 0; }
        else if (!strcmp(argv[i], "--mb")) mb = atof(argv[++i]);
        else if (!strcmp(argv[i], "--duty")) duty = atof(argv[++i]);
        else if (!strcmp(argv[i], "--log")) log = argv[++i];
    }
    if (!cpus) { fprintf(stderr, "usage: stream_load --cpus a,b,... [--kernel triad|copy|read] [--mb MB] [--duty d] [--log FILE]\n"); return 1; }
    if (duty <= 0 || duty > 1) duty = 1;
    elems = (size_t)(mb * (1 << 20) / 8) / 8 * 8;
    signal(SIGTERM, on_sig); signal(SIGINT, on_sig);
    int nt = 0, ids[256];
    char *c = strdup(cpus);
    for (char *t = strtok(c, ","); t && nt < 256; t = strtok(NULL, ",")) ids[nt++] = atoi(t);
    pthread_t th[256]; targ ta[256];
    for (int i = 0; i < nt; i++) { ta[i].cpu = ids[i]; pthread_create(&th[i], NULL, worker, &ta[i]); }
    FILE *f = log ? fopen(log, "w") : NULL;
    while (!stop) {
        if (f) { fprintf(f, "%.4f %ld\n", now(), atomic_load(&total_bytes)); fflush(f); }
        struct timespec ts = {0, 100000000}; nanosleep(&ts, NULL);
    }
    for (int i = 0; i < nt; i++) pthread_join(th[i], NULL);
    if (f) { fprintf(f, "%.4f %ld\n", now(), atomic_load(&total_bytes)); fclose(f); }
    return 0;
}
