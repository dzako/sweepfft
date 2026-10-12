# Controlled memory-bandwidth contention (`scripts/contention.py`)

## Method A: k independent processes

Per-process latency (P-core processes, ms), aggregate GFlop/s, per-process speed relative to k = 1 (P-core processes), DRAM bandwidth, DRAM bytes per transform and median effective clock; medians over rounds. k > number of P-cores adds E-core processes (their latency is in the E column).

**n = 3·2^20**

| k | impl | latency P (ms) | latency E (ms) | aggregate GF | per-process vs k=1 | DRAM GB/s | S / transform | GHz | SweepFFT agg. speedup |
|---|---|---|---|---|---|---|---|---|---|
| 1 | SweepFFT | 30.8 | nan | 11.0 | 1.00 | nan | nan | 3.97 | – |
| 1 | MKL | 117.9 | nan | 2.9 | 1.00 | nan | nan | 4.23 | 3.83 |
| 1 | FFTW | 92.2 | nan | 3.7 | 1.00 | nan | nan | 4.09 | 2.99 |
| 1 | ducc0 | 67.9 | nan | 5.0 | 1.00 | nan | nan | 4.21 | 2.20 |
| 2 | SweepFFT | 35.5 | nan | 19.1 | 0.87 | nan | nan | 3.92 | – |
| 2 | MKL | 128.8 | nan | 5.3 | 0.92 | nan | nan | 4.18 | 3.63 |
| 2 | FFTW | 94.6 | nan | 7.2 | 0.98 | nan | nan | 4.10 | 2.66 |
| 2 | ducc0 | 77.7 | nan | 8.7 | 0.87 | nan | nan | 4.18 | 2.19 |
| 4 | SweepFFT | 43.1 | nan | 31.5 | 0.71 | nan | nan | 3.92 | – |
| 4 | MKL | 154.8 | nan | 8.8 | 0.76 | nan | nan | 4.11 | 3.59 |
| 4 | FFTW | 101.1 | nan | 13.4 | 0.91 | nan | nan | 3.97 | 2.35 |
| 4 | ducc0 | 100.7 | nan | 13.5 | 0.67 | nan | nan | 4.11 | 2.34 |
| 6 | SweepFFT | 51.9 | nan | 39.4 | 0.60 | nan | nan | 3.81 | – |
| 6 | MKL | 185.8 | nan | 11.0 | 0.63 | nan | nan | 3.96 | 3.59 |
| 6 | FFTW | 110.9 | nan | 18.4 | 0.83 | nan | nan | 3.81 | 2.14 |
| 6 | ducc0 | 120.8 | nan | 16.9 | 0.56 | nan | nan | 3.96 | 2.34 |
| 8 | SweepFFT | 63.9 | nan | 42.6 | 0.48 | nan | nan | 3.84 | – |
| 8 | MKL | 219.5 | nan | 12.4 | 0.54 | nan | nan | 3.91 | 3.45 |
| 8 | FFTW | 129.1 | nan | 21.1 | 0.72 | nan | nan | 3.82 | 2.02 |
| 8 | ducc0 | 146.8 | nan | 18.5 | 0.46 | nan | nan | 3.91 | 2.31 |
| 10 | SweepFFT | 78.2 | nan | 43.5 | 0.39 | nan | nan | 3.84 | – |
| 10 | MKL | 251.4 | nan | 13.5 | 0.47 | nan | nan | 3.89 | 3.22 |
| 10 | FFTW | 153.6 | nan | 22.1 | 0.60 | nan | nan | 3.83 | 1.97 |
| 10 | ducc0 | 172.2 | nan | 19.7 | 0.39 | nan | nan | 3.89 | 2.21 |
| 12 | SweepFFT | 94.0 | nan | 43.4 | 0.33 | nan | nan | 3.83 | – |
| 12 | MKL | 292.3 | nan | 13.9 | 0.40 | nan | nan | 3.87 | 3.11 |
| 12 | FFTW | 191.8 | nan | 21.2 | 0.48 | nan | nan | 3.83 | 2.04 |
| 12 | ducc0 | 201.7 | nan | 20.2 | 0.34 | nan | nan | 3.86 | 2.14 |

**n = 2^22**

