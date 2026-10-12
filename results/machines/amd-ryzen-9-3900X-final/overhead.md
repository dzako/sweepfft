# Planning and memory overhead (`scripts/overhead.py`)

3 rounds, one fresh process per run; medians over rounds. Total time T(R) = planning + the first R calls, measured up to R = 2^20: 200, 3·2^20: 50, 2^22: 20, 2^24: 10, 2^26: 5 calls and extrapolated with the steady-state median beyond. † = FFTW's planner hit its time limit.

## Setup and per-call cost

| n | impl | library init (s) | planning (s) | first call (ms) | steady call (ms) | first / steady | planner candidates / timed transforms |
|---|---|---|---|---|---|---|---|
| 2^20 | SweepFFT | 0.000 | 2.900 | 8.38 | 8.28 | 1.01 | 7 / 70 |
| 2^20 | SweepFFT (rule) | 0.000 | 0.003 | 11.49 | 9.55 | 1.20 | – |
| 2^20 | MKL | 0.002 | 0.008 | 11.66 | 11.06 | 1.05 | – |
| 2^20 | FFTW MEASURE+wisdom | 0.002 | 0.001 | 12.05 | 11.48 | 1.05 | – |
| 2^20 | FFTW MEASURE fresh | 0.015 | 3.744 | 11.76 | 11.52 | 1.02 | – |
| 2^20 | FFTW ESTIMATE | 0.001 | 0.001 | 44.19 | 43.20 | 1.02 | – |
| 2^20 | ducc0 | 0.000 | 0.000 | 21.55 | 14.48 | 1.49 | – |
| 3·2^20 | SweepFFT | 0.000 | 0.797 | 29.82 | 29.74 | 1.00 | 5 / 20 |
| 3·2^20 | SweepFFT (rule) | 0.000 | 0.007 | 34.32 | 29.73 | 1.15 | – |
| 3·2^20 | MKL | 0.002 | 0.059 | 117.01 | 115.55 | 1.01 | – |
| 3·2^20 | FFTW MEASURE+wisdom | 0.002 | 0.062 | 89.56 | 88.35 | 1.01 | – |
| 3·2^20 | FFTW MEASURE fresh † | 0.015 | 60.191 | 389.46 | 389.36 | 1.00 | – |
| 3·2^20 | FFTW ESTIMATE | 0.001 | 0.008 | 389.44 | 388.36 | 1.00 | – |
| 3·2^20 | ducc0 | 0.000 | 0.000 | 85.58 | 67.32 | 1.27 | – |
| 2^22 | SweepFFT | 0.000 | 1.823 | 40.25 | 40.14 | 1.00 | 6 / 24 |
| 2^22 | SweepFFT (rule) | 0.000 | 0.010 | 45.67 | 39.84 | 1.15 | – |
| 2^22 | MKL | 0.002 | 0.033 | 70.57 | 70.24 | 1.00 | – |
| 2^22 | FFTW MEASURE+wisdom | 0.002 | 0.001 | 65.11 | 63.94 | 1.02 | – |
| 2^22 | FFTW MEASURE fresh | 0.015 | 14.711 | 64.27 | 64.15 | 1.00 | – |
| 2^22 | FFTW ESTIMATE | 0.001 | 0.002 | 473.23 | 473.20 | 1.00 | – |
| 2^22 | ducc0 | 0.000 | 0.000 | 114.86 | 89.92 | 1.28 | – |
| 2^24 | SweepFFT | 0.000 | 14.151 | 179.39 | 179.04 | 1.00 | 8 / 32 |
| 2^24 | SweepFFT (rule) | 0.000 | 0.034 | 203.17 | 182.45 | 1.11 | – |
| 2^24 | MKL | 0.002 | 0.173 | 298.54 | 298.50 | 1.00 | – |
| 2^24 | FFTW MEASURE+wisdom | 0.002 | 0.001 | 271.93 | 271.10 | 1.00 | – |
| 2^24 | FFTW MEASURE fresh † | 0.015 | 60.143 | 1798.36 | 1798.88 | 1.00 | – |
| 2^24 | FFTW ESTIMATE | 0.001 | 0.002 | 1797.41 | 1796.48 | 1.00 | – |
| 2^24 | ducc0 | 0.000 | 0.000 | 594.69 | 489.98 | 1.21 | – |
| 2^26 | SweepFFT | 0.000 | 57.412 | 737.81 | 737.73 | 1.00 | 8 / 32 |
| 2^26 | SweepFFT (rule) | 0.000 | 0.127 | 807.86 | 727.89 | 1.11 | – |
| 2^26 | MKL | 0.002 | 0.721 | 1319.80 | 1317.87 | 1.00 | – |
| 2^26 | FFTW MEASURE+wisdom | 0.002 | 0.002 | 1260.90 | 1259.64 | 1.00 | – |
| 2^26 | FFTW MEASURE fresh † | 0.015 | 61.317 | 4940.19 | 4941.10 | 1.00 | – |
| 2^26 | FFTW ESTIMATE | 0.001 | 0.002 | 4935.41 | 4934.85 | 1.00 | – |
| 2^26 | ducc0 | 0.000 | 0.000 | 2479.91 | 2068.96 | 1.20 | – |

