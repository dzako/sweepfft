# SPDX-License-Identifier: GPL-2.0-or-later
"""DRAM traffic per transform from hardware counters (perf stat), counted only around the timed loop.

  uv run scripts/mem_traffic.py [--impls pmfft,mkl,...] [--n 2^22,2^24] [--out results/mem_traffic.csv]

For each (impl, n) bench_dft runs pinned to one core under `perf stat -a`. Counters are enabled only
during the timed loop (bench_dft --perf-ctl), and an idle baseline rate (same events, `sleep`) is
subtracted. Reported per transform:
  read_sweeps / write_sweeps : DRAM bytes read / written divided by one sweep S = 16 n bytes (the data size)
  llc_miss_per_point         : last-level-cache load+store misses / n
  dram_GBps                  : sustained DRAM bandwidth during the timed loop
  l2_in_sweeps               : cache lines filled into the benchmark core's L2 (demand + hardware prefetch, from
                               L3 or DRAM) / S.  Per-core, so unaffected by other processes (Intel only)
  useless_hwpf_sweeps        : hardware-prefetched L2 lines evicted unused / S (Intel only)

The idle baseline (system-wide DRAM traffic of other processes) is measured right before and after every run
and averaged; with a busy desktop it still adds noise, so close browsers etc. for clean DRAM numbers.

Needs system-wide counters: `sudo sysctl kernel.perf_event_paranoid=0` (until reboot) or CAP_PERFMON.
On AMD the DRAM counters live in the uncore PMU: `sudo modprobe amd_uncore` if /sys/bus/event_source/devices
has no amd_df (e.g. Ubuntu live sessions).
DRAM counters: Intel client/server IMC (uncore_imc_free_running_* data_read/data_write, or uncore_imc_*
cas_count_read/write); AMD Zen 2/3 data-fabric DRAM channel events (read+write combined). Without them,
only LLC misses are reported.
"""
import argparse
import io
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
BIN = ROOT / "build" / "bench_dft"
sys.path.insert(0, str(ROOT / "scripts"))
from run_bench import parse_sizes, CORE  # noqa: E402

PMU = Path("/sys/bus/event_source/devices")


def perf_list():
    """`perf list` output, or "" when perf is not installed (containers): callers then run without counters."""
    if not shutil.which("perf"):
        return ""
    return subprocess.run(["perf", "list", "--no-desc"], capture_output=True, text=True).stdout


def dram_events():
    """(list of perf events, kind) where kind tells how to turn counts into read/write bytes."""
    if not shutil.which("perf"):
        return [], "none"
    imc = sorted(PMU.glob("uncore_imc_free_running_*"))
    if imc:
        ev = []
        for d in imc:
            ev += [f"{d.name}/data_read/", f"{d.name}/data_write/"]
        return ev, "intel_free_running"            # values already scaled to MiB by perf
    imc = sorted(PMU.glob("uncore_imc_[0-9]*"))
    if imc and (imc[0] / "events" / "cas_count_read").exists():
        ev = []
        for d in imc:
            ev += [f"{d.name}/cas_count_read/", f"{d.name}/cas_count_write/"]
        return ev, "intel_cas"                     # scaled to MiB by perf (64 B per CAS)
    lst = perf_list()
    ch = sorted(set(re.findall(r"(dram_channel_data_controller_\d+)", lst)))
    if ch:
        return supported(ch), "amd_df"            # 64 B beats, read+write combined
    if (PMU / "amd_df").exists() and amd_family() in (0x17,):
        # Zen 1/2: perf has no names for the data-fabric DRAM channel events; use the raw encodings
        # (PPR "DramChannelDataController0..7", umask 0x38, 64 B beats, read+write).  Unverified until the
        # calibration kernel (build/traffic_calib) is run on such a machine.
        raw = [f"amd_df/event={e:#x},umask=0x38/" for e in (0x07, 0x47, 0x87, 0xC7, 0x107, 0x147, 0x187, 0x1C7)]
        raw = supported(raw)
        if raw:
            return raw, "amd_df_raw"
    return [], "none"


