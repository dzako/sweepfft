# Full factorial ablation (2^4) on log runtime

## n = 262144  (all off -> all on: 1.49x faster; residual sd 0.009 in log t, 32 dof, R^2 = 0.9994)

| term | runtime ratio (main: on/off; interaction: ratio of ratios) | 95% CI | share of explained SS |
|---|---|---|---|
| BATCH:FUSE | 0.453 | 0.448-0.458 | 41.0% |
| BATCH | 0.684 | 0.680-0.688 | 37.7% |
| NT:SPLIT | 0.733 | 0.725-0.741 | 6.3% |
| SPLIT | 1.140 | 1.134-1.146 | 4.5% |
| BATCH:SPLIT | 0.798 | 0.789-0.807 | 3.3% |
| NT:FUSE | 1.204 | 1.191-1.218 | 2.3% |
| NT:BATCH | 0.854 | 0.845-0.864 | 1.6% |
| NT | 0.934 | 0.929-0.940 | 1.2% |
| FUSE:SPLIT | 0.874 | 0.864-0.883 | 1.2% |
| NT:BATCH:FUSE | 0.859 | 0.840-0.877 | 0.4% |
| FUSE | 0.972 | 0.966-0.977 | 0.2% |
| BATCH:FUSE:SPLIT | 0.894 | 0.874-0.913 | 0.2% |
| NT:FUSE:SPLIT | 1.031 | 1.009-1.054 | 0.0% |

5 term(s) explain 90% of the explained variance: BATCH:FUSE, BATCH, NT:SPLIT, SPLIT, BATCH:SPLIT

NT simple effects (runtime ratio NT on / off, geometric mean over SPLIT and rounds):

| BATCH | FUSE | ratio |
|---|---|---|
| 0 | 0 | 0.887 |
| 0 | 1 | 1.153 |
| 1 | 0 | 0.818 |
| 1 | 1 | 0.912 |

DRAM traffic per cell (median read + write sweeps):

| NT | BATCH | FUSE | SPLIT | read S | write S | GF/s |
|---|---|---|---|---|---|---|
| 0 | 0 | 0 | 0 | 9.47 | nan | 7.95 |
| 0 | 0 | 0 | 1 | 11.88 | nan | 5.04 |
| 0 | 0 | 1 | 0 | -0.08 | nan | 5.95 |
| 0 | 0 | 1 | 1 | 0.29 | nan | 4.19 |
| 0 | 1 | 0 | 0 | 9.66 | nan | 6.85 |
| 0 | 1 | 0 | 1 | 19.70 | nan | 5.20 |
| 0 | 1 | 1 | 0 | 0.01 | nan | 10.01 |
| 0 | 1 | 1 | 1 | 10.74 | nan | 9.44 |
| 1 | 0 | 0 | 0 | 21.96 | nan | 7.56 |
| 1 | 0 | 0 | 1 | 21.58 | nan | 6.76 |
| 1 | 0 | 1 | 0 | 19.98 | nan | 4.48 |
| 1 | 0 | 1 | 1 | 18.54 | nan | 4.25 |
| 1 | 1 | 0 | 0 | 22.00 | nan | 7.16 |
| 1 | 1 | 0 | 1 | 27.75 | nan | 7.47 |
| 1 | 1 | 1 | 0 | 5.63 | nan | 9.51 |
| 1 | 1 | 1 | 1 | 7.15 | nan | 11.84 |

## n = 1048576  (all off -> all on: 1.73x faster; residual sd 0.012 in log t, 32 dof, R^2 = 0.9994)

| term | runtime ratio (main: on/off; interaction: ratio of ratios) | 95% CI | share of explained SS |
|---|---|---|---|
| BATCH | 0.594 | 0.589-0.598 | 46.2% |
| BATCH:FUSE | 0.463 | 0.456-0.469 | 25.2% |
| NT | 0.729 | 0.724-0.734 | 16.9% |
| SPLIT | 1.231 | 1.223-1.240 | 7.3% |
| NT:SPLIT | 0.838 | 0.827-0.850 | 1.3% |
| FUSE | 1.088 | 1.080-1.095 | 1.2% |
| NT:FUSE | 1.139 | 1.124-1.155 | 0.7% |
| BATCH:SPLIT | 1.102 | 1.086-1.117 | 0.4% |
| NT:BATCH | 0.921 | 0.909-0.934 | 0.3% |
| FUSE:SPLIT | 0.926 | 0.913-0.939 | 0.3% |
| NT:FUSE:SPLIT | 0.922 | 0.897-0.948 | 0.1% |
| NT:BATCH:SPLIT | 1.070 | 1.041-1.101 | 0.0% |
| NT:BATCH:FUSE:SPLIT | 1.092 | 1.033-1.155 | 0.0% |

