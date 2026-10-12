# Reproducibility study: pre-specified endpoints (`results/ENDPOINTS.md`)

10 blocks in 1 session(s) (20261011-230304); 450 runs, 4375 samples; retried runs: 0. Sizes P = 2^22, 2^23, 2^24, 2^25, 2^26; Q = 3·2^20, 5·2^20, 3·2^22, 5·2^22. FFTW plans capped (excluded from FFTW endpoints): 5·2^20, 3·2^22, 5·2^22.

## Primary endpoints

Geometric-mean speedup over P (> 1: SweepFFT faster), 95% block-bootstrap interval, one-sided exact sign-flip p-value, Holm-adjusted across E1 and E2.

| endpoint | sizes | blocks | speedup | 95% CI | p | p (Holm) | decision |
|---|---|---|---|---|---|---|---|
| E1 vs MKL (secondary on AMD) | 5 | 10 | **1.741** | [1.739, 1.743] | 0.0010 | 0.0020 | faster |
| E2 vs FFTW MEASURE | 5 | 10 | **1.597** | [1.594, 1.599] | 0.0010 | 0.0020 | faster |

Per-block endpoint values (block order): E1 1.737, 1.737, 1.746, 1.737, 1.740, 1.741, 1.740, 1.742, 1.743, 1.744; E2 1.598, 1.589, 1.600, 1.591, 1.600, 1.599, 1.597, 1.597, 1.599, 1.597.

## Secondary endpoints

| endpoint | comparison | sizes | blocks | speedup | 95% CI |
|---|---|---|---|---|---|
| S1 | pmfft vs ducc | 2^22, 2^23, 2^24, 2^25, 2^26 | 10 | 2.531 | [2.529, 2.534] |
| S2 | pmfft_heur vs mkl | 2^22, 2^23, 2^24, 2^25, 2^26 | 10 | 1.746 | [1.743, 1.749] |
| S2 | pmfft_heur vs fftw_measure | 2^22, 2^23, 2^24, 2^25, 2^26 | 10 | 1.602 | [1.599, 1.604] |
| S3 | pmfft vs mkl | 3·2^20, 5·2^20, 3·2^22, 5·2^22 | 10 | 3.283 | [3.276, 3.290] |
| S3 | pmfft vs fftw_measure | 3·2^20 | 10 | 2.992 | [2.979, 3.005] |

## S4: per-size speedups (95% block-bootstrap CI) and median GFlop/s

| n | set | GF pmfft | GF pmfft_heur | GF mkl | GF fftw_measure | GF ducc | vs MKL | vs FFTW | vs ducc0 | heur vs MKL |
|---|---|---|---|---|---|---|---|---|---|---|
| 2^22 | P | 11.53 | 11.48 | 6.57 | 7.20 | 5.13 | 1.757 [1.750, 1.764] | 1.603 [1.599, 1.606] | 2.245 [2.240, 2.250] | 1.752 [1.739, 1.765] |
| 2^23 | P | 11.56 | 11.54 | 6.59 | 7.40 | 5.25 | 1.754 [1.748, 1.761] | 1.563 [1.559, 1.567] | 2.200 [2.195, 2.205] | 1.753 [1.751, 1.755] |
| 2^24 | P | 11.27 | 10.98 | 6.75 | 7.44 | 4.11 | 1.672 [1.669, 1.676] | 1.517 [1.513, 1.520] | 2.746 [2.739, 2.753] | 1.629 [1.624, 1.635] |
| 2^25 | P | 11.41 | 11.80 | 6.59 | 7.17 | 4.18 | 1.731 [1.727, 1.736] | 1.592 [1.585, 1.600] | 2.726 [2.718, 2.736] | 1.791 [1.785, 1.798] |
| 2^26 | P | 11.84 | 11.96 | 6.60 | 6.89 | 4.21 | 1.790 [1.787, 1.794] | 1.716 [1.711, 1.720] | 2.812 [2.807, 2.815] | 1.811 [1.805, 1.816] |
| 3·2^20 | Q | 11.47 | 11.45 | 2.95 | 3.84 | 5.04 | 3.888 [3.869, 3.907] | 2.992 [2.979, 3.005] | 2.275 [2.269, 2.281] | 3.879 [3.864, 3.895] |
| 5·2^20 | Q | 11.80 | 11.67 | 2.97 | 0.77 | 5.16 | 3.968 [3.948, 3.987] | 15.393 [15.300, 15.523] † | 2.285 [2.276, 2.293] | 3.932 [3.907, 3.956] |
| 3·2^22 | Q | 11.27 | 11.27 | 3.05 | 0.53 | 4.03 | 3.702 [3.692, 3.713] | 21.114 [21.055, 21.180] † | 2.798 [2.793, 2.803] | 3.701 [3.687, 3.716] |
| 5·2^22 | Q | 11.50 | 11.47 | 5.65 | 1.11 | 4.12 | 2.034 [2.028, 2.040] | 10.368 [10.327, 10.410] † | 2.788 [2.781, 2.794] | 2.031 [2.026, 2.036] |

