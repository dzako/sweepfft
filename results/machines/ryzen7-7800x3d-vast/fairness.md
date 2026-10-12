# Fairness and protocol sensitivity (`scripts/fairness.py`)

Rounds (independent blocks): 3; sizes: 2^18, 2^20, 3·2^20, 2^22, 5·2^21, 2^24, 2^25. Speedup = library time / SweepFFT time, paired within a round, geometric mean with 95% t interval over rounds; > 1 means SweepFFT is faster. † = FFTW's planner hit its time limit (plan truncated).

Correctness: 242 rows checked against the quad reference (n ≤ 2^20), max relative RMS error 3.3e-16; 0 rows above 1e-14.

MKL code path: Intel(R) Architecture processors.

## Unadjusted: the headline protocol (FFTW wisdom imported, default paging)

| n | pmfft vs mkl | pmfft vs fftw_measure | pmfft vs ducc |
|---|---|---|---|
| 2^18 | 1.63 [1.61, 1.64] | 1.08 [1.07, 1.09] | 2.38 [2.31, 2.47] |
| 2^20 | 0.95 [0.86, 1.04] | 0.98 [0.89, 1.09] | 1.32 [1.21, 1.45] |
| 3·2^20 | 1.92 [1.68, 2.20] | 0.85 [0.84, 0.85] | 1.49 [1.46, 1.52] |
| 2^22 | 1.03 [0.99, 1.08] | 1.05 [1.02, 1.08] | 1.52 [1.46, 1.59] |
| 5·2^21 | 2.19 [1.78, 2.70] | 2.03 [1.63, 2.53] | 1.70 [1.35, 2.13] |
| 2^24 | 1.13 [1.10, 1.16] | 0.99 [0.98, 1.00] | 1.58 [1.56, 1.61] |
| 2^25 | 1.29 [1.28, 1.31] | 1.53 [1.51, 1.55] | 1.68 [1.66, 1.69] |

## Matched protocol: all planners from scratch, huge pages for all memory

| n | pmfft vs mkl | pmfft vs fftw_measure_fresh | pmfft vs ducc | pmfft_heur vs mkl | pmfft_heur vs fftw_measure_fresh | pmfft_heur vs ducc |
|---|---|---|---|---|---|---|
| 2^18 | 1.63 [1.62, 1.65] | 1.05 [0.96, 1.15] | 2.45 [2.36, 2.55] | 1.47 [1.45, 1.48] | 0.95 [0.87, 1.03] | 2.21 [2.12, 2.29] |
| 2^20 | 0.97 [0.95, 0.98] | 1.01 [0.98, 1.04] | 1.42 [1.40, 1.44] | 0.61 [0.51, 0.74] | 0.64 [0.52, 0.78] | 0.90 [0.74, 1.10] |
| 3·2^20 | 1.95 [1.81, 2.11] | 1.46 [1.29, 1.66] † | 1.46 [1.40, 1.51] | 1.38 [1.20, 1.60] | 1.04 [0.84, 1.27] † | 1.03 [0.88, 1.21] |
| 2^22 | 0.81 [0.57, 1.14] | 0.86 [0.67, 1.11] | 1.23 [0.97, 1.55] | 0.69 [0.54, 0.87] | 0.73 [0.63, 0.84] | 1.04 [0.91, 1.17] |
| 5·2^21 | 2.41 [2.37, 2.45] | 2.25 [2.23, 2.28] † | 1.82 [1.81, 1.84] | 1.58 [1.55, 1.61] | 1.48 [1.41, 1.55] † | 1.20 [1.16, 1.24] |
| 2^24 | 1.25 [1.24, 1.26] | 1.16 [1.15, 1.18] † | 1.87 [1.85, 1.89] | 0.97 [0.64, 1.48] | 0.90 [0.59, 1.38] † | 1.45 [0.95, 2.20] |
| 2^25 | 1.30 [1.22, 1.39] | 2.36 [2.20, 2.54] † | 1.87 [1.72, 2.03] | 1.51 [1.49, 1.53] | 2.74 [2.72, 2.76] † | 2.17 [2.14, 2.20] |

