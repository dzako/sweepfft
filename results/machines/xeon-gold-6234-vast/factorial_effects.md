# Full factorial ablation (2^4) on log runtime

## n = 262144  (all off -> all on: 1.14x faster; residual sd 0.023 in log t, 32 dof, R^2 = 0.9994)

| term | runtime ratio (main: on/off; interaction: ratio of ratios) | 95% CI | share of explained SS |
|---|---|---|---|
| BATCH:FUSE | 0.168 | 0.163-0.172 | 32.3% |
| BATCH | 0.431 | 0.425-0.437 | 28.7% |
| NT | 1.624 | 1.602-1.647 | 9.5% |
| FUSE | 1.617 | 1.595-1.639 | 9.3% |
| NT:BATCH | 0.446 | 0.434-0.458 | 6.6% |
| NT:BATCH:FUSE | 0.206 | 0.195-0.217 | 6.3% |
| NT:FUSE | 1.827 | 1.778-1.878 | 3.7% |
| BATCH:SPLIT | 1.561 | 1.519-1.604 | 2.0% |
| SPLIT | 1.177 | 1.161-1.193 | 1.1% |
| FUSE:SPLIT | 0.872 | 0.848-0.896 | 0.2% |
| NT:SPLIT | 0.907 | 0.883-0.932 | 0.1% |
| NT:BATCH:SPLIT | 0.857 | 0.811-0.904 | 0.1% |
| BATCH:FUSE:SPLIT | 1.151 | 1.091-1.216 | 0.1% |

6 term(s) explain 90% of the explained variance: BATCH:FUSE, BATCH, NT, FUSE, NT:BATCH, NT:BATCH:FUSE

NT simple effects (runtime ratio NT on / off, geometric mean over SPLIT and rounds):

| BATCH | FUSE | ratio |
|---|---|---|
| 0 | 0 | 1.212 |
| 0 | 1 | 4.883 |
| 1 | 0 | 1.192 |
| 1 | 1 | 0.987 |

## n = 1048576  (all off -> all on: 1.72x faster; residual sd 0.011 in log t, 32 dof, R^2 = 0.9999)

| term | runtime ratio (main: on/off; interaction: ratio of ratios) | 95% CI | share of explained SS |
|---|---|---|---|
| BATCH:FUSE | 0.147 | 0.145-0.149 | 38.9% |
| BATCH | 0.407 | 0.404-0.409 | 34.3% |
| FUSE | 1.735 | 1.723-1.746 | 12.9% |
| NT:BATCH | 0.495 | 0.489-0.502 | 5.2% |
| NT:BATCH:FUSE | 0.249 | 0.242-0.256 | 5.1% |
| SPLIT | 1.199 | 1.191-1.207 | 1.4% |
| NT:FUSE | 1.417 | 1.398-1.436 | 1.3% |
| BATCH:SPLIT | 1.235 | 1.219-1.251 | 0.5% |
| NT:FUSE:SPLIT | 0.741 | 0.722-0.761 | 0.2% |
| NT | 1.040 | 1.033-1.047 | 0.1% |
| NT:SPLIT | 0.925 | 0.913-0.937 | 0.1% |
| FUSE:SPLIT | 1.072 | 1.059-1.087 | 0.1% |
| NT:BATCH:FUSE:SPLIT | 1.115 | 1.058-1.175 | 0.0% |
| NT:BATCH:SPLIT | 1.040 | 1.013-1.068 | 0.0% |

4 term(s) explain 90% of the explained variance: BATCH:FUSE, BATCH, FUSE, NT:BATCH

NT simple effects (runtime ratio NT on / off, geometric mean over SPLIT and rounds):

| BATCH | FUSE | ratio |
|---|---|---|
| 0 | 0 | 0.877 |
| 0 | 1 | 2.490 |
| 1 | 0 | 0.871 |
| 1 | 1 | 0.615 |

## n = 4194304  (all off -> all on: 1.80x faster; residual sd 0.003 in log t, 32 dof, R^2 = 1.0000)

