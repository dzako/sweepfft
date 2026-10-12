# Reproducibility study: pre-specified endpoints (`results/ENDPOINTS.md`)

10 blocks in 1 session(s) (20261011-235339); 450 runs, 3635 samples; retried runs: 0. Sizes P = 2^22, 2^23, 2^24, 2^25, 2^26; Q = 3·2^20, 5·2^20, 3·2^22, 5·2^22. FFTW plans capped (excluded from FFTW endpoints): 5·2^20, 3·2^22, 5·2^22.

## Primary endpoints

Geometric-mean speedup over P (> 1: SweepFFT faster), 95% block-bootstrap interval, one-sided exact sign-flip p-value, Holm-adjusted across E1 and E2.

| endpoint | sizes | blocks | speedup | 95% CI | p | p (Holm) | decision |
|---|---|---|---|---|---|---|---|
| E1 vs MKL | 5 | 10 | **1.177** | [1.151, 1.198] | 0.0010 | 0.0020 | faster |
| E2 vs FFTW MEASURE | 5 | 10 | **1.229** | [1.203, 1.248] | 0.0010 | 0.0020 | faster |

Per-block endpoint values (block order): E1 1.154, 1.198, 1.185, 1.185, 1.203, 1.086, 1.181, 1.230, 1.154, 1.196; E2 1.228, 1.237, 1.256, 1.231, 1.260, 1.130, 1.228, 1.263, 1.219, 1.247.

## Secondary endpoints

| endpoint | comparison | sizes | blocks | speedup | 95% CI |
|---|---|---|---|---|---|
| S1 | pmfft vs ducc | 2^22, 2^23, 2^24, 2^25, 2^26 | 10 | 2.203 | [2.122, 2.284] |
| S2 | pmfft_heur vs mkl | 2^22, 2^23, 2^24, 2^25, 2^26 | 10 | 1.145 | [1.120, 1.169] |
| S2 | pmfft_heur vs fftw_measure | 2^22, 2^23, 2^24, 2^25, 2^26 | 10 | 1.197 | [1.170, 1.220] |
| S3 | pmfft vs mkl | 3·2^20, 5·2^20, 3·2^22, 5·2^22 | 10 | 1.198 | [1.180, 1.217] |
| S3 | pmfft vs fftw_measure | 3·2^20 | 10 | 0.934 | [0.925, 0.945] |

## S4: per-size speedups (95% block-bootstrap CI) and median GFlop/s

| n | set | GF pmfft | GF pmfft_heur | GF mkl | GF fftw_measure | GF ducc | vs MKL | vs FFTW | vs ducc0 | heur vs MKL |
|---|---|---|---|---|---|---|---|---|---|---|
| 2^22 | P | 6.58 | 6.68 | 6.33 | 5.45 | 3.85 | 1.042 [1.024, 1.059] | 1.215 [1.200, 1.232] | 1.722 [1.638, 1.850] | 1.051 [1.022, 1.074] |
| 2^23 | P | 6.34 | 6.22 | 4.89 | 5.13 | 3.10 | 1.333 [1.296, 1.372] | 1.270 [1.235, 1.310] | 2.210 [1.934, 2.548] | 1.284 [1.271, 1.297] |
| 2^24 | P | 6.58 | 6.24 | 5.64 | 5.16 | 2.72 | 1.127 [1.040, 1.184] | 1.232 [1.139, 1.288] | 2.148 [1.882, 2.375] | 1.010 [0.910, 1.106] |
| 2^25 | P | 5.93 | 6.05 | 5.47 | 4.99 | 2.40 | 1.072 [1.054, 1.089] | 1.178 [1.163, 1.192] | 2.432 [2.389, 2.469] | 1.105 [1.095, 1.115] |
| 2^26 | P | 6.36 | 6.13 | 4.71 | 5.05 | 2.42 | 1.343 [1.313, 1.373] | 1.252 [1.230, 1.269] | 2.611 [2.565, 2.647] | 1.309 [1.285, 1.335] |
| 3·2^20 | Q | 6.85 | 6.96 | 5.50 | 7.34 | 4.17 | 1.241 [1.221, 1.264] | 0.934 [0.925, 0.945] | 1.699 [1.618, 1.807] | 1.259 [1.235, 1.283] |
| 5·2^20 | Q | 6.56 | 6.59 | 5.23 | 5.71 | 3.90 | 1.281 [1.247, 1.333] | 1.149 [1.141, 1.157] † | 1.791 [1.658, 2.038] | 1.290 [1.255, 1.341] |
| 3·2^22 | Q | 6.66 | 6.53 | 5.82 | 5.22 | 3.27 | 1.132 [1.110, 1.151] | 1.274 [1.262, 1.287] † | 2.040 [1.884, 2.208] | 1.044 [0.950, 1.121] |
| 5·2^22 | Q | 6.13 | 6.31 | 5.43 | 3.21 | 2.69 | 1.144 [1.092, 1.197] | 1.911 [1.857, 1.961] † | 2.320 [2.201, 2.440] | 1.141 [1.089, 1.199] |

