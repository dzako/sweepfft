# Reproducibility study: pre-specified endpoints (`results/ENDPOINTS.md`)

10 blocks in 1 session(s) (20261011-213154); 450 runs, 6895 samples; retried runs: 0. Sizes P = 2^22, 2^23, 2^24, 2^25, 2^26; Q = 3·2^20, 5·2^20, 3·2^22, 5·2^22. FFTW plans capped (excluded from FFTW endpoints): 5·2^20, 3·2^22, 5·2^22.

## Primary endpoints

Geometric-mean speedup over P (> 1: SweepFFT faster), 95% block-bootstrap interval, one-sided exact sign-flip p-value, Holm-adjusted across E1 and E2.

| endpoint | sizes | blocks | speedup | 95% CI | p | p (Holm) | decision |
|---|---|---|---|---|---|---|---|
| E1 vs MKL (secondary on AMD) | 5 | 10 | **1.280** | [1.263, 1.299] | 0.0010 | 0.0020 | faster |
| E2 vs FFTW MEASURE | 5 | 10 | **1.231** | [1.221, 1.241] | 0.0010 | 0.0020 | faster |

Per-block endpoint values (block order): E1 1.268, 1.291, 1.336, 1.326, 1.281, 1.241, 1.249, 1.273, 1.274, 1.264; E2 1.243, 1.253, 1.250, 1.207, 1.240, 1.208, 1.217, 1.228, 1.245, 1.217.

## Secondary endpoints

| endpoint | comparison | sizes | blocks | speedup | 95% CI |
|---|---|---|---|---|---|
| S1 | pmfft vs ducc | 2^22, 2^23, 2^24, 2^25, 2^26 | 10 | 1.771 | [1.761, 1.782] |
| S2 | pmfft_heur vs mkl | 2^22, 2^23, 2^24, 2^25, 2^26 | 10 | 1.246 | [1.235, 1.260] |
| S2 | pmfft_heur vs fftw_measure | 2^22, 2^23, 2^24, 2^25, 2^26 | 10 | 1.198 | [1.191, 1.206] |
| S3 | pmfft vs mkl | 3·2^20, 5·2^20, 3·2^22, 5·2^22 | 10 | 2.082 | [2.072, 2.095] |
| S3 | pmfft vs fftw_measure | 3·2^20 | 10 | 0.885 | [0.876, 0.893] |

## S4: per-size speedups (95% block-bootstrap CI) and median GFlop/s

| n | set | GF pmfft | GF pmfft_heur | GF mkl | GF fftw_measure | GF ducc | vs MKL | vs FFTW | vs ducc0 | heur vs MKL |
|---|---|---|---|---|---|---|---|---|---|---|
| 2^22 | P | 16.16 | 16.19 | 15.42 | 14.39 | 10.09 | 1.077 [1.039, 1.130] | 1.125 [1.121, 1.129] | 1.589 [1.572, 1.603] | 1.070 [1.041, 1.110] |
| 2^23 | P | 15.28 | 15.38 | 12.54 | 12.31 | 8.72 | 1.233 [1.214, 1.262] | 1.244 [1.235, 1.255] | 1.756 [1.747, 1.766] | 1.238 [1.220, 1.266] |
| 2^24 | P | 15.49 | 14.85 | 11.91 | 12.15 | 8.26 | 1.271 [1.236, 1.301] | 1.234 [1.196, 1.270] | 1.823 [1.778, 1.862] | 1.238 [1.230, 1.246] |
| 2^25 | P | 15.54 | 14.96 | 10.83 | 12.15 | 8.19 | 1.422 [1.403, 1.440] | 1.273 [1.265, 1.279] | 1.887 [1.861, 1.910] | 1.371 [1.357, 1.384] |
| 2^26 | P | 16.05 | 14.82 | 10.95 | 12.18 | 8.67 | 1.432 [1.387, 1.467] | 1.285 [1.248, 1.317] | 1.817 [1.768, 1.853] | 1.338 [1.319, 1.355] |
| 3·2^20 | Q | 16.43 | 16.39 | 9.42 | 18.39 | 10.93 | 1.729 [1.709, 1.747] | 0.885 [0.876, 0.893] | 1.489 [1.472, 1.505] | 1.717 [1.680, 1.743] |
| 5·2^20 | Q | 15.93 | 15.88 | 7.17 | 8.69 | 8.91 | 2.220 [2.212, 2.229] | 1.832 [1.814, 1.849] † | 1.792 [1.783, 1.802] | 2.194 [2.152, 2.222] |
| 3·2^22 | Q | 15.36 | 15.86 | 6.34 | 9.16 | 8.30 | 2.417 [2.366, 2.465] | 1.673 [1.641, 1.700] † | 1.842 [1.811, 1.877] | 2.504 [2.489, 2.520] |
| 5·2^22 | Q | 15.80 | 15.80 | 7.78 | 6.03 | 8.22 | 2.027 [2.018, 2.036] | 2.611 [2.592, 2.627] † | 1.905 [1.890, 1.918] | 2.028 [2.024, 2.032] |

