# Reproducibility study: pre-specified endpoints (`results/ENDPOINTS.md`)

10 blocks in 1 session(s) (20261011-224418); 450 runs, 4162 samples; retried runs: 0. Sizes P = 2^22, 2^23, 2^24, 2^25, 2^26; Q = 3·2^20, 5·2^20, 3·2^22, 5·2^22. FFTW plans capped (excluded from FFTW endpoints): 5·2^20, 3·2^22, 5·2^22.

## Primary endpoints

Geometric-mean speedup over P (> 1: SweepFFT faster), 95% block-bootstrap interval, one-sided exact sign-flip p-value, Holm-adjusted across E1 and E2.

| endpoint | sizes | blocks | speedup | 95% CI | p | p (Holm) | decision |
|---|---|---|---|---|---|---|---|
| E1 vs MKL (secondary on AMD) | 5 | 10 | **1.170** | [1.155, 1.183] | 0.0010 | 0.0020 | faster |
| E2 vs FFTW MEASURE | 5 | 10 | **1.316** | [1.298, 1.337] | 0.0010 | 0.0020 | faster |

Per-block endpoint values (block order): E1 1.174, 1.131, 1.195, 1.184, 1.145, 1.166, 1.193, 1.140, 1.179, 1.190; E2 1.318, 1.303, 1.388, 1.335, 1.280, 1.276, 1.288, 1.301, 1.329, 1.346.

## Secondary endpoints

| endpoint | comparison | sizes | blocks | speedup | 95% CI |
|---|---|---|---|---|---|
| S1 | pmfft vs ducc | 2^22, 2^23, 2^24, 2^25, 2^26 | 10 | 2.191 | [2.152, 2.236] |
| S2 | pmfft_heur vs mkl | 2^22, 2^23, 2^24, 2^25, 2^26 | 10 | 0.965 | [0.927, 1.016] |
| S2 | pmfft_heur vs fftw_measure | 2^22, 2^23, 2^24, 2^25, 2^26 | 10 | 1.086 | [1.042, 1.142] |
| S3 | pmfft vs mkl | 3·2^20, 5·2^20, 3·2^22, 5·2^22 | 10 | 1.972 | [1.951, 1.993] |
| S3 | pmfft vs fftw_measure | 3·2^20 | 10 | 1.021 | [1.017, 1.025] |

## S4: per-size speedups (95% block-bootstrap CI) and median GFlop/s

| n | set | GF pmfft | GF pmfft_heur | GF mkl | GF fftw_measure | GF ducc | vs MKL | vs FFTW | vs ducc0 | heur vs MKL |
|---|---|---|---|---|---|---|---|---|---|---|
| 2^22 | P | 9.02 | 8.99 | 7.57 | 7.41 | 5.17 | 1.193 [1.186, 1.199] | 1.217 [1.211, 1.222] | 1.871 [1.706, 2.075] | 1.189 [1.180, 1.197] |
| 2^23 | P | 8.63 | 8.70 | 7.67 | 7.42 | 3.97 | 1.118 [1.101, 1.133] | 1.156 [1.134, 1.173] | 2.188 [2.127, 2.250] | 1.132 [1.121, 1.142] |
| 2^24 | P | 8.51 | 8.58 | 7.81 | 6.26 | 3.84 | 1.095 [1.084, 1.113] | 1.353 [1.302, 1.402] | 2.230 [2.189, 2.283] | 1.103 [1.096, 1.109] |
| 2^25 | P | 8.65 | 7.76 | 7.24 | 5.82 | 3.52 | 1.193 [1.169, 1.214] | 1.481 [1.427, 1.538] | 2.449 [2.401, 2.489] | 1.073 [1.040, 1.103] |
| 2^26 | P | 7.87 | 2.79 | 6.28 | 5.75 | 3.56 | 1.256 [1.175, 1.340] | 1.402 [1.329, 1.473] | 2.256 [2.121, 2.390] | 0.526 [0.435, 0.671] |
| 3·2^20 | Q | 9.01 | 9.04 | 4.65 | 8.82 | 5.58 | 1.933 [1.925, 1.941] | 1.021 [1.017, 1.025] | 1.690 [1.613, 1.799] | 1.939 [1.924, 1.951] |
| 5·2^20 | Q | 9.13 | 9.11 | 4.65 | 2.79 | 4.42 | 1.964 [1.952, 1.979] | 3.777 [3.280, 4.824] † | 2.032 [1.873, 2.212] | 1.957 [1.942, 1.974] |
| 3·2^22 | Q | 9.02 | 9.11 | 4.31 | 2.87 | 3.86 | 2.078 [2.032, 2.113] | 3.175 [2.993, 3.370] † | 2.261 [2.153, 2.352] | 2.107 [2.087, 2.123] |
| 5·2^22 | Q | 8.44 | 8.17 | 4.52 | 2.57 | 3.77 | 1.916 [1.868, 1.973] | 3.337 [3.146, 3.538] † | 2.285 [2.235, 2.351] | 1.839 [1.764, 1.917] |

