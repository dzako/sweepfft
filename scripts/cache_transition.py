# SPDX-License-Identifier: GPL-2.0-or-later
"""Cache-capacity transition experiment: a dense one-core sweep of smooth sizes across the L2, LLC and
2/4/8 x LLC working-set boundaries, with time, cycles, cache misses, DRAM traffic, plan choice and memory.

  uv run scripts/cache_transition.py run  [--impls pmfft,mkl,fftw_measure,ducc] [--rounds 2] [--quick]
  uv run scripts/cache_transition.py plot [--csv results/cache_transition.csv]

Sizes: n = m * 2^a for odd parts m in {1,3,5,7,9,15,21,25} (eight sizes per octave, spread over the octave,
and one "factorization class" per m), 2^13 <= n <= 2^25.  With the data working set W = 32 n bytes
(out-of-place input + output) the thresholds L2 = 1.25 MB, LLC = 24 MB and 2/4/8 x LLC fall exactly on
n = 5*2^13 and 3*2^18 ... 3*2^21 on the i7-13700H.

Each (impl, n) is a fresh bench_dft process pinned to one core under `perf stat` (counters enabled only
around the timed loop, as in mem_traffic.py).  Per row:
  t_med_ns, gflops               median time, 5 n log2 n / t
  cyc_per_elem, ipc              core cycles / (calls * n) and instructions per cycle on the benchmark core
  llc_miss_per_elem              LLC load + store misses / (calls * n)
  l2_in_per_elem                 L2 line fills (demand + prefetch) / (calls * n)
  read_sweeps, write_sweeps      DRAM bytes / (calls * 16 n), idle baseline subtracted
  lib_bytes, plan_peak_bytes     resident memory the implementation adds beyond the in/out arrays (plan,
                                 twiddles, scratch), and its peak during planning (bench_dft "mem" line)
  footprint_bytes                32 n + lib_bytes: the working set the transform actually touches
  plan, plan_s                   the planner's choice (pmfft: component and parameters; FFTW: solver chain)
  fftw_capped                    FFTW planning hit $FFTW_TIMELIMIT (plan truncated)
Results are appended after every run; a rerun skips (impl, n, round) rows already in the CSV.
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
from run_bench import CORE  # noqa: E402
from mem_traffic import dram_events, core_events, supported, perf_stat, bytes_rw, PMU  # noqa: E402

BIN = ROOT / "build" / "bench_dft"
ODD = (1, 3, 5, 7, 9, 15, 21, 25)


def sizes(lo=1 << 13, hi=1 << 25, odd=ODD):
    out = []
    for m in odd:
        a = 0
        while m << a <= hi:
            if m << a >= lo:
                out.append(m << a)
            a += 1
    return sorted(out)


def cache_bytes(cpu, level):
    """Size in bytes of the unified/data cache at `level` seen by `cpu` (sysfs), or None."""
    for d in sorted(Path(f"/sys/devices/system/cpu/cpu{cpu}/cache").glob("index*")):
        try:
            if int((d / "level").read_text()) == level and (d / "type").read_text().strip() in ("Unified", "Data"):
                v = (d / "size").read_text().strip()
                mul = {"K": 1 << 10, "M": 1 << 20, "G": 1 << 30}.get(v[-1], 1)
                return int(v.rstrip("KMG")) * mul
        except (OSError, ValueError):
            pass
    return None


def odd_part(n):
    while n % 2 == 0:
        n //= 2
    return n


def run(a):
    out = Path(a.out)
    done = set()
    rows = []
    if out.exists() and not a.fresh:
        old = pd.read_csv(out)
        rows = old.to_dict("records")
        done = {(r["impl"], int(r["n"]), int(r["round"])) for r in rows}
    impls = a.impls.split(",")
    ns = sizes(odd=(1, 3, 5)) if a.quick else sizes()
    if a.quick:
        ns = [n for n in ns if (1 << 14) <= n <= (1 << 22)]
    l2, llc = cache_bytes(CORE, 2), cache_bytes(CORE, 3)
    dev, kind = dram_events()
    pre, suf = ("cpu_core/", "/") if (PMU / "cpu_core").exists() else ("", "")
    core = core_events() + supported([f"{pre}cycles{suf}", f"{pre}instructions{suf}"])
    events = dev + core
    print(f"cpu {CORE}: L2 {l2} B, LLC {llc} B; DRAM events {kind} ({len(dev)}); core events {core}; "
          f"{len(ns)} sizes x {len(impls)} impls x {a.rounds} rounds", flush=True)
    if not events:
        print("no usable counters (perf_event_paranoid > 0?): timing and memory only", flush=True)
    tl = float(os.environ.get("FFTW_TIMELIMIT", "60"))
    env = dict(os.environ, FFTW_TIMELIMIT=str(tl))
    with tempfile.TemporaryDirectory() as tmp:
        ctl, ack = os.path.join(tmp, "ctl"), os.path.join(tmp, "ack")
        os.mkfifo(ctl)
        os.mkfifo(ack)
        for rnd in range(a.rounds):
            for i, n in enumerate(ns):
                todo = [impls[(j + rnd + i) % len(impls)] for j in range(len(impls))]   # rotate the order
                todo = [im for im in todo if (im, n, rnd) not in done]
                if not todo:
                    continue
                idle = perf_stat(dev, ["sleep", "1"], tmp)[0] if dev else {}
                for impl in todo:
                    cmd = ["taskset", "-c", CORE, str(BIN), "--impl", impl, "--n", str(n), "--mintime", str(a.mintime)]
                    if events:
                        cmd += ["--perf-ctl", f"{ctl},{ack}"]
                        try:
                            vals, so, se = perf_stat(events, ["env"] + [f"{k}={v}" for k, v in env.items()
                                                                        if k.startswith("FFTW")] + cmd, tmp, (ctl, ack))
                        except RuntimeError as e:
                            print(f"FAIL {impl} n={n}: {e}", file=sys.stderr)
                            continue
                    else:
                        r = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT, env=env)
                        vals, so, se = {}, r.stdout, r.stderr
                    mm = re.search(r"mem n=\d+ lib_bytes=(-?\d+) plan_peak_bytes=(-?\d+) plan=(.*)", se)
                    if not so.strip() or not mm:
                        print(f"FAIL {impl} n={n}: {se.strip()[-300:]}", file=sys.stderr)
                        continue
                    f = pd.read_csv(io.StringIO(so), header=None).iloc[0]
                    plan_s, t = float(f[3]), float(f[4]) * 1e-9
                    r = dict(impl=impl, n=n, odd=odd_part(n), round=rnd, ws_bytes=32 * n, l2_bytes=l2, llc_bytes=llc,
                             plan_s=plan_s, t_med_ns=t * 1e9, gflops=5 * n * np.log2(n) / t * 1e-9,
                             lib_bytes=int(mm.group(1)), plan_peak_bytes=int(mm.group(2)), plan=mm.group(3).strip(),
                             fftw_capped=impl.startswith("fftw") and plan_s >= 0.9 * tl)
                    r["footprint_bytes"] = 32 * n + max(r["lib_bytes"], 0)
                    m = re.search(r"timed_s=([\d.]+) calls=(\d+)", se)
                    if events and m:
                        timed, calls = float(m.group(1)), int(m.group(2))
                        net = {k: v - idle.get(k, 0.0) * timed if k in idle else v for k, v in vals.items()}
                        rd, wr = bytes_rw(net, kind)
                        tot = calls * n

                        def ev(key):
                            v = [x for k, x in vals.items() if key in k]
                            return sum(v) / tot if v else np.nan
                        r.update(calls=calls, cyc_per_elem=ev("cycles"),
                                 ipc=ev("instructions") / ev("cycles"),
                                 llc_miss_per_elem=ev("LLC"), l2_in_per_elem=ev("l2_lines_in"),
                                 read_sweeps=rd / tot / 16, write_sweeps=wr / tot / 16,
                                 dram_GBps=(rd + (0 if np.isnan(wr) else wr)) / timed * 1e-9, dram_kind=kind)
                    rows.append(r)
                    print(f"r{rnd} {impl:13s} n={n:<9d} W={32 * n / 2**20:8.2f} MB  {r['gflops']:6.2f} GF  "
                          f"{r.get('cyc_per_elem', np.nan):6.1f} cyc/el  R {r.get('read_sweeps', np.nan):5.2f} "
                          f"W {r.get('write_sweeps', np.nan):5.2f} S  lib {r['lib_bytes'] / (16 * n):4.2f} S  "
                          f"{r['plan'][:60]}", flush=True)
                    out.parent.mkdir(parents=True, exist_ok=True)
                    pd.DataFrame(rows).to_csv(out, index=False)


def summarize(df):
    """Median over rounds per (impl, n); FFTW rows planned under a cap in any round keep the flag."""
    num = [c for c in ("t_med_ns", "gflops", "cyc_per_elem", "ipc", "llc_miss_per_elem", "l2_in_per_elem",
                       "read_sweeps", "write_sweeps", "dram_GBps", "lib_bytes", "footprint_bytes", "plan_peak_bytes")
           if c in df]
    g = df.groupby(["impl", "n"])
    s = g[num].median()
    s["plan_s"] = g["plan_s"].max()
    s["fftw_capped"] = g["fftw_capped"].any()
    s["plan"] = g["plan"].agg(lambda x: x.mode().iloc[0])
    s["spread"] = g["gflops"].agg(lambda x: (x.max() - x.min()) / x.median() if len(x) > 1 else 0.0)
    for c in ("odd", "ws_bytes", "l2_bytes", "llc_bytes"):
        s[c] = g[c].first()
    return s.reset_index()


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--impls", default="pmfft,mkl,fftw_measure,ducc")
    r.add_argument("--rounds", type=int, default=2)
    r.add_argument("--mintime", type=float, default=0.5)
    r.add_argument("--quick", action="store_true", help="odd parts 1,3,5 and 2^14..2^22 only")
    r.add_argument("--fresh", action="store_true", help="ignore rows already in --out")
    r.add_argument("--out", default=str(ROOT / "results" / "cache_transition.csv"))
    p = sub.add_parser("plot")
    p.add_argument("--csv", default=str(ROOT / "results" / "cache_transition.csv"))
    p.add_argument("--out", default=str(ROOT / "results" / "fig_cache_transition.png"))
    a = ap.parse_args()
    if a.cmd == "run":
        run(a)
    else:
        from plot_cache_transition import plot
        plot(summarize(pd.read_csv(a.csv)), a.out)


if __name__ == "__main__":
    main()
