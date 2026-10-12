# SPDX-License-Identifier: GPL-2.0-or-later
"""Pick CPUs for pinned benchmark runs (stdlib only, usable from shell scripts).

  python3 scripts/cpus.py single   -> one logical CPU for single-core timings
  python3 scripts/cpus.py list     -> comma-separated logical CPUs, one per physical core

Overrides: $BENCH_CPU (single) and $BENCH_CPUS (list).
Selection: physical cores of socket/NUMA node 0 only (keeps multi-socket servers on one memory controller),
one logical CPU per core (no SMT siblings), fastest cores first by max MHz (P-cores before E-cores on hybrid
Intel parts), CPU 0 last (it takes most interrupts).
"""
import os
import subprocess
import sys


def physical_cores():
    out = subprocess.run(["lscpu", "-p=CPU,CORE,SOCKET,NODE,MAXMHZ"], capture_output=True, text=True).stdout
    cores = {}
    for line in out.splitlines():
        if line.startswith("#"):
            continue
        cpu, core, sock, node, mhz = (line.split(",") + [""] * 5)[:5]
        sock = int(sock or 0)
        node = int(node) if node else 0
        if sock != 0 or node != 0:
            continue
        cpu = int(cpu)
        key = (sock, int(core or cpu))
        if key not in cores or cpu < cores[key][0]:
            cores[key] = (cpu, float(mhz or 0))
    lst = sorted(cores.values(), key=lambda c: (-c[1], c[0] == 0, c[0]))
    return [c[0] for c in lst] or [0]


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "single"
    if mode == "single":
        print(os.environ.get("BENCH_CPU") or physical_cores()[0])
    elif mode == "list":
        print(os.environ.get("BENCH_CPUS") or ",".join(map(str, physical_cores())))
    else:
        sys.exit("usage: cpus.py single|list")


if __name__ == "__main__":
    main()
