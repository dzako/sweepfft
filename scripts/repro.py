# SPDX-License-Identifier: GPL-2.0-or-later
"""Statistical reproducibility study with pre-specified endpoints (results/ENDPOINTS.md).

  uv run scripts/repro.py run     [--blocks 10] [--session NAME] [--quick]
  uv run scripts/repro.py analyze [--csv results/repro.csv]

run: measures blocks until --blocks blocks are complete (resumable: a later invocation, e.g. after a reboot,
adds blocks to the same files under a new session name).  A block runs every (implementation, size) once, each
in a fresh process pinned to one core; the size order is shuffled per block, the implementation order per size
is a row of a Williams Latin square.  Per run it stores the median and every sample (results/repro_samples.csv),
the planning time and plan, the effective core clock (perf cycles and ref-cycles over the timed loop, when perf
is permitted), package and core temperature before and after, the AC power state and the wall-clock time.
Failed runs are retried once in the same block; nothing is removed as an outlier.

analyze: the primary endpoints E1 (vs MKL) and E2 (vs FFTW MEASURE): geometric-mean speedup over the
memory-bound powers of two P, 95% block bootstrap interval (10,000 resamples of whole blocks), exact one-sided
sign-flip permutation test with Holm correction, and the pre-specified decision; secondary endpoints S1-S4;
noise (within-run sample spread, between-block CV) and drift (log t against block index, clock and temperature).
"""
import argparse
import io
import os
import random
import re
import subprocess
import sys
import tempfile
import time
from itertools import product
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from run_bench import CORE, parse_sizes  # noqa: E402
from mem_traffic import supported, perf_stat, PMU  # noqa: E402
from fairness import williams, nlabel  # noqa: E402
from fftw_best_wisdom import wisdom_for  # noqa: E402

BIN = ROOT / "build" / "bench_dft"
IMPLS = ["pmfft", "pmfft_heur", "mkl", "fftw_measure", "ducc"]
P_SIZES = "2^22,2^23,2^24,2^25,2^26"
Q_SIZES = "3*2^20,5*2^20,3*2^22,5*2^22"
B_BOOT, SEED_BOOT = 10000, 12345


# ------------------------------------------------------------------------------------------------ environment probes

def coretemp(cpu):
    """(package, core) temperature in deg C from hwmon (coretemp / k10temp / zenpower), NaN if unavailable."""
    try:
        core_id = int(Path(f"/sys/devices/system/cpu/cpu{cpu}/topology/core_id").read_text())
    except (OSError, ValueError):
        core_id = None
    pkg = core = np.nan
    for h in Path("/sys/class/hwmon").glob("hwmon*"):
        try:
            name = (h / "name").read_text().strip()
        except OSError:
            continue
        if name not in ("coretemp", "k10temp", "zenpower"):
            continue
        for lab in h.glob("temp*_label"):
            try:
                l = lab.read_text().strip()
                v = int((h / lab.name.replace("_label", "_input")).read_text()) / 1000
            except (OSError, ValueError):
                continue
            if l.startswith("Package") or (l in ("Tctl", "Tdie") and np.isnan(pkg)):
                pkg = v
            elif core_id is not None and l == f"Core {core_id}":
                core = v
    return pkg, core


def ac_online():
    for p in Path("/sys/class/power_supply").glob("*"):
        try:
            if (p / "type").read_text().strip() == "Mains":
                return int((p / "online").read_text())
        except (OSError, ValueError):
            pass
    return -1                                   # desktop / unknown


def clock_events():
    pre, suf = ("cpu_core/", "/") if (PMU / "cpu_core").exists() else ("", "")
    return supported([f"{pre}cycles{suf}", f"{pre}ref-cycles{suf}"])


# --------------------------------------------------------------------------------------------------------------- run

def jobs_for(sizes):
    return [(i, n) for n in sizes for i in IMPLS]


