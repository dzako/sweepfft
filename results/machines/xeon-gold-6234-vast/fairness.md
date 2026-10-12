# Fairness and protocol sensitivity (`scripts/fairness.py`)

Rounds (independent blocks): 3; sizes: 2^18, 2^20, 3·2^20, 2^22, 5·2^21, 2^24, 2^25. Speedup = library time / SweepFFT time, paired within a round, geometric mean with 95% t interval over rounds; > 1 means SweepFFT is faster. † = FFTW's planner hit its time limit (plan truncated).

Correctness: 242 rows checked against the quad reference (n ≤ 2^20), max relative RMS error 3.8e-16; 0 rows above 1e-14.

MKL code path: Intel(R) Advanced Vector Extensions 512 (Intel(R) AVX-512) with support of Intel(R) Deep Learning Boost (Intel(R) DL Boost).

## Unadjusted: the headline protocol (FFTW wisdom imported, default paging)

| n | pmfft vs mkl | pmfft vs fftw_measure | pmfft vs ducc |
|---|---|---|---|
| 2^18 | 1.10 [1.09, 1.10] | 0.99 [0.98, 1.00] | 1.89 [1.74, 2.05] |
| 2^20 | 0.95 [0.78, 1.16] | 1.12 [0.95, 1.32] | 2.12 [2.03, 2.22] |
| 3·2^20 | 1.11 [1.09, 1.13] | 1.40 [1.39, 1.41] | 3.04 [2.84, 3.26] |
| 2^22 | 1.08 [1.04, 1.13] | 1.44 [1.38, 1.50] | 3.06 [2.97, 3.15] |
| 5·2^21 | 1.24 [1.19, 1.30] | 1.88 [1.84, 1.92] | 2.91 [2.77, 3.06] |
| 2^24 | 1.36 [1.20, 1.54] | 1.44 [1.39, 1.48] | 2.87 [2.79, 2.95] |
| 2^25 | 1.28 [1.19, 1.38] | 1.36 [1.35, 1.36] | 2.79 [2.75, 2.83] |

## Matched protocol: all planners from scratch, huge pages for all memory

| n | pmfft vs mkl | pmfft vs fftw_measure_fresh | pmfft vs ducc | pmfft_heur vs mkl | pmfft_heur vs fftw_measure_fresh | pmfft_heur vs ducc |
|---|---|---|---|---|---|---|
| 2^18 | 1.11 [1.10, 1.11] | 0.94 [0.79, 1.12] | 1.87 [1.86, 1.87] | 0.90 [0.90, 0.91] | 0.77 [0.64, 0.92] | 1.52 [1.51, 1.53] |
| 2^20 | 0.93 [0.73, 1.17] | 1.08 [0.95, 1.23] | 1.98 [1.72, 2.27] | 0.93 [0.77, 1.12] | 1.08 [0.89, 1.32] | 1.98 [1.88, 2.09] |
| 3·2^20 | 1.08 [1.05, 1.12] | 1.32 [1.26, 1.37] † | 2.98 [2.75, 3.23] | 1.07 [1.06, 1.08] | 1.31 [1.28, 1.33] † | 2.96 [2.78, 3.15] |
| 2^22 | 1.11 [1.09, 1.12] | 1.44 [1.41, 1.48] | 3.06 [2.93, 3.18] | 1.06 [1.03, 1.08] | 1.38 [1.33, 1.42] | 2.91 [2.79, 3.03] |
| 5·2^21 | 1.22 [1.17, 1.29] | 1.87 [1.84, 1.90] † | 2.93 [2.90, 2.95] | 1.18 [1.12, 1.25] | 1.80 [1.77, 1.83] † | 2.83 [2.78, 2.88] |
| 2^24 | 1.31 [1.21, 1.42] | 3.00 [2.89, 3.12] † | 2.88 [2.73, 3.05] | 1.22 [1.14, 1.30] | 2.79 [2.77, 2.81] † | 2.68 [2.61, 2.75] |
| 2^25 | 1.28 [1.21, 1.36] | 2.78 [2.73, 2.83] † | 2.68 [2.66, 2.70] | 1.25 [1.18, 1.32] | 2.70 [2.67, 2.74] † | 2.61 [2.58, 2.64] |

