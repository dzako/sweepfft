# Planning and memory overhead (`scripts/overhead.py`)

3 rounds, one fresh process per run; medians over rounds. Total time T(R) = planning + the first R calls, measured up to R = 2^20: 1000, 3·2^20: 200, 2^22: 100, 2^24: 20, 2^26: 5 calls and extrapolated with the steady-state median beyond. † = FFTW's planner hit its time limit.

## Setup and per-call cost

| n | impl | library init (s) | planning (s) | first call (ms) | steady call (ms) | first / steady | planner candidates / timed transforms |
|---|---|---|---|---|---|---|---|
| 2^20 | SweepFFT | 0.000 | 0.751 | 5.89 | 5.43 | 1.08 | 7 / 70 |
| 2^20 | SweepFFT (rule) | 0.000 | 0.002 | 7.46 | 5.41 | 1.38 | – |
| 2^20 | MKL | 0.001 | 0.006 | 5.34 | 5.33 | 1.00 | – |
| 2^20 | FFTW MEASURE+wisdom | 0.001 | 0.000 | 6.53 | 5.65 | 1.15 | – |
| 2^20 | FFTW MEASURE fresh | 0.018 | 2.188 | 6.21 | 5.59 | 1.11 | – |
| 2^20 | FFTW ESTIMATE | 0.000 | 0.001 | 16.81 | 13.28 | 1.27 | – |
| 2^20 | ducc0 | 0.000 | 0.000 | 16.89 | 10.91 | 1.55 | – |
| 3·2^20 | SweepFFT | 0.000 | 0.502 | 21.44 | 20.62 | 1.04 | 5 / 20 |
| 3·2^20 | SweepFFT (rule) | 0.000 | 0.004 | 25.65 | 20.57 | 1.25 | – |
| 3·2^20 | MKL | 0.001 | 0.035 | 54.92 | 51.49 | 1.07 | – |
| 3·2^20 | FFTW MEASURE+wisdom | 0.001 | 0.018 | 21.02 | 19.90 | 1.06 | – |
| 3·2^20 | FFTW MEASURE fresh † | 0.018 | 60.030 | 69.75 | 69.29 | 1.01 | – |
| 3·2^20 | FFTW ESTIMATE | 0.000 | 0.005 | 69.82 | 69.04 | 1.01 | – |
| 3·2^20 | ducc0 | 0.000 | 0.000 | 58.92 | 42.63 | 1.38 | – |
| 2^22 | SweepFFT | 0.000 | 1.135 | 28.93 | 28.54 | 1.01 | 6 / 24 |
| 2^22 | SweepFFT (rule) | 0.000 | 0.005 | 34.26 | 27.67 | 1.24 | – |
| 2^22 | MKL | 0.001 | 0.024 | 30.58 | 29.39 | 1.04 | – |
| 2^22 | FFTW MEASURE+wisdom | 0.001 | 0.001 | 42.67 | 40.27 | 1.06 | – |
| 2^22 | FFTW MEASURE fresh | 0.018 | 9.501 | 40.98 | 40.58 | 1.01 | – |
| 2^22 | FFTW ESTIMATE | 0.000 | 0.001 | 123.09 | 120.95 | 1.02 | – |
| 2^22 | ducc0 | 0.000 | 0.000 | 78.30 | 57.58 | 1.36 | – |
| 2^24 | SweepFFT | 0.000 | 6.427 | 120.16 | 120.28 | 1.00 | 8 / 32 |
| 2^24 | SweepFFT (rule) | 0.000 | 0.019 | 146.43 | 120.56 | 1.21 | – |
| 2^24 | MKL | 0.001 | 0.114 | 145.04 | 141.63 | 1.02 | – |
| 2^24 | FFTW MEASURE+wisdom | 0.001 | 0.001 | 184.57 | 177.81 | 1.04 | – |
| 2^24 | FFTW MEASURE fresh | 0.018 | 40.727 | 178.41 | 178.26 | 1.00 | – |
| 2^24 | FFTW ESTIMATE | 0.000 | 0.001 | 546.37 | 538.11 | 1.02 | – |
| 2^24 | ducc0 | 0.000 | 0.000 | 322.72 | 245.45 | 1.31 | – |
| 2^26 | SweepFFT | 0.000 | 27.036 | 510.56 | 511.09 | 1.00 | 8 / 32 |
| 2^26 | SweepFFT (rule) | 0.000 | 0.072 | 640.59 | 554.79 | 1.15 | – |
| 2^26 | MKL | 0.001 | 0.592 | 621.26 | 619.56 | 1.00 | – |
| 2^26 | FFTW MEASURE+wisdom | 0.001 | 0.001 | 779.78 | 770.70 | 1.01 | – |
| 2^26 | FFTW MEASURE fresh † | 0.018 | 64.263 | 2290.40 | 2289.00 | 1.00 | – |
| 2^26 | FFTW ESTIMATE | 0.000 | 0.001 | 2298.82 | 2291.19 | 1.00 | – |
| 2^26 | ducc0 | 0.000 | 0.000 | 1365.93 | 1113.69 | 1.23 | – |