def run(a):
    out, sout = Path(a.out), Path(a.samples_out)
    rows = pd.read_csv(out).to_dict("records") if out.exists() else []
    srows = pd.read_csv(sout) if sout.exists() else pd.DataFrame()
    P = parse_sizes(a.primary)
    Q = parse_sizes(a.secondary)
    if a.quick:
        P, Q = P[:1], Q[:1]
    sizes = P + Q
    done = {(int(r["block"]), r["impl"], int(r["n"])) for r in rows}
    session = a.session or time.strftime("%Y%m%d-%H%M%S")
    ev = clock_events() if not a.no_perf else []
    W = williams(len(IMPLS))
    tl = os.environ.get("FFTW_TIMELIMIT", "60")
    wis = os.environ.get("FFTW_WISDOM_FILE") or str(ROOT / "results" / "fftw_wisdom.dat")
    print(f"cpu {CORE}; session {session}; {a.blocks} blocks x {len(sizes)} sizes x {len(IMPLS)} impls; "
          f"clock events {ev or 'none'}; temperature {coretemp(CORE)}; AC {ac_online()}; wisdom {wis} (read-only)",
          flush=True)
    new_samples = []
    with tempfile.TemporaryDirectory() as tmp:
        ctl, ack = os.path.join(tmp, "ctl"), os.path.join(tmp, "ack")
        os.mkfifo(ctl)
        os.mkfifo(ack)
        for blk in range(a.blocks):
            order = sizes[:]
            random.Random(a.seed * 1000 + blk).shuffle(order)
            for si, n in enumerate(order):
                row = W[(blk * len(sizes) + si) % len(W)]
                for pos, impl in enumerate(IMPLS[k] for k in row):
                    if (blk, impl, n) in done:
                        continue
                    for attempt in range(2):
                        r = one(impl, n, a, ev, (ctl, ack), tmp, wis, tl)
                        if r is not None:
                            break
                        print(f"FAIL b{blk} {impl} n={n} (attempt {attempt + 1})", file=sys.stderr, flush=True)
                    if r is None:
                        continue
                    r, samp = r
                    r.update(block=blk, session=session, pos=pos, size_set="P" if n in P else "Q", retry=attempt)
                    rows.append(r)
                    new_samples.append(pd.DataFrame({"block": blk, "impl": impl, "n": n, "k": range(len(samp)),
                                                     "t_ns": samp}))
                    print(f"b{blk} {impl:12s} n={n:<9d} {5 * n * np.log2(n) / r['t_med_ns']:6.2f} GF  "
                          f"{r['eff_ghz']:4.2f} GHz  {r['temp_pkg_before']:.0f}->{r['temp_pkg_after']:.0f} C  "
                          f"plan {r['plan_s']:6.2f} s  {len(samp)} samples", flush=True)
                    out.parent.mkdir(parents=True, exist_ok=True)
                    pd.DataFrame(rows).to_csv(out, index=False)
                    pd.concat([srows] + new_samples).to_csv(sout, index=False)


def one(impl, n, a, ev, ctl, tmp, wis, tl):
    env = dict(os.environ, FFTW_WISDOM_FILE=wisdom_for(n, wis), FFTW_WISDOM_RO="1", FFTW_TIMELIMIT=tl)
    cmd = ["taskset", "-c", CORE, str(BIN), "--impl", impl, "--n", str(n), "--mintime", str(a.mintime), "--samples"]
    pk0, co0 = coretemp(CORE)
    t_wall = time.time()
    vals = {}
    try:
        if ev:
            vals, so, se = perf_stat(ev, ["env"] + [f"{k}={v}" for k, v in env.items() if k.startswith("FFTW")]
                                     + cmd + ["--perf-ctl", f"{ctl[0]},{ctl[1]}"], tmp, ctl)
        else:
            p = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT, env=env)
            if p.returncode:
                return None
            so, se = p.stdout, p.stderr
    except RuntimeError:
        return None
    pk1, co1 = coretemp(CORE)
    if not so.strip():
        return None
    f = pd.read_csv(io.StringIO(so), header=None).iloc[0]
    if str(f[4]) == "nan":
        return None
    m = re.search(r"samples n=\d+ inner=(\d+) t_ns=([\d.,]+)", se)
    samp = [float(x) for x in m.group(2).split(",")] if m else []
    r = dict(impl=impl, n=n, plan_s=float(f[3]), t_med_ns=float(f[4]), t_min_ns=float(f[5]),
             n_samples=len(samp), inner=int(m.group(1)) if m else np.nan, wall_start=t_wall,
             temp_pkg_before=pk0, temp_pkg_after=pk1, temp_core_before=co0, temp_core_after=co1, ac=ac_online(),
             cpu=CORE)
    mm = re.search(r"mem n=\d+ lib_bytes=(-?\d+) plan_peak_bytes=(-?\d+) plan=(.*)", se)
    r["plan"] = mm.group(3).strip() if mm else ""
    r["fftw_capped"] = impl.startswith("fftw") and (r["plan_s"] >= 0.9 * float(tl) or search_capped(n))
    mt = re.search(r"timed_s=([\d.]+) calls=(\d+)", se)
    cyc = sum(v for k, v in vals.items() if "cycles" in k and "ref-cycles" not in k)
    ref = sum(v for k, v in vals.items() if "ref-cycles" in k)
    timed = float(mt.group(1)) if mt else np.nan
    r["eff_ghz"] = cyc / timed * 1e-9 if cyc and timed else np.nan
    r["ref_ghz"] = ref / timed * 1e-9 if ref and timed else np.nan
    return r, samp


