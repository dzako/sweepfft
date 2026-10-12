# Reproducibility study: pre-specified endpoints (`results/ENDPOINTS.md`)

10 blocks in 1 session(s) (20261012-004939); 450 runs, 3684 samples; retried runs: 0. Sizes P = 2^22, 2^23, 2^24, 2^25, 2^26; Q = 3·2^20, 5·2^20, 3·2^22, 5·2^22. FFTW plans capped (excluded from FFTW endpoints): 5·2^20, 3·2^22, 5·2^22.

## Primary endpoints

Geometric-mean speedup over P (> 1: SweepFFT faster), 95% block-bootstrap interval, one-sided exact sign-flip p-value, Holm-adjusted across E1 and E2.

| endpoint | sizes | blocks | speedup | 95% CI | p | p (Holm) | decision |
|---|---|---|---|---|---|---|---|
| E1 vs MKL | 5 | 10 | **1.187** | [1.182, 1.193] | 0.0010 | 0.0020 | faster |
| E2 vs FFTW MEASURE | 5 | 10 | **1.385** | [1.380, 1.390] | 0.0010 | 0.0020 | faster |

Per-block endpoint values (block order): E1 1.170, 1.184, 1.186, 1.198, 1.202, 1.198, 1.186, 1.182, 1.188, 1.182; E2 1.379, 1.390, 1.396, 1.396, 1.389, 1.379, 1.381, 1.389, 1.377, 1.373.

## Secondary endpoints

| endpoint | comparison | sizes | blocks | speedup | 95% CI |
|---|---|---|---|---|---|
| S1 | pmfft vs ducc | 2^22, 2^23, 2^24, 2^25, 2^26 | 10 | 2.839 | [2.829, 2.850] |
| S2 | pmfft_heur vs mkl | 2^22, 2^23, 2^24, 2^25, 2^26 | 10 | 1.176 | [1.172, 1.181] |
| S2 | pmfft_heur vs fftw_measure | 2^22, 2^23, 2^24, 2^25, 2^26 | 10 | 1.372 | [1.368, 1.376] |
| S3 | pmfft vs mkl | 3·2^20, 5·2^20, 3·2^22, 5·2^22 | 10 | 1.127 | [1.121, 1.133] |
| S3 | pmfft vs fftw_measure | 3·2^20 | 10 | 1.383 | [1.366, 1.397] |

## S4: per-size speedups (95% block-bootstrap CI) and median GFlop/s

| n | set | GF pmfft | GF pmfft_heur | GF mkl | GF fftw_measure | GF ducc | vs MKL | vs FFTW | vs ducc0 | heur vs MKL |
|---|---|---|---|---|---|---|---|---|---|---|
| 2^22 | P | 7.56 | 7.66 | 6.87 | 5.21 | 2.45 | 1.100 [1.096, 1.105] | 1.448 [1.445, 1.451] | 3.081 [3.050, 3.113] | 1.115 [1.110, 1.121] |
| 2^23 | P | 7.36 | 7.40 | 6.19 | 4.97 | 2.49 | 1.187 [1.179, 1.195] | 1.479 [1.471, 1.487] | 2.956 [2.938, 2.972] | 1.190 [1.182, 1.199] |
| 2^24 | P | 7.28 | 7.20 | 6.10 | 5.12 | 2.55 | 1.188 [1.178, 1.199] | 1.415 [1.400, 1.427] | 2.834 [2.796, 2.865] | 1.181 [1.170, 1.194] |
| 2^25 | P | 6.90 | 6.56 | 5.35 | 5.12 | 2.50 | 1.294 [1.274, 1.315] | 1.345 [1.342, 1.349] | 2.762 [2.755, 2.770] | 1.227 [1.211, 1.245] |
| 2^26 | P | 6.54 | 6.59 | 5.55 | 5.28 | 2.54 | 1.176 [1.160, 1.189] | 1.251 [1.235, 1.268] | 2.588 [2.562, 2.617] | 1.171 [1.157, 1.184] |
| 3·2^20 | Q | 7.47 | 7.72 | 6.76 | 5.38 | 2.39 | 1.100 [1.089, 1.109] | 1.383 [1.366, 1.397] | 3.065 [2.992, 3.133] | 1.142 [1.138, 1.146] |
| 5·2^20 | Q | 7.46 | 7.60 | 6.70 | 5.50 | 2.46 | 1.108 [1.101, 1.114] | 1.351 [1.342, 1.359] † | 3.019 [3.002, 3.035] | 1.124 [1.109, 1.135] |
| 3·2^22 | Q | 7.23 | 7.24 | 5.94 | 5.21 | 2.50 | 1.212 [1.197, 1.227] | 1.385 [1.369, 1.399] † | 2.875 [2.842, 2.899] | 1.217 [1.205, 1.230] |
| 5·2^22 | Q | 6.86 | 6.89 | 6.29 | 3.79 | 2.56 | 1.092 [1.077, 1.109] | 1.803 [1.787, 1.820] † | 2.689 [2.674, 2.709] | 1.096 [1.079, 1.114] |

