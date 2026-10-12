# SPDX-License-Identifier: GPL-2.0-or-later
"""Fairness and benchmark-protocol sensitivity: do SweepFFT's wins survive changes of planning, placement,
cache state, allocation, paging, compiler settings and protocol?

  uv run scripts/fairness.py run     [--n 2^18,2^20,2^22,2^24,2^25,3*2^20,5*2^21] [--rounds 3] [--quick]
  uv run scripts/fairness.py analyze [--csv results/fairness.csv]

Conditions (one factor changed at a time from the protocol used for every other result, "baseline"):
  baseline     out-of-place, warm, buffers reused, steady state (median after one warm-up call), FFTW wisdom
               imported from the machine's wisdom file, transparent huge pages as in the other results
               (shared buffers and SweepFFT scratch advised, library-internal malloc memory not)
  inplace      in-place transforms (FFTW in-place plan, DFTI_INPLACE, ducc0 without its copy; SweepFFT's two-pass
               plans run directly, its in-cache plans copy to a plan-owned array first)
  cold         caches flushed (256 MB read) before every timed call
  fresh_alloc  new input and output arrays for every call (output pages first touched inside the call)
  no_thp       standard 4 KB pages for everything (prctl PR_SET_THP_DISABLE)
  thp_all      huge pages for every malloc, library internals included (GLIBC_TUNABLES=glibc.malloc.hugetlb=1)
  matched      the matched protocol: every planner starts from scratch in the measuring process (FFTW MEASURE
               without wisdom, SweepFFT's measuring planner, MKL commit, ducc0 plan), huge pages for all memory
               (thp_all), everything else as baseline; SweepFFT also without its measuring planner (pmfft_heur)
In the baseline condition the FFTW planner variants and the compiler variants run in the same blocks:
  fftw_estimate          ESTIMATE, no wisdom              fftw_estimate_wisdom  ESTIMATE request, wisdom imported
  fftw_measure           MEASURE, wisdom imported          fftw_measure_fresh    MEASURE, no wisdom
  fftw_patient_fresh     PATIENT, no wisdom, $FFTW_PATIENT_TIMELIMIT (default 300 s), first round only
  pmfft_v3, pmfft_heur_v3  SweepFFT built with -march=x86-64-v3 -mtune=generic instead of -march=native
FFTW answers a request from wisdom of the same or a more rigorous mode, so the requested flag and the planning
actually done can differ: every row records the planning time, whether wisdom was imported, and the solver chain.

Crossover design: every run is a fresh process pinned to one core; per round (block) the (condition, size) jobs
are shuffled, and within a job the implementation order is a row of a Williams Latin square (balanced for
first-order carry-over), a different row for each job.  Sizes <= 2^20 are checked against the quad-precision
reference in every condition.  Each row records the steady-state median, the first call of the plan, the
planning time and the resident transparent-huge-page memory.
"""
import argparse
import io
import os
import random
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from run_bench import CORE, parse_sizes  # noqa: E402

BIN = ROOT / "build" / "bench_dft"
BIN_V3 = ROOT / "build" / "fair" / "bench_dft_v3"
CORE5 = ["pmfft", "pmfft_heur", "mkl", "fftw_measure", "ducc"]
CONDITIONS = {
    "baseline": dict(env={}, args=[], impls=CORE5 + ["fftw_measure_fresh", "fftw_estimate", "fftw_estimate_wisdom",
                                                     "fftw_patient_fresh", "pmfft_v3", "pmfft_heur_v3"]),
    "inplace": dict(env={"BENCH_INPLACE": "1"}, args=[], impls=CORE5),
    "cold": dict(env={}, args=["--cold"], impls=CORE5),
    "fresh_alloc": dict(env={}, args=["--fresh-alloc"], impls=CORE5),
    "no_thp": dict(env={"BENCH_NO_THP": "1"}, args=[], impls=CORE5),
    "thp_all": dict(env={"GLIBC_TUNABLES": "glibc.malloc.hugetlb=1"}, args=[], impls=CORE5),
    "matched": dict(env={"GLIBC_TUNABLES": "glibc.malloc.hugetlb=1"}, args=[],
                    impls=["pmfft", "pmfft_heur", "mkl", "fftw_measure_fresh", "ducc"]),
}
COND_DESC = {
    "baseline": "headline protocol", "inplace": "in-place", "cold": "cold caches", "fresh_alloc": "fresh arrays",
    "no_thp": "4 KB pages only", "thp_all": "huge pages for all", "matched": "matched protocol",
}
SWEEP = ("pmfft", "pmfft_heur")


