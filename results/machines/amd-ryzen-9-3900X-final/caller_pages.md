# Caller-array paging (`scripts/caller_pages.py`)

Median GFlop/s over 3 rounds; huge = caller arrays on 2 MB pages (headline protocol), plain = ordinary aligned allocation (system THP mode). Speedup = SweepFFT / library, both under the same condition.

| n | impl | huge | plain | plain / huge | SweepFFT speedup, huge | SweepFFT speedup, plain |
|---|---|---|---|---|---|---|
| 3·2^20 | SweepFFT | 11.47 | 11.09 | 0.97 | – | – |
| 3·2^20 | MKL | 2.89 | 5.64 | 1.95 | 3.97 | 1.97 |
| 3·2^20 | FFTW | 3.84 | 9.97 | 2.59 | 2.99 | 1.11 |
| 3·2^20 | ducc0 | 5.05 | 7.09 | 1.40 | 2.27 | 1.56 |
| 2^22 | SweepFFT | 11.52 | 11.32 | 0.98 | – | – |
| 2^22 | MKL | 6.52 | 9.06 | 1.39 | 1.77 | 1.25 |
| 2^22 | FFTW | 7.17 | 9.16 | 1.28 | 1.61 | 1.24 |
| 2^22 | ducc0 | 5.12 | 7.07 | 1.38 | 2.25 | 1.60 |
| 2^24 | SweepFFT | 11.31 | 10.64 | 0.94 | – | – |
| 2^24 | MKL | 6.72 | 9.34 | 1.39 | 1.68 | 1.14 |
| 2^24 | FFTW | 7.37 | 7.73 | 1.05 | 1.53 | 1.38 |
| 2^24 | ducc0 | 4.11 | 5.07 | 1.23 | 2.75 | 2.10 |
| 2^25 | SweepFFT | 11.36 | 11.08 | 0.98 | – | – |
| 2^25 | MKL | 6.58 | 8.82 | 1.34 | 1.73 | 1.26 |
| 2^25 | FFTW | 7.08 | 8.16 | 1.15 | 1.61 | 1.36 |
| 2^25 | ducc0 | 4.18 | 5.23 | 1.25 | 2.72 | 2.12 |
| 2^26 | SweepFFT | 11.82 | 11.17 | 0.95 | – | – |
| 2^26 | MKL | 6.62 | 8.84 | 1.34 | 1.79 | 1.26 |
| 2^26 | FFTW | 6.91 | 7.62 | 1.10 | 1.71 | 1.47 |
| 2^26 | ducc0 | 4.20 | 4.99 | 1.19 | 2.82 | 2.24 |

Each implementation with its faster paging (SweepFFT speedup):

| n | vs MKL | vs FFTW | vs ducc0 |
|---|---|---|---|
| 3·2^20 | 2.04 | 1.15 | 1.62 |
| 2^22 | 1.27 | 1.26 | 1.63 |
| 2^24 | 1.21 | 1.46 | 2.23 |
| 2^25 | 1.29 | 1.39 | 2.17 |
| 2^26 | 1.34 | 1.55 | 2.37 |