| k | impl | latency P (ms) | latency E (ms) | aggregate GF | per-process vs k=1 | DRAM GB/s | S / transform | GHz | SweepFFT agg. speedup |
|---|---|---|---|---|---|---|---|---|---|
| 1 | SweepFFT | 42.3 | nan | 10.9 | 1.00 | nan | nan | 3.86 | – |
| 1 | MKL | 73.2 | nan | 6.3 | 1.00 | nan | nan | 3.99 | 1.73 |
| 1 | FFTW | 67.5 | nan | 6.8 | 1.00 | nan | nan | 3.84 | 1.59 |
| 1 | ducc0 | 91.0 | nan | 5.1 | 1.00 | nan | nan | 4.12 | 2.15 |
| 2 | SweepFFT | 48.2 | nan | 19.2 | 0.88 | nan | nan | 3.91 | – |
| 2 | MKL | 88.4 | nan | 10.4 | 0.83 | nan | nan | 4.04 | 1.83 |
| 2 | FFTW | 75.3 | nan | 12.3 | 0.90 | nan | nan | 3.89 | 1.56 |
| 2 | ducc0 | 103.5 | nan | 8.9 | 0.88 | nan | nan | 4.16 | 2.15 |
| 4 | SweepFFT | 60.3 | nan | 30.6 | 0.70 | nan | nan | 3.84 | – |
| 4 | MKL | 134.7 | nan | 13.7 | 0.54 | nan | nan | 4.01 | 2.23 |
| 4 | FFTW | 102.0 | nan | 18.1 | 0.66 | nan | nan | 3.86 | 1.69 |
| 4 | ducc0 | 134.2 | nan | 13.8 | 0.68 | nan | nan | 4.07 | 2.22 |
| 6 | SweepFFT | 72.6 | nan | 38.3 | 0.59 | nan | nan | 3.78 | – |
| 6 | MKL | 189.2 | nan | 14.9 | 0.40 | nan | nan | 3.89 | 2.56 |
| 6 | FFTW | 133.5 | nan | 20.8 | 0.51 | nan | nan | 3.77 | 1.85 |
| 6 | ducc0 | 161.6 | nan | 17.2 | 0.56 | nan | nan | 3.93 | 2.23 |
| 8 | SweepFFT | 90.6 | nan | 40.9 | 0.47 | nan | nan | 3.83 | – |
| 8 | MKL | 251.7 | nan | 15.0 | 0.30 | nan | nan | 3.90 | 2.72 |
| 8 | FFTW | 169.4 | nan | 21.8 | 0.40 | nan | nan | 3.86 | 1.87 |
| 8 | ducc0 | 193.1 | nan | 19.1 | 0.47 | nan | nan | 3.91 | 2.14 |
| 10 | SweepFFT | 108.7 | nan | 42.5 | 0.39 | nan | nan | 3.85 | – |
| 10 | MKL | 310.7 | nan | 14.9 | 0.24 | nan | nan | 3.89 | 2.86 |
| 10 | FFTW | 209.0 | nan | 22.1 | 0.32 | nan | nan | 3.88 | 1.93 |
| 10 | ducc0 | 228.0 | nan | 20.2 | 0.40 | nan | nan | 3.89 | 2.10 |
| 12 | SweepFFT | 131.7 | nan | 42.0 | 0.32 | nan | nan | 3.85 | – |
| 12 | MKL | 376.0 | nan | 14.7 | 0.19 | nan | nan | 3.87 | 2.86 |
| 12 | FFTW | 251.9 | nan | 22.0 | 0.27 | nan | nan | 3.87 | 1.91 |
| 12 | ducc0 | 272.9 | nan | 20.3 | 0.33 | nan | nan | 3.86 | 2.07 |

**n = 2^24**

