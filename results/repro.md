# Reproducibility study: pre-specified endpoints (`results/ENDPOINTS.md`)

10 blocks in 1 session(s) (20261010-223408); 450 runs, 6536 samples; retried runs: 0. Sizes P = 2^22, 2^23, 2^24, 2^25, 2^26; Q = 3·2^20, 5·2^20, 3·2^22, 5·2^22. FFTW plans capped (excluded from FFTW endpoints): 5·2^20, 3·2^22, 5·2^22.

## Primary endpoints

Geometric-mean speedup over P (> 1: SweepFFT faster), 95% block-bootstrap interval, one-sided exact sign-flip p-value, Holm-adjusted across E1 and E2.

| endpoint | sizes | blocks | speedup | 95% CI | p | p (Holm) | decision |
|---|---|---|---|---|---|---|---|
| E1 vs MKL | 5 | 10 | **1.131** | [1.123, 1.138] | 0.0010 | 0.0020 | faster |
| E2 vs FFTW MEASURE | 5 | 10 | **1.446** | [1.434, 1.456] | 0.0010 | 0.0020 | faster |

Per-block endpoint values (block order): E1 1.137, 1.115, 1.135, 1.110, 1.134, 1.122, 1.138, 1.127, 1.143, 1.147; E2 1.463, 1.435, 1.455, 1.404, 1.456, 1.454, 1.448, 1.430, 1.467, 1.452.

## Secondary endpoints

| endpoint | comparison | sizes | blocks | speedup | 95% CI |
|---|---|---|---|---|---|
| S1 | pmfft vs ducc | 2^22, 2^23, 2^24, 2^25, 2^26 | 10 | 2.036 | [2.013, 2.061] |
| S2 | pmfft_heur vs mkl | 2^22, 2^23, 2^24, 2^25, 2^26 | 10 | 1.118 | [1.112, 1.124] |
| S2 | pmfft_heur vs fftw_measure | 2^22, 2^23, 2^24, 2^25, 2^26 | 10 | 1.430 | [1.421, 1.439] |
| S3 | pmfft vs mkl | 3·2^20, 5·2^20, 3·2^22, 5·2^22 | 10 | 2.295 | [2.271, 2.318] |
| S3 | pmfft vs fftw_measure | 3·2^20 | 10 | 0.980 | [0.961, 0.998] |

## S4: per-size speedups (95% block-bootstrap CI) and median GFlop/s

| n | set | GF pmfft | GF pmfft_heur | GF mkl | GF fftw_measure | GF ducc | vs MKL | vs FFTW | vs ducc0 | heur vs MKL |
|---|---|---|---|---|---|---|---|---|---|---|
| 2^22 | P | 15.97 | 16.54 | 15.69 | 11.37 | 7.98 | 1.035 [1.019, 1.051] | 1.437 [1.401, 1.477] | 2.060 [2.011, 2.114] | 1.052 [1.033, 1.070] |
| 2^23 | P | 16.48 | 16.31 | 14.30 | 11.49 | 8.11 | 1.145 [1.130, 1.160] | 1.448 [1.426, 1.471] | 2.059 [2.022, 2.105] | 1.127 [1.106, 1.146] |
| 2^24 | P | 16.60 | 16.72 | 14.19 | 11.28 | 8.19 | 1.166 [1.147, 1.184] | 1.468 [1.448, 1.485] | 2.015 [1.986, 2.043] | 1.177 [1.162, 1.191] |
| 2^25 | P | 16.02 | 15.64 | 14.01 | 11.12 | 8.13 | 1.136 [1.114, 1.154] | 1.424 [1.402, 1.442] | 1.947 [1.917, 1.972] | 1.122 [1.114, 1.130] |
| 2^26 | P | 16.99 | 15.71 | 14.04 | 11.32 | 7.86 | 1.178 [1.133, 1.216] | 1.457 [1.404, 1.504] | 2.103 [2.026, 2.170] | 1.116 [1.099, 1.128] |
| 3·2^20 | Q | 16.49 | 16.54 | 6.47 | 17.00 | 7.89 | 2.547 [2.473, 2.624] | 0.980 [0.961, 0.998] | 2.121 [2.066, 2.192] | 2.557 [2.482, 2.631] |
| 5·2^20 | Q | 16.94 | 17.05 | 6.16 | 4.84 | 7.96 | 2.773 [2.726, 2.823] | 3.493 [3.458, 3.526] † | 2.199 [2.137, 2.268] | 2.800 [2.762, 2.845] |
| 3·2^22 | Q | 15.32 | 15.84 | 6.07 | 4.53 | 7.89 | 2.534 [2.488, 2.583] | 3.397 [3.331, 3.467] † | 1.980 [1.926, 2.043] | 2.571 [2.514, 2.623] |
| 5·2^22 | Q | 16.34 | 15.88 | 10.43 | 4.41 | 8.09 | 1.549 [1.525, 1.570] | 3.769 [3.638, 3.940] † | 2.001 [1.974, 2.024] | 1.523 [1.510, 1.533] |