## Noise

Within-run spread: (p75 − p25) / median of the samples of one run, median over blocks. Between-block CV: standard deviation / mean of the run medians over blocks.

| n | pmfft within / between | pmfft_heur within / between | mkl within / between | fftw_measure within / between | ducc within / between |
|---|---|---|---|---|---|
| 2^22 | 0.6% / 1.2% | 0.2% / 1.3% | 0.1% / 3.1% | 0.3% / 1.2% | 0.6% / 11.0% |
| 2^23 | 0.2% / 5.0% | 0.1% / 1.8% | 0.1% / 2.2% | 0.2% / 1.2% | 1.0% / 24.0% |
| 2^24 | 0.1% / 14.1% | 0.1% / 18.6% | 0.1% / 2.3% | 0.2% / 0.6% | 0.5% / 11.6% |
| 2^25 | 0.1% / 2.1% | 0.0% / 0.2% | 0.0% / 1.7% | 0.7% / 0.2% | 0.3% / 1.5% |
| 2^26 | 0.0% / 2.7% | 0.0% / 0.8% | 0.1% / 3.2% | 0.1% / 0.3% | 0.2% / 0.2% |
| 3·2^20 | 0.7% / 1.1% | 0.2% / 1.0% | 0.2% / 2.8% | 0.2% / 1.0% | 0.5% / 9.1% |
| 5·2^20 | 0.3% / 1.0% | 0.2% / 0.9% | 0.2% / 5.9% | 0.2% / 0.9% | 0.5% / 24.7% |
| 3·2^22 | 0.1% / 1.6% | 0.1% / 15.1% | 0.1% / 2.4% | 0.2% / 0.7% | 0.9% / 12.7% |
| 5·2^22 | 0.0% / 3.0% | 0.1% / 6.7% | 1.1% / 6.3% | 0.3% / 2.7% | 0.4% / 7.4% |

## Drift

Slope of log t against block index (% per block, 95% CI), pooled over sizes per implementation (size fixed effects); the same for the paired log speedup of the primary comparisons; and the clock and temperature ranges.

| quantity | slope %/block | 95% CI |
|---|---|---|
| t, pmfft | -0.07 | [-0.42, +0.27] |
| t, pmfft_heur | -0.01 | [-0.58, +0.56] |
| t, mkl | -0.24 | [-0.50, +0.02] |
| t, fftw_measure | -0.05 | [-0.14, +0.03] |
| t, ducc | +0.80 | [-0.12, +1.72] |
| speedup vs mkl on P | +0.09 | [-0.55, +0.72] |
| speedup vs fftw_measure on P | -0.03 | [-0.65, +0.59] |

Package temperature before runs: 45–63 °C (median 47); after: 45–51 °C. AC power: [-1] (1 = on mains). Wall-clock span: 0.9 h.
