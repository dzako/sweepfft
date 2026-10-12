# Movement and compute ceilings of the two-pass plan (`scripts/ceiling.py`)

Median time per transform (ms) over 3 rounds. S = 16n bytes; the two-pass ideal moves 4 S. GB/s columns = 4 S / time. move/ideal: cost of the plan's strided access pattern over sequential streaming; compute/full: arithmetic share; (move+compute)/full > 1 means the two overlap.

| plan | caller pages | n | full | move+tw | move | compute | ideal | full GB/s | move GB/s | ideal GB/s | full/ideal | move/ideal | compute/full | (move+compute)/full |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| rec4 | huge | 2^22 | 40.3 | 22.6 | 19.3 | 17.7 | 7.7 | 6.7 | 13.9 | 34.9 | 5.24 | 2.51 | 0.44 | 0.92 |
| rec4 | huge | 2^24 | 183.1 | 100.6 | 83.5 | 82.5 | 30.8 | 5.9 | 12.9 | 34.9 | 5.95 | 2.71 | 0.45 | 0.91 |
| rec4 | huge | 2^25 | 369.1 | 201.1 | 167.0 | 165.5 | 61.1 | 5.8 | 12.9 | 35.1 | 6.04 | 2.73 | 0.45 | 0.90 |
| rec4 | huge | 2^26 | 745.3 | 402.5 | 333.4 | 335.9 | 121.6 | 5.8 | 12.9 | 35.3 | 6.13 | 2.74 | 0.45 | 0.90 |
| rec4 | plain | 2^22 | 40.7 | 23.2 | 19.8 | 17.5 | 8.4 | 6.6 | 13.6 | 31.8 | 4.81 | 2.34 | 0.43 | 0.92 |
| rec4 | plain | 2^24 | 182.0 | 98.1 | 83.6 | 82.7 | 33.5 | 5.9 | 12.8 | 32.1 | 5.43 | 2.49 | 0.45 | 0.91 |
| rec4 | plain | 2^25 | 382.2 | 206.4 | 173.3 | 166.3 | 65.7 | 5.6 | 12.4 | 32.7 | 5.81 | 2.64 | 0.44 | 0.89 |
| rec4 | plain | 2^26 | 778.5 | 421.8 | 357.5 | 351.7 | 133.1 | 5.5 | 12.0 | 32.3 | 5.85 | 2.69 | 0.45 | 0.91 |
| staged | huge | 2^24 | 170.4 | 92.1 | 77.2 | 77.6 | 30.8 | 6.3 | 13.9 | 34.9 | 5.54 | 2.51 | 0.46 | 0.91 |
| staged | huge | 2^25 | 357.4 | 184.6 | 151.0 | 174.9 | 61.1 | 6.0 | 14.2 | 35.1 | 5.85 | 2.47 | 0.49 | 0.91 |
| staged | huge | 2^26 | 732.1 | 365.5 | 297.0 | 402.1 | 121.6 | 5.9 | 14.5 | 35.3 | 6.02 | 2.44 | 0.55 | 0.95 |
| staged | plain | 2^24 | 178.6 | 98.5 | 83.3 | 76.9 | 33.5 | 6.0 | 12.9 | 32.1 | 5.33 | 2.49 | 0.43 | 0.90 |
| staged | plain | 2^25 | 389.4 | 207.8 | 172.8 | 172.6 | 65.7 | 5.5 | 12.4 | 32.7 | 5.92 | 2.63 | 0.44 | 0.89 |
| staged | plain | 2^26 | 1053.2 | 424.7 | 350.9 | 383.3 | 133.1 | 4.1 | 12.2 | 32.3 | 7.91 | 2.64 | 0.36 | 0.70 |
