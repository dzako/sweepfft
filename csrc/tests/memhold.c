// SPDX-License-Identifier: GPL-2.0-or-later
// Put the kernel's free memory into a known state and hold it there while another process allocates
// (scripts/frag.py).  Both modes use 4 KB pages (MADV_NOHUGEPAGE) and keep their memory until stdin closes.
//   memhold contig <MB>       take <MB> of the smallest free blocks (the scattered ones the buddy allocator hands
//                             out first), so the next allocations are split from large, physically contiguous blocks
//   memhold frag <MB> <seed>  touch <MB>, then free a random half of its pages, so the next allocations get
//                             scattered single pages
// Prints READY when the state is set.
#define _GNU_SOURCE
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <unistd.h>

int main(int argc, char **argv) {
    if (argc < 3) { fprintf(stderr, "usage: memhold contig|frag <MB> [seed]\n"); return 1; }
    const size_t pg = 4096, bytes = (size_t)atoll(argv[2]) << 20, np = bytes / pg;
    char *a = mmap(NULL, bytes, PROT_READ | PROT_WRITE, MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    if (a == MAP_FAILED) { perror("mmap"); return 1; }
    madvise(a, bytes, MADV_NOHUGEPAGE);
    for (size_t i = 0; i < np; i++) a[i * pg] = 1;
    if (!strcmp(argv[1], "frag")) {
        uint64_t s = argc > 3 ? strtoull(argv[3], NULL, 10) * 2654435761u + 1 : 1;
        for (size_t i = 0; i < np; i++) {
            s ^= s << 13; s ^= s >> 7; s ^= s << 17;
            if (s & 1) madvise(a + i * pg, pg, MADV_DONTNEED);
        }
    }
    printf("READY\n"); fflush(stdout);
    char c;
    while (read(0, &c, 1) > 0) {}
    return 0;
}