## Total time T(R) for R repeated transforms (s), planning included, library already initialised

| n | impl | R=1 | R=2 | R=10 | R=100 | R=1,000 | R=10,000 |
|---|---|---|---|---|---|---|---|
| 2^20 | SweepFFT | 0.757 | 0.762 | 0.806 | 1.29 | 6.13 | 55.1 |
| 2^20 | SweepFFT (rule) | 0.00906 | 0.0149 | 0.0609 | 0.57 | 5.46 | 54.2 |
| 2^20 | MKL | 0.011 | 0.0163 | 0.0581 | 0.533 | 5.33 | 53.3 |
| 2^20 | FFTW MEASURE+wisdom | 0.00693 | 0.0132 | 0.0617 | 0.605 | 5.7 | 56.5 |
| 2^20 | FFTW MEASURE fresh | 2.19 | 2.2 | 2.25 | 2.76 | 7.84 | 58.1 |
| 2^20 | FFTW ESTIMATE | 0.0177 | 0.0342 | 0.164 | 1.62 | 13.7 | 133 |
| 2^20 | ducc0 | 0.0169 | 0.0306 | 0.139 | 1.28 | 11.2 | 109 |
| 3·2^20 | SweepFFT | 0.524 | 0.546 | 0.712 | 2.57 | 21.2 | 207 |
| 3·2^20 | SweepFFT (rule) | 0.0296 | 0.0511 | 0.223 | 2.13 | 20.6 | 206 |
| 3·2^20 | MKL | 0.0893 | 0.144 | 0.582 | 5.25 | 51.6 | 515 |
| 3·2^20 | FFTW MEASURE+wisdom | 0.0392 | 0.0605 | 0.229 | 2.04 | 20 | 199 |
| 3·2^20 | FFTW MEASURE fresh | 60.1 | 60.2 | 60.7 | 67 | 129 | 753 |
| 3·2^20 | FFTW ESTIMATE | 0.0746 | 0.144 | 0.699 | 6.92 | 69.1 | 690 |
| 3·2^20 | ducc0 | 0.059 | 0.107 | 0.49 | 4.43 | 42.8 | 426 |
| 2^22 | SweepFFT | 1.16 | 1.19 | 1.42 | 3.98 | 29.7 | 287 |
| 2^22 | SweepFFT (rule) | 0.0395 | 0.0687 | 0.302 | 2.82 | 27.7 | 277 |
| 2^22 | MKL | 0.0548 | 0.0857 | 0.33 | 3.01 | 29.5 | 294 |
| 2^22 | FFTW MEASURE+wisdom | 0.0432 | 0.0857 | 0.424 | 4.07 | 40.3 | 403 |
| 2^22 | FFTW MEASURE fresh | 9.54 | 9.58 | 9.91 | 13.6 | 50.1 | 415 |
| 2^22 | FFTW ESTIMATE | 0.124 | 0.244 | 1.21 | 12.1 | 121 | 1.21e+03 |
| 2^22 | ducc0 | 0.0784 | 0.143 | 0.659 | 5.86 | 57.7 | 576 |
| 2^24 | SweepFFT | 6.55 | 6.67 | 7.63 | 18.4 | 127 | 1.21e+03 |
| 2^24 | SweepFFT (rule) | 0.165 | 0.292 | 1.28 | 12.1 | 121 | 1.21e+03 |
| 2^24 | MKL | 0.259 | 0.404 | 1.56 | 14.3 | 142 | 1.42e+03 |
| 2^24 | FFTW MEASURE+wisdom | 0.185 | 0.37 | 1.81 | 17.8 | 178 | 1.78e+03 |
| 2^24 | FFTW MEASURE fresh | 40.9 | 41.1 | 42.5 | 58.4 | 219 | 1.82e+03 |
| 2^24 | FFTW ESTIMATE | 0.547 | 1.09 | 5.39 | 53.8 | 538 | 5.38e+03 |
| 2^24 | ducc0 | 0.323 | 0.568 | 2.53 | 24.6 | 246 | 2.45e+03 |
| 2^26 | SweepFFT | 27.5 | 28.1 | 32.2 | 78.3 | 538 | 5.14e+03 |
| 2^26 | SweepFFT (rule) | 0.712 | 1.26 | 5.7 | 55.6 | 555 | 5.55e+03 |
| 2^26 | MKL | 1.21 | 1.83 | 6.8 | 62.6 | 620 | 6.2e+03 |
| 2^26 | FFTW MEASURE+wisdom | 0.781 | 1.55 | 7.73 | 77.1 | 771 | 7.71e+03 |
| 2^26 | FFTW MEASURE fresh | 66.6 | 68.9 | 87.2 | 293 | 2.35e+03 | 2.3e+04 |
| 2^26 | FFTW ESTIMATE | 2.3 | 4.59 | 22.9 | 229 | 2.29e+03 | 2.29e+04 |
| 2^26 | ducc0 | 1.37 | 2.48 | 11.4 | 112 | 1.11e+03 | 1.11e+04 |