def variant(impl, nowis):
    """Virtual implementation name -> (driver impl, binary, extra env)."""
    real, binary, env = impl, BIN, {}
    if impl.endswith("_v3"):
        real, binary = impl[:-3], BIN_V3
    if impl in ("fftw_measure_fresh", "fftw_patient_fresh", "fftw_estimate"):
        real = {"fftw_measure_fresh": "fftw_measure", "fftw_patient_fresh": "fftw_patient"}.get(impl, impl)
        env["FFTW_WISDOM_FILE"] = nowis                         # does not exist: planning from scratch
    if impl == "fftw_estimate_wisdom":
        real = "fftw_estimate"
    if impl == "fftw_patient_fresh":
        env["FFTW_TIMELIMIT"] = os.environ.get("FFTW_PATIENT_TIMELIMIT", "300")
    return real, binary, env


def williams(k):
    """Rows of a Williams design for k treatments (2k rows if k is odd)."""
    base = [0]
    lo, hi = 1, k - 1
    for j in range(1, k):
        base.append(lo if j % 2 else hi)
        if j % 2:
            lo += 1
        else:
            hi -= 1
    rows = [[(b + r) % k for b in base] for r in range(k)]
    if k % 2:
        rows += [row[::-1] for row in rows]
    return rows


def parse(so, se):
    f = pd.read_csv(io.StringIO(so), header=None).iloc[0]
    r = dict(plan_s=float(f[3]), t_med_ns=float(f[4]), t_min_ns=float(f[5]),
             rms_err=float(f[7]) if str(f[7]) != "nan" else np.nan, reps=int(f[9]))
    m = re.search(r"mem n=\d+ lib_bytes=(-?\d+) plan_peak_bytes=(-?\d+) plan=(.*)", se)
    if m:
        r.update(lib_bytes=int(m.group(1)), plan_peak_bytes=int(m.group(2)), plan=m.group(3).strip())
    m = re.search(r"fair n=\d+ t_first_ns=([\d.]+) anon_huge_bytes=(-?\d+) samples=(\d+)", se)
    if m:
        r.update(t_first_ns=float(m.group(1)), anon_huge_bytes=int(m.group(2)), samples=int(m.group(3)))
    m = re.search(r"fftw wisdom_file=\S+ imported=(\d)", se)
    if m:
        r["wisdom_imported"] = int(m.group(1))
    m = re.search(r"mkl version=(\S+) isa=(.*)", se)
    if m:
        r["mkl_isa"] = m.group(2).strip()
    return r


