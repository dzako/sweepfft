// SPDX-License-Identifier: GPL-2.0-or-later
// Calibration for scripts/mem_traffic.py.  Kernels over N bytes, repeated `reps` times; expected DRAM traffic:
//   a  copy, ordinary stores      read 2N (data + read-for-ownership), write N
//   b  copy, non-temporal stores  read N, write N
//   r  read only (sum)            read N
//   w  fill, ordinary stores      read N (read-for-ownership), write N
//   n  fill, non-temporal stores  write N
// r/w/n separate the per-kind weights on counters that do not split reads and writes (AMD data fabric).
//   perf stat -a -e uncore_imc_free_running_0/data_read/,... -- build/traffic_calib a|b [MiB] [reps] [CTL,ACK]
// With CTL,ACK (perf --control fifo FIFOs, see bench_dft --perf-ctl) counting covers only the copy loop and
// "timed_s=<s> calls=<reps>" is printed to stderr (used by scripts/mem_traffic.py to calibrate counters).
#include <immintrin.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "../common/common.h"

static void perf_ctl(const char *spec, const char *cmd) {
    static FILE *f = NULL, *a = NULL;
    if (!f) {
        char ctl[2048], ack[2048];
        const char *c = strchr(spec, ',');
        if (!c) exit(1);
        snprintf(ctl, sizeof ctl, "%.*s", (int)(c - spec), spec);
        snprintf(ack, sizeof ack, "%s", c + 1);
        f = fopen(ctl, "w"); a = fopen(ack, "r");
        if (!f || !a) exit(1);
    }
    fprintf(f, "%s\n", cmd); fflush(f);
    char buf[64];
    if (!fgets(buf, sizeof buf, a)) fprintf(stderr, "no ack\n");
}

int main(int argc, char **argv) {
    char mode = argc > 1 ? argv[1][0] : 'a';
    size_t mib = argc > 2 ? (size_t)atol(argv[2]) : 1024, reps = argc > 3 ? (size_t)atol(argv[3]) : 10;
    size_t nd = mib * (1u << 20) / 8;
    double *src = xmalloc(nd * 8), *dst = xmalloc(nd * 8);
    for (size_t i = 0; i < nd; i++) { src[i] = (double)i; dst[i] = 0; }
    const char *pctl = argc > 4 ? argv[4] : NULL;
    if (pctl) perf_ctl(pctl, "enable");
    double t = now_sec();
    for (size_t r = 0; r < reps; r++) {
        if (mode == 'a')
            for (size_t i = 0; i < nd; i += 4) _mm256_store_pd(dst + i, _mm256_load_pd(src + i));
        else if (mode == 'b')
            for (size_t i = 0; i < nd; i += 4) _mm256_stream_pd(dst + i, _mm256_load_pd(src + i));
        else if (mode == 'r') {
            __m256d acc = _mm256_setzero_pd(), acc2 = _mm256_setzero_pd();
            for (size_t i = 0; i < nd; i += 8) {
                acc = _mm256_add_pd(acc, _mm256_load_pd(src + i));
                acc2 = _mm256_add_pd(acc2, _mm256_load_pd(src + i + 4));
            }
            _mm256_store_pd(dst + (r % 64) * 4, _mm256_add_pd(acc, acc2));
        } else if (mode == 'w') {
            __m256d v = _mm256_set1_pd((double)r);
            for (size_t i = 0; i < nd; i += 4) _mm256_store_pd(dst + i, v);
        } else {
            __m256d v = _mm256_set1_pd((double)r);
            for (size_t i = 0; i < nd; i += 4) _mm256_stream_pd(dst + i, v);
        }
        _mm_sfence();
    }
    t = now_sec() - t;
    if (pctl) { perf_ctl(pctl, "disable"); fprintf(stderr, "timed_s=%.6f calls=%zu\n", t, reps); }
    fprintf(stderr, "mode %c: %zu x %zu MiB in %.3f s (%.1f GB/s copied); checksum %g\n", mode, reps, mib, t,
            reps * mib * 1.048576e-3 / t, dst[nd / 3]);
    return 0;
}
