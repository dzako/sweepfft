# SPDX-License-Identifier: GPL-2.0-or-later
"""Full 2^4 factorial ablation of the four key rec4 design choices, with an interaction model on log runtime.

  uv run scripts/factorial.py run     [--n 2^18,2^20,2^22,2^25] [--rounds 3] [--quick] [--nt-study]
  uv run scripts/factorial.py analyze [--csv results/factorial.csv]

Factors (all on the same rec4 kernel, leaves budget=131072 radix-8, pad=4, no staging, one core):
  NT     non-temporal stores        off: ordinary stores         on: nt=1 (also 16-byte NT stores for short segments)
  BATCH  batched strips             off: Bc = G = 1 (one column / row per kernel call)    on: Bc = G = 8 (auto)
  FUSE   transposition              off: sep=1, three explicit blocked transpose passes (six-step, 5 sweeps)
                                    on:  transposes fused into the strip gathers / scatters (2 passes)
  SPLIT  four-step split            off: balanced N1 ~ sqrt(n)   on: split=1, N1 sized to fill the leaf budget
Sizes: 2^18 (in LLC), 2^20 (cache transition, W = 32 MB), 2^22 (moderately out of cache), 2^25 (very large).

Each (cell, n, round) is a fresh bench_dft process pinned to one core; the cell order is shuffled per round.
With system-wide perf counters the DRAM read / write sweeps and core cycles are recorded too (as in
mem_traffic.py).  --nt-study adds the NT x strip-width experiment: fused, balanced split, Bc = G in
{1, 2, 4, 8, 16, 32}, NT off/on, at the two largest sizes: does NT help only with enough independent
full-line writes in flight?

analyze: per size, OLS of log t on the +-1 coded factors with all interactions (16 terms, replicates give the
residual error).  A k-factor term is reported as the runtime ratio exp(2^k beta): a main effect is the
(geometric) mean ratio on/off over the other factors (< 1 means faster); a two-factor interaction A:B is the
ratio of A's effect with B on to A's effect with B off (1 = independent); a three-factor term compares that
ratio across the third factor.  With a 95% CI and the term's share of the explained sum of squares.
Also: simple effects of NT at every (BATCH, FUSE) level, and the NT x strip-width table.
"""
import argparse
import io
import itertools
import os
import random
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
from mem_traffic import dram_events, supported, perf_stat, bytes_rw, PMU  # noqa: E402

BIN = ROOT / "build" / "bench_dft"
FACTORS = ("NT", "BATCH", "FUSE", "SPLIT")
BASE = "budget=131072,rmax=8,pad=4"


def cell_params(nt, batch, fuse, split):
    b = 0 if batch else 1                       # 0 = auto (8 lanes), 1 = unbatched
    return f"{BASE},nt={nt},Bc={b},G={b},sep={1 - fuse},split={split}"


def cells():
    for lv in itertools.product((0, 1), repeat=4):
        yield dict(zip(FACTORS, lv)), cell_params(*lv)


def nt_cells():
    for bc in (1, 2, 4, 8, 16, 32):
        for nt in (0, 1):
            yield dict(study="nt_lanes", NT=nt, Bc=bc), f"{BASE},nt={nt},Bc={bc},G={bc},sep=0,split=0"


