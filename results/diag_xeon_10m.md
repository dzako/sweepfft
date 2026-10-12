# Why pmfft was slow at n = 10^7 on the Xeon Gold 6234 (2026-10-12)

**Symptom.** In the five-machine run, pmfft and pmfft_heur at 10^7 ran at 1.41 GFlop/s (818–823 ms in every
round), 0.22× MKL. Other sizes with large powers of five ran normally (10^6, 6553600). On the i7, 10^7 ran at
120 ms. All six candidate plans were slow on the Xeon, so the cause had to be something they share.

**Cause.** `rec4_choose_n1` picks the most balanced split, 10^7 = 3125 × 3200. N1 = 3125 is odd, so the step-B
strip width G falls from 8 to 1. Each output segment is then a single complex number (16 B), written with a
non-temporal store, at a stride of N1 × 16 B = 50 kB. Each store fills a quarter of a cache line, and the rest
of the line is written by other rows much later. Write combining cannot merge these, so every partial line
costs a memory transaction.

Phase times from `csrc/tests/prof_rec4.c`, n = 10^7, single core:

| split | machine | total | output scatter (step B) |
|---|---|---|---|
| 3125 × 3200 (G = 1), NT stores | Xeon Gold 6234 | 864–1072 ms | 739–945 ms |
| 3125 × 3200 (G = 1), ordinary stores | Xeon Gold 6234 | 314 ms | 188 ms |
| 5000 × 2000 (G = 8) | Xeon Gold 6234 | 164 ms | 26 ms |
| 3125 × 3200 (G = 1), NT stores | i7-13700H | 117–350 ms | 47–249 ms |
| 3125 × 3200 (G = 1), ordinary stores | i7-13700H | 119–122 ms | 46–48 ms |
| 5000 × 2000 (G = 8) | i7-13700H | 70 ms | – |

The penalty is 28× on the server part and erratic on both machines.

**Fixes** (`csrc/dft/rec4.h`):
1. `rec4_choose_n1` penalises splits whose factors are not multiples of the strip width (8 / Bt complex), so
   both passes keep full 128-byte strips. 10^7 now splits as 5000 × 2000.
2. Segments shorter than a cache line are written with ordinary stores instead of non-temporal ones. This is
   a safety net for sizes that have no aligned split.

**Result.**

| n = 10^7 | before | after | MKL |
|---|---|---|---|
| Xeon Gold 6234 | 820 ms (0.22× MKL) | 160 ms (**1.12× MKL**) | 180 ms |
| i7-13700H | 120 ms | 75 ms (1.6× faster) | |

- No other size tested changed by more than ±5% (10^6 to 2^26 on the i7; 10^6 and 6553600 on the Xeon).
- The quick correctness suite passes, and the maximum error at 10^7 is 4.6·10⁻¹⁶.
- The five-machine data in `results/machines/` predate this fix; only sizes whose balanced split has an
  odd or non-multiple-of-8 factor are affected.
- The unbatched ablation cells (Bc = G = 1) now use ordinary stores where they used 16-byte non-temporal ones.
