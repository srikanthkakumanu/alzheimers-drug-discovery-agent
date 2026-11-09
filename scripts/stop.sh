#!/usr/bin/env bash
# Stop and remove the NeuroQuest container. Run history (neuroquest-var volume) is kept.
#
#   scripts/stop.sh           stop and remove the container
#   scripts/stop.sh --purge   also delete the run-history volume (asks first)
set -euo pipefail

NAME=neuroquest
VOLUME=neuroquest-var

purge=false
case "${1:-}" in
  "") ;;
  --purge) purge=true ;;
  -h|--help) sed -n '2,5p' "$0"; exit 0 ;;
  *) echo "Unknown option: $1 (use --purge or --help)" >&2; exit 2 ;;
esac

docker info >/dev/null 2>&1 || { echo "Docker is not running; nothing to stop." >&2; exit 0; }

if docker ps -a --format '{{.Names}}' | grep -qx "$NAME"; then
  docker rm -f "$NAME" >/dev/null
  echo "Container '$NAME' stopped and removed."
else
  echo "No container named '$NAME'."
fi

if $purge; then
  if docker volume inspect "$VOLUME" >/dev/null 2>&1; then
    read -r -p "Delete volume '$VOLUME' with all run history and human decisions? [y/N] " answer
    if [[ "$answer" == "y" || "$answer" == "Y" ]]; then
      docker volume rm "$VOLUME" >/dev/null
      echo "Volume '$VOLUME' deleted."
    else
      echo "Kept volume '$VOLUME'."
    fi
  else
    echo "No volume named '$VOLUME'."
  fi
else
  echo "Run history kept in volume '$VOLUME' (scripts/stop.sh --purge to delete)."
fi
