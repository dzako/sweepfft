# Reproducibility study: pre-specified endpoints (`results/ENDPOINTS.md`)

10 blocks in 1 session(s) (20261011-220624); 450 runs, 7121 samples; retried runs: 0. Sizes P = 2^22, 2^23, 2^24, 2^25, 2^26; Q = 3·2^20, 5·2^20, 3·2^22, 5·2^22. FFTW plans capped (excluded from FFTW endpoints): 5·2^20, 3·2^22, 5·2^22.

## Primary endpoints

Geometric-mean speedup over P (> 1: SweepFFT faster), 95% block-bootstrap interval, one-sided exact sign-flip p-value, Holm-adjusted across E1 and E2.

| endpoint | sizes | blocks | speedup | 95% CI | p | p (Holm) | decision |
|---|---|---|---|---|---|---|---|
| E1 vs MKL (secondary on AMD) | 5 | 10 | **1.147** | [1.142, 1.151] | 0.0010 | 0.0020 | faster |
| E2 vs FFTW MEASURE | 5 | 10 | **1.447** | [1.443, 1.452] | 0.0010 | 0.0020 | faster |

Per-block endpoint values (block order): E1 1.133, 1.148, 1.152, 1.154, 1.138, 1.148, 1.159, 1.147, 1.142, 1.148; E2 1.438, 1.458, 1.448, 1.442, 1.450, 1.452, 1.458, 1.443, 1.445, 1.436.

## Secondary endpoints

| endpoint | comparison | sizes | blocks | speedup | 95% CI |
|---|---|---|---|---|---|
| S1 | pmfft vs ducc | 2^22, 2^23, 2^24, 2^25, 2^26 | 10 | 1.619 | [1.612, 1.625] |
| S2 | pmfft_heur vs mkl | 2^22, 2^23, 2^24, 2^25, 2^26 | 10 | 1.181 | [1.176, 1.186] |
| S2 | pmfft_heur vs fftw_measure | 2^22, 2^23, 2^24, 2^25, 2^26 | 10 | 1.491 | [1.483, 1.498] |
| S3 | pmfft vs mkl | 3·2^20, 5·2^20, 3·2^22, 5·2^22 | 10 | 2.180 | [2.161, 2.202] |
| S3 | pmfft vs fftw_measure | 3·2^20 | 10 | 0.868 | [0.846, 0.906] |

## S4: per-size speedups (95% block-bootstrap CI) and median GFlop/s

| n | set | GF pmfft | GF pmfft_heur | GF mkl | GF fftw_measure | GF ducc | vs MKL | vs FFTW | vs ducc0 | heur vs MKL |
|---|---|---|---|---|---|---|---|---|---|---|
| 2^22 | P | 16.89 | 16.88 | 16.07 | 15.88 | 10.89 | 1.042 [1.027, 1.055] | 1.061 [1.056, 1.066] | 1.553 [1.542, 1.565] | 1.038 [1.024, 1.050] |
| 2^23 | P | 15.37 | 15.36 | 13.64 | 13.80 | 9.29 | 1.126 [1.122, 1.131] | 1.114 [1.111, 1.118] | 1.666 [1.646, 1.694] | 1.126 [1.121, 1.129] |
| 2^24 | P | 14.06 | 14.11 | 12.45 | 14.17 | 8.82 | 1.127 [1.123, 1.131] | 0.992 [0.986, 0.999] | 1.591 [1.582, 1.600] | 1.130 [1.124, 1.135] |
| 2^25 | P | 14.67 | 15.19 | 11.24 | 9.57 | 8.75 | 1.303 [1.300, 1.306] | 1.532 [1.526, 1.537] | 1.683 [1.671, 1.699] | 1.335 [1.303, 1.354] |
| 2^26 | P | 13.18 | 14.84 | 11.33 | 3.70 | 8.16 | 1.152 [1.143, 1.161] | 3.532 [3.501, 3.560] | 1.604 [1.590, 1.617] | 1.306 [1.298, 1.312] |
| 3·2^20 | Q | 17.22 | 17.16 | 9.61 | 20.19 | 11.51 | 1.805 [1.746, 1.873] | 0.868 [0.846, 0.906] | 1.496 [1.487, 1.505] | 1.803 [1.741, 1.875] |
| 5·2^20 | Q | 16.45 | 16.42 | 6.58 | 7.44 | 9.70 | 2.482 [2.446, 2.516] | 2.197 [2.157, 2.235] † | 1.681 [1.661, 1.701] | 2.489 [2.468, 2.509] |
| 3·2^22 | Q | 14.86 | 14.85 | 6.65 | 9.48 | 8.80 | 2.233 [2.212, 2.250] | 1.564 [1.550, 1.575] † | 1.682 [1.668, 1.693] | 2.231 [2.216, 2.244] |
| 5·2^22 | Q | 14.92 | 14.90 | 6.56 | 6.08 | 8.84 | 2.256 [2.210, 2.289] | 2.437 [2.390, 2.470] † | 1.674 [1.639, 1.700] | 2.272 [2.263, 2.281] |

