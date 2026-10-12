# Controlled memory-bandwidth contention (`scripts/contention.py`)

## Method A: k independent processes

Per-process latency (P-core processes, ms), aggregate GFlop/s, per-process speed relative to k = 1 (P-core processes), DRAM bandwidth, DRAM bytes per transform and median effective clock; medians over rounds. k > number of P-cores adds E-core processes (their latency is in the E column).

**n = 3·2^20**

| k | impl | latency P (ms) | latency E (ms) | aggregate GF | per-process vs k=1 | DRAM GB/s | S / transform | GHz | SweepFFT agg. speedup |
|---|---|---|---|---|---|---|---|---|---|
| 1 | SweepFFT | 44.7 | nan | 7.6 | 1.00 | nan | nan | nan | – |
| 1 | MKL | 50.2 | nan | 6.8 | 1.00 | nan | nan | nan | 1.12 |
| 1 | FFTW | 62.9 | nan | 5.4 | 1.00 | nan | nan | nan | 1.40 |
| 1 | ducc0 | 144.3 | nan | 2.4 | 1.00 | nan | nan | nan | 3.22 |
| 2 | SweepFFT | 45.4 | nan | 14.9 | 0.99 | nan | nan | nan | – |
| 2 | MKL | 52.2 | nan | 13.0 | 0.96 | nan | nan | nan | 1.15 |
| 2 | FFTW | 66.7 | nan | 10.2 | 0.94 | nan | nan | nan | 1.47 |
| 2 | ducc0 | 142.5 | nan | 4.8 | 1.01 | nan | nan | nan | 3.14 |
| 4 | SweepFFT | 46.0 | nan | 29.5 | 0.97 | nan | nan | nan | – |
| 4 | MKL | 54.3 | nan | 25.0 | 0.92 | nan | nan | nan | 1.18 |
| 4 | FFTW | 69.0 | nan | 19.7 | 0.91 | nan | nan | nan | 1.50 |
| 4 | ducc0 | 142.7 | nan | 9.5 | 1.01 | nan | nan | nan | 3.10 |
| 6 | SweepFFT | 46.7 | nan | 43.6 | 0.96 | nan | nan | nan | – |
| 6 | MKL | 56.0 | nan | 36.4 | 0.90 | nan | nan | nan | 1.20 |
| 6 | FFTW | 72.5 | nan | 28.1 | 0.87 | nan | nan | nan | 1.55 |
| 6 | ducc0 | 144.5 | nan | 14.1 | 1.00 | nan | nan | nan | 3.09 |
| 8 | SweepFFT | 47.9 | nan | 56.7 | 0.93 | nan | nan | nan | – |
| 8 | MKL | 58.0 | nan | 46.8 | 0.87 | nan | nan | nan | 1.21 |
| 8 | FFTW | 76.7 | nan | 35.4 | 0.82 | nan | nan | nan | 1.60 |
| 8 | ducc0 | 147.2 | nan | 18.5 | 0.98 | nan | nan | nan | 3.07 |

**n = 2^22**

| k | impl | latency P (ms) | latency E (ms) | aggregate GF | per-process vs k=1 | DRAM GB/s | S / transform | GHz | SweepFFT agg. speedup |
|---|---|---|---|---|---|---|---|---|---|
| 1 | SweepFFT | 60.6 | nan | 7.6 | 1.00 | nan | nan | nan | – |
| 1 | MKL | 67.5 | nan | 6.8 | 1.00 | nan | nan | nan | 1.11 |
| 1 | FFTW | 88.1 | nan | 5.2 | 1.00 | nan | nan | nan | 1.45 |
| 1 | ducc0 | 186.6 | nan | 2.5 | 1.00 | nan | nan | nan | 3.08 |
| 2 | SweepFFT | 61.3 | nan | 15.1 | 0.99 | nan | nan | nan | – |
| 2 | MKL | 69.3 | nan | 13.3 | 0.97 | nan | nan | nan | 1.13 |
| 2 | FFTW | 92.9 | nan | 9.9 | 0.95 | nan | nan | nan | 1.52 |
| 2 | ducc0 | 190.3 | nan | 4.8 | 0.98 | nan | nan | nan | 3.11 |
| 4 | SweepFFT | 62.1 | nan | 29.7 | 0.98 | nan | nan | nan | – |
| 4 | MKL | 71.6 | nan | 25.8 | 0.94 | nan | nan | nan | 1.15 |
| 4 | FFTW | 95.7 | nan | 19.3 | 0.92 | nan | nan | nan | 1.54 |
| 4 | ducc0 | 193.6 | nan | 9.5 | 0.96 | nan | nan | nan | 3.12 |
| 6 | SweepFFT | 62.6 | nan | 44.2 | 0.97 | nan | nan | nan | – |
| 6 | MKL | 73.1 | nan | 37.9 | 0.92 | nan | nan | nan | 1.17 |
| 6 | FFTW | 96.7 | nan | 28.6 | 0.91 | nan | nan | nan | 1.54 |
| 6 | ducc0 | 195.8 | nan | 14.1 | 0.95 | nan | nan | nan | 3.13 |
| 8 | SweepFFT | 63.1 | nan | 58.5 | 0.96 | nan | nan | nan | – |
| 8 | MKL | 75.8 | nan | 48.7 | 0.89 | nan | nan | nan | 1.20 |
| 8 | FFTW | 98.9 | nan | 37.3 | 0.89 | nan | nan | nan | 1.57 |
| 8 | ducc0 | 198.0 | nan | 18.6 | 0.94 | nan | nan | nan | 3.14 |

