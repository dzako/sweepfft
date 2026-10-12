# SPDX-License-Identifier: GPL-2.0-or-later
"""Controlled memory-bandwidth contention: does SweepFFT degrade more slowly than the libraries as memory
pressure rises?

  uv run scripts/contention.py procs     [--sizes 2^22,2^24,3*2^20] [--ks 1,2,4,6,8,10,12,14] [--rounds 3]
  uv run scripts/contention.py interfere [--sizes 2^22,2^24,3*2^20] [--levels 0,1x0.25,1x0.5,1x0.75,1,2x0.75,2,4,8]
                                         [--placement any|same-llc|other-llc] [--kernel triad] [--rounds 3]
  uv run scripts/contention.py analyze

Method A (procs): k independent single-threaded FFT processes, one per physical core (P-cores first, then
E-cores on hybrid parts), each with its own arrays.  They plan one at a time, synchronise on a barrier and are
timed concurrently.  While all k run, a perf window (system-wide, 0.75 x --mintime) records the DRAM traffic
(memory-controller counters) and the cycles of every CPU, giving: per-process latency and core type,
aggregate GFlop/s, DRAM bandwidth, DRAM bytes per transform (in sweeps S = 16 n bytes) and each core's
effective clock.

Method B (interfere): one FFT process on the benchmark core alongside build/stream_load (STREAM triad by
default) on other cores.  An intensity level "TxD" is T load threads at duty cycle D (D = 1 if omitted; "0" =
no load).  For every level the background is first measured alone (memory-controller counters over 2 s, and
the load's own byte count), then each FFT implementation runs with counters enabled only during its timed loop:
total system DRAM bandwidth during the FFT, and the background's bandwidth over the same window from the load's
log.  Slowdown = FFT time / its time at level 0 in the same round.  --placement selects load CPUs that share the
FFT core's last-level cache, or only DRAM (other LLC; possible on parts with several L3 domains, e.g. Zen 2
CCXs; on a single-LLC part every load shares the LLC and the run says so).

DRAM counters are used where they were calibrated (Intel memory-controller counters; scripts/mem_traffic.py
--calib-only); elsewhere bandwidth comes from the load's own byte count (no read-for-ownership; a triad's DRAM
traffic is about 4/3 of that) and the FFT traffic columns are left empty.
"""
import argparse
import io
import os
import random
import re
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from run_bench import CORE, parse_sizes  # noqa: E402
from mem_traffic import dram_events, supported, parse_perf, perf_stat, bytes_rw, PMU  # noqa: E402
from fftw_best_wisdom import wisdom_for  # noqa: E402

BIN = ROOT / "build" / "bench_dft"
LOAD = ROOT / "build" / "stream_load"
IMPLS = ["pmfft", "mkl", "fftw_measure", "ducc"]
NAME = {"pmfft": "SweepFFT", "mkl": "MKL", "fftw_measure": "FFTW", "ducc": "ducc0"}
COLS = "impl,params,n,plan_s,t_med_ns,t_min_ns,mflops,rms_err,max_err,reps".split(",")
TRUSTED = ("intel_free_running", "intel_cas")
STEADY_B, PEAK_B = 80, 128


# ------------------------------------------------------------------------------------------------------- topology

def cpu_list():
    return [int(c) for c in subprocess.run([sys.executable, str(ROOT / "scripts" / "cpus.py"), "list"],
                                           capture_output=True, text=True).stdout.strip().split(",")]


def core_type(cpu):
    f = PMU / "cpu_atom" / "cpus"
    if not f.exists():
        return "P"
    return "E" if cpu in expand(f.read_text().strip()) else "P"


def expand(spec):
    out = []
    for part in spec.split(","):
        if "-" in part:
            a, b = map(int, part.split("-"))
            out += range(a, b + 1)
        elif part:
            out.append(int(part))
    return out


def llc_group(cpu):
    try:
        return Path(f"/sys/devices/system/cpu/cpu{cpu}/cache/index3/shared_cpu_list").read_text().strip()
    except OSError:
        return "?"


