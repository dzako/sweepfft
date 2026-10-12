# Movement and compute ceilings of the two-pass plan (`scripts/ceiling.py`)

Median time per transform (ms) over 3 rounds. S = 16n bytes; the two-pass ideal moves 4 S. GB/s columns = 4 S / time. move/ideal: cost of the plan's strided access pattern over sequential streaming; compute/full: arithmetic share; (move+compute)/full > 1 means the two overlap.

| plan | caller pages | n | full | move+tw | move | compute | ideal | full GB/s | move GB/s | ideal GB/s | full/ideal | move/ideal | compute/full | (move+compute)/full |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| rec4 | huge | 2^22 | 51.5 | 28.1 | 23.5 | 22.9 | 9.0 | 5.2 | 11.4 | 29.9 | 5.74 | 2.62 | 0.45 | 0.90 |
| rec4 | huge | 2^24 | 230.9 | 123.7 | 99.3 | 112.1 | 35.9 | 4.6 | 10.8 | 29.9 | 6.43 | 2.77 | 0.49 | 0.92 |
| rec4 | huge | 2^25 | 475.4 | 246.3 | 200.8 | 215.8 | 71.8 | 4.5 | 10.7 | 29.9 | 6.62 | 2.80 | 0.45 | 0.88 |
| rec4 | huge | 2^26 | 948.4 | 497.6 | 404.6 | 459.3 | 143.4 | 4.5 | 10.6 | 30.0 | 6.61 | 2.82 | 0.48 | 0.91 |
| rec4 | plain | 2^22 | 51.6 | 28.6 | 23.7 | 24.2 | 10.3 | 5.2 | 11.3 | 25.9 | 4.98 | 2.29 | 0.47 | 0.93 |
| rec4 | plain | 2^24 | 300.2 | 122.3 | 103.2 | 118.3 | 41.4 | 3.6 | 10.4 | 26.0 | 7.26 | 2.49 | 0.39 | 0.74 |
| rec4 | plain | 2^25 | 1482.2 | 251.8 | 207.6 | 288.3 | 82.2 | 1.4 | 10.3 | 26.1 | 18.04 | 2.53 | 0.19 | 0.33 |
| rec4 | plain | 2^26 | 1637.9 | 515.4 | 430.3 | 549.8 | 164.5 | 2.6 | 10.0 | 26.1 | 9.96 | 2.62 | 0.34 | 0.60 |
| staged | huge | 2^24 | 216.0 | 109.7 | 89.5 | 108.6 | 35.9 | 5.0 | 12.0 | 29.9 | 6.02 | 2.49 | 0.50 | 0.92 |
| staged | huge | 2^25 | 440.2 | 219.4 | 174.6 | 233.1 | 71.8 | 4.9 | 12.3 | 29.9 | 6.13 | 2.43 | 0.53 | 0.93 |
| staged | huge | 2^26 | 918.3 | 432.2 | 342.6 | 498.7 | 143.4 | 4.7 | 12.5 | 30.0 | 6.40 | 2.39 | 0.54 | 0.92 |
| staged | plain | 2^24 | 224.2 | 118.6 | 97.8 | 103.4 | 41.4 | 4.8 | 11.0 | 26.0 | 5.42 | 2.36 | 0.46 | 0.90 |
| staged | plain | 2^25 | 888.1 | 244.9 | 198.7 | 321.0 | 82.2 | 2.4 | 10.8 | 26.1 | 10.81 | 2.42 | 0.36 | 0.59 |
| staged | plain | 2^26 | 1583.6 | 494.3 | 397.8 | 670.1 | 164.5 | 2.7 | 10.8 | 26.1 | 9.63 | 2.42 | 0.42 | 0.67 |
