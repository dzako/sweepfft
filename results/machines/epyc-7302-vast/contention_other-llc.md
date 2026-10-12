# Controlled memory-bandwidth contention (`scripts/contention.py`)

## Method A: k independent processes

Per-process latency (P-core processes, ms), aggregate GFlop/s, per-process speed relative to k = 1 (P-core processes), DRAM bandwidth, DRAM bytes per transform and median effective clock; medians over rounds. k > number of P-cores adds E-core processes (their latency is in the E column).

**n = 3·2^20**

| k | impl | latency P (ms) | latency E (ms) | aggregate GF | per-process vs k=1 | DRAM GB/s | S / transform | GHz | SweepFFT agg. speedup |
|---|---|---|---|---|---|---|---|---|---|
| 1 | SweepFFT | 36.8 | nan | 9.2 | 1.00 | nan | nan | nan | – |
| 1 | MKL | 144.9 | nan | 2.3 | 1.00 | nan | nan | nan | 3.94 |
| 1 | FFTW | 38.7 | nan | 8.8 | 1.00 | nan | nan | nan | 1.05 |
| 1 | ducc0 | 88.7 | nan | 3.8 | 1.00 | nan | nan | nan | 2.41 |
| 2 | SweepFFT | 39.5 | nan | 17.2 | 0.93 | nan | nan | nan | – |
| 2 | MKL | 150.8 | nan | 4.5 | 0.96 | nan | nan | nan | 3.82 |
| 2 | FFTW | 44.2 | nan | 15.4 | 0.88 | nan | nan | nan | 1.12 |
| 2 | ducc0 | 95.4 | nan | 7.1 | 0.93 | nan | nan | nan | 2.42 |
| 4 | SweepFFT | 45.9 | nan | 29.6 | 0.80 | nan | nan | nan | – |
| 4 | MKL | 178.0 | nan | 7.6 | 0.81 | nan | nan | nan | 3.88 |
| 4 | FFTW | 70.0 | nan | 19.4 | 0.55 | nan | nan | nan | 1.53 |
| 4 | ducc0 | 116.3 | nan | 11.7 | 0.76 | nan | nan | nan | 2.53 |

**n = 2^22**

| k | impl | latency P (ms) | latency E (ms) | aggregate GF | per-process vs k=1 | DRAM GB/s | S / transform | GHz | SweepFFT agg. speedup |
|---|---|---|---|---|---|---|---|---|---|
| 1 | SweepFFT | 50.8 | nan | 9.1 | 1.00 | nan | nan | nan | – |
| 1 | MKL | 84.2 | nan | 5.5 | 1.00 | nan | nan | nan | 1.66 |
| 1 | FFTW | 79.1 | nan | 5.8 | 1.00 | nan | nan | nan | 1.56 |
| 1 | ducc0 | 119.1 | nan | 3.9 | 1.00 | nan | nan | nan | 2.35 |
| 2 | SweepFFT | 52.8 | nan | 17.5 | 0.96 | nan | nan | nan | – |
| 2 | MKL | 101.3 | nan | 9.1 | 0.83 | nan | nan | nan | 1.92 |
| 2 | FFTW | 85.2 | nan | 10.8 | 0.93 | nan | nan | nan | 1.61 |
| 2 | ducc0 | 128.8 | nan | 7.2 | 0.92 | nan | nan | nan | 2.44 |
| 4 | SweepFFT | 63.3 | nan | 29.2 | 0.80 | nan | nan | nan | – |
| 4 | MKL | 157.8 | nan | 11.7 | 0.53 | nan | nan | nan | 2.49 |
| 4 | FFTW | 107.8 | nan | 17.1 | 0.73 | nan | nan | nan | 1.70 |
| 4 | ducc0 | 156.0 | nan | 11.8 | 0.76 | nan | nan | nan | 2.47 |

**n = 2^24**

| k | impl | latency P (ms) | latency E (ms) | aggregate GF | per-process vs k=1 | DRAM GB/s | S / transform | GHz | SweepFFT agg. speedup |
|---|---|---|---|---|---|---|---|---|---|
| 1 | SweepFFT | 227.1 | nan | 8.9 | 1.00 | nan | nan | nan | – |
| 1 | MKL | 356.8 | nan | 5.6 | 1.00 | nan | nan | nan | 1.57 |
| 1 | FFTW | 336.7 | nan | 6.0 | 1.00 | nan | nan | nan | 1.48 |
| 1 | ducc0 | 505.5 | nan | 4.0 | 1.00 | nan | nan | nan | 2.23 |
| 2 | SweepFFT | 242.8 | nan | 16.6 | 0.94 | nan | nan | nan | – |
| 2 | MKL | 430.0 | nan | 9.4 | 0.83 | nan | nan | nan | 1.77 |
| 2 | FFTW | 359.8 | nan | 11.2 | 0.94 | nan | nan | nan | 1.48 |
| 2 | ducc0 | 550.0 | nan | 7.3 | 0.92 | nan | nan | nan | 2.27 |
| 4 | SweepFFT | 286.1 | nan | 28.2 | 0.79 | nan | nan | nan | – |
| 4 | MKL | 644.7 | nan | 12.5 | 0.55 | nan | nan | nan | 2.25 |
| 4 | FFTW | 452.0 | nan | 17.8 | 0.74 | nan | nan | nan | 1.58 |
| 4 | ducc0 | 658.8 | nan | 12.2 | 0.77 | nan | nan | nan | 2.30 |

