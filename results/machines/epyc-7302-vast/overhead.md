# Planning and memory overhead (`scripts/overhead.py`)

3 rounds, one fresh process per run; medians over rounds. Total time T(R) = planning + the first R calls, measured up to R = 2^20: 200, 3·2^20: 20, 2^22: 20, 2^24: 5, 2^26: 2 calls and extrapolated with the steady-state median beyond. † = FFTW's planner hit its time limit.

## Setup and per-call cost

| n | impl | library init (s) | planning (s) | first call (ms) | steady call (ms) | first / steady | planner candidates / timed transforms |
|---|---|---|---|---|---|---|---|
| 2^20 | SweepFFT | 0.000 | 3.747 | 10.64 | 10.45 | 1.02 | 7 / 70 |
| 2^20 | SweepFFT (rule) | 0.000 | 0.004 | 14.57 | 12.29 | 1.19 | – |
| 2^20 | MKL | 0.003 | 0.011 | 13.63 | 13.49 | 1.01 | – |
| 2^20 | FFTW MEASURE+wisdom | 0.003 | 0.001 | 14.80 | 14.43 | 1.03 | – |
| 2^20 | FFTW MEASURE fresh | 0.020 | 4.780 | 14.76 | 14.44 | 1.02 | – |
| 2^20 | FFTW ESTIMATE | 0.001 | 0.002 | 56.56 | 56.41 | 1.00 | – |
| 2^20 | ducc0 | 0.000 | 0.000 | 28.59 | 18.13 | 1.58 | – |
| 3·2^20 | SweepFFT | 0.000 | 1.019 | 36.84 | 36.80 | 1.00 | 5 / 20 |
| 3·2^20 | SweepFFT (rule) | 0.000 | 0.009 | 42.58 | 36.92 | 1.15 | – |
| 3·2^20 | MKL | 0.004 | 0.080 | 145.59 | 145.67 | 1.00 | – |
| 3·2^20 | FFTW MEASURE+wisdom | 0.004 | 0.043 | 38.35 | 38.70 | 0.99 | – |
| 3·2^20 | FFTW MEASURE fresh † | 0.019 | 60.073 | 519.77 | 520.13 | 1.00 | – |
| 3·2^20 | FFTW ESTIMATE | 0.001 | 0.011 | 518.10 | 517.88 | 1.00 | – |
| 3·2^20 | ducc0 | 0.000 | 0.000 | 115.39 | 89.46 | 1.29 | – |
| 2^22 | SweepFFT | 0.000 | 2.354 | 51.41 | 50.89 | 1.01 | 6 / 24 |
| 2^22 | SweepFFT (rule) | 0.000 | 0.012 | 58.04 | 50.73 | 1.14 | – |
| 2^22 | MKL | 0.004 | 0.045 | 84.02 | 83.70 | 1.00 | – |
| 2^22 | FFTW MEASURE+wisdom | 0.003 | 0.001 | 79.82 | 79.18 | 1.01 | – |
| 2^22 | FFTW MEASURE fresh | 0.019 | 18.695 | 79.52 | 79.01 | 1.01 | – |
| 2^22 | FFTW ESTIMATE | 0.001 | 0.002 | 673.45 | 671.82 | 1.00 | – |
| 2^22 | ducc0 | 0.000 | 0.000 | 154.11 | 119.25 | 1.29 | – |
| 2^24 | SweepFFT | 0.000 | 17.953 | 228.93 | 226.74 | 1.01 | 8 / 32 |
| 2^24 | SweepFFT (rule) | 0.000 | 0.044 | 256.98 | 229.25 | 1.12 | – |
| 2^24 | MKL | 0.003 | 0.226 | 358.47 | 356.69 | 1.00 | – |
| 2^24 | FFTW MEASURE+wisdom | 0.003 | 0.001 | 337.61 | 336.55 | 1.00 | – |
| 2^24 | FFTW MEASURE fresh † | 0.020 | 60.386 | 2531.61 | 2531.40 | 1.00 | – |
| 2^24 | FFTW ESTIMATE | 0.001 | 0.002 | 2544.83 | 2543.91 | 1.00 | – |
| 2^24 | ducc0 | 0.000 | 0.000 | 647.94 | 501.25 | 1.29 | – |
| 2^26 | SweepFFT | 0.000 | 73.319 | 932.41 | 927.28 | 1.01 | 8 / 32 |
| 2^26 | SweepFFT (rule) | 0.000 | 0.166 | 1038.65 | 920.10 | 1.13 | – |
| 2^26 | MKL | 0.004 | 0.943 | 1678.35 | 1585.53 | 1.06 | – |
| 2^26 | FFTW MEASURE+wisdom | 0.003 | 0.003 | 1550.17 | 1550.38 | 1.00 | – |
| 2^26 | FFTW MEASURE fresh † | 0.020 | 60.835 | 7190.34 | 7182.56 | 1.00 | – |
| 2^26 | FFTW ESTIMATE | 0.001 | 0.003 | 7188.07 | 7188.89 | 1.00 | – |
| 2^26 | ducc0 | 0.000 | 0.001 | 2828.91 | 2158.95 | 1.31 | – |

