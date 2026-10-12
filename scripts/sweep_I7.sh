#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-2.0-or-later
# I7 / Toeplitz T4: arbitrary (prime) length DFT strategies.
set -e
CPU=${BENCH_CPU:-$(python3 "$(dirname "$0")/cpus.py" single)}; export BENCH_CPU=$CPU
cd "$(dirname "$0")/.."
P=1009,10007,100003,1000003,4000037,16000057
uv run scripts/run_bench.py sweep --impl gauss --grid "L=4,5.5,7,9;delta=0.25,0.4,0.6;iters=0,1,2,4" --n $P --rounds 2 --check --mintime 0.2 --out results/abl_I7_gauss.csv
uv run scripts/run_bench.py sweep --impl bluestein,rader --grid "pow2=0,1" --n $P --rounds 2 --check --mintime 0.2 --out results/abl_I7_blurad.csv
uv run scripts/run_bench.py sweep --impl fftw_measure,mkl,ducc --n $P --rounds 2 --check --mintime 0.2 --out results/abl_I7_ext.csv