## Sensitivity: SweepFFT (pmfft) speedup under each condition

**vs MKL**

| condition | 2^18 | 2^20 | 3·2^20 | 2^22 | 5·2^21 | 2^24 | 2^25 |
|---|---|---|---|---|---|---|---|
| headline protocol | 1.10 | 0.95 | 1.11 | 1.08 | 1.24 | 1.36 | 1.28 |
| in-place | 1.33 | 1.71 | 2.15 | 2.18 | 1.68 | 1.62 | 1.57 |
| cold caches | 1.15 | 0.87 | 1.10 | 1.09 | 1.35 | 1.37 | 1.26 |
| fresh arrays | 1.10 | 0.94 | 1.05 | 1.03 | 1.09 | 1.13 | 1.09 |
| 4 KB pages only | 1.12 | 0.91 | 1.19 | 1.06 | 0.99 | 1.08 | 1.10 |
| huge pages for all | 1.11 | 0.94 | 1.07 | 1.09 | 1.22 | 1.28 | 1.29 |
| matched protocol | 1.11 | 0.93 | 1.08 | 1.11 | 1.22 | 1.31 | 1.28 |

**vs FFTW MEASURE**

| condition | 2^18 | 2^20 | 3·2^20 | 2^22 | 5·2^21 | 2^24 | 2^25 |
|---|---|---|---|---|---|---|---|
| headline protocol | 0.99 | 1.12 | 1.40 | 1.44 | 1.88 | 1.44 | 1.36 |
| in-place | 0.79 | 0.95 | 2.21 † | 1.30 | 2.26 † | 1.23 | 2.37 † |
| cold caches | 0.98 | 1.01 | 1.39 | 1.45 | 1.95 | 1.42 | 1.35 |
| fresh arrays | 0.98 | 1.10 | 1.28 | 1.35 | 1.58 | 1.35 | 1.29 |
| 4 KB pages only | 0.86 | 1.03 | 0.95 | 1.20 | 1.74 | 1.16 | 1.15 |
| huge pages for all | 1.01 | 1.12 | 1.34 | 1.44 | 1.87 | 1.42 | 1.34 |
| matched protocol | 0.94 | 1.08 | 1.32 † | 1.44 | 1.87 † | 3.00 † | 2.78 † |

## Do the baseline wins persist?

A *win* is a baseline (size, library) pair with speedup > 1 whose 95% interval excludes 1 (capped FFTW plans excluded). For each condition: how many of those wins remain > 1, and the range of the speedups there.

| condition | wins kept | speedup range on baseline wins | min speedup out of cache (n ≥ 2^22) |
|---|---|---|---|
| headline protocol | 18/18 | 1.08–3.06 | 1.08 |
| in-place | 15/15 | 1.23–3.07 | 1.23 |
| cold caches | 18/18 | 1.09–3.09 | 1.09 |
| fresh arrays | 18/18 | 1.03–2.69 | 1.03 |
| 4 KB pages only | 16/18 | 0.95–2.40 | 0.99 |
| huge pages for all | 18/18 | 1.07–2.96 | 1.09 |
| matched protocol | 14/14 | 1.08–3.06 | 1.11 |

## First call vs steady state (baseline)

t_first / t_med: the first call of a freshly planned transform relative to the steady-state median; and SweepFFT's speedup if only the first call is counted.