## Method B: one FFT with controlled background load

Load kernel triad, placement other-llc (load cores do not share the FFT core’s LLC). Background bandwidth: measured alone (memory-controller counters) and during the FFT (the load's own byte count). Slowdown = time / time at level 0 (same round), median over rounds.

**n = 3·2^20**

| level | background alone, DRAM GB/s | background during FFT (logical GB/s) | SweepFFT slowdown | MKL slowdown | FFTW slowdown | ducc0 slowdown | SweepFFT vs MKL | vs FFTW | vs ducc0 | system DRAM GB/s (SweepFFT run) |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 | nan | 0.0 | 1.00 | 1.00 | 1.00 | 1.00 | 3.93 | 1.05 | 2.40 | nan |
| 1x0.25 | nan | nan | 1.04 | 1.06 | 1.04 | 1.06 | 4.00 | 1.06 | 2.46 | nan |
| 1x0.5 | nan | nan | 1.08 | 1.13 | 1.11 | 1.14 | 4.11 | 1.07 | 2.52 | nan |
| 1x0.75 | nan | nan | 1.14 | 1.22 | 1.17 | 1.26 | 4.22 | 1.09 | 2.66 | nan |
| 1 | nan | nan | 1.21 | 1.36 | 1.30 | 1.42 | 4.39 | 1.13 | 2.83 | nan |
| 2x0.75 | nan | nan | 1.27 | 1.46 | 1.35 | 1.53 | 4.55 | 1.12 | 2.91 | nan |
| 2 | nan | nan | 1.39 | 1.67 | 1.43 | 1.77 | 4.77 | 1.10 | 3.09 | nan |

**n = 2^22**

| level | background alone, DRAM GB/s | background during FFT (logical GB/s) | SweepFFT slowdown | MKL slowdown | FFTW slowdown | ducc0 slowdown | SweepFFT vs MKL | vs FFTW | vs ducc0 | system DRAM GB/s (SweepFFT run) |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 | nan | 0.0 | 1.00 | 1.00 | 1.00 | 1.00 | 1.68 | 1.57 | 2.35 | nan |
| 1x0.25 | nan | nan | 1.04 | 1.07 | 1.05 | 1.06 | 1.71 | 1.58 | 2.38 | nan |
| 1x0.5 | nan | nan | 1.09 | 1.16 | 1.12 | 1.16 | 1.78 | 1.62 | 2.51 | nan |
| 1x0.75 | nan | nan | 1.14 | 1.25 | 1.19 | 1.26 | 1.85 | 1.64 | 2.61 | nan |
| 1 | nan | nan | 1.22 | 1.43 | 1.31 | 1.43 | 1.96 | 1.69 | 2.76 | nan |
| 2x0.75 | nan | nan | 1.29 | 1.49 | 1.39 | 1.56 | 1.94 | 1.69 | 2.84 | nan |
| 2 | nan | nan | 1.39 | 1.60 | 1.53 | 1.79 | 1.93 | 1.73 | 3.04 | nan |

**n = 2^24**

| level | background alone, DRAM GB/s | background during FFT (logical GB/s) | SweepFFT slowdown | MKL slowdown | FFTW slowdown | ducc0 slowdown | SweepFFT vs MKL | vs FFTW | vs ducc0 | system DRAM GB/s (SweepFFT run) |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 | nan | 0.0 | 1.00 | 1.00 | 1.00 | 1.00 | 1.58 | 1.49 | 2.24 | nan |
| 1x0.25 | nan | nan | 1.04 | 1.07 | 1.06 | 1.06 | 1.61 | 1.51 | 2.26 | nan |
| 1x0.5 | nan | nan | 1.09 | 1.15 | 1.12 | 1.15 | 1.67 | 1.53 | 2.38 | nan |
| 1x0.75 | nan | nan | 1.10 | 1.24 | 1.18 | 1.24 | 1.78 | 1.59 | 2.53 | nan |
| 1 | nan | nan | 1.18 | 1.40 | 1.29 | 1.40 | 1.88 | 1.63 | 2.67 | nan |
| 2x0.75 | nan | nan | 1.25 | 1.47 | 1.37 | 1.53 | 1.84 | 1.62 | 2.73 | nan |
| 2 | nan | nan | 1.33 | 1.58 | 1.50 | 1.76 | 1.86 | 1.67 | 2.94 | nan |

**Sensitivity to background bandwidth**: slope of log(slowdown) against the background bandwidth measured alone (memory-controller counters where calibrated, otherwise the load's byte count), % per 10 GB/s, with 95% CI (all levels and rounds).

| n | SweepFFT | MKL | FFTW | ducc0 |
|---|---|---|---|---|
| 3·2^20 | +13.7 [+12.3, +15.1] | +21.9 [+19.6, +24.3] | +16.2 [+15.2, +17.1] | +24.4 [+22.1, +26.7] |
| 2^22 | +13.7 [+12.3, +15.1] | +21.1 [+20.3, +21.9] | +18.2 [+16.6, +19.8] | +25.2 [+22.8, +27.5] |
| 2^24 | +11.9 [+10.3, +13.6] | +20.5 [+19.5, +21.6] | +16.9 [+15.4, +18.5] | +23.8 [+21.5, +26.2] |
