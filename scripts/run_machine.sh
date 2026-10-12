#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-2.0-or-later
# Run the headline benchmark on this machine and store everything under results/machines/<label>/.
#
#   scripts/run_machine.sh <label> [--quick] [--no-scale] [--ablations] [--mt] [--factorial] [--cache-transition] [--fairness] [--repro] [--overhead] [--contention] [--caller-pages] [--ceiling] [--all] [--skip-base]
#
#   <label>       short machine name, e.g. epyc-9654 or ryzen-7950x (letters, digits, '-', '_', '.')
#   --quick       smoke test: 1 round, fewer sizes, short timings (~5 min); results go to <label>-quick
#   --no-scale    skip the multi-process bandwidth-scaling test
#   --ablations   also re-run the key ablations (NT stores, batching, split shape, explicit transposes)
#   --mt          also run the multithreaded comparison (pmfft_mt vs threaded MKL / FFTW, 1..all physical cores
#                 of socket 0; scripts/scale_mt.py).  FFTW plans each (threads, n) for up to $FFTW_TIMELIMIT_MT s
#                 (default 300), so this adds roughly 1-3 h
#   --factorial   full 2^4 factorial ablation of NT stores x batching x fused transposes x split policy at
#                 2^18, 2^20, 2^22, 2^25 (3 rounds), plus NT x strip width; interaction model on log runtime
#                 (scripts/factorial.py; ~1-1.5 h)
#   --cache-transition  dense smooth-size sweep across the L2 / LLC / 2-8 x LLC boundaries, pmfft vs MKL / FFTW /
#                 ducc0 with cycles, misses, DRAM traffic, plan choice and allocation size
#                 (scripts/cache_transition.py; ~1-2 h, FFTW planning dominates)
#   --fairness    protocol-sensitivity suite: in-place, cold caches, fresh arrays, 4 KB / all-huge pages, FFTW
#                 ESTIMATE / MEASURE / PATIENT with and without wisdom, first call, x86-64-v3 build, and a
#                 matched-protocol comparison; Williams-square order, 3 rounds (scripts/fairness.py; ~2-3 h)
#   --repro       reproducibility study with the pre-specified endpoints of results/ENDPOINTS.md: 10 blocks of
#                 pmfft / pmfft_heur / MKL / FFTW / ducc0 at 2^22..2^26 and four smooth sizes, every sample kept,
#                 clock and temperature logged, block bootstrap (scripts/repro.py).  Run twice: ordinary caller
#                 arrays (primary, amendment 3: repro_plain.*) and huge-page caller arrays (repro.*); ~2-3 h
#   --overhead    planning and memory overhead: library init, planning time, first call, cost curve of the first
#                 R calls, memory after planning / planning peak / execution scratch, break-even reuse counts
#                 (scripts/overhead.py; ~45 min, FFTW planning from scratch dominates)
#   --contention  controlled bandwidth contention: (A) k = 1..all cores independent processes with DRAM traffic and
#                 clocks per window, (B) one FFT beside a STREAM-triad load of measured bandwidth; on parts with
#                 several L3 domains B runs twice, load sharing the FFT core's L3 and load sharing only DRAM
#                 (scripts/contention.py; ~2 h)
#   --caller-pages  paging of the caller's arrays: interleaved A/B of huge-page vs ordinary (malloc'd) input/output
#                 for pmfft / MKL / FFTW / ducc0 (scripts/caller_pages.py, ~30 min), plus the strided-gather
#                 microbenchmark behind it: GB/s vs rows, segment size, page size and stride padding, which
#                 shows L2 set aliasing (scripts/idea1.py gather, ~10 min)
#   --ceiling     movement / compute ceilings of the two-pass plan (pure data movement, arithmetic only, two-pass
#                 streaming ideal; scripts/ceiling.py, ~20 min) and the error budget / speed-accuracy front of
#                 the Gaussian-resampling DFT for large primes (scripts/gauss_budget.py, ~40 min)
#   --all         every optional study: --ablations --mt --factorial --cache-transition --fairness --repro
#                 --overhead --contention --caller-pages --ceiling (~13-21 h)
#   --skip-base   skip the headline sweeps, convolution, scaling and traffic stages (for re-running selected
#                 optional studies into an existing results/machines/<label>/; build and correctness still run)
#   --no-counters skip the DRAM-traffic measurement (otherwise run when perf allows system-wide counters:
#                 `sudo sysctl kernel.perf_event_paranoid=0`, reverts at reboot)
#
# Single-core timings are pinned to one physical core chosen by scripts/cpus.py (override: BENCH_CPU=<cpu>);
# the scaling test uses one logical CPU per physical core of socket 0 (override: BENCH_CPUS=a,b,c).
# FFTW wisdom is kept per machine in results/machines/<label>/fftw_wisdom.dat.  A full run first plans every size
# >= 2^20 ahead with a long cap ($FFTW_PLAN_AHEAD_POW2 s for powers of two and 3*2^20, default 1800;
# $FFTW_PLAN_AHEAD_OTHER s otherwise, default 600; scripts/fftw_plan_ahead.py).  Remaining FFTW planning is capped at
# $FFTW_TIMELIMIT seconds per size (default 60).  Sizes where the cap is hit are flagged in summary.md.
# Full run: roughly 45-90 min depending on the machine.  Close other applications first.
set -uo pipefail
cd "$(dirname "$0")/.."
LABEL=${1:?usage: scripts/run_machine.sh <label> [--quick] [--no-scale] [--ablations] [--mt] [--factorial] [--cache-transition] [--fairness] [--repro] [--overhead] [--contention] [--caller-pages] [--ceiling] [--all]}; shift
[[ "$LABEL" =~ ^[A-Za-z0-9._-]+$ ]] || { echo "label must match [A-Za-z0-9._-]+"; exit 1; }
QUICK=0; SCALE=1; ABL=0; CNT=1; DOMT=0; FAC=0; CT=0; FAIR=0; REP=0; OVH=0; CON=0; CP=0; CEIL=0; BASE=1
for a in "$@"; do case $a in --quick) QUICK=1;; --no-scale) SCALE=0;; --ablations) ABL=1;; --no-counters) CNT=0;; --mt) DOMT=1;; --factorial) FAC=1;; --cache-transition) CT=1;; --fairness) FAIR=1;; --repro) REP=1;; --overhead) OVH=1;; --contention) CON=1;; --caller-pages) CP=1;; --ceiling) CEIL=1;; --skip-base) BASE=0; SCALE=0; CNT=0;;
  --all) ABL=1; DOMT=1; FAC=1; CT=1; FAIR=1; REP=1; OVH=1; CON=1; CP=1; CEIL=1;;
  *) echo "unknown option $a"; exit 1;; esac; done
