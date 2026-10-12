// SPDX-License-Identifier: GPL-2.0-or-later
// Strided gather from a 2^24-complex input viewed as N1 x N2 (row stride = N2*16 B, a power of two):
// bandwidth of reading `seg` bytes per row into a contiguous staging buffer, for growing seg.
// Answers: how wide must a column super-strip be for the gather to stream at near-sequential speed?
// $BENCH_NO_THP=1: standard 4 KB pages (prctl PR_SET_THP_DISABLE), to separate DRAM-row from TLB effects.
// Optional third argument: extra bytes added to the row stride (a non-power-of-two stride breaks the cache-set
// and DRAM-bank aliasing of a power-of-two stride, which huge pages preserve in the physical address).
// $GATHER_PF=nta|t0|t1|t2 with $GATHER_PFD=D (rows, default 8): software-prefetch the segment of row r+D
// before copying row r, with that hint (nta fills L1 and the LLC but not L2, so the L2 streamer may not train).
#include <sys/prctl.h>
#include <immintrin.h>
#include "../common/common.h"
int main(int argc, char **argv) {
    if (getenv("BENCH_NO_THP") && *getenv("BENCH_NO_THP") == '1') prctl(PR_SET_THP_DISABLE, 1, 0, 0, 0);
    int64_t N1 = argc > 1 ? atoll(argv[1]) : 4096, N2 = argc > 2 ? atoll(argv[2]) : 4096;
    size_t pad = argc > 3 ? (size_t)atoll(argv[3]) : 0;
    size_t rowb = (size_t)N2 * 16, stride = rowb + pad, total = (size_t)N1 * rowb;
    char *a = xmalloc((size_t)N1 * stride); memset(a, 1, (size_t)N1 * stride);
    char *buf = xmalloc((size_t)N1 * 8192);
    const char *pfm = getenv("GATHER_PF");
    const int pfh = !pfm ? -1 : !strcmp(pfm, "nta") ? 0 : !strcmp(pfm, "t0") ? 1 : !strcmp(pfm, "t1") ? 2 : 3;
    const int64_t D = getenv("GATHER_PFD") ? atoll(getenv("GATHER_PFD")) : 8;
    for (size_t seg = 128; seg <= 8192; seg *= 2) {
        double best = 1e9;
        for (int it = 0; it < 3; it++) {
            double t = now_sec();
            for (size_t c = 0; c < rowb; c += seg) {
                if (pfh < 0)
                    for (int64_t r = 0; r < N1; r++) memcpy(buf + r * seg, a + r * stride + c, seg);
                else
                    for (int64_t r = 0; r < N1; r++) {
                        if (r + D < N1) {
                            const char *q = a + (r + D) * stride + c;
                            for (size_t l = 0; l < seg; l += 64)
                                switch (pfh) {
                                case 0: _mm_prefetch(q + l, _MM_HINT_NTA); break;
                                case 1: _mm_prefetch(q + l, _MM_HINT_T0); break;
                                case 2: _mm_prefetch(q + l, _MM_HINT_T1); break;
                                default: _mm_prefetch(q + l, _MM_HINT_T2);
                                }
                        }
                        memcpy(buf + r * seg, a + r * stride + c, seg);
                    }
                asm volatile("" ::: "memory");
            }
            t = now_sec() - t; if (t < best) best = t;
        }
        printf("N1=%ld seg=%5zu B (staging %6.2f MB): %6.2f GB/s\n", (long)N1, seg, N1 * seg / 1048576.0, total / best / 1e9);
    }
    double t = now_sec(); memcpy(buf, a, (size_t)N1 * 8192 < total ? (size_t)N1 * 8192 : total); (void)t;
    return 0;
}
