#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-2.0-or-later
# Re-measure the results affected by the split / sub-line-store fix (commit 410a7d6, results/diag_xeon_10m.md):
# the smooth size 10^7, the fast (Gaussian-resampling) prime mode, and the error-budget timings, whose inner
# smooth lengths changed split.  Powers of two and the pre-registered studies are unaffected.
#   scripts/postfix_rerun.sh <machine results dir> [FFTW wisdom file] [FFTW choice csv]
# Writes <dir>/postfix/: final_smooth.csv (n = 10^7), final_prime.csv + final_prime_fast.csv, gauss_budget_*.
set -uo pipefail
cd "$(dirname "$0")/.."
D=${1:?machine results dir}; W=${2:-$D/fftw_wisdom.dat}; C=${3:-$D/fftw_wisdom_choice.csv}
OUT=$D/postfix; mkdir -p "$OUT"
export FFTW_WISDOM_FILE=$PWD/$W FFTW_WISDOM_RO=1 FFTW_TIMELIMIT=60
[ -f "$C" ] && export FFTW_WISDOM_CHOICE=$PWD/$C
export BENCH_CPU=${BENCH_CPU:-$(python3 scripts/cpus.py single)}
RB="uv run scripts/run_bench.py sweep"
echo "=== $(date) postfix rerun in $OUT (cpu $BENCH_CPU, commit $(git rev-parse --short HEAD 2>/dev/null || echo archive))"
$RB --impl pmfft,pmfft_heur,mkl,fftw_measure,ducc --n 10000000 --rounds 3 --mintime 0.3 --out $OUT/final_smooth.csv
$RB --impl pmfft,mkl,fftw_measure,ducc --n 1009,10007,100003,1000003,4000037 --rounds 3 --mintime 0.3 --check \
    --out $OUT/final_prime.csv
$RB --impl pmfft --grid "fast=1" --n 1009,10007,100003,1000003,4000037 --rounds 3 --mintime 0.3 --check \
    --out $OUT/final_prime_fast.csv
uv run scripts/gauss_budget.py timing --rounds 3 --out-acc $D/gauss_budget_acc.csv --out-time $OUT/gauss_budget_time.csv
uv run scripts/gauss_budget.py analyze --out-acc $D/gauss_budget_acc.csv --out-time $OUT/gauss_budget_time.csv \
    --md $OUT/gauss_budget.md > /dev/null
echo "=== $(date) POSTFIX DONE"
