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
if [ -f "${REPO_ROOT}/asv_machines/ci_machine.json" ]; then
  mkdir -p "${REPO_ROOT}/asv_results/temple-ci-gh-actions"
  cp "${REPO_ROOT}/asv_machines/ci_machine.json" "${REPO_ROOT}/asv_results/temple-ci-gh-actions/machine.json"
  echo "Copied deterministic machine JSON into asv_results/temple-ci-gh-actions/machine.json"
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
# Avoid passing `--repo` to `asv run` — some installed ASV versions
# do not accept that flag. `asv.conf.json` already specifies the repo.
asv run --quick --machine "temple-ci-gh-actions" || true
'

RC=$?
if [ $RC -eq 0 ]; then
  echo "Podman ASV run completed (exit code 0)."
else
  echo "Podman ASV run exited with code $RC" >&2
fi

exit $RC