**n = 2^24**

| k | impl | latency P (ms) | latency E (ms) | aggregate GF | per-process vs k=1 | DRAM GB/s | S / transform | GHz | SweepFFT agg. speedup |
|---|---|---|---|---|---|---|---|---|---|
| 1 | SweepFFT | 278.9 | nan | 7.2 | 1.00 | nan | nan | nan | – |
| 1 | MKL | 331.0 | nan | 6.1 | 1.00 | nan | nan | nan | 1.19 |
| 1 | FFTW | 393.3 | nan | 5.1 | 1.00 | nan | nan | nan | 1.41 |
| 1 | ducc0 | 786.3 | nan | 2.6 | 1.00 | nan | nan | nan | 2.82 |
| 2 | SweepFFT | 283.7 | nan | 14.2 | 0.98 | nan | nan | nan | – |
| 2 | MKL | 387.4 | nan | 10.4 | 0.85 | nan | nan | nan | 1.37 |
| 2 | FFTW | 399.1 | nan | 10.1 | 0.99 | nan | nan | nan | 1.41 |
| 2 | ducc0 | 792.8 | nan | 5.1 | 0.99 | nan | nan | nan | 2.79 |
| 4 | SweepFFT | 282.7 | nan | 28.5 | 0.99 | nan | nan | nan | – |
| 4 | MKL | 390.1 | nan | 20.7 | 0.85 | nan | nan | nan | 1.38 |
| 4 | FFTW | 405.6 | nan | 19.9 | 0.97 | nan | nan | nan | 1.44 |
| 4 | ducc0 | 797.7 | nan | 10.1 | 0.99 | nan | nan | nan | 2.82 |
| 6 | SweepFFT | 286.2 | nan | 42.2 | 0.97 | nan | nan | nan | – |
| 6 | MKL | 400.3 | nan | 30.2 | 0.83 | nan | nan | nan | 1.40 |
| 6 | FFTW | 409.6 | nan | 29.5 | 0.96 | nan | nan | nan | 1.43 |
| 6 | ducc0 | 805.3 | nan | 15.0 | 0.98 | nan | nan | nan | 2.81 |
| 8 | SweepFFT | 291.8 | nan | 55.2 | 0.96 | nan | nan | nan | – |
| 8 | MKL | 407.3 | nan | 39.5 | 0.81 | nan | nan | nan | 1.40 |
| 8 | FFTW | 416.7 | nan | 38.6 | 0.94 | nan | nan | nan | 1.43 |
| 8 | ducc0 | 815.9 | nan | 19.7 | 0.96 | nan | nan | nan | 2.80 |

## Method B: one FFT with controlled background load

