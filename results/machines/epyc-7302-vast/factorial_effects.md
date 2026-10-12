# Full factorial ablation (2^4) on log runtime

## n = 262144  (all off -> all on: 1.44x faster; residual sd 0.010 in log t, 32 dof, R^2 = 0.9992)

| term | runtime ratio (main: on/off; interaction: ratio of ratios) | 95% CI | share of explained SS |
|---|---|---|---|
| BATCH:FUSE | 0.449 | 0.444-0.455 | 42.4% |
| BATCH | 0.702 | 0.698-0.706 | 33.2% |
| NT:SPLIT | 0.746 | 0.737-0.755 | 5.7% |
| BATCH:SPLIT | 0.747 | 0.737-0.756 | 5.7% |
| SPLIT | 1.141 | 1.135-1.149 | 4.6% |
| NT:FUSE | 1.234 | 1.219-1.249 | 2.9% |
| FUSE:SPLIT | 0.854 | 0.844-0.865 | 1.6% |
| NT:BATCH | 0.856 | 0.846-0.867 | 1.6% |
| NT | 0.933 | 0.927-0.938 | 1.3% |
| NT:BATCH:FUSE | 0.846 | 0.825-0.867 | 0.5% |
| BATCH:FUSE:SPLIT | 0.862 | 0.841-0.883 | 0.4% |
| NT:FUSE:SPLIT | 1.077 | 1.051-1.104 | 0.1% |
| FUSE | 0.986 | 0.980-0.993 | 0.0% |
| NT:BATCH:FUSE:SPLIT | 0.920 | 0.876-0.966 | 0.0% |

5 term(s) explain 90% of the explained variance: BATCH:FUSE, BATCH, NT:SPLIT, BATCH:SPLIT, SPLIT

NT simple effects (runtime ratio NT on / off, geometric mean over SPLIT and rounds):

| BATCH | FUSE | ratio |
|---|---|---|
| 0 | 0 | 0.870 |
| 0 | 1 | 1.168 |
| 1 | 0 | 0.810 |
| 1 | 1 | 0.919 |

## n = 1048576  (all off -> all on: 1.61x faster; residual sd 0.018 in log t, 32 dof, R^2 = 0.9986)

| term | runtime ratio (main: on/off; interaction: ratio of ratios) | 95% CI | share of explained SS |
|---|---|---|---|
| BATCH | 0.600 | 0.594-0.606 | 45.4% |
| BATCH:FUSE | 0.466 | 0.456-0.475 | 25.3% |
| NT | 0.741 | 0.734-0.749 | 15.5% |
| SPLIT | 1.238 | 1.225-1.251 | 7.9% |
| FUSE | 1.092 | 1.081-1.104 | 1.4% |
| NT:SPLIT | 0.851 | 0.833-0.869 | 1.1% |
| BATCH:SPLIT | 1.158 | 1.134-1.182 | 0.9% |
| NT:FUSE | 1.153 | 1.129-1.177 | 0.9% |
| FUSE:SPLIT | 0.883 | 0.865-0.901 | 0.7% |
| NT:BATCH | 0.912 | 0.894-0.931 | 0.4% |
| BATCH:FUSE:SPLIT | 1.171 | 1.123-1.221 | 0.3% |
| NT:BATCH:FUSE:SPLIT | 0.841 | 0.774-0.914 | 0.1% |
| NT:FUSE:SPLIT | 1.075 | 1.032-1.121 | 0.1% |
| NT:BATCH:FUSE | 0.941 | 0.903-0.981 | 0.0% |
| NT:BATCH:SPLIT | 0.945 | 0.907-0.985 | 0.0% |

4 term(s) explain 90% of the explained variance: BATCH, BATCH:FUSE, NT, SPLIT

NT simple effects (runtime ratio NT on / off, geometric mean over SPLIT and rounds):

| BATCH | FUSE | ratio |
|---|---|---|
| 0 | 0 | 0.712 |
| 0 | 1 | 0.846 |
| 1 | 0 | 0.670 |
| 1 | 1 | 0.749 |

## n = 4194304  (all off -> all on: 1.81x faster; residual sd 0.005 in log t, 32 dof, R^2 = 0.9999)

