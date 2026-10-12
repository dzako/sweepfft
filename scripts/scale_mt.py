# SPDX-License-Identifier: GPL-2.0-or-later
"""Multithreaded comparison: pmfft_mt vs threaded MKL vs threaded FFTW (build/bench_dft_mt).

  uv run scripts/scale_mt.py [--threads 1,2,4,6 | auto] [--sizes 2^20,2^22,...] [--rounds 3] [--out results/scale_mt.csv]
  uv run scripts/scale_mt.py --quick        # smoke test

All three libraries use the same GNU OpenMP runtime and the same pinning: $OMP_PLACES = one logical CPU per
physical core of socket 0, fastest first (scripts/cpus.py; override with $BENCH_CPUS), OMP_PROC_BIND=close.
Phase 1 builds FFTW wisdom for every (threads, n) with a generous planning limit (--fftw-timelimit, default
300 s) in its own file (FFTW_WISDOM_FILE, default results/fftw_wisdom_mt.dat).  Phase 2 times every
(threads, n, impl) in interleaved rounds with read-only wisdom; planning time is excluded as everywhere.
FFTW rows whose plan hit the cap are marked fftw_capped=True (truncated plan: not representative).
Memory: one process holding ~8.5 GB at n = 2^26; pass smaller --sizes on machines with < 16 GB.
"""
import argparse
import io
import os
import subprocess
import sys
import time
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from run_bench import parse_sizes, COLS  # noqa: E402

BIN = ROOT / "build" / "bench_dft_mt"


def cpus():
    out = subprocess.run([sys.executable, str(ROOT / "scripts" / "cpus.py"), "list"], capture_output=True, text=True)
    return [int(c) for c in out.stdout.strip().split(",")]


def run(impl, n, T, cpu_list, wisdom, mintime, check, write_wisdom=False, timelimit=60):
    env = dict(os.environ, BENCH_THREADS=str(T), OMP_NUM_THREADS=str(T), OMP_PROC_BIND="close",
               OMP_PLACES=",".join("{%d}" % c for c in cpu_list[:T]), FFTW_WISDOM_FILE=str(wisdom),
               FFTW_TIMELIMIT=str(timelimit), MKL_DYNAMIC="FALSE")
    if not write_wisdom:
        env["FFTW_WISDOM_RO"] = "1"
    cmd = ["taskset", "-c", ",".join(map(str, cpu_list[:T])), str(BIN), "--impl", impl, "--n", str(n),
           "--mintime", str(mintime)]
    if check:
        cmd += ["--check", "--check-max", str(1 << 22)]
    r = subprocess.run(cmd, capture_output=True, text=True, env=env, cwd=ROOT)
    if r.returncode != 0 or not r.stdout.strip():
        print(f"FAIL {impl} n={n} T={T}: {r.stderr.strip()[-300:]}", file=sys.stderr, flush=True)
        return None
    return pd.read_csv(io.StringIO(r.stdout), header=None, names=COLS).iloc[0].to_dict()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--threads", default="auto")
    ap.add_argument("--sizes", default="2^20,2^22,2^24,2^26,3*2^20")
    ap.add_argument("--impls", default="pmfft_mt,mkl,fftw_measure")
    ap.add_argument("--rounds", type=int, default=3)
    ap.add_argument("--mintime", type=float, default=1.0)
    ap.add_argument("--fftw-timelimit", type=float, default=300)
    ap.add_argument("--wisdom", default=str(ROOT / "results" / "fftw_wisdom_mt.dat"))
    ap.add_argument("--out", default=str(ROOT / "results" / "scale_mt.csv"))
    ap.add_argument("--quick", action="store_true", help="smoke test: threads 1 and max, n = 2^22, 1 round, 60 s cap")
    a = ap.parse_args()
    cl = cpus()
    if a.threads == "auto" or a.quick:   # 1, 2, 4, ... up to the number of physical cores of socket 0
        Ts = sorted({t for t in (1, 2, 4, 6, 8, 12, 16, 24, 32, 48, 64) if t <= len(cl)} | {len(cl)})
        if a.quick:
            Ts = sorted({1, len(cl)})
    else:
        Ts = [t for t in map(int, a.threads.split(",")) if t <= len(cl)]
    if a.quick:
        a.sizes, a.rounds, a.fftw_timelimit, a.mintime = "2^22", 1, 60, 0.3
    sizes = parse_sizes(a.sizes)
    impls = a.impls.split(",")
    print(f"CPUs {cl[:max(Ts)]}, threads {Ts}, sizes {sizes}", flush=True)
    capped = set()   # (T, n) where FFTW planning hit the cap: its plan there is truncated
    if "fftw_measure" in impls:
        for T in Ts:
            for n in sizes:
                t0 = time.time()
                r = run("fftw_measure", n, T, cl, a.wisdom, 0.05, False, write_wisdom=True, timelimit=a.fftw_timelimit)
                plan = r["plan_s"] if r else float("nan")
                if plan >= 0.98 * a.fftw_timelimit:
                    capped.add((T, n))
                print(f"wisdom T={T} n={n}: plan {plan:.1f} s ({time.time() - t0:.0f} s)"
                      + ("  [hit the planning cap]" if plan >= 0.98 * a.fftw_timelimit else ""), flush=True)
    rows = []
    for rnd in range(a.rounds):
        for T in Ts:
            for n in sizes:
                order = impls[rnd % len(impls):] + impls[:rnd % len(impls)]
                for impl in order:
                    r = run(impl, n, T, cl, a.wisdom, a.mintime, check=(rnd == 0))
                    if r is None:
                        continue
                    r.update(threads=T, round=rnd, fftw_capped=(impl == "fftw_measure" and (T, n) in capped),
                             fftw_timelimit=a.fftw_timelimit)
                    rows.append(r)
                    print(f"r{rnd} T={T} n={n:<9d} {impl:13s} {r['mflops'] / 1e3:6.1f} GF/s  err={r['rms_err']:.1e}",
                          flush=True)
                    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
                    pd.DataFrame(rows).to_csv(a.out, index=False)


if __name__ == "__main__":
    main()
