# Controlled memory-bandwidth contention (`scripts/contention.py`)

## Method A: k independent processes

Per-process latency (P-core processes, ms), aggregate GFlop/s, per-process speed relative to k = 1 (P-core processes), DRAM bandwidth, DRAM bytes per transform and median effective clock; medians over rounds. k > number of P-cores adds E-core processes (their latency is in the E column).

**n = 3·2^20**

| k | impl | latency P (ms) | latency E (ms) | aggregate GF | per-process vs k=1 | DRAM GB/s | S / transform | GHz | SweepFFT agg. speedup |
|---|---|---|---|---|---|---|---|---|---|
| 1 | SweepFFT | 19.8 | nan | 17.1 | 1.00 | nan | nan | nan | – |
| 1 | MKL | 38.3 | nan | 8.9 | 1.00 | nan | nan | nan | 1.94 |
| 1 | FFTW | 16.7 | nan | 20.3 | 1.00 | nan | nan | nan | 0.84 |
| 1 | ducc0 | 29.5 | nan | 11.5 | 1.00 | nan | nan | nan | 1.49 |
| 2 | SweepFFT | 22.9 | nan | 29.7 | 0.87 | nan | nan | nan | – |
| 2 | MKL | 57.2 | nan | 11.9 | 0.67 | nan | nan | nan | 2.50 |
| 2 | FFTW | 24.5 | nan | 27.7 | 0.68 | nan | nan | nan | 1.07 |
| 2 | ducc0 | 38.4 | nan | 17.7 | 0.77 | nan | nan | nan | 1.68 |
| 4 | SweepFFT | 32.5 | nan | 41.8 | 0.61 | nan | nan | nan | – |
| 4 | MKL | 78.0 | nan | 17.4 | 0.49 | nan | nan | nan | 2.40 |
| 4 | FFTW | 45.1 | nan | 30.1 | 0.37 | nan | nan | nan | 1.39 |
| 4 | ducc0 | 60.9 | nan | 22.3 | 0.48 | nan | nan | nan | 1.87 |
| 6 | SweepFFT | 39.7 | nan | 51.3 | 0.50 | nan | nan | nan | – |
| 6 | MKL | 99.7 | nan | 20.4 | 0.38 | nan | nan | nan | 2.51 |
| 6 | FFTW | 65.5 | nan | 31.1 | 0.26 | nan | nan | nan | 1.65 |
| 6 | ducc0 | 82.1 | nan | 24.8 | 0.36 | nan | nan | nan | 2.07 |
| 8 | SweepFFT | 46.1 | nan | 59.0 | 0.43 | nan | nan | nan | – |
| 8 | MKL | 126.4 | nan | 21.5 | 0.30 | nan | nan | nan | 2.74 |
| 8 | FFTW | 86.4 | nan | 31.5 | 0.19 | nan | nan | nan | 1.87 |
| 8 | ducc0 | 105.5 | nan | 25.7 | 0.28 | nan | nan | nan | 2.29 |

**n = 2^22**

| k | impl | latency P (ms) | latency E (ms) | aggregate GF | per-process vs k=1 | DRAM GB/s | S / transform | GHz | SweepFFT agg. speedup |
|---|---|---|---|---|---|---|---|---|---|
| 1 | SweepFFT | 27.3 | nan | 16.9 | 1.00 | nan | nan | nan | – |
| 1 | MKL | 28.7 | nan | 16.1 | 1.00 | nan | nan | nan | 1.05 |
| 1 | FFTW | 29.4 | nan | 15.7 | 1.00 | nan | nan | nan | 1.08 |
| 1 | ducc0 | 42.3 | nan | 10.9 | 1.00 | nan | nan | nan | 1.55 |
| 2 | SweepFFT | 32.2 | nan | 28.7 | 0.85 | nan | nan | nan | – |
| 2 | MKL | 35.4 | nan | 26.0 | 0.81 | nan | nan | nan | 1.10 |
| 2 | FFTW | 35.9 | nan | 25.7 | 0.82 | nan | nan | nan | 1.12 |
| 2 | ducc0 | 56.8 | nan | 16.2 | 0.74 | nan | nan | nan | 1.76 |
| 4 | SweepFFT | 41.5 | nan | 44.5 | 0.66 | nan | nan | nan | – |
| 4 | MKL | 61.4 | nan | 30.0 | 0.47 | nan | nan | nan | 1.48 |
| 4 | FFTW | 51.6 | nan | 35.8 | 0.57 | nan | nan | nan | 1.24 |
| 4 | ducc0 | 84.5 | nan | 21.8 | 0.50 | nan | nan | nan | 2.04 |
| 6 | SweepFFT | 52.6 | nan | 52.6 | 0.52 | nan | nan | nan | – |
| 6 | MKL | 86.0 | nan | 32.2 | 0.33 | nan | nan | nan | 1.63 |
| 6 | FFTW | 69.2 | nan | 40.0 | 0.42 | nan | nan | nan | 1.31 |
| 6 | ducc0 | 112.0 | nan | 24.7 | 0.38 | nan | nan | nan | 2.13 |
| 8 | SweepFFT | 62.0 | nan | 59.6 | 0.44 | nan | nan | nan | – |
| 8 | MKL | 115.2 | nan | 32.0 | 0.25 | nan | nan | nan | 1.86 |
| 8 | FFTW | 87.1 | nan | 42.4 | 0.34 | nan | nan | nan | 1.40 |
| 8 | ducc0 | 145.9 | nan | 25.3 | 0.29 | nan | nan | nan | 2.35 |

