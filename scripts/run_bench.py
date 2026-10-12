# SPDX-License-Identifier: GPL-2.0-or-later
"""Benchmark sweep runner: calls build/bench_dft for (impl, params, sizes) and collects a DataFrame.

Usage examples:
  uv run scripts/run_bench.py sweep --impl rec4 --grid "budget=8192,32768;Bc=8,16" --n 2^20,2^22 --out results/x.csv
  uv run scripts/run_bench.py quick           # correctness + short sweep of every implementation
"""
import argparse
import io
import os
import itertools
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
BIN = ROOT / "build" / "bench_dft"
# CPU for pinned single-core timings: $BENCH_CPU, else the fastest physical core (scripts/cpus.py)
CORE = os.environ.get("BENCH_CPU") or subprocess.run([sys.executable, str(ROOT / "scripts" / "cpus.py"), "single"],
                                                     capture_output=True, text=True).stdout.strip() or "0"
COLS = "impl,params,n,plan_s,t_med_ns,t_min_ns,mflops,rms_err,max_err,reps".split(",")


def parse_sizes(spec):
    out = []
    for tok in spec.split(","):
        tok = tok.strip()
        if "*" in tok:
            v = 1
            for f in tok.split("*"):
                v *= parse_sizes(f)[0]
            out.append(v)
        elif "^" in tok:
            b, e = tok.split("^")
            out.append(int(b) ** int(e))
        else:
            out.append(int(tok))
    return out


def run(impl, params, sizes, check=False, mintime=0.3, extra=()):
    cmd = ["taskset", "-c", CORE, str(BIN), "--impl", impl, "--params", params,
           "--n", ",".join(map(str, sizes)), "--mintime", str(mintime)]
    if check:
        cmd += ["--check", "--check-max", str(1 << 20)]
    cmd += list(extra)
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT)
    if r.returncode != 0:
        print(r.stderr, file=sys.stderr)
    if not r.stdout.strip():
        return pd.DataFrame(columns=COLS)
    df = pd.read_csv(io.StringIO(r.stdout), header=None, names=COLS)
    df["params"] = df["params"].fillna("")
    return df


def grid(spec):
    """'a=1,2;b=x,y' -> ['a=1,b=x', 'a=1,b=y', ...]"""
    if not spec:
        return [""]
    keys, vals = [], []
    for part in spec.split(";"):
        k, v = part.split("=")
        keys.append(k)
        vals.append(v.split(","))
    return [",".join(f"{k}={x}" for k, x in zip(keys, combo)) for combo in itertools.product(*vals)]


def sweep(impls, gridspec, sizes, check=False, mintime=0.3, verbose=True, rounds=1):
    """Run every (impl, params) over sizes; with rounds > 1 the full grid is repeated in
    interleaved order (reduces bias from thermal / background-load drift).  Each row keeps its
    round index; analysis takes the median over rounds."""
    frames = []
    for rnd in range(rounds):
        for impl in impls:
            for params in grid(gridspec):
                df = run(impl, params, sizes, check=check and rnd == 0, mintime=mintime)
                df["round"] = rnd
                if verbose and len(df):
                    for _, r in df.iterrows():
                        print(f"[{rnd}] {impl:16s} {params:40s} n={r.n:<10d} {r.mflops:9.1f} MF  err={r.rms_err:.2e}", flush=True)
                frames.append(df)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(columns=COLS)


def summarize(df):
    """Median over rounds of the per-run median time; error from round 0."""
    df = df.copy()
    df["params"] = df["params"].fillna("").astype(str)
    g = df.groupby(["impl", "params", "n"], sort=False)
    out = g.agg(t_med_ns=("t_med_ns", "median"), t_min_ns=("t_min_ns", "min"),
                mflops_spread=("mflops", lambda x: (x.max() - x.min()) / x.median() if len(x) > 1 else 0.0),
                rms_err=("rms_err", "first"), max_err=("max_err", "first")).reset_index()
    out["mflops"] = 5 * out.n * np.log2(out.n) / out.t_med_ns * 1e3
    return out


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("sweep")
    s.add_argument("--impl", required=True, help="comma-separated")
    s.add_argument("--grid", default="")
    s.add_argument("--n", required=True)
    s.add_argument("--check", action="store_true")
    s.add_argument("--mintime", type=float, default=0.3)
    s.add_argument("--rounds", type=int, default=1)
    s.add_argument("--out")
    q = sub.add_parser("quick")
    q.add_argument("--out", default=None)
    a = ap.parse_args()
    if a.cmd == "sweep":
        df = sweep(a.impl.split(","), a.grid, parse_sizes(a.n), a.check, a.mintime, rounds=a.rounds)
    else:
        sizes = parse_sizes("2^4,2^7,2^10,2^13,2^16,2^18,3*2^10,5*7*2^8")
        sizes += parse_sizes("1009,10007")          # primes: Bluestein path of pmfft
        df = sweep(["fftw_estimate", "mkl", "ducc", "radix2", "stockham", "rec4", "pmfft"], "", sizes, check=True, mintime=0.1)
        # radix2 / rec4 support powers of two (rec4 also smooth n) only: unsupported sizes are skipped, not failures
        df = df[~((df.impl == "radix2") & ((df.n & (df.n - 1)) != 0)) & ~(df.impl.isin(["radix2", "rec4", "stockham"]) & df.n.isin([1009, 10007]))]
        bad = df[(df.rms_err > 1e-14) | df.rms_err.isna()]
        print("\nCORRECTNESS:", "ALL OK" if bad.empty else f"{len(bad)} rows failed or unsupported")
        if not bad.empty:
            print(bad[["impl", "params", "n", "rms_err"]].to_string())
            sys.exit(1)
    if a.out:
        out = ROOT / a.out
        out.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(out, index=False)


if __name__ == "__main__":
    main()
