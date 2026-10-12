# Fairness and protocol sensitivity (`scripts/fairness.py`)

Rounds (independent blocks): 3; sizes: 2^18, 2^20, 3·2^20, 2^22, 5·2^21, 2^24, 2^25. Speedup = library time / SweepFFT time, paired within a round, geometric mean with 95% t interval over rounds; > 1 means SweepFFT is faster. † = FFTW's planner hit its time limit (plan truncated).

Correctness: 242 rows checked against the quad reference (n ≤ 2^20), max relative RMS error 3.3e-16; 0 rows above 1e-14.

MKL code path: Intel(R) Architecture processors.

## Unadjusted: the headline protocol (FFTW wisdom imported, default paging)

| n | pmfft vs mkl | pmfft vs fftw_measure | pmfft vs ducc |
|---|---|---|---|
| 2^18 | 1.74 [1.72, 1.75] | 1.26 [1.25, 1.27] | 2.04 [2.02, 2.06] |
| 2^20 | 1.31 [1.25, 1.36] | 1.39 [1.35, 1.43] | 1.75 [1.74, 1.77] |
| 3·2^20 | 3.94 [3.83, 4.05] | 1.05 [1.03, 1.06] | 2.42 [2.40, 2.43] |
| 2^22 | 1.66 [1.62, 1.70] | 1.56 [1.52, 1.60] | 2.34 [2.30, 2.38] |
| 5·2^21 | 5.93 [5.73, 6.14] | 10.17 [9.77, 10.58] | 2.23 [2.16, 2.32] |
| 2^24 | 1.59 [1.57, 1.60] | 1.49 [1.47, 1.51] | 2.23 [2.19, 2.26] |
| 2^25 | 1.66 [1.65, 1.67] | 1.58 [1.56, 1.59] | 2.24 [2.20, 2.28] |

## Matched protocol: all planners from scratch, huge pages for all memory

| n | pmfft vs mkl | pmfft vs fftw_measure_fresh | pmfft vs ducc | pmfft_heur vs mkl | pmfft_heur vs fftw_measure_fresh | pmfft_heur vs ducc |
|---|---|---|---|---|---|---|
| 2^18 | 1.76 [1.72, 1.80] | 1.16 [1.13, 1.20] | 2.08 [2.02, 2.15] | 0.20 [0.20, 0.20] | 0.13 [0.12, 0.14] | 0.23 [0.23, 0.23] |
| 2^20 | 1.29 [1.26, 1.32] | 1.39 [1.36, 1.42] | 1.83 [1.80, 1.85] | 0.84 [0.84, 0.84] | 0.90 [0.90, 0.90] | 1.19 [1.17, 1.20] |
| 3·2^20 | 3.17 [3.07, 3.27] | 11.46 [11.38, 11.53] † | 1.92 [1.92, 1.92] | 3.16 [3.08, 3.25] | 11.42 [11.17, 11.68] † | 1.91 [1.88, 1.95] |
| 2^22 | 1.65 [1.28, 2.13] | 1.56 [1.21, 2.01] | 2.38 [1.83, 3.10] | 1.35 [1.34, 1.36] | 1.28 [1.27, 1.29] | 1.95 [1.90, 2.00] |
| 5·2^21 | 5.95 [5.07, 6.99] | 10.23 [8.68, 12.06] † | 2.23 [1.86, 2.66] | 5.07 [5.05, 5.10] | 8.72 [8.72, 8.73] † | 1.90 [1.85, 1.94] |
| 2^24 | 1.86 [1.82, 1.90] | 13.20 [12.93, 13.47] † | 3.31 [3.27, 3.35] | 1.35 [1.34, 1.35] | 9.56 [9.51, 9.61] † | 2.40 [2.36, 2.44] |
| 2^25 | 1.60 [1.50, 1.71] | 7.25 [6.83, 7.69] † | 2.75 [2.56, 2.94] | 1.96 [1.95, 1.97] | 8.88 [8.80, 8.96] † | 3.36 [3.31, 3.42] |

## Sensitivity: SweepFFT (pmfft) speedup under each condition

**vs MKL**

| condition | 2^18 | 2^20 | 3·2^20 | 2^22 | 5·2^21 | 2^24 | 2^25 |
|---|---|---|---|---|---|---|---|
| headline protocol | 1.74 | 1.31 | 3.94 | 1.66 | 5.93 | 1.59 | 1.66 |
| in-place | 1.63 | 1.08 | 4.00 | 1.52 | 6.77 | 1.44 | 1.52 |
| cold caches | 1.62 | 1.27 | 3.95 | 1.64 | 5.94 | 1.57 | 1.64 |
| fresh arrays | 1.58 | 1.21 | 3.59 | 1.52 | 5.42 | 1.45 | 1.51 |
| 4 KB pages only | 1.73 | 1.23 | 1.92 | 1.16 | 1.69 | 1.08 | 1.01 |
| huge pages for all | 1.76 | 1.29 | 3.75 | 1.74 | 6.23 | 1.82 | 1.65 |
| matched protocol | 1.76 | 1.29 | 3.17 | 1.65 | 5.95 | 1.86 | 1.60 |

**vs FFTW MEASURE**

