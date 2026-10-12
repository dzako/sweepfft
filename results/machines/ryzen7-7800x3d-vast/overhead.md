# Planning and memory overhead (`scripts/overhead.py`)

3 rounds, one fresh process per run; medians over rounds. Total time T(R) = planning + the first R calls, measured up to R = 2^20: 1000, 3·2^20: 500, 2^22: 200, 2^24: 50, 2^26: 5 calls and extrapolated with the steady-state median beyond. † = FFTW's planner hit its time limit.

## Setup and per-call cost

| n | impl | library init (s) | planning (s) | first call (ms) | steady call (ms) | first / steady | planner candidates / timed transforms |
|---|---|---|---|---|---|---|---|
| 2^20 | SweepFFT | 0.000 | 1.578 | 7.17 | 5.85 | 1.23 | 7 / 70 |
| 2^20 | SweepFFT (rule) | 0.000 | 0.002 | 8.26 | 7.51 | 1.10 | – |
| 2^20 | MKL | 0.019 | 0.006 | 6.79 | 5.62 | 1.21 | – |
| 2^20 | FFTW MEASURE+wisdom | 0.001 | 0.000 | 6.73 | 5.84 | 1.15 | – |
| 2^20 | FFTW MEASURE fresh | 0.014 | 2.361 | 7.45 | 6.04 | 1.23 | – |
| 2^20 | FFTW ESTIMATE | 0.001 | 0.001 | 11.42 | 10.32 | 1.11 | – |
| 2^20 | ducc0 | 0.000 | 0.000 | 13.24 | 7.88 | 1.68 | – |
| 3·2^20 | SweepFFT | 0.000 | 0.593 | 23.57 | 19.76 | 1.19 | 5 / 20 |
| 3·2^20 | SweepFFT (rule) | 0.000 | 0.004 | 23.27 | 19.84 | 1.17 | – |
| 3·2^20 | MKL | 0.019 | 0.039 | 45.05 | 35.85 | 1.26 | – |
| 3·2^20 | FFTW MEASURE+wisdom | 0.001 | 0.014 | 18.25 | 16.69 | 1.09 | – |
| 3·2^20 | FFTW MEASURE fresh † | 0.015 | 60.160 | 40.27 | 29.44 | 1.37 | – |
| 3·2^20 | FFTW ESTIMATE | 0.001 | 0.006 | 29.61 | 29.21 | 1.01 | – |
| 3·2^20 | ducc0 | 0.000 | 0.000 | 42.89 | 29.42 | 1.46 | – |
| 2^22 | SweepFFT | 0.000 | 1.633 | 31.88 | 27.61 | 1.15 | 6 / 24 |
| 2^22 | SweepFFT (rule) | 0.000 | 0.005 | 33.31 | 27.93 | 1.19 | – |
| 2^22 | MKL | 0.019 | 0.025 | 33.04 | 28.49 | 1.16 | – |
| 2^22 | FFTW MEASURE+wisdom | 0.002 | 0.000 | 31.54 | 28.95 | 1.09 | – |
| 2^22 | FFTW MEASURE fresh | 0.015 | 11.176 | 32.37 | 29.77 | 1.09 | – |
| 2^22 | FFTW ESTIMATE | 0.001 | 0.001 | 57.93 | 54.83 | 1.06 | – |
| 2^22 | ducc0 | 0.000 | 0.000 | 59.62 | 41.75 | 1.43 | – |
| 2^24 | SweepFFT | 0.000 | 8.698 | 143.26 | 143.51 | 1.00 | 8 / 32 |
| 2^24 | SweepFFT (rule) | 0.000 | 0.016 | 162.55 | 143.00 | 1.14 | – |
| 2^24 | MKL | 0.020 | 0.100 | 167.81 | 162.61 | 1.03 | – |
| 2^24 | FFTW MEASURE+wisdom | 0.001 | 0.001 | 144.44 | 142.03 | 1.02 | – |
| 2^24 | FFTW MEASURE fresh † | 0.015 | 54.899 | 146.80 | 144.34 | 1.02 | – |
| 2^24 | FFTW ESTIMATE | 0.001 | 0.001 | 277.75 | 279.21 | 0.99 | – |
| 2^24 | ducc0 | 0.000 | 0.000 | 275.81 | 227.28 | 1.21 | – |
| 2^26 | SweepFFT | 0.000 | 58.476 | 665.88 | 666.20 | 1.00 | 8 / 32 |
| 2^26 | SweepFFT (rule) | 0.000 | 0.055 | 652.10 | 585.05 | 1.11 | – |
| 2^26 | MKL | 0.021 | 0.519 | 759.42 | 759.69 | 1.00 | – |
| 2^26 | FFTW MEASURE+wisdom | 0.002 | 0.001 | 2348.29 | 2351.12 | 1.00 | – |
| 2^26 | FFTW MEASURE fresh † | 0.015 | 60.572 | 1357.70 | 1360.01 | 1.00 | – |
| 2^26 | FFTW ESTIMATE | 0.001 | 0.001 | 1357.61 | 1360.96 | 1.00 | – |
| 2^26 | ducc0 | 0.000 | 0.000 | 1304.33 | 1076.13 | 1.21 | – |