| k | impl | latency P (ms) | latency E (ms) | aggregate GF | per-process vs k=1 | DRAM GB/s | S / transform | GHz | SweepFFT agg. speedup |
|---|---|---|---|---|---|---|---|---|---|
| 1 | SweepFFT | 189.7 | nan | 10.6 | 1.00 | nan | nan | 3.89 | – |
| 1 | MKL | 305.4 | nan | 6.6 | 1.00 | nan | nan | 4.09 | 1.61 |
| 1 | FFTW | 284.8 | nan | 7.1 | 1.00 | nan | nan | 3.90 | 1.50 |
| 1 | ducc0 | 496.5 | nan | 4.1 | 1.00 | nan | nan | 4.13 | 2.62 |
| 2 | SweepFFT | 207.6 | nan | 19.4 | 0.91 | nan | nan | 3.98 | – |
| 2 | MKL | 376.1 | nan | 10.7 | 0.81 | nan | nan | 4.11 | 1.81 |
| 2 | FFTW | 320.3 | nan | 12.6 | 0.89 | nan | nan | 3.97 | 1.54 |
| 2 | ducc0 | 547.8 | nan | 7.4 | 0.91 | nan | nan | 4.16 | 2.64 |
| 4 | SweepFFT | 258.5 | nan | 31.1 | 0.73 | nan | nan | 3.98 | – |
| 4 | MKL | 540.8 | nan | 14.9 | 0.56 | nan | nan | 4.07 | 2.09 |
| 4 | FFTW | 419.9 | nan | 19.2 | 0.68 | nan | nan | 3.98 | 1.62 |
| 4 | ducc0 | 667.2 | nan | 12.1 | 0.74 | nan | nan | 4.10 | 2.58 |
| 6 | SweepFFT | 326.4 | nan | 37.4 | 0.59 | nan | nan | 3.93 | – |
| 6 | MKL | 742.3 | nan | 16.5 | 0.42 | nan | nan | 3.93 | 2.27 |
| 6 | FFTW | 543.1 | nan | 22.3 | 0.52 | nan | nan | 3.87 | 1.68 |
| 6 | ducc0 | 774.8 | nan | 15.6 | 0.64 | nan | nan | 3.96 | 2.40 |
| 8 | SweepFFT | 436.1 | nan | 37.0 | 0.44 | nan | nan | 3.92 | – |
| 8 | MKL | 977.1 | nan | 16.8 | 0.32 | nan | nan | 3.92 | 2.20 |
| 8 | FFTW | 690.7 | nan | 23.3 | 0.41 | nan | nan | 3.91 | 1.59 |
| 8 | ducc0 | 922.7 | nan | 17.5 | 0.54 | nan | nan | 3.92 | 2.12 |
| 10 | SweepFFT | 506.6 | nan | 39.9 | 0.38 | nan | nan | 3.91 | – |
| 10 | MKL | 1214.9 | nan | 16.6 | 0.25 | nan | nan | 3.91 | 2.41 |
| 10 | FFTW | 845.2 | nan | 23.8 | 0.34 | nan | nan | 3.90 | 1.67 |
| 10 | ducc0 | 1069.6 | nan | 18.8 | 0.46 | nan | nan | 3.90 | 2.12 |
| 12 | SweepFFT | 701.8 | nan | 34.4 | 0.27 | nan | nan | 3.90 | – |
| 12 | MKL | 1474.3 | nan | 16.4 | 0.21 | nan | nan | 3.91 | 2.10 |
| 12 | FFTW | 1003.3 | nan | 24.1 | 0.28 | nan | nan | 3.88 | 1.43 |
| 12 | ducc0 | 1242.5 | nan | 19.4 | 0.40 | nan | nan | 3.88 | 1.77 |

## Method B: one FFT with controlled background load