## Total time T(R) for R repeated transforms (s), planning included, library already initialised

| n | impl | R=1 | R=2 | R=10 | R=100 | R=1,000 | R=10,000 |
|---|---|---|---|---|---|---|---|
| 2^20 | SweepFFT | 3.76 | 3.77 | 3.85 | 4.79 | 14.2 | 108 |
| 2^20 | SweepFFT (rule) | 0.0183 | 0.0306 | 0.129 | 1.24 | 12.3 | 123 |
| 2^20 | MKL | 0.0246 | 0.0381 | 0.146 | 1.36 | 13.5 | 135 |
| 2^20 | FFTW MEASURE+wisdom | 0.0158 | 0.0303 | 0.146 | 1.45 | 14.4 | 144 |
| 2^20 | FFTW MEASURE fresh | 4.79 | 4.81 | 4.92 | 6.23 | 19.2 | 149 |
| 2^20 | FFTW ESTIMATE | 0.0585 | 0.115 | 0.567 | 5.66 | 56.4 | 564 |
| 2^20 | ducc0 | 0.0287 | 0.0469 | 0.193 | 1.83 | 18.3 | 181 |
| 3·2^20 | SweepFFT | 1.06 | 1.09 | 1.39 | 4.7 | 37.8 | 369 |
| 3·2^20 | SweepFFT (rule) | 0.0517 | 0.0886 | 0.383 | 3.7 | 36.9 | 369 |
| 3·2^20 | MKL | 0.225 | 0.371 | 1.54 | 14.7 | 146 | 1.46e+03 |
| 3·2^20 | FFTW MEASURE+wisdom | 0.0817 | 0.12 | 0.427 | 3.9 | 38.6 | 387 |
| 3·2^20 | FFTW MEASURE fresh | 60.6 | 61.1 | 65.2 | 112 | 580 | 5.26e+03 |
| 3·2^20 | FFTW ESTIMATE | 0.529 | 1.05 | 5.21 | 51.8 | 518 | 5.18e+03 |
| 3·2^20 | ducc0 | 0.115 | 0.205 | 0.915 | 9.01 | 89.5 | 895 |
| 2^22 | SweepFFT | 2.41 | 2.46 | 2.87 | 7.48 | 53.3 | 511 |
| 2^22 | SweepFFT (rule) | 0.0702 | 0.121 | 0.527 | 5.1 | 50.7 | 507 |
| 2^22 | MKL | 0.13 | 0.213 | 0.882 | 8.46 | 83.8 | 837 |
| 2^22 | FFTW MEASURE+wisdom | 0.081 | 0.16 | 0.796 | 7.93 | 79.2 | 792 |
| 2^22 | FFTW MEASURE fresh | 18.8 | 18.9 | 19.5 | 26.6 | 97.9 | 809 |
| 2^22 | FFTW ESTIMATE | 0.676 | 1.35 | 6.73 | 67.2 | 672 | 6.72e+03 |
| 2^22 | ducc0 | 0.154 | 0.273 | 1.23 | 12.1 | 119 | 1.19e+03 |
| 2^24 | SweepFFT | 18.2 | 18.4 | 20.2 | 40.6 | 245 | 2.29e+03 |
| 2^24 | SweepFFT (rule) | 0.301 | 0.532 | 2.37 | 23 | 229 | 2.29e+03 |
| 2^24 | MKL | 0.584 | 0.941 | 3.84 | 36.1 | 357 | 3.57e+03 |
| 2^24 | FFTW MEASURE+wisdom | 0.339 | 0.679 | 3.37 | 33.7 | 337 | 3.37e+03 |
| 2^24 | FFTW MEASURE fresh | 62.9 | 65.5 | 85.8 | 314 | 2.59e+03 | 2.54e+04 |
| 2^24 | FFTW ESTIMATE | 2.55 | 5.09 | 25.4 | 254 | 2.54e+03 | 2.54e+04 |
| 2^24 | ducc0 | 0.648 | 1.15 | 5.25 | 50.5 | 502 | 5.01e+03 |
| 2^26 | SweepFFT | 74.3 | 75.2 | 82.6 | 166 | 1e+03 | 9.35e+03 |
| 2^26 | SweepFFT (rule) | 1.2 | 2.13 | 9.53 | 92.4 | 920 | 9.2e+03 |
| 2^26 | MKL | 2.62 | 4.3 | 17.2 | 160 | 1.59e+03 | 1.59e+04 |
| 2^26 | FFTW MEASURE+wisdom | 1.55 | 3.1 | 15.5 | 155 | 1.55e+03 | 1.55e+04 |
| 2^26 | FFTW MEASURE fresh | 68 | 75.2 | 133 | 779 | 7.24e+03 | 7.19e+04 |
| 2^26 | FFTW ESTIMATE | 7.19 | 14.4 | 71.9 | 719 | 7.19e+03 | 7.19e+04 |
| 2^26 | ducc0 | 2.83 | 5.17 | 22.5 | 217 | 2.16e+03 | 2.16e+04 |

