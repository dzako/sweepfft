#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-2.0-or-later
# Poll remote suite runs (scripts/remote_run.sh); exit when any machine reaches a milestone not reported before,
# so that a caller waiting on this process is notified.  Milestones: QUICK_OK (full run started), FINISHED (results
# copied into results/machines/), FAILED, and UNREACHABLE (once per hour).
#   scripts/remote_watch.sh <state file> <machine>...    machine = user@host:port:label:remote log:remote repo dir
set -u
STATE=$1; shift; touch "$STATE"
REPO=$(cd "$(dirname "$0")/.." && pwd)
pull() {  # dest port label repo-dir log
  mkdir -p "$REPO/results/machines/$3"
  rsync -az -e "ssh -p $2 -o BatchMode=yes" "$1:$4/results/machines/$3" "$1:$4/results/machines/$3-quick" \
    "$REPO/results/machines/" 2>&1 | tail -2
  rsync -az -e "ssh -p $2 -o BatchMode=yes" "$1:$5" "$REPO/results/machines/$3/suite.log" 2>&1 | tail -2
}
while true; do
  new=0
  for m in "$@"; do
    IFS=: read -r dest port label log dir <<< "$m"
    out=$(ssh -o BatchMode=yes -o ConnectTimeout=20 -p "$port" "$dest" \
          "grep -E '^=== .*(full|FAILED|SUITE FINISHED)' $log; tail -1 $log" 2>/dev/null)
    if [ -z "$out" ]; then
      key="$label UNREACHABLE $(date +%Y%m%d%H)"
      grep -qxF "$key" "$STATE" || { echo "$key"; echo "$key" >> "$STATE"; new=1; }
      continue
    fi
    for ms in QUICK_OK FAILED FINISHED; do
      case $ms in QUICK_OK) pat="^=== .* full";; FAILED) pat="FAILED";; FINISHED) pat="SUITE FINISHED";; esac
      if echo "$out" | grep -qE "$pat" && ! grep -qxF "$label $ms" "$STATE"; then
        echo "$label $ms   (last: $(echo "$out" | tail -1))"
        echo "$label $ms" >> "$STATE"; new=1
        if [ $ms = QUICK_OK ]; then
          rsync -az -e "ssh -p $port -o BatchMode=yes" "$dest:$dir/results/machines/$label-quick" "$REPO/results/machines/" 2>&1 | tail -1
        else pull "$dest" "$port" "$label" "$dir" "$log"; fi
      fi
    done
  done
  [ $new = 1 ] && exit 0
  sleep 300
done
