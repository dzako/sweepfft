# Reproducibility study: pre-specified endpoints (`results/ENDPOINTS.md`)

10 blocks in 1 session(s) (20261011-234248); 450 runs, 3900 samples; retried runs: 0. Sizes P = 2^22, 2^23, 2^24, 2^25, 2^26; Q = 3·2^20, 5·2^20, 3·2^22, 5·2^22. FFTW plans capped (excluded from FFTW endpoints): 5·2^20, 3·2^22, 5·2^22.

## Primary endpoints

Geometric-mean speedup over P (> 1: SweepFFT faster), 95% block-bootstrap interval, one-sided exact sign-flip p-value, Holm-adjusted across E1 and E2.

| endpoint | sizes | blocks | speedup | 95% CI | p | p (Holm) | decision |
|---|---|---|---|---|---|---|---|
| E1 vs MKL (secondary on AMD) | 5 | 10 | **1.651** | [1.649, 1.653] | 0.0010 | 0.0020 | faster |
| E2 vs FFTW MEASURE | 5 | 10 | **1.561** | [1.559, 1.565] | 0.0010 | 0.0020 | faster |

Per-block endpoint values (block order): E1 1.655, 1.649, 1.647, 1.649, 1.651, 1.654, 1.649, 1.656, 1.655, 1.645; E2 1.565, 1.558, 1.556, 1.563, 1.558, 1.562, 1.559, 1.574, 1.561, 1.560.

## Secondary endpoints

| endpoint | comparison | sizes | blocks | speedup | 95% CI |
|---|---|---|---|---|---|
| S1 | pmfft vs ducc | 2^22, 2^23, 2^24, 2^25, 2^26 | 10 | 2.277 | [2.273, 2.282] |
| S2 | pmfft_heur vs mkl | 2^22, 2^23, 2^24, 2^25, 2^26 | 10 | 1.672 | [1.670, 1.674] |
| S2 | pmfft_heur vs fftw_measure | 2^22, 2^23, 2^24, 2^25, 2^26 | 10 | 1.581 | [1.580, 1.583] |
| S3 | pmfft vs mkl | 3·2^20, 5·2^20, 3·2^22, 5·2^22 | 10 | 3.265 | [3.251, 3.278] |
| S3 | pmfft vs fftw_measure | 3·2^20 | 10 | 1.050 | [1.046, 1.055] |

## S4: per-size speedups (95% block-bootstrap CI) and median GFlop/s

| n | set | GF pmfft | GF pmfft_heur | GF mkl | GF fftw_measure | GF ducc | vs MKL | vs FFTW | vs ducc0 | heur vs MKL |
|---|---|---|---|---|---|---|---|---|---|---|
| 2^22 | P | 9.09 | 9.03 | 5.46 | 5.83 | 3.88 | 1.662 [1.654, 1.670] | 1.560 [1.554, 1.565] | 2.341 [2.329, 2.351] | 1.652 [1.642, 1.662] |
| 2^23 | P | 9.12 | 9.16 | 5.47 | 5.95 | 3.99 | 1.670 [1.658, 1.682] | 1.538 [1.528, 1.550] | 2.292 [2.276, 2.309] | 1.674 [1.669, 1.678] |
| 2^24 | P | 8.87 | 8.77 | 5.62 | 5.97 | 3.98 | 1.578 [1.574, 1.582] | 1.488 [1.484, 1.492] | 2.227 [2.216, 2.238] | 1.558 [1.552, 1.564] |
| 2^25 | P | 9.04 | 9.52 | 5.48 | 5.76 | 4.06 | 1.646 [1.638, 1.654] | 1.569 [1.564, 1.574] | 2.226 [2.218, 2.235] | 1.733 [1.727, 1.738] |
| 2^26 | P | 9.35 | 9.63 | 5.49 | 5.63 | 4.06 | 1.701 [1.696, 1.706] | 1.658 [1.650, 1.665] | 2.301 [2.295, 2.309] | 1.750 [1.742, 1.757] |
| 3·2^20 | Q | 9.23 | 9.17 | 2.34 | 8.77 | 3.80 | 3.929 [3.911, 3.945] | 1.050 [1.046, 1.055] | 2.415 [2.397, 2.433] | 3.916 [3.897, 3.934] |
| 5·2^20 | Q | 9.17 | 9.18 | 2.37 | 0.59 | 3.92 | 3.862 [3.826, 3.897] | 15.648 [15.523, 15.767] † | 2.341 [2.323, 2.357] | 3.872 [3.845, 3.901] |
| 3·2^22 | Q | 9.01 | 9.06 | 2.43 | 0.42 | 3.92 | 3.729 [3.683, 3.768] | 21.679 [21.448, 21.882] † | 2.300 [2.279, 2.322] | 3.733 [3.691, 3.777] |
| 5·2^22 | Q | 9.26 | 9.28 | 4.62 | 0.85 | 3.99 | 2.008 [2.002, 2.016] | 10.932 [10.906, 10.956] † | 2.345 [2.317, 2.391] | 2.012 [2.005, 2.021] |