[ $QUICK = 1 ] && LABEL=$LABEL-quick
OUT=results/machines/$LABEL
mkdir -p "$OUT/logs"
LOG=$OUT/run.log
export FFTW_WISDOM_FILE=$PWD/$OUT/fftw_wisdom.dat
export BENCH_CPU=${BENCH_CPU:-$(python3 scripts/cpus.py single)}
export FFTW_TIMELIMIT=${FFTW_TIMELIMIT:-60}   # seconds per FFTW plan; raise on slow machines (see README)
stage() { echo "=== $(date +%T) START $1" | tee -a "$LOG"; }
done_() { echo "=== $(date +%T) END   $1 (rc=$2)" | tee -a "$LOG"; }
run() { local name=$1; shift; stage "$name"; "$@" >> "$OUT/logs/$name.log" 2>&1; done_ "$name" $?; }

# ---- machine description ----
{
  echo "label: $LABEL"; echo "date: $(date -Is)"; echo "commit: $(git rev-parse --short HEAD 2>/dev/null || echo none)"
  echo "kernel: $(uname -srm)"; echo "compiler: $(gcc --version | head -1)"
  echo "bench_cpu: $BENCH_CPU"; echo "scale_cpus: $(python3 scripts/cpus.py list)"; echo "fftw_timelimit: $FFTW_TIMELIMIT"
  echo "glibc_tunables: ${GLIBC_TUNABLES:-none}   # glibc.malloc.hugetlb=1 gives library-internal buffers huge pages too"
  echo "thp: $(cat /sys/kernel/mm/transparent_hugepage/enabled 2>/dev/null)"
  echo "governor: $(cat /sys/devices/system/cpu/cpu$BENCH_CPU/cpufreq/scaling_governor 2>/dev/null || echo n/a)"
  echo "mem_total_gib: $(awk '/MemTotal/ {printf "%.1f", $2/1048576}' /proc/meminfo)"
  echo; echo "---- lscpu ----"; lscpu
  echo; echo "---- memory devices (needs root, optional) ----"; (sudo -n dmidecode -t memory 2>/dev/null | grep -E "^\s+(Speed|Configured Memory Speed|Type|Size):" | sort | uniq -c) || true
} > "$OUT/machine.txt"
grep -qw avx2 /proc/cpuinfo && grep -qw fma /proc/cpuinfo || { echo "AVX2+FMA required" | tee -a "$LOG"; exit 1; }

