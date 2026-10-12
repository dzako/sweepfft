# SPDX-License-Identifier: GPL-2.0-or-later
"""Error budget and speed/accuracy front of the Gaussian-resampling DFT (I7, fast mode) for large primes.

  uv run scripts/gauss_budget.py accuracy [--n 100003,1000003,4000037]
  uv run scripts/gauss_budget.py timing   [--rounds 3]
  uv run scripts/gauss_budget.py analyze

Background (csrc/dft/arbitrary.h, gau_*): the transform spreads the input onto a smooth grid of length
t = smooth((1 + delta) s) with a Gaussian of width set by L (nats), takes one FFT of length t, divides by the
Gaussian's spectrum (which amplifies the FFT's rounding by up to e^L at the band edge), and corrects the aliased
neighbours with `iters` Neumann iterations (the largest alias ratio is R = exp(-4 L (delta + delta^2))).
The research note on chirp scaling (CrocSwap/integer-mult-bounds #371, notes/chirp-scaling-correction) makes the
point that such a scheme needs an explicit precision budget.  Here: the measured error against a quad-precision
reference over a grid of (L, delta, iters), a fitted error model err ~ a e^L eps + b R^(iters+1), and the time of
the configurations on the accuracy/speed front, against exact Bluestein (pmfft) and MKL.  Current fast default:
L = 4, delta = 0.4, iters = 1.
"""
import argparse
import io
import math
import random
import subprocess
import sys
from itertools import product
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from run_bench import CORE  # noqa: E402

LS = [2, 3, 4, 5, 6, 8]
DELTAS = [0.25, 0.4, 0.6]
ITERS = [0, 1, 2, 3]


def bench(impl, params, n, check, mintime):
    cmd = ["taskset", "-c", CORE, str(ROOT / "build" / "bench_dft"), "--impl", impl, "--n", str(n), "--mintime",
           str(mintime)] + (["--params", params] if params else []) + (["--check", "--check-max", str(1 << 23)] if check else [])
    p = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT)
    if p.returncode or not p.stdout.strip():
        print(f"FAIL {impl} {params} n={n}: {p.stderr.strip()[-200:]}", file=sys.stderr, flush=True)
        return None
    f = pd.read_csv(io.StringIO(p.stdout), header=None).iloc[0]
    return dict(t_ms=float(f[4]) / 1e6, rms=float(f[7]), max=float(f[8]))


def cfg(L, d, it):
    return f"L={L},delta={d},iters={it}"


def accuracy(a):
    rows = []
    for n in [int(x) for x in a.n.split(",")]:
        for L, d, it in product(LS, DELTAS, ITERS):
            r = bench("gauss", cfg(L, d, it), n, True, 0.05)
            if r:
                rows.append(dict(n=n, L=L, delta=d, iters=it, **r))
                print(f"n={n} L={L} delta={d} iters={it}: rms {r['rms']:.2e} max {r['max']:.2e}", flush=True)
        for impl, params in (("pmfft", None), ("mkl", None)):
            r = bench(impl, params, n, True, 0.05)
            if r:
                rows.append(dict(n=n, L=np.nan, delta=np.nan, iters=np.nan, impl=impl, **r))
        pd.DataFrame(rows).to_csv(a.out_acc, index=False)


def front(acc):
    """Configurations on the accuracy front at each n: for each error decade, the cheapest (fewest taps, shortest t,
    fewest iterations) is not known without timing, so keep all configs that are not dominated in (rms, L, delta,
    iters) -- smaller is cheaper for every parameter."""
    g = acc[acc.L.notna()]
    keep = set()
    for n, x in g.groupby("n"):
        for _, r in x.iterrows():
            dom = x[(x.rms <= r.rms) & (x.L <= r.L) & (x.delta <= r.delta) & (x.iters <= r.iters)
                    & ((x.rms < r.rms) | (x.L < r.L) | (x.delta < r.delta) | (x.iters < r.iters))]
            if dom.empty and r.rms < 1e-10:
                keep.add((r.L, r.delta, int(r.iters)))
    keep.add((4, 0.4, 1))
    return sorted(keep)


def timing(a):
    acc = pd.read_csv(a.out_acc)
    cfgs = front(acc)
    ns = sorted(acc.n.unique())
    jobs = [("gauss", cfg(*c), n) for c in cfgs for n in ns] + [(i, None, n) for i in ("pmfft", "mkl") for n in ns]
    rows, rng = [], random.Random(11)
    for rnd in range(a.rounds):
        rng.shuffle(jobs)
        for impl, params, n in jobs:
            r = bench(impl, params, int(n), False, a.mintime)
            if r:
                rows.append(dict(impl=impl, params=params or "", n=int(n), round=rnd, t_ms=r["t_ms"]))
                print(f"r{rnd} {impl:5s} {params or '':28s} n={n:<8d} {r['t_ms']:8.2f} ms", flush=True)
        pd.DataFrame(rows).to_csv(a.out_time, index=False)


