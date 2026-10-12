# SPDX-License-Identifier: GPL-2.0-or-later
"""Plan FFTW ahead with a long time cap, so that every later study on this machine imports complete plans.

  uv run scripts/fftw_plan_ahead.py --wisdom results/machines/<label>/fftw_wisdom.dat --n 2^20,...,3*2^20,...
                                    --out results/machines/<label>/fftw_wisdom_choice.csv

Why: run_machine.sh caps FFTW's MEASURE planner at $FFTW_TIMELIMIT (60 s) per size.  On slower or server cores
that cap is hit from 2^24 on, and the truncated plans run 3-10x slower than complete ones.  The studies reuse the
machine's wisdom file, so one truncated search silently weakens every later FFTW comparison.

Per size, one bench_dft run of fftw_measure plans with a cap of --cap-pow2 seconds (powers of two and 3*2^20) or
--cap-other seconds (other sizes; the i7 protocol already excludes their FFTW comparisons when the search is
capped), writing the plan into the wisdom file.  Sizes that already have wisdom take ~0 s.  The output CSV has the
format of results/fftw_wisdom_choice.csv ($FFTW_WISDOM_CHOICE), including `search_capped`, which the studies use
to exclude or flag sizes whose search hit the cap (plans imported from wisdom take ~0 s to "plan", so a cap can no
longer be seen during the studies themselves).
"""
import argparse
import io
import os
import subprocess
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from run_bench import CORE, parse_sizes  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--wisdom", required=True)
    ap.add_argument("--n", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--cap-pow2", type=float, default=1800)
    ap.add_argument("--cap-other", type=float, default=600)
    a = ap.parse_args()
    out = Path(a.out)
    rows = pd.read_csv(out).to_dict("records") if out.exists() else []
    have = {int(r["n"]) for r in rows}
    wis = str(Path(a.wisdom).resolve())
    for n in sorted(set(parse_sizes(a.n))):
        if n in have:
            continue
        cap = a.cap_pow2 if (n & (n - 1)) == 0 or n == 3 << 20 else a.cap_other
        env = dict(os.environ, FFTW_WISDOM_FILE=wis, FFTW_TIMELIMIT=str(cap))
        env.pop("FFTW_WISDOM_RO", None)
        p = subprocess.run(["taskset", "-c", CORE, str(ROOT / "build" / "bench_dft"), "--impl", "fftw_measure", "--n",
                            str(n), "--mintime", "0.5"], capture_output=True, text=True, cwd=ROOT, env=env)
        if p.returncode or not p.stdout.strip():
            print(f"FAIL n={n}: {p.stderr.strip()[-200:]}", file=sys.stderr, flush=True)
            continue
        f = pd.read_csv(io.StringIO(p.stdout), header=None).iloc[0]
        plan_s, gf = float(f[3]), float(f[6]) / 1e3
        rows.append({"n": n, "best_file": wis, "best_gflops": gf, "search_capped": plan_s >= 0.98 * cap,
                     "fresh_search_s": plan_s, "cap_s": cap})
        print(f"n={n:<9d} plan {plan_s:7.1f} s (cap {cap:g}){' CAPPED' if plan_s >= 0.98 * cap else ''}  "
              f"{gf:6.2f} GF", flush=True)
        out.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(rows).to_csv(out, index=False)


if __name__ == "__main__":
    main()
