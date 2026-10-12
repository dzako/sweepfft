# Planning and memory overhead (`scripts/overhead.py`)

3 rounds, one fresh process per run; medians over rounds. Total time T(R) = planning + the first R calls, measured up to R = 2^20: 500, 3·2^20: 100, 2^22: 100, 2^24: 20, 2^26: 5 calls and extrapolated with the steady-state median beyond. † = FFTW's planner hit its time limit.

## Setup and per-call cost

| n | impl | library init (s) | planning (s) | first call (ms) | steady call (ms) | first / steady | planner candidates / timed transforms |
|---|---|---|---|---|---|---|---|
| 2^20 | SweepFFT | 0.000 | 1.436 | 14.68 | 12.47 | 1.18 | 7 / 70 |
| 2^20 | SweepFFT (rule) | 0.000 | 0.005 | 17.58 | 12.49 | 1.41 | – |
| 2^20 | MKL | 0.002 | 0.002 | 14.16 | 11.66 | 1.21 | – |
| 2^20 | FFTW MEASURE+wisdom | 0.003 | 0.001 | 16.43 | 13.90 | 1.18 | – |
| 2^20 | FFTW MEASURE fresh | 0.020 | 4.901 | 22.07 | 14.01 | 1.58 | – |
| 2^20 | FFTW ESTIMATE | 0.001 | 0.002 | 22.47 | 21.46 | 1.05 | – |
| 2^20 | ducc0 | 0.000 | 0.000 | 33.41 | 27.22 | 1.23 | – |
| 3·2^20 | SweepFFT | 0.000 | 1.098 | 46.21 | 44.19 | 1.05 | 5 / 20 |
| 3·2^20 | SweepFFT (rule) | 0.000 | 0.012 | 56.33 | 44.19 | 1.27 | – |
| 3·2^20 | MKL | 0.002 | 0.002 | 50.19 | 50.16 | 1.00 | – |
| 3·2^20 | FFTW MEASURE+wisdom | 0.003 | 0.040 | 63.52 | 63.05 | 1.01 | – |
| 3·2^20 | FFTW MEASURE fresh † | 0.020 | 60.090 | 62.34 | 61.29 | 1.02 | – |
| 3·2^20 | FFTW ESTIMATE | 0.001 | 0.009 | 61.67 | 61.33 | 1.01 | – |
| 3·2^20 | ducc0 | 0.000 | 0.000 | 155.59 | 137.21 | 1.13 | – |
| 2^22 | SweepFFT | 0.000 | 2.362 | 61.88 | 60.02 | 1.03 | 6 / 24 |
| 2^22 | SweepFFT (rule) | 0.000 | 0.016 | 75.94 | 60.18 | 1.26 | – |
| 2^22 | MKL | 0.002 | 0.002 | 66.50 | 67.35 | 0.99 | – |
| 2^22 | FFTW MEASURE+wisdom | 0.003 | 0.002 | 88.60 | 88.13 | 1.01 | – |
| 2^22 | FFTW MEASURE fresh | 0.020 | 25.591 | 89.72 | 85.41 | 1.05 | – |
| 2^22 | FFTW ESTIMATE | 0.001 | 0.003 | 161.65 | 166.13 | 0.97 | – |
| 2^22 | ducc0 | 0.000 | 0.000 | 207.90 | 188.97 | 1.10 | – |
| 2^24 | SweepFFT | 0.000 | 14.198 | 280.32 | 279.11 | 1.00 | 8 / 32 |
| 2^24 | SweepFFT (rule) | 0.000 | 0.061 | 335.31 | 277.85 | 1.21 | – |
| 2^24 | MKL | 0.002 | 0.002 | 334.30 | 336.44 | 0.99 | – |
| 2^24 | FFTW MEASURE+wisdom | 0.003 | 0.001 | 391.70 | 393.40 | 1.00 | – |
| 2^24 | FFTW MEASURE fresh † | 0.020 | 60.341 | 807.22 | 804.75 | 1.00 | – |
| 2^24 | FFTW ESTIMATE | 0.001 | 0.003 | 805.42 | 804.69 | 1.00 | – |
| 2^24 | ducc0 | 0.000 | 0.000 | 884.22 | 789.00 | 1.12 | – |
| 2^26 | SweepFFT | 0.000 | 61.895 | 1284.11 | 1282.73 | 1.00 | 8 / 32 |
| 2^26 | SweepFFT (rule) | 0.000 | 0.238 | 1548.01 | 1318.77 | 1.17 | – |
| 2^26 | MKL | 0.002 | 0.003 | 1550.41 | 1548.67 | 1.00 | – |
| 2^26 | FFTW MEASURE+wisdom | 0.003 | 0.001 | 1648.26 | 1651.01 | 1.00 | – |
| 2^26 | FFTW MEASURE fresh † | 0.020 | 61.907 | 3702.37 | 3698.05 | 1.00 | – |
| 2^26 | FFTW ESTIMATE | 0.001 | 0.003 | 3630.65 | 3627.93 | 1.00 | – |
| 2^26 | ducc0 | 0.000 | 0.000 | 3851.18 | 3430.09 | 1.12 | – |

