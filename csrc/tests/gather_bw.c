// SPDX-License-Identifier: GPL-2.0-or-later
// Raw strided-gather bandwidth: read `rows` segments of `seg` bytes at stride `stride` (sweeping all columns).
#include "../common/common.h"
int main(void) {
    size_t total = 64u << 20;
    char *a = xmalloc(total + (8u << 20)); memset(a, 1, total + (8u << 20));
    char *buf = xmalloc(4u << 20);
    struct { size_t rows, seg, pad; int pf; } cfg[] = {
        {2048, 128, 0, 0}, {2048, 128, 64, 0}, {2048, 128, 0, 1}, {2048, 128, 64, 1}, {2048, 512, 0, 0}, {2048, 512, 64, 0},
        {256, 1024, 0, 0}, {256, 1024, 64, 0}, {64, 4096, 0, 0}, {64, 4096, 64, 0}, {16, 16384, 0, 0}, {1, 1 << 20, 0, 0}};
    for (size_t c = 0; c < sizeof cfg / sizeof cfg[0]; c++) {
        size_t rows = cfg[c].rows, seg = cfg[c].seg, stride = total / rows + cfg[c].pad, cols = (total / rows) / seg;
        double best = 1e9;
        for (int it = 0; it < 4; it++) {
            double t = now_sec();
            for (size_t col = 0; col < cols; col++) {
                for (size_t r = 0; r < rows; r++) {
                    if (cfg[c].pf && col + 1 < cols) for (size_t l = 0; l < seg; l += 64) _mm_prefetch(a + r * stride + (col + 1) * seg + l, _MM_HINT_T1);
                    memcpy(buf + r * seg, a + r * stride + col * seg, seg);
                }
                asm volatile("" ::: "memory");
            }
            t = now_sec() - t; if (t < best) best = t;
        }
        printf("rows=%5zu seg=%7zu pad=%3zu pf=%d : %6.2f GB/s\n", rows, seg, cfg[c].pad, cfg[c].pf, total / best / 1e9);
    }
}
