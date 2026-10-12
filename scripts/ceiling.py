# SPDX-License-Identifier: GPL-2.0-or-later
"""Data-movement and compute ceilings of the two-pass plan (rec4), per machine.

  uv run scripts/ceiling.py run [--n 2^22,2^24,2^25,2^26] [--rounds 3]
  uv run scripts/ceiling.py analyze

Idea (from the "design ceiling" method of the integer-multiplication research: bound a design before tuning it):
time the exact access pattern of the plan with the arithmetic removed, and the arithmetic with the memory traffic
removed (rec4 parameter ceil, csrc/dft/rec4.h):
  full     the plan as is
  move+tw  no sub-FFTs: gathers, twiddle multiplies, scatters (ceil=1)
  move     no sub-FFTs, no twiddles: pure data movement with the same strides and NT stores (ceil=2)
  compute  sub-FFTs only, on cache-resident strip buffers (ceil=3)
  ideal    two sequential passes in -> W -> out with NT stores: 4 S at streaming speed (ceil=4)
From these: how far the plan is from the two-pass ideal (full / ideal), how much of that is the strided access
pattern (move / ideal), how much is arithmetic (compute / full), and how well the two overlap
((move + compute) / full > 1: overlap).  Plans: the default two-pass rec4 and the staged variant; caller arrays on
huge pages and ordinarily allocated (BENCH_CALLER_PAGES).  Each run a fresh pinned process; order shuffled.
"""
import argparse
import io
import os
import random
import subprocess
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from run_bench import CORE, parse_sizes  # noqa: E402
from fairness import nlabel  # noqa: E402

PLANS = {"rec4": "budget=131072,rmax=8,nt=1,pad=4", "staged": "budget=131072,rmax=8,nt=1,pad=4,N1=2048,G=4,stage=256"}
CEIL = {0: "full", 1: "move+tw", 2: "move", 3: "compute", 4: "ideal"}
PAGES = ["huge", "plain"]


def run(a):
    out = Path(a.out)
    rows = pd.read_csv(out).to_dict("records") if out.exists() and not a.fresh else []
    done = {(r["plan"], r["ceil"], r["pages"], int(r["n"]), int(r["round"])) for r in rows}
    jobs = [(pl, c, pg, n) for pl in PLANS for c in CEIL for pg in PAGES for n in parse_sizes(a.n)
            if not (pl == "staged" and (n < 2**24 or c == 4))]
    rng = random.Random(a.seed)
    for rnd in range(a.rounds):
        rng.shuffle(jobs)
        for pl, c, pg, n in jobs:
            if (pl, c, pg, n, rnd) in done:
                continue
            env = dict(os.environ, BENCH_CALLER_PAGES=pg)
            p = subprocess.run(["taskset", "-c", CORE, str(ROOT / "build" / "bench_dft"), "--impl", "rec4", "--params",
                                f"{PLANS[pl]},ceil={c}", "--n", str(n), "--mintime", str(a.mintime)],
                               capture_output=True, text=True, cwd=ROOT, env=env)
            if p.returncode or not p.stdout.strip():
                print(f"FAIL {pl} ceil={c} {pg} n={n}: {p.stderr.strip()[-200:]}", file=sys.stderr, flush=True)
                continue
            f = pd.read_csv(io.StringIO(p.stdout), header=None).iloc[0]
            rows.append(dict(plan=pl, ceil=c, pages=pg, n=n, round=rnd, t_ms=float(f[4]) / 1e6))
            print(f"r{rnd} {pl:6s} {CEIL[c]:8s} {pg:5s} n={n:<9d} {rows[-1]['t_ms']:8.2f} ms", flush=True)
            out.parent.mkdir(parents=True, exist_ok=True)
            pd.DataFrame(rows).to_csv(out, index=False)


def analyze(a):
    d = pd.read_csv(a.out)
    g = d.groupby(["plan", "pages", "n", "ceil"]).t_ms.median().unstack()
    lines = ["# Movement and compute ceilings of the two-pass plan (`scripts/ceiling.py`)\n",
             f"Median time per transform (ms) over {d['round'].nunique()} rounds. S = 16n bytes; the two-pass ideal "
             "moves 4 S. GB/s columns = 4 S / time. move/ideal: cost of the plan's strided access pattern over "
             "sequential streaming; compute/full: arithmetic share; (move+compute)/full > 1 means the two overlap.\n",
             "| plan | caller pages | n | full | move+tw | move | compute | ideal | full GB/s | move GB/s | ideal GB/s "
             "| full/ideal | move/ideal | compute/full | (move+compute)/full |",
             "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for (pl, pg, n), r in g.iterrows():
        ideal = g.loc[("rec4", pg, n), 4] if ("rec4", pg, n) in g.index else float("nan")
        gb = lambda t: 4 * 16 * n / (t * 1e-3) / 1e9  # noqa: E731
        lines.append(f"| {pl} | {pg} | {nlabel(n)} | {r[0]:.1f} | {r[1]:.1f} | {r[2]:.1f} | {r[3]:.1f} | {ideal:.1f} | "
                     f"{gb(r[0]):.1f} | {gb(r[2]):.1f} | {gb(ideal):.1f} | {r[0] / ideal:.2f} | {r[2] / ideal:.2f} | "
                     f"{r[3] / r[0]:.2f} | {(r[2] + r[3]) / r[0]:.2f} |")
    Path(a.md).write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--n", default="2^22,2^24,2^25,2^26")
    r.add_argument("--rounds", type=int, default=3)
    r.add_argument("--mintime", type=float, default=1.0)
    r.add_argument("--seed", type=int, default=5)
    r.add_argument("--fresh", action="store_true")
    z = sub.add_parser("analyze")
    z.add_argument("--md", default=str(ROOT / "results" / "ceiling.md"))
    for x in (r, z):
        x.add_argument("--out", default=str(ROOT / "results" / "ceiling.csv"))
    a = ap.parse_args()
    {"run": run, "analyze": analyze}[a.cmd](a)


if __name__ == "__main__":
    main()