# ---- build + correctness ----
stage build; scripts/build.sh > "$OUT/logs/build.log" 2>&1; rc=$?; done_ build $rc
[ $rc = 0 ] || { echo "BUILD FAILED, see $OUT/logs/build.log"; exit 1; }
run test_stockham build/test_stockham
run correctness uv run scripts/run_bench.py quick
grep -q "ALL OK" "$OUT/logs/correctness.log" || echo "WARNING: correctness check reported failures (see $OUT/logs/correctness.log)" | tee -a "$LOG"

# ---- sizes (largest power of two limited by memory: ~128 B/point while pmfft plans) ----
AVAIL=$(awk '/MemAvailable/ {print $2*1024}' /proc/meminfo)
KMAX=$(python3 -c "import math; print(min(26, int(math.log2(0.8*$AVAIL/128))))")
if [ $QUICK = 1 ]; then
  ROUNDS=1; MT=0.1; P2=$(python3 -c "print(','.join(str(2**k) for k in range(6,min(23,$KMAX+1),2)))")
  SM=1000,100000,3145728; PR=10007,1000003; CONV="16 20 22"
else
  ROUNDS=3; MT=0.3; P2=$(python3 -c "print(','.join(str(2**k) for k in range(4,$KMAX+1)))")
  SM=1000,3000,10000,100000,1000000,3145728,6553600,10000000; PR=1009,10007,100003,1000003,4000037; CONV="16 18 20 22 24"
fi