Load kernel triad, placement same-llc (every load core shares the FFT core’s LLC). Background bandwidth: measured alone (memory-controller counters) and during the FFT (the load's own byte count). Slowdown = time / time at level 0 (same round), median over rounds.

**n = 3·2^20**

| level | background alone, DRAM GB/s | background during FFT (logical GB/s) | SweepFFT slowdown | MKL slowdown | FFTW slowdown | ducc0 slowdown | SweepFFT vs MKL | vs FFTW | vs ducc0 | system DRAM GB/s (SweepFFT run) |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 | nan | 0.0 | 1.00 | 1.00 | 1.00 | 1.00 | 1.08 | 1.36 | 3.11 | nan |
| 1x0.25 | nan | nan | 1.00 | 1.03 | 1.01 | 0.99 | 1.12 | 1.38 | 3.08 | nan |
| 1x0.5 | nan | nan | 1.05 | 1.06 | 1.02 | 1.03 | 1.08 | 1.32 | 2.97 | nan |
| 1x0.75 | nan | nan | 1.01 | 1.06 | 1.03 | 1.03 | 1.14 | 1.39 | 3.19 | nan |
| 1 | nan | nan | 1.01 | 1.08 | 1.04 | 1.05 | 1.15 | 1.40 | 3.24 | nan |
| 2x0.75 | nan | nan | 1.03 | 1.09 | 1.05 | 1.03 | 1.15 | 1.39 | 3.10 | nan |
| 2 | nan | nan | 1.05 | 1.11 | 1.06 | 1.09 | 1.14 | 1.39 | 3.15 | nan |
| 4 | nan | nan | 1.05 | 1.15 | 1.12 | 1.15 | 1.19 | 1.46 | 3.35 | nan |

**n = 2^22**

| level | background alone, DRAM GB/s | background during FFT (logical GB/s) | SweepFFT slowdown | MKL slowdown | FFTW slowdown | ducc0 slowdown | SweepFFT vs MKL | vs FFTW | vs ducc0 | system DRAM GB/s (SweepFFT run) |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 | nan | 0.0 | 1.00 | 1.00 | 1.00 | 1.00 | 1.08 | 1.44 | 2.99 | nan |
| 1x0.25 | nan | nan | 1.01 | 1.03 | 1.00 | 1.02 | 1.10 | 1.43 | 3.04 | nan |
| 1x0.5 | nan | nan | 1.02 | 1.05 | 1.03 | 1.04 | 1.12 | 1.46 | 3.05 | nan |
| 1x0.75 | nan | nan | 1.01 | 1.06 | 1.02 | 1.07 | 1.13 | 1.45 | 3.16 | nan |
| 1 | nan | nan | 1.01 | 1.07 | 1.03 | 1.08 | 1.15 | 1.46 | 3.19 | nan |
| 2x0.75 | nan | nan | 1.02 | 1.09 | 1.04 | 1.07 | 1.15 | 1.46 | 3.15 | nan |
| 2 | nan | nan | 1.04 | 1.11 | 1.05 | 1.12 | 1.14 | 1.45 | 3.20 | nan |
| 4 | nan | nan | 1.06 | 1.16 | 1.09 | 1.16 | 1.18 | 1.48 | 3.32 | nan |

**n = 2^24**

| level | background alone, DRAM GB/s | background during FFT (logical GB/s) | SweepFFT slowdown | MKL slowdown | FFTW slowdown | ducc0 slowdown | SweepFFT vs MKL | vs FFTW | vs ducc0 | system DRAM GB/s (SweepFFT run) |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 | nan | 0.0 | 1.00 | 1.00 | 1.00 | 1.00 | 1.13 | 1.41 | 2.82 | nan |
| 1x0.25 | nan | nan | 1.02 | 1.08 | 1.01 | 1.04 | 1.19 | 1.38 | 2.86 | nan |
| 1x0.5 | nan | nan | 1.03 | 1.07 | 1.02 | 1.05 | 1.18 | 1.39 | 2.86 | nan |
| 1x0.75 | nan | nan | 1.02 | 1.08 | 1.02 | 1.06 | 1.20 | 1.40 | 2.94 | nan |
| 1 | nan | nan | 1.03 | 1.09 | 1.03 | 1.08 | 1.22 | 1.41 | 2.95 | nan |
| 2x0.75 | nan | nan | 1.04 | 1.16 | 1.04 | 1.09 | 1.26 | 1.40 | 2.95 | nan |
| 2 | nan | nan | 1.03 | 1.14 | 1.05 | 1.12 | 1.25 | 1.43 | 3.05 | nan |
| 4 | nan | nan | 1.06 | 1.38 | 1.09 | 1.16 | 1.48 | 1.45 | 3.09 | nan |

**Sensitivity to background bandwidth**: slope of log(slowdown) against the background bandwidth measured alone (memory-controller counters where calibrated, otherwise the load's byte count), % per 10 GB/s, with 95% CI (all levels and rounds).

| n | SweepFFT | MKL | FFTW | ducc0 |
|---|---|---|---|---|
| 3·2^20 | +0.9 [+0.3, +1.5] | +2.6 [+2.2, +3.1] | +2.3 [+2.0, +2.5] | +2.6 [+1.8, +3.3] |
| 2^22 | +1.1 [+0.5, +1.6] | +2.6 [+2.2, +3.0] | +1.7 [+1.5, +1.9] | +2.7 [+2.0, +3.5] |
| 2^24 | +0.7 [+0.3, +1.1] | +5.6 [+4.5, +6.6] | +1.7 [+1.5, +1.9] | +2.6 [+2.2, +3.1] |