| term | runtime ratio (main: on/off; interaction: ratio of ratios) | 95% CI | share of explained SS |
|---|---|---|---|
| BATCH:FUSE | 0.128 | 0.127-0.128 | 39.8% |
| BATCH | 0.371 | 0.370-0.372 | 36.9% |
| FUSE | 1.998 | 1.994-2.002 | 18.0% |
| NT:BATCH:FUSE | 0.449 | 0.445-0.452 | 1.5% |
| NT:BATCH | 0.673 | 0.670-0.675 | 1.5% |
| NT | 0.831 | 0.830-0.833 | 1.3% |
| SPLIT | 1.134 | 1.131-1.136 | 0.6% |
| BATCH:SPLIT | 1.206 | 1.201-1.211 | 0.3% |
| BATCH:FUSE:SPLIT | 0.899 | 0.892-0.907 | 0.0% |
| NT:FUSE | 1.045 | 1.041-1.050 | 0.0% |
| NT:BATCH:FUSE:SPLIT | 0.895 | 0.880-0.909 | 0.0% |
| NT:BATCH:SPLIT | 0.946 | 0.938-0.954 | 0.0% |
| NT:FUSE:SPLIT | 1.045 | 1.036-1.053 | 0.0% |
| FUSE:SPLIT | 1.019 | 1.015-1.023 | 0.0% |
| NT:SPLIT | 1.009 | 1.005-1.013 | 0.0% |

3 term(s) explain 90% of the explained variance: BATCH:FUSE, BATCH, FUSE

NT simple effects (runtime ratio NT on / off, geometric mean over SPLIT and rounds):

| BATCH | FUSE | ratio |
|---|---|---|
| 0 | 0 | 0.812 |
| 0 | 1 | 1.266 |
| 1 | 0 | 0.815 |
| 1 | 1 | 0.571 |

## n = 33554432  (all off -> all on: 1.80x faster; residual sd 0.004 in log t, 32 dof, R^2 = 1.0000)

| term | runtime ratio (main: on/off; interaction: ratio of ratios) | 95% CI | share of explained SS |
|---|---|---|---|
| BATCH:FUSE | 0.150 | 0.150-0.151 | 41.4% |
| BATCH | 0.440 | 0.438-0.441 | 31.1% |
| FUSE | 1.967 | 1.962-1.972 | 21.1% |
| NT | 0.790 | 0.789-0.792 | 2.5% |
| NT:BATCH:FUSE | 0.449 | 0.444-0.453 | 1.9% |
| NT:BATCH | 0.681 | 0.678-0.684 | 1.7% |
| BATCH:FUSE:SPLIT | 0.842 | 0.834-0.850 | 0.1% |
| NT:SPLIT | 1.080 | 1.075-1.085 | 0.1% |
| NT:FUSE:SPLIT | 1.137 | 1.127-1.148 | 0.0% |
| BATCH:SPLIT | 0.938 | 0.934-0.943 | 0.0% |
| FUSE:SPLIT | 0.960 | 0.955-0.964 | 0.0% |
| NT:FUSE | 0.966 | 0.961-0.970 | 0.0% |
| NT:BATCH:SPLIT | 1.071 | 1.061-1.081 | 0.0% |
| NT:BATCH:FUSE:SPLIT | 1.112 | 1.091-1.133 | 0.0% |
| SPLIT | 0.987 | 0.985-0.990 | 0.0% |

3 term(s) explain 90% of the explained variance: BATCH:FUSE, BATCH, FUSE

NT simple effects (runtime ratio NT on / off, geometric mean over SPLIT and rounds):

| BATCH | FUSE | ratio |
|---|---|---|
| 0 | 0 | 0.798 |
| 0 | 1 | 1.151 |
| 1 | 0 | 0.811 |
| 1 | 1 | 0.525 |

## NT x strip width (fused, balanced split)

| n | Bc = G | GF/s NT off | GF/s NT on | NT ratio (on/off time) | write S off | write S on |
|---|---|---|---|---|---|---|
| 4194304 | 1 | 0.79 | 0.66 | 1.206 | 3.00 | 3.00 |
| 4194304 | 2 | 1.37 | 1.43 | 0.954 | 3.00 | 3.00 |
| 4194304 | 4 | 2.62 | 7.48 | 0.351 | 3.00 | 3.00 |
| 4194304 | 8 | 4.58 | 7.72 | 0.593 | 3.00 | 3.00 |
| 4194304 | 16 | 5.32 | 7.04 | 0.756 | 3.00 | 3.00 |
| 4194304 | 32 | 5.00 | 5.56 | 0.900 | 3.00 | 3.00 |
| 33554432 | 1 | 0.87 | 0.79 | 1.107 | 3.00 | 3.00 |
| 33554432 | 2 | 1.43 | 1.59 | 0.899 | 3.00 | 3.00 |
| 33554432 | 4 | 2.78 | 7.13 | 0.390 | 3.00 | 3.00 |
| 33554432 | 8 | 3.13 | 6.55 | 0.478 | 3.00 | 3.00 |
| 33554432 | 16 | 4.32 | 5.73 | 0.753 | 3.00 | 3.00 |
| 33554432 | 32 | 3.91 | 4.31 | 0.905 | 3.00 | 3.00 |
