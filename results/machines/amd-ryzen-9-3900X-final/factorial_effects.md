# Full factorial ablation (2^4) on log runtime

## n = 262144  (all off -> all on: 1.49x faster; residual sd 0.010 in log t, 32 dof, R^2 = 0.9994)

| term | runtime ratio (main: on/off; interaction: ratio of ratios) | 95% CI | share of explained SS |
|---|---|---|---|
| BATCH:FUSE | 0.443 | 0.438-0.448 | 42.5% |
| BATCH | 0.686 | 0.683-0.690 | 36.2% |
| NT:SPLIT | 0.727 | 0.719-0.735 | 6.5% |
| SPLIT | 1.146 | 1.140-1.153 | 4.8% |
| BATCH:SPLIT | 0.806 | 0.797-0.816 | 3.0% |
| NT:FUSE | 1.190 | 1.177-1.204 | 1.9% |
| NT:BATCH | 0.846 | 0.836-0.855 | 1.8% |
| NT | 0.924 | 0.919-0.930 | 1.6% |
| FUSE:SPLIT | 0.874 | 0.864-0.884 | 1.2% |
| NT:BATCH:FUSE | 0.857 | 0.838-0.877 | 0.4% |
| BATCH:FUSE:SPLIT | 0.915 | 0.895-0.936 | 0.1% |
| FUSE | 0.983 | 0.977-0.988 | 0.1% |
| NT:BATCH:FUSE:SPLIT | 0.930 | 0.889-0.973 | 0.0% |

5 term(s) explain 90% of the explained variance: BATCH:FUSE, BATCH, NT:SPLIT, SPLIT, BATCH:SPLIT

NT simple effects (runtime ratio NT on / off, geometric mean over SPLIT and rounds):

| BATCH | FUSE | ratio |
|---|---|---|
| 0 | 0 | 0.887 |
| 0 | 1 | 1.140 |
| 1 | 0 | 0.810 |
| 1 | 1 | 0.892 |

DRAM traffic per cell (median read + write sweeps):

| NT | BATCH | FUSE | SPLIT | read S | write S | GF/s |
|---|---|---|---|---|---|---|
| 0 | 0 | 0 | 0 | 9.50 | nan | 8.15 |
| 0 | 0 | 0 | 1 | 12.03 | nan | 5.11 |
| 0 | 0 | 1 | 0 | 0.02 | nan | 5.92 |
| 0 | 0 | 1 | 1 | 0.05 | nan | 4.17 |
| 0 | 1 | 0 | 0 | 9.67 | nan | 6.88 |
| 0 | 1 | 0 | 1 | 19.83 | nan | 5.25 |
| 0 | 1 | 1 | 0 | -0.01 | nan | 10.22 |
| 0 | 1 | 1 | 1 | 10.60 | nan | 9.17 |
| 1 | 0 | 0 | 0 | 21.97 | nan | 7.76 |
| 1 | 0 | 0 | 1 | 21.27 | nan | 6.91 |
| 1 | 0 | 1 | 0 | 20.10 | nan | 4.49 |
| 1 | 0 | 1 | 1 | 18.46 | nan | 4.26 |
| 1 | 1 | 0 | 0 | 21.96 | nan | 7.30 |
| 1 | 1 | 0 | 1 | 27.58 | nan | 7.47 |
| 1 | 1 | 1 | 0 | 5.70 | nan | 9.64 |
| 1 | 1 | 1 | 1 | 6.98 | nan | 12.14 |

## n = 1048576  (all off -> all on: 1.74x faster; residual sd 0.008 in log t, 32 dof, R^2 = 0.9997)

| term | runtime ratio (main: on/off; interaction: ratio of ratios) | 95% CI | share of explained SS |
|---|---|---|---|
| BATCH | 0.594 | 0.591-0.596 | 45.4% |
| BATCH:FUSE | 0.461 | 0.457-0.465 | 25.1% |
| NT | 0.719 | 0.716-0.722 | 18.2% |
| SPLIT | 1.228 | 1.222-1.233 | 7.0% |
| FUSE | 1.092 | 1.087-1.097 | 1.3% |
| NT:SPLIT | 0.854 | 0.847-0.862 | 1.0% |
| BATCH:SPLIT | 1.125 | 1.115-1.135 | 0.6% |
| NT:FUSE | 1.116 | 1.106-1.126 | 0.5% |
| NT:BATCH | 0.909 | 0.900-0.917 | 0.4% |
| FUSE:SPLIT | 0.912 | 0.904-0.921 | 0.4% |
| NT:FUSE:SPLIT | 0.936 | 0.919-0.953 | 0.0% |
| BATCH:FUSE:SPLIT | 1.065 | 1.046-1.084 | 0.0% |
| NT:BATCH:SPLIT | 1.062 | 1.043-1.082 | 0.0% |
| NT:BATCH:FUSE | 0.950 | 0.933-0.968 | 0.0% |
| NT:BATCH:FUSE:SPLIT | 1.072 | 1.034-1.111 | 0.0% |