| n | pmfft first/steady | pmfft_heur first/steady | mkl first/steady | fftw_measure first/steady | ducc first/steady | first-call speedup vs MKL | vs FFTW |
|---|---|---|---|---|---|---|---|
| 2^18 | 1.77 | 1.41 | 1.28 | 1.09 | 2.01 | 0.80 | 0.61 |
| 2^20 | 1.13 | 1.38 | 1.22 | 1.24 | 1.26 | 0.98 | 1.18 |
| 3·2^20 | 1.02 | 1.29 | 1.02 | 1.01 | 1.10 | 1.10 | 1.39 |
| 2^22 | 1.02 | 1.26 | 1.00 | 1.00 | 1.11 | 1.08 | 1.43 |
| 5·2^21 | 1.01 | 1.22 | 1.00 | 1.01 | 1.12 | 1.24 | 1.88 |
| 2^24 | 1.01 | 1.21 | 1.00 | 1.00 | 1.12 | 1.35 | 1.43 |
| 2^25 | 1.00 | 1.19 | 1.00 | 1.00 | 1.11 | 1.27 | 1.35 |

## FFTW: requested planner flag vs planning actually done (baseline)

Planning time (median over rounds, s), steady-state GFlop/s and whether the chosen plan equals the plan found by a fresh MEASURE / fresh PATIENT search (solver chains compared).

| n | fftw_estimate | fftw_estimate_wisdom | fftw_measure | fftw_measure_fresh | fftw_patient_fresh | imported MEASURE = fresh MEASURE? | = fresh PATIENT? |
|---|---|---|---|---|---|---|---|
| 2^18 | 0.00 s, 10.5 GF | 0.00 s, 12.1 GF | 0.00 s, 12.1 GF | 9.86 s, 12.1 GF | 188.70 s, 14.7 GF | yes | no |
| 2^20 | 0.00 s, 4.7 GF | 0.00 s, 7.5 GF | 0.00 s, 7.5 GF | 4.84 s, 7.4 GF | 300.01 s, 7.4 GF † | no | no |
| 3·2^20 | 0.01 s, 5.6 GF | 0.04 s, 5.4 GF | 0.04 s, 5.3 GF | 60.12 s, 5.6 GF † | 300.33 s, 5.6 GF † | no | no |
| 2^22 | 0.00 s, 2.8 GF | 0.00 s, 5.2 GF | 0.00 s, 5.2 GF | 25.64 s, 5.4 GF | 300.05 s, 5.4 GF † | no | no |
| 5·2^21 | 0.05 s, 3.9 GF | 0.05 s, 3.9 GF | 0.05 s, 3.9 GF | 60.80 s, 3.9 GF † | 301.58 s, 3.8 GF † | yes | yes |
| 2^24 | 0.00 s, 2.5 GF | 0.00 s, 5.1 GF | 0.00 s, 5.1 GF | 60.23 s, 2.5 GF † | 300.04 s, 5.1 GF † | no | no |
| 2^25 | 0.00 s, 2.5 GF | 0.00 s, 5.1 GF | 0.00 s, 5.1 GF | 61.61 s, 2.5 GF † | 300.59 s, 5.2 GF † | no | no |

## Huge-page coverage at the largest size

Resident transparent-huge-page memory / (32 n + memory the implementation adds), median over rounds.

| condition | pmfft | pmfft_heur | mkl | fftw_measure | ducc |
|---|---|---|---|---|---|
| headline protocol | 1.00 | 1.00 | 1.00 | 1.00 | 0.67 |
| 4 KB pages only | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| huge pages for all | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |

## Compiler settings: SweepFFT built for x86-64-v3 (generic tuning) vs -march=native

| n | pmfft v3 / native (time) | pmfft_heur v3 / native (time) |
|---|---|---|
| 2^18 | 1.02 [1.02, 1.03] | 1.01 [1.01, 1.01] |
| 2^20 | 1.06 [1.02, 1.11] | 1.05 [1.01, 1.08] |
| 3·2^20 | 1.03 [1.01, 1.05] | 1.03 [1.00, 1.06] |
| 2^22 | 1.03 [1.00, 1.05] | 1.02 [0.99, 1.05] |
| 5·2^21 | 1.02 [1.01, 1.03] | 1.02 [1.00, 1.05] |
| 2^24 | 1.03 [1.00, 1.06] | 1.02 [1.01, 1.04] |
| 2^25 | 1.06 [1.05, 1.07] | 1.01 [1.01, 1.02] |
