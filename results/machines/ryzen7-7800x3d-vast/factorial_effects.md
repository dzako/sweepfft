# Full factorial ablation (2^4) on log runtime

## n = 262144  (all off -> all on: 1.02x faster; residual sd 0.047 in log t, 32 dof, R^2 = 0.9929)

| term | runtime ratio (main: on/off; interaction: ratio of ratios) | 95% CI | share of explained SS |
|---|---|---|---|
| BATCH:FUSE | 0.348 | 0.329-0.367 | 34.1% |
| BATCH | 0.602 | 0.585-0.619 | 31.5% |
| NT | 1.478 | 1.437-1.519 | 18.6% |
| FUSE | 1.275 | 1.240-1.310 | 7.2% |
| BATCH:SPLIT | 0.754 | 0.713-0.797 | 2.4% |
| NT:BATCH | 0.798 | 0.755-0.843 | 1.6% |
| NT:BATCH:FUSE | 0.656 | 0.588-0.733 | 1.4% |
| FUSE:SPLIT | 0.818 | 0.774-0.865 | 1.2% |
| SPLIT | 0.916 | 0.891-0.941 | 0.9% |
| NT:FUSE | 1.114 | 1.054-1.177 | 0.4% |
| NT:SPLIT | 1.098 | 1.039-1.161 | 0.3% |
| NT:BATCH:FUSE:SPLIT | 0.702 | 0.563-0.876 | 0.2% |

4 term(s) explain 90% of the explained variance: BATCH:FUSE, BATCH, NT, FUSE

NT simple effects (runtime ratio NT on / off, geometric mean over SPLIT and rounds):

| BATCH | FUSE | ratio |
|---|---|---|
| 0 | 0 | 1.410 |
| 0 | 1 | 1.940 |
| 1 | 0 | 1.389 |
| 1 | 1 | 1.254 |

## n = 1048576  (all off -> all on: 1.18x faster; residual sd 0.043 in log t, 32 dof, R^2 = 0.9947)

| term | runtime ratio (main: on/off; interaction: ratio of ratios) | 95% CI | share of explained SS |
|---|---|---|---|
| BATCH | 0.513 | 0.500-0.526 | 48.1% |
| BATCH:FUSE | 0.341 | 0.324-0.359 | 31.1% |
| NT | 1.423 | 1.387-1.459 | 13.4% |
| FUSE | 1.164 | 1.135-1.194 | 2.5% |
| NT:BATCH | 0.785 | 0.746-0.826 | 1.6% |
| NT:BATCH:FUSE | 0.650 | 0.588-0.720 | 1.2% |
| NT:FUSE | 1.168 | 1.110-1.228 | 0.6% |
| BATCH:SPLIT | 1.165 | 1.108-1.226 | 0.6% |
| SPLIT | 1.054 | 1.028-1.081 | 0.3% |
| BATCH:FUSE:SPLIT | 1.182 | 1.068-1.307 | 0.2% |
| FUSE:SPLIT | 0.920 | 0.875-0.968 | 0.2% |
| NT:SPLIT | 1.054 | 1.003-1.109 | 0.1% |

3 term(s) explain 90% of the explained variance: BATCH, BATCH:FUSE, NT

NT simple effects (runtime ratio NT on / off, geometric mean over SPLIT and rounds):

| BATCH | FUSE | ratio |
|---|---|---|
| 0 | 0 | 1.335 |
| 0 | 1 | 1.933 |
| 1 | 0 | 1.299 |
| 1 | 1 | 1.223 |

## n = 4194304  (all off -> all on: 1.84x faster; residual sd 0.011 in log t, 32 dof, R^2 = 0.9995)

