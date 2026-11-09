#!/usr/bin/env bash
# Build the NeuroQuest image and start a long-lived container to send commands to.
#
#   scripts/start.sh              build (cached) and start
#   scripts/start.sh --rebuild    rebuild without cache, then start
#   docker exec neuroquest neuroquest review A G N
#   scripts/stop.sh
#
# The repository is mounted read-only at /repo and is the working directory, so the app
# reads /repo/.env itself (pydantic-settings handles quoted JSON; docker --env-file does not).
# Secrets never enter the image or `docker inspect`. Run history lives in the neuroquest-var volume.
set -euo pipefail

NAME=neuroquest
IMAGE=neuroquest
VOLUME=neuroquest-var
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

build_args=()
case "${1:-}" in
  "") ;;
  --rebuild) build_args+=(--no-cache) ;;
  -h|--help) sed -n '2,10p' "$0"; exit 0 ;;
  *) echo "Unknown option: $1 (use --rebuild or --help)" >&2; exit 2 ;;
esac

docker info >/dev/null 2>&1 || { echo "Docker is not running. Start Docker Desktop and retry." >&2; exit 1; }
[[ -f "$ROOT/.env" ]] || { echo "No .env in $ROOT. Copy .env.example to .env and add your keys." >&2; exit 1; }

if docker ps --format '{{.Names}}' | grep -qx "$NAME"; then
  echo "Container '$NAME' is already running. Use scripts/stop.sh first to restart it."
  exit 0
fi
docker rm "$NAME" >/dev/null 2>&1 || true  # a stopped leftover with the same name

echo "Building image '$IMAGE'..."
docker build ${build_args[@]+"${build_args[@]}"} -t "$IMAGE" "$ROOT"

echo "Starting container '$NAME'..."
docker run -d --name "$NAME" \
  -w /repo \
  -v "$ROOT":/repo:ro \
  -v "$VOLUME":/var/lib/neuroquest \
  --entrypoint sleep \
  "$IMAGE" infinity >/dev/null

# Fail fast if configuration is broken (prints model names only, never keys).
docker exec "$NAME" python -c '
from neuroquest.settings import Settings
from neuroquest.service import PIPELINE_TIERS
s = Settings()
for t in PIPELINE_TIERS:
    m = s.model_for(t); s.price_for(m); print(f"  {t}: {m}")
for p in sorted(s.providers_in_use(PIPELINE_TIERS)):
    s.api_key_for(p)
' || { echo "Configuration check failed; see the message above. Container left running for inspection." >&2; exit 1; }

cat <<EOF
Container '$NAME' is running.
  Review:    docker exec $NAME neuroquest review A G N
  Runs:      docker exec $NAME neuroquest runs
  Decide:    docker exec $NAME neuroquest decide <run_id> -d A=follow-up --reason "..."
  Stop:      scripts/stop.sh
EOF
