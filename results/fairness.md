# Fairness and protocol sensitivity (`scripts/fairness.py`)

Rounds (independent blocks): 3; sizes: 2^18, 2^20, 3·2^20, 2^22, 5·2^21, 2^24, 2^25. Speedup = library time / SweepFFT time, paired within a round, geometric mean with 95% t interval over rounds; > 1 means SweepFFT is faster. † = FFTW's planner hit its time limit (plan truncated).

Correctness: 242 rows checked against the quad reference (n ≤ 2^20), max relative RMS error 3.3e-16; 0 rows above 1e-14.

MKL code path: Intel(R) Advanced Vector Extensions 2 (Intel(R) AVX-2) with support of Intel(R) Deep Learning Boost (Intel(R) DL Boost).

## Unadjusted: the headline protocol (FFTW wisdom imported, default paging)

| n | pmfft vs mkl | pmfft vs fftw_measure | pmfft vs ducc |
|---|---|---|---|
| 2^18 | 0.76 [0.71, 0.80] | 1.06 [1.02, 1.11] | 1.60 [1.55, 1.65] |
| 2^20 | 0.94 [0.88, 1.00] | 1.02 [0.96, 1.09] | 1.92 [1.88, 1.97] |
| 3·2^20 | 2.53 [2.52, 2.54] | 3.47 [3.30, 3.65] | 2.16 [2.06, 2.26] |
| 2^22 | 1.10 [1.06, 1.13] | 1.49 [1.43, 1.55] | 2.20 [1.81, 2.69] |
| 5·2^21 | 2.77 [2.75, 2.78] | 3.80 [3.60, 4.00] | 2.15 [2.12, 2.19] |
| 2^24 | 1.15 [0.98, 1.34] | 1.81 [1.58, 2.06] | 1.97 [1.74, 2.24] |
| 2^25 | 1.16 [1.13, 1.19] | 1.46 [1.41, 1.51] | 2.00 [1.92, 2.08] |

## Matched protocol: all planners from scratch, huge pages for all memory

| n | pmfft vs mkl | pmfft vs fftw_measure_fresh | pmfft vs ducc | pmfft_heur vs mkl | pmfft_heur vs fftw_measure_fresh | pmfft_heur vs ducc |
|---|---|---|---|---|---|---|
| 2^18 | 0.75 [0.74, 0.76] | 0.87 [0.83, 0.91] | 1.77 [1.15, 2.72] | 0.74 [0.71, 0.78] | 0.86 [0.79, 0.93] | 1.75 [1.10, 2.80] |
| 2^20 | 0.98 [0.93, 1.04] | 1.08 [0.94, 1.23] | 2.08 [1.84, 2.36] | 0.95 [0.91, 0.98] | 1.04 [0.93, 1.15] | 2.00 [1.76, 2.28] |
| 3·2^20 | 2.50 [2.33, 2.69] | 3.31 [3.09, 3.53] † | 2.14 [1.87, 2.45] | 2.49 [2.30, 2.69] | 3.28 [3.09, 3.50] † | 2.13 [1.87, 2.42] |
| 2^22 | 1.05 [1.01, 1.10] | 1.25 [1.19, 1.31] | 2.20 [2.12, 2.29] | 1.03 [1.00, 1.06] | 1.22 [1.19, 1.25] | 2.16 [2.13, 2.18] |
| 5·2^21 | 2.69 [2.55, 2.83] | 3.64 [3.40, 3.89] † | 2.12 [2.03, 2.21] | 2.69 [2.62, 2.76] | 3.64 [3.49, 3.80] † | 2.12 [2.04, 2.21] |
| 2^24 | 1.18 [1.14, 1.22] | 4.38 [4.19, 4.59] † | 2.15 [2.00, 2.31] | 1.17 [1.11, 1.22] | 4.34 [4.11, 4.58] † | 2.13 [1.95, 2.32] |
| 2^25 | 1.16 [1.14, 1.17] | 4.20 [4.14, 4.26] † | 2.06 [2.06, 2.07] | 1.13 [1.11, 1.16] | 4.11 [3.96, 4.26] † | 2.02 [1.96, 2.08] |

## Sensitivity: SweepFFT (pmfft) speedup under each condition

**vs MKL**

| condition | 2^18 | 2^20 | 3·2^20 | 2^22 | 5·2^21 | 2^24 | 2^25 |
|---|---|---|---|---|---|---|---|
| headline protocol | 0.76 | 0.94 | 2.53 | 1.10 | 2.77 | 1.15 | 1.16 |
| in-place | 0.67 | 0.66 | 2.47 | 1.01 | 3.32 | 1.03 | 0.99 |
| cold caches | 0.84 | 0.89 | 2.46 | 1.05 | 2.76 | 1.19 | 1.15 |
| fresh arrays | 0.80 | 0.94 | 2.29 | 1.05 | 2.46 | 1.14 | 1.10 |
| 4 KB pages only | 0.77 | 0.82 | 2.68 | 0.96 | 2.68 | 0.99 | 0.96 |
| huge pages for all | 0.76 | 0.95 | 2.46 | 1.06 | 2.69 | 1.17 | 1.15 |
| matched protocol | 0.75 | 0.98 | 2.50 | 1.05 | 2.69 | 1.18 | 1.16 |

**vs FFTW MEASURE**