4 term(s) explain 90% of the explained variance: BATCH, BATCH:FUSE, NT, SPLIT

NT simple effects (runtime ratio NT on / off, geometric mean over SPLIT and rounds):

| BATCH | FUSE | ratio |
|---|---|---|
| 0 | 0 | 0.707 |
| 0 | 1 | 0.816 |
| 1 | 0 | 0.660 |
| 1 | 1 | 0.742 |

DRAM traffic per cell (median read + write sweeps):

| NT | BATCH | FUSE | SPLIT | read S | write S | GF/s |
|---|---|---|---|---|---|---|
| 0 | 0 | 0 | 0 | 29.13 | nan | 5.99 |
| 0 | 0 | 0 | 1 | 28.29 | nan | 4.53 |
| 0 | 0 | 1 | 0 | 9.08 | nan | 3.98 |
| 0 | 0 | 1 | 1 | 12.23 | nan | 3.09 |
| 0 | 1 | 0 | 0 | 29.10 | nan | 6.88 |
| 0 | 1 | 0 | 1 | 28.32 | nan | 4.84 |
| 0 | 1 | 1 | 0 | 10.59 | nan | 9.86 |
| 0 | 1 | 1 | 1 | 12.87 | nan | 7.12 |
| 1 | 0 | 0 | 0 | 25.27 | nan | 7.89 |
| 1 | 0 | 0 | 1 | 24.28 | nan | 6.89 |
| 1 | 0 | 1 | 0 | 22.03 | nan | 4.27 |
| 1 | 0 | 1 | 1 | 22.43 | nan | 4.33 |
| 1 | 1 | 0 | 0 | 25.51 | nan | 9.81 |
| 1 | 1 | 0 | 1 | 24.31 | nan | 7.82 |
| 1 | 1 | 1 | 0 | 7.77 | nan | 11.89 |
| 1 | 1 | 1 | 1 | 8.65 | nan | 10.39 |

## n = 4194304  (all off -> all on: 1.94x faster; residual sd 0.030 in log t, 32 dof, R^2 = 0.9980)

| term | runtime ratio (main: on/off; interaction: ratio of ratios) | 95% CI | share of explained SS |
|---|---|---|---|
| BATCH | 0.489 | 0.480-0.498 | 41.7% |
| BATCH:FUSE | 0.313 | 0.302-0.324 | 27.4% |
| NT | 0.627 | 0.616-0.639 | 17.7% |
| FUSE | 1.378 | 1.354-1.403 | 8.4% |
| NT:SPLIT | 0.704 | 0.679-0.729 | 2.5% |
| SPLIT | 1.134 | 1.114-1.154 | 1.3% |
| NT:BATCH:FUSE | 1.349 | 1.257-1.448 | 0.5% |
| NT:BATCH:FUSE:SPLIT | 1.500 | 1.302-1.728 | 0.2% |
| NT:FUSE:SPLIT | 0.839 | 0.782-0.901 | 0.2% |
| NT:BATCH:SPLIT | 1.184 | 1.103-1.271 | 0.1% |
| NT:BATCH | 1.063 | 1.026-1.101 | 0.1% |
| NT:FUSE | 0.963 | 0.930-0.998 | 0.0% |

4 term(s) explain 90% of the explained variance: BATCH, BATCH:FUSE, NT, FUSE

NT simple effects (runtime ratio NT on / off, geometric mean over SPLIT and rounds):

| BATCH | FUSE | ratio |
|---|---|---|
| 0 | 0 | 0.668 |
| 0 | 1 | 0.554 |
| 1 | 0 | 0.612 |
| 1 | 1 | 0.684 |

DRAM traffic per cell (median read + write sweeps):

| NT | BATCH | FUSE | SPLIT | read S | write S | GF/s |
|---|---|---|---|---|---|---|
| 0 | 0 | 0 | 0 | 29.09 | nan | 5.82 |
| 0 | 0 | 0 | 1 | 30.57 | nan | 4.58 |
| 0 | 0 | 1 | 0 | 19.33 | nan | 2.36 |
| 0 | 0 | 1 | 1 | 26.79 | nan | 1.55 |
| 0 | 1 | 0 | 0 | 29.08 | nan | 6.52 |
| 0 | 1 | 0 | 1 | 30.13 | nan | 4.90 |
| 0 | 1 | 1 | 0 | 10.55 | nan | 8.82 |
| 0 | 1 | 1 | 1 | 16.28 | nan | 7.24 |
| 1 | 0 | 0 | 0 | 24.14 | nan | 7.70 |
| 1 | 0 | 0 | 1 | 24.42 | nan | 7.75 |
| 1 | 0 | 1 | 0 | 24.80 | nan | 3.11 |
| 1 | 0 | 1 | 1 | 27.56 | nan | 3.81 |
| 1 | 1 | 0 | 0 | 24.32 | nan | 9.26 |
| 1 | 1 | 0 | 1 | 24.35 | nan | 9.22 |
| 1 | 1 | 1 | 0 | 6.92 | nan | 11.40 |
| 1 | 1 | 1 | 1 | 7.79 | nan | 11.31 |