| term | runtime ratio (main: on/off; interaction: ratio of ratios) | 95% CI | share of explained SS |
|---|---|---|---|
| BATCH | 0.572 | 0.568-0.576 | 49.6% |
| BATCH:FUSE | 0.396 | 0.391-0.401 | 34.1% |
| FUSE | 1.209 | 1.201-1.216 | 5.7% |
| NT:BATCH | 0.740 | 0.731-0.749 | 3.6% |
| NT:BATCH:FUSE | 0.561 | 0.547-0.576 | 3.3% |
| NT:FUSE | 1.220 | 1.205-1.236 | 1.6% |
| NT | 0.910 | 0.904-0.916 | 1.4% |
| BATCH:SPLIT | 1.094 | 1.080-1.107 | 0.3% |
| NT:FUSE:SPLIT | 1.147 | 1.119-1.176 | 0.2% |
| SPLIT | 0.980 | 0.974-0.986 | 0.1% |
| NT:SPLIT | 1.032 | 1.019-1.045 | 0.0% |
| NT:BATCH:SPLIT | 0.971 | 0.947-0.995 | 0.0% |

4 term(s) explain 90% of the explained variance: BATCH, BATCH:FUSE, FUSE, NT:BATCH

NT simple effects (runtime ratio NT on / off, geometric mean over SPLIT and rounds):

| BATCH | FUSE | ratio |
|---|---|---|
| 0 | 0 | 0.829 |
| 0 | 1 | 1.350 |
| 1 | 0 | 0.818 |
| 1 | 1 | 0.748 |

## n = 33554432  (all off -> all on: 1.95x faster; residual sd 0.040 in log t, 32 dof, R^2 = 0.9926)

| term | runtime ratio (main: on/off; interaction: ratio of ratios) | 95% CI | share of explained SS |
|---|---|---|---|
| BATCH | 0.591 | 0.577-0.605 | 47.0% |
| BATCH:FUSE | 0.436 | 0.415-0.457 | 29.4% |
| FUSE | 1.232 | 1.203-1.262 | 7.4% |
| NT | 0.849 | 0.829-0.870 | 4.5% |
| NT:BATCH | 0.740 | 0.706-0.776 | 3.8% |
| NT:FUSE | 1.284 | 1.225-1.347 | 2.7% |
| NT:BATCH:FUSE | 0.614 | 0.558-0.675 | 2.5% |
| SPLIT | 0.906 | 0.884-0.927 | 1.7% |
| BATCH:SPLIT | 1.106 | 1.055-1.160 | 0.4% |
| NT:BATCH:FUSE:SPLIT | 0.778 | 0.643-0.941 | 0.2% |
| BATCH:FUSE:SPLIT | 1.115 | 1.014-1.226 | 0.1% |

5 term(s) explain 90% of the explained variance: BATCH, BATCH:FUSE, FUSE, NT, NT:BATCH

NT simple effects (runtime ratio NT on / off, geometric mean over SPLIT and rounds):

| BATCH | FUSE | ratio |
|---|---|---|
| 0 | 0 | 0.771 |
| 0 | 1 | 1.264 |
| 1 | 0 | 0.728 |
| 1 | 1 | 0.733 |

## NT x strip width (fused, balanced split)

| n | Bc = G | GF/s NT off | GF/s NT on | NT ratio (on/off time) | write S off | write S on |
|---|---|---|---|---|---|---|
| 4194304 | 1 | 5.57 | 4.38 | 1.272 | 3.00 | 3.00 |
| 4194304 | 2 | 7.13 | 7.28 | 0.979 | 3.00 | 3.00 |
| 4194304 | 4 | 11.77 | 14.54 | 0.809 | 3.00 | 3.00 |
| 4194304 | 8 | 12.21 | 16.62 | 0.734 | 3.00 | 3.00 |
| 4194304 | 16 | 15.20 | 17.65 | 0.862 | 3.00 | 3.00 |
| 4194304 | 32 | 14.14 | 17.41 | 0.812 | 3.00 | 3.00 |
| 33554432 | 1 | 4.95 | 4.27 | 1.159 | 3.00 | 3.00 |
| 33554432 | 2 | 6.55 | 6.92 | 0.946 | 3.00 | 3.00 |
| 33554432 | 4 | 9.17 | 12.09 | 0.759 | 3.00 | 3.00 |
| 33554432 | 8 | 11.03 | 14.72 | 0.750 | 3.00 | 3.00 |
| 33554432 | 16 | 14.15 | 16.34 | 0.866 | 3.00 | 3.00 |
| 33554432 | 32 | 11.40 | 13.30 | 0.857 | 3.00 | 3.00 |