## Total time T(R) for R repeated transforms (s), planning included, library already initialised

| n | impl | R=1 | R=2 | R=10 | R=100 | R=1,000 | R=10,000 |
|---|---|---|---|---|---|---|---|
| 2^20 | SweepFFT | 1.45 | 1.46 | 1.57 | 2.74 | 14.1 | 127 |
| 2^20 | SweepFFT (rule) | 0.0225 | 0.0353 | 0.134 | 1.24 | 12.5 | 125 |
| 2^20 | MKL | 0.0158 | 0.028 | 0.121 | 1.17 | 11.7 | 117 |
| 2^20 | FFTW MEASURE+wisdom | 0.017 | 0.0322 | 0.145 | 1.4 | 13.9 | 139 |
| 2^20 | FFTW MEASURE fresh | 4.92 | 4.94 | 5.05 | 6.29 | 18.9 | 145 |
| 2^20 | FFTW ESTIMATE | 0.0254 | 0.0476 | 0.219 | 2.16 | 21.5 | 215 |
| 2^20 | ducc0 | 0.0335 | 0.0615 | 0.282 | 2.74 | 27.2 | 272 |
| 3·2^20 | SweepFFT | 1.14 | 1.19 | 1.55 | 5.59 | 45.4 | 443 |
| 3·2^20 | SweepFFT (rule) | 0.0687 | 0.113 | 0.465 | 4.43 | 44.2 | 442 |
| 3·2^20 | MKL | 0.0519 | 0.101 | 0.499 | 5.01 | 50.1 | 501 |
| 3·2^20 | FFTW MEASURE+wisdom | 0.104 | 0.167 | 0.671 | 6.35 | 63.1 | 631 |
| 3·2^20 | FFTW MEASURE fresh | 60.2 | 60.2 | 60.7 | 66.2 | 122 | 673 |
| 3·2^20 | FFTW ESTIMATE | 0.071 | 0.132 | 0.622 | 6.14 | 61.3 | 613 |
| 3·2^20 | ducc0 | 0.156 | 0.295 | 1.41 | 13.9 | 138 | 1.37e+03 |
| 2^22 | SweepFFT | 2.42 | 2.49 | 2.97 | 8.42 | 62.5 | 603 |
| 2^22 | SweepFFT (rule) | 0.0922 | 0.152 | 0.633 | 6.05 | 60.2 | 602 |
| 2^22 | MKL | 0.0682 | 0.134 | 0.668 | 6.72 | 67.3 | 673 |
| 2^22 | FFTW MEASURE+wisdom | 0.0902 | 0.179 | 0.882 | 8.82 | 88.1 | 881 |
| 2^22 | FFTW MEASURE fresh | 25.7 | 25.8 | 26.5 | 34.1 | 111 | 880 |
| 2^22 | FFTW ESTIMATE | 0.164 | 0.326 | 1.63 | 16.6 | 166 | 1.66e+03 |
| 2^22 | ducc0 | 0.208 | 0.395 | 1.89 | 18.8 | 189 | 1.89e+03 |
| 2^24 | SweepFFT | 14.5 | 14.8 | 17 | 42.1 | 293 | 2.81e+03 |
| 2^24 | SweepFFT (rule) | 0.397 | 0.674 | 2.9 | 27.9 | 278 | 2.78e+03 |
| 2^24 | MKL | 0.336 | 0.67 | 3.36 | 33.6 | 336 | 3.36e+03 |
| 2^24 | FFTW MEASURE+wisdom | 0.393 | 0.785 | 3.93 | 39.3 | 393 | 3.93e+03 |
| 2^24 | FFTW MEASURE fresh | 61.1 | 61.9 | 68.4 | 141 | 867 | 8.11e+03 |
| 2^24 | FFTW ESTIMATE | 0.808 | 1.61 | 8.05 | 80.5 | 805 | 8.05e+03 |
| 2^24 | ducc0 | 0.884 | 1.67 | 7.98 | 79 | 789 | 7.89e+03 |
| 2^26 | SweepFFT | 63.2 | 64.5 | 74.7 | 190 | 1.34e+03 | 1.29e+04 |
| 2^26 | SweepFFT (rule) | 1.79 | 3.11 | 13.7 | 132 | 1.32e+03 | 1.32e+04 |
| 2^26 | MKL | 1.55 | 3.1 | 15.5 | 155 | 1.55e+03 | 1.55e+04 |
| 2^26 | FFTW MEASURE+wisdom | 1.65 | 3.3 | 16.5 | 165 | 1.65e+03 | 1.65e+04 |
| 2^26 | FFTW MEASURE fresh | 65.6 | 69.3 | 98.8 | 431 | 3.76e+03 | 3.7e+04 |
| 2^26 | FFTW ESTIMATE | 3.63 | 7.26 | 36.3 | 363 | 3.63e+03 | 3.63e+04 |
| 2^26 | ducc0 | 3.85 | 7.29 | 34.8 | 343 | 3.43e+03 | 3.43e+04 |

