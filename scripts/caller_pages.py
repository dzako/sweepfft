# SPDX-License-Identifier: GPL-2.0-or-later
"""How the paging of the caller's arrays changes every implementation (interleaved A/B).

  uv run scripts/caller_pages.py run [--n 2^22,3*2^20,2^24,2^25,2^26] [--rounds 3]
  uv run scripts/caller_pages.py analyze

Conditions ($BENCH_CALLER_PAGES in bench_dft): "huge" = the headline protocol (input and output 2 MB aligned and
advised MADV_HUGEPAGE); "plain" = 64-byte aligned with no advice, which is what an ordinary caller that mallocs its
arrays gets under the system's THP mode ("madvise" on stock Ubuntu: 4 KB pages).  Library-internal memory is
untouched in both.  Background: with huge pages the physical address keeps the power-of-two row stride of a
strided pass, so all rows fall into the same L2 sets (scripts/idea1.py, results/idea1.md).
Each (condition, implementation, size) is a fresh pinned process; order shuffled per round; FFTW gets its best
saved plan per size ($FFTW_WISDOM_CHOICE, else $FFTW_WISDOM_FILE).
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
from fftw_best_wisdom import wisdom_for  # noqa: E402

IMPLS = ["pmfft", "mkl", "fftw_measure", "ducc"]
NAME = {"pmfft": "SweepFFT", "mkl": "MKL", "fftw_measure": "FFTW", "ducc": "ducc0"}
CONDS = ["huge", "plain"]


def run(a):
    out = Path(a.out)
    rows = pd.read_csv(out).to_dict("records") if out.exists() and not a.fresh else []
    done = {(r["cond"], r["impl"], int(r["n"]), int(r["round"])) for r in rows}
    jobs = [(c, i, n) for c in CONDS for i in IMPLS for n in parse_sizes(a.n)]
    rng = random.Random(a.seed)
    for rnd in range(a.rounds):
        rng.shuffle(jobs)
        for cond, impl, n in jobs:
            if (cond, impl, n, rnd) in done:
                continue
            env = dict(os.environ, BENCH_CALLER_PAGES=cond, FFTW_WISDOM_RO="1", FFTW_TIMELIMIT="60",
                       FFTW_WISDOM_FILE=wisdom_for(n, os.environ.get("FFTW_WISDOM_FILE") or str(ROOT / "results" / "fftw_wisdom.dat")))
            p = subprocess.run(["taskset", "-c", CORE, str(ROOT / "build" / "bench_dft"), "--impl", impl, "--n", str(n),
                                "--mintime", str(a.mintime)], capture_output=True, text=True, cwd=ROOT, env=env)
            if p.returncode or not p.stdout.strip():
                print(f"FAIL {cond} {impl} n={n}: {p.stderr.strip()[-200:]}", file=sys.stderr, flush=True)
                continue
            f = pd.read_csv(io.StringIO(p.stdout), header=None).iloc[0]
            rows.append(dict(cond=cond, impl=impl, n=n, round=rnd, gflops=float(f[6]) / 1e3, plan_s=float(f[3])))
            print(f"r{rnd} {cond:5s} {impl:13s} n={n:<9d} {rows[-1]['gflops']:6.2f} GF", flush=True)
            out.parent.mkdir(parents=True, exist_ok=True)
            pd.DataFrame(rows).to_csv(out, index=False)


def analyze(a):
    d = pd.read_csv(a.out)
    g = d.groupby(["n", "impl", "cond"]).gflops.median().unstack()
    lines = ["# Caller-array paging (`scripts/caller_pages.py`)\n",
             f"Median GFlop/s over {d['round'].nunique()} rounds; huge = caller arrays on 2 MB pages (headline "
             "protocol), plain = ordinary aligned allocation (system THP mode). Speedup = SweepFFT / library, "
             "both under the same condition.\n",
             "| n | impl | huge | plain | plain / huge | SweepFFT speedup, huge | SweepFFT speedup, plain |",
             "|---|---|---|---|---|---|---|"]
    for n in sorted(d.n.unique()):
        for impl in IMPLS:
            if (n, impl) not in g.index:
                continue
            h, pl = g.loc[(n, impl), "huge"], g.loc[(n, impl), "plain"]
            sh = g.loc[(n, "pmfft"), "huge"] / h if impl != "pmfft" else float("nan")
            sp = g.loc[(n, "pmfft"), "plain"] / pl if impl != "pmfft" else float("nan")
            lines.append(f"| {nlabel(n)} | {NAME[impl]} | {h:.2f} | {pl:.2f} | {pl / h:.2f} | "
                         + ("–" if impl == "pmfft" else f"{sh:.2f}") + " | " + ("–" if impl == "pmfft" else f"{sp:.2f}") + " |")
    # best-of-both: every implementation with its faster paging
    lines += ["", "Each implementation with its faster paging (SweepFFT speedup):", "",
              "| n | vs MKL | vs FFTW | vs ducc0 |", "|---|---|---|---|"]
    for n in sorted(d.n.unique()):
        best = g.loc[n].max(axis=1)
        lines.append(f"| {nlabel(n)} | " + " | ".join(f"{best['pmfft'] / best[i]:.2f}" for i in IMPLS[1:]) + " |")
    Path(a.md).write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--n", default="2^22,3*2^20,2^24,2^25,2^26")
    r.add_argument("--rounds", type=int, default=3)
    r.add_argument("--mintime", type=float, default=1.0)
    r.add_argument("--seed", type=int, default=7)
    r.add_argument("--fresh", action="store_true")
    z = sub.add_parser("analyze")
    z.add_argument("--md", default=str(ROOT / "results" / "caller_pages.md"))
    for x in (r, z):
        x.add_argument("--out", default=str(ROOT / "results" / "caller_pages.csv"))
    a = ap.parse_args()
    {"run": run, "analyze": analyze}[a.cmd](a)


if __name__ == "__main__":
    main()