## Sensitivity: SweepFFT (pmfft) speedup under each condition

**vs MKL**

| condition | 2^18 | 2^20 | 3·2^20 | 2^22 | 5·2^21 | 2^24 | 2^25 |
|---|---|---|---|---|---|---|---|
| headline protocol | 1.63 | 0.95 | 1.92 | 1.03 | 2.19 | 1.13 | 1.29 |
| in-place | 1.49 | 0.85 | 1.61 | 0.79 | 2.95 | 1.00 | 1.18 |
| cold caches | 1.57 | 1.10 | 2.07 | 1.07 | 2.23 | 1.13 | 1.31 |
| fresh arrays | 1.65 | 0.96 | 1.45 | 1.02 | 2.02 | 1.05 | 1.24 |
| 4 KB pages only | 1.62 | 0.88 | 1.85 | 1.00 | 2.32 | 1.13 | 1.30 |
| huge pages for all | 1.63 | 0.96 | 1.67 | 0.80 | 2.15 | 1.36 | 1.32 |
| matched protocol | 1.63 | 0.97 | 1.95 | 0.81 | 2.41 | 1.25 | 1.30 |

**vs FFTW MEASURE**

| condition | 2^18 | 2^20 | 3·2^20 | 2^22 | 5·2^21 | 2^24 | 2^25 |
|---|---|---|---|---|---|---|---|
| headline protocol | 1.08 | 0.98 | 0.85 | 1.05 | 2.03 | 0.99 | 1.53 |
| in-place | 1.08 | 0.90 | 0.73 | 0.85 | 1.69 † | 0.92 | 1.82 † |
| cold caches | 1.14 | 1.14 | 0.97 | 1.06 | 1.96 | 0.97 | 1.53 |
| fresh arrays | 1.06 | 1.00 | 0.74 | 1.08 | 1.70 | 0.99 | 1.50 |
| 4 KB pages only | 1.09 | 0.94 | 0.86 | 1.04 | 1.88 | 1.06 | 1.15 |
| huge pages for all | 1.07 | 1.00 | 0.74 | 0.86 | 2.01 | 1.22 | 1.57 |
| matched protocol | 1.05 | 1.01 | 1.46 † | 0.86 | 2.25 † | 1.16 † | 2.36 † |

## Do the baseline wins persist?

A *win* is a baseline (size, library) pair with speedup > 1 whose 95% interval excludes 1 (capped FFTW plans excluded). For each condition: how many of those wins remain > 1, and the range of the speedups there.

| condition | wins kept | speedup range on baseline wins | min speedup out of cache (n ≥ 2^22) |
|---|---|---|---|
| headline protocol | 16/16 | 1.05–2.38 | 0.99 |
| in-place | 12/14 | 0.85–2.95 | 0.79 |
| cold caches | 16/16 | 1.06–2.23 | 0.97 |
| fresh arrays | 16/16 | 1.05–2.38 | 0.99 |
| 4 KB pages only | 16/16 | 1.04–2.36 | 1.00 |
| huge pages for all | 15/16 | 0.86–2.43 | 0.80 |
| matched protocol | 13/14 | 0.86–2.45 | 0.81 |

## First call vs steady state (baseline)

t_first / t_med: the first call of a freshly planned transform relative to the steady-state median; and SweepFFT's speedup if only the first call is counted.