## Noise

Within-run spread: (p75 − p25) / median of the samples of one run, median over blocks. Between-block CV: standard deviation / mean of the run medians over blocks.

| n | pmfft within / between | pmfft_heur within / between | mkl within / between | fftw_measure within / between | ducc within / between |
|---|---|---|---|---|---|
| 2^22 | 0.4% / 0.3% | 0.2% / 0.6% | 0.5% / 0.5% | 0.4% / 0.4% | 0.5% / 1.8% |
| 2^23 | 0.2% / 0.8% | 0.1% / 0.8% | 0.1% / 1.1% | 0.3% / 0.6% | 0.3% / 0.6% |
| 2^24 | 0.1% / 1.9% | 0.1% / 1.6% | 0.1% / 1.5% | 0.1% / 0.4% | 0.4% / 0.5% |
| 2^25 | 0.0% / 0.4% | 0.1% / 0.9% | 0.1% / 2.7% | 0.1% / 0.1% | 0.1% / 0.2% |
| 2^26 | 0.0% / 1.6% | 0.0% / 1.4% | 0.0% / 1.3% | 0.1% / 1.1% | 0.1% / 0.6% |
| 3·2^20 | 0.5% / 1.6% | 0.2% / 0.4% | 0.3% / 0.5% | 0.2% / 0.8% | 1.3% / 3.6% |
| 5·2^20 | 0.3% / 0.8% | 0.2% / 1.9% | 0.1% / 0.7% | 0.3% / 0.8% | 0.5% / 0.7% |
| 3·2^22 | 0.1% / 1.5% | 0.2% / 0.8% | 0.1% / 1.5% | 0.2% / 0.8% | 0.2% / 0.8% |
| 5·2^22 | 0.1% / 0.4% | 0.1% / 0.8% | 0.2% / 2.4% | 0.4% / 1.3% | 0.2% / 0.8% |

## Drift

Slope of log t against block index (% per block, 95% CI), pooled over sizes per implementation (size fixed effects); the same for the paired log speedup of the primary comparisons; and the clock and temperature ranges.

| quantity | slope %/block | 95% CI |
|---|---|---|
| t, pmfft | +0.02 | [-0.06, +0.11] |
| t, pmfft_heur | +0.02 | [-0.07, +0.10] |
| t, mkl | +0.06 | [-0.05, +0.17] |
| t, fftw_measure | +0.00 | [-0.05, +0.06] |
| t, ducc | -0.03 | [-0.14, +0.08] |
| speedup vs mkl on P | +0.04 | [-0.14, +0.22] |
| speedup vs fftw_measure on P | -0.11 | [-0.23, +0.02] |

Package temperature before runs: 42–55 °C (median 46); after: 43–50 °C. AC power: [-1] (1 = on mains). Wall-clock span: 0.9 h.