## Total time T(R) for R repeated transforms (s), planning included, library already initialised

| n | impl | R=1 | R=2 | R=10 | R=100 | R=1,000 | R=10,000 |
|---|---|---|---|---|---|---|---|
| 2^20 | SweepFFT | 2.91 | 2.92 | 2.98 | 3.73 | 11.2 | 85.6 |
| 2^20 | SweepFFT (rule) | 0.0144 | 0.0242 | 0.101 | 0.96 | 9.56 | 95.5 |
| 2^20 | MKL | 0.0197 | 0.0311 | 0.12 | 1.12 | 11.1 | 111 |
| 2^20 | FFTW MEASURE+wisdom | 0.0129 | 0.0247 | 0.117 | 1.15 | 11.5 | 115 |
| 2^20 | FFTW MEASURE fresh | 3.76 | 3.77 | 3.86 | 4.89 | 15.3 | 119 |
| 2^20 | FFTW ESTIMATE | 0.0456 | 0.0888 | 0.436 | 4.33 | 43.2 | 432 |
| 2^20 | ducc0 | 0.0216 | 0.0363 | 0.152 | 1.45 | 14.5 | 145 |
| 3·2^20 | SweepFFT | 0.827 | 0.857 | 1.09 | 3.77 | 30.5 | 298 |
| 3·2^20 | SweepFFT (rule) | 0.0417 | 0.0712 | 0.309 | 2.99 | 29.8 | 297 |
| 3·2^20 | MKL | 0.176 | 0.291 | 1.21 | 11.6 | 116 | 1.16e+03 |
| 3·2^20 | FFTW MEASURE+wisdom | 0.152 | 0.24 | 0.947 | 8.9 | 88.4 | 884 |
| 3·2^20 | FFTW MEASURE fresh | 60.6 | 61 | 64.1 | 99 | 449 | 3.95e+03 |
| 3·2^20 | FFTW ESTIMATE | 0.398 | 0.786 | 3.89 | 38.9 | 388 | 3.88e+03 |
| 3·2^20 | ducc0 | 0.0857 | 0.154 | 0.694 | 6.75 | 67.3 | 673 |
| 2^22 | SweepFFT | 1.86 | 1.9 | 2.22 | 5.84 | 42 | 403 |
| 2^22 | SweepFFT (rule) | 0.0556 | 0.0955 | 0.415 | 4 | 39.9 | 398 |
| 2^22 | MKL | 0.105 | 0.175 | 0.737 | 7.06 | 70.3 | 702 |
| 2^22 | FFTW MEASURE+wisdom | 0.066 | 0.13 | 0.645 | 6.42 | 64 | 639 |
| 2^22 | FFTW MEASURE fresh | 14.8 | 14.8 | 15.3 | 21.1 | 78.9 | 656 |
| 2^22 | FFTW ESTIMATE | 0.475 | 0.948 | 4.74 | 47.3 | 473 | 4.73e+03 |
| 2^22 | ducc0 | 0.115 | 0.205 | 0.925 | 9.03 | 90 | 899 |
| 2^24 | SweepFFT | 14.3 | 14.5 | 15.9 | 32.1 | 193 | 1.8e+03 |
| 2^24 | SweepFFT (rule) | 0.237 | 0.42 | 1.88 | 18.3 | 182 | 1.82e+03 |
| 2^24 | MKL | 0.472 | 0.77 | 3.16 | 30 | 299 | 2.99e+03 |
| 2^24 | FFTW MEASURE+wisdom | 0.273 | 0.545 | 2.72 | 27.1 | 271 | 2.71e+03 |
| 2^24 | FFTW MEASURE fresh | 61.9 | 63.7 | 78.1 | 240 | 1.86e+03 | 1.8e+04 |
| 2^24 | FFTW ESTIMATE | 1.8 | 3.6 | 18 | 180 | 1.8e+03 | 1.8e+04 |
| 2^24 | ducc0 | 0.595 | 1.08 | 5 | 49.1 | 490 | 4.9e+03 |
| 2^26 | SweepFFT | 58.1 | 58.9 | 64.8 | 131 | 795 | 7.43e+03 |
| 2^26 | SweepFFT (rule) | 0.935 | 1.66 | 7.49 | 73 | 728 | 7.28e+03 |
| 2^26 | MKL | 2.04 | 3.36 | 13.9 | 133 | 1.32e+03 | 1.32e+04 |
| 2^26 | FFTW MEASURE+wisdom | 1.26 | 2.53 | 12.6 | 126 | 1.26e+03 | 1.26e+04 |
| 2^26 | FFTW MEASURE fresh | 66.3 | 71.2 | 111 | 555 | 5e+03 | 4.95e+04 |
| 2^26 | FFTW ESTIMATE | 4.94 | 9.87 | 49.4 | 493 | 4.93e+03 | 4.93e+04 |
| 2^26 | ducc0 | 2.48 | 4.55 | 21.1 | 207 | 2.07e+03 | 2.07e+04 |

