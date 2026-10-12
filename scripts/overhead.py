# SPDX-License-Identifier: GPL-2.0-or-later
"""Planning and memory overhead: is the speedup useful once planning and memory are paid for?

  uv run scripts/overhead.py run     [--n 2^20,2^22,2^24,2^26,3*2^20] [--rounds 3] [--quick]
  uv run scripts/overhead.py analyze [--csv results/overhead.csv]

Every (implementation, n, round) is a fresh process pinned to one core (Williams-square order per size, as in
fairness.py).  It records:
  init_s            one-time library initialisation in a new process (a warm-up 64-point plan and call)
  plan_s            planner wall-clock time
  cum(R)            cumulative execution time of the first R calls right after planning, R = 1, 2, 5, 10, ...
                    (measured until R = 10,000 or 20 s of calls), then the usual steady-state median t_med
  memory            resident memory added by planning alone, the peak during planning, the execution-scratch
                    peak during the first call, and the steady state after it (all beyond the 32 n bytes of
                    input and output)
  planner work      SweepFFT: candidates timed and transforms executed while planning
Implementations: pmfft (measuring planner), pmfft_heur (size rule), mkl, ducc, and FFTW four ways:
  fftw_measure (MEASURE with the machine's saved wisdom: plan reuse), fftw_measure_fresh (MEASURE from
  scratch), fftw_estimate (ESTIMATE, no wisdom).  SweepFFT has no plan serialisation; it plans in every process.

analyze: total time T(R) = plan_s + cum(R) for R = 1, 2, 10, 100, 1,000, 10,000 (measured where the run reached R,
cum(R_last) + (R - R_last) t_med beyond), also with init_s added ("new process"); the break-even reuse count
    R* = (P_s - P_b) / (t_b - t_s),  P = plan_s + (t_first - t_med)  (setup including the first call's excess),
rounded up (1 if SweepFFT is ahead from the first transform, "never" if the baseline's steady state is faster);
memory per implementation in MB and in sweeps S = 16 n bytes.
"""
import argparse
import io
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from run_bench import CORE, parse_sizes  # noqa: E402
from fairness import williams, nlabel  # noqa: E402
from fftw_best_wisdom import wisdom_for  # noqa: E402

BIN = ROOT / "build" / "bench_dft"
IMPLS = ["pmfft", "pmfft_heur", "mkl", "fftw_measure", "fftw_measure_fresh", "fftw_estimate", "ducc"]
BASELINES = ["mkl", "fftw_measure", "fftw_measure_fresh", "fftw_estimate", "ducc"]
NAME = {"pmfft": "SweepFFT", "pmfft_heur": "SweepFFT (rule)", "mkl": "MKL", "fftw_measure": "FFTW MEASURE+wisdom",
        "fftw_measure_fresh": "FFTW MEASURE fresh", "fftw_estimate": "FFTW ESTIMATE", "ducc": "ducc0"}
RS = (1, 2, 10, 100, 1000, 10000)


def run(a):
    out = Path(a.out)
    rows = pd.read_csv(out).to_dict("records") if out.exists() and not a.fresh else []
    done = {(r["impl"], int(r["n"]), int(r["round"])) for r in rows}
    ns = parse_sizes(a.n)
    if a.quick:
        ns = ns[:2]
    wis = os.environ.get("FFTW_WISDOM_FILE") or str(ROOT / "results" / "fftw_wisdom.dat")
    tl = os.environ.get("FFTW_TIMELIMIT", "60")
    W = williams(len(IMPLS))
    print(f"cpu {CORE}; {len(ns)} sizes x {len(IMPLS)} impls x {a.rounds} rounds; wisdom {wis} (read-only)", flush=True)
    with tempfile.TemporaryDirectory() as tmp:
        nowis = os.path.join(tmp, "none.dat")
        for rnd in range(a.rounds):
            for si, n in enumerate(ns):
                for pos, impl in enumerate(IMPLS[k] for k in W[(rnd * len(ns) + si) % len(W)]):
                    if (impl, n, rnd) in done:
                        continue
                    real = {"fftw_measure_fresh": "fftw_measure"}.get(impl, impl)
                    env = dict(os.environ, FFTW_WISDOM_FILE=wisdom_for(n, wis), FFTW_WISDOM_RO="1", FFTW_TIMELIMIT=tl)
                    if impl in ("fftw_measure_fresh", "fftw_estimate"):
                        env["FFTW_WISDOM_FILE"] = nowis
                    cmd = ["taskset", "-c", CORE, str(BIN), "--impl", real, "--n", str(n), "--mintime",
                           str(a.mintime), "--curve", "10000", "--curve-max", str(a.curve_max)]
                    p = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT, env=env)
                    if p.returncode or not p.stdout.strip():
                        print(f"FAIL {impl} n={n}: {p.stderr.strip()[-300:]}", file=sys.stderr, flush=True)
                        continue
                    r = parse(p.stdout, p.stderr)
                    r.update(impl=impl, n=n, round=rnd, pos=pos, cpu=CORE)
                    r["fftw_capped"] = impl.startswith("fftw") and r["plan_s"] >= 0.9 * float(tl)
                    rows.append(r)
                    print(f"r{rnd} {impl:19s} n={n:<9d} init {r['init_s']:5.2f} s  plan {r['plan_s']:7.3f} s  "
                          f"first {r['t_first_s'] * 1e3:8.2f} ms  steady {r['t_med_s'] * 1e3:8.2f} ms  "
                          f"mem {r['lib_bytes'] / 16 / n:4.2f} S  peak {r['plan_peak_bytes'] / 16 / n:4.2f} S", flush=True)
                    out.parent.mkdir(parents=True, exist_ok=True)
                    pd.DataFrame(rows).to_csv(out, index=False)