def analyze(a):
    acc = pd.read_csv(a.out_acc)
    g = acc[acc.L.notna()].copy()
    eps = 2.0**-53
    g["R"] = np.exp(-4 * g.L * (g.delta + g.delta**2))
    # fit log(rms) ~ log(a e^L eps + b R^(c (iters+1))) by least squares over (a, b, c) on a grid
    best = None
    lr = np.log10(g.rms.values)
    for c in np.linspace(0.5, 4, 36):
        alias = g.R.values ** (c * (g.iters.values + 1))
        for la in np.linspace(-1, 2, 31):
            floor = 10**la * np.exp(g.L.values) * eps
            for lb in np.linspace(-4, 2, 61):
                e = float(np.mean((np.log10(floor + 10**lb * alias) - lr) ** 2))
                if best is None or e < best[0]:
                    best = (e, la, lb, c)
    _, la, lb, c = best
    g["model"] = 10**la * np.exp(g.L) * eps + 10**lb * g.R ** (c * (g.iters + 1))
    lines = ["# Gaussian-resampling DFT: error budget and speed/accuracy front (`scripts/gauss_budget.py`)\n",
             f"Relative RMS error against a quad-precision reference. Fitted model: rms ≈ {10**la:.2g}·e^L·ε + "
             f"{10**lb:.2g}·R^({c:.1f}·(iters+1)), R = exp(−4L(δ+δ²)); log10 RMS residual {math.sqrt(best[0]):.2f} "
             "(a factor of " f"{10**math.sqrt(best[0]):.1f}). The first term is the rounding floor (the deconvolution "
             "multiplies rounding errors by up to e^L), the second the uncorrected aliasing.\n"]
    ref = acc[acc.L.isna()]
    for n, x in g.groupby("n"):
        lines.append(f"## n = {n}\n")
        e_ex = ref[(ref.n == n) & (ref.impl == "pmfft")].rms
        e_mk = ref[(ref.n == n) & (ref.impl == "mkl")].rms
        lines.append(f"Exact Bluestein (pmfft) rms {e_ex.iloc[0]:.1e}; MKL {e_mk.iloc[0]:.1e}.\n" if len(e_ex) and len(e_mk) else "")
        piv = x.pivot_table(index=["L", "delta"], columns="iters", values="rms")
        lines.append(piv.map(lambda v: f"{v:.1e}").to_markdown())
        lines.append("")
    if Path(a.out_time).exists():
        t = pd.read_csv(a.out_time, keep_default_na=False)
        tm = t.groupby(["impl", "params", "n"]).t_ms.median().reset_index()
        lines.append("## Speed/accuracy front (median ms over rounds; speedup vs MKL)\n")
        lines.append("| n | config | rms | ms | vs MKL | vs exact Bluestein |")
        lines.append("|---|---|---|---|---|---|")
        for n, x in tm.groupby("n"):
            mk = x[x.impl == "mkl"].t_ms.iloc[0]
            ex = x[x.impl == "pmfft"].t_ms.iloc[0]
            for _, r in x[x.impl == "gauss"].sort_values("t_ms").iterrows():
                kv = dict(p.split("=") for p in r.params.split(","))
                e = g[(g.n == n) & (g.L == float(kv["L"])) & (g.delta == float(kv["delta"]))
                      & (g.iters == int(kv["iters"]))].rms.iloc[0]
                lines.append(f"| {n} | {r.params} | {e:.1e} | {r.t_ms:.2f} | {mk / r.t_ms:.2f} | {ex / r.t_ms:.2f} |")
            lines.append(f"| {n} | exact Bluestein | | {ex:.2f} | {mk / ex:.2f} | 1.00 |")
            lines.append(f"| {n} | MKL | | {mk:.2f} | 1.00 | |")
    Path(a.md).write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("accuracy")
    c.add_argument("--n", default="100003,1000003,4000037")
    t = sub.add_parser("timing")
    t.add_argument("--rounds", type=int, default=3)
    t.add_argument("--mintime", type=float, default=0.5)
    z = sub.add_parser("analyze")
    z.add_argument("--md", default=str(ROOT / "results" / "gauss_budget.md"))
    for x in (c, t, z):
        x.add_argument("--out-acc", default=str(ROOT / "results" / "gauss_budget_acc.csv"))
        x.add_argument("--out-time", default=str(ROOT / "results" / "gauss_budget_time.csv"))
    a = ap.parse_args()
    {"accuracy": accuracy, "timing": timing, "analyze": analyze}[a.cmd](a)


if __name__ == "__main__":
    main()
