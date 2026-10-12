# SPDX-License-Identifier: GPL-2.0-or-later
"""Summarise results/machines/<label>/ directories (written by scripts/run_machine.sh).

  uv run scripts/compare_machines.py            # writes <label>/summary.md and results/machines/COMPARISON.md

Speeds are GFlop/s = 5 n log2 n / t (t = median over rounds of per-run medians); ratios > 1 mean pmfft is faster.
"""
import re
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
MDIR = ROOT / "results" / "machines"
NAMES = {"pmfft": "pmfft", "pmfft_heur": "pmfft_heur", "mkl": "MKL", "fftw_measure": "FFTW", "ducc": "ducc0"}


def fftw_limit(d):
    """FFTW planning cap of a run (machine.txt 'fftw_timelimit:', default 60 s)."""
    p = d / "machine.txt"
    m = re.search(r"fftw_timelimit:\s*([\d.]+)", p.read_text()) if p.exists() else None
    return float(m.group(1)) if m else 60.0


def fftw_capped(df, limit):
    """Sizes where FFTW MEASURE planning hit the time cap (in any round): the plan is truncated."""
    d = df[(df.impl == "fftw_measure") & (df.plan_s >= 0.98 * limit)]
    return sorted(int(n) for n in d.n.unique())


def choice_capped(d):
    """Sizes whose planned-ahead FFTW search hit its cap (fftw_wisdom_choice.csv, scripts/fftw_plan_ahead.py)."""
    p = d / "fftw_wisdom_choice.csv"
    if not p.exists():
        return set()
    c = pd.read_csv(p)
    return {int(n) for n in c[c.search_capped.astype(bool)].n}


def gf(df):
    """impl x n table of GFlop/s from a run_bench CSV (median time over rounds)."""
    df = df.copy()
    df["params"] = df["params"].fillna("").astype(str)
    t = df.groupby(["impl", "params", "n"]).t_med_ns.median().reset_index()
    t["gf"] = 5 * t.n * np.log2(t.n) / t.t_med_ns
    return t


def load(d, name):
    p = d / name
    return pd.read_csv(p) if p.exists() and p.stat().st_size > 0 else None


def fmt_n(n):
    n = int(n)
    if n & (n - 1) == 0:
        return f"2^{n.bit_length() - 1}"
    for k in range(30, 0, -1):
        if n % (1 << k) == 0 and n >> k in (3, 5, 7):
            return f"{n >> k}·2^{k}"
    return f"{n:,}".replace(",", " ")


def md(df, floatfmt="{:.2f}"):
    cols = list(df.columns)
    out = ["| " + " | ".join(map(str, cols)) + " |", "|" + "---|" * len(cols)]
    for _, r in df.iterrows():
        out.append("| " + " | ".join(floatfmt.format(v) if isinstance(v, (float, np.floating)) and not pd.isna(v)
                                     else ("—" if pd.isna(v) else str(v)) for v in r) + " |")
    return "\n".join(out)


def machine_info(d):
    info = {"label": d.name, "cpu": "?", "cores": "?", "mem": "?"}
    p = d / "machine.txt"
    if p.exists():
        txt = p.read_text()
        m = re.search(r"Model name:\s*(.+)", txt)
        info["cpu"] = m.group(1).strip() if m else "?"
        sock = re.search(r"Socket\(s\):\s*(\d+)", txt)
        cps = re.search(r"Core\(s\) per socket:\s*(\d+)", txt)
        if sock and cps:
            info["cores"] = f"{int(sock.group(1))}×{cps.group(1)}"
        m = re.search(r"mem_total_gib:\s*(\S+)", txt)
        info["mem"] = f"{m.group(1)} GiB" if m else "?"
    return info


def speed_table(t, impls, sizes=None):
    t = t[t.params == ""]
    p = t.pivot_table(index="n", columns="impl", values="gf")
    p = p[[c for c in impls if c in p.columns]]
    if sizes is not None:
        p = p[p.index.isin(sizes)]
    for c in p.columns:
        if c not in ("pmfft", "pmfft_heur") and "pmfft" in p.columns:
            p[f"pmfft/{NAMES[c]}"] = p["pmfft"] / p[c]
    if "pmfft_heur" in p.columns and "mkl" in p.columns:
        p["heur/MKL"] = p["pmfft_heur"] / p["mkl"]
    p = p.rename(columns=NAMES).reset_index()
    p["n"] = p["n"].map(fmt_n)
    return p