def run(a):
    out = Path(a.out)
    rows, done = [], set()
    if out.exists() and not a.fresh:
        rows = pd.read_csv(out).to_dict("records")
        done = {(r["params"], int(r["n"]), int(r["round"])) for r in rows}
    ns = parse_sizes(a.n)
    jobs = [(dict(study="factorial", **lv), p, n) for lv, p in cells() for n in ns]
    if a.nt_study:
        jobs += [(lv, p, n) for lv, p in nt_cells() for n in ns[-2:]]
    dev, kind = dram_events()
    pre, suf = ("cpu_core/", "/") if (PMU / "cpu_core").exists() else ("", "")
    core = supported([f"{pre}cycles{suf}", f"{pre}instructions{suf}"]) if dev else []
    events = dev + core
    print(f"cpu {CORE}; {len(jobs)} jobs x {a.rounds} rounds; DRAM events {kind} ({len(dev)}), core {core}", flush=True)
    rng = random.Random(a.seed)
    with tempfile.TemporaryDirectory() as tmp:
        ctl, ack = os.path.join(tmp, "ctl"), os.path.join(tmp, "ack")
        os.mkfifo(ctl)
        os.mkfifo(ack)
        idle = {}
        for rnd in range(a.rounds):
            order = jobs[:]
            rng.shuffle(order)
            for k, (lv, params, n) in enumerate(order):
                if (params, n, rnd) in done:
                    continue
                if dev and (k % 16 == 0 or not idle):
                    idle = perf_stat(dev, ["sleep", "1"], tmp)[0]       # idle DRAM baseline, refreshed regularly
                cmd = ["taskset", "-c", CORE, str(BIN), "--impl", "rec4", "--params", params, "--n", str(n),
                       "--mintime", str(a.mintime)]
                vals = {}
                if events:
                    try:
                        vals, so, se = perf_stat(events, cmd + ["--perf-ctl", f"{ctl},{ack}"], tmp, (ctl, ack))
                    except RuntimeError as e:
                        print(f"FAIL {params} n={n}: {e}", file=sys.stderr)
                        continue
                else:
                    r = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT)
                    so, se = r.stdout, r.stderr
                if not so.strip():
                    print(f"FAIL {params} n={n}: {se.strip()[-300:]}", file=sys.stderr)
                    continue
                f = pd.read_csv(io.StringIO(so), header=None).iloc[0]
                t = float(f[4]) * 1e-9
                r = dict(lv, params=params, n=n, round=rnd, t_med_ns=t * 1e9,
                         gflops=5 * n * np.log2(n) / t * 1e-9, cpu=CORE)
                m = re.search(r"timed_s=([\d.]+) calls=(\d+)", se)
                if events and m:
                    timed, calls = float(m.group(1)), int(m.group(2))
                    net = {kk: v - idle.get(kk, 0.0) * timed if kk in idle else v for kk, v in vals.items()}
                    rd, wr = bytes_rw(net, kind)
                    cyc = sum(v for kk, v in vals.items() if "cycles" in kk)
                    ins = sum(v for kk, v in vals.items() if "instructions" in kk)
                    r.update(read_sweeps=rd / calls / (16 * n), write_sweeps=wr / calls / (16 * n),
                             cyc_per_elem=cyc / calls / n if cyc else np.nan, ipc=ins / cyc if cyc else np.nan,
                             dram_kind=kind)
                rows.append(r)
                tag = " ".join(f"{k}={lv[k]}" for k in lv if k != "study")
                print(f"r{rnd} n={n:<9d} {tag:28s} {r['gflops']:6.2f} GF  R {r.get('read_sweeps', np.nan):5.2f} "
                      f"W {r.get('write_sweeps', np.nan):5.2f} S", flush=True)
                out.parent.mkdir(parents=True, exist_ok=True)
                pd.DataFrame(rows).to_csv(out, index=False)


# ---------------- analysis ----------------
def terms():
    """All 16 terms of the full factorial model, as tuples of factor names (() = intercept)."""
    return [c for k in range(5) for c in itertools.combinations(FACTORS, k)]


def fit(d):
    """OLS of log t on +-1 coded factors with all interactions; returns a DataFrame of terms."""
    from scipy import stats
    X = np.column_stack([np.prod([2 * d[f].values - 1 for f in tm], axis=0) if tm else np.ones(len(d))
                         for tm in terms()])
    y = np.log(d.t_med_ns.values)
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    res = y - X @ beta
    dof = len(y) - X.shape[1]
    s2 = res @ res / dof if dof > 0 else np.nan
    se = np.sqrt(s2 * np.diag(np.linalg.pinv(X.T @ X))) if dof > 0 else np.full(len(beta), np.nan)
    q = stats.t.ppf(0.975, dof) if dof > 0 else np.nan
    ss = beta**2 * len(y)                    # orthogonal design: SS of a term = N beta^2
    tot = ss[1:].sum()
    out = []
    for tm, b, e, sq in zip(terms(), beta, se, ss):
        if not tm:
            continue
        c = 2.0 ** len(tm)        # main effect: ratio on/off; 2-way: ratio of the two simple-effect ratios; ...
        out.append(dict(term=":".join(tm), order=len(tm), ratio=np.exp(c * b), lo=np.exp(c * (b - q * e)),
                        hi=np.exp(c * (b + q * e)), share=sq / tot,
                        signif=bool(abs(b) > q * e) if dof > 0 else None))
    return pd.DataFrame(out), dict(dof=dof, resid_sd=np.sqrt(s2), r2=1 - res @ res / ((y - y.mean()) @ (y - y.mean())))