def parse(so, se):
    f = pd.read_csv(io.StringIO(so), header=None).iloc[0]
    r = dict(plan_s=float(f[3]), t_med_s=float(f[4]) * 1e-9)
    m = re.search(r"curve n=\d+ init_s=([\d.]+) plan_s=[\d.]+ cum=(\S+)", se)
    r["init_s"] = float(m.group(1))
    cum = dict(tuple(map(float, x.split(":"))) for x in m.group(2).split(","))
    r["t_first_s"] = cum[1.0]
    r["cum"] = ";".join(f"{int(k)}:{v:.6f}" for k, v in sorted(cum.items()))
    m = re.search(r"mem n=\d+ lib_bytes=(-?\d+) plan_peak_bytes=(-?\d+) plan=(.*)", se)
    r.update(lib_bytes=int(m.group(1)), plan_peak_bytes=int(m.group(2)), plan=m.group(3).strip())
    m = re.search(r"mem2 n=\d+ after_plan_bytes=(-?\d+) exec_peak_bytes=(-?\d+)", se)
    r.update(after_plan_bytes=int(m.group(1)), exec_peak_bytes=int(m.group(2)))
    m = re.findall(r"planner n=(\d+) candidates=(\d+) timed_transforms=(\d+)", se)
    m = [x for x in m if x[0] != "64"]                 # not the 64-point warm-up plan
    m = m[-1][1:] if m else None
    r.update(candidates=int(m[0]) if m else np.nan, timed_transforms=int(m[1]) if m else np.nan)
    m = re.search(r"fftw wisdom_file=\S+ imported=(\d)", se)
    r["wisdom_imported"] = int(m.group(1)) if m else np.nan
    return r


# ---------------------------------------------------------------------------------------------------------- analysis

def total(row, R, new_process=False):
    """T(R) = plan + cumulative time of the first R calls (+ library init for a new process)."""
    cum = {int(k): float(v) for k, v in (x.split(":") for x in row["cum"].split(";"))}
    last = max(k for k in cum if k <= R) if any(k <= R for k in cum) else 1
    c = cum[R] if R in cum else cum[last] + (R - last) * row["t_med_s"]
    return row["plan_s"] + c + (row["init_s"] if new_process else 0.0)


def summary(df):
    """Median over rounds per (impl, n) of every scalar, and the median total time at each R."""
    rows = []
    for (impl, n), d in df.groupby(["impl", "n"]):
        r = dict(impl=impl, n=n)
        for c in ("init_s", "plan_s", "t_first_s", "t_med_s", "lib_bytes", "plan_peak_bytes", "after_plan_bytes",
                  "exec_peak_bytes", "candidates", "timed_transforms"):
            r[c] = d[c].median()
        r["fftw_capped"] = bool(d.fftw_capped.any())
        for R in RS:
            r[f"T{R}"] = np.median([total(x, R) for _, x in d.iterrows()])
            r[f"N{R}"] = np.median([total(x, R, True) for _, x in d.iterrows()])
        r["R_measured"] = int(np.median([max(int(k.split(":")[0]) for k in x.cum.split(";")) for _, x in d.iterrows()]))
        rows.append(r)
    return pd.DataFrame(rows)


