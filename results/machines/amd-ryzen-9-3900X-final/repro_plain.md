# Reproducibility study: pre-specified endpoints (`results/ENDPOINTS.md`)

10 blocks in 1 session(s) (20261011-221939); 450 runs, 4927 samples; retried runs: 0. Sizes P = 2^22, 2^23, 2^24, 2^25, 2^26; Q = 3·2^20, 5·2^20, 3·2^22, 5·2^22. FFTW plans capped (excluded from FFTW endpoints): 5·2^20, 3·2^22, 5·2^22.

## Primary endpoints

Geometric-mean speedup over P (> 1: SweepFFT faster), 95% block-bootstrap interval, one-sided exact sign-flip p-value, Holm-adjusted across E1 and E2.

| endpoint | sizes | blocks | speedup | 95% CI | p | p (Holm) | decision |
|---|---|---|---|---|---|---|---|
| E1 vs MKL (secondary on AMD) | 5 | 10 | **1.219** | [1.215, 1.223] | 0.0010 | 0.0020 | faster |
| E2 vs FFTW MEASURE | 5 | 10 | **1.307** | [1.298, 1.313] | 0.0010 | 0.0020 | faster |

Per-block endpoint values (block order): E1 1.219, 1.219, 1.231, 1.212, 1.209, 1.225, 1.227, 1.218, 1.224, 1.208; E2 1.305, 1.311, 1.320, 1.300, 1.278, 1.316, 1.317, 1.299, 1.318, 1.299.

## Secondary endpoints

| endpoint | comparison | sizes | blocks | speedup | 95% CI |
|---|---|---|---|---|---|
| S1 | pmfft vs ducc | 2^22, 2^23, 2^24, 2^25, 2^26 | 10 | 1.987 | [1.975, 1.997] |
| S2 | pmfft_heur vs mkl | 2^22, 2^23, 2^24, 2^25, 2^26 | 10 | 1.160 | [1.152, 1.168] |
| S2 | pmfft_heur vs fftw_measure | 2^22, 2^23, 2^24, 2^25, 2^26 | 10 | 1.243 | [1.235, 1.252] |
| S3 | pmfft vs mkl | 3·2^20, 5·2^20, 3·2^22, 5·2^22 | 10 | 1.999 | [1.991, 2.005] |
| S3 | pmfft vs fftw_measure | 3·2^20 | 10 | 1.128 | [1.122, 1.134] |

## S4: per-size speedups (95% block-bootstrap CI) and median GFlop/s

| n | set | GF pmfft | GF pmfft_heur | GF mkl | GF fftw_measure | GF ducc | vs MKL | vs FFTW | vs ducc0 | heur vs MKL |
|---|---|---|---|---|---|---|---|---|---|---|
| 2^22 | P | 11.35 | 11.28 | 9.04 | 9.17 | 7.12 | 1.247 [1.232, 1.257] | 1.230 [1.217, 1.239] | 1.585 [1.566, 1.597] | 1.251 [1.244, 1.258] |
| 2^23 | P | 11.10 | 11.04 | 9.20 | 9.39 | 5.56 | 1.208 [1.204, 1.212] | 1.184 [1.180, 1.189] | 2.013 [1.988, 2.040] | 1.203 [1.198, 1.207] |
| 2^24 | P | 10.65 | 11.07 | 9.35 | 7.84 | 5.09 | 1.140 [1.136, 1.144] | 1.358 [1.352, 1.363] | 2.072 [2.024, 2.101] | 1.185 [1.182, 1.188] |
| 2^25 | P | 11.02 | 10.84 | 8.82 | 8.25 | 5.23 | 1.250 [1.243, 1.257] | 1.326 [1.309, 1.341] | 2.105 [2.094, 2.117] | 1.228 [1.221, 1.234] |
| 2^26 | P | 11.17 | 8.36 | 8.86 | 7.63 | 5.00 | 1.255 [1.236, 1.270] | 1.452 [1.424, 1.477] | 2.225 [2.190, 2.256] | 0.960 [0.925, 0.996] |
| 3·2^20 | Q | 11.23 | 11.18 | 5.63 | 10.00 | 7.09 | 2.004 [1.995, 2.014] | 1.128 [1.122, 1.134] | 1.603 [1.583, 1.636] | 1.989 [1.980, 1.997] |
| 5·2^20 | Q | 11.42 | 11.30 | 5.65 | 3.54 | 6.94 | 2.004 [1.975, 2.024] | 3.201 [3.156, 3.231] † | 1.634 [1.608, 1.651] | 2.001 [1.994, 2.008] |
| 3·2^22 | Q | 11.49 | 11.44 | 5.28 | 4.23 | 5.25 | 2.177 [2.173, 2.181] | 2.724 [2.711, 2.739] † | 2.180 [2.142, 2.217] | 2.168 [2.163, 2.172] |
| 5·2^22 | Q | 11.24 | 11.25 | 6.14 | 4.35 | 5.05 | 1.826 [1.813, 1.836] | 2.587 [2.566, 2.608] † | 2.221 [2.210, 2.231] | 1.826 [1.815, 1.838] |

