#!/usr/bin/env bash
# Configure deterministic CI machine identity for ASV benchmarks
# This script creates ~/.asv-machine.json mapping the runner hostname to ci_machine.json
# so ASV doesn't prompt interactively for machine information.

set -euo pipefail

HOSTNAME=$(hostname)
SRC="${1:-asv/machines/ci_machine.json}"

if [ -f "$SRC" ]; then
  echo -n '{' > ~/.asv-machine.json
  printf '%s' "\"$HOSTNAME\"" >> ~/.asv-machine.json
  echo -n ':' >> ~/.asv-machine.json
  cat "$SRC" >> ~/.asv-machine.json
  echo -n ",\"version\": 1}" >> ~/.asv-machine.json
  
  MNAME=$(grep -m1 '"machine"' "$SRC" | sed -E "s/.*:\\s*\"([^\"]+)\".*/\\1/")
  if [ -z "$MNAME" ]; then
    MNAME="$HOSTNAME"
  fi
  
  mkdir -p "asv/results/$MNAME"
  cp "$SRC" "asv/results/$MNAME/machine.json"
  echo "✓ Configured ASV machine identity: $MNAME (hostname: $HOSTNAME)"
else
  echo "⚠ Warning: Machine config file not found: $SRC"
  exit 1
fi