def amd_family():
    try:
        txt = Path("/proc/cpuinfo").read_text()
        if "AuthenticAMD" not in txt:
            return None
        return int(re.search(r"cpu family\s*:\s*(\d+)", txt).group(1))
    except (OSError, AttributeError):
        return None


def supported(events):
    """Keep only events perf can actually count system-wide on this machine (none without perf)."""
    ok = []
    if not shutil.which("perf"):
        return ok
    for e in events:
        r = subprocess.run(["perf", "stat", "-a", "-x,", "-e", e, "--", "true"], capture_output=True, text=True)
        if r.returncode == 0 and "not supported" not in r.stderr and "<not" not in r.stderr:
            ok.append(e)
    return ok


def core_events():
    """Per-core events, counted on the benchmark CPU only (perf -A)."""
    pre = "cpu_core/" if (PMU / "cpu_core").exists() else ""       # hybrid Intel: P-core PMU
    suf = "/" if pre else ""
    ev = [f"{pre}LLC-load-misses{suf}", f"{pre}LLC-store-misses{suf}"]
    lst = perf_list()
    for e in ("l2_lines_in.all", "l2_lines_out.useless_hwpf"):
        if re.search(rf"\b{re.escape(e)}\b", lst):
            ev.append(f"{pre}{e}{suf}")
    return supported(ev)


def parse_perf(path, cpu):
    """perf stat -a -A -x, output -> {event: value}.  Uncore/DRAM events are summed over all rows; per-core
    events (LLC, L2) are taken from the benchmark CPU's row only."""
    vals = {}
    for line in Path(path).read_text().splitlines():
        if not line or line.startswith("#"):
            continue
        f = line.split(",")
        if len(f) < 4 or not f[0].startswith("CPU") or f[1].startswith("<"):
            continue
        ev = f[3]
        core = "LLC" in ev or "l2_lines" in ev or "cycles" in ev or "instructions" in ev
        if core and f[0] != f"CPU{cpu}":
            continue
        try:
            vals[ev] = vals.get(ev, 0.0) + float(f[1])
        except ValueError:
            pass
    return vals


def perf_stat(events, cmd, tmp, ctl=None):
    out = os.path.join(tmp, "perf.txt")
    pc = ["perf", "stat", "-a", "-A", "-x,", "--no-big-num", "-o", out, "-e", ",".join(events)]
    if ctl:
        pc += ["--delay=-1", "--control", f"fifo:{ctl[0]},{ctl[1]}"]
    r = subprocess.run(pc + ["--"] + cmd, capture_output=True, text=True, cwd=ROOT)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip()[-400:])
    return parse_perf(out, CORE), r.stdout, r.stderr


