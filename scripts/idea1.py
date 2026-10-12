# SPDX-License-Identifier: GPL-2.0-or-later
"""Idea 1: raise the bandwidth of the column pass (the strided gather of rec4's pass A).

  uv run scripts/idea1.py gather                   # microbenchmark: GB/s vs rows N1 and bytes per row visit
  uv run scripts/idea1.py sweep [--n 2^22,2^24,2^26] [--rounds 2] [--k 6]
  uv run scripts/idea1.py analyze

Background (REPORT sections 10-11): pass A gathers 128-byte segments from N1 ~ 2048 rows at ~10 GB/s (first
attributed to DRAM row activations and the TLB; the gather microbenchmark here shows it is L2 set aliasing of the
power-of-two row stride under huge pages, REPORT section 20); the L2 prefetcher adds 1.2-1.8 S of useless
reads.  Staging 4 KB per row into an N1 x 4 KB buffer streams at 16-18 GB/s and reaches the 4 S two-pass ideal,
but with N1 = 2048 the buffer is 8 MB, and six processes' buffers overflow the 24 MB L3 (staging loses under
contention).

Hypothesis: a smaller top-level N1 makes the staging buffer small (N1 x stage x 16 B; 256 x 4 KB = 1 MB), so the
long-run gather keeps its byte savings without the LLC footprint.  The price: a longer second dimension
N2 = n / N1 for pass B (rows of length N2, still leaf-sized up to the leaf budget).

sweep: rec4 configurations (base budget=131072, rmax=8, nt=1, pad=4) at each size, each a fresh process pinned
to one core, with DRAM read / write sweeps from the memory-controller counters; plus k concurrent processes
(aggregate GFlop/s, as in the contention experiments).  Order shuffled per round.
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

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from run_bench import CORE, parse_sizes  # noqa: E402
from mem_traffic import dram_events, perf_stat, bytes_rw  # noqa: E402
from fairness import nlabel  # noqa: E402

BIN = ROOT / "build" / "bench_dft"
BASE = "budget=131072,rmax=8,nt=1,pad=4"


def configs():
    yield "balanced", BASE                                         # what the planner's default rec4 does
    yield "staged N1=2048 S=256", f"{BASE},N1=2048,G=4,stage=256"  # current staged candidate (8 MB buffer)
    for n1 in (64, 128, 256, 512, 1024):
        yield f"N1={n1}", f"{BASE},N1={n1},G=4"
        for s in (64, 128, 256):
            yield f"N1={n1} S={s}", f"{BASE},N1={n1},G=4,stage={s}"


def gather(a):
    exe = ROOT / "build" / "gather_seg"
    if not exe.exists() or exe.stat().st_mtime < (ROOT / "csrc/tests/gather_seg.c").stat().st_mtime:
        subprocess.run(["gcc", "-O3", "-march=native", "-o", str(exe), str(ROOT / "csrc/tests/gather_seg.c"), "-lm"],
                       check=True)
    rows = []
    for n1 in (64, 128, 256, 512, 1024, 2048, 4096):
        n2 = (1 << 24) // n1
        # huge pages with the power-of-two row stride, huge pages with a padded stride, 4 KB pages
        for thp, pad in ((1, 0), (1, 64), (0, 0)):
            env = dict(os.environ, BENCH_NO_THP="0" if thp else "1")
            p = subprocess.run(["taskset", "-c", CORE, str(exe), str(n1), str(n2), str(pad)],
                               capture_output=True, text=True, env=env)
            for line in p.stdout.splitlines():
                m = re.search(r"N1=(\d+) seg=\s*(\d+) B \(staging\s+([\d.]+) MB\):\s+([\d.]+) GB/s", line)
                if m:
                    rows.append(dict(N1=int(m.group(1)), seg=int(m.group(2)), staging_MB=float(m.group(3)),
                                     GBps=float(m.group(4)), thp=thp, pad=pad))
            print(f"N1={n1} thp={thp} pad={pad}: " + ", ".join(
                f"{r['seg']}B {r['GBps']:.1f}" for r in rows if r["N1"] == n1 and r["thp"] == thp and r["pad"] == pad),
                flush=True)
    pd.DataFrame(rows).to_csv(a.out_gather, index=False)


def run_single(cmd, dev, kind, tmp, ctl):
    if dev:
        return perf_stat(dev, cmd + ["--perf-ctl", f"{ctl[0]},{ctl[1]}"], tmp, ctl)
    p = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT)
    return {}, p.stdout, p.stderr


def run_concurrent(params, n, k, mintime, tmp):
    cpus = [int(c) for c in subprocess.run([sys.executable, str(ROOT / "scripts" / "cpus.py"), "list"],
                                           capture_output=True, text=True).stdout.strip().split(",")][:k]
    bdir = tempfile.mkdtemp(prefix="bar_", dir=tmp)
    procs = [subprocess.Popen(["taskset", "-c", str(c), str(BIN), "--impl", "rec4", "--params", params, "--n", str(n),
                               "--mintime", str(mintime), "--barrier", bdir, str(k), "--plan-lock", bdir + ".lock"],
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=ROOT) for c in cpus]
    gf = []
    for p in procs:
        so, _ = p.communicate()
        if p.returncode == 0 and so.strip():
            gf.append(float(pd.read_csv(io.StringIO(so), header=None).iloc[0][6]) / 1e3)
    return sum(gf) if len(gf) == k else np.nan


def sweep(a):
    out = Path(a.out)
    rows = pd.read_csv(out).to_dict("records") if out.exists() and not a.fresh else []
    done = {(r["config"], int(r["n"]), int(r["round"])) for r in rows}
    dev, kind = dram_events()
    jobs = [(c, p, n) for c, p in configs() for n in parse_sizes(a.n)]
    rng = random.Random(a.seed)
    with tempfile.TemporaryDirectory() as tmp:
        ctl = (os.path.join(tmp, "ctl"), os.path.join(tmp, "ack"))
        os.mkfifo(ctl[0])
        os.mkfifo(ctl[1])
        for rnd in range(a.rounds):
            rng.shuffle(jobs)
            idle = perf_stat(dev, ["sleep", "1"], tmp)[0] if dev else {}
            for cfg, params, n in jobs:
                if (cfg, n, rnd) in done:
                    continue
                cmd = ["taskset", "-c", CORE, str(BIN), "--impl", "rec4", "--params", params, "--n", str(n),
                       "--mintime", str(a.mintime), "--check", "--check-max", str(1 << 20)]
                try:
                    vals, so, se = run_single(cmd, dev, kind, tmp, ctl)
                except RuntimeError as e:
                    print(f"FAIL {cfg} n={n}: {e}", file=sys.stderr, flush=True)
                    continue
                if not so.strip():
                    print(f"FAIL {cfg} n={n}: {se.strip()[-200:]}", file=sys.stderr, flush=True)
                    continue
                f = pd.read_csv(io.StringIO(so), header=None).iloc[0]
                r = dict(config=cfg, params=params, n=n, round=rnd, gflops=float(f[6]) / 1e3, t_med_ns=float(f[4]))
                m = re.search(r"timed_s=([\d.]+) calls=(\d+)", se)
                if dev and m:
                    timed, calls = float(m.group(1)), int(m.group(2))
                    net = {kk: v - idle.get(kk, 0.0) * timed if kk in idle else v for kk, v in vals.items()}
                    rd, wr = bytes_rw(net, kind)
                    r.update(read_sweeps=rd / calls / (16 * n), write_sweeps=wr / calls / (16 * n),
                             dram_GBps=(rd + wr) / timed * 1e-9)
                mb = re.search(r"mem n=\d+ lib_bytes=(-?\d+)", se)
                r["lib_MB"] = int(mb.group(1)) / 2**20 if mb else np.nan
                r[f"agg_k{a.k}"] = run_concurrent(params, n, a.k, a.mintime_k, tmp) if a.k > 1 else np.nan
                rows.append(r)
                print(f"r{rnd} n={n:<9d} {cfg:22s} {r['gflops']:6.2f} GF  R {r.get('read_sweeps', np.nan):5.2f} "
                      f"W {r.get('write_sweeps', np.nan):5.2f} S  {r.get('dram_GBps', np.nan):5.1f} GB/s  "
                      f"k={a.k}: {r[f'agg_k{a.k}']:6.1f} GF", flush=True)
                out.parent.mkdir(parents=True, exist_ok=True)
                pd.DataFrame(rows).to_csv(out, index=False)


def analyze(a):
    d = pd.read_csv(a.out) if Path(a.out).exists() else pd.DataFrame(columns=["n", "config", "agg_k1"])
    kcol = [c for c in d.columns if c.startswith("agg_k")][0]
    s = d.groupby(["n", "config"]).median(numeric_only=True).reset_index()
    out = ["# Idea 1: column-pass bandwidth (`scripts/idea1.py`)\n"]
    if Path(a.out_gather).exists():
        g = pd.read_csv(a.out_gather)
        out.append("## Gather microbenchmark: GB/s reading `seg` bytes per row visit from N1 rows (2^24 complex)\n")
        g["pages"] = np.where(g.thp == 1, np.where(g.get("pad", 0) > 0, "2 MB, padded stride", "2 MB"), "4 KB")
        piv = g.pivot_table(index=["pages", "N1"], columns="seg", values="GBps")
        out.append(piv.round(1).to_markdown())
        out.append("")
    for n in sorted(s.n.unique()):
        x = s[s.n == n].copy()
        b = x[x.config == "balanced"].iloc[0]
        x["vs_balanced"] = x.gflops / b.gflops
        x[f"{kcol}_vs_balanced"] = x[kcol] / b[kcol]
        out.append(f"## n = {nlabel(n)}\n")
        cols = ["config", "gflops", "vs_balanced", "read_sweeps", "write_sweeps", "dram_GBps", "lib_MB", kcol,
                f"{kcol}_vs_balanced"]
        out.append(x[[c for c in cols if c in x]].sort_values("gflops", ascending=False).round(3).to_markdown(index=False))
        out.append("")
    Path(a.md).write_text("\n".join(out))
    print("\n".join(out))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("gather")
    s = sub.add_parser("sweep")
    s.add_argument("--n", default="2^22,2^24,2^26")
    s.add_argument("--rounds", type=int, default=2)
    s.add_argument("--mintime", type=float, default=0.5)
    s.add_argument("--k", type=int, default=6)
    s.add_argument("--mintime-k", type=float, default=2.0)
    s.add_argument("--seed", type=int, default=1)
    s.add_argument("--fresh", action="store_true")
    z = sub.add_parser("analyze")
    z.add_argument("--md", default=str(ROOT / "results" / "idea1.md"))
    for x in (g, s, z):
        x.add_argument("--out", default=str(ROOT / "results" / "idea1.csv"))
        x.add_argument("--out-gather", default=str(ROOT / "results" / "idea1_gather.csv"))
    a = ap.parse_args()
    {"gather": gather, "sweep": sweep, "analyze": analyze}[a.cmd](a)


if __name__ == "__main__":
    main()