def run(a):
    out = Path(a.out)
    rows, done = [], set()
    if out.exists() and not a.fresh:
        rows = pd.read_csv(out).to_dict("records")
        done = {(r["cond"], r["impl"], int(r["n"]), int(r["round"])) for r in rows}
    ns = parse_sizes(a.n)
    conds = list(CONDITIONS)
    if a.quick:
        ns = [n for n in ns if n <= (1 << 22)][:3]
    tl = os.environ.get("FFTW_TIMELIMIT", "60")
    wis = os.environ.get("FFTW_WISDOM_FILE") or str(ROOT / "results" / "fftw_wisdom.dat")
    rng = random.Random(a.seed)
    njobs = sum(len(CONDITIONS[c]["impls"]) for c in conds) * len(ns)
    print(f"cpu {CORE}; {len(conds)} conditions x {len(ns)} sizes, {njobs} runs per round x {a.rounds} rounds; "
          f"wisdom {wis} (read-only); FFTW_TIMELIMIT {tl} s", flush=True)
    with tempfile.TemporaryDirectory() as tmp:
        nowis = os.path.join(tmp, "no-wisdom.dat")
        for rnd in range(a.rounds):
            jobs = [(c, n) for c in conds for n in ns]
            rng.shuffle(jobs)
            for jdx, (cond, n) in enumerate(jobs):
                C = CONDITIONS[cond]
                impls = [i for i in C["impls"] if not (i == "fftw_patient_fresh" and rnd > 0)]
                W = williams(len(impls))
                order = [impls[k] for k in W[(rnd * len(jobs) + jdx) % len(W)]]
                for pos, impl in enumerate(order):
                    if (cond, impl, n, rnd) in done:
                        continue
                    real, binary, venv = variant(impl, nowis)
                    env = dict(os.environ, FFTW_WISDOM_FILE=wis, FFTW_WISDOM_RO="1", FFTW_TIMELIMIT=tl)
                    env.update(C["env"])
                    env.update(venv)
                    cmd = ["taskset", "-c", CORE, str(binary), "--impl", real, "--n", str(n),
                           "--mintime", str(a.mintime)] + C["args"]
                    if n <= (1 << 20):
                        cmd += ["--check", "--check-max", str(1 << 20)]
                    p = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT, env=env)
                    if p.returncode or not p.stdout.strip():
                        print(f"FAIL {cond} {impl} n={n}: {p.stderr.strip()[-300:]}", file=sys.stderr, flush=True)
                        continue
                    r = dict(cond=cond, impl=impl, n=n, round=rnd, pos=pos, cpu=CORE, **parse(p.stdout, p.stderr))
                    ptl = float(venv.get("FFTW_TIMELIMIT", tl))
                    r["fftw_capped"] = impl.startswith("fftw") and r["plan_s"] >= 0.9 * ptl
                    r["gflops"] = 5 * n * np.log2(n) / r["t_med_ns"]
                    rows.append(r)
                    print(f"r{rnd} {cond:11s} {impl:21s} n={n:<9d} {r['gflops']:6.2f} GF  first "
                          f"{r.get('t_first_ns', np.nan) / r['t_med_ns']:5.2f}x  plan {r['plan_s']:7.2f} s  "
                          f"err {r['rms_err']:.1e}  {str(r.get('plan', ''))[:50]}", flush=True)
                    out.parent.mkdir(parents=True, exist_ok=True)
                    pd.DataFrame(rows).to_csv(out, index=False)


# ---------------------------------------------------------------------------------------------------------- analysis

def nlabel(n):
    k = int(n).bit_length() - 1
    if n == 1 << k:
        return f"2^{k}"
    odd = n
    while odd % 2 == 0:
        odd //= 2
    return f"{odd}·2^{int(n // odd).bit_length() - 1}"


def paired(df, cond, s, lib, n):
    """Speedup t_lib / t_s per round (paired within a block): geometric mean, 95% CI, rounds."""
    d = df[(df.cond == cond) & (df.n == n)]
    a = d[d.impl == s].set_index("round").t_med_ns
    b = d[d.impl == lib].set_index("round").t_med_ns
    cap = d[(d.impl == lib) & d.fftw_capped.astype(bool)]
    r = np.log(b / a).dropna()
    if r.empty:
        return np.nan, np.nan, np.nan, 0, not cap.empty
    m = r.mean()
    if len(r) > 1:
        h = stats.t.ppf(0.975, len(r) - 1) * r.std(ddof=1) / np.sqrt(len(r))
    else:
        h = np.nan
    return np.exp(m), np.exp(m - h), np.exp(m + h), len(r), not cap.empty


def fmt(v, lo, hi, cap=False):
    if np.isnan(v):
        return "–"
    s = f"{v:.2f}"
    if not np.isnan(lo):
        s += f" [{lo:.2f}, {hi:.2f}]"
    return s + (" †" if cap else "")


def fftw_of(cond):
    return "fftw_measure_fresh" if cond == "matched" else "fftw_measure"


