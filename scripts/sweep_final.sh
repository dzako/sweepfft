#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-2.0-or-later
# Final comparison: pmfft (combined algorithm) vs MKL / FFTW / ducc, single P-core, 3 interleaved rounds.
set -e
CPU=${BENCH_CPU:-$(python3 "$(dirname "$0")/cpus.py" single)}; export BENCH_CPU=$CPU
cd "$(dirname "$0")/.."
scripts/build.sh > /dev/null
RB="uv run scripts/run_bench.py sweep"
P2=$(python3 -c "print(','.join(str(2**k) for k in range(4,27)))")
P2S=$(python3 -c "print(','.join(str(2**k) for k in range(4,21)))")
$RB --impl pmfft,mkl,fftw_measure,ducc --n $P2 --rounds 3 --mintime 0.3 --check --out results/final_pow2.csv
$RB --impl fftw_patient --n $P2S --rounds 3 --mintime 0.3 --out results/final_pow2_patient.csv
SM=1000,3000,10000,100000,1000000,3145728,6553600,10000000
$RB --impl pmfft,mkl,fftw_measure,ducc --n $SM --rounds 3 --mintime 0.3 --check --out results/final_smooth.csv
PR=1009,10007,100003,1000003,4000037
$RB --impl pmfft,mkl,fftw_measure,ducc --n $PR --rounds 3 --mintime 0.3 --check --out results/final_prime.csv
$RB --impl pmfft --grid "fast=1" --n $PR --rounds 3 --mintime 0.3 --check --out results/final_prime_fast.csv
echo FINAL DONE