| condition | 2^18 | 2^20 | 3·2^20 | 2^22 | 5·2^21 | 2^24 | 2^25 |
|---|---|---|---|---|---|---|---|
| headline protocol | 1.06 | 1.02 | 3.47 | 1.49 | 3.80 | 1.81 | 1.46 |
| in-place | 0.71 | 0.95 | 1.45 | 1.53 | 2.80 † | 1.26 | 2.72 † |
| cold caches | 1.07 | 0.97 | 3.26 | 1.45 | 3.73 | 1.87 | 1.44 |
| fresh arrays | 1.10 | 0.99 | 3.10 | 1.39 | 3.28 | 1.79 | 1.41 |
| 4 KB pages only | 0.94 | 0.93 | 2.92 | 1.05 | 3.29 | 1.02 | 1.04 |
| huge pages for all | 1.08 | 1.03 | 3.30 | 1.42 | 3.72 | 1.85 | 1.44 |
| matched protocol | 0.87 | 1.08 | 3.31 † | 1.25 | 3.64 † | 4.38 † | 4.20 † |

## Do the baseline wins persist?

A *win* is a baseline (size, library) pair with speedup > 1 whose 95% interval excludes 1 (capped FFTW plans excluded). For each condition: how many of those wins remain > 1, and the range of the speedups there.

| condition | wins kept | speedup range on baseline wins | min speedup out of cache (n ≥ 2^22) |
|---|---|---|---|
| headline protocol | 17/17 | 1.06–3.80 | 1.10 |
| in-place | 13/15 | 0.71–3.32 | 0.99 |
| cold caches | 17/17 | 1.05–3.73 | 1.05 |
| fresh arrays | 17/17 | 1.05–3.28 | 1.05 |
| 4 KB pages only | 14/17 | 0.94–3.29 | 0.96 |
| huge pages for all | 17/17 | 1.06–3.72 | 1.06 |
| matched protocol | 12/13 | 0.87–2.69 | 1.05 |

## First call vs steady state (baseline)

t_first / t_med: the first call of a freshly planned transform relative to the steady-state median; and SweepFFT's speedup if only the first call is counted.

| n | pmfft first/steady | pmfft_heur first/steady | mkl first/steady | fftw_measure first/steady | ducc first/steady | first-call speedup vs MKL | vs FFTW |
|---|---|---|---|---|---|---|---|
| 2^18 | 1.44 | 1.55 | 1.21 | 1.08 | 1.94 | 0.64 | 0.81 |
| 2^20 | 0.99 | 1.36 | 1.00 | 1.04 | 1.53 | 0.94 | 1.07 |
| 3·2^20 | 1.02 | 1.19 | 1.00 | 1.00 | 1.26 | 2.49 | 3.38 |
| 2^22 | 1.01 | 1.20 | 1.00 | 1.03 | 1.32 | 1.08 | 1.52 |
| 5·2^21 | 1.00 | 1.20 | 1.02 | 1.02 | 1.23 | 2.82 | 3.85 |
| 2^24 | 1.00 | 1.15 | 1.01 | 1.00 | 1.22 | 1.20 | 1.88 |
| 2^25 | 1.00 | 1.15 | 1.00 | 1.00 | 1.23 | 1.16 | 1.47 |

## FFTW: requested planner flag vs planning actually done (baseline)

Planning time (median over rounds, s), steady-state GFlop/s and whether the chosen plan equals the plan found by a fresh MEASURE / fresh PATIENT search (solver chains compared).

| n | fftw_estimate | fftw_estimate_wisdom | fftw_measure | fftw_measure_fresh | fftw_patient_fresh | imported MEASURE = fresh MEASURE? | = fresh PATIENT? |
|---|---|---|---|---|---|---|---|
| 2^18 | 0.00 s, 9.4 GF | 0.00 s, 20.7 GF | 0.00 s, 20.7 GF | 4.91 s, 22.6 GF | 93.60 s, 28.3 GF | no | no |
| 2^20 | 0.00 s, 7.7 GF | 0.00 s, 17.7 GF | 0.00 s, 17.8 GF | 2.19 s, 18.0 GF | 300.01 s, 18.0 GF † | no | no |
| 3·2^20 | 0.00 s, 4.8 GF | 0.00 s, 4.8 GF | 0.00 s, 4.8 GF | 60.02 s, 4.8 GF † | 300.10 s, 4.7 GF † | yes | yes |
| 2^22 | 0.00 s, 3.8 GF | 0.00 s, 11.3 GF | 0.00 s, 11.2 GF | 9.84 s, 11.1 GF | 300.06 s, 10.8 GF † | yes | yes |
| 5·2^21 | 0.02 s, 4.5 GF | 0.02 s, 4.5 GF | 0.02 s, 4.5 GF | 60.31 s, 4.5 GF † | 300.08 s, 4.5 GF † | yes | yes |
| 2^24 | 0.00 s, 3.7 GF | 0.00 s, 8.8 GF | 0.00 s, 8.9 GF | 42.81 s, 11.2 GF | 300.04 s, 11.1 GF † | no | no |
| 2^25 | 0.00 s, 3.8 GF | 0.00 s, 10.9 GF | 0.00 s, 10.9 GF | 58.03 s, 11.1 GF † | 300.39 s, 11.5 GF † | no | no |

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
| 2^18 | 0.99 [0.97, 1.02] | 0.94 [0.72, 1.22] |
| 2^20 | 0.95 [0.90, 1.01] | 0.97 [0.90, 1.04] |
| 3·2^20 | 0.99 [0.97, 1.00] | 0.99 [0.92, 1.07] |
| 2^22 | 0.99 [0.94, 1.06] | 0.96 [0.90, 1.03] |
| 5·2^21 | 0.99 [0.97, 1.02] | 1.00 [0.95, 1.04] |
| 2^24 | 1.00 [0.94, 1.06] | 0.99 [0.98, 1.00] |
| 2^25 | 1.01 [0.97, 1.06] | 1.00 [0.97, 1.03] |
