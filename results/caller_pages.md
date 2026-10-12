# Caller-array paging (`scripts/caller_pages.py`)

Median GFlop/s over 3 rounds; huge = caller arrays on 2 MB pages (headline protocol), plain = ordinary aligned allocation (system THP mode). Speedup = SweepFFT / library, both under the same condition.

| n | impl | huge | plain | plain / huge | SweepFFT speedup, huge | SweepFFT speedup, plain |
|---|---|---|---|---|---|---|
| 3·2^20 | SweepFFT | 16.62 | 16.39 | 0.99 | – | – |
| 3·2^20 | MKL | 6.53 | 6.58 | 1.01 | 2.54 | 2.49 |
| 3·2^20 | FFTW | 17.04 | 17.27 | 1.01 | 0.98 | 0.95 |
| 3·2^20 | ducc0 | 7.91 | 10.12 | 1.28 | 2.10 | 1.62 |
| 2^22 | SweepFFT | 16.68 | 16.41 | 0.98 | – | – |
| 2^22 | MKL | 15.73 | 18.29 | 1.16 | 1.06 | 0.90 |
| 2^22 | FFTW | 11.44 | 16.48 | 1.44 | 1.46 | 1.00 |
| 2^22 | ducc0 | 8.04 | 10.70 | 1.33 | 2.07 | 1.53 |
| 2^24 | SweepFFT | 16.69 | 17.02 | 1.02 | – | – |
| 2^24 | MKL | 14.23 | 14.24 | 1.00 | 1.17 | 1.20 |
| 2^24 | FFTW | 11.30 | 11.49 | 1.02 | 1.48 | 1.48 |
| 2^24 | ducc0 | 8.22 | 8.03 | 0.98 | 2.03 | 2.12 |
| 2^25 | SweepFFT | 16.09 | 15.66 | 0.97 | – | – |
| 2^25 | MKL | 13.99 | 13.67 | 0.98 | 1.15 | 1.15 |
| 2^25 | FFTW | 11.12 | 10.97 | 0.99 | 1.45 | 1.43 |
| 2^25 | ducc0 | 8.23 | 7.86 | 0.96 | 1.96 | 1.99 |
| 2^26 | SweepFFT | 17.04 | 16.98 | 1.00 | – | – |
| 2^26 | MKL | 14.05 | 13.65 | 0.97 | 1.21 | 1.24 |
| 2^26 | FFTW | 11.34 | 10.88 | 0.96 | 1.50 | 1.56 |
| 2^26 | ducc0 | 7.91 | 7.74 | 0.98 | 2.15 | 2.19 |

Each implementation with its faster paging (SweepFFT speedup):

| n | vs MKL | vs FFTW | vs ducc0 |
|---|---|---|---|
| 3·2^20 | 2.53 | 0.96 | 1.64 |
| 2^22 | 0.91 | 1.01 | 1.56 |
| 2^24 | 1.20 | 1.48 | 2.07 |
| 2^25 | 1.15 | 1.45 | 1.96 |
| 2^26 | 1.21 | 1.50 | 2.15 |
