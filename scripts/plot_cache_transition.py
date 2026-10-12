# SPDX-License-Identifier: GPL-2.0-or-later
"""Figure for the cache-capacity transition experiment (scripts/cache_transition.py).

(a) phase diagram: every measured size placed by its data working set W = 32 n bytes (x) and the odd part of n
    (y, its factorization class); the cell colour is the fastest implementation, the number is SweepFFT's
    speed relative to the fastest other library (bold where SweepFFT wins); † = FFTW's planner hit its time
    limit at that size, so FFTW is left out of that cell (its plan is truncated);
(b) SweepFFT speedup over MKL and FFTW against W (all sizes);
(c) DRAM traffic per transform (read + write, in sweeps S = 16 n bytes);
(d) resident memory each implementation adds beyond its input and output (plan, twiddles, scratch), in S.
Dotted lines: per-core L2 and the shared LLC, and 2, 4, 8 x LLC.
"""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import numpy as np
import pandas as pd

PAL = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#4a3aa7", "#e34948"]
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"
IMPLS = ("pmfft", "mkl", "fftw_measure", "ducc")
COLOR = {"pmfft": PAL[0], "mkl": PAL[1], "fftw_measure": PAL[2], "ducc": PAL[3]}
MARK = {"pmfft": "o", "mkl": "s", "fftw_measure": "^", "ducc": "D"}
NAME = {"pmfft": "SweepFFT", "mkl": "MKL", "fftw_measure": "FFTW", "ducc": "ducc0"}


