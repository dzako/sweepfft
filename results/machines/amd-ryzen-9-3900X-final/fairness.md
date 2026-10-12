# Fairness and protocol sensitivity (`scripts/fairness.py`)

Rounds (independent blocks): 3; sizes: 2^18, 2^20, 3·2^20, 2^22, 5·2^21, 2^24, 2^25. Speedup = library time / SweepFFT time, paired within a round, geometric mean with 95% t interval over rounds; > 1 means SweepFFT is faster. † = FFTW's planner hit its time limit (plan truncated).

Correctness: 242 rows checked against the quad reference (n ≤ 2^20), max relative RMS error 3.3e-16; 0 rows above 1e-14.

MKL code path: Intel(R) Architecture processors.

## Unadjusted: the headline protocol (FFTW wisdom imported, default paging)

| n | pmfft vs mkl | pmfft vs fftw_measure | pmfft vs ducc |
|---|---|---|---|
| 2^18 | 1.71 [1.71, 1.72] | 1.29 [1.25, 1.32] | 2.03 [2.01, 2.04] |
| 2^20 | 1.31 [1.29, 1.32] | 1.37 [1.33, 1.41] | 1.73 [1.66, 1.81] |
| 3·2^20 | 3.91 [3.83, 3.99] | 2.99 [2.98, 3.01] | 2.27 [2.22, 2.32] |
| 2^22 | 1.77 [1.74, 1.79] | 1.60 [1.59, 1.62] | 2.24 [2.22, 2.27] |
| 5·2^21 | 5.89 [5.82, 5.96] | 9.66 [9.41, 9.92] | 2.71 [2.66, 2.76] |
| 2^24 | 1.67 [1.65, 1.69] | 1.51 [1.51, 1.52] | 2.74 [2.73, 2.76] |
| 2^25 | 1.74 [1.73, 1.75] | 1.60 [1.58, 1.62] | 2.73 [2.71, 2.76] |

## Matched protocol: all planners from scratch, huge pages for all memory

| n | pmfft vs mkl | pmfft vs fftw_measure_fresh | pmfft vs ducc | pmfft_heur vs mkl | pmfft_heur vs fftw_measure_fresh | pmfft_heur vs ducc |
|---|---|---|---|---|---|---|
| 2^18 | 1.72 [1.65, 1.80] | 1.18 [1.09, 1.27] | 2.03 [1.94, 2.13] | 0.23 [0.23, 0.23] | 0.16 [0.15, 0.17] | 0.27 [0.27, 0.28] |
| 2^20 | 1.35 [1.32, 1.37] | 1.46 [1.31, 1.62] | 1.87 [1.83, 1.92] | 0.98 [0.67, 1.44] | 1.06 [0.65, 1.73] | 1.37 [0.94, 1.99] |
| 3·2^20 | 4.01 [3.62, 4.43] | 13.45 [12.01, 15.07] † | 2.30 [2.08, 2.55] | 3.35 [2.78, 4.04] | 11.25 [9.32, 13.57] † | 1.92 [1.58, 2.35] |
| 2^22 | 1.84 [1.63, 2.08] | 1.69 [1.49, 1.91] | 2.43 [2.12, 2.78] | 1.54 [1.17, 2.04] | 1.41 [1.07, 1.87] | 2.04 [1.56, 2.66] |
| 5·2^21 | 6.05 [5.45, 6.72] | 10.07 [9.11, 11.13] † | 2.76 [2.48, 3.08] | 4.57 [1.33, 15.66] | 7.60 [2.21, 26.17] † | 2.08 [0.61, 7.12] |
| 2^24 | 1.80 [1.78, 1.83] | 10.93 [10.83, 11.04] † | 3.77 [3.75, 3.80] | 1.12 [0.22, 5.63] | 6.79 [1.33, 34.53] † | 2.34 [0.46, 11.83] |
| 2^25 | 1.75 [1.47, 2.08] | 6.48 [5.49, 7.66] † | 3.48 [2.93, 4.12] | 1.78 [1.76, 1.81] | 6.60 [6.54, 6.66] † | 3.54 [3.50, 3.58] |

## Sensitivity: SweepFFT (pmfft) speedup under each condition

**vs MKL**

| condition | 2^18 | 2^20 | 3·2^20 | 2^22 | 5·2^21 | 2^24 | 2^25 |
|---|---|---|---|---|---|---|---|
| headline protocol | 1.71 | 1.31 | 3.91 | 1.77 | 5.89 | 1.67 | 1.74 |
| in-place | 1.59 | 1.10 | 4.01 | 1.60 | 6.74 | 1.51 | 1.59 |
| cold caches | 1.54 | 1.29 | 3.89 | 1.75 | 5.84 | 1.68 | 1.74 |
| fresh arrays | 1.50 | 1.27 | 3.58 | 1.60 | 5.48 | 1.54 | 1.59 |
| 4 KB pages only | 1.72 | 1.24 | 1.96 | 1.21 | 1.70 | 1.14 | 0.98 |
| huge pages for all | 1.74 | 1.36 | 3.94 | 1.83 | 6.24 | 1.71 | 1.75 |
| matched protocol | 1.72 | 1.35 | 4.01 | 1.84 | 6.05 | 1.80 | 1.75 |

**vs FFTW MEASURE**

