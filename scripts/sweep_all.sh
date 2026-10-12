#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-2.0-or-later
# Remaining ablations (run after sweep_I7.sh). One-factor-at-a-time around the rec4 base config.
set -e
CPU=${BENCH_CPU:-$(python3 "$(dirname "$0")/cpus.py" single)}; export BENCH_CPU=$CPU
cd "$(dirname "$0")/.."
RB="uv run scripts/run_bench.py sweep"
S=2^14,2^16,2^18,2^20,2^22,2^24,2^26
BASE="budget=131072;Bc=8;G=8;split=0;nt=1;pad=4;rmax=16"
ofat() { # $1=name $2=factor-grid (replaces that key in BASE)
  local key=${2%%=*}; local g=$(echo "$BASE" | tr ';' '\n' | grep -v "^$key=" | tr '\n' ';')"$2"
  $RB --impl rec4 --grid "$g" --n $S --rounds 3 --mintime 0.3 --out results/abl_rec4_$1.csv
}
ofat I3_batch "Bc=1,2,8,32"
ofat I4_split "split=0,1,2"
ofat I5_budget "budget=4096,16384,131072,1048576"
ofat nt "nt=0,1"
ofat pad "pad=0,4"
ofat leafradix "rmax=8,16"
# I1: explicit transposes (six-step) vs fused (rec4) vs flat Stockham, all baselines
$RB --impl sixstep --grid "nt=0,1" --n $S --rounds 3 --mintime 0.3 --out results/abl_I1_sixstep.csv
$RB --impl stockham --grid "rmax=8" --n $S --rounds 3 --mintime 0.3 --out results/abl_I1_stockham.csv
$RB --impl fftw_measure,mkl,ducc --n $S --rounds 3 --mintime 0.3 --out results/base_pow2_ext.csv
taskset -c $CPU build/bench_transpose > results/abl_I1toy_I14_transpose.csv
# I9 convolution
echo "variant,n,t_med_ns,rel_err,round" > results/abl_I9_conv.csv
for r in 1 2 3; do for k in 16 18 20 22 24; do taskset -c $CPU build/bench_conv $((1<<k)) 0.5 | sed "s/$/,$r/" >> results/abl_I9_conv.csv; done; done
# I8 2-D
echo "variant,N,t_med_ns,mflops,rel_err,round" > results/abl_I8_2d.csv
for r in 1 2 3; do for N in 64 128 256 512 1024 2048; do taskset -c $CPU build/bench_2d $N 0.3 | sed "s/$/,$r/" >> results/abl_I8_2d.csv; done; done
# I15 PFA vs mixed radix
SM=1536,26880,82944,512000,1720320,6635520
$RB --impl pfa,stockham,rec4,fftw_measure,mkl,ducc --n $SM --rounds 3 --mintime 0.3 --check --out results/abl_I15_pfa.csv
echo ALL DONE