## Break-even reuse count R* for SweepFFT vs each baseline

Smallest number of transforms after which SweepFFT (planning included) has spent less total time than the baseline; closed form R* = (P_s − P_b) / (t_b − t_s), P = planning + first-call excess. "always": SweepFFT is ahead from the first transform; "never": the baseline's steady state is faster. In a running process (library initialised) / in a new process (initialisation included).

**SweepFFT**

| n | MKL | FFTW MEASURE+wisdom | FFTW MEASURE fresh | FFTW ESTIMATE | ducc0 |
|---|---|---|---|---|---|
| 2^20 | 1,038 / 1,037 | 904 / 904 | 1 (always) / 1 (always) | 83 / 83 | 467 / 467 |
| 3·2^20 | 9 / 9 | 13 / 13 | 1 (always) / 1 (always) † | 3 / 3 | 21 / 21 |
| 2^22 | 60 / 60 | 77 / 77 | 1 (always) / 1 (always) | 5 / 5 | 37 / 37 |
| 2^24 | 118 / 117 | 154 / 154 | 1 (always) / 1 (always) † | 9 / 9 | 46 / 46 |
| 2^26 | 98 / 98 | 110 / 110 | 1 (always) / 1 (always) † | 14 / 14 | 43 / 43 |

**SweepFFT (rule)**

| n | MKL | FFTW MEASURE+wisdom | FFTW MEASURE fresh | FFTW ESTIMATE | ducc0 |
|---|---|---|---|---|---|
| 2^20 | 1 (always) / 1 (always) | 2 / 1 (always) | 1 (always) / 1 (always) | 1 (always) / 1 (always) | 1 (always) / 1 (always) |
| 3·2^20 | 1 (always) / 1 (always) | 1 (always) / 1 (always) | 1 (always) / 1 (always) † | 1 (always) / 1 (always) | 1 (always) / 1 (always) |
| 2^22 | 1 (always) / 1 (always) | 1 (always) / 1 (always) | 1 (always) / 1 (always) | 1 (always) / 1 (always) | 1 (always) / 1 (always) |
| 2^24 | 1 (always) / 1 (always) | 1 (always) / 1 (always) | 1 (always) / 1 (always) † | 1 (always) / 1 (always) | 1 (always) / 1 (always) |
| 2^26 | 1 (always) / 1 (always) | 1 (always) / 1 (always) | 1 (always) / 1 (always) † | 1 (always) / 1 (always) | 1 (always) / 1 (always) |

## Memory beyond the 32 n bytes of input and output (MB; in sweeps S = 16 n bytes)

after planning = resident memory the plan holds; planning peak = peak during planning and the first call; execution scratch = extra resident peak during the first call; steady = after the first call.

