#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-2.0-or-later
# Bootstrap and run the full per-machine suite on a remote host (started detached by the caller, see
# scripts/remote_watch.sh).  Run from the repository root on the remote machine:
#   nohup setsid scripts/remote_run.sh <label> [run_machine.sh options, default --all] > /dev/null 2>&1 &
# Installs missing build tools (as root only) and uv, builds, runs the --quick smoke test with the same options,
# then the full run.  Progress: ~/suite-<label>.log; milestones are lines starting with "=== ".
set -uo pipefail
LABEL=$1; shift
OPTS=${*:---all}
cd "$(dirname "$0")/.."
exec > "$HOME/suite-$LABEL.log" 2>&1
echo "=== $(date) bootstrap $LABEL ($OPTS)"
if ! command -v gcc >/dev/null || ! command -v make >/dev/null || ! command -v unzip >/dev/null; then
  if [ "$(id -u)" = 0 ]; then
    export DEBIAN_FRONTEND=noninteractive
    apt-get update -q && apt-get install -yq build-essential curl git python3 unzip rsync util-linux procps
  else echo "=== missing build tools and not root"; exit 1; fi
fi
command -v uv >/dev/null || [ -x "$HOME/.local/bin/uv" ] || curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH=$HOME/.local/bin:$PATH
uv sync -q
scripts/setup_third_party.sh && scripts/build.sh || { echo "=== BUILD FAILED"; exit 1; }
echo "=== $(date) quick"
scripts/run_machine.sh "$LABEL" --quick $OPTS
grep -q "DONE" "results/machines/$LABEL-quick/run.log" || { echo "=== QUICK FAILED"; exit 1; }
echo "=== $(date) full"
scripts/run_machine.sh "$LABEL" $OPTS
echo "=== $(date) SUITE FINISHED"
