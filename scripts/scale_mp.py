# SPDX-License-Identifier: GPL-2.0-or-later
"""Multi-process bandwidth-scaling test (proxy for multithreaded out-of-cache behaviour).

For each (n, impl, k) launch k independent single-thread bench_dft processes, each pinned to its own
physical P-core. They plan and warm up independently, then synchronise on a file barrier and time
concurrently, so they compete for the shared L3 and DRAM bandwidth the way k threads of one FFT would.
Aggregate throughput = sum of per-process GFlop/s (5 n log2 n / t).

  uv run scripts/scale_mp.py [--quick] [--ks 1,2,4,8] [--out results/machines/<label>/scale_mp.csv]

CPUs come from scripts/cpus.py (one per physical core of socket 0, fastest first; override with $BENCH_CPUS).
The number of concurrent processes per size is capped by the available memory.
"""
import argparse, io, os, subprocess, sys, tempfile, time
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BIN = os.path.join(ROOT, "build", "bench_dft")
CPUS = [int(c) for c in subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "cpus.py"), "list"],
                                       capture_output=True, text=True).stdout.strip().split(",")]
# Memory per point: steady state (in + out + plan scratch; pmfft ~80 B, MKL/FFTW ~40 B) and planning peak
# (pmfft ~125 B).  Processes plan one at a time (--plan-lock), so only one planning peak is live at once.
STEADY_B, PEAK_B = 80, 128


def mem_available():
    for line in open("/proc/meminfo"):
        if line.startswith("MemAvailable:"):
            return int(line.split()[1]) * 1024
    return 8 << 30


COLS = "impl,params,n,plan_s,t_med_ns,t_min_ns,mflops,rms_err,max_err,reps".split(",")


def run_one(spec, n, k, mintime):
    impl, params = spec.split(":", 1) if ":" in spec else (spec, "")
    bdir = tempfile.mkdtemp(prefix="bar_", dir=os.environ.get("TMPDIR", "/tmp"))
    env = dict(os.environ, FFTW_WISDOM_RO="1")
    procs = [subprocess.Popen(["taskset", "-c", str(c), BIN, "--impl", impl, "--params", params, "--n", str(n), "--mintime", str(mintime),
                               "--barrier", bdir, str(k), "--plan-lock", bdir + ".lock"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                              env=env, cwd=ROOT) for c in CPUS[:k]]
    rows = []
    for c, p in zip(CPUS[:k], procs):
        out, err = p.communicate()
        if p.returncode != 0 or not out.strip():
            print(f"FAIL {impl} n={n} k={k} cpu={c}: {err.strip()[:200]}", file=sys.stderr)
            continue
        r = pd.read_csv(io.StringIO(out), header=None, names=COLS).iloc[0].to_dict()
        r.update(k=k, cpu=c)
        rows.append(r)
    for f in os.listdir(bdir):
        os.remove(os.path.join(bdir, f))
    os.rmdir(bdir)
    if os.path.exists(bdir + ".lock"):
        os.remove(bdir + ".lock")
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--rounds", type=int, default=2)
    ap.add_argument("--out", default=os.path.join(ROOT, "results", "scale_mp.csv"))
    ap.add_argument("--ks", default="1,2,4,6", help="numbers of concurrent processes (capped by #cores and memory)")
    ap.add_argument("--impls", default="pmfft,mkl,fftw_measure",
                    help="comma-separated; use ';' to separate when giving impl:params (params contain commas)")
    ap.add_argument("--sizes", default="", help="override sizes, e.g. 2^22,2^24")
    a = ap.parse_args()
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    impls = a.impls.split(";") if ";" in a.impls else a.impls.split(",")
    ks = [k for k in map(int, a.ks.split(",")) if k <= len(CPUS)]
    mem = mem_available()
    # (n, max k): (k-1) steady processes + one planning peak within 80% of the currently available memory
    sizes = (2**22, 2**24, 3 * 2**20, 2**26)
    if a.sizes:
        sys.path.insert(0, os.path.join(ROOT, "scripts"))
        from run_bench import parse_sizes
        sizes = parse_sizes(a.sizes)
    plan = [(n, int((0.8 * mem - PEAK_B * n) // (STEADY_B * n)) + 1) for n in sizes]
    print(f"CPUs {CPUS[:max(ks)]}, MemAvailable {mem / 2**30:.1f} GiB, max k per n: {dict(plan)}", flush=True)
    mintime = 4.0
    if a.quick:
        plan, ks, mintime, a.rounds = [(2**22, 2)], [1, 2], 1.0, 1
    rows = []
    for rnd in range(a.rounds):
        for n, kmax in plan:
            for k in [k for k in ks if k <= kmax]:
                order = impls[rnd % len(impls):] + impls[:rnd % len(impls)]           # rotate impl order between rounds
                for impl in order:
                    t0 = time.time()
                    rs = run_one(impl, n, k, mintime)
                    for r in rs:
                        r["round"] = rnd
                    rows += rs
                    agg = sum(r["mflops"] for r in rs) / 1e3
                    print(f"r{rnd} n={n} k={k} {impl[:40]:40s} agg={agg:6.1f} GF/s  per-proc="
                          f"{[round(r['mflops'] / 1e3, 1) for r in rs]}  ({time.time() - t0:.0f}s)", flush=True)
                    pd.DataFrame(rows).to_csv(a.out, index=False)


if __name__ == "__main__":
    main()
