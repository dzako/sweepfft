#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-2.0-or-later
# Full experiment, clean run: every ablation + final comparison + Toeplitz tests + analysis.
# Timed runs are pinned to one core ($BENCH_CPU, default from scripts/cpus.py); stages run strictly sequentially (no concurrent load).
CPU=${BENCH_CPU:-$(python3 "$(dirname "$0")/cpus.py" single)}; export BENCH_CPU=$CPU
cd "$(dirname "$0")/.."
LOG=results/run_all.log
stage() { echo "=== $(date +%T) START $1" | tee -a $LOG; }
done_() { echo "=== $(date +%T) END   $1 (rc=$2)" | tee -a $LOG; }
run() { local name=$1; shift; stage "$name"; "$@" >> results/logs/$name.log 2>&1; done_ "$name" $?; }

mkdir -p results/logs
scripts/build.sh > results/logs/build.log 2>&1 || { echo "BUILD FAILED" | tee -a $LOG; exit 1; }
build/test_stockham >> results/logs/build.log 2>&1
RB="uv run scripts/run_bench.py sweep"
S=2^14,2^16,2^18,2^20,2^22,2^24,2^26
P=1009,10007,100003,1000003,4000037,16000057
SM=1536,26880,82944,512000,1720320,6635520

# ---- I2 / I10 / I6: Stockham radix x codelet variant ----
run I2_I10 $RB --impl stockham --grid "rmax=2,4,8,16,32;mode=0,1,2" --n 2^6,2^8,2^10,2^12,2^14,2^16,2^18,2^20,2^22 --mintime 0.2 --rounds 3 --check --out results/abl_I2_I10.csv

# ---- I7 / T4: prime lengths ----
run I7_gauss $RB --impl gauss --grid "L=2,3,4,5.5,7;delta=0.25,0.4,0.6;iters=0,1,2,4" --n $P --rounds 2 --check --mintime 0.2 --out results/abl_I7_gauss.csv
run I7_blurad $RB --impl bluestein,rader --grid "pow2=0,1" --n $P --rounds 2 --check --mintime 0.2 --out results/abl_I7_blurad.csv
run I7_ext $RB --impl fftw_measure,mkl,ducc --n $P --rounds 2 --check --mintime 0.2 --out results/abl_I7_ext.csv

# ---- rec4 one-factor-at-a-time (I3, I4, I5, NT stores, padding, leaf radix) ----
BASE="budget=131072;Bc=8;G=8;split=0;nt=1;pad=4;rmax=16"
ofat() {
  local key=${2%%=*}; local g=$(echo "$BASE" | tr ';' '\n' | grep -v "^$key=" | tr '\n' ';')"$2"
  run rec4_$1 $RB --impl rec4 --grid "$g" --n $S --rounds 3 --mintime 0.3 --out results/abl_rec4_$1.csv
}
ofat I3_batch "Bc=1,2,8,32"
ofat I4_split "split=0,1,2"
ofat I5_budget "budget=4096,16384,131072,1048576"
ofat nt "nt=0,1"
ofat pad "pad=0,4"
ofat leafradix "rmax=8,16"

# ---- I1: explicit transposes vs fused; flat Stockham; external baselines; transposes / I14 ----
run I1_sixstep $RB --impl sixstep --grid "nt=0,1" --n $S --rounds 3 --mintime 0.3 --out results/abl_I1_sixstep.csv
run I1_stockham $RB --impl stockham --grid "rmax=8" --n $S --rounds 3 --mintime 0.3 --out results/abl_I1_stockham.csv
run base_ext $RB --impl fftw_measure,mkl,ducc --n $S --rounds 3 --mintime 0.3 --out results/base_pow2_ext.csv
stage transpose; taskset -c $CPU build/bench_transpose > results/abl_I1toy_I14_transpose.csv 2>> results/logs/transpose.log; done_ transpose $?

# ---- I9 convolution ----
stage I9_conv
echo "variant,n,t_med_ns,rel_err,round" > results/abl_I9_conv.csv
for r in 1 2 3; do for k in 16 18 20 22 24; do taskset -c $CPU build/bench_conv $((1<<k)) 0.5 | sed "s/$/,$r/" >> results/abl_I9_conv.csv; done; done
done_ I9_conv $?

# ---- I8 2-D ----
stage I8_2d
echo "variant,N,t_med_ns,mflops,rel_err,round" > results/abl_I8_2d.csv
for r in 1 2 3; do for N in 64 128 256 512 1024 2048; do taskset -c $CPU build/bench_2d $N 0.3 | sed "s/$/,$r/" >> results/abl_I8_2d.csv; done; done
done_ I8_2d $?

# ---- I15 PFA vs mixed radix ----
run I15_pfa $RB --impl pfa,stockham,rec4,fftw_measure,mkl,ducc --n $SM --rounds 3 --mintime 0.3 --check --out results/abl_I15_pfa.csv

# ---- Final comparison ----
P2=$(python3 -c "print(','.join(str(2**k) for k in range(4,27)))")
P2S=$(python3 -c "print(','.join(str(2**k) for k in range(4,21)))")
run final_pow2 $RB --impl pmfft,mkl,fftw_measure,ducc --n $P2 --rounds 3 --mintime 0.3 --check --out results/final_pow2.csv
run final_patient $RB --impl fftw_patient --n $P2S --rounds 3 --mintime 0.3 --out results/final_pow2_patient.csv
run final_smooth $RB --impl pmfft,mkl,fftw_measure,ducc --n 1000,3000,10000,100000,1000000,3145728,6553600,10000000 --rounds 3 --mintime 0.3 --check --out results/final_smooth.csv
run final_prime $RB --impl pmfft,mkl,fftw_measure,ducc --n 1009,10007,100003,1000003,4000037 --rounds 3 --mintime 0.3 --check --out results/final_prime.csv
run final_prime_fast $RB --impl pmfft --grid "fast=1" --n 1009,10007,100003,1000003,4000037 --rounds 3 --mintime 0.3 --check --out results/final_prime_fast.csv

# ---- untimed: Toeplitz tests, analysis ----
stage toeplitz; OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 taskset -c $CPU uv run tests/test_toeplitz.py > results/logs/toeplitz.log 2>&1; done_ toeplitz $?
run analyze uv run scripts/analyze.py
echo "=== $(date +%T) RUN_ALL COMPLETE" | tee -a $LOG