## Noise

Within-run spread: (p75 − p25) / median of the samples of one run, median over blocks. Between-block CV: standard deviation / mean of the run medians over blocks.

| n | pmfft within / between | pmfft_heur within / between | mkl within / between | fftw_measure within / between | ducc within / between |
|---|---|---|---|---|---|
| 2^22 | 0.9% / 0.9% | 1.5% / 1.9% | 0.9% / 2.4% | 0.4% / 0.5% | 1.0% / 0.8% |
| 2^23 | 0.2% / 0.5% | 0.2% / 0.5% | 0.4% / 0.4% | 0.2% / 0.4% | 0.6% / 2.4% |
| 2^24 | 0.2% / 0.6% | 0.1% / 0.9% | 0.2% / 0.3% | 0.2% / 0.8% | 0.4% / 0.6% |
| 2^25 | 0.1% / 0.3% | 0.1% / 3.5% | 0.1% / 0.5% | 0.4% / 0.5% | 0.4% / 1.5% |
| 2^26 | 0.2% / 1.5% | 0.1% / 0.9% | 0.1% / 0.6% | 0.1% / 0.1% | 0.2% / 0.3% |
| 3·2^20 | 0.4% / 0.6% | 0.4% / 0.6% | 3.8% / 6.4% | 0.6% / 7.1% | 1.2% / 0.7% |
| 5·2^20 | 0.9% / 2.2% | 0.7% / 1.2% | 0.5% / 0.7% | 1.5% / 1.3% | 1.0% / 0.6% |
| 3·2^22 | 0.3% / 1.0% | 0.2% / 1.0% | 0.2% / 1.0% | 0.3% / 0.6% | 0.4% / 0.6% |
| 5·2^22 | 0.3% / 3.3% | 0.1% / 0.6% | 0.2% / 0.4% | 0.5% / 0.6% | 0.3% / 0.6% |

## Drift

Slope of log t against block index (% per block, 95% CI), pooled over sizes per implementation (size fixed effects); the same for the paired log speedup of the primary comparisons; and the clock and temperature ranges.

| quantity | slope %/block | 95% CI |
|---|---|---|
| t, pmfft | -0.02 | [-0.13, +0.09] |
| t, pmfft_heur | +0.05 | [-0.06, +0.16] |
| t, mkl | -0.10 | [-0.27, +0.07] |
| t, fftw_measure | +0.01 | [-0.16, +0.17] |
| t, ducc | +0.03 | [-0.04, +0.11] |
| speedup vs mkl on P | +0.05 | [-0.08, +0.17] |
| speedup vs fftw_measure on P | -0.04 | [-0.13, +0.06] |

Package temperature before runs: nan–nan °C (median nan); after: nan–nan °C. AC power: [-1] (1 = on mains). Wall-clock span: 0.6 h.