# ---- FFTW plans ahead with a long cap (scripts/fftw_plan_ahead.py), for every size >= 2^20 any study uses, so the
#      studies import complete plans instead of searching under the 60 s cap; capped searches are recorded and
#      flagged through $FFTW_WISDOM_CHOICE ----
if [ $QUICK = 0 ]; then
  PPN=$(python3 -c "
k = $KMAX
s = [2**e for e in range(20, k + 1)] + [3 * 2**20, 5 * 2**20, 3 * 2**22, 5 * 2**22, 1000000, 6553600, 10000000, 1000003, 4000037]
print(','.join(str(n) for n in sorted(set(s)) if n <= 2**k))")
  run fftw_plan_ahead uv run scripts/fftw_plan_ahead.py --wisdom $OUT/fftw_wisdom.dat --n "$PPN" \
      --cap-pow2 ${FFTW_PLAN_AHEAD_POW2:-1800} --cap-other ${FFTW_PLAN_AHEAD_OTHER:-600} --out $OUT/fftw_wisdom_choice.csv
fi
[ -f $OUT/fftw_wisdom_choice.csv ] && export FFTW_WISDOM_CHOICE=$PWD/$OUT/fftw_wisdom_choice.csv
RB="uv run scripts/run_bench.py sweep"

# ---- headline comparison (same protocol as results/REPORT.md) ----
if [ $BASE = 1 ]; then
run final_pow2 $RB --impl pmfft,pmfft_heur,mkl,fftw_measure,ducc --n $P2 --rounds $ROUNDS --mintime $MT --check --out $OUT/final_pow2.csv
run final_smooth $RB --impl pmfft,pmfft_heur,mkl,fftw_measure,ducc --n $SM --rounds $ROUNDS --mintime $MT --check --out $OUT/final_smooth.csv
run final_prime $RB --impl pmfft,mkl,fftw_measure,ducc --n $PR --rounds $ROUNDS --mintime $MT --check --out $OUT/final_prime.csv
run final_prime_fast $RB --impl pmfft --grid "fast=1" --n $PR --rounds $ROUNDS --mintime $MT --check --out $OUT/final_prime_fast.csv

# ---- 3-sweep convolution vs library convolution ----
stage conv
echo "variant,n,t_med_ns,rel_err,round" > $OUT/conv.csv
for r in $(seq 1 $ROUNDS); do for k in $CONV; do
  taskset -c $BENCH_CPU build/bench_conv $((1<<k)) 0.5 2>> $OUT/logs/conv.log | sed "s/$/,$r/" >> $OUT/conv.csv
done; done
done_ conv $?
fi

# ---- multi-process bandwidth scaling ----
if [ $SCALE = 1 ]; then
  NC=$(python3 scripts/cpus.py list | tr ',' '\n' | wc -l)
  KS=$(python3 -c "print(','.join(str(k) for k in [1,2,4,6,8,12,16,24,32,48,64] if k <= $NC))")
  if [ $QUICK = 1 ]; then run scale_mp uv run scripts/scale_mp.py --quick --out $OUT/scale_mp.csv
  else run scale_mp uv run scripts/scale_mp.py --ks $KS --out $OUT/scale_mp.csv; fi
fi

# ---- DRAM traffic per transform from hardware counters (needs perf_event_paranoid <= 0) ----
if [ $CNT = 1 ]; then
  if [ "$(cat /proc/sys/kernel/perf_event_paranoid)" -le 0 ] && perf stat -a -e cycles -- true > /dev/null 2>&1; then
    R4="budget=131072,Bc=8,G=8,split=0,pad=4,rmax=16"
    MTN=2^22,2^24,3*2^20; [ $KMAX -ge 26 ] && MTN=$MTN,2^26; [ $QUICK = 1 ] && MTN=2^22
    run mem_traffic uv run scripts/mem_traffic.py --impls "pmfft;pmfft_heur;mkl;fftw_measure;ducc;rec4:$R4,nt=1;rec4:$R4,nt=0" \
        --n $MTN --rounds $([ $QUICK = 1 ] && echo 1 || echo 2) --mintime 2 --out $OUT/mem_traffic.csv
  else
    echo "=== skipping mem_traffic: run 'sudo sysctl kernel.perf_event_paranoid=0' to enable DRAM counters" | tee -a "$LOG"
  fi
fi

# ---- optional: multithreaded comparison (one process, T OpenMP threads, all libraries threaded) ----
if [ $DOMT = 1 ]; then
  if [ -x build/bench_dft_mt ]; then
    MTS=2^20,2^22,2^24,3*2^20; [ $KMAX -ge 26 ] && MTS=$MTS,2^26
    if [ $QUICK = 1 ]; then run scale_mt uv run scripts/scale_mt.py --quick --wisdom $OUT/fftw_wisdom_mt.dat --out $OUT/scale_mt.csv
    else run scale_mt uv run scripts/scale_mt.py --sizes $MTS --rounds 3 --fftw-timelimit ${FFTW_TIMELIMIT_MT:-300} \
             --wisdom $OUT/fftw_wisdom_mt.dat --out $OUT/scale_mt.csv; fi
    if [ $CNT = 1 ] && [ "$(cat /proc/sys/kernel/perf_event_paranoid)" -le 0 ]; then
      NC=$(python3 scripts/cpus.py list | tr ',' '\n' | wc -l)
      run mem_traffic_mt env FFTW_WISDOM_FILE=$PWD/$OUT/fftw_wisdom_mt.dat uv run scripts/mem_traffic.py --threads $NC \
          --impls "pmfft_mt,mkl,fftw_measure" --n $([ $QUICK = 1 ] && echo 2^22 || echo "2^22,2^24,3*2^20") \
          --rounds $([ $QUICK = 1 ] && echo 1 || echo 2) --mintime 2 --out $OUT/mem_traffic_mt.csv
    fi
  else
    echo "=== skipping scale_mt: build/bench_dft_mt missing (needs FFTW with --enable-openmp: rerun scripts/setup_third_party.sh)" | tee -a "$LOG"
  fi
fi

# ---- optional: do the key ideas transfer to this machine? ----
if [ $ABL = 1 ]; then
  S=2^18,2^20,2^22,2^24,$(python3 -c "print(f'2^{min(26,$KMAX)}')")
  BASE="budget=131072;Bc=8;G=8;split=0;nt=1;pad=4;rmax=16"
  ofat() { local key=${2%%=*}; local g=$(echo "$BASE" | tr ';' '\n' | grep -v "^$key=" | tr '\n' ';')"$2"
           run abl_rec4_$1 $RB --impl rec4 --grid "$g" --n $S --rounds $ROUNDS --mintime $MT --out $OUT/abl_rec4_$1.csv; }
  ofat nt "nt=0,1"; ofat I3_batch "Bc=1,8"; ofat I4_split "split=0,1"
  run abl_I1_sixstep $RB --impl sixstep --grid "nt=0,1" --n $S --rounds $ROUNDS --mintime $MT --out $OUT/abl_I1_sixstep.csv
fi

# ---- optional: full factorial ablation (interactions between NT, batching, fused transposes, split) ----
if [ $FAC = 1 ]; then
  FN=2^18,2^20,2^22,2^25; [ $KMAX -lt 25 ] && FN=2^18,2^20,2^22,2^$KMAX
  if [ $QUICK = 1 ]; then run factorial uv run scripts/factorial.py run --quick --out $OUT/factorial.csv
  else run factorial uv run scripts/factorial.py run --n $FN --rounds 3 --nt-study --out $OUT/factorial.csv; fi
  run factorial_analyze uv run scripts/factorial.py analyze --csv $OUT/factorial.csv
fi

# ---- optional: cache-capacity transition sweep ----
if [ $CT = 1 ]; then
  run cache_transition uv run scripts/cache_transition.py run $([ $QUICK = 1 ] && echo "--quick --rounds 1" || echo "--rounds 2") \
      --out $OUT/cache_transition.csv
  run cache_transition_plot uv run scripts/cache_transition.py plot --csv $OUT/cache_transition.csv \
      --out $OUT/fig_cache_transition.png
fi

# ---- optional: fairness / protocol sensitivity ----
if [ $FAIR = 1 ]; then
  FS=2^18,2^20,2^22,2^24,2^25,3*2^20,5*2^21; [ $KMAX -lt 25 ] && FS=2^18,2^20,2^22,2^$KMAX,3*2^20
  if [ $QUICK = 1 ]; then run fairness uv run scripts/fairness.py run --quick --rounds 1 --mintime 0.2 --out $OUT/fairness.csv
  else run fairness uv run scripts/fairness.py run --n "$FS" --rounds 3 --out $OUT/fairness.csv; fi
  run fairness_analyze uv run scripts/fairness.py analyze --csv $OUT/fairness.csv --md $OUT/fairness.md \
      --fig $OUT/fig_fairness.png
fi

# ---- optional: reproducibility study (pre-specified endpoints) ----
if [ $REP = 1 ]; then
  RP=2^22,2^23,2^24,2^25,2^26; [ $KMAX -lt 26 ] && RP=$(python3 -c "print(','.join(f'2^{k}' for k in range(22, $KMAX + 1)))")
  for pg in plain huge; do
    sfx=$([ $pg = plain ] && echo _plain || echo "")
    if [ $QUICK = 1 ]; then RA="--quick --blocks 2 --mintime 0.3"; else RA="--blocks 10"; fi
    run repro$sfx env BENCH_CALLER_PAGES=$pg uv run scripts/repro.py run $RA --primary $RP \
        --out $OUT/repro$sfx.csv --samples-out $OUT/repro${sfx}_samples.csv
    run repro${sfx}_analyze uv run scripts/repro.py analyze --csv $OUT/repro$sfx.csv \
        --samples $OUT/repro${sfx}_samples.csv --md $OUT/repro$sfx.md --fig $OUT/fig_repro$sfx.png
  done
fi

# ---- optional: planning and memory overhead ----
if [ $OVH = 1 ]; then
  ON=2^20,2^22,2^24,2^26,3*2^20; [ $KMAX -lt 26 ] && ON=2^20,2^22,2^24,2^$KMAX,3*2^20
  if [ $QUICK = 1 ]; then run overhead uv run scripts/overhead.py run --quick --rounds 1 --curve-max 3 --out $OUT/overhead.csv
  else run overhead uv run scripts/overhead.py run --n "$ON" --rounds 3 --out $OUT/overhead.csv; fi
  run overhead_analyze uv run scripts/overhead.py analyze --csv $OUT/overhead.csv --md $OUT/overhead.md \
      --fig $OUT/fig_overhead.png
fi

# ---- optional: controlled bandwidth contention ----
if [ $CON = 1 ]; then
  CA="--out-procs $OUT/contention_procs.csv"
  if [ $QUICK = 1 ]; then
    run contention_procs uv run scripts/contention.py procs --sizes 2^22 --ks 1,2 --rounds 1 --mintime 1 $CA
    run contention_interfere uv run scripts/contention.py interfere --sizes 2^22 --levels 0,1,2 --rounds 1 \
        --out-interfere $OUT/contention_interfere.csv
    run contention_analyze uv run scripts/contention.py analyze $CA --out-interfere $OUT/contention_interfere.csv \
        --md $OUT/contention.md --fig $OUT/fig_contention.png --plot-n 4194304
  else
    run contention_procs uv run scripts/contention.py procs --rounds 3 $CA
    # L3 domains among the CPUs the studies use (socket 0, scripts/cpus.py): a second socket's L3 does not count
    NLLC=$(for c in $(python3 scripts/cpus.py list | tr ',' ' '); do cat /sys/devices/system/cpu/cpu$c/cache/index3/shared_cpu_list 2>/dev/null; done | sort -u | wc -l)
    if [ "$NLLC" -gt 1 ]; then PLS="same-llc other-llc"; else PLS="any"; fi
    for pl in $PLS; do
      run contention_interfere_$pl uv run scripts/contention.py interfere --placement $pl --rounds 3 \
          --out-interfere $OUT/contention_interfere_$pl.csv
      run contention_analyze_$pl uv run scripts/contention.py analyze $CA --out-interfere $OUT/contention_interfere_$pl.csv \
          --md $OUT/contention_$pl.md --fig $OUT/fig_contention_$pl.png
    done
  fi
fi

# ---- optional: paging of the caller's arrays, and the strided-gather mechanism ----
if [ $CP = 1 ]; then
  CPN=2^22,3*2^20,2^24,2^25,2^26; [ $KMAX -lt 26 ] && CPN=$(python3 -c "print(','.join(['3*2^20'] + [f'2^{k}' for k in range(22, $KMAX + 1, 2)]))")
  if [ $QUICK = 1 ]; then run caller_pages uv run scripts/caller_pages.py run --n 2^22 --rounds 1 --mintime 0.3 \
      --out $OUT/caller_pages.csv
  else run caller_pages uv run scripts/caller_pages.py run --n "$CPN" --rounds 3 --out $OUT/caller_pages.csv; fi
  run caller_pages_analyze uv run scripts/caller_pages.py analyze --out $OUT/caller_pages.csv --md $OUT/caller_pages.md
  run gather uv run scripts/idea1.py gather --out-gather $OUT/idea1_gather.csv --out $OUT/idea1.csv
  run gather_analyze uv run scripts/idea1.py analyze --out-gather $OUT/idea1_gather.csv --out $OUT/idea1.csv \
      --md $OUT/gather.md
fi

# ---- optional: movement / compute ceilings and the Gaussian-resampling error budget ----
if [ $CEIL = 1 ]; then
  CN=2^22,2^24,2^25,2^26; [ $KMAX -lt 26 ] && CN=$(python3 -c "print(','.join(f'2^{k}' for k in (22, 24, 25, 26) if k <= $KMAX))")
  if [ $QUICK = 1 ]; then run ceiling uv run scripts/ceiling.py run --n 2^22 --rounds 1 --mintime 0.3 --out $OUT/ceiling.csv
  else run ceiling uv run scripts/ceiling.py run --n "$CN" --rounds 3 --out $OUT/ceiling.csv; fi
  run ceiling_analyze uv run scripts/ceiling.py analyze --out $OUT/ceiling.csv --md $OUT/ceiling.md
  GA="--out-acc $OUT/gauss_budget_acc.csv --out-time $OUT/gauss_budget_time.csv"
  if [ $QUICK = 1 ]; then run gauss_accuracy uv run scripts/gauss_budget.py accuracy --n 100003 $GA
  else run gauss_accuracy uv run scripts/gauss_budget.py accuracy $GA; fi
  run gauss_timing uv run scripts/gauss_budget.py timing --rounds $([ $QUICK = 1 ] && echo 1 || echo 3) $GA
  run gauss_analyze uv run scripts/gauss_budget.py analyze $GA --md $OUT/gauss_budget.md
fi

run summary uv run scripts/compare_machines.py
echo "=== $(date +%T) DONE: results in $OUT (summary: $OUT/summary.md, all machines: results/machines/COMPARISON.md)" | tee -a "$LOG"