## Noise

Within-run spread: (p75 − p25) / median of the samples of one run, median over blocks. Between-block CV: standard deviation / mean of the run medians over blocks.

| n | pmfft within / between | pmfft_heur within / between | mkl within / between | fftw_measure within / between | ducc within / between |
|---|---|---|---|---|---|
| 2^22 | 1.4% / 0.4% | 0.8% / 2.7% | 0.5% / 7.4% | 0.4% / 0.5% | 1.6% / 1.5% |
| 2^23 | 0.4% / 1.0% | 0.2% / 0.7% | 0.4% / 3.6% | 0.4% / 0.8% | 0.5% / 0.3% |
| 2^24 | 0.1% / 4.6% | 0.1% / 0.7% | 0.1% / 1.0% | 0.2% / 2.9% | 0.3% / 1.8% |
| 2^25 | 0.2% / 1.9% | 0.1% / 0.8% | 0.3% / 1.1% | 0.2% / 2.2% | 0.2% / 1.0% |
| 2^26 | 0.1% / 4.1% | 0.2% / 2.4% | 0.2% / 1.0% | 0.1% / 1.8% | 0.1% / 0.9% |
| 3·2^20 | 0.7% / 1.5% | 1.1% / 3.3% | 0.9% / 0.4% | 0.8% / 0.3% | 2.0% / 0.8% |
| 5·2^20 | 0.6% / 0.4% | 0.5% / 3.2% | 0.3% / 0.7% | 2.4% / 1.3% | 1.6% / 0.9% |
| 3·2^22 | 0.4% / 3.0% | 0.3% / 0.3% | 0.1% / 0.9% | 0.2% / 0.5% | 0.3% / 1.5% |
| 5·2^22 | 0.1% / 0.8% | 0.1% / 0.3% | 0.2% / 0.3% | 0.3% / 1.5% | 0.3% / 1.4% |

## Drift

Slope of log t against block index (% per block, 95% CI), pooled over sizes per implementation (size fixed effects); the same for the paired log speedup of the primary comparisons; and the clock and temperature ranges.

| quantity | slope %/block | 95% CI |
|---|---|---|
| t, pmfft | +0.11 | [-0.07, +0.29] |
| t, pmfft_heur | -0.07 | [-0.21, +0.08] |
| t, mkl | -0.13 | [-0.33, +0.07] |
| t, fftw_measure | +0.01 | [-0.11, +0.13] |
| t, ducc | -0.01 | [-0.10, +0.08] |
| speedup vs mkl on P | -0.35 | [-0.81, +0.11] |
| speedup vs fftw_measure on P | -0.19 | [-0.50, +0.11] |

Package temperature before runs: nan–nan °C (median nan); after: nan–nan °C. AC power: [-1] (1 = on mains). Wall-clock span: 0.6 h.
