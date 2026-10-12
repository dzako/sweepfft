# SPDX-License-Identifier: GPL-2.0-or-later
"""Does the physical layout of ordinarily allocated (4 KB-page) caller arrays decide the libraries' speed?

  uv run scripts/frag.py run [--n 2^22,2^24] [--rounds 3]
  uv run scripts/frag.py analyze

Hypothesis (results/REPORT.md section 21): with 4 KB pages, a power-of-two row stride aliases in the L2 sets only if
the array's pages are physically contiguous.  The buddy allocator hands out the smallest free blocks first, so the
layout depends on how fragmented free memory is when the caller allocates; the libraries' speed with ordinary
arrays should then drift with the machine's memory state, while SweepFFT's should not.

Free-memory states, set by build/memhold (csrc/tests/memhold.c), which holds its memory during the measurement:
  as-is   the machine's current state (no holder)
  contig  the holder takes every free block below order 9 (2 MB), so the arrays are split from large blocks
  frag    the holder touches 8 GB and frees a random half of its pages, so the arrays get scattered pages
Per state: /proc/buddyinfo, the strided-gather bandwidth with 4 KB pages (build/gather_seg, N1 = 2048, 128-byte
segments: high = no aliasing), and pmfft / MKL / FFTW / ducc0 with BENCH_CALLER_PAGES=plain, each a fresh pinned
process.  State order shuffled per round.
"""
import argparse
import io
import os
import random
import re
import subprocess
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from run_bench import CORE, parse_sizes  # noqa: E402
from fairness import nlabel  # noqa: E402
from fftw_best_wisdom import wisdom_for  # noqa: E402

IMPLS = ["pmfft", "mkl", "fftw_measure", "ducc"]
NAME = {"pmfft": "SweepFFT", "mkl": "MKL", "fftw_measure": "FFTW", "ducc": "ducc0"}
STATES = ["as-is", "contig", "frag"]


def build(name, src):
    exe = ROOT / "build" / name
    if not exe.exists() or exe.stat().st_mtime < (ROOT / src).stat().st_mtime:
        subprocess.run(["gcc", "-O3", "-march=native", "-o", str(exe), str(ROOT / src), "-lm"], check=True)
    return exe


def buddy():
    """Free memory per order (MB, summed over zones) and the MB in blocks below order 9."""
    tot = [0.0] * 11
    for line in Path("/proc/buddyinfo").read_text().splitlines():
        c = [int(x) for x in line.split()[4:]]
        for o, k in enumerate(c):
            tot[o] += k * 4096 * 2**o / 2**20
    return tot, sum(tot[:9])


def holder(state, seed):
    if state == "as-is":
        return None
    _, small = buddy()
    args = ["contig", str(int(small) + 64)] if state == "contig" else ["frag", "8192", str(seed)]
    p = subprocess.Popen([str(ROOT / "build" / "memhold")] + args, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         text=True)
    if p.stdout.readline().strip() != "READY":
        raise RuntimeError(f"memhold {args} failed")
    return p


def gather():
    env = dict(os.environ, BENCH_NO_THP="1")
    p = subprocess.run(["taskset", "-c", CORE, str(ROOT / "build" / "gather_seg"), "2048", "8192", "0"],
                       capture_output=True, text=True, env=env)
    m = re.search(r"seg=\s*128 B .*?([\d.]+) GB/s", p.stdout)
    return float(m.group(1)) if m else float("nan")


