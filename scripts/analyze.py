# SPDX-License-Identifier: GPL-2.0-or-later
"""Turn results/*.csv into ablation tables (markdown) and figures (PNG) for the report.

Usage: uv run scripts/analyze.py      -> results/tables.md, results/fig_*.png
"""
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_bench import summarize  # noqa: E402

R = Path(__file__).resolve().parent.parent / "results"
# validated reference categorical palette (light), fixed order
PAL = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#4a3aa7", "#e34948"]
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"
plt.rcParams.update({"font.size": 10, "axes.edgecolor": INK2, "axes.labelcolor": INK, "xtick.color": INK2,
                     "ytick.color": INK2, "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6,
                     "axes.spines.top": False, "axes.spines.right": False, "lines.linewidth": 2,
                     "legend.frameon": False, "figure.dpi": 130})
out_md = []


def md(title, df, floatfmt=".3g"):
    out_md.append(f"\n### {title}\n")
    out_md.append(df.to_markdown(floatfmt=floatfmt))
    out_md.append("")


def load(name):
    p = R / name
    return summarize(pd.read_csv(p)) if p.exists() else None


def log2n(n):
    return np.log2(n.astype(float))


def lineplot(ax, df, key, label_map=None, order=None):
    keys = order or list(dict.fromkeys(df[key]))
    for i, k in enumerate(keys):
        d = df[df[key] == k].sort_values("n")
        ax.plot(log2n(d.n), d.mflops / 1e3, marker="o", ms=4, color=PAL[i % len(PAL)],
                label=label_map.get(k, k) if label_map else k)
    ax.set_xlabel("log2 n")
    ax.set_ylabel("GFlop/s (5 n log2 n / t)")


def fig_I2_I10():
    d = load("abl_I2_I10.csv")
    if d is None:
        return
    d["rmax"] = d.params.str.extract(r"rmax=(\d+)")[0].astype(int)
    d["mode"] = d.params.str.extract(r"mode=(\d)")[0].astype(int)
    fig, ax = plt.subplots(1, 2, figsize=(10, 3.8))
    a = d[d["mode"] == 0].copy()
    a["k"] = "radix " + a.rmax.astype(str)
    lineplot(ax[0], a, "k", order=[f"radix {r}" for r in [2, 4, 8, 16, 32]])
    ax[0].set_title("I2  levels fused per sweep (opt codelets)", loc="left", fontsize=10)
    ax[0].legend(fontsize=8)
    b = d[d.rmax == 8].copy()
    b["k"] = b["mode"].map({0: "opt (CSE + trivial twiddles)", 1: "plain (CSE only)", 2: "naive (dense R x R)"})
    lineplot(ax[1], b, "k", order=["opt (CSE + trivial twiddles)", "plain (CSE only)", "naive (dense R x R)"])
    ax[1].set_title("I10  codelet circuit, radix 8", loc="left", fontsize=10)
    ax[1].legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(R / "fig_I2_I10.png")
    md("I2/I10 GFlop/s (Stockham; rows mode/rmax)", d.pivot_table(index=["mode", "rmax"], columns="n", values="mflops").div(1e3), ".1f")
    md("I6 accuracy: relative RMS error x1e16 (rows mode/rmax)",
       d[d.n <= 2 ** 20].pivot_table(index=["mode", "rmax"], columns="n", values="rms_err").mul(1e16), ".2f")


def fig_rec4():
    names = [("I3_batch", "Bc"), ("I4_split", "split"), ("I5_budget", "budget"), ("nt", "nt"), ("pad", "pad"), ("leafradix", "rmax")]
    have = [(f, k) for f, k in names if (R / f"abl_rec4_{f}.csv").exists()]
    if not have:
        return
    fig, axs = plt.subplots(2, 3, figsize=(12, 6.5))
    for ax, (f, k) in zip(axs.flat, have):
        d = load(f"abl_rec4_{f}.csv")
        d["v"] = d.params.str.extract(rf"(?:^|,){k}=([^,]+)")[0]
        lineplot(ax, d, "v", label_map={v: f"{k}={v}" for v in d.v.unique()})
        ax.set_title(f"rec4 ablation: {f}", loc="left", fontsize=10)
        ax.legend(fontsize=8)
        md(f"rec4 one-factor-at-a-time: {f} (GFlop/s)", d.pivot_table(index="v", columns="n", values="mflops").div(1e3), ".1f")
    for ax in list(axs.flat)[len(have):]:
        ax.axis("off")
    fig.tight_layout()
    fig.savefig(R / "fig_rec4_ablation.png")