## Break-even reuse count R* for SweepFFT vs each baseline

Smallest number of transforms after which SweepFFT (planning included) has spent less total time than the baseline; closed form R* = (P_s − P_b) / (t_b − t_s), P = planning + first-call excess. "always": SweepFFT is ahead from the first transform; "never": the baseline's steady state is faster. In a running process (library initialised) / in a new process (initialisation included).

**SweepFFT**

| n | MKL | FFTW MEASURE+wisdom | FFTW MEASURE fresh | FFTW ESTIMATE | ducc0 |
|---|---|---|---|---|---|
| 2^20 | never / never | 1,004 / 1,003 | 1 (always) / 1 (always) | 160 / 160 | 98 / 98 |
| 3·2^20 | 184 / 184 | 57 / 56 | 1 (always) / 1 (always) † | 64 / 64 | 12 / 12 |
| 2^22 | 323 / 323 | 85 / 84 | 1 (always) / 1 (always) | 23 / 23 | 19 / 19 |
| 2^24 | 248 / 248 | 125 / 125 | 1 (always) / 1 (always) † | 28 / 28 | 28 / 28 |
| 2^26 | 233 / 233 | 169 / 169 | 1 (always) / 1 (always) † | 27 / 27 | 29 / 29 |

**SweepFFT (rule)**

| n | MKL | FFTW MEASURE+wisdom | FFTW MEASURE fresh | FFTW ESTIMATE | ducc0 |
|---|---|---|---|---|---|
| 2^20 | never / never | 5 / 3 | 1 (always) / 1 (always) | 1 (always) / 1 (always) | 1 (always) / 1 (always) |
| 3·2^20 | 4 / 4 | 1 (always) / 1 (always) | 1 (always) / 1 (always) † | 1 (always) / 1 (always) | 1 (always) / 1 (always) |
| 2^22 | 5 / 5 | 2 / 1 (always) | 1 (always) / 1 (always) | 1 (always) / 1 (always) | 1 (always) / 1 (always) |
| 2^24 | 3 / 2 | 2 / 2 | 1 (always) / 1 (always) † | 1 (always) / 1 (always) | 1 (always) / 1 (always) |
| 2^26 | 3 / 3 | 2 / 2 | 1 (always) / 1 (always) † | 1 (always) / 1 (always) | 1 (always) / 1 (always) |

## Memory beyond the 32 n bytes of input and output (MB; in sweeps S = 16 n bytes)

after planning = resident memory the plan holds; planning peak = peak during planning and the first call; execution scratch = extra resident peak during the first call; steady = after the first call.