| n | pmfft first/steady | pmfft_heur first/steady | mkl first/steady | fftw_measure first/steady | ducc first/steady | first-call speedup vs MKL | vs FFTW |
|---|---|---|---|---|---|---|---|
| 2^18 | 1.30 | 1.23 | 1.09 | 1.19 | 1.57 | 1.36 | 0.99 |
| 2^20 | 1.17 | 1.12 | 1.18 | 1.16 | 1.58 | 0.97 | 0.99 |
| 3·2^20 | 1.17 | 1.18 | 1.13 | 1.07 | 1.47 | 1.91 | 0.78 |
| 2^22 | 1.14 | 1.20 | 1.15 | 1.07 | 1.39 | 1.03 | 0.97 |
| 5·2^21 | 1.01 | 1.14 | 1.00 | 0.99 | 1.24 | 2.07 | 1.89 |
| 2^24 | 1.00 | 1.12 | 1.03 | 1.00 | 1.21 | 1.16 | 1.00 |
| 2^25 | 1.00 | 1.14 | 1.01 | 1.01 | 1.22 | 1.31 | 1.54 |

## FFTW: requested planner flag vs planning actually done (baseline)

Planning time (median over rounds, s), steady-state GFlop/s and whether the chosen plan equals the plan found by a fresh MEASURE / fresh PATIENT search (solver chains compared).

| n | fftw_estimate | fftw_estimate_wisdom | fftw_measure | fftw_measure_fresh | fftw_patient_fresh | imported MEASURE = fresh MEASURE? | = fresh PATIENT? |
|---|---|---|---|---|---|---|---|
| 2^18 | 0.00 s, 9.1 GF | 0.00 s, 28.6 GF | 0.00 s, 28.5 GF | 5.26 s, 28.2 GF | 103.48 s, 32.8 GF | no | no |
| 2^20 | 0.00 s, 10.1 GF | 0.00 s, 17.7 GF | 0.00 s, 17.8 GF | 2.36 s, 17.7 GF | 300.01 s, 17.1 GF † | yes | yes |
| 3·2^20 | 0.01 s, 11.5 GF | 0.01 s, 20.2 GF | 0.01 s, 20.0 GF | 60.06 s, 11.5 GF † | 300.03 s, 12.1 GF † | no | no |
| 2^22 | 0.00 s, 8.4 GF | 0.00 s, 16.0 GF | 0.00 s, 15.8 GF | 11.18 s, 15.7 GF | 300.06 s, 15.8 GF † | no | no |
| 5·2^21 | 0.03 s, 7.3 GF | 0.03 s, 7.3 GF | 0.03 s, 7.3 GF | 60.61 s, 7.3 GF † | 300.69 s, 7.4 GF † | yes | yes |
| 2^24 | 0.00 s, 7.3 GF | 0.00 s, 14.2 GF | 0.00 s, 14.1 GF | 55.31 s, 14.1 GF † | 300.06 s, 13.9 GF † | no | no |
| 2^25 | 0.00 s, 6.4 GF | 0.00 s, 9.6 GF | 0.00 s, 9.6 GF | 60.89 s, 6.3 GF † | 301.19 s, 9.3 GF † | no | yes |

## Huge-page coverage at the largest size

Resident transparent-huge-page memory / (32 n + memory the implementation adds), median over rounds.

| condition | pmfft | pmfft_heur | mkl | fftw_measure | ducc |
|---|---|---|---|---|---|
| headline protocol | 1.00 | 1.00 | 0.80 | 1.00 | 0.67 |
| 4 KB pages only | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| huge pages for all | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |

## Compiler settings: SweepFFT built for x86-64-v3 (generic tuning) vs -march=native

| n | pmfft v3 / native (time) | pmfft_heur v3 / native (time) |
|---|---|---|
| 2^18 | 1.00 [1.00, 1.00] | 1.03 [1.01, 1.06] |
| 2^20 | 0.99 [0.91, 1.08] | 1.04 [1.01, 1.07] |
| 3·2^20 | 1.04 [1.04, 1.05] | 1.04 [0.98, 1.09] |
| 2^22 | 1.03 [0.96, 1.10] | 1.04 [1.00, 1.09] |
| 5·2^21 | 1.10 [0.83, 1.45] | 1.01 [1.01, 1.02] |
| 2^24 | 1.04 [0.98, 1.10] | 1.02 [1.01, 1.04] |
| 2^25 | 1.02 [1.00, 1.04] | 1.01 [0.97, 1.06] |
