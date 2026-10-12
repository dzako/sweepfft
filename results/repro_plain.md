# Reproducibility study: pre-specified endpoints (`results/ENDPOINTS.md`)

10 blocks in 1 session(s) (plain-20261011); 450 runs, 7018 samples; retried runs: 0. Sizes P = 2^22, 2^23, 2^24, 2^25, 2^26; Q = 3·2^20, 5·2^20, 3·2^22, 5·2^22. FFTW plans capped (excluded from FFTW endpoints): 5·2^20, 3·2^22, 5·2^22.

## Primary endpoints

Geometric-mean speedup over P (> 1: SweepFFT faster), 95% block-bootstrap interval, one-sided exact sign-flip p-value, Holm-adjusted across E1 and E2.

| endpoint | sizes | blocks | speedup | 95% CI | p | p (Holm) | decision |
|---|---|---|---|---|---|---|---|
| E1 vs MKL | 5 | 10 | **1.027** | [1.018, 1.037] | 0.0010 | 0.0020 | faster |
| E2 vs FFTW MEASURE | 5 | 10 | **1.181** | [1.164, 1.198] | 0.0010 | 0.0020 | faster |

Per-block endpoint values (block order): E1 1.043, 1.026, 1.014, 1.005, 1.016, 1.019, 1.058, 1.019, 1.042, 1.028; E2 1.237, 1.178, 1.170, 1.145, 1.171, 1.140, 1.198, 1.187, 1.208, 1.178.

## Secondary endpoints

| endpoint | comparison | sizes | blocks | speedup | 95% CI |
|---|---|---|---|---|---|
| S1 | pmfft vs ducc | 2^22, 2^23, 2^24, 2^25, 2^26 | 10 | 1.824 | [1.804, 1.846] |
| S2 | pmfft_heur vs mkl | 2^22, 2^23, 2^24, 2^25, 2^26 | 10 | 0.993 | [0.985, 1.000] |
| S2 | pmfft_heur vs fftw_measure | 2^22, 2^23, 2^24, 2^25, 2^26 | 10 | 1.142 | [1.127, 1.158] |
| S3 | pmfft vs mkl | 3·2^20, 5·2^20, 3·2^22, 5·2^22 | 10 | 2.294 | [2.277, 2.312] |
| S3 | pmfft vs fftw_measure | 3·2^20 | 10 | 1.026 | [0.982, 1.070] |

## S4: per-size speedups (95% block-bootstrap CI) and median GFlop/s

| n | set | GF pmfft | GF pmfft_heur | GF mkl | GF fftw_measure | GF ducc | vs MKL | vs FFTW | vs ducc0 | heur vs MKL |
|---|---|---|---|---|---|---|---|---|---|---|
| 2^22 | P | 17.01 | 17.39 | 17.96 | 16.15 | 10.39 | 0.951 [0.922, 0.978] | 1.066 [1.034, 1.095] | 1.648 [1.590, 1.700] | 0.959 [0.939, 0.976] |
| 2^23 | P | 16.05 | 16.95 | 16.72 | 16.08 | 10.05 | 0.962 [0.948, 0.982] | 1.008 [0.969, 1.053] | 1.621 [1.578, 1.671] | 1.019 [1.012, 1.027] |
| 2^24 | P | 16.31 | 16.30 | 15.96 | 14.62 | 9.19 | 1.020 [0.998, 1.043] | 1.115 [1.070, 1.167] | 1.781 [1.736, 1.841] | 1.021 [1.007, 1.034] |
| 2^25 | P | 15.40 | 14.48 | 15.44 | 12.18 | 7.95 | 0.998 [0.968, 1.034] | 1.230 [1.169, 1.295] | 1.932 [1.903, 1.957] | 0.944 [0.916, 0.978] |
| 2^26 | P | 16.87 | 14.33 | 13.67 | 10.75 | 7.66 | 1.226 [1.183, 1.272] | 1.558 [1.535, 1.582] | 2.197 [2.178, 2.215] | 1.024 [0.991, 1.054] |
| 3·2^20 | Q | 17.15 | 17.30 | 6.44 | 16.38 | 10.21 | 2.614 [2.525, 2.699] | 1.026 [0.982, 1.070] | 1.715 [1.625, 1.800] | 2.686 [2.631, 2.733] |
| 5·2^20 | Q | 17.39 | 17.16 | 6.19 | 5.98 | 10.00 | 2.770 [2.716, 2.818] | 2.872 [2.812, 2.924] † | 1.761 [1.699, 1.852] | 2.766 [2.726, 2.801] |
| 3·2^22 | Q | 16.14 | 16.14 | 6.12 | 5.96 | 9.35 | 2.620 [2.556, 2.670] | 2.739 [2.640, 2.853] † | 1.780 [1.686, 1.888] | 2.627 [2.579, 2.670] |
| 5·2^22 | Q | 15.59 | 15.82 | 10.69 | 5.06 | 8.37 | 1.460 [1.419, 1.504] | 3.055 [2.996, 3.111] † | 1.847 [1.804, 1.888] | 1.478 [1.440, 1.520] |