| n | impl | after planning | planning peak | execution scratch | steady |
|---|---|---|---|---|---|
| 2^20 | SweepFFT | 17 (1.03) | 97 (6.07) | 0 (0.00) | 17 (1.04) |
| 2^20 | SweepFFT (rule) | 0 (0.01) | 17 (1.03) | 16 (1.02) | 17 (1.04) |
| 2^20 | MKL | 1 (0.05) | 1 (0.09) | 0 (0.03) | 1 (0.09) |
| 2^20 | FFTW MEASURE+wisdom | 0 (0.01) | 0 (0.03) | 0 (0.02) | 0 (0.02) |
| 2^20 | FFTW MEASURE fresh | 0 (0.01) | 34 (2.12) | 0 (0.02) | 0 (0.02) |
| 2^20 | FFTW ESTIMATE | 0 (0.00) | 0 (0.02) | 0 (0.01) | 0 (0.01) |
| 2^20 | ducc0 | 0 (0.00) | 16 (1.01) | 16 (1.01) | 16 (1.01) |
| 3·2^20 | SweepFFT | 49 (1.02) | 202 (4.21) | 0 (0.00) | 49 (1.02) |
| 3·2^20 | SweepFFT (rule) | 0 (0.01) | 49 (1.02) | 49 (1.01) | 49 (1.02) |
| 3·2^20 | MKL | 1 (0.02) | 2 (0.03) | 1 (0.01) | 2 (0.03) |
| 3·2^20 | FFTW MEASURE+wisdom | 27 (0.57) | 27 (0.57) | 0 (0.00) | 28 (0.57) |
| 3·2^20 | FFTW MEASURE fresh | 6 (0.13) | 111 (2.32) | 0 (0.00) | 6 (0.13) |
| 3·2^20 | FFTW ESTIMATE | 6 (0.13) | 6 (0.13) | 0 (0.00) | 6 (0.13) |
| 3·2^20 | ducc0 | 0 (0.00) | 48 (1.01) | 48 (1.00) | 48 (1.01) |
| 2^22 | SweepFFT | 65 (1.02) | 385 (6.02) | 0 (0.00) | 65 (1.02) |
| 2^22 | SweepFFT (rule) | 0 (0.01) | 65 (1.02) | 65 (1.01) | 65 (1.02) |
| 2^22 | MKL | 1 (0.01) | 1 (0.02) | 1 (0.01) | 1 (0.02) |
| 2^22 | FFTW MEASURE+wisdom | 1 (0.01) | 1 (0.01) | 0 (0.00) | 1 (0.01) |
| 2^22 | FFTW MEASURE fresh | 0 (0.01) | 131 (2.05) | 1 (0.01) | 1 (0.01) |
| 2^22 | FFTW ESTIMATE | 0 (0.00) | 0 (0.01) | 0 (0.00) | 0 (0.00) |
| 2^22 | ducc0 | 0 (0.00) | 64 (1.01) | 64 (1.01) | 64 (1.01) |
| 2^24 | SweepFFT | 258 (1.01) | 1538 (6.01) | 0 (0.00) | 258 (1.01) |
| 2^24 | SweepFFT (rule) | 1 (0.00) | 258 (1.01) | 257 (1.00) | 258 (1.01) |
| 2^24 | MKL | 1 (0.00) | 2 (0.01) | 1 (0.00) | 2 (0.01) |
| 2^24 | FFTW MEASURE+wisdom | 1 (0.00) | 1 (0.00) | 1 (0.00) | 1 (0.00) |
| 2^24 | FFTW MEASURE fresh | 0 (0.00) | 515 (2.01) | 0 (0.00) | 0 (0.00) |
| 2^24 | FFTW ESTIMATE | 0 (0.00) | 1 (0.00) | 1 (0.00) | 0 (0.00) |
| 2^24 | ducc0 | 0 (0.00) | 257 (1.00) | 257 (1.00) | 257 (1.00) |
| 2^26 | SweepFFT | 1037 (1.01) | 6155 (6.01) | 0 (0.00) | 1037 (1.01) |
| 2^26 | SweepFFT (rule) | 1 (0.00) | 1037 (1.01) | 1036 (1.01) | 1037 (1.01) |
| 2^26 | MKL | 1 (0.00) | 3 (0.00) | 1 (0.00) | 3 (0.00) |
| 2^26 | FFTW MEASURE+wisdom | 1 (0.00) | 9 (0.01) | 8 (0.01) | 1 (0.00) |
| 2^26 | FFTW MEASURE fresh | 0 (0.00) | 2051 (2.00) | 1 (0.00) | 0 (0.00) |
| 2^26 | FFTW ESTIMATE | 0 (0.00) | 1 (0.00) | 1 (0.00) | 0 (0.00) |
| 2^26 | ducc0 | 0 (0.00) | 1026 (1.00) | 1025 (1.00) | 1025 (1.00) |