## Break-even reuse count R* for SweepFFT vs each baseline

Smallest number of transforms after which SweepFFT (planning included) has spent less total time than the baseline; closed form R* = (P_s − P_b) / (t_b − t_s), P = planning + first-call excess. "always": SweepFFT is ahead from the first transform; "never": the baseline's steady state is faster. In a running process (library initialised) / in a new process (initialisation included).

**SweepFFT**

| n | MKL | FFTW MEASURE+wisdom | FFTW MEASURE fresh | FFTW ESTIMATE | ducc0 |
|---|---|---|---|---|---|
| 2^20 | never / never | 3,424 / 3,422 | 1 (always) / 1 (always) | 96 / 96 | 137 / 137 |
| 3·2^20 | 16 / 16 | never / never | 1 (always) / 1 (always) † | 11 / 11 | 23 / 23 |
| 2^22 | 1,321 / 1,320 | 97 / 97 | 1 (always) / 1 (always) | 13 / 13 | 39 / 39 |
| 2^24 | 296 / 296 | 112 / 112 | 1 (always) / 1 (always) | 16 / 16 | 51 / 51 |
| 2^26 | 244 / 244 | 105 / 105 | 1 (always) / 1 (always) † | 16 / 16 | 45 / 45 |

**SweepFFT (rule)**

| n | MKL | FFTW MEASURE+wisdom | FFTW MEASURE fresh | FFTW ESTIMATE | ducc0 |
|---|---|---|---|---|---|
| 2^20 | never / never | 10 / 8 | 1 (always) / 1 (always) | 1 (always) / 1 (always) | 1 (always) / 1 (always) |
| 3·2^20 | 1 (always) / 1 (always) | never / never | 1 (always) / 1 (always) † | 1 (always) / 1 (always) | 1 (always) / 1 (always) |
| 2^22 | 1 (always) / 1 (always) | 1 (always) / 1 (always) | 1 (always) / 1 (always) | 1 (always) / 1 (always) | 1 (always) / 1 (always) |
| 2^24 | 1 (always) / 1 (always) | 1 (always) / 1 (always) | 1 (always) / 1 (always) | 1 (always) / 1 (always) | 1 (always) / 1 (always) |
| 2^26 | 1 (always) / 1 (always) | 1 (always) / 1 (always) | 1 (always) / 1 (always) † | 1 (always) / 1 (always) | 1 (always) / 1 (always) |

## Memory beyond the 32 n bytes of input and output (MB; in sweeps S = 16 n bytes)

after planning = resident memory the plan holds; planning peak = peak during planning and the first call; execution scratch = extra resident peak during the first call; steady = after the first call.