## Noise

Within-run spread: (p75 − p25) / median of the samples of one run, median over blocks. Between-block CV: standard deviation / mean of the run medians over blocks.

| n | pmfft within / between | pmfft_heur within / between | mkl within / between | fftw_measure within / between | ducc within / between |
|---|---|---|---|---|---|
| 2^22 | 0.4% / 2.5% | 0.4% / 2.5% | 0.7% / 2.0% | 0.3% / 2.7% | 0.8% / 4.7% |
| 2^23 | 0.3% / 1.3% | 0.5% / 2.5% | 0.5% / 1.4% | 0.4% / 2.5% | 0.8% / 3.8% |
| 2^24 | 0.2% / 2.5% | 0.4% / 1.9% | 0.6% / 0.9% | 0.4% / 1.4% | 0.5% / 0.4% |
| 2^25 | 0.3% / 2.4% | 0.5% / 0.5% | 0.3% / 1.1% | 0.3% / 0.4% | 0.2% / 0.3% |
| 2^26 | 0.3% / 5.9% | 0.2% / 2.2% | 0.3% / 0.8% | 0.1% / 0.3% | 0.1% / 0.9% |
| 3·2^20 | 0.7% / 1.4% | 0.4% / 1.5% | 0.6% / 4.5% | 0.5% / 2.5% | 0.9% / 4.6% |
| 5·2^20 | 0.2% / 1.2% | 0.2% / 0.8% | 0.7% / 2.8% | 1.1% / 1.2% | 0.8% / 5.3% |
| 3·2^22 | 0.3% / 3.3% | 0.4% / 3.6% | 1.1% / 0.5% | 0.2% / 0.9% | 0.6% / 2.9% |
| 5·2^22 | 0.7% / 2.4% | 0.4% / 1.3% | 0.2% / 0.2% | 1.4% / 7.3% | 0.5% / 0.9% |

## Drift

Slope of log t against block index (% per block, 95% CI), pooled over sizes per implementation (size fixed effects); the same for the paired log speedup of the primary comparisons; and the clock and temperature ranges.

| quantity | slope %/block | 95% CI |
|---|---|---|
| t, pmfft | -0.13 | [-0.34, +0.08] |
| t, pmfft_heur | -0.08 | [-0.23, +0.07] |
| t, mkl | -0.03 | [-0.18, +0.12] |
| t, fftw_measure | -0.17 | [-0.37, +0.04] |
| t, ducc | -0.13 | [-0.36, +0.11] |
| speedup vs mkl on P | +0.18 | [-0.18, +0.53] |
| speedup vs fftw_measure on P | +0.06 | [-0.32, +0.44] |

Effective core clock during the timed loop (GHz), min / median / max per implementation: pmfft 4.96 / 4.98 / 4.99; pmfft_heur 4.97 / 4.99 / 4.99; mkl 4.97 / 4.98 / 4.99; fftw_measure 4.97 / 4.98 / 4.99; ducc 4.98 / 4.98 / 4.98.

Correlation of effective clock with log t (relative to each implementation and size's median): -0.05.

Package temperature before runs: 59–73 °C (median 64); after: 59–73 °C. AC power: [1] (1 = on mains). Wall-clock span: 0.4 h.