def analyze(a):
    df = pd.read_csv(a.csv)
    fac = df[df.study == "factorial"].copy()
    fac[list(FACTORS)] = fac[list(FACTORS)].astype(int)
    lines = ["# Full factorial ablation (2^4) on log runtime", ""]
    allfx = []
    for n, d in fac.groupby("n"):
        cnt = d.groupby(list(FACTORS)).size()
        if len(cnt) < 16:
            lines.append(f"n = {n}: only {len(cnt)} of 16 cells measured, skipped\n")
            continue
        fx, info = fit(d)
        fx["n"] = n
        allfx.append(fx)
        best = d.groupby(list(FACTORS)).t_med_ns.median()
        off, on = best[(0, 0, 0, 0)], best[(1, 1, 1, 1)]
        lines += [f"## n = {n}  (all off -> all on: {off / on:.2f}x faster; residual sd {info['resid_sd']:.3f} "
                  f"in log t, {info['dof']} dof, R^2 = {info['r2']:.4f})", "",
                  "| term | runtime ratio (main: on/off; interaction: ratio of ratios) | 95% CI | share of explained SS |",
                  "|---|---|---|---|"]
        for _, r in fx.sort_values("share", ascending=False).iterrows():
            if r.share < 0.005 and r.order > 1 and not r.signif:
                continue
            lines.append(f"| {r.term} | {r.ratio:.3f}{'' if r.signif else ' (n.s.)'} | {r.lo:.3f}-{r.hi:.3f} | "
                         f"{100 * r.share:.1f}% |")
        top = fx.sort_values("share", ascending=False)
        cum = top.share.cumsum().values
        k = int(np.searchsorted(cum, 0.9) + 1)
        lines += ["", f"{k} term(s) explain 90% of the explained variance: {', '.join(top.term.values[:k])}", ""]
        # simple effects of NT at each (BATCH, FUSE) level, SPLIT averaged
        g = d.groupby(["BATCH", "FUSE", "NT"]).t_med_ns.apply(lambda x: np.exp(np.log(x).mean())).unstack("NT")
        lines += ["NT simple effects (runtime ratio NT on / off, geometric mean over SPLIT and rounds):", "",
                  "| BATCH | FUSE | ratio |", "|---|---|---|"]
        for (b, fu), r in g.iterrows():
            lines.append(f"| {int(b)} | {int(fu)} | {r[1] / r[0]:.3f} |")
        if "read_sweeps" in d:
            tr = d.groupby(list(FACTORS))[["read_sweeps", "write_sweeps"]].median()
            lines += ["", "DRAM traffic per cell (median read + write sweeps):", "",
                      "| NT | BATCH | FUSE | SPLIT | read S | write S | GF/s |", "|---|---|---|---|---|---|---|"]
            gf = d.groupby(list(FACTORS)).gflops.median()
            for idx, r in tr.iterrows():
                lines.append("| " + " | ".join(str(int(v)) for v in idx) + f" | {r.read_sweeps:.2f} | {r.write_sweeps:.2f} | "
                             f"{gf[idx]:.2f} |")
        lines.append("")
    nts = df[df.study == "nt_lanes"]
    if len(nts):
        lines += ["## NT x strip width (fused, balanced split)", "", "| n | Bc = G | GF/s NT off | GF/s NT on | "
                  "NT ratio (on/off time) | write S off | write S on |", "|---|---|---|---|---|---|---|"]
        m = nts.groupby(["n", "Bc", "NT"]).agg(t=("t_med_ns", "median"), gf=("gflops", "median"),
                                              w=("write_sweeps", "median") if "write_sweeps" in nts else ("gflops", "size"))
        for (n, bc), r in m.groupby(level=[0, 1]):
            r = r.droplevel([0, 1])
            if len(r) < 2:
                continue
            lines.append(f"| {n} | {int(bc)} | {r.gf[0]:.2f} | {r.gf[1]:.2f} | {r.t[1] / r.t[0]:.3f} | {r.w[0]:.2f} | {r.w[1]:.2f} |")
    if allfx:
        pd.concat(allfx).to_csv(Path(a.csv).with_name(Path(a.csv).stem + "_effects.csv"), index=False)
    md = Path(a.csv).with_name(Path(a.csv).stem + "_effects.md")
    md.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    print("wrote", md)


TERMS_SHOWN = ("BATCH", "FUSE", "NT", "SPLIT", "BATCH:FUSE", "NT:FUSE", "NT:BATCH", "NT:SPLIT")


