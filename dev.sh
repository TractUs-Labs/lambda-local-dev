#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VALID_SERVICES=$(python3 -c "
import json
svcs = json.load(open('$SCRIPT_DIR/services.json'))['services']
print(' '.join(s['name'] for s in svcs))
")

if [[ $# -eq 0 ]]; then
  echo "Usage: ./dev.sh <service> [service...] | --all | stop | restart <service> [--sam]"
  echo "Services: $VALID_SERVICES"
  exit 1
fi

if [[ "$1" == "--all" ]]; then
  exec overmind start
fi

if [[ "$1" == "stop" ]]; then
  exec overmind stop
fi

if [[ "$1" == "restart" ]]; then
  if [[ $# -lt 2 ]]; then
    echo "Usage: ./dev.sh restart <service> [--sam]"
    exit 1
  fi
  svc="$2"
  if ! echo "$VALID_SERVICES" | grep -qw "$svc"; then
    echo "Unknown service: $svc"
    echo "Valid services: $VALID_SERVICES"
    exit 1
  fi
  if [[ $# -eq 2 ]]; then
    exec overmind restart "${svc}-sam" "${svc}-proxy" "${svc}-tunnel"
  fi
  if [[ $# -eq 3 && "$3" == "--sam" ]]; then
    # Restart SAM only — keeps proxy and tunnel (and tunnel URL) running
    exec overmind restart "${svc}-sam"
  fi
  echo "Usage: ./dev.sh restart <service> [--sam]"
  exit 1
fi

procs=""
for svc in "$@"; do
  if ! echo "$VALID_SERVICES" | grep -qw "$svc"; then
    echo "Unknown service: $svc"
    echo "Valid services: $VALID_SERVICES"
    exit 1
  fi
  procs="${procs:+$procs,}${svc}-sam,${svc}-proxy,${svc}-tunnel"
done

exec overmind start -l "$procs"