def analyze(a):
    df = pd.read_csv(a.csv)
    df["fftw_capped"] = df.get("fftw_capped", False).fillna(False).astype(bool)
    ns = sorted(df.n.unique())
    out = []
    P = out.append
    P("# Fairness and protocol sensitivity (`scripts/fairness.py`)\n")
    P(f"Rounds (independent blocks): {df['round'].nunique()}; sizes: {', '.join(nlabel(n) for n in ns)}. "
      "Speedup = library time / SweepFFT time, paired within a round, geometric mean with 95% t interval over "
      "rounds; > 1 means SweepFFT is faster. † = FFTW's planner hit its time limit (plan truncated).\n")
    bad = df[df.rms_err > 1e-14]
    P(f"Correctness: {int(df.rms_err.notna().sum())} rows checked against the quad reference (n ≤ 2^20), "
      f"max relative RMS error {df.rms_err.max():.1e}; {len(bad)} rows above 1e-14.\n")
    if "mkl_isa" in df and df.mkl_isa.notna().any():
        P(f"MKL code path: {df.mkl_isa.dropna().iloc[0]}.\n")

    def table(cond, sweeps, libs, title):
        P(f"## {title}\n")
        hdr = "| n | " + " | ".join(f"{s} vs {l}" for s in sweeps for l in libs) + " |"
        P(hdr)
        P("|" + "---|" * (1 + len(sweeps) * len(libs)))
        for n in ns:
            cells = [fmt(*paired(df, cond, s, l, n)[:3], paired(df, cond, s, l, n)[4]) for s in sweeps for l in libs]
            P(f"| {nlabel(n)} | " + " | ".join(cells) + " |")
        P("")

    table("baseline", ["pmfft"], ["mkl", "fftw_measure", "ducc"],
          "Unadjusted: the headline protocol (FFTW wisdom imported, default paging)")
    table("matched", list(SWEEP), ["mkl", "fftw_measure_fresh", "ducc"],
          "Matched protocol: all planners from scratch, huge pages for all memory")

    # sensitivity: every condition, speedup vs MKL and FFTW per size
    P("## Sensitivity: SweepFFT (pmfft) speedup under each condition\n")
    for lib in ("mkl", "fftw"):
        P(f"**vs {'MKL' if lib == 'mkl' else 'FFTW MEASURE'}**\n")
        P("| condition | " + " | ".join(nlabel(n) for n in ns) + " |")
        P("|" + "---|" * (1 + len(ns)))
        for cond in CONDITIONS:
            L = lib if lib == "mkl" else fftw_of(cond)
            cells = []
            for n in ns:
                v, lo, hi, k, cap = paired(df, cond, "pmfft", L, n)
                cells.append(fmt(v, np.nan, np.nan, cap))
            P(f"| {COND_DESC[cond]} | " + " | ".join(cells) + " |")
        P("")
    # wins that persist
    P("## Do the baseline wins persist?\n")
    P("A *win* is a baseline (size, library) pair with speedup > 1 whose 95% interval excludes 1 "
      "(capped FFTW plans excluded). For each condition: how many of those wins remain > 1, and the range of the "
      "speedups there.\n")
    P("| condition | wins kept | speedup range on baseline wins | min speedup out of cache (n ≥ 2^22) |")
    P("|---|---|---|---|")
    wins = []
    for n in ns:
        for lib in ("mkl", "fftw", "ducc"):
            v, lo, hi, k, cap = paired(df, "baseline", "pmfft", "fftw_measure" if lib == "fftw" else lib, n)
            if not cap and lo > 1:
                wins.append((n, lib))
    for cond in CONDITIONS:
        vals, big = [], []
        for n, lib in wins:
            L = fftw_of(cond) if lib == "fftw" else lib
            v, _, _, _, cap = paired(df, cond, "pmfft", L, n)
            if not np.isnan(v) and not cap:
                vals.append(v)
        for n in ns:
            if n < (1 << 22):
                continue
            for lib in ("mkl", "fftw", "ducc"):
                L = fftw_of(cond) if lib == "fftw" else lib
                v, _, _, _, cap = paired(df, cond, "pmfft", L, n)
                if not np.isnan(v) and not cap:
                    big.append(v)
        kept = sum(v > 1 for v in vals)
        rng = f"{min(vals):.2f}–{max(vals):.2f}" if vals else "–"
        P(f"| {COND_DESC[cond]} | {kept}/{len(vals)} | {rng} | {min(big):.2f} |" if big else
          f"| {COND_DESC[cond]} | {kept}/{len(vals)} | {rng} | – |")
    P("")

    # first call vs steady state
    g = df.groupby(["cond", "impl", "n"])
    s = g[["t_med_ns", "t_first_ns", "plan_s"]].median().reset_index()
    P("## First call vs steady state (baseline)\n")
    P("t_first / t_med: the first call of a freshly planned transform relative to the steady-state median; "
      "and SweepFFT's speedup if only the first call is counted.\n")
    imps = [i for i in CORE5]
    P("| n | " + " | ".join(f"{i} first/steady" for i in imps) + " | first-call speedup vs MKL | vs FFTW |")
    P("|" + "---|" * (3 + len(imps)))
    b = s[s.cond == "baseline"].set_index(["impl", "n"])
    for n in ns:
        cells = []
        for i in imps:
            try:
                cells.append(f"{b.loc[(i, n), 't_first_ns'] / b.loc[(i, n), 't_med_ns']:.2f}")
            except KeyError:
                cells.append("–")
        try:
            fm = b.loc[("mkl", n), "t_first_ns"] / b.loc[("pmfft", n), "t_first_ns"]
            ff = b.loc[("fftw_measure", n), "t_first_ns"] / b.loc[("pmfft", n), "t_first_ns"]
            cells += [f"{fm:.2f}", f"{ff:.2f}"]
        except KeyError:
            cells += ["–", "–"]
        P(f"| {nlabel(n)} | " + " | ".join(cells) + " |")
    P("")

    # FFTW planner rigor: requested flag vs planning done
    P("## FFTW: requested planner flag vs planning actually done (baseline)\n")
    P("Planning time (median over rounds, s), steady-state GFlop/s and whether the chosen plan equals the plan "
      "found by a fresh MEASURE / fresh PATIENT search (solver chains compared).\n")
    fv = ["fftw_estimate", "fftw_estimate_wisdom", "fftw_measure", "fftw_measure_fresh", "fftw_patient_fresh"]
    P("| n | " + " | ".join(fv) + " | imported MEASURE = fresh MEASURE? | = fresh PATIENT? |")
    P("|" + "---|" * (3 + len(fv)))
    bb = df[df.cond == "baseline"]
    for n in ns:
        cells = []
        chain = {}
        for v in fv:
            d = bb[(bb.impl == v) & (bb.n == n)]
            if d.empty:
                cells.append("–")
                continue
            chain[v] = d.plan.mode().iloc[0] if "plan" in d and d.plan.notna().any() else ""
            gf = 5 * n * np.log2(n) / d.t_med_ns.median()
            cap = " †" if d.fftw_capped.any() else ""
            cells.append(f"{d.plan_s.median():.2f} s, {gf:.1f} GF{cap}")
        eqm = "yes" if chain.get("fftw_measure") and chain.get("fftw_measure") == chain.get("fftw_measure_fresh") else "no"
        eqp = ("yes" if chain.get("fftw_patient_fresh") and chain.get("fftw_measure") == chain.get("fftw_patient_fresh")
               else ("–" if "fftw_patient_fresh" not in chain else "no"))
        P(f"| {nlabel(n)} | " + " | ".join(cells) + f" | {eqm} | {eqp} |")
    P("")

    # huge-page coverage
    P("## Huge-page coverage at the largest size\n")
    P("Resident transparent-huge-page memory / (32 n + memory the implementation adds), median over rounds.\n")
    nmax = max(ns)
    P("| condition | " + " | ".join(CORE5) + " |")
    P("|" + "---|" * (1 + len(CORE5)))
    for cond in ("baseline", "no_thp", "thp_all"):
        cells = []
        for i in CORE5:
            d = df[(df.cond == cond) & (df.impl == i) & (df.n == nmax)]
            if d.empty or "anon_huge_bytes" not in d:
                cells.append("–")
                continue
            cov = d.anon_huge_bytes / (32.0 * nmax + d.lib_bytes.clip(lower=0))
            cells.append(f"{cov.median():.2f}")
        P(f"| {COND_DESC[cond]} | " + " | ".join(cells) + " |")
    P("")

    # compiler / ISA
    P("## Compiler settings: SweepFFT built for x86-64-v3 (generic tuning) vs -march=native\n")
    P("| n | pmfft v3 / native (time) | pmfft_heur v3 / native (time) |")
    P("|---|---|---|")
    for n in ns:
        cells = []
        for i in SWEEP:
            v, lo, hi, k, _ = paired(df, "baseline", i, i + "_v3", n)   # t_v3 / t_native
            cells.append(fmt(v, lo, hi))
        P(f"| {nlabel(n)} | " + " | ".join(cells) + " |")
    P("")
    Path(a.md).write_text("\n".join(out))
    print("\n".join(out))
    print("wrote", a.md)