## Noise

Within-run spread: (p75 − p25) / median of the samples of one run, median over blocks. Between-block CV: standard deviation / mean of the run medians over blocks.

| n | pmfft within / between | pmfft_heur within / between | mkl within / between | fftw_measure within / between | ducc within / between |
|---|---|---|---|---|---|
| 2^22 | 0.1% / 0.4% | 0.1% / 0.7% | 0.1% / 0.7% | 0.2% / 0.4% | 0.1% / 0.2% |
| 2^23 | 0.1% / 0.5% | 0.1% / 0.3% | 0.1% / 0.2% | 0.1% / 0.3% | 0.1% / 0.5% |
| 2^24 | 0.1% / 0.3% | 0.1% / 0.3% | 0.1% / 0.4% | 0.1% / 0.4% | 0.1% / 0.3% |
| 2^25 | 0.1% / 0.5% | 0.1% / 0.4% | 0.0% / 0.3% | 0.1% / 0.4% | 0.1% / 0.2% |
| 2^26 | 0.1% / 0.3% | 0.1% / 0.5% | 0.0% / 0.3% | 0.1% / 0.3% | 0.0% / 0.1% |
| 3·2^20 | 0.1% / 0.5% | 0.1% / 0.5% | 0.4% / 0.6% | 0.1% / 0.5% | 0.1% / 0.2% |
| 5·2^20 | 0.2% / 0.5% | 0.1% / 0.5% | 0.4% / 0.7% | 0.1% / 1.1% | 0.1% / 0.3% |
| 3·2^22 | 0.1% / 0.4% | 0.1% / 0.4% | 0.2% / 0.5% | 0.0% / 0.3% | 0.1% / 0.2% |
| 5·2^22 | 0.1% / 0.5% | 0.1% / 0.4% | 0.1% / 0.2% | 0.0% / 0.4% | 0.0% / 0.3% |

## Drift

Slope of log t against block index (% per block, 95% CI), pooled over sizes per implementation (size fixed effects); the same for the paired log speedup of the primary comparisons; and the clock and temperature ranges.

| quantity | slope %/block | 95% CI |
|---|---|---|
| t, pmfft | -0.03 | [-0.06, -0.00] |
| t, pmfft_heur | +0.01 | [-0.03, +0.04] |
| t, mkl | -0.03 | [-0.06, +0.01] |
| t, fftw_measure | -0.01 | [-0.04, +0.03] |
| t, ducc | -0.01 | [-0.03, +0.01] |
| speedup vs mkl on P | +0.04 | [-0.02, +0.09] |
| speedup vs fftw_measure on P | +0.02 | [-0.03, +0.07] |

Effective core clock during the timed loop (GHz), min / median / max per implementation: pmfft 4.21 / 4.22 / 4.23; pmfft_heur 4.20 / 4.22 / 4.23; mkl 4.25 / 4.27 / 4.30; fftw_measure 4.23 / 4.24 / 4.31; ducc 4.27 / 4.28 / 4.28.

Correlation of effective clock with log t (relative to each implementation and size's median): +0.06.

Package temperature before runs: 78–100 °C (median 92); after: 78–100 °C. AC power: [-1] (1 = on mains). Wall-clock span: 0.8 h.