| n | impl | after planning | planning peak | execution scratch | steady |
|---|---|---|---|---|---|
| 2^20 | SweepFFT | 17 (1.04) | 97 (6.07) | 0 (0.00) | 17 (1.04) |
| 2^20 | SweepFFT (rule) | 0 (0.02) | 17 (1.04) | 16 (1.02) | 17 (1.04) |
| 2^20 | MKL | 8 (0.51) | 10 (0.64) | 0 (0.01) | 8 (0.53) |
| 2^20 | FFTW MEASURE+wisdom | 0 (0.02) | 0 (0.02) | 0 (0.00) | 0 (0.02) |
| 2^20 | FFTW MEASURE fresh | 0 (0.01) | 34 (2.11) | 0 (0.00) | 0 (0.02) |
| 2^20 | FFTW ESTIMATE | 0 (0.00) | 0 (0.01) | 0 (0.00) | 0 (0.01) |
| 2^20 | ducc0 | 0 (0.00) | 16 (1.02) | 16 (1.02) | 16 (1.02) |
| 3·2^20 | SweepFFT | 49 (1.02) | 202 (4.21) | 0 (0.00) | 49 (1.02) |
| 3·2^20 | SweepFFT (rule) | 0 (0.01) | 49 (1.02) | 49 (1.01) | 49 (1.02) |
| 3·2^20 | MKL | 48 (1.01) | 96 (2.00) | 0 (0.00) | 48 (1.01) |
| 3·2^20 | FFTW MEASURE+wisdom | 24 (0.50) | 24 (0.50) | 0 (0.00) | 24 (0.50) |
| 3·2^20 | FFTW MEASURE fresh | 6 (0.13) | 115 (2.40) | 0 (0.00) | 6 (0.13) |
| 3·2^20 | FFTW ESTIMATE | 6 (0.13) | 6 (0.13) | 0 (0.00) | 6 (0.13) |
| 3·2^20 | ducc0 | 0 (0.00) | 48 (1.01) | 48 (1.01) | 48 (1.01) |
| 2^22 | SweepFFT | 65 (1.02) | 385 (6.02) | 0 (0.00) | 65 (1.02) |
| 2^22 | SweepFFT (rule) | 0 (0.01) | 65 (1.02) | 65 (1.01) | 65 (1.02) |
| 2^22 | MKL | 32 (0.50) | 40 (0.63) | 0 (0.00) | 33 (0.51) |
| 2^22 | FFTW MEASURE+wisdom | 0 (0.01) | 1 (0.01) | 0 (0.00) | 0 (0.01) |
| 2^22 | FFTW MEASURE fresh | 0 (0.00) | 132 (2.06) | 0 (0.00) | 0 (0.01) |
| 2^22 | FFTW ESTIMATE | 0 (0.00) | 0 (0.00) | 0 (0.00) | 0 (0.00) |
| 2^22 | ducc0 | 0 (0.00) | 65 (1.01) | 64 (1.01) | 64 (1.01) |
| 2^24 | SweepFFT | 258 (1.01) | 1538 (6.01) | 0 (0.00) | 258 (1.01) |
| 2^24 | SweepFFT (rule) | 1 (0.00) | 258 (1.01) | 257 (1.00) | 258 (1.01) |
| 2^24 | MKL | 128 (0.50) | 160 (0.63) | 0 (0.00) | 129 (0.50) |
| 2^24 | FFTW MEASURE+wisdom | 0 (0.00) | 1 (0.00) | 1 (0.00) | 1 (0.00) |
| 2^24 | FFTW MEASURE fresh | 0 (0.00) | 518 (2.02) | 1 (0.00) | 1 (0.00) |
| 2^24 | FFTW ESTIMATE | 0 (0.00) | 1 (0.00) | 1 (0.00) | 0 (0.00) |
| 2^24 | ducc0 | 0 (0.00) | 257 (1.00) | 257 (1.00) | 256 (1.00) |
| 2^26 | SweepFFT | 3072 (3.00) | 6159 (6.01) | 0 (0.00) | 3072 (3.00) |
| 2^26 | SweepFFT (rule) | 1 (0.00) | 1037 (1.01) | 1036 (1.01) | 1038 (1.01) |
| 2^26 | MKL | 510 (0.50) | 638 (0.62) | 0 (0.00) | 511 (0.50) |
| 2^26 | FFTW MEASURE+wisdom | 1 (0.00) | 2 (0.00) | 1 (0.00) | 1 (0.00) |
| 2^26 | FFTW MEASURE fresh | 0 (0.00) | 2054 (2.01) | 1 (0.00) | 0 (0.00) |
| 2^26 | FFTW ESTIMATE | 0 (0.00) | 1 (0.00) | 1 (0.00) | 0 (0.00) |
| 2^26 | ducc0 | 0 (0.00) | 1026 (1.00) | 1025 (1.00) | 1025 (1.00) |
