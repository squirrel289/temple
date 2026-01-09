#!/usr/bin/env bash
set -euo pipefail

# Simple helper to run ASV inside Podman and restore asv.conf.json afterwards.
# Run from the repository root: ./scripts/asv_local_podman.sh

if ! command -v podman >/dev/null 2>&1; then
  echo "podman not found. Install Podman or run the interactive container steps manually." >&2
  exit 1
fi

REPO_ROOT=$(pwd)
BACKUP="${REPO_ROOT}/asv.conf.json.bak.$(date +%s)"
if [ ! -f "${REPO_ROOT}/asv.conf.json" ]; then
  echo "asv.conf.json not found in repo root (${REPO_ROOT})." >&2
  exit 1
fi

cp "${REPO_ROOT}/asv.conf.json" "$BACKUP"
echo "Backed up asv.conf.json -> $BACKUP"

# If a deterministic CI machine JSON is present, copy it into asv_results so ASV
# will see it and run non-interactively using that identity.
DETERMINISTIC_ID=2b167144ba2b
if [ -f "${REPO_ROOT}/asv_machines/2b167144ba2b_machine.json" ]; then
  mkdir -p "${REPO_ROOT}/asv_results/${DETERMINISTIC_ID}"
  cp "${REPO_ROOT}/asv_machines/2b167144ba2b_machine.json" "${REPO_ROOT}/asv_results/${DETERMINISTIC_ID}/machine.json"
  echo "Copied deterministic machine JSON into asv_results/${DETERMINISTIC_ID}/machine.json"
fi

restore() {
  echo "Restoring original asv.conf.json from $BACKUP"
  if [ -f "$BACKUP" ]; then
    mv -f "$BACKUP" "${REPO_ROOT}/asv.conf.json"
  fi
}
trap restore EXIT

# Run ASV inside a disposable Podman container
PODMAN_IMAGE="python:3.11-slim"

echo "Starting Podman container (${PODMAN_IMAGE}) to run ASV..."

podman run --rm -v "${REPO_ROOT}":/work:z -w /work $PODMAN_IMAGE bash -lc '
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive
apt-get update -y >/dev/null
apt-get install -y --no-install-recommends build-essential git ca-certificates wget python3-venv >/dev/null
python -m pip install --upgrade pip >/dev/null
pip install asv virtualenv >/dev/null

# Restrict ASV python matrix locally to the container Python to avoid requiring multiple interpreters
python - <<"PY"
import json,sys
p="asv.conf.json"
try:
    j=json.load(open(p))
except Exception as e:
    print("Failed to read asv.conf.json:", e, file=sys.stderr)
    sys.exit(1)
j.setdefault("matrix", {})["python"]=["3.11"]
open(p, "w").write(json.dumps(j, indent=2))
print("Temporarily set matrix.python ->", j["matrix"]["python"])
PY

# Non-interactive setup and run (use checked-in deterministic machine if present)
asv update || true

# Create ~/.asv-machine.json mapping for the runtime hostname to a checked-in
# machine JSON if available. This ensures ASV finds machine info non-interactively.
HOSTNAME=$(hostname)
SRC=''
if [ -f "/work/asv_machines/${HOSTNAME}_machine.json" ]; then
  SRC="/work/asv_machines/${HOSTNAME}_machine.json"
elif [ -f "/work/asv_machines/ci_machine.json" ]; then
  SRC="/work/asv_machines/ci_machine.json"
elif [ -f "/work/asv_machines/2b167144ba2b_machine.json" ]; then
  SRC="/work/asv_machines/2b167144ba2b_machine.json"
fi
if [ -n "$SRC" ]; then
    # Write mapping and include API version so asv can parse the file.
    echo -n '{' > ~/.asv-machine.json
    printf '%s' "\"$HOSTNAME\"" >> ~/.asv-machine.json
    echo -n ':' >> ~/.asv-machine.json
    cat "$SRC" >> ~/.asv-machine.json
    echo -n ",\"version\": 1}" >> ~/.asv-machine.json
  # Extract machine name from the JSON and ensure results dir has machine.json
  MNAME=$(grep -m1 '"machine"' "$SRC" | sed -E "s/.*:\\s*\"([^\"]+)\".*/\\1/")
  if [ -z "$MNAME" ]; then
    MNAME="$HOSTNAME"
  fi
  mkdir -p "/work/asv_results/$MNAME"
  cp "$SRC" "/work/asv_results/$MNAME/machine.json"
  echo "Wrote ~/.asv-machine.json and asv_results/$MNAME/machine.json"
else
  echo "No checked-in machine json found; ASV will prompt if no existing record"
fi

# Run ASV (no interactive prompt expected if ~/.asv-machine.json contained the host entry)
asv run --quick || true
'

RC=$?
if [ $RC -eq 0 ]; then
  echo "Podman ASV run completed (exit code 0)."
else
  echo "Podman ASV run exited with code $RC" >&2
fi

exit $RC