## Noise

Within-run spread: (p75 − p25) / median of the samples of one run, median over blocks. Between-block CV: standard deviation / mean of the run medians over blocks.

| n | pmfft within / between | pmfft_heur within / between | mkl within / between | fftw_measure within / between | ducc within / between |
|---|---|---|---|---|---|
| 2^22 | 0.1% / 0.4% | 0.1% / 0.7% | 0.1% / 0.7% | 0.1% / 0.3% | 0.1% / 0.7% |
| 2^23 | 0.2% / 1.0% | 0.1% / 0.3% | 0.0% / 0.5% | 0.1% / 0.4% | 0.0% / 0.7% |
| 2^24 | 0.1% / 0.4% | 0.1% / 0.5% | 1.1% / 0.3% | 0.2% / 0.4% | 0.3% / 0.5% |
| 2^25 | 0.1% / 0.7% | 0.1% / 0.5% | 0.2% / 0.3% | 0.2% / 0.5% | 0.3% / 0.4% |
| 2^26 | 0.2% / 0.4% | 0.2% / 0.6% | 0.1% / 0.3% | 0.1% / 0.6% | 4.1% / 0.5% |
| 3·2^20 | 0.2% / 0.8% | 0.1% / 0.5% | 0.1% / 0.5% | 0.1% / 0.4% | 0.2% / 0.8% |
| 5·2^20 | 0.2% / 1.2% | 0.2% / 0.8% | 0.2% / 0.6% | 0.3% / 0.3% | 0.1% / 0.5% |
| 3·2^22 | 0.1% / 1.7% | 0.2% / 1.4% | 3.5% / 1.2% | 0.2% / 0.2% | 0.1% / 0.6% |
| 5·2^22 | 0.1% / 0.3% | 0.1% / 0.4% | 0.4% / 0.7% | 0.3% / 0.1% | 3.9% / 3.2% |

## Drift

Slope of log t against block index (% per block, 95% CI), pooled over sizes per implementation (size fixed effects); the same for the paired log speedup of the primary comparisons; and the clock and temperature ranges.

| quantity | slope %/block | 95% CI |
|---|---|---|
| t, pmfft | +0.01 | [-0.06, +0.07] |
| t, pmfft_heur | -0.00 | [-0.06, +0.05] |
| t, mkl | +0.01 | [-0.03, +0.06] |
| t, fftw_measure | +0.03 | [+0.01, +0.06] |
| t, ducc | +0.01 | [-0.07, +0.10] |
| speedup vs mkl on P | +0.00 | [-0.08, +0.09] |
| speedup vs fftw_measure on P | +0.02 | [-0.05, +0.10] |

Package temperature before runs: 46–52 °C (median 50); after: 46–52 °C. AC power: [-1] (1 = on mains). Wall-clock span: 1.0 h.
