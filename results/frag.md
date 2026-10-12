# Physical layout of ordinary caller arrays (`scripts/frag.py`)

Median over 3 rounds; caller arrays allocated the ordinary way (4 KB pages). States: as-is = the machine's current free memory; contig = small free blocks held, arrays split from large contiguous blocks; frag = arrays get scattered pages.

| state | free memory in blocks < 2 MB (MB) | strided gather, 128 B x 2048 rows (GB/s) |
|---|---|---|
| as-is | 3287 | 17.5 |
| contig | 697 | 9.9 |
| frag | 4648 | 17.8 |

GFlop/s and SweepFFT speedup per state:

| n | impl | as-is | contig | frag | speedup as-is | speedup contig | speedup frag |
|---|---|---|---|---|---|---|---|
| 2^22 | SweepFFT | 17.76 | 16.73 | 17.88 | – | – | – |
| 2^22 | MKL | 18.22 | 17.11 | 18.30 | 0.97 | 0.98 | 0.98 |
| 2^22 | FFTW | 16.57 | 12.68 | 16.63 | 1.07 | 1.32 | 1.07 |
| 2^22 | ducc0 | 10.46 | 8.50 | 10.66 | 1.70 | 1.97 | 1.68 |
| 2^24 | SweepFFT | 16.50 | 16.26 | 17.02 | – | – | – |
| 2^24 | MKL | 16.26 | 13.64 | 16.42 | 1.01 | 1.19 | 1.04 |
| 2^24 | FFTW | 15.47 | 11.02 | 15.98 | 1.07 | 1.48 | 1.07 |
| 2^24 | ducc0 | 8.96 | 7.94 | 10.08 | 1.84 | 2.05 | 1.69 |