## Noise

Within-run spread: (p75 − p25) / median of the samples of one run, median over blocks. Between-block CV: standard deviation / mean of the run medians over blocks.

| n | pmfft within / between | pmfft_heur within / between | mkl within / between | fftw_measure within / between | ducc within / between |
|---|---|---|---|---|---|
| 2^22 | 0.1% / 1.9% | 0.1% / 0.9% | 0.1% / 0.2% | 0.2% / 0.4% | 0.2% / 0.2% |
| 2^23 | 0.1% / 0.6% | 0.1% / 0.6% | 0.1% / 0.1% | 0.2% / 0.2% | 0.1% / 2.3% |
| 2^24 | 0.1% / 0.5% | 0.1% / 0.5% | 0.1% / 0.1% | 0.1% / 0.5% | 0.1% / 3.6% |
| 2^25 | 0.0% / 0.8% | 0.1% / 0.8% | 0.1% / 0.2% | 0.0% / 2.2% | 0.0% / 0.6% |
| 2^26 | 0.1% / 2.6% | 0.1% / 6.1% | 0.1% / 0.2% | 0.1% / 1.6% | 0.0% / 0.5% |
| 3·2^20 | 0.2% / 0.6% | 0.2% / 0.7% | 0.1% / 0.6% | 0.2% / 0.9% | 0.2% / 2.8% |
| 5·2^20 | 0.2% / 2.2% | 0.1% / 0.5% | 0.4% / 0.4% | 0.1% / 0.2% | 0.1% / 0.4% |
| 3·2^22 | 0.1% / 0.3% | 0.1% / 0.3% | 0.1% / 0.2% | 0.1% / 0.8% | 0.1% / 2.8% |
| 5·2^22 | 0.1% / 0.5% | 0.1% / 0.7% | 0.1% / 0.9% | 0.1% / 1.3% | 0.0% / 0.6% |

## Drift

Slope of log t against block index (% per block, 95% CI), pooled over sizes per implementation (size fixed effects); the same for the paired log speedup of the primary comparisons; and the clock and temperature ranges.

| quantity | slope %/block | 95% CI |
|---|---|---|
| t, pmfft | +0.04 | [-0.06, +0.14] |
| t, pmfft_heur | +0.06 | [-0.10, +0.22] |
| t, mkl | +0.00 | [-0.03, +0.03] |
| t, fftw_measure | +0.00 | [-0.08, +0.08] |
| t, ducc | +0.09 | [-0.06, +0.24] |
| speedup vs mkl on P | -0.04 | [-0.18, +0.11] |
| speedup vs fftw_measure on P | -0.01 | [-0.20, +0.18] |

Effective core clock during the timed loop (GHz), min / median / max per implementation: pmfft 4.21 / 4.22 / 4.23; pmfft_heur 4.21 / 4.22 / 4.24; mkl 4.22 / 4.24 / 4.29; fftw_measure 4.16 / 4.22 / 4.29; ducc 4.21 / 4.27 / 4.28.

Correlation of effective clock with log t (relative to each implementation and size's median): +0.00.

Package temperature before runs: 85–97 °C (median 92); after: 85–97 °C. AC power: [-1] (1 = on mains). Wall-clock span: 0.7 h.