**n = 2^24**

| k | impl | latency P (ms) | latency E (ms) | aggregate GF | per-process vs k=1 | DRAM GB/s | S / transform | GHz | SweepFFT agg. speedup |
|---|---|---|---|---|---|---|---|---|---|
| 1 | SweepFFT | 145.1 | nan | 13.9 | 1.00 | nan | nan | nan | – |
| 1 | MKL | 161.9 | nan | 12.4 | 1.00 | nan | nan | nan | 1.12 |
| 1 | FFTW | 142.2 | nan | 14.2 | 1.00 | nan | nan | nan | 0.98 |
| 1 | ducc0 | 227.2 | nan | 8.9 | 1.00 | nan | nan | nan | 1.57 |
| 2 | SweepFFT | 153.6 | nan | 26.2 | 0.94 | nan | nan | nan | – |
| 2 | MKL | 192.2 | nan | 21.0 | 0.84 | nan | nan | nan | 1.25 |
| 2 | FFTW | 153.4 | nan | 26.2 | 0.93 | nan | nan | nan | 1.00 |
| 2 | ducc0 | 255.9 | nan | 15.7 | 0.89 | nan | nan | nan | 1.67 |
| 4 | SweepFFT | 186.9 | nan | 43.1 | 0.78 | nan | nan | nan | – |
| 4 | MKL | 281.4 | nan | 28.6 | 0.58 | nan | nan | nan | 1.50 |
| 4 | FFTW | 218.8 | nan | 36.8 | 0.65 | nan | nan | nan | 1.17 |
| 4 | ducc0 | 318.5 | nan | 25.3 | 0.71 | nan | nan | nan | 1.70 |
| 6 | SweepFFT | 225.6 | nan | 53.5 | 0.64 | nan | nan | nan | – |
| 6 | MKL | 388.7 | nan | 31.1 | 0.42 | nan | nan | nan | 1.72 |
| 6 | FFTW | 300.3 | nan | 40.2 | 0.47 | nan | nan | nan | 1.33 |
| 6 | ducc0 | 405.6 | nan | 29.8 | 0.56 | nan | nan | nan | 1.80 |
| 8 | SweepFFT | 264.7 | nan | 60.9 | 0.55 | nan | nan | nan | – |
| 8 | MKL | 509.6 | nan | 31.6 | 0.32 | nan | nan | nan | 1.92 |
| 8 | FFTW | 384.4 | nan | 41.9 | 0.37 | nan | nan | nan | 1.45 |
| 8 | ducc0 | 493.3 | nan | 32.7 | 0.46 | nan | nan | nan | 1.86 |

## Method B: one FFT with controlled background load