def run(a):
    build("memhold", "csrc/tests/memhold.c")
    build("gather_seg", "csrc/tests/gather_seg.c")
    out = Path(a.out)
    rows = pd.read_csv(out).to_dict("records") if out.exists() and not a.fresh else []
    rng = random.Random(a.seed)
    for rnd in range(a.rounds):
        states = STATES[:]
        rng.shuffle(states)
        for st in states:
            h = holder(st, rnd)
            try:
                orders, small = buddy()
                g = gather()
                print(f"r{rnd} {st:6s} free<2MB {small:7.0f} MB  free>=2MB {sum(orders[9:]):7.0f} MB  "
                      f"gather {g:5.1f} GB/s", flush=True)
                jobs = [(i, n) for i in IMPLS for n in parse_sizes(a.n)]
                rng.shuffle(jobs)
                for impl, n in jobs:
                    env = dict(os.environ, BENCH_CALLER_PAGES="plain", FFTW_WISDOM_RO="1", FFTW_TIMELIMIT="60",
                               FFTW_WISDOM_FILE=wisdom_for(n, os.environ.get("FFTW_WISDOM_FILE")
                                                           or str(ROOT / "results" / "fftw_wisdom.dat")))
                    p = subprocess.run(["taskset", "-c", CORE, str(ROOT / "build" / "bench_dft"), "--impl", impl,
                                        "--n", str(n), "--mintime", str(a.mintime)],
                                       capture_output=True, text=True, cwd=ROOT, env=env)
                    if p.returncode or not p.stdout.strip():
                        print(f"FAIL {st} {impl} n={n}: {p.stderr.strip()[-200:]}", file=sys.stderr, flush=True)
                        continue
                    f = pd.read_csv(io.StringIO(p.stdout), header=None).iloc[0]
                    rows.append(dict(state=st, round=rnd, impl=impl, n=n, gflops=float(f[6]) / 1e3, gather_GBps=g,
                                     free_small_MB=small, free_large_MB=sum(orders[9:])))
                    print(f"   {impl:13s} n={n:<9d} {rows[-1]['gflops']:6.2f} GF", flush=True)
                    out.parent.mkdir(parents=True, exist_ok=True)
                    pd.DataFrame(rows).to_csv(out, index=False)
            finally:
                if h:
                    h.stdin.close()
                    h.wait()


def analyze(a):
    d = pd.read_csv(a.out)
    g = d.groupby(["n", "impl", "state"]).gflops.median().unstack()
    st = [s for s in STATES if s in g.columns]
    gat = d.groupby("state").gather_GBps.median()
    small = d.groupby("state").free_small_MB.median()
    lines = ["# Physical layout of ordinary caller arrays (`scripts/frag.py`)\n",
             f"Median over {d['round'].nunique()} rounds; caller arrays allocated the ordinary way (4 KB pages). "
             "States: as-is = the machine's current free memory; contig = small free blocks held, arrays split "
             "from large contiguous blocks; frag = arrays get scattered pages.\n",
             "| state | free memory in blocks < 2 MB (MB) | strided gather, 128 B x 2048 rows (GB/s) |", "|---|---|---|"]
    lines += [f"| {s} | {small[s]:.0f} | {gat[s]:.1f} |" for s in st]
    lines += ["", "GFlop/s and SweepFFT speedup per state:", "",
              "| n | impl | " + " | ".join(st) + " | " + " | ".join(f"speedup {s}" for s in st) + " |",
              "|---|---|" + "---|" * (2 * len(st))]
    for n in sorted(d.n.unique()):
        for impl in IMPLS:
            if (n, impl) not in g.index:
                continue
            v = g.loc[(n, impl)]
            sp = ["–" if impl == "pmfft" else f"{g.loc[(n, 'pmfft'), s] / v[s]:.2f}" for s in st]
            lines.append(f"| {nlabel(n)} | {NAME[impl]} | " + " | ".join(f"{v[s]:.2f}" for s in st) + " | "
                         + " | ".join(sp) + " |")
    Path(a.md).write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--n", default="2^22,2^24")
    r.add_argument("--rounds", type=int, default=3)
    r.add_argument("--mintime", type=float, default=1.0)
    r.add_argument("--seed", type=int, default=3)
    r.add_argument("--fresh", action="store_true")
    z = sub.add_parser("analyze")
    z.add_argument("--md", default=str(ROOT / "results" / "frag.md"))
    for x in (r, z):
        x.add_argument("--out", default=str(ROOT / "results" / "frag.csv"))
    a = ap.parse_args()
    {"run": run, "analyze": analyze}[a.cmd](a)


if __name__ == "__main__":
    main()