## Break-even reuse count R* for SweepFFT vs each baseline

Smallest number of transforms after which SweepFFT (planning included) has spent less total time than the baseline; closed form R* = (P_s − P_b) / (t_b − t_s), P = planning + first-call excess. "always": SweepFFT is ahead from the first transform; "never": the baseline's steady state is faster. In a running process (library initialised) / in a new process (initialisation included).

**SweepFFT**

| n | MKL | FFTW MEASURE+wisdom | FFTW MEASURE fresh | FFTW ESTIMATE | ducc0 |
|---|---|---|---|---|---|
| 2^20 | 1,228 / 1,227 | 942 / 942 | 1 (always) / 1 (always) | 82 / 82 | 487 / 487 |
| 3·2^20 | 9 / 9 | 515 / 513 | 1 (always) / 1 (always) † | 3 / 3 | 19 / 19 |
| 2^22 | 71 / 71 | 84 / 84 | 1 (always) / 1 (always) | 4 / 4 | 34 / 34 |
| 2^24 | 137 / 137 | 164 / 164 | 1 (always) / 1 (always) † | 8 / 8 | 65 / 65 |
| 2^26 | 110 / 110 | 118 / 118 | 2 / 2 † | 12 / 12 | 59 / 59 |

**SweepFFT (rule)**

| n | MKL | FFTW MEASURE+wisdom | FFTW MEASURE fresh | FFTW ESTIMATE | ducc0 |
|---|---|---|---|---|---|
| 2^20 | 1 (always) / 1 (always) | 3 / 1 (always) | 1 (always) / 1 (always) | 1 (always) / 1 (always) | 1 (always) / 1 (always) |
| 3·2^20 | 1 (always) / 1 (always) | 1 (always) / 1 (always) | 1 (always) / 1 (always) † | 1 (always) / 1 (always) | 1 (always) / 1 (always) |
| 2^22 | 1 (always) / 1 (always) | 1 (always) / 1 (always) | 1 (always) / 1 (always) | 1 (always) / 1 (always) | 1 (always) / 1 (always) |
| 2^24 | 1 (always) / 1 (always) | 1 (always) / 1 (always) | 1 (always) / 1 (always) † | 1 (always) / 1 (always) | 1 (always) / 1 (always) |
| 2^26 | 1 (always) / 1 (always) | 1 (always) / 1 (always) | 1 (always) / 1 (always) † | 1 (always) / 1 (always) | 1 (always) / 1 (always) |

## Memory beyond the 32 n bytes of input and output (MB; in sweeps S = 16 n bytes)

after planning = resident memory the plan holds; planning peak = peak during planning and the first call; execution scratch = extra resident peak during the first call; steady = after the first call.