def winners(s):
    """Per n: fastest implementation and SweepFFT speed / fastest other (capped FFTW plans excluded)."""
    ok = s[~(s.impl.str.startswith("fftw") & s.fftw_capped)]
    t = ok.pivot(index="n", columns="impl", values="t_med_ns")
    w = pd.DataFrame({"n": t.index, "winner": t.idxmin(axis=1).values})
    others = t.drop(columns="pmfft")
    w["ratio"] = (others.min(axis=1) / t["pmfft"]).values
    w["vs_mkl"] = (t["mkl"] / t["pmfft"]).values if "mkl" in t else np.nan
    w["vs_fftw"] = (t["fftw_measure"] / t["pmfft"]).values if "fftw_measure" in t else np.nan
    w["odd"] = [n // (n & -n) for n in w.n]
    cap = s[s.impl.str.startswith("fftw") & s.fftw_capped].n
    w["fftw_capped"] = w.n.isin(cap).values
    w["W"] = 32.0 * w.n
    return w


def thresholds(s):
    l2, llc = s.l2_bytes.dropna().iloc[0], s.llc_bytes.dropna().iloc[0]
    return [(l2, "L2"), (llc, "LLC"), (2 * llc, "2×"), (4 * llc, "4×"), (8 * llc, "8×")]


def vlines(ax, th, label=False, ytxt=None):
    for b, lab in th:
        ax.axvline(np.log2(b / 2**20), color=INK2, lw=0.6, ls=":", zorder=0)
        if label:
            ax.text(np.log2(b / 2**20), ytxt, lab, color=INK2, fontsize=6.5, ha="center", va="bottom")


def mb_axis(ax, lo, hi):
    """x axis in log2 MB with tick labels in MB."""
    ax.set_xlim(lo, hi)
    t = np.arange(np.ceil(lo), np.floor(hi) + 1, 2)
    ax.set_xticks(t, [f"{2.0**v:g}" for v in t])


def binned(x, y, width=0.5):
    """Median of y in bins of `width` in x (x already log2)."""
    b = np.round(np.asarray(x) / width) * width
    d = pd.DataFrame({"b": b, "y": y}).groupby("b").y.median()
    return d.index.values, d.values


def plot(s, out, width=7.16, height=5.0, fontsize=7):
    plt.rcParams.update({"font.size": fontsize, "font.family": "serif", "axes.edgecolor": INK2,
                         "axes.labelcolor": INK, "xtick.color": INK2, "ytick.color": INK2, "axes.grid": True,
                         "grid.color": GRID, "grid.linewidth": 0.5, "axes.spines.top": False,
                         "axes.spines.right": False, "lines.linewidth": 1.4, "lines.markersize": 3,
                         "legend.frameon": False, "legend.fontsize": fontsize - 0.5, "pdf.fonttype": 42})
    th = thresholds(s)
    w = winners(s)
    fig = plt.figure(figsize=(width, height))
    gs = fig.add_gridspec(2, 3, height_ratios=[1.25, 1], hspace=0.6, wspace=0.32)
    ax = fig.add_subplot(gs[0, :])
    odds = sorted(w.odd.unique())
    xlo = np.log2(min(w.W.min(), th[0][0]) / 2**20) - 0.4
    xhi = np.log2(max(w.W.max(), th[-1][0]) / 2**20) + 0.4
    for _, r in w.iterrows():
        x, y = np.log2(r.W / 2**20), odds.index(r.odd)
        ax.add_patch(plt.Rectangle((x - 0.17, y - 0.38), 0.34, 0.76, color=COLOR[r.winner], lw=0,
                                   alpha=1.0 if r.winner == "pmfft" else 0.85))
        lab = (f"{r.ratio:.2f}"[1:] if r.ratio < 1 else f"{r.ratio:.2f}") + ("†" if r.fftw_capped else "")
        ax.text(x, y, lab, ha="center", va="center",
                fontsize=fontsize - 2.6, color="white" if r.winner in ("pmfft", "fftw_measure") else INK,
                fontweight="bold" if r.winner == "pmfft" else "normal")
    mb_axis(ax, xlo, xhi)
    ax.set_ylim(-0.6, len(odds) - 0.4 + 0.6)
    ax.set_yticks(range(len(odds)), ["$2^a$" if m == 1 else f"${m}\\cdot 2^a$" for m in odds])
    ax.grid(False)
    vlines(ax, th, label=True, ytxt=len(odds) - 0.45)
    ax.set_xlabel("data working set $W = 32n$ (MB, log scale)")
    ax.set_title("(a) fastest per size; number = SweepFFT speed / best other",
                 fontsize=fontsize, loc="left", color=INK)
    present = [i for i in IMPLS if i in set(w.winner)]
    ax.legend(handles=[Patch(color=COLOR[i], label=NAME[i] + " fastest") for i in present],
              loc="upper right", bbox_to_anchor=(1, -0.17), ncol=len(present), borderaxespad=0.2)

    lw = np.log2(w.W / 2**20)
    ax = fig.add_subplot(gs[1, 0])
    for col, impl in (("vs_mkl", "mkl"), ("vs_fftw", "fftw_measure")):
        ax.scatter(lw, w[col], s=5, color=COLOR[impl], alpha=0.45, lw=0)
        bx, by = binned(lw[w[col].notna()], w[col].dropna())
        ax.plot(bx, by, color=COLOR[impl], label=f"vs {NAME[impl]}")
    ax.axhline(1, color=INK2, lw=0.7)
    vlines(ax, th)
    mb_axis(ax, xlo, xhi)
    ax.set_xlabel("W (MB)")
    ax.set_ylabel("SweepFFT speedup")
    ax.set_title("(b) speedup (median per ½ octave)", fontsize=fontsize, loc="left")
    ax.legend(loc="upper left")

    ax = fig.add_subplot(gs[1, 1])
    if "read_sweeps" not in s:   # no DRAM counters (e.g. containers without perf)
        ax.text(0.5, 0.5, "no DRAM counters on this machine", ha="center", va="center", transform=ax.transAxes)
    for impl in (IMPLS if "read_sweeps" in s else []):
        d = s[(s.impl == impl)].dropna(subset=["read_sweeps"])
        if d.empty:
            continue
        x = np.log2(d.ws_bytes / 2**20)
        bx, by = binned(x, d.read_sweeps + d.write_sweeps)
        ax.plot(bx, by, color=COLOR[impl], marker=MARK[impl], label=NAME[impl])
    ax.axhline(4, color=INK2, lw=0.6, ls="--")
    vlines(ax, th)
    mb_axis(ax, xlo, xhi)
    ax.set_xlabel("W (MB)")
    ax.set_ylabel("DRAM read+write (S)")
    ax.set_title("(c) DRAM traffic per transform", fontsize=fontsize, loc="left")
    ax.legend(loc="upper left")

    ax = fig.add_subplot(gs[1, 2])
    for impl in IMPLS:
        d = s[s.impl == impl]
        x = np.log2(d.ws_bytes / 2**20)
        bx, by = binned(x, d.lib_bytes / (16.0 * d.n))
        ax.plot(bx, by, color=COLOR[impl], marker=MARK[impl], label=NAME[impl])
    vlines(ax, th)
    mb_axis(ax, xlo, xhi)
    ax.set_xlabel("W (MB)")
    ax.set_ylabel("extra resident memory (S)")
    ax.set_title("(d) memory beyond in/out arrays", fontsize=fontsize, loc="left")
    fig.savefig(out, bbox_inches="tight", dpi=200)
    plt.close(fig)
    print("wrote", out)