Load kernel triad, placement same-llc (every load core shares the FFT core’s LLC). Background bandwidth: measured alone (memory-controller counters) and during the FFT (the load's own byte count). Slowdown = time / time at level 0 (same round), median over rounds.

**n = 3·2^20**

| level | background alone, DRAM GB/s | background during FFT (logical GB/s) | SweepFFT slowdown | MKL slowdown | FFTW slowdown | ducc0 slowdown | SweepFFT vs MKL | vs FFTW | vs ducc0 | system DRAM GB/s (SweepFFT run) |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 | nan | 0.0 | 1.00 | 1.00 | 1.00 | 1.00 | 3.88 | 2.97 | 2.22 | nan |
| 1x0.25 | nan | nan | 1.06 | 1.10 | 1.03 | 1.09 | 4.02 | 2.88 | 2.29 | nan |
| 1x0.5 | nan | nan | 1.12 | 1.22 | 1.06 | 1.21 | 4.22 | 2.78 | 2.40 | nan |
| 1x0.75 | nan | nan | 1.18 | 1.34 | 1.10 | 1.33 | 4.43 | 2.75 | 2.53 | nan |
| 1 | nan | nan | 1.28 | 1.59 | 1.12 | 1.59 | 4.82 | 2.62 | 2.78 | nan |
| 2x0.75 | nan | nan | 1.53 | 1.88 | 1.42 | 1.83 | 4.73 | 2.77 | 2.65 | nan |
| 2 | nan | nan | 2.07 | 2.75 | 2.16 | 2.57 | 5.16 | 3.11 | 2.76 | nan |

**n = 2^22**

| level | background alone, DRAM GB/s | background during FFT (logical GB/s) | SweepFFT slowdown | MKL slowdown | FFTW slowdown | ducc0 slowdown | SweepFFT vs MKL | vs FFTW | vs ducc0 | system DRAM GB/s (SweepFFT run) |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 | nan | 0.0 | 1.00 | 1.00 | 1.00 | 1.00 | 1.76 | 1.62 | 2.22 | nan |
| 1x0.25 | nan | nan | 1.06 | 1.09 | 1.08 | 1.09 | 1.80 | 1.65 | 2.28 | nan |
| 1x0.5 | nan | nan | 1.14 | 1.21 | 1.19 | 1.21 | 1.84 | 1.68 | 2.35 | nan |
| 1x0.75 | nan | nan | 1.21 | 1.33 | 1.31 | 1.33 | 1.95 | 1.75 | 2.46 | nan |
| 1 | nan | nan | 1.31 | 1.55 | 1.57 | 1.57 | 2.08 | 1.92 | 2.67 | nan |
| 2x0.75 | nan | nan | 1.54 | 1.78 | 1.78 | 1.83 | 2.00 | 1.86 | 2.62 | nan |
| 2 | nan | nan | 2.07 | 2.39 | 2.72 | 2.57 | 2.03 | 2.12 | 2.76 | nan |

**n = 2^24**

| level | background alone, DRAM GB/s | background during FFT (logical GB/s) | SweepFFT slowdown | MKL slowdown | FFTW slowdown | ducc0 slowdown | SweepFFT vs MKL | vs FFTW | vs ducc0 | system DRAM GB/s (SweepFFT run) |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 | nan | 0.0 | 1.00 | 1.00 | 1.00 | 1.00 | 1.66 | 1.50 | 2.68 | nan |
| 1x0.25 | nan | nan | 1.06 | 1.09 | 1.11 | 1.10 | 1.71 | 1.57 | 2.79 | nan |
| 1x0.5 | nan | nan | 1.15 | 1.19 | 1.19 | 1.20 | 1.72 | 1.57 | 2.82 | nan |
| 1x0.75 | nan | nan | 1.20 | 1.30 | 1.32 | 1.32 | 1.80 | 1.65 | 2.97 | nan |
| 1 | nan | nan | 1.32 | 1.53 | 1.73 | 1.55 | 1.91 | 1.96 | 3.15 | nan |
| 2x0.75 | nan | nan | 1.61 | 1.75 | 2.11 | 1.80 | 1.79 | 1.97 | 2.99 | nan |
| 2 | nan | nan | 2.34 | 2.40 | 3.59 | 2.52 | 1.70 | 2.31 | 2.88 | nan |

**Sensitivity to background bandwidth**: slope of log(slowdown) against the background bandwidth measured alone (memory-controller counters where calibrated, otherwise the load's byte count), % per 10 GB/s, with 95% CI (all levels and rounds).

| n | SweepFFT | MKL | FFTW | ducc0 |
|---|---|---|---|---|
| 3·2^20 | +22.9 [+16.0, +29.7] | +33.7 [+26.1, +41.3] | +21.7 [+12.1, +31.4] | +32.3 [+25.6, +38.9] |
| 2^22 | +23.4 [+17.1, +29.7] | +30.2 [+24.4, +36.0] | +33.0 [+25.1, +40.9] | +32.2 [+25.4, +39.0] |
| 2^24 | +26.3 [+18.4, +34.2] | +29.7 [+23.5, +35.9] | +42.2 [+31.3, +53.0] | +31.2 [+24.5, +37.8] |