## Total time T(R) for R repeated transforms (s), planning included, library already initialised

| n | impl | R=1 | R=2 | R=10 | R=100 | R=1,000 | R=10,000 |
|---|---|---|---|---|---|---|---|
| 2^20 | SweepFFT | 1.58 | 1.59 | 1.64 | 2.17 | 7.47 | 60 |
| 2^20 | SweepFFT (rule) | 0.00996 | 0.0174 | 0.077 | 0.744 | 7.42 | 75.1 |
| 2^20 | MKL | 0.0127 | 0.0183 | 0.0635 | 0.571 | 5.64 | 56.2 |
| 2^20 | FFTW MEASURE+wisdom | 0.00693 | 0.0129 | 0.0601 | 0.588 | 5.87 | 58.5 |
| 2^20 | FFTW MEASURE fresh | 2.37 | 2.38 | 2.43 | 2.98 | 8.49 | 62.9 |
| 2^20 | FFTW ESTIMATE | 0.0124 | 0.0229 | 0.106 | 1.04 | 10.4 | 103 |
| 2^20 | ducc0 | 0.0132 | 0.0213 | 0.0855 | 0.799 | 7.9 | 78.8 |
| 3·2^20 | SweepFFT | 0.616 | 0.639 | 0.803 | 2.58 | 20.4 | 198 |
| 3·2^20 | SweepFFT (rule) | 0.0274 | 0.0478 | 0.211 | 2 | 19.8 | 198 |
| 3·2^20 | MKL | 0.0843 | 0.122 | 0.411 | 3.68 | 36.1 | 359 |
| 3·2^20 | FFTW MEASURE+wisdom | 0.0321 | 0.0501 | 0.186 | 1.7 | 16.8 | 167 |
| 3·2^20 | FFTW MEASURE fresh | 60.2 | 60.2 | 60.4 | 63.1 | 89.6 | 355 |
| 3·2^20 | FFTW ESTIMATE | 0.0353 | 0.0652 | 0.299 | 2.92 | 29.2 | 292 |
| 3·2^20 | ducc0 | 0.043 | 0.0731 | 0.309 | 2.94 | 29.4 | 294 |
| 2^22 | SweepFFT | 1.66 | 1.7 | 1.92 | 4.41 | 29.3 | 278 |
| 2^22 | SweepFFT (rule) | 0.0383 | 0.0671 | 0.29 | 2.74 | 27.9 | 279 |
| 2^22 | MKL | 0.0573 | 0.0865 | 0.315 | 2.88 | 28.6 | 285 |
| 2^22 | FFTW MEASURE+wisdom | 0.0317 | 0.0622 | 0.296 | 2.91 | 29.2 | 290 |
| 2^22 | FFTW MEASURE fresh | 11.2 | 11.2 | 11.5 | 14.2 | 40.9 | 309 |
| 2^22 | FFTW ESTIMATE | 0.0592 | 0.116 | 0.556 | 5.46 | 54.8 | 548 |
| 2^22 | ducc0 | 0.0597 | 0.103 | 0.445 | 4.25 | 41.9 | 418 |
| 2^24 | SweepFFT | 8.84 | 8.99 | 10.2 | 23 | 152 | 1.44e+03 |
| 2^24 | SweepFFT (rule) | 0.178 | 0.321 | 1.47 | 14.3 | 143 | 1.43e+03 |
| 2^24 | MKL | 0.267 | 0.43 | 1.73 | 16.3 | 163 | 1.63e+03 |
| 2^24 | FFTW MEASURE+wisdom | 0.145 | 0.288 | 1.43 | 14.2 | 142 | 1.42e+03 |
| 2^24 | FFTW MEASURE fresh | 55 | 55.2 | 56.3 | 69.3 | 199 | 1.5e+03 |
| 2^24 | FFTW ESTIMATE | 0.279 | 0.558 | 2.78 | 28 | 279 | 2.79e+03 |
| 2^24 | ducc0 | 0.276 | 0.503 | 2.32 | 22.8 | 227 | 2.27e+03 |
| 2^26 | SweepFFT | 59.1 | 59.8 | 65.1 | 125 | 725 | 6.72e+03 |
| 2^26 | SweepFFT (rule) | 0.707 | 1.29 | 5.97 | 58.6 | 585 | 5.85e+03 |
| 2^26 | MKL | 1.28 | 2.04 | 8.11 | 76.5 | 760 | 7.6e+03 |
| 2^26 | FFTW MEASURE+wisdom | 2.35 | 4.7 | 23.5 | 235 | 2.35e+03 | 2.35e+04 |
| 2^26 | FFTW MEASURE fresh | 61.9 | 63.3 | 74.2 | 197 | 1.42e+03 | 1.37e+04 |
| 2^26 | FFTW ESTIMATE | 1.36 | 2.72 | 13.6 | 136 | 1.36e+03 | 1.36e+04 |
| 2^26 | ducc0 | 1.3 | 2.39 | 11 | 108 | 1.08e+03 | 1.08e+04 |