| term | runtime ratio (main: on/off; interaction: ratio of ratios) | 95% CI | share of explained SS |
|---|---|---|---|
| BATCH | 0.493 | 0.491-0.494 | 41.1% |
| BATCH:FUSE | 0.308 | 0.306-0.309 | 28.5% |
| NT | 0.645 | 0.643-0.647 | 15.8% |
| FUSE | 1.386 | 1.381-1.390 | 8.7% |
| NT:SPLIT | 0.675 | 0.670-0.679 | 3.2% |
| SPLIT | 1.131 | 1.127-1.134 | 1.2% |
| NT:BATCH:FUSE | 1.447 | 1.429-1.466 | 0.7% |
| NT:BATCH | 1.110 | 1.103-1.117 | 0.2% |
| NT:BATCH:FUSE:SPLIT | 1.507 | 1.469-1.546 | 0.2% |
| NT:BATCH:SPLIT | 1.191 | 1.176-1.207 | 0.2% |
| NT:FUSE:SPLIT | 0.887 | 0.876-0.898 | 0.1% |
| FUSE:SPLIT | 0.971 | 0.964-0.977 | 0.0% |
| BATCH:SPLIT | 1.012 | 1.006-1.019 | 0.0% |

4 term(s) explain 90% of the explained variance: BATCH, BATCH:FUSE, NT, FUSE

NT simple effects (runtime ratio NT on / off, geometric mean over SPLIT and rounds):

| BATCH | FUSE | ratio |
|---|---|---|
| 0 | 0 | 0.673 |
| 0 | 1 | 0.557 |
| 1 | 0 | 0.621 |
| 1 | 1 | 0.744 |

## n = 33554432  (all off -> all on: 2.30x faster; residual sd 0.013 in log t, 32 dof, R^2 = 0.9997)

| term | runtime ratio (main: on/off; interaction: ratio of ratios) | 95% CI | share of explained SS |
|---|---|---|---|
| BATCH | 0.462 | 0.459-0.466 | 37.7% |
| BATCH:FUSE | 0.251 | 0.247-0.255 | 30.3% |
| NT | 0.568 | 0.563-0.572 | 20.3% |
| FUSE | 1.500 | 1.489-1.512 | 10.4% |
| NT:BATCH:FUSE | 1.564 | 1.517-1.614 | 0.8% |
| NT:BATCH | 1.161 | 1.143-1.179 | 0.4% |
| SPLIT | 0.978 | 0.970-0.985 | 0.0% |
| NT:SPLIT | 0.966 | 0.951-0.981 | 0.0% |
| NT:FUSE | 1.019 | 1.003-1.035 | 0.0% |
| FUSE:SPLIT | 0.983 | 0.968-0.999 | 0.0% |

4 term(s) explain 90% of the explained variance: BATCH, BATCH:FUSE, NT, FUSE

NT simple effects (runtime ratio NT on / off, geometric mean over SPLIT and rounds):

| BATCH | FUSE | ratio |
|---|---|---|
| 0 | 0 | 0.584 |
| 0 | 1 | 0.476 |
| 1 | 0 | 0.542 |
| 1 | 1 | 0.691 |

## NT x strip width (fused, balanced split)

| n | Bc = G | GF/s NT off | GF/s NT on | NT ratio (on/off time) | write S off | write S on |
|---|---|---|---|---|---|---|
| 4194304 | 1 | 1.98 | 2.58 | 0.770 | 3.00 | 3.00 |
| 4194304 | 2 | 3.03 | 3.73 | 0.812 | 3.00 | 3.00 |
| 4194304 | 4 | 5.45 | 7.71 | 0.707 | 3.00 | 3.00 |
| 4194304 | 8 | 7.76 | 9.12 | 0.851 | 3.00 | 3.00 |
| 4194304 | 16 | 8.71 | 9.96 | 0.875 | 3.00 | 3.00 |
| 4194304 | 32 | 8.34 | 9.75 | 0.856 | 3.00 | 3.00 |
| 33554432 | 1 | 1.22 | 2.53 | 0.483 | 3.00 | 3.00 |
| 33554432 | 2 | 2.16 | 3.74 | 0.577 | 3.00 | 3.00 |
| 33554432 | 4 | 3.88 | 6.89 | 0.563 | 3.00 | 3.00 |
| 33554432 | 8 | 6.37 | 9.09 | 0.701 | 3.00 | 3.00 |
| 33554432 | 16 | 8.41 | 10.32 | 0.815 | 3.00 | 3.00 |
| 33554432 | 32 | 2.37 | 2.63 | 0.904 | 3.00 | 3.00 |