## n = 33554432  (all off -> all on: 2.42x faster; residual sd 0.019 in log t, 32 dof, R^2 = 0.9994)

| term | runtime ratio (main: on/off; interaction: ratio of ratios) | 95% CI | share of explained SS |
|---|---|---|---|
| BATCH | 0.465 | 0.460-0.470 | 38.7% |
| BATCH:FUSE | 0.262 | 0.256-0.268 | 29.6% |
| NT | 0.565 | 0.559-0.572 | 21.4% |
| FUSE | 1.451 | 1.435-1.467 | 9.1% |
| NT:BATCH:FUSE | 1.525 | 1.459-1.594 | 0.7% |
| NT:BATCH | 1.136 | 1.111-1.162 | 0.3% |
| SPLIT | 0.972 | 0.961-0.983 | 0.1% |
| NT:SPLIT | 0.951 | 0.931-0.973 | 0.0% |
| NT:FUSE | 0.959 | 0.938-0.981 | 0.0% |
| BATCH:FUSE:SPLIT | 1.046 | 1.000-1.093 | 0.0% |
| BATCH:SPLIT | 1.023 | 1.000-1.045 | 0.0% |

4 term(s) explain 90% of the explained variance: BATCH, BATCH:FUSE, NT, FUSE

NT simple effects (runtime ratio NT on / off, geometric mean over SPLIT and rounds):

| BATCH | FUSE | ratio |
|---|---|---|
| 0 | 0 | 0.602 |
| 0 | 1 | 0.467 |
| 1 | 0 | 0.554 |
| 1 | 1 | 0.656 |

DRAM traffic per cell (median read + write sweeps):

| NT | BATCH | FUSE | SPLIT | read S | write S | GF/s |
|---|---|---|---|---|---|---|
| 0 | 0 | 0 | 0 | 30.00 | nan | 4.89 |
| 0 | 0 | 0 | 1 | 30.59 | nan | 4.88 |
| 0 | 0 | 1 | 0 | 23.07 | nan | 1.50 |
| 0 | 0 | 1 | 1 | 21.86 | nan | 1.53 |
| 0 | 1 | 0 | 0 | 28.87 | nan | 5.15 |
| 0 | 1 | 0 | 1 | 29.97 | nan | 5.17 |
| 0 | 1 | 1 | 0 | 12.89 | nan | 7.60 |
| 0 | 1 | 1 | 1 | 12.83 | nan | 7.81 |
| 1 | 0 | 0 | 0 | 22.78 | nan | 7.95 |
| 1 | 0 | 0 | 1 | 23.91 | nan | 8.25 |
| 1 | 0 | 1 | 0 | 24.90 | nan | 3.09 |
| 1 | 0 | 1 | 1 | 23.90 | nan | 3.41 |
| 1 | 1 | 0 | 0 | 22.54 | nan | 9.12 |
| 1 | 1 | 0 | 1 | 24.08 | nan | 9.51 |
| 1 | 1 | 1 | 0 | 7.67 | nan | 11.30 |
| 1 | 1 | 1 | 1 | 6.93 | nan | 11.85 |

## NT x strip width (fused, balanced split)

| n | Bc = G | GF/s NT off | GF/s NT on | NT ratio (on/off time) | write S off | write S on |
|---|---|---|---|---|---|---|
| 4194304 | 1 | 2.37 | 3.12 | 0.759 | nan | nan |
| 4194304 | 2 | 3.81 | 4.56 | 0.835 | nan | nan |
| 4194304 | 4 | 6.43 | 9.32 | 0.690 | nan | nan |
| 4194304 | 8 | 8.70 | 11.30 | 0.770 | nan | nan |
| 4194304 | 16 | 10.25 | 12.48 | 0.821 | nan | nan |
| 4194304 | 32 | 9.99 | 12.13 | 0.823 | nan | nan |
| 33554432 | 1 | 1.50 | 3.09 | 0.483 | nan | nan |
| 33554432 | 2 | 2.72 | 4.64 | 0.586 | nan | nan |
| 33554432 | 4 | 4.80 | 8.67 | 0.553 | nan | nan |
| 33554432 | 8 | 7.57 | 11.31 | 0.669 | nan | nan |
| 33554432 | 16 | 10.09 | 12.84 | 0.786 | nan | nan |
| 33554432 | 32 | 3.24 | 3.72 | 0.871 | nan | nan |