## Break-even reuse count R* for SweepFFT vs each baseline

Smallest number of transforms after which SweepFFT (planning included) has spent less total time than the baseline; closed form R* = (P_s − P_b) / (t_b − t_s), P = planning + first-call excess. "always": SweepFFT is ahead from the first transform; "never": the baseline's steady state is faster. In a running process (library initialised) / in a new process (initialisation included).

**SweepFFT**

| n | MKL | FFTW MEASURE+wisdom | FFTW MEASURE fresh | FFTW ESTIMATE | ducc0 |
|---|---|---|---|---|---|
| 2^20 | never / never | never / never | 1 (always) / 1 (always) | 353 / 353 | 773 / 773 |
| 3·2^20 | 35 / 33 | never / never | 1 (always) / 1 (always) † | 63 / 63 | 61 / 61 |
| 2^22 | 1,826 / 1,805 | 1,222 / 1,221 | 1 (always) / 1 (always) | 61 / 60 | 115 / 115 |
| 2^24 | 451 / 449 | never / never | 1 (always) / 1 (always) † | 65 / 65 | 104 / 104 |
| 2^26 | 620 / 620 | 35 / 35 | 1 (always) / 1 (always) † | 85 / 85 | 143 / 143 |

**SweepFFT (rule)**

| n | MKL | FFTW MEASURE+wisdom | FFTW MEASURE fresh | FFTW ESTIMATE | ducc0 |
|---|---|---|---|---|---|
| 2^20 | never / never | never / never | never / never | 1 (always) / 1 (always) | 1 (always) / 1 (always) |
| 3·2^20 | 1 (always) / 1 (always) | never / never | 1 (always) / 1 (always) † | 1 (always) / 1 (always) | 1 (always) / 1 (always) |
| 2^22 | 1 (always) / 1 (always) | 8 / 7 | 1 (always) / 1 (always) | 1 (always) / 1 (always) | 1 (always) / 1 (always) |
| 2^24 | 1 (always) / 1 (always) | never / never | 1 (always) / 1 (always) † | 1 (always) / 1 (always) | 1 (always) / 1 (always) |
| 2^26 | 1 (always) / 1 (always) | 1 (always) / 1 (always) | 1 (always) / 1 (always) † | 1 (always) / 1 (always) | 1 (always) / 1 (always) |

## Memory beyond the 32 n bytes of input and output (MB; in sweeps S = 16 n bytes)

after planning = resident memory the plan holds; planning peak = peak during planning and the first call; execution scratch = extra resident peak during the first call; steady = after the first call.