def bytes_rw(vals, kind):
    """(read_bytes, write_bytes); for AMD data-fabric events reads+writes are reported together as reads."""
    if kind in ("intel_free_running", "intel_cas"):
        rd = sum(v for k, v in vals.items() if "read" in k) * 2**20
        wr = sum(v for k, v in vals.items() if "write" in k) * 2**20
        return rd, wr
    if kind == "amd_df":
        return sum(v for k, v in vals.items() if "dram_channel" in k) * 64.0, np.nan
    if kind == "amd_df_raw":
        return sum(v for k, v in vals.items() if "amd_df" in k) * 64.0, np.nan
    return np.nan, np.nan


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--impls", default="pmfft,mkl,fftw_measure,ducc")
    ap.add_argument("--grid", default="", help="params for every impl, e.g. 'nt=0' (one setting)")
    ap.add_argument("--n", default="2^20,2^22,2^24,2^26,3*2^20")
    ap.add_argument("--mintime", type=float, default=2.0)
    ap.add_argument("--rounds", type=int, default=2)
    ap.add_argument("--bin", default=str(BIN))
    ap.add_argument("--out", default=str(ROOT / "results" / "mem_traffic.csv"))
    ap.add_argument("--calib-only", action="store_true", help="run only the calibration kernels")
    ap.add_argument("--threads", type=int, default=1,
                    help="T > 1: threaded libraries (build/bench_dft_mt, pinned like scale_mt.py, MT wisdom file); "
                         "per-core L2 columns are then left empty")
    a = ap.parse_args()
    mt_env = []
    if a.threads > 1:
        from scale_mt import cpus
        cl = cpus()[:a.threads]
        if a.bin == str(BIN):
            a.bin = str(ROOT / "build" / "bench_dft_mt")
        mt_env = [f"BENCH_THREADS={a.threads}", f"OMP_NUM_THREADS={a.threads}", "OMP_PROC_BIND=close",
                  "OMP_PLACES=" + ",".join("{%d}" % c for c in cl), "MKL_DYNAMIC=FALSE",
                  "FFTW_WISDOM_FILE=" + os.environ.get("FFTW_WISDOM_FILE", str(ROOT / "results" / "fftw_wisdom_mt.dat"))]
        bench_cpus = ",".join(map(str, cl))
    else:
        bench_cpus = CORE
    dev, kind = dram_events()
    core = core_events()
    events = dev + core
    print(f"DRAM events: {kind} ({len(dev)}), core events on cpu {CORE}: {core}", flush=True)
    if not dev and amd_family() and not (PMU / "amd_df").exists():
        print("AMD CPU without the amd_df PMU: load the uncore driver with `sudo modprobe amd_uncore` "
              "for DRAM counters", flush=True)
    if not events:
        print("no usable hardware counters on this machine (or perf_event_paranoid > 0): skipping", flush=True)
        return
    rows = []
    impls = [s.split(":", 1) if ":" in s else (s, a.grid) for s in a.impls.split(";" if ";" in a.impls else ",")]
    with tempfile.TemporaryDirectory() as tmp:
        ctl, ack = os.path.join(tmp, "ctl"), os.path.join(tmp, "ack")
        os.mkfifo(ctl)
        os.mkfifo(ack)
        def idle_rate():
            if not dev:
                return {}
            idle, _, _ = perf_stat(dev, ["sleep", "1"], tmp)
            return idle
        if dev and (ROOT / "build" / "traffic_calib").exists():
            # calibration: 1 GiB copies with ordinary stores (expect read 2, write 1 per copy: data + RFO) and
            # non-temporal stores (expect read 1, write 1); reported in units of the copied size
            for mode, expect in (("a", "2R+1W"), ("b", "1R+1W"), ("r", "1R"), ("w", "1R+1W (RFO)"), ("n", "1W NT")):
                before = idle_rate()
                cmd = ["taskset", "-c", CORE, str(ROOT / "build" / "traffic_calib"), mode, "1024", "10", f"{ctl},{ack}"]
                vals, _, err = perf_stat(events, cmd, tmp, (ctl, ack))
                m = re.search(r"timed_s=([\d.]+) calls=(\d+)", err)
                if not m:
                    continue
                timed, calls = float(m.group(1)), int(m.group(2))
                after = idle_rate()
                idle = {k: 0.5 * (before.get(k, 0.0) + after.get(k, 0.0)) for k in set(before) | set(after)}
                net = {k: v - idle.get(k, 0.0) * timed for k, v in vals.items()}
                rd, wr = bytes_rw(net, kind)
                C = 1024.0 * 2**20
                name = {"a": "copy_store", "b": "copy_nt", "r": "read", "w": "fill_store", "n": "fill_nt"}[mode]
                rows.append(dict(impl=f"calib_{name}", params=f"expect {expect}", n=0,
                                 round=-1, calls=calls, timed_s=timed, read_sweeps=rd / calls / C,
                                 write_sweeps=wr / calls / C, dram_kind=kind))
                print(f"calibration {mode} (expect {expect}): read {rd / calls / C:.2f}  write {wr / calls / C:.2f} "
                      f"per pass" + ("  [AMD: read column = read+write combined]" if kind.startswith("amd") else ""),
                      flush=True)
        # calibration verdict: total (read + write) per pass must match the known traffic of every kernel
        expect_tot = {"calib_copy_store": 3.0, "calib_copy_nt": 2.0, "calib_read": 1.0, "calib_fill_store": 2.0,
                      "calib_fill_nt": 1.0}
        errs = [abs((r["read_sweeps"] + (0 if np.isnan(r["write_sweeps"]) else r["write_sweeps"])) / expect_tot[r["impl"]] - 1)
                for r in rows if r["impl"] in expect_tot]
        if errs and max(errs) > 0.15:
            print(f"WARNING: counters fail calibration (max error {100 * max(errs):.0f}%): DRAM numbers on this machine "
                  "do not measure bytes; results are marked uncalibrated", flush=True)
            kind += "_uncalibrated"
            for r in rows:
                r["dram_kind"] = kind
        elif errs:
            print(f"calibration OK (max error {100 * max(errs):.0f}%)", flush=True)
        if a.calib_only:
            Path(a.out).parent.mkdir(parents=True, exist_ok=True)
            pd.DataFrame(rows).to_csv(a.out, index=False)
            return
        for rnd in range(a.rounds):
            for n in parse_sizes(a.n):
                for impl, params in impls:
                    before = idle_rate()
                    cmd = ["taskset", "-c", bench_cpus, a.bin, "--impl", impl, "--params", params, "--n", str(n),
                           "--mintime", str(a.mintime), "--perf-ctl", f"{ctl},{ack}"]
                    env_cmd = ["env", "FFTW_WISDOM_RO=1"] + mt_env + cmd
                    vals, out, err = perf_stat(events, env_cmd, tmp, (ctl, ack))
                    m = re.search(r"timed_s=([\d.]+) calls=(\d+)", err)
                    if not m or not out.strip():
                        print(f"FAIL {impl} n={n}: {err.strip()[-200:]}", file=sys.stderr)
                        continue
                    timed, calls = float(m.group(1)), int(m.group(2))
                    after = idle_rate()
                    idle = {k: 0.5 * (before.get(k, 0.0) + after.get(k, 0.0)) for k in set(before) | set(after)}
                    net = {k: v - idle.get(k, 0.0) * timed for k, v in vals.items()}
                    idle_gbps = sum(idle.values()) * (2**20 if kind.startswith("intel") else 64.0) * 1e-9 if idle else np.nan
                    rd, wr = bytes_rw(net, kind)
                    S = 16.0 * n
                    llc_m = sum(v for k, v in net.items() if "LLC" in k)
                    l2in = sum(v for k, v in vals.items() if "l2_lines_in" in k)
                    uhw = sum(v for k, v in vals.items() if "useless_hwpf" in k)
                    has_l2 = any("l2_lines_in" in k for k in vals) and a.threads == 1
                    t_med = float(pd.read_csv(io.StringIO(out), header=None).iloc[0, 4]) * 1e-9
                    r = dict(impl=impl, params=params, n=n, round=rnd, threads=a.threads, calls=calls, timed_s=timed,
                             t_med_ns=t_med * 1e9, gflops=5 * n * np.log2(n) / t_med * 1e-9,
                             read_sweeps=rd / calls / S, write_sweeps=wr / calls / S,
                             dram_GBps=(rd + (0 if np.isnan(wr) else wr)) / timed * 1e-9,
                             llc_miss_per_point=llc_m / calls / n, dram_kind=kind,
                             l2_in_sweeps=l2in * 64 / calls / S if has_l2 else np.nan,
                             useless_hwpf_sweeps=uhw * 64 / calls / S if has_l2 else np.nan,
                             idle_GBps=idle_gbps)
                    rows.append(r)
                    print(f"r{rnd} {impl:13s} {params:12s} n={n:<10d} {r['gflops']:6.2f} GF/s  read {r['read_sweeps']:5.2f} S  "
                          f"write {r['write_sweeps']:5.2f} S  {r['dram_GBps']:5.1f} GB/s  L2in {r['l2_in_sweeps']:5.2f} S  "
                          f"uselessHWPF {r['useless_hwpf_sweeps']:5.2f} S  (idle {idle_gbps:.2f} GB/s)",
                          flush=True)
                    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
                    pd.DataFrame(rows).to_csv(a.out, index=False)


if __name__ == "__main__":
    main()