def mem_available():
    for line in open("/proc/meminfo"):
        if line.startswith("MemAvailable:"):
            return int(line.split()[1]) * 1024
    return 8 << 30


def cycle_events():
    if (PMU / "cpu_core").exists():
        return supported(["cpu_core/cycles/"] + (["cpu_atom/cycles/"] if (PMU / "cpu_atom").exists() else []))
    return supported(["cycles"])


def perf_window(events, seconds, tmp):
    """System-wide perf stat over `sleep seconds`: (DRAM values summed, {cpu: cycles})."""
    out = os.path.join(tmp, "win.txt")
    subprocess.run(["perf", "stat", "-a", "-A", "-x,", "--no-big-num", "-o", out, "-e", ",".join(events), "--",
                    "sleep", f"{seconds:.3f}"], capture_output=True, text=True)
    cyc = {}
    for line in Path(out).read_text().splitlines():
        f = line.split(",")
        if len(f) >= 4 and f[0].startswith("CPU") and "cycles" in f[3] and not f[1].startswith("<"):
            try:
                cyc[int(f[0][3:])] = cyc.get(int(f[0][3:]), 0.0) + float(f[1])
            except ValueError:
                pass
    return parse_perf(out, CORE), cyc


# --------------------------------------------------------------------------------------------- Method A: processes