| n | impl | after planning | planning peak | execution scratch | steady |
|---|---|---|---|---|---|
| 2^20 | SweepFFT | 17 (1.04) | 97 (6.08) | 0 (0.00) | 17 (1.05) |
| 2^20 | SweepFFT (rule) | 0 (0.02) | 17 (1.04) | 16 (1.02) | 17 (1.04) |
| 2^20 | MKL | 8 (0.51) | 10 (0.62) | 0 (0.00) | 8 (0.52) |
| 2^20 | FFTW MEASURE+wisdom | 0 (0.01) | 0 (0.01) | 0 (0.00) | 0 (0.02) |
| 2^20 | FFTW MEASURE fresh | 0 (0.01) | 34 (2.13) | 0 (0.00) | 0 (0.02) |
| 2^20 | FFTW ESTIMATE | 0 (0.00) | 0 (0.01) | 0 (0.00) | 0 (0.02) |
| 2^20 | ducc0 | 0 (0.01) | 16 (1.01) | 16 (1.00) | 16 (1.02) |
| 3·2^20 | SweepFFT | 49 (1.02) | 202 (4.21) | 0 (0.00) | 49 (1.02) |
| 3·2^20 | SweepFFT (rule) | 1 (0.01) | 49 (1.02) | 48 (1.01) | 49 (1.02) |
| 3·2^20 | MKL | 48 (1.00) | 96 (2.00) | 0 (0.00) | 48 (1.00) |
| 3·2^20 | FFTW MEASURE+wisdom | 15 (0.31) | 15 (0.31) | 0 (0.00) | 15 (0.31) |
| 3·2^20 | FFTW MEASURE fresh | 6 (0.13) | 111 (2.32) | 0 (0.00) | 6 (0.13) |
| 3·2^20 | FFTW ESTIMATE | 6 (0.13) | 6 (0.13) | 0 (0.00) | 6 (0.13) |
| 3·2^20 | ducc0 | 0 (0.00) | 49 (1.01) | 48 (1.01) | 49 (1.01) |
| 2^22 | SweepFFT | 65 (1.02) | 385 (6.02) | 0 (0.00) | 65 (1.02) |
| 2^22 | SweepFFT (rule) | 0 (0.01) | 65 (1.02) | 64 (1.01) | 65 (1.02) |
| 2^22 | MKL | 32 (0.50) | 40 (0.62) | 0 (0.00) | 32 (0.51) |
| 2^22 | FFTW MEASURE+wisdom | 0 (0.00) | 1 (0.02) | 1 (0.02) | 0 (0.00) |
| 2^22 | FFTW MEASURE fresh | 0 (0.00) | 132 (2.06) | 1 (0.01) | 0 (0.01) |
| 2^22 | FFTW ESTIMATE | 0 (0.00) | 0 (0.00) | 0 (0.00) | 0 (0.00) |
| 2^22 | ducc0 | 0 (0.00) | 65 (1.01) | 64 (1.00) | 64 (1.01) |
| 2^24 | SweepFFT | 258 (1.01) | 1538 (6.01) | 0 (0.00) | 258 (1.01) |
| 2^24 | SweepFFT (rule) | 1 (0.00) | 258 (1.01) | 257 (1.00) | 258 (1.01) |
| 2^24 | MKL | 128 (0.50) | 160 (0.62) | 0 (0.00) | 128 (0.50) |
| 2^24 | FFTW MEASURE+wisdom | 0 (0.00) | 2 (0.01) | 2 (0.01) | 0 (0.00) |
| 2^24 | FFTW MEASURE fresh | 0 (0.00) | 517 (2.02) | 2 (0.01) | 0 (0.00) |
| 2^24 | FFTW ESTIMATE | 0 (0.00) | 1 (0.00) | 0 (0.00) | 0 (0.00) |
| 2^24 | ducc0 | 0 (0.00) | 257 (1.00) | 257 (1.00) | 257 (1.00) |
| 2^26 | SweepFFT | 1028 (1.00) | 6149 (6.00) | 0 (0.00) | 1028 (1.00) |
| 2^26 | SweepFFT (rule) | 1 (0.00) | 1037 (1.01) | 1036 (1.01) | 1037 (1.01) |
| 2^26 | MKL | 510 (0.50) | 638 (0.62) | 0 (0.00) | 510 (0.50) |
| 2^26 | FFTW MEASURE+wisdom | 1 (0.00) | 9 (0.01) | 8 (0.01) | 1 (0.00) |
| 2^26 | FFTW MEASURE fresh | 0 (0.00) | 2053 (2.01) | 1 (0.00) | 1 (0.00) |
| 2^26 | FFTW ESTIMATE | 0 (0.00) | 1 (0.00) | 1 (0.00) | 0 (0.00) |
| 2^26 | ducc0 | 1 (0.00) | 1025 (1.00) | 1025 (1.00) | 1025 (1.00) |