| n | impl | after planning | planning peak | execution scratch | steady |
|---|---|---|---|---|---|
| 2^20 | SweepFFT | 17 (1.04) | 97 (6.06) | 0 (0.00) | 17 (1.05) |
| 2^20 | SweepFFT (rule) | 0 (0.01) | 17 (1.03) | 16 (1.02) | 17 (1.04) |
| 2^20 | MKL | 8 (0.50) | 10 (0.62) | 0 (0.01) | 8 (0.52) |
| 2^20 | FFTW MEASURE+wisdom | 0 (0.02) | 0 (0.03) | 0 (0.01) | 0 (0.03) |
| 2^20 | FFTW MEASURE fresh | 0 (0.01) | 34 (2.12) | 0 (0.01) | 0 (0.02) |
| 2^20 | FFTW ESTIMATE | 0 (0.00) | 0 (0.01) | 0 (0.00) | 0 (0.01) |
| 2^20 | ducc0 | 0 (0.00) | 16 (1.02) | 16 (1.01) | 16 (1.01) |
| 3·2^20 | SweepFFT | 49 (1.02) | 202 (4.21) | 0 (0.00) | 49 (1.02) |
| 3·2^20 | SweepFFT (rule) | 0 (0.01) | 49 (1.02) | 49 (1.01) | 49 (1.02) |
| 3·2^20 | MKL | 48 (1.00) | 96 (2.00) | 0 (0.00) | 48 (1.01) |
| 3·2^20 | FFTW MEASURE+wisdom | 24 (0.50) | 24 (0.50) | 0 (0.00) | 24 (0.50) |
| 3·2^20 | FFTW MEASURE fresh | 6 (0.13) | 115 (2.40) | 0 (0.00) | 6 (0.13) |
| 3·2^20 | FFTW ESTIMATE | 6 (0.13) | 6 (0.13) | 0 (0.00) | 6 (0.13) |
| 3·2^20 | ducc0 | 0 (0.00) | 48 (1.01) | 48 (1.00) | 48 (1.01) |
| 2^22 | SweepFFT | 65 (1.02) | 385 (6.02) | 0 (0.00) | 65 (1.02) |
| 2^22 | SweepFFT (rule) | 0 (0.01) | 65 (1.02) | 65 (1.01) | 65 (1.02) |
| 2^22 | MKL | 32 (0.50) | 40 (0.62) | 0 (0.00) | 32 (0.51) |
| 2^22 | FFTW MEASURE+wisdom | 0 (0.01) | 1 (0.01) | 1 (0.01) | 0 (0.01) |
| 2^22 | FFTW MEASURE fresh | 0 (0.00) | 131 (2.05) | 1 (0.01) | 0 (0.01) |
| 2^22 | FFTW ESTIMATE | 0 (0.00) | 0 (0.00) | 0 (0.00) | 0 (0.00) |
| 2^22 | ducc0 | 0 (0.00) | 65 (1.01) | 64 (1.01) | 64 (1.01) |
| 2^24 | SweepFFT | 263 (1.03) | 1544 (6.03) | 0 (0.00) | 264 (1.03) |
| 2^24 | SweepFFT (rule) | 1 (0.00) | 258 (1.01) | 257 (1.00) | 258 (1.01) |
| 2^24 | MKL | 128 (0.50) | 160 (0.62) | 0 (0.00) | 129 (0.50) |
| 2^24 | FFTW MEASURE+wisdom | 0 (0.00) | 2 (0.01) | 2 (0.01) | 0 (0.00) |
| 2^24 | FFTW MEASURE fresh | 0 (0.00) | 517 (2.02) | 1 (0.00) | 0 (0.00) |
| 2^24 | FFTW ESTIMATE | 0 (0.00) | 1 (0.00) | 1 (0.00) | 0 (0.00) |
| 2^24 | ducc0 | 0 (0.00) | 257 (1.00) | 257 (1.00) | 256 (1.00) |
| 2^26 | SweepFFT | 1028 (1.00) | 6148 (6.00) | 0 (0.00) | 1028 (1.00) |
| 2^26 | SweepFFT (rule) | 1 (0.00) | 1037 (1.01) | 1036 (1.01) | 1038 (1.01) |
| 2^26 | MKL | 510 (0.50) | 638 (0.62) | 0 (0.00) | 511 (0.50) |
| 2^26 | FFTW MEASURE+wisdom | 1 (0.00) | 2 (0.00) | 1 (0.00) | 1 (0.00) |
| 2^26 | FFTW MEASURE fresh | 0 (0.00) | 2052 (2.00) | 1 (0.00) | 0 (0.00) |
| 2^26 | FFTW ESTIMATE | 0 (0.00) | 1 (0.00) | 1 (0.00) | 0 (0.00) |
| 2^26 | ducc0 | 0 (0.00) | 1026 (1.00) | 1025 (1.00) | 1025 (1.00) |