def breakeven(s, sw, b, n, col="T"):
    """Break-even reuse count from the per-impl medians (closed form, T(R) ~ P + R t): 1 if always, inf if never."""
    a = s[(s.impl == sw) & (s.n == n)].iloc[0]
    c = s[(s.impl == b) & (s.n == n)].iloc[0]
    Pa = a.plan_s + a.t_first_s - a.t_med_s + (a.init_s if col == "N" else 0)
    Pc = c.plan_s + c.t_first_s - c.t_med_s + (c.init_s if col == "N" else 0)
    ta, tc = a.t_med_s, c.t_med_s
    if Pa <= Pc and ta <= tc:
        return 1.0, (Pa - Pc) / (tc - ta) if tc > ta else np.nan
    if ta >= tc:
        return np.inf, np.nan
    rstar = (Pa - Pc) / (tc - ta)
    return max(1.0, np.ceil(rstar)), rstar


def fmt_r(v):
    if np.isinf(v):
        return "never"
    if v <= 1:
        return "1 (always)"
    return f"{v:,.0f}"


def analyze(a):
    df = pd.read_csv(a.csv)
    df["fftw_capped"] = df.fftw_capped.fillna(False).astype(bool)
    s = summary(df)
    ns = sorted(s.n.unique())
    out = []
    W = out.append
    W("# Planning and memory overhead (`scripts/overhead.py`)\n")
    W(f"{df['round'].nunique()} rounds, one fresh process per run; medians over rounds. Total time T(R) = planning + "
      "the first R calls, measured up to R = " + ", ".join(f"{nlabel(n)}: {int(s[s.n == n].R_measured.min())}"
                                                           for n in ns) +
      " calls and extrapolated with the steady-state median beyond. † = FFTW's planner hit its time limit.\n")
    W("## Setup and per-call cost\n")
    W("| n | impl | library init (s) | planning (s) | first call (ms) | steady call (ms) | first / steady | "
      "planner candidates / timed transforms |")
    W("|---|---|---|---|---|---|---|---|")
    for n in ns:
        for i in IMPLS:
            d = s[(s.impl == i) & (s.n == n)]
            if d.empty:
                continue
            r = d.iloc[0]
            pc = (f"{int(r.candidates)} / {int(r.timed_transforms)}" if not np.isnan(r.candidates) else "–")
            W(f"| {nlabel(n)} | {NAME[i]}{' †' if r.fftw_capped else ''} | {r.init_s:.3f} | {r.plan_s:.3f} | "
              f"{r.t_first_s * 1e3:.2f} | {r.t_med_s * 1e3:.2f} | {r.t_first_s / r.t_med_s:.2f} | {pc} |")
    W("")
    W("## Total time T(R) for R repeated transforms (s), planning included, library already initialised\n")
    W("| n | impl | " + " | ".join(f"R={R:,}" for R in RS) + " |")
    W("|---|---|" + "---|" * len(RS))
    for n in ns:
        for i in IMPLS:
            d = s[(s.impl == i) & (s.n == n)]
            if d.empty:
                continue
            r = d.iloc[0]
            W(f"| {nlabel(n)} | {NAME[i]} | " + " | ".join(f"{r[f'T{R}']:.3g}" for R in RS) + " |")
    W("")
    W("## Break-even reuse count R* for SweepFFT vs each baseline\n")
    W("Smallest number of transforms after which SweepFFT (planning included) has spent less total time than the "
      "baseline; closed form R* = (P_s − P_b) / (t_b − t_s), P = planning + first-call excess. \"always\": SweepFFT "
      "is ahead from the first transform; \"never\": the baseline's steady state is faster. In a running process "
      "(library initialised) / in a new process (initialisation included).\n")
    for sw in ("pmfft", "pmfft_heur"):
        W(f"**{NAME[sw]}**\n")
        W("| n | " + " | ".join(NAME[b] for b in BASELINES) + " |")
        W("|---|" + "---|" * len(BASELINES))
        for n in ns:
            cells = []
            for b in BASELINES:
                if s[(s.impl == b) & (s.n == n)].empty or s[(s.impl == sw) & (s.n == n)].empty:
                    cells.append("–")
                    continue
                r1, _ = breakeven(s, sw, b, n, "T")
                r2, _ = breakeven(s, sw, b, n, "N")
                cap = " †" if s[(s.impl == b) & (s.n == n)].fftw_capped.iloc[0] else ""
                cells.append(f"{fmt_r(r1)} / {fmt_r(r2)}{cap}")
            W(f"| {nlabel(n)} | " + " | ".join(cells) + " |")
        W("")
    W("## Memory beyond the 32 n bytes of input and output (MB; in sweeps S = 16 n bytes)\n")
    W("after planning = resident memory the plan holds; planning peak = peak during planning and the first call; "
      "execution scratch = extra resident peak during the first call; steady = after the first call.\n")
    W("| n | impl | after planning | planning peak | execution scratch | steady |")
    W("|---|---|---|---|---|---|")
    for n in ns:
        for i in IMPLS:
            d = s[(s.impl == i) & (s.n == n)]
            if d.empty:
                continue
            r = d.iloc[0]
            cells = [f"{max(r[c], 0) / 2**20:.0f} ({max(r[c], 0) / (16 * n):.2f})"
                     for c in ("after_plan_bytes", "plan_peak_bytes", "exec_peak_bytes", "lib_bytes")]
            W(f"| {nlabel(n)} | {NAME[i]} | " + " | ".join(cells) + " |")
    W("")
    Path(a.md).write_text("\n".join(out))
    print("\n".join(out))
    print("wrote", a.md)
    plot(s, a.fig)