4 term(s) explain 90% of the explained variance: BATCH, BATCH:FUSE, NT, SPLIT

NT simple effects (runtime ratio NT on / off, geometric mean over SPLIT and rounds):

| BATCH | FUSE | ratio |
|---|---|---|
| 0 | 0 | 0.705 |
| 0 | 1 | 0.807 |
| 1 | 0 | 0.657 |
| 1 | 1 | 0.715 |

DRAM traffic per cell (median read + write sweeps):

| NT | BATCH | FUSE | SPLIT | read S | write S | GF/s |
|---|---|---|---|---|---|---|
| 0 | 0 | 0 | 0 | 29.13 | nan | 6.07 |
| 0 | 0 | 0 | 1 | 28.23 | nan | 4.61 |
| 0 | 0 | 1 | 0 | 9.06 | nan | 3.92 |
| 0 | 0 | 1 | 1 | 11.46 | nan | 3.17 |
| 0 | 1 | 0 | 0 | 29.21 | nan | 6.95 |
| 0 | 1 | 0 | 1 | 28.21 | nan | 4.90 |
| 0 | 1 | 1 | 0 | 10.82 | nan | 9.52 |
| 0 | 1 | 1 | 1 | 12.59 | nan | 7.05 |
| 1 | 0 | 0 | 0 | 25.27 | nan | 8.03 |
| 1 | 0 | 0 | 1 | 24.42 | nan | 6.99 |
| 1 | 0 | 1 | 0 | 21.77 | nan | 4.29 |
| 1 | 0 | 1 | 1 | 22.37 | nan | 4.43 |
| 1 | 1 | 0 | 0 | 25.39 | nan | 10.01 |
| 1 | 1 | 0 | 1 | 24.38 | nan | 7.87 |
| 1 | 1 | 1 | 0 | 8.23 | nan | 12.38 |
| 1 | 1 | 1 | 1 | 8.71 | nan | 10.57 |

## n = 4194304  (all off -> all on: 1.95x faster; residual sd 0.006 in log t, 32 dof, R^2 = 0.9999)

| term | runtime ratio (main: on/off; interaction: ratio of ratios) | 95% CI | share of explained SS |
|---|---|---|---|
| BATCH | 0.489 | 0.487-0.490 | 41.4% |
| BATCH:FUSE | 0.310 | 0.308-0.312 | 27.7% |
| NT | 0.624 | 0.621-0.626 | 18.0% |
| FUSE | 1.376 | 1.371-1.381 | 8.2% |
| NT:SPLIT | 0.707 | 0.702-0.712 | 2.4% |
| SPLIT | 1.114 | 1.110-1.118 | 0.9% |
| NT:BATCH:FUSE | 1.393 | 1.373-1.413 | 0.6% |
| NT:BATCH:FUSE:SPLIT | 1.613 | 1.567-1.660 | 0.3% |
| NT:BATCH:SPLIT | 1.230 | 1.212-1.248 | 0.2% |
| NT:BATCH | 1.080 | 1.072-1.088 | 0.1% |
| NT:FUSE:SPLIT | 0.865 | 0.852-0.877 | 0.1% |
| FUSE:SPLIT | 0.957 | 0.951-0.964 | 0.0% |
| NT:FUSE | 0.971 | 0.964-0.978 | 0.0% |
| BATCH:SPLIT | 1.018 | 1.011-1.025 | 0.0% |
| BATCH:FUSE:SPLIT | 0.985 | 0.970-0.999 | 0.0% |

4 term(s) explain 90% of the explained variance: BATCH, BATCH:FUSE, NT, FUSE

NT simple effects (runtime ratio NT on / off, geometric mean over SPLIT and rounds):

| BATCH | FUSE | ratio |
|---|---|---|
| 0 | 0 | 0.662 |
| 0 | 1 | 0.544 |
| 1 | 0 | 0.606 |
| 1 | 1 | 0.694 |

DRAM traffic per cell (median read + write sweeps):

| NT | BATCH | FUSE | SPLIT | read S | write S | GF/s |
|---|---|---|---|---|---|---|
| 0 | 0 | 0 | 0 | 29.39 | nan | 5.93 |
| 0 | 0 | 0 | 1 | 30.74 | nan | 4.64 |
| 0 | 0 | 1 | 0 | 18.95 | nan | 2.35 |
| 0 | 0 | 1 | 1 | 26.27 | nan | 1.58 |
| 0 | 1 | 0 | 0 | 29.17 | nan | 6.60 |
| 0 | 1 | 0 | 1 | 30.16 | nan | 4.95 |
| 0 | 1 | 1 | 0 | 11.59 | nan | 8.78 |
| 0 | 1 | 1 | 1 | 15.14 | nan | 7.26 |
| 1 | 0 | 0 | 0 | 24.17 | nan | 7.87 |
| 1 | 0 | 0 | 1 | 24.33 | nan | 7.97 |
| 1 | 0 | 1 | 0 | 24.99 | nan | 3.13 |
| 1 | 0 | 1 | 1 | 26.62 | nan | 3.99 |
| 1 | 1 | 0 | 0 | 24.42 | nan | 9.43 |
| 1 | 1 | 0 | 1 | 24.60 | nan | 9.44 |
| 1 | 1 | 1 | 0 | 8.63 | nan | 11.45 |
| 1 | 1 | 1 | 1 | 7.97 | nan | 11.56 |