def fig_I1():
    parts = [load(f) for f in ["abl_I1_sixstep.csv", "abl_I1_stockham.csv", "base_pow2_ext.csv", "abl_rec4_nt.csv"]]
    parts = [p for p in parts if p is not None]
    if not parts:
        return
    d = pd.concat(parts)
    d = d[~((d.impl == "rec4") & ~d.params.str.contains("nt=1"))]
    d["k"] = d.impl + np.where(d.params.str.contains("nt=1") & (d.impl == "sixstep"), " (NT)", "")
    fig, ax = plt.subplots(figsize=(6.5, 4))
    lineplot(ax, d, "k")
    ax.set_title("I1  explicit transposes (six-step) vs fused (rec4)", loc="left", fontsize=10)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(R / "fig_I1.png")
    md("I1 GFlop/s", d.pivot_table(index="k", columns="n", values="mflops").div(1e3), ".1f")
    t = R / "abl_I1toy_I14_transpose.csv"
    if t.exists():
        tt = pd.read_csv(t)
        md("I1-toy / I14 transposes (GB/s read+write)", tt.pivot_table(index=["test", "variant"], columns="shape", values="GBps_rw"), ".1f")


def fig_I7():
    g = load("abl_I7_gauss.csv")
    b = load("abl_I7_blurad.csv")
    e = load("abl_I7_ext.csv")
    if g is None or b is None:
        return
    errf = R / "abl_I7_gauss_err.csv"
    if errf.exists():
        ee = pd.read_csv(errf, header=None, names="impl,params,n,plan_s,t_med_ns,t_min_ns,mflops,rms_err,max_err,reps".split(","))
        errmap = ee[ee.n == 1000003].set_index("params").rms_err
    else:
        errmap = g[g.n == 1000003].set_index("params").rms_err
    fig, ax = plt.subplots(1, 2, figsize=(11, 4))
    for i, n in enumerate([1000003, 16000057]):
        ref = b[(b.n == n) & (b.impl == "bluestein") & (b.params == "pow2=0")].t_med_ns.values[0]
        gg = g[g.n == n].copy()
        gg["err"] = gg.params.map(errmap)
        gg["speedup"] = ref / gg.t_med_ns
        ax[i].scatter(gg.err, gg.speedup, s=28, color=PAL[0], label="Gaussian resampling (L, delta, iters grid)", zorder=3)
        others = pd.concat([b[b.n == n], e[e.n == n]]) if e is not None else b[b.n == n]
        for j, (_, r) in enumerate(others.iterrows()):
            err = r.rms_err if not np.isnan(r.rms_err) else 1e-15
            ax[i].scatter([err], [ref / r.t_med_ns], s=40, marker="D", color=PAL[1 + j % 7],
                          label=f"{r.impl} {r.params}".strip(), zorder=4)
        ax[i].set_xscale("log")
        ax[i].set_xlabel("relative RMS error (n = 1000003 measurement)")
        ax[i].set_ylabel("speed-up vs our Bluestein")
        ax[i].set_title(f"I7  prime n = {n}", loc="left", fontsize=10)
    ax[0].legend(fontsize=7, loc="upper right")
    fig.tight_layout()
    fig.savefig(R / "fig_I7_pareto.png")
    allp = pd.concat([x for x in [g, b, e] if x is not None])
    allp["label"] = allp.impl + " " + allp.params
    tab = allp.pivot_table(index="label", columns="n", values="t_med_ns").div(1e6)
    tab["err@1000003"] = [errmap.get(l.split(" ", 1)[1], np.nan) if l.startswith("gauss") else
                          allp[(allp.label == l) & (allp.n == 1000003)].rms_err.mean() for l in tab.index]
    md("I7 prime-length DFT time (ms) and error", tab.sort_values(1000003), ".3g")