## Noise

Within-run spread: (p75 − p25) / median of the samples of one run, median over blocks. Between-block CV: standard deviation / mean of the run medians over blocks.

| n | pmfft within / between | pmfft_heur within / between | mkl within / between | fftw_measure within / between | ducc within / between |
|---|---|---|---|---|---|
| 2^22 | 0.1% / 0.7% | 0.1% / 1.1% | 0.1% / 0.4% | 0.1% / 0.1% | 0.2% / 17.7% |
| 2^23 | 0.3% / 2.7% | 0.1% / 1.5% | 0.1% / 0.3% | 0.1% / 1.0% | 0.1% / 5.2% |
| 2^24 | 0.1% / 2.3% | 0.1% / 0.9% | 0.2% / 0.3% | 0.9% / 5.3% | 16.3% / 2.2% |
| 2^25 | 0.1% / 3.3% | 0.4% / 4.9% | 0.5% / 0.5% | 8.6% / 5.3% | 7.3% / 0.7% |
| 2^26 | 0.1% / 9.6% | 1.8% / 28.1% | 5.0% / 3.3% | 2.4% / 1.1% | 0.1% / 1.1% |
| 3·2^20 | 0.1% / 0.6% | 0.2% / 0.9% | 0.1% / 0.6% | 0.1% / 0.6% | 0.3% / 10.0% |
| 5·2^20 | 0.2% / 0.6% | 0.2% / 0.8% | 0.5% / 1.0% | 0.1% / 56.1% | 0.1% / 14.1% |
| 3·2^22 | 0.1% / 3.5% | 0.1% / 1.4% | 0.0% / 0.4% | 3.5% / 11.5% | 0.1% / 7.2% |
| 5·2^22 | 0.4% / 3.5% | 0.1% / 7.2% | 12.2% / 3.4% | 6.4% / 8.7% | 13.0% / 3.7% |

## Drift

Slope of log t against block index (% per block, 95% CI), pooled over sizes per implementation (size fixed effects); the same for the paired log speedup of the primary comparisons; and the clock and temperature ranges.

| quantity | slope %/block | 95% CI |
|---|---|---|
| t, pmfft | -0.07 | [-0.36, +0.21] |
| t, pmfft_heur | +0.31 | [-0.63, +1.26] |
| t, mkl | -0.07 | [-0.19, +0.05] |
| t, fftw_measure | -0.55 | [-1.53, +0.43] |
| t, ducc | -0.22 | [-0.85, +0.42] |
| speedup vs mkl on P | +0.14 | [-0.41, +0.68] |
| speedup vs fftw_measure on P | -0.06 | [-0.64, +0.51] |

Package temperature before runs: 47–51 °C (median 50); after: 47–51 °C. AC power: [-1] (1 = on mains). Wall-clock span: 1.0 h.