def run_procs(a):
    out = Path(a.out_procs)
    rows = pd.read_csv(out).to_dict("records") if out.exists() and not a.fresh else []
    done = {(r["impl"], int(r["n"]), int(r["k"]), int(r["round"])) for r in rows}
    cpus = cpu_list()
    ks = [k for k in parse_sizes(a.ks) if k <= len(cpus)]
    dev, kind = dram_events()
    ev = dev + cycle_events()
    mem = mem_available()
    print(f"CPUs {cpus} (types {''.join(core_type(c) for c in cpus)}); DRAM {kind} "
          f"({'calibrated' if kind in TRUSTED else 'not used'}); MemAvailable {mem / 2**30:.1f} GiB", flush=True)
    with tempfile.TemporaryDirectory() as tmp:
        for rnd in range(a.rounds):
            for n in parse_sizes(a.sizes):
                kmax = int((0.8 * mem - PEAK_B * n) // (STEADY_B * n)) + 1
                for k in [k for k in ks if k <= kmax]:
                    order = IMPLS[rnd % len(IMPLS):] + IMPLS[:rnd % len(IMPLS)]
                    for impl in order:
                        if (impl, n, k, rnd) in done:
                            continue
                        rs = procs_once(impl, n, cpus[:k], a.mintime, ev, kind, tmp)
                        for r in rs:
                            r.update(round=rnd)
                        rows += rs
                        if rs:
                            r0 = rs[0]
                            print(f"r{rnd} n={n:<9d} k={k:2d} {impl:13s} agg {sum(r['gflops'] for r in rs):6.1f} GF  "
                                  f"DRAM {r0['dram_GBps']:5.1f} GB/s  {r0['sweeps_per_transform']:5.2f} S/transform  "
                                  f"GHz {np.nanmedian([r['eff_ghz'] for r in rs]):.2f}", flush=True)
                        out.parent.mkdir(parents=True, exist_ok=True)
                        pd.DataFrame(rows).to_csv(out, index=False)


def procs_once(impl, n, cpus, mintime, ev, kind, tmp):
    k = len(cpus)
    bdir = tempfile.mkdtemp(prefix="bar_", dir=tmp)
    env = dict(os.environ, FFTW_WISDOM_RO="1")
    env["FFTW_WISDOM_FILE"] = wisdom_for(n, env.get("FFTW_WISDOM_FILE", str(ROOT / "results" / "fftw_wisdom.dat")))
    procs = [subprocess.Popen(["taskset", "-c", str(c), str(BIN), "--impl", impl, "--n", str(n), "--mintime",
                               str(mintime), "--barrier", bdir, str(k), "--plan-lock", bdir + ".lock"],
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env, cwd=ROOT)
             for c in cpus]
    # all processes ready (each creates its barrier file after planning) -> they start timing; measure inside
    t0 = time.time()
    while len(os.listdir(bdir)) < k and time.time() - t0 < 3600 and all(p.poll() is None for p in procs):
        time.sleep(0.02)
    W = 0.75 * mintime
    vals, cyc = perf_window(ev, W, tmp) if ev else ({}, {})
    res = []
    for c, p in zip(cpus, procs):
        so, se = p.communicate()
        if p.returncode or not so.strip():
            print(f"FAIL {impl} n={n} k={k} cpu={c}: {se.strip()[-200:]}", file=sys.stderr, flush=True)
            continue
        f = pd.read_csv(io.StringIO(so), header=None, names=COLS).iloc[0]
        res.append(dict(impl=impl, n=n, k=k, cpu=c, core_type=core_type(c), t_med_ns=float(f.t_med_ns),
                        gflops=float(f.mflops) / 1e3, eff_ghz=cyc.get(c, np.nan) / W * 1e-9 if cyc else np.nan))
    rd, wr = bytes_rw(vals, kind) if kind in TRUSTED and vals else (np.nan, np.nan)
    rate = sum(1e9 / r["t_med_ns"] for r in res)                       # transforms per second, all processes
    for r in res:
        r.update(dram_GBps=(rd + wr) / W * 1e-9, read_GBps=rd / W * 1e-9, write_GBps=wr / W * 1e-9,
                 sweeps_per_transform=(rd + wr) / (W * rate) / (16 * n) if rate else np.nan, window_s=W)
    for f in os.listdir(bdir):
        os.remove(os.path.join(bdir, f))
    os.rmdir(bdir)
    if os.path.exists(bdir + ".lock"):
        os.remove(bdir + ".lock")
    return res


# -------------------------------------------------------------------------------------------- Method B: interference

def parse_level(s):
    if s in ("0", "0x0"):
        return 0, 0.0
    t, _, d = s.partition("x")
    return int(t), float(d or 1)


def load_cpus(placement, cpus):
    others = [c for c in cpus if c != int(CORE)]
    g = llc_group(int(CORE))
    if placement == "same-llc":
        return [c for c in others if llc_group(c) == g]
    if placement == "other-llc":
        return [c for c in others if llc_group(c) != g]
    return others


def bg_rate(log, t0, t1):
    """Logical bytes/s of the background load between wall times t0 and t1, from its log."""
    try:
        d = np.loadtxt(log, ndmin=2)
    except (OSError, ValueError):
        return np.nan
    m = (d[:, 0] >= t0) & (d[:, 0] <= t1)
    if m.sum() < 2:
        return np.nan
    x = d[m]
    return (x[-1, 1] - x[0, 1]) / (x[-1, 0] - x[0, 0])


def run_interfere(a):
    out = Path(a.out_interfere)
    rows = pd.read_csv(out).to_dict("records") if out.exists() and not a.fresh else []
    done = {(r["level"], r["impl"], int(r["n"]), int(r["round"])) for r in rows}
    cpus = cpu_list()
    lc = load_cpus(a.placement, cpus)
    levels = [lv for lv in a.levels.split(",") if parse_level(lv)[0] <= len(lc)]
    if a.placement == "other-llc" and not lc:
        sys.exit("no CPU outside the benchmark core's LLC on this machine: every load shares the LLC")
    dev, kind = dram_events()
    trusted = kind in TRUSTED
    shared = all(llc_group(c) == llc_group(int(CORE)) for c in lc)
    print(f"FFT on cpu {CORE} ({core_type(int(CORE))}); load CPUs {lc} ({'all share' if shared else 'mixed / not sharing'} "
          f"the FFT core's LLC {llc_group(int(CORE))}); levels {levels}; DRAM {kind} "
          f"({'calibrated' if trusted else 'not used: bandwidth from the load log'})", flush=True)
    rng = random.Random(a.seed)
    with tempfile.TemporaryDirectory() as tmp:
        ctl, ack = os.path.join(tmp, "ctl"), os.path.join(tmp, "ack")
        os.mkfifo(ctl)
        os.mkfifo(ack)
        for rnd in range(a.rounds):
            lv_order = levels[:]
            rng.shuffle(lv_order)
            for li, lv in enumerate(lv_order):
                T, D = parse_level(lv)
                todo = [(n, i) for n in parse_sizes(a.sizes) for i in IMPLS if (lv, i, n, rnd) not in done]
                if not todo:
                    continue
                log = os.path.join(tmp, "load.log")
                lp = None
                if T:
                    lp = subprocess.Popen([str(LOAD), "--cpus", ",".join(map(str, lc[:T])), "--kernel", a.kernel,
                                           "--mb", str(a.load_mb), "--duty", str(D), "--log", log])
                    t_wait = time.time()
                    time.sleep(1.0)
                    while not bg_rate(log, time.time() - 0.6, time.time()) > 0 and time.time() - t_wait < 60:
                        time.sleep(0.2)                                   # until the arrays are initialised and streaming
                ts = time.time()
                if dev and trusted:
                    vals, _ = perf_window(dev, 2.0, tmp)
                    rd, wr = bytes_rw(vals, kind)
                    solo_dram = (rd + wr) / 2.0 * 1e-9
                else:
                    time.sleep(2.0)
                    solo_dram = np.nan
                solo_log = bg_rate(log, ts, time.time()) * 1e-9 if T else 0.0
                print(f"r{rnd} level {lv:7s}: background alone {solo_dram:6.1f} GB/s DRAM, {solo_log:6.1f} GB/s "
                      f"logical", flush=True)
                for jdx, (n, impl) in enumerate(sorted(todo, key=lambda x: (x[0], (IMPLS.index(x[1]) + rnd + li) % len(IMPLS)))):
                    cmd = ["taskset", "-c", CORE, str(BIN), "--impl", impl, "--n", str(n), "--mintime", str(a.mintime)]
                    wf = wisdom_for(n, os.environ.get("FFTW_WISDOM_FILE", str(ROOT / "results" / "fftw_wisdom.dat")))
                    env = dict(os.environ, FFTW_WISDOM_RO="1", FFTW_WISDOM_FILE=wf)
                    t_start = time.time()
                    try:
                        if dev and trusted:
                            vals, so, se = perf_stat(dev, ["env", "FFTW_WISDOM_RO=1", f"FFTW_WISDOM_FILE={wf}"] + cmd + ["--perf-ctl", f"{ctl},{ack}"],
                                                     tmp, (ctl, ack))
                        else:
                            p = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT, env=env)
                            vals, so, se = {}, p.stdout, p.stderr
                    except RuntimeError as e:
                        print(f"FAIL {lv} {impl} n={n}: {e}", file=sys.stderr, flush=True)
                        continue
                    t_end = time.time()
                    if not so.strip():
                        print(f"FAIL {lv} {impl} n={n}: {se.strip()[-200:]}", file=sys.stderr, flush=True)
                        continue
                    f = pd.read_csv(io.StringIO(so), header=None, names=COLS).iloc[0]
                    m = re.search(r"timed_s=([\d.]+) calls=(\d+)", se)
                    timed = float(m.group(1)) if m else np.nan
                    calls = int(m.group(2)) if m else np.nan
                    rd, wr = bytes_rw(vals, kind) if vals and trusted else (np.nan, np.nan)
                    r = dict(level=lv, threads=T, duty=D, kernel=a.kernel, placement=a.placement,
                             shares_llc=shared, impl=impl, n=n, round=rnd, t_med_ns=float(f.t_med_ns),
                             gflops=float(f.mflops) / 1e3, bg_solo_dram_GBps=solo_dram, bg_solo_logical_GBps=solo_log,
                             total_dram_GBps=(rd + wr) / timed * 1e-9 if timed else np.nan,
                             fft_bytes_per_transform_total=(rd + wr) / calls if calls else np.nan,
                             bg_logical_GBps=(bg_rate(log, t_end - timed, t_end) * 1e-9 if T and timed else 0.0))
                    rows.append(r)
                    print(f"r{rnd} level {lv:7s} {impl:13s} n={n:<9d} {r['gflops']:6.2f} GF  system DRAM "
                          f"{r['total_dram_GBps']:5.1f} GB/s  background {r['bg_logical_GBps']:5.1f} GB/s logical",
                          flush=True)
                    out.parent.mkdir(parents=True, exist_ok=True)
                    pd.DataFrame(rows).to_csv(out, index=False)
                if lp:
                    lp.send_signal(signal.SIGTERM)
                    lp.wait()