def fig_I9():
    p = R / "abl_I9_conv.csv"
    if not p.exists():
        return
    d = pd.read_csv(p)
    s = d.groupby(["variant", "n"]).agg(t=("t_med_ns", "median"), err=("rel_err", "max")).reset_index()
    base = s[s.variant == "mkl"].set_index("n").t
    s["vs_mkl"] = s.apply(lambda r: base[r.n] / r.t, axis=1)
    fig, ax = plt.subplots(figsize=(6.5, 4))
    for i, v in enumerate(["mkl", "fftw_measure", "ours_natural", "ours_fused3"]):
        x = s[s.variant == v].sort_values("n")
        ax.plot(np.log2(x.n), x.vs_mkl, marker="o", ms=4, color=PAL[i], label=v)
    ax.set_xlabel("log2 n")
    ax.set_ylabel("speed relative to MKL (higher = faster)")
    ax.set_title("I9  cyclic convolution: transposed spectrum, 3 fused sweeps", loc="left", fontsize=10)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(R / "fig_I9_conv.png")
    md("I9 convolution: time (ms)", s.pivot_table(index="variant", columns="n", values="t").div(1e6), ".3g")
    md("I9 convolution: speed vs MKL", s.pivot_table(index="variant", columns="n", values="vs_mkl"), ".2f")


def fig_I8():
    p = R / "abl_I8_2d.csv"
    if not p.exists():
        return
    d = pd.read_csv(p)
    s = d.groupby(["variant", "N"]).agg(mflops=("mflops", "median"), err=("rel_err", "max")).reset_index()
    md("I8 2-D DFT N x N (GFlop/s)", s.pivot_table(index="variant", columns="N", values="mflops").div(1e3), ".1f")


def fig_I15():
    d = load("abl_I15_pfa.csv")
    if d is None:
        return
    md("I15 PFA vs mixed radix (GFlop/s)", d.pivot_table(index="impl", columns="n", values="mflops").div(1e3), ".1f")
    md("I15 accuracy (rel RMS)", d.pivot_table(index="impl", columns="n", values="rms_err"), ".2e")


def fig_final():
    d = load("final_pow2.csv")
    if d is None:
        return
    pt = load("final_pow2_patient.csv")
    if pt is not None:
        d = pd.concat([d, pt])
    fig, ax = plt.subplots(figsize=(7.5, 4.2))
    lineplot(ax, d, "impl", order=["pmfft", "mkl", "fftw_patient", "fftw_measure", "ducc"])
    ax.set_title("Final: complex DFT, single core, powers of two", loc="left", fontsize=10)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(R / "fig_final_pow2.png")
    md("Final comparison, powers of two (GFlop/s)", d.pivot_table(index="impl", columns="n", values="mflops").div(1e3), ".1f")
    for f, title in [("final_smooth.csv", "Final comparison, smooth composite n (GFlop/s)"),
                     ("final_prime.csv", "Final comparison, prime n (GFlop/s)"),
                     ("final_prime_fast.csv", "pmfft fast mode (Gaussian resampling, L=3) on primes (GFlop/s)"),
                     ("final_prime_fast_L4.csv", "pmfft fast mode (Gaussian resampling, L=4, delta=0.4, 1 iter) on primes (GFlop/s)"),
                     ("final_pow2_patient.csv", "FFTW_PATIENT, powers of two (GFlop/s)")]:
        x = load(f)
        if x is not None:
            md(title, x.pivot_table(index=["impl", "params"], columns="n", values="mflops").div(1e3), ".2f")
            if x.rms_err.notna().any():
                md(title.replace("(GFlop/s)", "(rel RMS error)"), x.pivot_table(index=["impl", "params"], columns="n", values="rms_err"), ".2e")


if __name__ == "__main__":
    for f in [fig_I2_I10, fig_rec4, fig_I1, fig_I7, fig_I9, fig_I8, fig_I15, fig_final]:
        try:
            f()
        except Exception as ex:  # keep going: partial results are still useful
            print(f"{f.__name__}: {ex!r}")
    (R / "tables.md").write_text("\n".join(out_md))
    print("wrote", R / "tables.md")
