// SPDX-License-Identifier: GPL-2.0-or-later
// Timing breakdown of rec4 top level: stream bandwidth, step A, step B, leaf FFT-only cost.
#define REC4_PROF
#include "../dft/rec4.h"
int main(int argc, char **argv) {
    int64_t n = argc > 1 ? atoll(argv[1]) : (1 << 22);
    // usage: prof_rec4 n pf N1 Bc G pad budget rmax stage
    rec4_params p = {.budget = argc > 7 ? atoll(argv[7]) : 131072, .Bc = argc > 4 ? atoll(argv[4]) : 8, .G = argc > 5 ? atoll(argv[5]) : 8,
                     .split = 0, .rmax = argc > 8 ? atoi(argv[8]) : 16, .mode = 0, .nt = 1, .pf = argc > 2 ? atoi(argv[2]) : 1,
                     .N1top = argc > 3 ? atoll(argv[3]) : 0, .pad = argc > 6 ? atoll(argv[6]) : 0,
                     .stage = argc > 9 ? atoll(argv[9]) : 0};
    rec4_plan *P = rec4_plan_create(n, &p);
    rec4_node *N = P->root;
    printf("n=%ld N1=%ld N2=%ld Bc=%ld G=%ld colleaf=%d rowleaf=%d\n", n, N->N1, N->N2, N->Bc, N->G, N->colc->leaf, N->rowc->leaf);
    double *in = xmalloc(16 * n), *out = xmalloc(16 * n);
    uint64_t seed = 1; for (int64_t i = 0; i < 2 * n; i++) in[i] = rng_unif(&seed);
    for (int it = 0; it < 3; it++) rec4_plan_exec(P, in, out, 1);
    double t = now_sec(); for (int it = 0; it < 5; it++) rec4_plan_exec(P, in, out, 1); double tall = (now_sec() - t) / 5;
    // copy bandwidth (read + NT write)
    t = now_sec(); for (int it = 0; it < 5; it++) copy_seg(out, in, n, 1); _mm_sfence(); double tcp = (now_sec() - t) / 5;
    t = now_sec(); for (int it = 0; it < 5; it++) memcpy(out, in, 16 * n); double tmc = (now_sec() - t) / 5;
    // leaf FFT costs on buffers only (in-cache): column child N1 x Bc, row child N2 x G
    int64_t ncol = N->N2 / N->Bc, nrow = N->N1 / N->G;
    t = now_sec(); for (int64_t i = 0; i < ncol; i++) rec4_child(N->colc, N->buf, N->buf2); double tcolfft = now_sec() - t;
    t = now_sec(); for (int64_t i = 0; i < nrow; i++) rec4_child(N->rowc, N->buf, N->buf2); double trowfft = now_sec() - t;
    printf("total %.2f ms | copy(NT) %.2f ms (%.1f GB/s r+w) memcpy %.2f ms | colFFTs %.2f ms rowFFTs %.2f ms | other %.2f ms\n",
           tall * 1e3, tcp * 1e3, 32.0 * n / tcp / 1e9, tmc * 1e3, tcolfft * 1e3, trowfft * 1e3, (tall - tcolfft - trowfft) * 1e3);
    printf("flops-rate of in-cache FFT parts: %.1f GF\n", 5.0 * n * log2(n) / (tcolfft + trowfft) / 1e9);
    memset(rp_t, 0, sizeof rp_t);
    rec4_plan_exec(P, in, out, 1);
    const char *nm[6] = {"gatherA", "fftA", "twid+scatterA", "gatherB(T)", "fftB", "scatterB"};
    for (int i = 0; i < 6; i++) printf("  %-14s %7.2f ms\n", nm[i], rp_t[i] * 1e3);
    return 0;
}