def summarize_machine(d):
    info = machine_info(d)
    lines = [f"# {info['label']}: {info['cpu']} ({info['cores']} cores, {info['mem']})", "",
             "GFlop/s (5 n log2 n / t), single core; ratio > 1 = pmfft faster.", ""]
    res = {"info": info, "capped": set()}
    impls = ["pmfft", "pmfft_heur", "mkl", "fftw_measure", "ducc"]
    for name, title in [("final_pow2.csv", "Powers of two"), ("final_smooth.csv", "Smooth composite sizes"),
                        ("final_prime.csv", "Prime sizes (exact)")]:
        df = load(d, name)
        if df is None:
            continue
        t = gf(df)
        res[name] = t
        tab = speed_table(t, impls)
        if name == "final_prime.csv":
            fast = load(d, "final_prime_fast.csv")
            if fast is not None:
                f = gf(fast)
                f = f[f.impl == "pmfft"].groupby("n").gf.max()
                res["fast"] = f
                tab.insert(1, "pmfft fast (~3e-14)", tab["n"].map({fmt_n(k): v for k, v in f.items()}))
        lines += [f"## {title}", "", md(tab), ""]
        cap = sorted(set(fftw_capped(df, fftw_limit(d))) | (choice_capped(d) & {int(n) for n in df.n.unique()}))
        res["capped"] |= set(cap)
        if cap:
            lines += [f"**FFTW planning hit its time cap ({fftw_limit(d):g} s in the run"
                      + (", or the plan-ahead cap" if choice_capped(d) else "") + ") at n = " + ", ".join(fmt_n(n) for n in cap) +
                      "**: its plan there is truncated, so the FFTW numbers (and pmfft/FFTW ratios) at these sizes "
                      "are not representative.", ""]
        errs = df[df["round"] == 0].groupby("impl").rms_err.max()
        lines += ["max rms rel. error: " + ", ".join(f"{NAMES.get(i, i)} {e:.1e}" for i, e in errs.items() if not pd.isna(e)), ""]
    conv = load(d, "conv.csv")
    if conv is not None:
        c = conv.groupby(["variant", "n"]).t_med_ns.median().unstack(0)
        res["conv"] = c
        tab = pd.DataFrame({"n": [fmt_n(n) for n in c.index]})
        for v in c.columns:
            tab[f"{v} ms"] = (c[v] / 1e6).values
        if "ours_fused3" in c.columns and "mkl" in c.columns:
            tab["fused3 vs MKL"] = (c["mkl"] / c["ours_fused3"]).values
        if "ours_fused3" in c.columns and "fftw_measure" in c.columns:
            tab["fused3 vs FFTW"] = (c["fftw_measure"] / c["ours_fused3"]).values
        lines += ["## Cyclic convolution (forward + pointwise + inverse), time per convolution", "", md(tab), ""]
    sc = load(d, "scale_mp.csv")
    if sc is not None:
        sc["gf"] = sc.mflops / 1e3
        a = sc.groupby(["n", "k", "impl", "round"]).gf.sum().groupby(["n", "k", "impl"]).median().unstack("impl")
        res["scale"] = a
        a = a[[c for c in impls if c in a.columns]]
        for c in a.columns:
            if c != "pmfft":
                a[f"pmfft/{NAMES[c]}"] = a["pmfft"] / a[c]
        a = a.rename(columns=NAMES).reset_index()
        a["n"] = a["n"].map(fmt_n)
        lines += ["## Multi-process bandwidth scaling (k concurrent single-thread processes, aggregate GFlop/s)", "",
                  md(a, "{:.2f}"), ""]
    smt = load(d, "scale_mt.csv")
    if smt is not None and len(smt):
        smt["gf"] = smt.mflops / 1e3
        a = smt.groupby(["n", "threads", "impl"]).gf.median().unstack("impl")
        cap = smt[smt.get("fftw_capped", False) == True][["n", "threads"]].drop_duplicates()
        capped_mt = set(zip(cap.n, cap.threads))
        res["scale_mt"], res["capped_mt"] = a, capped_mt
        a = a[[c for c in ("pmfft_mt", "mkl", "fftw_measure") if c in a.columns]].copy()
        if "mkl" in a.columns:
            a["pmfft_mt/MKL"] = a["pmfft_mt"] / a["mkl"]
        if "fftw_measure" in a.columns:
            a["pmfft_mt/FFTW"] = [np.nan if (n, t) in capped_mt else v
                                  for (n, t), v in (a["pmfft_mt"] / a["fftw_measure"]).items()]
        a = a.rename(columns=NAMES).reset_index()
        a["n"] = a["n"].map(fmt_n)
        lines += ["## Multithreaded (one process, T OpenMP threads, all libraries threaded), GFlop/s", "",
                  "pmfft_mt/FFTW is left empty where FFTW planning hit its time cap for that (n, T).", "",
                  md(a, "{:.2f}"), ""]
    tmt = load(d, "mem_traffic_mt.csv")
    if tmt is not None and len(tmt) and "uncalibrated" not in str(tmt.dram_kind.iloc[-1]):
        tmt = tmt[tmt.n > 0]
        g = tmt.groupby(["n", "impl"]).agg(R=("read_sweeps", "median"), W=("write_sweeps", "median"))
        tab = (g.R + g.W).unstack("impl").rename(columns=NAMES).reset_index()
        tab["n"] = tab["n"].map(fmt_n)
        lines += [f"## DRAM traffic per transform, {int(tmt.threads.iloc[-1])} threads (sweeps S = 16 n bytes, read + write)",
                  "", md(tab), ""]
    mt = load(d, "mem_traffic.csv")
    if mt is not None and len(mt):
        mt["params"] = mt["params"].fillna("").astype(str)
        mt["label"] = mt.impl + mt.params.str.extract(r"(nt=\d)", expand=False).fillna("").radd(" ").str.rstrip()
        g = mt.groupby(["n", "label"]).agg(R=("read_sweeps", "median"), W=("write_sweeps", "median"),
                                          gbps=("dram_GBps", "median")).reset_index()
        g["RW"] = g.R + g.W.fillna(0)
        res["traffic"] = g
        tab = g.pivot(index="n", columns="label", values="RW")
        tab = tab.rename(columns=NAMES).reset_index()
        tab["n"] = tab["n"].map(fmt_n)
        kind = mt.dram_kind.iloc[-1]
        if "uncalibrated" in kind:
            res.pop("traffic", None)
            lines += ["## DRAM traffic per transform", "",
                      f"Counters ({kind}) failed the calibration kernels: no traffic numbers are reported for this "
                      "machine (raw values in mem_traffic.csv).", ""]
            (d / "summary.md").write_text("\n".join(lines))
            return res
        lines += ["## DRAM traffic per transform (hardware counters), in sweeps S = 16 n bytes (read + write)", "",
                  f"counter source: {kind}" + (" (AMD data fabric: read + write combined)" if kind == "amd_df" else ""), "",
                  md(tab), ""]
    (d / "summary.md").write_text("\n".join(lines))
    return res