# ------------------------------------------------------------------------------------------------------- analysis

def nlabel(n):
    from fairness import nlabel as nl
    return nl(n)


def analyze(a):
    out = ["# Controlled memory-bandwidth contention (`scripts/contention.py`)\n"]
    W = out.append
    A = pd.read_csv(a.out_procs) if Path(a.out_procs).exists() else None
    B = pd.read_csv(a.out_interfere) if Path(a.out_interfere).exists() else None
    if A is not None:
        W("## Method A: k independent processes\n")
        W("Per-process latency (P-core processes, ms), aggregate GFlop/s, per-process speed relative to k = 1 "
          "(P-core processes), DRAM bandwidth, DRAM bytes per transform and median effective clock; medians over "
          "rounds. k > number of P-cores adds E-core processes (their latency is in the E column).\n")
        g = A.groupby(["n", "k", "impl", "round"])
        per = g.apply(lambda d: pd.Series(dict(
            agg_gf=d.gflops.sum(), lat_p=d[d.core_type == "P"].t_med_ns.mean() / 1e6,
            lat_e=d[d.core_type == "E"].t_med_ns.mean() / 1e6 if (d.core_type == "E").any() else np.nan,
            gf_p=d[d.core_type == "P"].gflops.mean(), dram=d.dram_GBps.iloc[0], sw=d.sweeps_per_transform.iloc[0],
            ghz=d.eff_ghz.median()))).reset_index()
        s = per.groupby(["n", "k", "impl"]).median(numeric_only=True).reset_index()
        for n in sorted(s.n.unique()):
            W(f"**n = {nlabel(n)}**\n")
            W("| k | impl | latency P (ms) | latency E (ms) | aggregate GF | per-process vs k=1 | DRAM GB/s | "
              "S / transform | GHz | SweepFFT agg. speedup |")
            W("|---|---|---|---|---|---|---|---|---|---|")
            for k in sorted(s[s.n == n].k.unique()):
                d = s[(s.n == n) & (s.k == k)].set_index("impl")
                for i in IMPLS:
                    if i not in d.index:
                        continue
                    r = d.loc[i]
                    base = s[(s.n == n) & (s.k == 1) & (s.impl == i)].gf_p
                    ret = r.gf_p / base.iloc[0] if len(base) else np.nan
                    sp = d.loc["pmfft"].agg_gf / r.agg_gf if "pmfft" in d.index else np.nan
                    W(f"| {k} | {NAME[i]} | {r.lat_p:.1f} | {r.lat_e:.1f} | {r.agg_gf:.1f} | {ret:.2f} | {r.dram:.1f} | "
                      f"{r.sw:.2f} | {r.ghz:.2f} | {'–' if i == 'pmfft' else f'{sp:.2f}'} |")
            W("")
    if B is not None:
        W("## Method B: one FFT with controlled background load\n")
        shared = B.shares_llc.all()
        W(f"Load kernel {B.kernel.iloc[0]}, placement {B.placement.iloc[0]} "
          f"({'every load core shares the FFT core’s LLC' if shared else 'load cores do not share the FFT core’s LLC'}). "
          "Background bandwidth: measured alone (memory-controller counters) and during the FFT (the load's own "
          "byte count). Slowdown = time / time at level 0 (same round), median over rounds.\n")
        B = B.copy()
        base = B[B.threads == 0].set_index(["impl", "n", "round"]).t_med_ns
        B["slowdown"] = [r.t_med_ns / base.get((r.impl, r.n, r["round"]), np.nan) for _, r in B.iterrows()]
        s = B.groupby(["n", "level", "impl"]).median(numeric_only=True).reset_index()
        for n in sorted(s.n.unique()):
            W(f"**n = {nlabel(n)}**\n")
            W("| level | background alone, DRAM GB/s | background during FFT (logical GB/s) | " +
              " | ".join(f"{NAME[i]} slowdown" for i in IMPLS) + " | SweepFFT vs MKL | vs FFTW | vs ducc0 | system DRAM GB/s (SweepFFT run) |")
            W("|" + "---|" * (6 + len(IMPLS) + 1))
            d = s[s.n == n]
            for lv in sorted(d.level.unique(), key=lambda x: d[d.level == x].bg_solo_logical_GBps.median()):
                x = d[d.level == lv].set_index("impl")
                cells = [f"{x.loc[i].slowdown:.2f}" if i in x.index else "–" for i in IMPLS]
                sp = [f"{x.loc[l].t_med_ns / x.loc['pmfft'].t_med_ns:.2f}" if l in x.index and "pmfft" in x.index else "–"
                      for l in ("mkl", "fftw_measure", "ducc")]
                W(f"| {lv} | {x.bg_solo_dram_GBps.median():.1f} | {x.bg_logical_GBps.median():.1f} | " +
                  " | ".join(cells + sp) + f" | {x.loc['pmfft'].total_dram_GBps if 'pmfft' in x.index else np.nan:.1f} |")
            W("")
        W("**Sensitivity to background bandwidth**: slope of log(slowdown) against the background bandwidth "
          "measured alone (memory-controller counters where calibrated, otherwise the load's byte count), "
          "% per 10 GB/s, with 95% CI (all levels and rounds).\n")
        from scipy import stats
        W("| n | " + " | ".join(NAME[i] for i in IMPLS) + " |")
        W("|---|" + "---|" * len(IMPLS))
        for n in sorted(B.n.unique()):
            cells = []
            for i in IMPLS:
                d = B[(B.n == n) & (B.impl == i)].dropna(subset=["slowdown"])
                x = d.bg_solo_dram_GBps.where(d.bg_solo_dram_GBps.notna(), d.bg_solo_logical_GBps).fillna(0)
                if len(d) < 3:
                    cells.append("–")
                    continue
                res = stats.linregress(x, np.log(d.slowdown))
                h = stats.t.ppf(0.975, len(d) - 2) * res.stderr
                cells.append(f"{100 * 10 * res.slope:+.1f} [{100 * 10 * (res.slope - h):+.1f}, {100 * 10 * (res.slope + h):+.1f}]")
            W(f"| {nlabel(n)} | " + " | ".join(cells) + " |")
        W("")
    Path(a.md).write_text("\n".join(out))
    print("\n".join(out))
    print("wrote", a.md)
    plot(a, A, B)


