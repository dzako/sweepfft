// SPDX-License-Identifier: GPL-2.0-or-later
// Strided gather of 128-byte row segments (N1 x N2 complex input, power-of-two row stride) with software
// prefetch D rows ahead in the same strip.  Tests whether the gather is limited by misses in flight (MLP).
#include "../common/common.h"
static double run(const char *a, char *buf, int64_t N1, size_t rowb, size_t seg, int D, int hint) {
    double best = 1e9;
    for (int it = 0; it < 3; it++) {
        double t = now_sec();
        for (size_t c = 0; c < rowb; c += seg) {
            for (int64_t r = 0; r < N1; r++) {
                if (D) {
                    int64_t rp = r + D; size_t cp = c;
                    if (rp >= N1) { rp -= N1; cp += seg; }
                    if (cp < rowb) {
                        const char *p = a + rp * rowb + cp;
                        for (size_t l = 0; l < seg; l += 64) {
                            if (hint == 0) _mm_prefetch(p + l, _MM_HINT_T0);
                            else if (hint == 1) _mm_prefetch(p + l, _MM_HINT_T1);
                            else if (hint == 2) _mm_prefetch(p + l, _MM_HINT_T2);
                            else _mm_prefetch(p + l, _MM_HINT_NTA);
                        }
                    }
                }
                memcpy(buf + r * seg, a + r * rowb + c, seg);
            }
            asm volatile("" ::: "memory");
        }
        t = now_sec() - t; if (t < best) best = t;
    }
    return (double)N1 * rowb / best / 1e9;
}
int main(int argc, char **argv) {
    int64_t N1 = argc > 1 ? atoll(argv[1]) : 4096, N2 = argc > 2 ? atoll(argv[2]) : 4096;
    size_t rowb = (size_t)N2 * 16, seg = argc > 3 ? atoll(argv[3]) : 128;
    char *a = xmalloc((size_t)N1 * rowb); memset(a, 1, (size_t)N1 * rowb);
    char *buf = xmalloc((size_t)N1 * seg);
    printf("N1=%ld N2=%ld seg=%zu  no-prefetch: %.2f GB/s\n", (long)N1, (long)N2, seg, run(a, buf, N1, rowb, seg, 0, 0));
    const char *hn[] = {"T0", "T1", "T2", "NTA"};
    for (int h = 0; h < 4; h++) {
        printf("  %-3s", hn[h]);
        for (int D = 4; D <= 128; D *= 2) printf("  D=%3d %5.2f", D, run(a, buf, N1, rowb, seg, D, h));
        printf("  GB/s\n");
    }
}