def pick(t, impl, n):
    if t is None:
        return np.nan
    v = t[(t.impl == impl) & (t.n == n) & (t.params == "")].gf
    return float(v.iloc[0]) if len(v) else np.nan


def main():
    # quick / smoke-test runs get their own summary.md but are left out of the cross-machine table
    dirs = sorted(p for p in MDIR.iterdir() if p.is_dir()) if MDIR.exists() else []
    for d in [d for d in dirs if d.name.endswith("-quick") or d.name.startswith("smoketest")]:
        summarize_machine(d)
    dirs = [d for d in dirs if not (d.name.endswith("-quick") or d.name.startswith("smoketest"))]
    rows_gf, rows_mkl, rows_fftw, rows_other, rows_scale, rows_traffic, rows_mt = [], [], [], [], [], [], []
    for d in dirs:
        r = summarize_machine(d)
        lab = f"{d.name} ({r['info']['cpu']})"
        p2 = r.get("final_pow2.csv")
        g, vm, vf = {"machine": lab}, {"machine": lab}, {"machine": lab}
        for k in (12, 16, 20, 22, 24, 26):
            n = 2**k
            g[f"2^{k}"] = pick(p2, "pmfft", n)
            vm[f"2^{k}"] = pick(p2, "pmfft", n) / pick(p2, "mkl", n)
            vf[f"2^{k}"] = np.nan if n in r["capped"] else pick(p2, "pmfft", n) / pick(p2, "fftw_measure", n)
        rows_gf.append(g); rows_mkl.append(vm); rows_fftw.append(vf)
        sm, pr = r.get("final_smooth.csv"), r.get("final_prime.csv")
        o = {"machine": lab}
        for n in (1000000, 3 * 2**20, 10000000):
            o[f"smooth {fmt_n(n)} vs MKL"] = pick(sm, "pmfft", n) / pick(sm, "mkl", n)
        fast = r.get("fast")
        for n in (1000003, 4000037):
            o[f"prime {fmt_n(n)} exact vs MKL"] = pick(pr, "pmfft", n) / pick(pr, "mkl", n)
            o[f"prime {fmt_n(n)} fast vs MKL"] = (fast.get(n, np.nan) if fast is not None else np.nan) / pick(pr, "mkl", n)
        c = r.get("conv")
        for k in (22, 24):
            o[f"conv 2^{k} vs MKL"] = (c.loc[2**k, "mkl"] / c.loc[2**k, "ours_fused3"]) if c is not None and 2**k in c.index else np.nan
        rows_other.append(o)
        t = r.get("traffic")
        if t is not None:
            for n in sorted(t.n.unique()):
                tt = t[t.n == n].set_index("label").RW
                rows_traffic.append({"machine": lab, "n": fmt_n(n), "pmfft_heur S": tt.get("pmfft_heur", np.nan),
                                     "pmfft S": tt.get("pmfft", np.nan), "MKL S": tt.get("mkl", np.nan),
                                     "FFTW S": tt.get("fftw_measure", np.nan), "ducc0 S": tt.get("ducc", np.nan),
                                     "MKL / heur": tt.get("mkl", np.nan) / tt.get("pmfft_heur", np.nan),
                                     "FFTW / heur": tt.get("fftw_measure", np.nan) / tt.get("pmfft_heur", np.nan)})
        a = r.get("scale_mt")
        if a is not None:
            for n in sorted(a.index.get_level_values(0).unique()):
                tmax = a.loc[n].index.max()
                s = a.loc[(n, tmax)]
                rows_mt.append({"machine": lab, "n": fmt_n(n), "threads": int(tmax),
                                "pmfft_mt GF/s": s.get("pmfft_mt", np.nan),
                                "speedup vs 1 thread": s.get("pmfft_mt", np.nan) / a.loc[(n, a.loc[n].index.min())].get("pmfft_mt", np.nan),
                                "vs MKL": s.get("pmfft_mt", np.nan) / s.get("mkl", np.nan),
                                "vs FFTW": np.nan if (n, tmax) in r["capped_mt"] else s.get("pmfft_mt", np.nan) / s.get("fftw_measure", np.nan)})
        a = r.get("scale")
        if a is not None:
            for n in sorted(a.index.get_level_values(0).unique()):
                kmax = a.loc[n].index.max()
                s = a.loc[(n, kmax)]
                rows_scale.append({"machine": lab, "n": fmt_n(n), "k (max)": int(kmax),
                                   "pmfft agg GF/s": s.get("pmfft", np.nan),
                                   "vs MKL": s.get("pmfft", np.nan) / s.get("mkl", np.nan),
                                   "vs FFTW": np.nan if n in r["capped"] else s.get("pmfft", np.nan) / s.get("fftw_measure", np.nan)})
    out = ["# Cross-machine comparison", "",
           "Generated by `scripts/compare_machines.py` from `results/machines/*/`. Ratios are speed ratios "
           "(> 1 = pmfft faster); see each machine's `summary.md` for full tables and `machine.txt` for the setup.", ""]
    if rows_gf:
        out += ["## Powers of two, single core", "", "pmfft speed / MKL speed:", "", md(pd.DataFrame(rows_mkl)), "",
                "pmfft speed / FFTW (MEASURE) speed (— where FFTW planning hit its time cap):", "", md(pd.DataFrame(rows_fftw)), "",
                "pmfft GFlop/s:", "", md(pd.DataFrame(rows_gf), "{:.1f}"), ""]
    if rows_other:
        out += ["## Smooth sizes, primes and convolution, single core (pmfft or fused3 vs MKL)", "",
                md(pd.DataFrame(rows_other)), ""]
    if rows_scale:
        out += ["## Multi-process scaling at the largest process count", "",
                "(— where FFTW planning hit its time cap at that size in the single-core runs)", "", md(pd.DataFrame(rows_scale)), ""]
    if rows_mt:
        out += ["## Multithreaded, at the largest thread count (threaded MKL / FFTW; — where FFTW planning hit its cap)", "",
                md(pd.DataFrame(rows_mt)), ""]
    if rows_traffic:
        out += ["## DRAM traffic per transform (hardware counters, sweeps S = 16 n bytes, read + write)", "",
                md(pd.DataFrame(rows_traffic)), ""]
    MDIR.mkdir(parents=True, exist_ok=True)
    (MDIR / "COMPARISON.md").write_text("\n".join(out))
    print(f"summarised {len(dirs)} machine(s) -> {MDIR / 'COMPARISON.md'}")


if __name__ == "__main__":
    main()