def plot(s, out, width=7.16, height=2.5, fontsize=7):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    PAL = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#4a3aa7", "#e34948"]
    INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"
    COL = {"pmfft": PAL[0], "pmfft_heur": PAL[6], "mkl": PAL[1], "fftw_measure": PAL[2],
           "fftw_measure_fresh": PAL[5], "fftw_estimate": PAL[4], "ducc": PAL[3]}
    LS = {"fftw_measure_fresh": "--", "fftw_estimate": ":", "pmfft_heur": "--"}
    plt.rcParams.update({"font.size": fontsize, "font.family": "serif", "axes.edgecolor": INK2,
                         "axes.labelcolor": INK, "xtick.color": INK2, "ytick.color": INK2, "axes.grid": True,
                         "grid.color": GRID, "grid.linewidth": 0.5, "axes.spines.top": False,
                         "axes.spines.right": False, "lines.linewidth": 1.3, "lines.markersize": 3,
                         "legend.frameon": False, "legend.fontsize": fontsize - 0.5, "pdf.fonttype": 42})
    ns = sorted(s.n.unique())
    show = [n for n in ns if n in (1 << 22, 1 << 24, 1 << 26, 3 << 20)][:3] or ns[:3]
    fig, axs = plt.subplots(1, len(show), figsize=(width, height))
    axs = np.atleast_1d(axs)
    for ax, n in zip(axs, show):
        ref = s[(s.impl == "pmfft") & (s.n == n)]
        for i in IMPLS:
            d = s[(s.impl == i) & (s.n == n)]
            if d.empty or ref.empty:
                continue
            y = [d.iloc[0][f"T{R}"] / ref.iloc[0][f"T{R}"] for R in RS]
            ax.plot(RS, y, marker="o", color=COL[i], ls=LS.get(i, "-"),
                    label=NAME[i] + (" †" if d.iloc[0].fftw_capped else ""))
        ax.axhline(1, color=INK2, lw=0.8)
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_xticks(RS, ["1", "2", "10", "100", "1k", "10k"])
        ax.set_xlabel("number of transforms R")
        ax.set_title(f"n = {nlabel(n)}", fontsize=fontsize, loc="left")
    axs[0].set_ylabel("total time T(R) / SweepFFT's")
    axs[-1].legend(loc="center left", bbox_to_anchor=(1.0, 0.5))
    fig.tight_layout()
    fig.savefig(out, bbox_inches="tight", dpi=200)
    plt.close(fig)
    print("wrote", out)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--n", default="2^20,2^22,2^24,2^26,3*2^20")
    r.add_argument("--rounds", type=int, default=3)
    r.add_argument("--mintime", type=float, default=0.5)
    r.add_argument("--curve-max", type=float, default=20.0, help="stop the cost curve after this many seconds")
    r.add_argument("--quick", action="store_true")
    r.add_argument("--fresh", action="store_true")
    r.add_argument("--out", default=str(ROOT / "results" / "overhead.csv"))
    z = sub.add_parser("analyze")
    z.add_argument("--csv", default=str(ROOT / "results" / "overhead.csv"))
    z.add_argument("--md", default=str(ROOT / "results" / "overhead.md"))
    z.add_argument("--fig", default=str(ROOT / "results" / "fig_overhead.png"))
    a = ap.parse_args()
    run(a) if a.cmd == "run" else analyze(a)


if __name__ == "__main__":
    main()