| n | impl | after planning | planning peak | execution scratch | steady |
|---|---|---|---|---|---|
| 2^20 | SweepFFT | 17 (1.04) | 97 (6.07) | 0 (0.00) | 17 (1.04) |
| 2^20 | SweepFFT (rule) | 0 (0.02) | 17 (1.04) | 16 (1.02) | 17 (1.05) |
| 2^20 | MKL | 8 (0.50) | 10 (0.62) | 0 (0.01) | 8 (0.52) |
| 2^20 | FFTW MEASURE+wisdom | 0 (0.02) | 0 (0.03) | 0 (0.01) | 0 (0.02) |
| 2^20 | FFTW MEASURE fresh | 0 (0.01) | 34 (2.11) | 0 (0.01) | 0 (0.02) |
| 2^20 | FFTW ESTIMATE | 0 (0.00) | 0 (0.01) | 0 (0.00) | 0 (0.01) |
| 2^20 | ducc0 | 0 (0.00) | 16 (1.02) | 16 (1.02) | 16 (1.02) |
| 3·2^20 | SweepFFT | 49 (1.02) | 202 (4.21) | 0 (0.00) | 49 (1.02) |
| 3·2^20 | SweepFFT (rule) | 0 (0.01) | 49 (1.02) | 49 (1.01) | 49 (1.02) |
| 3·2^20 | MKL | 48 (1.00) | 96 (2.00) | 0 (0.00) | 48 (1.01) |
| 3·2^20 | FFTW MEASURE+wisdom | 48 (1.00) | 48 (1.00) | 0 (0.00) | 48 (1.00) |
| 3·2^20 | FFTW MEASURE fresh | 6 (0.13) | 115 (2.40) | 0 (0.00) | 6 (0.13) |
| 3·2^20 | FFTW ESTIMATE | 6 (0.13) | 6 (0.13) | 0 (0.00) | 6 (0.13) |
| 3·2^20 | ducc0 | 0 (0.00) | 48 (1.00) | 48 (1.00) | 48 (1.01) |
| 2^22 | SweepFFT | 65 (1.02) | 385 (6.02) | 0 (0.00) | 65 (1.02) |
| 2^22 | SweepFFT (rule) | 0 (0.01) | 65 (1.02) | 65 (1.01) | 65 (1.02) |
| 2^22 | MKL | 32 (0.50) | 40 (0.62) | 0 (0.00) | 32 (0.51) |
| 2^22 | FFTW MEASURE+wisdom | 0 (0.01) | 1 (0.01) | 1 (0.01) | 0 (0.01) |
| 2^22 | FFTW MEASURE fresh | 0 (0.00) | 131 (2.05) | 1 (0.01) | 0 (0.01) |
| 2^22 | FFTW ESTIMATE | 0 (0.00) | 0 (0.00) | 0 (0.00) | 0 (0.00) |
| 2^22 | ducc0 | 0 (0.00) | 65 (1.01) | 64 (1.01) | 64 (1.01) |
| 2^24 | SweepFFT | 264 (1.03) | 1544 (6.03) | 0 (0.00) | 264 (1.03) |
| 2^24 | SweepFFT (rule) | 1 (0.00) | 258 (1.01) | 257 (1.00) | 258 (1.01) |
| 2^24 | MKL | 128 (0.50) | 160 (0.62) | 0 (0.00) | 128 (0.50) |
| 2^24 | FFTW MEASURE+wisdom | 0 (0.00) | 2 (0.01) | 2 (0.01) | 1 (0.00) |
| 2^24 | FFTW MEASURE fresh | 0 (0.00) | 518 (2.02) | 1 (0.00) | 0 (0.00) |
| 2^24 | FFTW ESTIMATE | 0 (0.00) | 1 (0.00) | 1 (0.00) | 0 (0.00) |
| 2^24 | ducc0 | 0 (0.00) | 257 (1.00) | 257 (1.00) | 256 (1.00) |
| 2^26 | SweepFFT | 1028 (1.00) | 6149 (6.00) | 0 (0.00) | 1028 (1.00) |
| 2^26 | SweepFFT (rule) | 1 (0.00) | 1037 (1.01) | 1036 (1.01) | 1038 (1.01) |
| 2^26 | MKL | 510 (0.50) | 638 (0.62) | 0 (0.00) | 511 (0.50) |
| 2^26 | FFTW MEASURE+wisdom | 1 (0.00) | 2 (0.00) | 1 (0.00) | 1 (0.00) |
| 2^26 | FFTW MEASURE fresh | 0 (0.00) | 2054 (2.01) | 1 (0.00) | 0 (0.00) |
| 2^26 | FFTW ESTIMATE | 0 (0.00) | 1 (0.00) | 1 (0.00) | 0 (0.00) |
| 2^26 | ducc0 | 0 (0.00) | 1026 (1.00) | 1025 (1.00) | 1025 (1.00) |