def plot(csv, out, width=7.16, height=2.7, fontsize=7):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.ticker import NullFormatter
    PAL = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#4a3aa7", "#e34948"]
    INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"
    plt.rcParams.update({"font.size": fontsize, "font.family": "serif", "axes.edgecolor": INK2,
                         "axes.labelcolor": INK, "xtick.color": INK2, "ytick.color": INK2, "axes.grid": True,
                         "grid.color": GRID, "grid.linewidth": 0.5, "axes.spines.top": False,
                         "axes.spines.right": False, "lines.markersize": 4, "legend.frameon": False,
                         "legend.fontsize": fontsize - 0.5, "pdf.fonttype": 42})
    df = pd.read_csv(csv)
    df["fftw_capped"] = df.get("fftw_capped", False).fillna(False).astype(bool)
    ns = sorted(df.n.unique())
    conds = list(CONDITIONS)
    XL = (0.4, 4.0)
    fig, axs = plt.subplots(1, 3, figsize=(width, height), sharey=True)
    for ax, (lib, name) in zip(axs, (("mkl", "MKL"), ("fftw", "FFTW MEASURE"), ("ducc", "ducc0"))):
        for j, n in enumerate(ns):
            xs, ys = [], []
            for i, cond in enumerate(conds):
                L = fftw_of(cond) if lib == "fftw" else lib
                v, lo, hi, k, cap = paired(df, cond, "pmfft", L, n)
                if np.isnan(v) or cap:
                    continue
                y = i + (j - (len(ns) - 1) / 2) * 0.1
                xs.append(v)
                ys.append(y)
                if not np.isnan(lo):
                    ax.plot([max(lo, XL[0]), min(hi, XL[1])], [y, y], color=PAL[j % len(PAL)], lw=0.8)
            ax.plot(xs, ys, ls="", marker="o", color=PAL[j % len(PAL)], label=nlabel(n))
        ax.axvline(1, color=INK2, lw=0.8)
        ax.set_xscale("log")
        ax.set_xlim(*XL)
        ax.xaxis.set_minor_formatter(NullFormatter())
        ax.set_xticks([0.5, 0.7, 1, 1.5, 2, 3], ["0.5", "0.7", "1", "1.5", "2", "3"])
        ax.set_title(f"vs {name}", fontsize=fontsize, loc="left")
        ax.set_xlabel("SweepFFT speedup (log scale)")
    axs[0].set_yticks(range(len(conds)), [COND_DESC[c] for c in conds])
    axs[0].invert_yaxis()
    axs[-1].legend(loc="center left", bbox_to_anchor=(1.0, 0.5), title="n", title_fontsize=fontsize - 0.5)
    fig.tight_layout()
    fig.savefig(out, bbox_inches="tight", dpi=200)
    plt.close(fig)
    print("wrote", out)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--n", default="2^18,2^20,2^22,2^24,2^25,3*2^20,5*2^21")
    r.add_argument("--rounds", type=int, default=3)
    r.add_argument("--mintime", type=float, default=0.5)
    r.add_argument("--seed", type=int, default=1)
    r.add_argument("--quick", action="store_true", help="three sizes up to 2^22")
    r.add_argument("--fresh", action="store_true", help="ignore rows already in --out")
    r.add_argument("--out", default=str(ROOT / "results" / "fairness.csv"))
    z = sub.add_parser("analyze")
    z.add_argument("--csv", default=str(ROOT / "results" / "fairness.csv"))
    z.add_argument("--md", default=str(ROOT / "results" / "fairness.md"))
    z.add_argument("--fig", default=str(ROOT / "results" / "fig_fairness.png"))
    a = ap.parse_args()
    if a.cmd == "run":
        run(a)
    else:
        analyze(a)
        plot(a.csv, a.fig)


if __name__ == "__main__":
    main()
