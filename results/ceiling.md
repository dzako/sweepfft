# Movement and compute ceilings of the two-pass plan (`scripts/ceiling.py`)

Median time per transform (ms) over 3 rounds. S = 16n bytes; the two-pass ideal moves 4 S. GB/s columns = 4 S / time. move/ideal: cost of the plan's strided access pattern over sequential streaming; compute/full: arithmetic share; (move+compute)/full > 1 means the two overlap.

| plan | caller pages | n | full | move+tw | move | compute | ideal | full GB/s | move GB/s | ideal GB/s | full/ideal | move/ideal | compute/full | (move+compute)/full |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| rec4 | huge | 2^22 | 28.6 | 14.8 | 12.8 | 12.8 | 7.2 | 9.4 | 21.0 | 37.4 | 3.99 | 1.78 | 0.45 | 0.89 |
| rec4 | huge | 2^24 | 117.8 | 60.1 | 49.8 | 60.2 | 30.5 | 9.1 | 21.6 | 35.2 | 3.86 | 1.63 | 0.51 | 0.93 |
| rec4 | huge | 2^25 | 275.2 | 129.9 | 101.8 | 143.0 | 58.6 | 7.8 | 21.1 | 36.7 | 4.70 | 1.74 | 0.52 | 0.89 |
| rec4 | huge | 2^26 | 669.8 | 281.5 | 224.8 | 367.2 | 117.8 | 6.4 | 19.1 | 36.5 | 5.68 | 1.91 | 0.55 | 0.88 |
| rec4 | plain | 2^22 | 28.9 | 13.4 | 12.0 | 12.7 | 7.4 | 9.3 | 22.3 | 36.2 | 3.89 | 1.62 | 0.44 | 0.86 |
| rec4 | plain | 2^24 | 123.3 | 62.3 | 49.6 | 55.6 | 29.6 | 8.7 | 21.7 | 36.2 | 4.16 | 1.67 | 0.45 | 0.85 |
| rec4 | plain | 2^25 | 292.2 | 140.5 | 117.6 | 145.5 | 59.5 | 7.4 | 18.3 | 36.1 | 4.91 | 1.98 | 0.50 | 0.90 |
| rec4 | plain | 2^26 | 697.7 | 302.8 | 266.5 | 365.5 | 117.8 | 6.2 | 16.1 | 36.5 | 5.92 | 2.26 | 0.52 | 0.91 |
| staged | huge | 2^24 | 124.3 | 61.4 | 48.9 | 60.7 | 30.5 | 8.6 | 22.0 | 35.2 | 4.07 | 1.60 | 0.49 | 0.88 |
| staged | huge | 2^25 | 273.4 | 123.6 | 105.2 | 150.6 | 58.6 | 7.9 | 20.4 | 36.7 | 4.67 | 1.80 | 0.55 | 0.94 |
| staged | huge | 2^26 | 587.1 | 266.9 | 233.4 | 326.4 | 117.8 | 7.3 | 18.4 | 36.5 | 4.98 | 1.98 | 0.56 | 0.95 |
| staged | plain | 2^24 | 134.7 | 62.9 | 56.6 | 61.5 | 29.6 | 8.0 | 19.0 | 36.2 | 4.54 | 1.91 | 0.46 | 0.88 |
| staged | plain | 2^25 | 290.2 | 135.3 | 122.6 | 147.7 | 59.5 | 7.4 | 17.5 | 36.1 | 4.88 | 2.06 | 0.51 | 0.93 |
| staged | plain | 2^26 | 627.7 | 276.8 | 237.5 | 305.9 | 117.8 | 6.8 | 18.1 | 36.5 | 5.33 | 2.02 | 0.49 | 0.87 |