| condition | 2^18 | 2^20 | 3·2^20 | 2^22 | 5·2^21 | 2^24 | 2^25 |
|---|---|---|---|---|---|---|---|
| headline protocol | 1.29 | 1.37 | 2.99 | 1.60 | 9.66 | 1.51 | 1.60 |
| in-place | 1.19 | 1.36 | 1.17 | 1.52 | 4.88 † | 1.44 | 2.94 † |
| cold caches | 1.16 | 1.36 | 3.00 | 1.59 | 9.71 | 1.52 | 1.60 |
| fresh arrays | 1.15 | 1.34 | 2.77 | 1.53 | 9.07 | 1.47 | 1.54 |
| 4 KB pages only | 1.32 | 1.26 | 1.10 | 1.19 | 2.49 | 1.35 | 1.01 |
| huge pages for all | 1.29 | 1.42 | 3.01 | 1.68 | 10.32 | 1.55 | 1.62 |
| matched protocol | 1.18 | 1.46 | 13.45 † | 1.69 | 10.07 † | 10.93 † | 6.48 † |

## Do the baseline wins persist?

A *win* is a baseline (size, library) pair with speedup > 1 whose 95% interval excludes 1 (capped FFTW plans excluded). For each condition: how many of those wins remain > 1, and the range of the speedups there.

| condition | wins kept | speedup range on baseline wins | min speedup out of cache (n ≥ 2^22) |
|---|---|---|---|
| headline protocol | 21/21 | 1.29–9.66 | 1.51 |
| in-place | 19/19 | 1.10–6.74 | 1.44 |
| cold caches | 21/21 | 1.16–9.71 | 1.52 |
| fresh arrays | 21/21 | 1.15–9.07 | 1.47 |
| 4 KB pages only | 20/21 | 0.98–2.49 | 0.98 |
| huge pages for all | 21/21 | 1.29–10.32 | 1.55 |
| matched protocol | 17/17 | 1.18–6.05 | 1.69 |

## First call vs steady state (baseline)

t_first / t_med: the first call of a freshly planned transform relative to the steady-state median; and SweepFFT's speedup if only the first call is counted.

| n | pmfft first/steady | pmfft_heur first/steady | mkl first/steady | fftw_measure first/steady | ducc first/steady | first-call speedup vs MKL | vs FFTW |
|---|---|---|---|---|---|---|---|
| 2^18 | 1.57 | 1.05 | 1.06 | 1.03 | 1.77 | 1.15 | 0.85 |
| 2^20 | 1.01 | 1.18 | 1.02 | 1.02 | 1.40 | 1.32 | 1.39 |
| 3·2^20 | 1.00 | 1.15 | 1.00 | 1.00 | 1.25 | 3.90 | 2.99 |
| 2^22 | 1.00 | 1.14 | 1.01 | 1.01 | 1.27 | 1.77 | 1.61 |
| 5·2^21 | 1.00 | 1.13 | 1.00 | 1.00 | 1.22 | 5.89 | 9.73 |
| 2^24 | 1.00 | 1.11 | 1.00 | 1.01 | 1.22 | 1.66 | 1.53 |
| 2^25 | 1.00 | 1.12 | 1.00 | 1.00 | 1.20 | 1.74 | 1.60 |

## FFTW: requested planner flag vs planning actually done (baseline)

Planning time (median over rounds, s), steady-state GFlop/s and whether the chosen plan equals the plan found by a fresh MEASURE / fresh PATIENT search (solver chains compared).

| n | fftw_estimate | fftw_estimate_wisdom | fftw_measure | fftw_measure_fresh | fftw_patient_fresh | imported MEASURE = fresh MEASURE? | = fresh PATIENT? |
|---|---|---|---|---|---|---|---|
| 2^18 | 0.00 s, 1.2 GF | 0.00 s, 16.8 GF | 0.00 s, 16.8 GF | 6.85 s, 18.5 GF | 134.52 s, 20.4 GF | no | no |
| 2^20 | 0.00 s, 2.4 GF | 0.00 s, 9.1 GF | 0.00 s, 9.1 GF | 3.73 s, 9.1 GF | 300.00 s, 9.1 GF † | no | no |
| 3·2^20 | 0.01 s, 0.9 GF | 0.06 s, 3.8 GF | 0.06 s, 3.8 GF | 60.24 s, 0.9 GF † | 300.43 s, 0.9 GF † | no | no |
| 2^22 | 0.00 s, 1.0 GF | 0.00 s, 7.2 GF | 0.00 s, 7.2 GF | 14.72 s, 7.2 GF | 300.04 s, 7.2 GF † | yes | yes |
| 5·2^21 | 0.04 s, 1.1 GF | 0.04 s, 1.1 GF | 0.04 s, 1.1 GF | 60.57 s, 1.1 GF † | 300.49 s, 1.1 GF † | yes | yes |
| 2^24 | 0.00 s, 1.1 GF | 0.00 s, 7.4 GF | 0.00 s, 7.4 GF | 61.68 s, 1.1 GF † | 300.42 s, 7.4 GF † | no | yes |
| 2^25 | 0.00 s, 1.8 GF | 0.00 s, 7.2 GF | 0.00 s, 7.1 GF | 61.82 s, 1.8 GF † | 301.65 s, 7.1 GF † | no | no |

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
| 2^18 | 1.02 [0.93, 1.11] | 1.00 [0.98, 1.02] |
| 2^20 | 0.99 [0.96, 1.02] | 1.00 [0.98, 1.03] |
| 3·2^20 | 0.99 [0.99, 1.00] | 1.00 [0.99, 1.00] |
| 2^22 | 1.00 [0.99, 1.00] | 0.99 [0.98, 1.01] |
| 5·2^21 | 0.99 [0.98, 1.00] | 1.00 [1.00, 1.00] |
| 2^24 | 1.00 [0.99, 1.00] | 1.00 [0.99, 1.01] |
| 2^25 | 1.00 [0.99, 1.01] | 0.99 [0.99, 1.00] |