Load kernel triad, placement any (every load core shares the FFT core’s LLC). Background bandwidth: measured alone (memory-controller counters) and during the FFT (the load's own byte count). Slowdown = time / time at level 0 (same round), median over rounds.

**n = 3·2^20**

| level | background alone, DRAM GB/s | background during FFT (logical GB/s) | SweepFFT slowdown | MKL slowdown | FFTW slowdown | ducc0 slowdown | SweepFFT vs MKL | vs FFTW | vs ducc0 | system DRAM GB/s (SweepFFT run) |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 | nan | 0.0 | 1.00 | 1.00 | 1.00 | 1.00 | 1.92 | 0.84 | 1.50 | nan |
| 1x0.25 | nan | nan | 1.22 | 1.48 | 1.37 | 1.35 | 2.32 | 0.94 | 1.65 | nan |
| 1x0.5 | nan | nan | 1.42 | 1.97 | 1.66 | 1.86 | 2.67 | 0.98 | 1.95 | nan |
| 1x0.75 | nan | nan | 1.54 | 2.33 | 1.92 | 2.27 | 2.91 | 1.05 | 2.21 | nan |
| 2x0.75 | nan | nan | 2.01 | 3.66 | 3.54 | 3.31 | 3.50 | 1.48 | 2.46 | nan |
| 1 | nan | nan | 1.79 | 3.27 | 3.13 | 2.95 | 3.50 | 1.47 | 2.46 | nan |
| 4 | nan | nan | 4.52 | 11.84 | 10.56 | 9.10 | 5.01 | 1.97 | 3.01 | nan |
| 2 | nan | nan | 2.63 | 6.00 | 5.91 | 4.78 | 4.35 | 1.89 | 2.72 | nan |

**n = 2^22**

| level | background alone, DRAM GB/s | background during FFT (logical GB/s) | SweepFFT slowdown | MKL slowdown | FFTW slowdown | ducc0 slowdown | SweepFFT vs MKL | vs FFTW | vs ducc0 | system DRAM GB/s (SweepFFT run) |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 | nan | 0.0 | 1.00 | 1.00 | 1.00 | 1.00 | 1.04 | 1.07 | 1.59 | nan |
| 1x0.25 | nan | nan | 1.28 | 1.16 | 1.22 | 1.38 | 0.96 | 1.03 | 1.73 | nan |
| 1x0.5 | nan | nan | 1.42 | 1.47 | 1.55 | 1.74 | 1.06 | 1.17 | 1.94 | nan |
| 1x0.75 | nan | nan | 1.53 | 1.81 | 1.91 | 2.16 | 1.21 | 1.33 | 2.23 | nan |
| 2x0.75 | nan | nan | 1.97 | 2.55 | 2.56 | 2.93 | 1.37 | 1.39 | 2.37 | nan |
| 1 | nan | nan | 1.79 | 2.39 | 2.38 | 2.77 | 1.38 | 1.43 | 2.46 | nan |
| 4 | nan | nan | 4.63 | 6.35 | 7.11 | 8.40 | 1.45 | 1.65 | 2.91 | nan |
| 2 | nan | nan | 2.60 | 3.46 | 3.72 | 4.13 | 1.39 | 1.54 | 2.53 | nan |

**n = 2^24**

| level | background alone, DRAM GB/s | background during FFT (logical GB/s) | SweepFFT slowdown | MKL slowdown | FFTW slowdown | ducc0 slowdown | SweepFFT vs MKL | vs FFTW | vs ducc0 | system DRAM GB/s (SweepFFT run) |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 | nan | 0.0 | 1.00 | 1.00 | 1.00 | 1.00 | 1.13 | 0.99 | 1.61 | nan |
| 1x0.25 | nan | nan | 1.13 | 1.17 | 1.15 | 1.15 | 1.17 | 1.01 | 1.62 | nan |
| 1x0.5 | nan | nan | 1.19 | 1.30 | 1.30 | 1.34 | 1.22 | 1.08 | 1.79 | nan |
| 1x0.75 | nan | nan | 1.27 | 1.47 | 1.48 | 1.52 | 1.31 | 1.15 | 1.91 | nan |
| 2x0.75 | nan | nan | 1.56 | 1.93 | 2.07 | 2.15 | 1.39 | 1.31 | 2.20 | nan |
| 1 | nan | nan | 1.45 | 1.85 | 1.97 | 1.91 | 1.44 | 1.35 | 2.11 | nan |
| 4 | nan | nan | 4.02 | 4.71 | 6.08 | 6.18 | 1.32 | 1.50 | 2.47 | nan |
| 2 | nan | nan | 1.96 | 2.68 | 2.97 | 3.13 | 1.53 | 1.49 | 2.55 | nan |

**Sensitivity to background bandwidth**: slope of log(slowdown) against the background bandwidth measured alone (memory-controller counters where calibrated, otherwise the load's byte count), % per 10 GB/s, with 95% CI (all levels and rounds).

| n | SweepFFT | MKL | FFTW | ducc0 |
|---|---|---|---|---|
| 3·2^20 | +30.4 [+22.1, +38.6] | +53.5 [+42.3, +64.7] | +53.7 [+42.7, +64.7] | +48.3 [+38.6, +57.9] |
| 2^22 | +29.9 [+21.3, +38.5] | +41.0 [+32.0, +50.0] | +42.0 [+32.2, +51.8] | +44.7 [+34.9, +54.5] |
| 2^24 | +24.7 [+15.1, +34.2] | +32.1 [+23.2, +40.9] | +37.1 [+26.3, +47.9] | +37.8 [+26.9, +48.7] |
