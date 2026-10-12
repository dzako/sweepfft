# SPDX-License-Identifier: GPL-2.0-or-later
"""Give FFTW its best available plan per size.

FFTW_MEASURE chooses among plans by timing them, so two searches for the same size can settle on plans of
different speed (on the i7: the long-lived wisdom ran 8.9 GFlop/s at 2^24 where a fresh search found 11.2,
while at 2^23 the fresh search found 8.6 against the old wisdom's 11.5).  This script times FFTW with each
candidate wisdom file, alternating the files over --rounds fresh processes, and records per size the file
whose plan is fastest (median).  The choice uses only FFTW's own speed.

  uv run scripts/fftw_best_wisdom.py --n 2^22,... --wisdom results/fftw_wisdom.dat,results/fftw_wisdom_fresh.dat \
      [--rounds 3] [--out results/fftw_wisdom_choice.csv]

Scripts that compare against FFTW (repro.py, overhead.py, contention.py) use the recorded file for each size
when $FFTW_WISDOM_CHOICE points to the CSV (see wisdom_for below).
"""
import argparse
import io
import os
import subprocess
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent


def wisdom_for(n, default):
    """Wisdom file for size n: the recorded best when $FFTW_WISDOM_CHOICE names a choice CSV, else default."""
    p = os.environ.get("FFTW_WISDOM_CHOICE")
    if p and Path(p).exists():
        d = pd.read_csv(p)
        m = d[d.n == n]
        if len(m):
            f = m.iloc[0].best_file
            return str(ROOT / f) if not os.path.isabs(f) else f
    return default


def main():
    sys.path.insert(0, str(ROOT / "scripts"))
    from run_bench import CORE, parse_sizes
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", required=True)
    ap.add_argument("--wisdom", required=True, help="comma-separated wisdom files (paths relative to the repo)")
    ap.add_argument("--rounds", type=int, default=3)
    ap.add_argument("--mintime", type=float, default=0.5)
    ap.add_argument("--out", default=str(ROOT / "results" / "fftw_wisdom_choice.csv"))
    a = ap.parse_args()
    files = a.wisdom.split(",")
    rows = []
    for n in parse_sizes(a.n):
        for rnd in range(a.rounds):
            for f in (files if rnd % 2 == 0 else files[::-1]):
                env = dict(os.environ, FFTW_WISDOM_FILE=str(ROOT / f), FFTW_WISDOM_RO="1", FFTW_TIMELIMIT="0.5")
                p = subprocess.run(["taskset", "-c", CORE, str(ROOT / "build" / "bench_dft"), "--impl", "fftw_measure",
                                    "--n", str(n), "--mintime", str(a.mintime)], capture_output=True, text=True,
                                   cwd=ROOT, env=env)
                r = pd.read_csv(io.StringIO(p.stdout), header=None).iloc[0]
                plan = [l for l in p.stderr.splitlines() if l.startswith("mem ")]
                rows.append(dict(n=n, file=f, round=rnd, plan_s=float(r[3]), gflops=float(r[6]) / 1e3,
                                 plan=plan[0].split("plan=")[-1] if plan else ""))
                print(f"n={n:<9d} {f:40s} {rows[-1]['gflops']:6.2f} GF  plan {rows[-1]['plan_s']:.3f} s", flush=True)
    d = pd.DataFrame(rows)
    s = d.groupby(["n", "file"]).agg(gflops=("gflops", "median"), plan_s=("plan_s", "max"),
                                     plan=("plan", "first")).reset_index()
    out = []
    for n, g in s.groupby("n"):
        b = g.loc[g.gflops.idxmax()]
        r = dict(n=n, best_file=b.file, best_gflops=b.gflops)
        for _, x in g.iterrows():
            r[f"gflops[{x.file}]"] = x.gflops
            r[f"plan_s[{x.file}]"] = x.plan_s
        out.append(r)
    pd.DataFrame(out).to_csv(a.out, index=False)
    d.to_csv(a.out.replace(".csv", "_runs.csv"), index=False)
    print(pd.DataFrame(out).to_string(index=False))
    print("wrote", a.out)


if __name__ == "__main__":
    main()
