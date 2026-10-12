# Movement and compute ceilings of the two-pass plan (`scripts/ceiling.py`)

Median time per transform (ms) over 3 rounds. S = 16n bytes; the two-pass ideal moves 4 S. GB/s columns = 4 S / time. move/ideal: cost of the plan's strided access pattern over sequential streaming; compute/full: arithmetic share; (move+compute)/full > 1 means the two overlap.

| plan | caller pages | n | full | move+tw | move | compute | ideal | full GB/s | move GB/s | ideal GB/s | full/ideal | move/ideal | compute/full | (move+compute)/full |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| rec4 | huge | 2^22 | 61.7 | 36.2 | 35.0 | 23.7 | 24.5 | 4.3 | 7.7 | 11.0 | 2.52 | 1.43 | 0.38 | 0.95 |
| rec4 | huge | 2^24 | 279.8 | 155.6 | 149.0 | 117.4 | 98.9 | 3.8 | 7.2 | 10.9 | 2.83 | 1.51 | 0.42 | 0.95 |
| rec4 | huge | 2^25 | 657.5 | 320.2 | 302.7 | 318.5 | 198.6 | 3.3 | 7.1 | 10.8 | 3.31 | 1.52 | 0.48 | 0.94 |
| rec4 | huge | 2^26 | 1552.9 | 722.0 | 680.8 | 869.5 | 398.0 | 2.8 | 6.3 | 10.8 | 3.90 | 1.71 | 0.56 | 1.00 |
| rec4 | plain | 2^22 | 69.8 | 43.9 | 43.1 | 23.8 | 25.8 | 3.8 | 6.2 | 10.4 | 2.70 | 1.67 | 0.34 | 0.96 |
| rec4 | plain | 2^24 | 302.1 | 174.9 | 159.6 | 126.8 | 104.5 | 3.6 | 6.7 | 10.3 | 2.89 | 1.53 | 0.42 | 0.95 |
| rec4 | plain | 2^25 | 710.2 | 383.2 | 347.1 | 340.4 | 209.6 | 3.0 | 6.2 | 10.2 | 3.39 | 1.66 | 0.48 | 0.97 |
| rec4 | plain | 2^26 | 1816.4 | 902.6 | 865.8 | 890.4 | 419.6 | 2.4 | 5.0 | 10.2 | 4.33 | 2.06 | 0.49 | 0.97 |
| staged | huge | 2^24 | 285.6 | 153.0 | 146.7 | 122.3 | 98.9 | 3.8 | 7.3 | 10.9 | 2.89 | 1.48 | 0.43 | 0.94 |
| staged | huge | 2^25 | 645.6 | 332.8 | 318.7 | 315.1 | 198.6 | 3.3 | 6.7 | 10.8 | 3.25 | 1.60 | 0.49 | 0.98 |
| staged | huge | 2^26 | 1339.8 | 671.5 | 645.6 | 654.2 | 398.0 | 3.2 | 6.7 | 10.8 | 3.37 | 1.62 | 0.49 | 0.97 |
| staged | plain | 2^24 | 302.6 | 163.9 | 157.7 | 126.1 | 104.5 | 3.5 | 6.8 | 10.3 | 2.90 | 1.51 | 0.42 | 0.94 |
| staged | plain | 2^25 | 692.0 | 351.9 | 339.1 | 334.1 | 209.6 | 3.1 | 6.3 | 10.2 | 3.30 | 1.62 | 0.48 | 0.97 |
| staged | plain | 2^26 | 1423.6 | 707.4 | 681.5 | 685.7 | 419.6 | 3.0 | 6.3 | 10.2 | 3.39 | 1.62 | 0.48 | 0.96 |