def plot(a, A, B, width=7.16, height=2.6, fontsize=7):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    PAL = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#4a3aa7", "#e34948"]
    INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"
    COL = {"pmfft": PAL[0], "mkl": PAL[1], "fftw_measure": PAL[2], "ducc": PAL[3]}
    MK = {"pmfft": "o", "mkl": "s", "fftw_measure": "^", "ducc": "D"}
    plt.rcParams.update({"font.size": fontsize, "font.family": "serif", "axes.edgecolor": INK2,
                         "axes.labelcolor": INK, "xtick.color": INK2, "ytick.color": INK2, "axes.grid": True,
                         "grid.color": GRID, "grid.linewidth": 0.5, "axes.spines.top": False,
                         "axes.spines.right": False, "lines.linewidth": 1.3, "lines.markersize": 3.5,
                         "legend.frameon": False, "legend.fontsize": fontsize - 0.5, "pdf.fonttype": 42})
    n0 = a.plot_n
    fig, axs = plt.subplots(1, 3, figsize=(width, height))
    if A is not None and (A.n == n0).any():
        d = A[(A.n == n0) & (A.core_type == "P")]
        s = d.groupby(["impl", "k", "round"]).gflops.mean().groupby(["impl", "k"]).median().reset_index()
        t = A[A.n == n0].groupby(["impl", "k", "round"]).sweeps_per_transform.first().groupby(["impl", "k"]).median().reset_index()
        for i in IMPLS:
            x = s[s.impl == i]
            if x.empty:
                continue
            axs[0].plot(x.k, x.gflops / x.gflops.iloc[0], marker=MK[i], color=COL[i], label=NAME[i])
            y = t[t.impl == i]
            axs[1].plot(y.k, y.sweeps_per_transform, marker=MK[i], color=COL[i], label=NAME[i])
        axs[0].set_xlabel("concurrent processes k")
        axs[0].set_xticks([1, 2, 4, 6, 8, 10, 12, 14])
        axs[0].set_ylabel("per-process speed / k = 1 (P-cores)")
        axs[0].set_title(f"(a) A: speed retention, n = {nlabel(n0)}", fontsize=fontsize, loc="left")
        axs[0].legend(loc="lower left")
        axs[1].set_xlabel("concurrent processes k")
        axs[1].set_xticks([1, 2, 4, 6, 8, 10, 12, 14])
        axs[1].set_ylabel("DRAM bytes per transform (S)")
        axs[1].set_title("(b) A: traffic per transform", fontsize=fontsize, loc="left")
    if B is not None and (B.n == n0).any():
        B = B.copy()
        base = B[B.threads == 0].set_index(["impl", "n", "round"]).t_med_ns
        B["slowdown"] = [r.t_med_ns / base.get((r.impl, r.n, r["round"]), np.nan) for _, r in B.iterrows()]
        B["bg"] = B.bg_solo_dram_GBps.where(B.bg_solo_dram_GBps.notna(), B.bg_solo_logical_GBps).fillna(0)
        s = B[B.n == n0].groupby(["impl", "level"]).median(numeric_only=True).reset_index()
        for i in IMPLS:
            x = s[s.impl == i].sort_values("bg")
            axs[2].plot(x.bg, x.slowdown, marker=MK[i], color=COL[i], label=NAME[i])
        axs[2].axhline(1, color=INK2, lw=0.8)
        axs[2].set_xlabel("background bandwidth, measured alone (GB/s)")
        axs[2].set_ylabel("FFT slowdown (time / unloaded)")
        axs[2].set_title(f"(c) B: interference, n = {nlabel(n0)}", fontsize=fontsize, loc="left")
        axs[2].legend(loc="upper left")
    fig.tight_layout()
    fig.savefig(a.fig, bbox_inches="tight", dpi=200)
    plt.close(fig)
    print("wrote", a.fig)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("procs")
    p.add_argument("--sizes", default="2^22,2^24,3*2^20")
    p.add_argument("--ks", default="1,2,4,6,8,10,12,14")
    p.add_argument("--rounds", type=int, default=3)
    p.add_argument("--mintime", type=float, default=4.0)
    p.add_argument("--fresh", action="store_true")
    q = sub.add_parser("interfere")
    q.add_argument("--sizes", default="2^22,2^24,3*2^20")
    q.add_argument("--levels", default="0,1x0.25,1x0.5,1x0.75,1,2x0.75,2,4,8")
    q.add_argument("--placement", default="any", choices=("any", "same-llc", "other-llc"))
    q.add_argument("--kernel", default="triad", choices=("triad", "copy", "read"))
    q.add_argument("--load-mb", type=float, default=256)
    q.add_argument("--rounds", type=int, default=3)
    q.add_argument("--mintime", type=float, default=1.5)
    q.add_argument("--seed", type=int, default=1)
    q.add_argument("--fresh", action="store_true")
    z = sub.add_parser("analyze")
    z.add_argument("--md", default=str(ROOT / "results" / "contention.md"))
    z.add_argument("--fig", default=str(ROOT / "results" / "fig_contention.png"))
    z.add_argument("--plot-n", type=int, default=1 << 24)
    for x in (p, q, z):
        x.add_argument("--out-procs", default=str(ROOT / "results" / "contention_procs.csv"))
        x.add_argument("--out-interfere", default=str(ROOT / "results" / "contention_interfere.csv"))
    a = ap.parse_args()
    {"procs": run_procs, "interfere": run_interfere, "analyze": analyze}[a.cmd](a)


if __name__ == "__main__":
    main()