def search_capped(n):
    """True if FFTW's wisdom for n comes from a search that hit its time limit ($FFTW_WISDOM_CHOICE, Amendment 2)."""
    p = os.environ.get("FFTW_WISDOM_CHOICE")
    if not p or not Path(p).exists():
        return False
    d = pd.read_csv(p)
    m = d[d.n == n]
    return bool(len(m) and m.iloc[0].get("search_capped", False))


# ----------------------------------------------------------------------------------------------------------- analysis

def logratios(df, s, lib, sizes):
    """Block x size table of log(t_lib / t_s) (paired within block)."""
    d = df[df.n.isin(sizes)]
    ts = d[d.impl == s].pivot(index="block", columns="n", values="t_med_ns")
    tl = d[d.impl == lib].pivot(index="block", columns="n", values="t_med_ns")
    return np.log(tl / ts)


def capped_sizes(df):
    return set(df[(df.impl == "fftw_measure") & df.fftw_capped.astype(bool)].n)


def endpoint(df, s, lib, sizes, rng=None):
    """Per-block log endpoint values (mean over sizes), estimate, bootstrap CI, one-sided sign-flip p."""
    L = logratios(df, s, lib, sizes).dropna()          # only blocks with every size present
    v = L.mean(axis=1).values
    if len(v) == 0:
        return dict(est=np.nan, lo=np.nan, hi=np.nan, p=np.nan, blocks=0, vals=v)
    rng = rng or np.random.default_rng(SEED_BOOT)
    boot = v[rng.integers(0, len(v), size=(B_BOOT, len(v)))].mean(axis=1)
    lo, hi = np.percentile(boot, [2.5, 97.5])
    obs = v.mean()
    if len(v) <= 16:                                   # exact sign-flip distribution
        signs = np.array(list(product((1, -1), repeat=len(v))))
    else:
        signs = rng.choice((1, -1), size=(100000, len(v)))
    perm = (signs * v).mean(axis=1)
    p = float(np.mean(perm >= obs - 1e-15))
    return dict(est=np.exp(obs), lo=np.exp(lo), hi=np.exp(hi), p=p, blocks=len(v), vals=v)


def holm(ps):
    order = np.argsort(ps)
    adj = np.empty(len(ps))
    run_max = 0
    for rank, i in enumerate(order):
        run_max = max(run_max, min(1.0, (len(ps) - rank) * ps[i]))
        adj[i] = run_max
    return adj


def is_amd():
    try:
        return "AuthenticAMD" in Path("/proc/cpuinfo").read_text()
    except OSError:
        return False