def plot(csv, out, width=7.16, height=2.6, fontsize=7):
    """(a) effects (runtime ratios, log scale, 95% CI) of the main terms per size; (b) NT effect by strip width."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.ticker
    PAL = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#4a3aa7", "#e34948"]
    INK2, GRID = "#52514e", "#e4e3df"
    plt.rcParams.update({"font.size": fontsize, "font.family": "serif", "axes.edgecolor": INK2, "axes.grid": True,
                         "grid.color": GRID, "grid.linewidth": 0.5, "axes.spines.top": False,
                         "axes.spines.right": False, "legend.frameon": False, "legend.fontsize": fontsize - 0.5,
                         "pdf.fonttype": 42, "xtick.color": INK2, "ytick.color": INK2})
    fx = pd.read_csv(Path(csv).with_name(Path(csv).stem + "_effects.csv"))
    ns = sorted(fx.n.unique())
    fig, (ax, bx) = plt.subplots(1, 2, figsize=(width, height), gridspec_kw={"width_ratios": [1.6, 1]})
    y = np.arange(len(TERMS_SHOWN))
    h = 0.8 / len(ns)
    for i, n in enumerate(ns):
        d = fx[fx.n == n].set_index("term").reindex(TERMS_SHOWN)
        yy = y - 0.4 + h * (i + 0.5)
        ax.errorbar(d.ratio, yy, xerr=[d.ratio - d.lo, d.hi - d.ratio], fmt="o", ms=3, color=PAL[i], elinewidth=0.8,
                    capsize=0, label=f"$n=2^{{{int(np.log2(n))}}}$")
    ax.axvline(1, color=INK2, lw=0.7)
    ax.set_xscale("log")
    ax.set_xticks([0.25, 0.5, 1, 2], ["0.25", "0.5", "1", "2"])
    ax.xaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
    ax.set_yticks(y, [t.replace(":", " × ") for t in TERMS_SHOWN])
    ax.invert_yaxis()
    ax.set_xlabel("runtime ratio (main: on/off; interaction: ratio of ratios); < 1 = faster")
    ax.set_title("(a) effects in the log-runtime model, 95% CI", fontsize=fontsize, loc="left")
    ax.legend(loc="lower right", ncol=1)
    df = pd.read_csv(csv)
    nts = df[df.study == "nt_lanes"]
    for i, n in enumerate(sorted(nts.n.unique())):
        m = nts[nts.n == n].groupby(["Bc", "NT"]).t_med_ns.median().unstack("NT")
        col = PAL[ns.index(n)] if n in ns else PAL[i]
        bx.plot(m.index, m[1] / m[0], marker="o", ms=3, color=col, label=f"$n=2^{{{int(np.log2(n))}}}$")
    bx.axhline(1, color=INK2, lw=0.7)
    bx.axvline(4, color=INK2, lw=0.6, ls=":")
    bx.text(4.3, bx.get_ylim()[1], "64-byte segments", fontsize=fontsize - 1, color=INK2, va="top")
    bx.set_xscale("log", base=2)
    bx.set_xticks([1, 2, 4, 8, 16, 32], ["1", "2", "4", "8", "16", "32"])
    bx.set_xlabel("strip width Bc = G (complex per segment)")
    bx.set_ylabel("time NT on / NT off")
    bx.set_title("(b) NT stores vs strip width (fused)", fontsize=fontsize, loc="left")
    bx.legend(loc="lower right")
    fig.tight_layout(pad=0.3)
    fig.savefig(out, bbox_inches="tight", dpi=200)
    plt.close(fig)
    print("wrote", out)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--n", default="2^18,2^20,2^22,2^25")
    r.add_argument("--rounds", type=int, default=3)
    r.add_argument("--mintime", type=float, default=1.0)
    r.add_argument("--seed", type=int, default=1)
    r.add_argument("--quick", action="store_true", help="sizes 2^18,2^22, one round, short runs")
    r.add_argument("--nt-study", action="store_true", help="also NT x strip width at the two largest sizes")
    r.add_argument("--fresh", action="store_true")
    r.add_argument("--out", default=str(ROOT / "results" / "factorial.csv"))
    an = sub.add_parser("analyze")
    an.add_argument("--csv", default=str(ROOT / "results" / "factorial.csv"))
    pl = sub.add_parser("plot")
    pl.add_argument("--csv", default=str(ROOT / "results" / "factorial.csv"))
    pl.add_argument("--out", default=str(ROOT / "results" / "fig_factorial.png"))
    a = ap.parse_args()
    if a.cmd == "run":
        if a.quick:
            a.n, a.rounds, a.mintime = "2^18,2^22", 2, 0.3
        run(a)
    elif a.cmd == "analyze":
        analyze(a)
    else:
        plot(a.csv, a.out)


if __name__ == "__main__":
    main()