## n = 33554432  (all off -> all on: 2.38x faster; residual sd 0.019 in log t, 32 dof, R^2 = 0.9994)

| term | runtime ratio (main: on/off; interaction: ratio of ratios) | 95% CI | share of explained SS |
|---|---|---|---|
| BATCH | 0.465 | 0.460-0.470 | 37.9% |
| BATCH:FUSE | 0.260 | 0.254-0.266 | 29.3% |
| NT | 0.560 | 0.553-0.566 | 21.8% |
| FUSE | 1.476 | 1.459-1.493 | 9.8% |
| NT:BATCH:FUSE | 1.516 | 1.449-1.586 | 0.7% |
| NT:BATCH | 1.130 | 1.105-1.156 | 0.2% |
| SPLIT | 0.963 | 0.952-0.974 | 0.1% |
| FUSE:SPLIT | 0.958 | 0.936-0.980 | 0.0% |
| NT:FUSE | 0.961 | 0.939-0.983 | 0.0% |
| NT:SPLIT | 0.973 | 0.951-0.995 | 0.0% |
| NT:BATCH:FUSE:SPLIT | 1.114 | 1.018-1.220 | 0.0% |
| NT:BATCH:SPLIT | 1.050 | 1.003-1.098 | 0.0% |

4 term(s) explain 90% of the explained variance: BATCH, BATCH:FUSE, NT, FUSE

NT simple effects (runtime ratio NT on / off, geometric mean over SPLIT and rounds):

| BATCH | FUSE | ratio |
|---|---|---|
| 0 | 0 | 0.596 |
| 0 | 1 | 0.465 |
| 1 | 0 | 0.547 |
| 1 | 1 | 0.647 |

DRAM traffic per cell (median read + write sweeps):

| NT | BATCH | FUSE | SPLIT | read S | write S | GF/s |
|---|---|---|---|---|---|---|
| 0 | 0 | 0 | 0 | 29.99 | nan | 4.98 |
| 0 | 0 | 0 | 1 | 30.57 | nan | 4.94 |
| 0 | 0 | 1 | 0 | 23.01 | nan | 1.50 |
| 0 | 0 | 1 | 1 | 21.78 | nan | 1.53 |
| 0 | 1 | 0 | 0 | 29.04 | nan | 5.21 |
| 0 | 1 | 0 | 1 | 29.87 | nan | 5.22 |
| 0 | 1 | 1 | 0 | 12.88 | nan | 7.53 |
| 0 | 1 | 1 | 1 | 12.63 | nan | 7.83 |
| 1 | 0 | 0 | 0 | 22.83 | nan | 8.19 |
| 1 | 0 | 0 | 1 | 23.99 | nan | 8.46 |
| 1 | 0 | 1 | 0 | 25.04 | nan | 3.11 |
| 1 | 0 | 1 | 1 | 23.92 | nan | 3.41 |
| 1 | 1 | 0 | 0 | 22.72 | nan | 9.33 |
| 1 | 1 | 0 | 1 | 23.92 | nan | 9.73 |
| 1 | 1 | 1 | 0 | 7.96 | nan | 11.41 |
| 1 | 1 | 1 | 1 | 7.30 | nan | 11.87 |

## NT x strip width (fused, balanced split)

| n | Bc = G | GF/s NT off | GF/s NT on | NT ratio (on/off time) | write S off | write S on |
|---|---|---|---|---|---|---|
| 4194304 | 1 | 2.36 | 3.14 | 0.752 | nan | nan |
| 4194304 | 2 | 3.82 | 4.58 | 0.834 | nan | nan |
| 4194304 | 4 | 6.47 | 9.38 | 0.690 | nan | nan |
| 4194304 | 8 | 8.67 | 11.43 | 0.759 | nan | nan |
| 4194304 | 16 | 10.34 | 12.63 | 0.819 | nan | nan |
| 4194304 | 32 | 10.03 | 12.37 | 0.811 | nan | nan |
| 33554432 | 1 | 1.50 | 3.10 | 0.483 | nan | nan |
| 33554432 | 2 | 2.74 | 4.67 | 0.588 | nan | nan |
| 33554432 | 4 | 4.80 | 8.73 | 0.550 | nan | nan |
| 33554432 | 8 | 7.53 | 11.46 | 0.657 | nan | nan |
| 33554432 | 16 | 10.09 | 12.94 | 0.780 | nan | nan |
| 33554432 | 32 | 3.23 | 3.74 | 0.864 | nan | nan |