## Noise

Within-run spread: (p75 − p25) / median of the samples of one run, median over blocks. Between-block CV: standard deviation / mean of the run medians over blocks.

| n | pmfft within / between | pmfft_heur within / between | mkl within / between | fftw_measure within / between | ducc within / between |
|---|---|---|---|---|---|
| 2^22 | 1.6% / 3.8% | 1.9% / 5.1% | 3.1% / 3.1% | 2.7% / 5.0% | 3.3% / 3.9% |
| 2^23 | 0.9% / 2.4% | 1.6% / 1.9% | 1.6% / 2.4% | 2.3% / 7.0% | 2.0% / 4.9% |
| 2^24 | 1.2% / 3.2% | 1.2% / 2.3% | 1.2% / 2.6% | 1.2% / 6.8% | 1.0% / 3.7% |
| 2^25 | 1.1% / 3.8% | 0.9% / 2.6% | 0.6% / 5.8% | 0.7% / 8.5% | 0.6% / 2.8% |
| 2^26 | 0.5% / 2.1% | 0.8% / 5.3% | 0.7% / 5.7% | 1.2% / 2.1% | 0.5% / 1.2% |
| 3·2^20 | 2.6% / 5.7% | 2.7% / 3.2% | 2.0% / 2.8% | 4.4% / 2.5% | 3.9% / 10.6% |
| 5·2^20 | 1.6% / 3.5% | 1.3% / 2.5% | 1.0% / 1.0% | 1.0% / 0.8% | 2.8% / 8.6% |
| 3·2^22 | 1.7% / 4.3% | 1.5% / 3.6% | 0.9% / 2.3% | 0.6% / 8.2% | 2.8% / 9.9% |
| 5·2^22 | 1.0% / 3.5% | 1.2% / 3.5% | 0.6% / 5.4% | 0.7% / 3.5% | 0.8% / 3.7% |

## Drift

Slope of log t against block index (% per block, 95% CI), pooled over sizes per implementation (size fixed effects); the same for the paired log speedup of the primary comparisons; and the clock and temperature ranges.

| quantity | slope %/block | 95% CI |
|---|---|---|
| t, pmfft | -0.02 | [-0.29, +0.25] |
| t, pmfft_heur | +0.21 | [-0.04, +0.45] |
| t, mkl | -0.09 | [-0.36, +0.19] |
| t, fftw_measure | -0.19 | [-0.59, +0.21] |
| t, ducc | -0.20 | [-0.64, +0.24] |
| speedup vs mkl on P | +0.10 | [-0.40, +0.59] |
| speedup vs fftw_measure on P | -0.05 | [-0.71, +0.60] |

Effective core clock during the timed loop (GHz), min / median / max per implementation: pmfft 4.90 / 4.98 / 4.99; pmfft_heur 4.87 / 4.98 / 4.99; mkl 4.83 / 4.97 / 4.99; fftw_measure 4.80 / 4.96 / 4.99; ducc 4.87 / 4.97 / 4.98.

Correlation of effective clock with log t (relative to each implementation and size's median): -0.33.

Package temperature before runs: 64–93 °C (median 70); after: 64–93 °C. AC power: [1] (1 = on mains). Wall-clock span: 0.4 h.
