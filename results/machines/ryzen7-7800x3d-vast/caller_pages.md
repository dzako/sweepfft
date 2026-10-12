# Caller-array paging (`scripts/caller_pages.py`)

Median GFlop/s over 3 rounds; huge = caller arrays on 2 MB pages (headline protocol), plain = ordinary aligned allocation (system THP mode). Speedup = SweepFFT / library, both under the same condition.

| n | impl | huge | plain | plain / huge | SweepFFT speedup, huge | SweepFFT speedup, plain |
|---|---|---|---|---|---|---|
| 3·2^20 | SweepFFT | 16.87 | 16.31 | 0.97 | – | – |
| 3·2^20 | MKL | 9.03 | 9.43 | 1.04 | 1.87 | 1.73 |
| 3·2^20 | FFTW | 20.42 | 18.36 | 0.90 | 0.83 | 0.89 |
| 3·2^20 | ducc0 | 11.45 | 10.94 | 0.96 | 1.47 | 1.49 |
| 2^22 | SweepFFT | 16.97 | 16.13 | 0.95 | – | – |
| 2^22 | MKL | 16.16 | 15.59 | 0.96 | 1.05 | 1.03 |
| 2^22 | FFTW | 15.98 | 14.35 | 0.90 | 1.06 | 1.12 |
| 2^22 | ducc0 | 10.82 | 10.13 | 0.94 | 1.57 | 1.59 |
| 2^24 | SweepFFT | 14.07 | 14.84 | 1.05 | – | – |
| 2^24 | MKL | 12.43 | 11.91 | 0.96 | 1.13 | 1.25 |
| 2^24 | FFTW | 14.16 | 12.04 | 0.85 | 0.99 | 1.23 |
| 2^24 | ducc0 | 8.87 | 8.23 | 0.93 | 1.59 | 1.80 |
| 2^25 | SweepFFT | 14.65 | 15.53 | 1.06 | – | – |
| 2^25 | MKL | 11.31 | 10.82 | 0.96 | 1.29 | 1.44 |
| 2^25 | FFTW | 9.59 | 12.14 | 1.27 | 1.53 | 1.28 |
| 2^25 | ducc0 | 8.80 | 8.22 | 0.93 | 1.66 | 1.89 |
| 2^26 | SweepFFT | 13.14 | 16.15 | 1.23 | – | – |
| 2^26 | MKL | 11.32 | 10.91 | 0.96 | 1.16 | 1.48 |
| 2^26 | FFTW | 3.70 | 12.15 | 3.28 | 3.55 | 1.33 |
| 2^26 | ducc0 | 8.11 | 8.69 | 1.07 | 1.62 | 1.86 |

Each implementation with its faster paging (SweepFFT speedup):

| n | vs MKL | vs FFTW | vs ducc0 |
|---|---|---|---|
| 3·2^20 | 1.79 | 0.83 | 1.47 |
| 2^22 | 1.05 | 1.06 | 1.57 |
| 2^24 | 1.19 | 1.05 | 1.67 |
| 2^25 | 1.37 | 1.28 | 1.77 |
| 2^26 | 1.43 | 1.33 | 1.86 |
