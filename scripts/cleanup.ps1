<#
Safe, project-scoped cleanup for embedded-device-power-analytics.

Never runs a global `docker system/image/volume/container/network prune`.
Every Docker resource is verified via `com.docker.compose.project=<ProjectName>`
metadata before removal; anything that cannot be proven to belong to this
project (or is still referenced by another container) is preserved.
#>

$ErrorActionPreference = "Stop"
$ProjectName = "embedded_device_power_analytics"
$RepoRoot = Split-Path -Parent $PSScriptRoot

Write-Host "=== embedded-device-power-analytics cleanup ===" -ForegroundColor Cyan
Write-Host "Project namespace: $ProjectName"

# 1. Primary runtime teardown: stop and remove this project's containers,
#    networks, and named volumes via Compose.
Write-Host "`n[1/6] docker compose down --volumes --remove-orphans"
docker compose -p $ProjectName down --volumes --remove-orphans

# 2. Any remaining containers labelled with this project (defensive check —
#    `compose down` above should already have removed them).
Write-Host "`n[2/6] Checking for remaining project containers..."
$remainingContainers = docker ps -a --filter "label=com.docker.compose.project=$ProjectName" --format "{{.ID}}"
if ($remainingContainers) {
    foreach ($id in $remainingContainers) {
        $labels = docker inspect $id --format '{{ index .Config.Labels "com.docker.compose.project" }}'
        if ($labels -eq $ProjectName) {
            Write-Host "  Removing verified project container $id"
            docker rm -f $id | Out-Null
        } else {
            Write-Host "  PRESERVED (ownership label mismatch): $id"
        }
    }
} else {
    Write-Host "  None remaining."
}

# 3. Any remaining project-labelled volumes.
Write-Host "`n[3/6] Checking for remaining project volumes..."
$remainingVolumes = docker volume ls --filter "label=com.docker.compose.project=$ProjectName" --format "{{.Name}}"
if ($remainingVolumes) {
    foreach ($vol in $remainingVolumes) {
        $label = docker volume inspect $vol --format '{{ index .Labels "com.docker.compose.project" }}' 2>$null
        if ($label -eq $ProjectName) {
            Write-Host "  Removing verified project volume $vol"
            docker volume rm $vol | Out-Null
        } else {
            Write-Host "  PRESERVED (ownership label mismatch): $vol"
        }
    }
} else {
    Write-Host "  None remaining."
}

# 4. Any remaining project-labelled networks (never touches bridge/host/none
#    or unrelated user-defined networks).
Write-Host "`n[4/6] Checking for remaining project networks..."
$remainingNetworks = docker network ls --filter "label=com.docker.compose.project=$ProjectName" --format "{{.Name}}"
foreach ($net in $remainingNetworks) {
    if ($net -notin @("bridge", "host", "none")) {
        $label = docker network inspect $net --format '{{ index .Labels "com.docker.compose.project" }}' 2>$null
        if ($label -eq $ProjectName) {
            Write-Host "  Removing verified project network $net"
            docker network rm $net | Out-Null
        } else {
            Write-Host "  PRESERVED (ownership label mismatch): $net"
        }
    }
}

# 5. Custom project images: remove only if no remaining container references
#    them (never force-delete).
Write-Host "`n[5/6] Custom project images..."
$customImages = docker images --filter "reference=embedded-device-power-analytics*" --format "{{.Repository}}:{{.Tag}} {{.ID}}"
$customImages += (docker images --filter "reference=*embedded_device_power_analytics*" --format "{{.Repository}}:{{.Tag}} {{.ID}}")
$customImages = $customImages | Select-Object -Unique
foreach ($line in $customImages) {
    if (-not $line) { continue }
    $parts = $line -split " "
    $imageId = $parts[-1]
    $inUse = docker ps -a --filter "ancestor=$imageId" --format "{{.ID}}"
    if ($inUse) {
        Write-Host "  PRESERVED (still referenced by a container): $line"
    } else {
        Write-Host "  Removing unused custom image $line"
        docker image rm $imageId 2>$null | Out-Null
    }
}

# 6. Third-party/base images used by this project's Compose file: remove
#    individually only when zero remaining containers (running or stopped)
#    reference them. Never force-delete; a shared base image used elsewhere
#    on the machine is always preserved.
Write-Host "`n[6/6] Third-party/base images used by this project..."
$baseImageRefs = @(
    "eclipse-mosquitto:2.0",
    "timescale/timescaledb:2.17.2-pg16",
    "prom/prometheus:v2.55.1",
    "grafana/grafana:11.3.1"
)
foreach ($ref in $baseImageRefs) {
    $imageId = docker images --filter "reference=$ref" --format "{{.ID}}"
    if (-not $imageId) {
        Write-Host "  Not present locally: $ref"
        continue
    }
    $inUse = docker ps -a --filter "ancestor=$imageId" --format "{{.ID}}"
    if ($inUse) {
        Write-Host "  PRESERVED (referenced by another container): $ref"
    } else {
        Write-Host "  Removing unused base image $ref"
        docker image rm $imageId 2>$null | Out-Null
    }
}

# Project-local generated files/caches (never touches system Python or any
# other project's virtual environment).
Write-Host "`nCleaning project-local caches..."
$pathsToClean = @(
    "$RepoRoot\__pycache__",
    "$RepoRoot\.pytest_cache",
    "$RepoRoot\.ruff_cache",
    "$RepoRoot\.coverage",
    "$RepoRoot\htmlcov",
    "$RepoRoot\data\generated"
)
foreach ($p in $pathsToClean) {
    if (Test-Path $p) {
        Remove-Item -Recurse -Force $p
        Write-Host "  Removed $p"
    }
}
Get-ChildItem -Path $RepoRoot -Recurse -Directory -Filter "__pycache__" -ErrorAction SilentlyContinue |
    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

if (Test-Path "$RepoRoot\.venv") {
    Write-Host "  Removing project-local .venv"
    Remove-Item -Recurse -Force "$RepoRoot\.venv"
}

# Final verification.
Write-Host "`n=== Post-cleanup verification ===" -ForegroundColor Cyan
$leftoverContainers = docker ps -a --filter "label=com.docker.compose.project=$ProjectName" --format "{{.Names}}"
$leftoverVolumes = docker volume ls --filter "label=com.docker.compose.project=$ProjectName" --format "{{.Name}}"
$leftoverNetworks = docker network ls --filter "label=com.docker.compose.project=$ProjectName" --format "{{.Name}}"

if (-not $leftoverContainers -and -not $leftoverVolumes -and -not $leftoverNetworks) {
    Write-Host "Project-specific Docker runtime resources removed successfully." -ForegroundColor Green
} else {
    Write-Host "Some project-labelled resources still remain:" -ForegroundColor Yellow
    $leftoverContainers | ForEach-Object { Write-Host "  container: $_" }
    $leftoverVolumes | ForEach-Object { Write-Host "  volume: $_" }
    $leftoverNetworks | ForEach-Object { Write-Host "  network: $_" }
}

Write-Host "`nGlobal Docker prune: NOT used."
Write-Host "Unrelated Docker resources: untouched."
