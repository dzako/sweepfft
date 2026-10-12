# Caller-array paging (`scripts/caller_pages.py`)

Median GFlop/s over 3 rounds; huge = caller arrays on 2 MB pages (headline protocol), plain = ordinary aligned allocation (system THP mode). Speedup = SweepFFT / library, both under the same condition.

| n | impl | huge | plain | plain / huge | SweepFFT speedup, huge | SweepFFT speedup, plain |
|---|---|---|---|---|---|---|
| 3·2^20 | SweepFFT | 9.19 | 9.03 | 0.98 | – | – |
| 3·2^20 | MKL | 2.34 | 4.59 | 1.96 | 3.93 | 1.97 |
| 3·2^20 | FFTW | 8.74 | 8.84 | 1.01 | 1.05 | 1.02 |
| 3·2^20 | ducc0 | 3.81 | 5.59 | 1.47 | 2.42 | 1.62 |
| 2^22 | SweepFFT | 9.07 | 8.83 | 0.97 | – | – |
| 2^22 | MKL | 5.47 | 7.57 | 1.38 | 1.66 | 1.17 |
| 2^22 | FFTW | 5.83 | 7.36 | 1.26 | 1.56 | 1.20 |
| 2^22 | ducc0 | 3.84 | 4.63 | 1.20 | 2.36 | 1.91 |
| 2^24 | SweepFFT | 8.90 | 8.43 | 0.95 | – | – |
| 2^24 | MKL | 5.64 | 7.79 | 1.38 | 1.58 | 1.08 |
| 2^24 | FFTW | 5.96 | 6.12 | 1.03 | 1.49 | 1.38 |
| 2^24 | ducc0 | 4.00 | 3.87 | 0.97 | 2.22 | 2.18 |
| 2^25 | SweepFFT | 8.90 | 8.86 | 1.00 | – | – |
| 2^25 | MKL | 5.48 | 7.20 | 1.31 | 1.62 | 1.23 |
| 2^25 | FFTW | 5.77 | 5.44 | 0.94 | 1.54 | 1.63 |
| 2^25 | ducc0 | 4.06 | 3.54 | 0.87 | 2.19 | 2.50 |
| 2^26 | SweepFFT | 9.30 | 7.65 | 0.82 | – | – |
| 2^26 | MKL | 5.49 | 6.55 | 1.19 | 1.69 | 1.17 |
| 2^26 | FFTW | 5.62 | 5.61 | 1.00 | 1.66 | 1.36 |
| 2^26 | ducc0 | 4.04 | 3.45 | 0.85 | 2.30 | 2.22 |

Each implementation with its faster paging (SweepFFT speedup):

| n | vs MKL | vs FFTW | vs ducc0 |
|---|---|---|---|
| 3·2^20 | 2.00 | 1.04 | 1.64 |
| 2^22 | 1.20 | 1.23 | 1.96 |
| 2^24 | 1.14 | 1.46 | 2.22 |
| 2^25 | 1.24 | 1.54 | 2.19 |
| 2^26 | 1.42 | 1.66 | 2.30 |