| condition | 2^18 | 2^20 | 3·2^20 | 2^22 | 5·2^21 | 2^24 | 2^25 |
|---|---|---|---|---|---|---|---|
| headline protocol | 1.26 | 1.39 | 1.05 | 1.56 | 10.17 | 1.49 | 1.58 |
| in-place | 1.44 | 1.38 | 1.42 † | 1.50 | 4.96 † | 1.41 | 3.75 † |
| cold caches | 1.30 | 1.37 | 1.05 | 1.54 | 10.20 | 1.48 | 1.56 |
| fresh arrays | 1.16 | 1.28 | 1.02 | 1.49 | 9.23 | 1.43 | 1.50 |
| 4 KB pages only | 1.38 | 1.27 | 1.00 | 1.19 | 3.08 | 1.35 | 1.12 |
| huge pages for all | 1.28 | 1.38 | 1.01 | 1.64 | 10.70 | 1.72 | 1.57 |
| matched protocol | 1.16 | 1.39 | 11.46 † | 1.56 | 10.23 † | 13.20 † | 7.25 † |

## Do the baseline wins persist?

A *win* is a baseline (size, library) pair with speedup > 1 whose 95% interval excludes 1 (capped FFTW plans excluded). For each condition: how many of those wins remain > 1, and the range of the speedups there.

| condition | wins kept | speedup range on baseline wins | min speedup out of cache (n ≥ 2^22) |
|---|---|---|---|
| headline protocol | 21/21 | 1.05–10.17 | 1.49 |
| in-place | 18/18 | 1.08–6.77 | 1.41 |
| cold caches | 21/21 | 1.05–10.20 | 1.48 |
| fresh arrays | 21/21 | 1.02–9.23 | 1.43 |
| 4 KB pages only | 21/21 | 1.00–3.08 | 1.01 |
| huge pages for all | 21/21 | 1.01–10.70 | 1.57 |
| matched protocol | 17/17 | 1.16–5.95 | 1.56 |

## First call vs steady state (baseline)

t_first / t_med: the first call of a freshly planned transform relative to the steady-state median; and SweepFFT's speedup if only the first call is counted.

| n | pmfft first/steady | pmfft_heur first/steady | mkl first/steady | fftw_measure first/steady | ducc first/steady | first-call speedup vs MKL | vs FFTW |
|---|---|---|---|---|---|---|---|
| 2^18 | 1.44 | 1.04 | 1.42 | 1.42 | 2.54 | 1.71 | 1.24 |
| 2^20 | 1.02 | 1.20 | 1.01 | 1.04 | 1.58 | 1.30 | 1.43 |
| 3·2^20 | 1.00 | 1.15 | 1.00 | 1.00 | 1.29 | 3.95 | 1.05 |
| 2^22 | 1.01 | 1.13 | 1.00 | 1.01 | 1.28 | 1.65 | 1.56 |
| 5·2^21 | 1.01 | 1.13 | 1.00 | 1.00 | 1.31 | 5.92 | 10.15 |
| 2^24 | 1.00 | 1.13 | 1.00 | 1.00 | 1.29 | 1.57 | 1.48 |
| 2^25 | 1.00 | 1.13 | 1.00 | 1.00 | 1.28 | 1.66 | 1.57 |

## FFTW: requested planner flag vs planning actually done (baseline)

Planning time (median over rounds, s), steady-state GFlop/s and whether the chosen plan equals the plan found by a fresh MEASURE / fresh PATIENT search (solver chains compared).

| n | fftw_estimate | fftw_estimate_wisdom | fftw_measure | fftw_measure_fresh | fftw_patient_fresh | imported MEASURE = fresh MEASURE? | = fresh PATIENT? |
|---|---|---|---|---|---|---|---|
| 2^18 | 0.00 s, 0.9 GF | 0.01 s, 13.6 GF | 0.01 s, 13.6 GF | 8.84 s, 14.6 GF | 175.67 s, 15.3 GF | no | no |
| 2^20 | 0.00 s, 1.9 GF | 0.00 s, 7.3 GF | 0.00 s, 7.3 GF | 4.77 s, 7.2 GF | 300.01 s, 7.2 GF † | yes | yes |
| 3·2^20 | 0.01 s, 0.7 GF | 0.04 s, 8.8 GF | 0.04 s, 8.8 GF | 60.10 s, 0.7 GF † | 300.07 s, 0.7 GF † | no | no |
| 2^22 | 0.00 s, 0.7 GF | 0.00 s, 5.8 GF | 0.00 s, 5.8 GF | 18.69 s, 5.8 GF | 300.03 s, 5.9 GF † | yes | yes |
| 5·2^21 | 0.06 s, 0.9 GF | 0.06 s, 0.9 GF | 0.06 s, 0.9 GF | 60.77 s, 0.9 GF † | 300.40 s, 0.9 GF † | yes | yes |
| 2^24 | 0.00 s, 0.8 GF | 0.00 s, 6.0 GF | 0.00 s, 6.0 GF | 60.89 s, 0.8 GF † | 300.96 s, 6.0 GF † | no | no |
| 2^25 | 0.00 s, 1.2 GF | 0.00 s, 5.8 GF | 0.00 s, 5.8 GF | 62.83 s, 1.2 GF † | 302.42 s, 5.7 GF † | no | no |

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
| 2^18 | 1.00 [0.97, 1.03] | 0.92 [0.91, 0.93] |
| 2^20 | 1.01 [0.96, 1.06] | 1.01 [0.99, 1.03] |
| 3·2^20 | 1.00 [0.99, 1.01] | 1.00 [0.97, 1.03] |
| 2^22 | 0.99 [0.97, 1.01] | 1.00 [0.99, 1.01] |
| 5·2^21 | 1.00 [0.95, 1.05] | 0.99 [0.94, 1.06] |
| 2^24 | 1.00 [0.99, 1.01] | 1.00 [1.00, 1.01] |
| 2^25 | 1.01 [0.96, 1.06] | 1.01 [0.93, 1.11] |
