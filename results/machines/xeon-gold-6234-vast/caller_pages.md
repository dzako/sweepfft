# Caller-array paging (`scripts/caller_pages.py`)

Median GFlop/s over 3 rounds; huge = caller arrays on 2 MB pages (headline protocol), plain = ordinary aligned allocation (system THP mode). Speedup = SweepFFT / library, both under the same condition.

| n | impl | huge | plain | plain / huge | SweepFFT speedup, huge | SweepFFT speedup, plain |
|---|---|---|---|---|---|---|
| 3·2^20 | SweepFFT | 7.49 | 6.77 | 0.90 | – | – |
| 3·2^20 | MKL | 6.80 | 5.09 | 0.75 | 1.10 | 1.33 |
| 3·2^20 | FFTW | 5.39 | 7.11 | 1.32 | 1.39 | 0.95 |
| 3·2^20 | ducc0 | 2.36 | 3.17 | 1.34 | 3.17 | 2.13 |
| 2^22 | SweepFFT | 7.51 | 6.60 | 0.88 | – | – |
| 2^22 | MKL | 6.90 | 6.39 | 0.93 | 1.09 | 1.03 |
| 2^22 | FFTW | 5.24 | 5.47 | 1.05 | 1.43 | 1.21 |
| 2^22 | ducc0 | 2.47 | 3.71 | 1.50 | 3.04 | 1.78 |
| 2^24 | SweepFFT | 7.19 | 5.47 | 0.76 | – | – |
| 2^24 | MKL | 6.13 | 5.61 | 0.92 | 1.17 | 0.98 |
| 2^24 | FFTW | 5.14 | 5.18 | 1.01 | 1.40 | 1.06 |
| 2^24 | ducc0 | 2.56 | 2.91 | 1.13 | 2.81 | 1.88 |
| 2^25 | SweepFFT | 6.86 | 5.94 | 0.87 | – | – |
| 2^25 | MKL | 5.51 | 5.34 | 0.97 | 1.24 | 1.11 |
| 2^25 | FFTW | 5.12 | 5.00 | 0.98 | 1.34 | 1.19 |
| 2^25 | ducc0 | 2.48 | 2.44 | 0.98 | 2.76 | 2.44 |
| 2^26 | SweepFFT | 6.72 | 6.28 | 0.93 | – | – |
| 2^26 | MKL | 5.55 | 4.69 | 0.84 | 1.21 | 1.34 |
| 2^26 | FFTW | 5.27 | 5.07 | 0.96 | 1.28 | 1.24 |
| 2^26 | ducc0 | 2.55 | 2.43 | 0.95 | 2.63 | 2.58 |

Each implementation with its faster paging (SweepFFT speedup):

| n | vs MKL | vs FFTW | vs ducc0 |
|---|---|---|---|
| 3·2^20 | 1.10 | 1.05 | 2.36 |
| 2^22 | 1.09 | 1.37 | 2.02 |
| 2^24 | 1.17 | 1.39 | 2.48 |
| 2^25 | 1.24 | 1.34 | 2.76 |
| 2^26 | 1.21 | 1.28 | 2.63 |