def analyze(a):
    df = pd.read_csv(a.csv)
    df["fftw_capped"] = df.fftw_capped.fillna(False).astype(bool)
    P = sorted(df[df.size_set == "P"].n.unique())
    Q = sorted(df[df.size_set == "Q"].n.unique())
    cap = capped_sizes(df)
    out = []
    W = out.append
    W("# Reproducibility study: pre-specified endpoints (`results/ENDPOINTS.md`)\n")
    nb = df.block.nunique()
    W(f"{nb} blocks in {df.session.nunique()} session(s) ({', '.join(map(str, df.session.unique()))}); "
      f"{len(df)} runs, {int(df.n_samples.sum())} samples; retried runs: {int((df.retry > 0).sum())}. "
      f"Sizes P = {', '.join(nlabel(n) for n in P)}; Q = {', '.join(nlabel(n) for n in Q)}. "
      f"FFTW plans capped (excluded from FFTW endpoints): {', '.join(nlabel(n) for n in sorted(cap)) or 'none'}.\n")
    P2 = [n for n in P if n not in cap]
    Q2 = [n for n in Q if n not in cap]

    W("## Primary endpoints\n")
    W("Geometric-mean speedup over P (> 1: SweepFFT faster), 95% block-bootstrap interval, one-sided exact "
      "sign-flip p-value, Holm-adjusted across E1 and E2.\n")
    e1 = endpoint(df, "pmfft", "mkl", P)
    e2 = endpoint(df, "pmfft", "fftw_measure", P2)
    adj = holm(np.array([e1["p"], e2["p"]]))
    W("| endpoint | sizes | blocks | speedup | 95% CI | p | p (Holm) | decision |")
    W("|---|---|---|---|---|---|---|---|")
    amd = is_amd()
    res = {}
    for name, e, pa, sz in (("E1 vs MKL" + (" (secondary on AMD)" if amd else ""), e1, adj[0], P),
                            ("E2 vs FFTW MEASURE", e2, adj[1], P2)):
        dec = ("faster" if e["lo"] > 1 and pa < 0.05 else
               "slower" if e["hi"] < 1 else "no detectable difference")
        res[name[:2]] = (e, pa, dec)
        W(f"| {name} | {len(sz)} | {e['blocks']} | **{e['est']:.3f}** | [{e['lo']:.3f}, {e['hi']:.3f}] | "
          f"{e['p']:.4f} | {pa:.4f} | {dec} |")
    W("")
    W("Per-block endpoint values (block order): E1 " + ", ".join(f"{np.exp(v):.3f}" for v in e1["vals"]) +
      "; E2 " + ", ".join(f"{np.exp(v):.3f}" for v in e2["vals"]) + ".\n")

    W("## Secondary endpoints\n")
    W("| endpoint | comparison | sizes | blocks | speedup | 95% CI |")
    W("|---|---|---|---|---|---|")
    for name, s, lib, sz in (("S1", "pmfft", "ducc", P), ("S2", "pmfft_heur", "mkl", P),
                             ("S2", "pmfft_heur", "fftw_measure", P2), ("S3", "pmfft", "mkl", Q),
                             ("S3", "pmfft", "fftw_measure", Q2)):
        e = endpoint(df, s, lib, sz)
        W(f"| {name} | {s} vs {lib} | {', '.join(nlabel(n) for n in sz) or '–'} | {e['blocks']} | "
          f"{e['est']:.3f} | [{e['lo']:.3f}, {e['hi']:.3f}] |")
    W("")

    W("## S4: per-size speedups (95% block-bootstrap CI) and median GFlop/s\n")
    W("| n | set | " + " | ".join(f"GF {i}" for i in IMPLS) + " | vs MKL | vs FFTW | vs ducc0 | heur vs MKL |")
    W("|" + "---|" * (6 + len(IMPLS)))
    for n in P + Q:
        d = df[df.n == n]
        gf = [f"{5 * n * np.log2(n) / d[d.impl == i].t_med_ns.median():.2f}" if (d.impl == i).any() else "–"
              for i in IMPLS]
        cells = []
        for s, lib in (("pmfft", "mkl"), ("pmfft", "fftw_measure"), ("pmfft", "ducc"), ("pmfft_heur", "mkl")):
            e = endpoint(df, s, lib, [n])
            c = f"{e['est']:.3f} [{e['lo']:.3f}, {e['hi']:.3f}]"
            cells.append(c + (" †" if lib.startswith("fftw") and n in cap else ""))
        W(f"| {nlabel(n)} | {'P' if n in P else 'Q'} | " + " | ".join(gf + cells) + " |")
    W("")

    W("## Noise\n")
    W("Within-run spread: (p75 − p25) / median of the samples of one run, median over blocks. Between-block CV: "
      "standard deviation / mean of the run medians over blocks.\n")
    sp = None
    if Path(a.samples).exists():
        s = pd.read_csv(a.samples)
        g = s.groupby(["block", "impl", "n"]).t_ns
        sp = ((g.quantile(0.75) - g.quantile(0.25)) / g.median()).groupby(["impl", "n"]).median()
    cv = df.groupby(["impl", "n"]).t_med_ns.agg(lambda x: x.std(ddof=1) / x.mean())
    W("| n | " + " | ".join(f"{i} within / between" for i in IMPLS) + " |")
    W("|" + "---|" * (1 + len(IMPLS)))
    for n in P + Q:
        cells = []
        for i in IMPLS:
            w = sp.get((i, n), np.nan) if sp is not None else np.nan
            b = cv.get((i, n), np.nan)
            cells.append(f"{100 * w:.1f}% / {100 * b:.1f}%")
        W(f"| {nlabel(n)} | " + " | ".join(cells) + " |")
    W("")

    W("## Drift\n")
    W("Slope of log t against block index (% per block, 95% CI), pooled over sizes per implementation (size "
      "fixed effects); the same for the paired log speedup of the primary comparisons; and the clock and "
      "temperature ranges.\n")
    from scipy import stats
    W("| quantity | slope %/block | 95% CI |")
    W("|---|---|---|")

    def slope(y, x, groups):
        y = pd.Series(y).reset_index(drop=True)
        x = pd.Series(x).reset_index(drop=True).astype(float)
        g = pd.Series(groups).reset_index(drop=True)
        yc = y - y.groupby(g).transform("mean")
        xc = x - x.groupby(g).transform("mean")
        b = (xc * yc).sum() / (xc ** 2).sum()
        resid = yc - b * xc
        dof = len(y) - g.nunique() - 1
        if dof <= 0 or (xc ** 2).sum() == 0:
            return np.nan, np.nan, np.nan
        se = np.sqrt((resid ** 2).sum() / dof / (xc ** 2).sum())
        h = stats.t.ppf(0.975, dof) * se
        return 100 * b, 100 * (b - h), 100 * (b + h)

    for i in IMPLS:
        d = df[df.impl == i]
        b, lo, hi = slope(np.log(d.t_med_ns), d.block, d.n)
        W(f"| t, {i} | {b:+.2f} | [{lo:+.2f}, {hi:+.2f}] |")
    for lib, sz in (("mkl", P), ("fftw_measure", P2)):
        L = logratios(df, "pmfft", lib, sz).stack().reset_index()
        L.columns = ["block", "n", "lr"]
        b, lo, hi = slope(L.lr, L.block, L.n)
        W(f"| speedup vs {lib} on P | {b:+.2f} | [{lo:+.2f}, {hi:+.2f}] |")
    W("")
    if df.eff_ghz.notna().any():
        W("Effective core clock during the timed loop (GHz), min / median / max per implementation: " +
          "; ".join(f"{i} {df[df.impl == i].eff_ghz.min():.2f} / {df[df.impl == i].eff_ghz.median():.2f} / "
                    f"{df[df.impl == i].eff_ghz.max():.2f}" for i in IMPLS) + ".\n")
        r = np.corrcoef(df.dropna(subset=["eff_ghz"]).eff_ghz,
                        np.log(df.dropna(subset=["eff_ghz"]).t_med_ns) -
                        np.log(df.dropna(subset=["eff_ghz"]).groupby(["impl", "n"]).t_med_ns.transform("median")))[0, 1]
        W(f"Correlation of effective clock with log t (relative to each implementation and size's median): {r:+.2f}.\n")
    W(f"Package temperature before runs: {df.temp_pkg_before.min():.0f}–{df.temp_pkg_before.max():.0f} °C "
      f"(median {df.temp_pkg_before.median():.0f}); after: {df.temp_pkg_after.min():.0f}–"
      f"{df.temp_pkg_after.max():.0f} °C. AC power: {sorted(int(v) for v in df.ac.dropna().unique())} (1 = on mains). "
      f"Wall-clock span: {(df.wall_start.max() - df.wall_start.min()) / 3600:.1f} h.\n")
    Path(a.md).write_text("\n".join(out))
    print("\n".join(out))
    print("wrote", a.md)
    plot(df, P, Q, P2, cap, a.fig)


