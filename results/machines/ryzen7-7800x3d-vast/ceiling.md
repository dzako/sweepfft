# Movement and compute ceilings of the two-pass plan (`scripts/ceiling.py`)

Median time per transform (ms) over 3 rounds. S = 16n bytes; the two-pass ideal moves 4 S. GB/s columns = 4 S / time. move/ideal: cost of the plan's strided access pattern over sequential streaming; compute/full: arithmetic share; (move+compute)/full > 1 means the two overlap.

| plan | caller pages | n | full | move+tw | move | compute | ideal | full GB/s | move GB/s | ideal GB/s | full/ideal | move/ideal | compute/full | (move+compute)/full |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| rec4 | huge | 2^22 | 27.5 | 13.9 | 12.5 | 13.3 | 5.2 | 9.8 | 21.5 | 51.6 | 5.28 | 2.40 | 0.49 | 0.94 |
| rec4 | huge | 2^24 | 142.8 | 76.4 | 71.5 | 66.9 | 22.1 | 7.5 | 15.0 | 48.5 | 6.45 | 3.23 | 0.47 | 0.97 |
| rec4 | huge | 2^25 | 285.3 | 157.3 | 145.3 | 130.8 | 44.9 | 7.5 | 14.8 | 47.8 | 6.36 | 3.24 | 0.46 | 0.97 |
| rec4 | huge | 2^26 | 658.8 | 398.3 | 376.8 | 262.2 | 90.7 | 6.5 | 11.4 | 47.4 | 7.27 | 4.16 | 0.40 | 0.97 |
| rec4 | plain | 2^22 | 28.6 | 15.0 | 13.7 | 13.3 | 5.4 | 9.4 | 19.6 | 49.7 | 5.30 | 2.54 | 0.46 | 0.94 |
| rec4 | plain | 2^24 | 135.8 | 69.8 | 63.0 | 65.6 | 22.9 | 7.9 | 17.0 | 46.9 | 5.93 | 2.75 | 0.48 | 0.95 |
| rec4 | plain | 2^25 | 269.3 | 142.1 | 127.8 | 130.9 | 46.3 | 8.0 | 16.8 | 46.4 | 5.82 | 2.76 | 0.49 | 0.96 |
| rec4 | plain | 2^26 | 540.8 | 286.7 | 263.6 | 260.2 | 93.0 | 7.9 | 16.3 | 46.2 | 5.81 | 2.83 | 0.48 | 0.97 |
| staged | huge | 2^24 | 129.1 | 70.0 | 66.3 | 59.0 | 22.1 | 8.3 | 16.2 | 48.5 | 5.83 | 3.00 | 0.46 | 0.97 |
| staged | huge | 2^25 | 276.9 | 142.5 | 133.8 | 130.8 | 44.9 | 7.8 | 16.1 | 47.8 | 6.17 | 2.98 | 0.47 | 0.96 |
| staged | huge | 2^26 | 587.6 | 293.5 | 274.8 | 285.9 | 90.7 | 7.3 | 15.6 | 47.4 | 6.48 | 3.03 | 0.49 | 0.95 |
| staged | plain | 2^24 | 130.2 | 71.3 | 67.7 | 58.4 | 22.9 | 8.2 | 15.9 | 46.9 | 5.68 | 2.95 | 0.45 | 0.97 |
| staged | plain | 2^25 | 280.3 | 145.9 | 137.9 | 130.6 | 46.3 | 7.7 | 15.6 | 46.4 | 6.05 | 2.98 | 0.47 | 0.96 |
| staged | plain | 2^26 | 588.3 | 300.0 | 279.5 | 285.3 | 93.0 | 7.3 | 15.4 | 46.2 | 6.32 | 3.00 | 0.49 | 0.96 |
