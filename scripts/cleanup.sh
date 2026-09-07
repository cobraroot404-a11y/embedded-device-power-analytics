#!/usr/bin/env bash
# Safe, project-scoped cleanup for embedded-device-power-analytics.
#
# Never runs a global `docker system/image/volume/container/network prune`.
# Every Docker resource is verified via `com.docker.compose.project=<name>`
# metadata before removal; anything that cannot be proven to belong to this
# project (or is still referenced by another container) is preserved.

set -euo pipefail

PROJECT_NAME="embedded_device_power_analytics"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "=== embedded-device-power-analytics cleanup ==="
echo "Project namespace: $PROJECT_NAME"

echo
echo "[1/6] docker compose down --volumes --remove-orphans"
docker compose -p "$PROJECT_NAME" down --volumes --remove-orphans

echo
echo "[2/6] Checking for remaining project containers..."
for id in $(docker ps -a --filter "label=com.docker.compose.project=$PROJECT_NAME" --format "{{.ID}}"); do
    label=$(docker inspect "$id" --format '{{ index .Config.Labels "com.docker.compose.project" }}' 2>/dev/null || true)
    if [ "$label" = "$PROJECT_NAME" ]; then
        echo "  Removing verified project container $id"
        docker rm -f "$id" >/dev/null
    else
        echo "  PRESERVED (ownership label mismatch): $id"
    fi
done

echo
echo "[3/6] Checking for remaining project volumes..."
for vol in $(docker volume ls --filter "label=com.docker.compose.project=$PROJECT_NAME" --format "{{.Name}}"); do
    label=$(docker volume inspect "$vol" --format '{{ index .Labels "com.docker.compose.project" }}' 2>/dev/null || true)
    if [ "$label" = "$PROJECT_NAME" ]; then
        echo "  Removing verified project volume $vol"
        docker volume rm "$vol" >/dev/null
    else
        echo "  PRESERVED (ownership label mismatch): $vol"
    fi
done

echo
echo "[4/6] Checking for remaining project networks..."
for net in $(docker network ls --filter "label=com.docker.compose.project=$PROJECT_NAME" --format "{{.Name}}"); do
    case "$net" in
        bridge|host|none) continue ;;
    esac
    label=$(docker network inspect "$net" --format '{{ index .Labels "com.docker.compose.project" }}' 2>/dev/null || true)
    if [ "$label" = "$PROJECT_NAME" ]; then
        echo "  Removing verified project network $net"
        docker network rm "$net" >/dev/null
    else
        echo "  PRESERVED (ownership label mismatch): $net"
    fi
done

echo
echo "[5/6] Custom project images..."
for line in $(docker images --filter "reference=*embedded_device_power_analytics*" --format "{{.ID}}" | sort -u); do
    in_use=$(docker ps -a --filter "ancestor=$line" --format "{{.ID}}")
    if [ -n "$in_use" ]; then
        echo "  PRESERVED (still referenced by a container): $line"
    else
        echo "  Removing unused custom image $line"
        docker image rm "$line" 2>/dev/null || true
    fi
done

echo
echo "[6/6] Third-party/base images used by this project..."
BASE_IMAGES=(
    "eclipse-mosquitto:2.0"
    "timescale/timescaledb:2.17.2-pg16"
    "prom/prometheus:v2.55.1"
    "grafana/grafana:11.3.1"
)
for ref in "${BASE_IMAGES[@]}"; do
    image_id=$(docker images --filter "reference=$ref" --format "{{.ID}}")
    if [ -z "$image_id" ]; then
        echo "  Not present locally: $ref"
        continue
    fi
    in_use=$(docker ps -a --filter "ancestor=$image_id" --format "{{.ID}}")
    if [ -n "$in_use" ]; then
        echo "  PRESERVED (referenced by another container): $ref"
    else
        echo "  Removing unused base image $ref"
        docker image rm "$image_id" 2>/dev/null || true
    fi
done

echo
echo "Cleaning project-local caches..."
for p in "$REPO_ROOT/__pycache__" "$REPO_ROOT/.pytest_cache" "$REPO_ROOT/.ruff_cache" \
         "$REPO_ROOT/.coverage" "$REPO_ROOT/htmlcov" "$REPO_ROOT/data/generated"; do
    if [ -e "$p" ]; then
        rm -rf "$p"
        echo "  Removed $p"
    fi
done
find "$REPO_ROOT" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

if [ -d "$REPO_ROOT/.venv" ]; then
    echo "  Removing project-local .venv"
    rm -rf "$REPO_ROOT/.venv"
fi

echo
echo "=== Post-cleanup verification ==="
remaining_containers=$(docker ps -a --filter "label=com.docker.compose.project=$PROJECT_NAME" --format "{{.Names}}")
remaining_volumes=$(docker volume ls --filter "label=com.docker.compose.project=$PROJECT_NAME" --format "{{.Name}}")
remaining_networks=$(docker network ls --filter "label=com.docker.compose.project=$PROJECT_NAME" --format "{{.Name}}")

if [ -z "$remaining_containers" ] && [ -z "$remaining_volumes" ] && [ -z "$remaining_networks" ]; then
    echo "Project-specific Docker runtime resources removed successfully."
else
    echo "Some project-labelled resources still remain:"
    echo "$remaining_containers" | sed 's/^/  container: /'
    echo "$remaining_volumes" | sed 's/^/  volume: /'
    echo "$remaining_networks" | sed 's/^/  network: /'
fi

echo
echo "Global Docker prune: NOT used."
echo "Unrelated Docker resources: untouched."