def plot(df, P, Q, P2, cap, fig_out, width=7.16, height=2.8, fontsize=7):
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
    fig, axs = plt.subplots(1, 3, figsize=(width, height), gridspec_kw={"width_ratios": [1.3, 1, 1]})
    # (a) per-size speedups and the primary endpoints
    ax = axs[0]
    labels = [nlabel(n) for n in P + Q] + ["E1 / E2 (P)"]
    for j, (lib, name, col) in enumerate((("mkl", "MKL", PAL[1]), ("fftw_measure", "FFTW", PAL[2]),
                                          ("ducc", "ducc0", PAL[3]))):
        for i, n in enumerate(P + Q):
            if lib.startswith("fftw") and n in cap:
                continue
            e = endpoint(df, "pmfft", lib, [n])
            y = i + (j - 1) * 0.22
            ax.plot([e["lo"], e["hi"]], [y, y], color=col, lw=0.9)
            ax.plot([e["est"]], [y], "o", color=col, ms=3, label=name if i == 0 else None)
        if lib != "ducc":
            e = endpoint(df, "pmfft", lib, P if lib == "mkl" else P2)
            y = len(P + Q) + (j - 1) * 0.22
            ax.plot([e["lo"], e["hi"]], [y, y], color=col, lw=1.4)
            ax.plot([e["est"]], [y], "D", color=col, ms=4.5)
    ax.axvline(1, color=INK2, lw=0.8)
    ax.axhline(len(P) - 0.5, color=GRID, lw=0.8)
    ax.axhline(len(P + Q) - 0.5, color=INK2, lw=0.6)
    ax.set_yticks(range(len(labels)), labels)
    ax.invert_yaxis()
    ax.set_xscale("log")
    ax.xaxis.set_minor_formatter(NullFormatter())
    ax.set_xticks([0.8, 1, 1.25, 1.5, 2, 3], ["0.8", "1", "1.25", "1.5", "2", "3"])
    ax.set_xlabel("SweepFFT speedup, 95% block-bootstrap CI")
    ax.set_title("(a) per size and endpoints", fontsize=fontsize, loc="left")
    ax.legend(loc="upper right")
    # (b) per-block endpoint values
    ax = axs[1]
    for lib, sz, col, name in (("mkl", P, PAL[1], "E1 vs MKL"), ("fftw_measure", P2, PAL[2], "E2 vs FFTW")):
        L = logratios(df, "pmfft", lib, sz).dropna()
        ax.plot(L.index, np.exp(L.mean(axis=1)), "o-", color=col, label=name, lw=1)
    ax.axhline(1, color=INK2, lw=0.8)
    ax.set_xlabel("block")
    ax.set_xticks(range(0, int(df.block.max()) + 1, 1 if df.block.max() < 12 else 2))
    ax.set_ylabel("block endpoint value")
    ax.set_title("(b) endpoint in every block", fontsize=fontsize, loc="left")
    ax.legend(loc="best")
    # (c) clock and temperature over the study
    ax = axs[2]
    t0 = df.wall_start.min()
    h = (df.wall_start - t0) / 3600
    if df.eff_ghz.notna().any():
        ax.scatter(h, df.eff_ghz, s=4, color=PAL[0], lw=0, label="core clock (GHz)")
        ax.set_ylabel("effective clock (GHz)")
    ax2 = ax.twinx()
    ax2.scatter(h, df.temp_pkg_before, s=4, color=PAL[7], lw=0, label="package °C")
    ax2.set_ylabel("package temperature (°C)", color=PAL[7])
    ax2.spines["right"].set_visible(True)
    ax2.grid(False)
    ax.set_xlabel("hours since start")
    ax.set_title("(c) clock and temperature", fontsize=fontsize, loc="left")
    fig.tight_layout()
    fig.savefig(fig_out, bbox_inches="tight", dpi=200)
    plt.close(fig)
    print("wrote", fig_out)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--blocks", type=int, default=10, help="total number of blocks to reach")
    r.add_argument("--session", default=None)
    r.add_argument("--primary", default=P_SIZES)
    r.add_argument("--secondary", default=Q_SIZES)
    r.add_argument("--mintime", type=float, default=1.0)
    r.add_argument("--seed", type=int, default=1)
    r.add_argument("--no-perf", action="store_true")
    r.add_argument("--quick", action="store_true", help="one size of each set")
    r.add_argument("--out", default=str(ROOT / "results" / "repro.csv"))
    r.add_argument("--samples-out", default=str(ROOT / "results" / "repro_samples.csv"))
    z = sub.add_parser("analyze")
    z.add_argument("--csv", default=str(ROOT / "results" / "repro.csv"))
    z.add_argument("--samples", default=str(ROOT / "results" / "repro_samples.csv"))
    z.add_argument("--md", default=str(ROOT / "results" / "repro.md"))
    z.add_argument("--fig", default=str(ROOT / "results" / "fig_repro.png"))
    a = ap.parse_args()
    run(a) if a.cmd == "run" else analyze(a)


if __name__ == "__main__":
    main()
