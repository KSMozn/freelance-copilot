<#
.SYNOPSIS
  One-shot setup / build / run for the Careero monorepo (native PowerShell).

.DESCRIPTION
  Prep + run, with visible step-by-step output:
    1. Start Docker Desktop if the engine is down (and wait for it).
    2. Free the app ports (5173, 8000, 5432) from stray host processes.
    3. Bootstrap .env from .env.example if missing.
    4. Build images (cached; skip with -NoBuild).
    5. Start the stack detached (db + backend + frontend).
    6. Wait until backend + frontend report healthy.
    7. Stream all logs live in the foreground (skip with -Detach).

  The stack runs in the BACKGROUND (containers have restart: unless-stopped).
  The final live log tail is just a viewer: Ctrl-C detaches it, the stack
  keeps running. The backend applies `alembic upgrade head` on boot.

.EXAMPLE
  .\start.ps1                     # prep + build + start, then stream logs live
  .\start.ps1 -Detach             # same, but don't attach to logs at the end
  .\start.ps1 -NoBuild            # start without rebuilding images
  .\start.ps1 -Admin you@x.com    # also create/reset an admin user
  .\start.ps1 -Logs               # just attach to logs of the running stack
  .\start.ps1 -FreePorts          # just free ports 5173/8000/5432 and exit
  .\start.ps1 -Down               # stop the stack and exit
#>
[CmdletBinding()]
param(
  [switch]$Down,
  [switch]$NoBuild,
  [switch]$Detach,
  [switch]$Logs,
  [switch]$FreePorts,
  [string]$Admin
)

$ErrorActionPreference = 'Continue'
if (Test-Path variable:PSNativeCommandUseErrorActionPreference) {
  $PSNativeCommandUseErrorActionPreference = $false
}
Set-Location -LiteralPath $PSScriptRoot -ErrorAction Stop

$Ports = 5173, 8000, 5432   # frontend, backend, db (from docker-compose.yml)

function Info($m) { Write-Host "==> $m" -ForegroundColor Green }
function Warn($m) { Write-Host "==> $m" -ForegroundColor Yellow }
function Die($m)  { Write-Host "error: $m" -ForegroundColor Red; exit 1 }

function Clear-AppPorts {
  Info "Releasing our stack's ports (docker compose down)..."
  docker compose down --remove-orphans 2>$null

  Info "Freeing app ports from stray processes ($($Ports -join ', '))..."
  foreach ($p in $Ports) {
    $conns = Get-NetTCPConnection -LocalPort $p -State Listen -ErrorAction SilentlyContinue
    if (-not $conns) { continue }
    foreach ($procId in @($conns.OwningProcess | Sort-Object -Unique)) {
      $proc = Get-Process -Id $procId -ErrorAction SilentlyContinue
      if (-not $proc) { continue }
      if ($proc.ProcessName -match 'docker|vpnkit|wslrelay|dockerd') {
        Write-Host "   port $p held by Docker ($($proc.ProcessName)) - leaving it"
        continue
      }
      Write-Host "   port $p held by $($proc.ProcessName) (PID $procId) - killing" -ForegroundColor Yellow
      Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
    }
  }
}

# ---- prerequisites ---------------------------------------------------------
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
  Die "Docker is not installed or not on PATH."
}
docker compose version *> $null
if ($LASTEXITCODE -ne 0) { Die "Docker Compose v2 is required (``docker compose``)." }

if ($Down) { Info "Stopping stack..."; docker compose down; exit $LASTEXITCODE }

# ---- -FreePorts: just free the app ports and exit --------------------------
if ($FreePorts) { Clear-AppPorts; Info "Ports freed."; exit 0 }

# ---- -Logs: just attach to the running stack -------------------------------
if ($Logs) {
  Info "Attaching to logs (Ctrl-C to detach; the stack keeps running)..."
  docker compose logs -f --tail=200
  exit $LASTEXITCODE
}

# ---- 1) ensure the Docker engine is running --------------------------------
function Test-DockerUp {
  $null = docker info 2>&1
  return ($LASTEXITCODE -eq 0)
}

if (-not (Test-DockerUp)) {
  Warn "Docker daemon is not running - starting Docker Desktop..."
  $exe = @(
    "$env:ProgramFiles\Docker\Docker\Docker Desktop.exe",
    "${env:ProgramFiles(x86)}\Docker\Docker\Docker Desktop.exe",
    "$env:LOCALAPPDATA\Docker\Docker Desktop.exe"
  ) | Where-Object { $_ -and (Test-Path $_) } | Select-Object -First 1

  if (-not $exe) { Die "Could not locate 'Docker Desktop.exe'. Start Docker Desktop manually and retry." }
  Start-Process -FilePath $exe -ErrorAction Stop | Out-Null

  Write-Host -NoNewline "   waiting for the Docker engine"
  $ok = $false
  foreach ($i in 1..60) {
    if (Test-DockerUp) { $ok = $true; break }
    Write-Host -NoNewline "."; Start-Sleep -Seconds 3
  }
  if ($ok) { Write-Host " OK" -ForegroundColor Green }
  else { Write-Host ""; Die "Docker engine did not come up within ~3 min. Start it manually and retry." }
}

# ---- 2) free the app ports -------------------------------------------------
Clear-AppPorts

# ---- 3) environment --------------------------------------------------------
if (-not (Test-Path .env)) {
  Info "No .env found - creating one from .env.example (dev defaults, all mock providers)."
  Copy-Item .env.example .env -ErrorAction Stop
} else {
  Info "Using existing .env"
}

# ---- 4) build --------------------------------------------------------------
if (-not $NoBuild) {
  Info "Building images (cached; first run takes a few minutes)..."
  docker compose build
  if ($LASTEXITCODE -ne 0) { Die "docker compose build failed." }
}

# ---- 5) start --------------------------------------------------------------
Info "Starting the stack in the background (db -> backend -> frontend)..."
docker compose up -d
if ($LASTEXITCODE -ne 0) { Die "docker compose up failed." }

# ---- 6) wait for health ----------------------------------------------------
function Wait-Healthy($svc, $tries = 60) {
  Write-Host -NoNewline "   waiting for $svc"
  foreach ($i in 1..$tries) {
    $status = (docker compose ps --format '{{.Health}}' $svc 2>$null | Select-Object -First 1)
    switch ($status) {
      'healthy'   { Write-Host " OK" -ForegroundColor Green; return $true }
      'unhealthy' { Write-Host " FAILED" -ForegroundColor Red; return $false }
    }
    Write-Host -NoNewline "."; Start-Sleep -Seconds 3
  }
  Write-Host " (timeout)" -ForegroundColor Yellow
  return $false
}

$healthOk = $true
if (-not (Wait-Healthy 'backend'))  { $healthOk = $false }
if (-not (Wait-Healthy 'frontend')) { $healthOk = $false }

# ---- optional admin bootstrap ---------------------------------------------
if ($Admin) {
  Info "Creating/resetting admin user: $Admin"
  docker compose exec -e ADMIN_EMAIL=$Admin backend python -m app.scripts.create_admin
}

# ---- summary ---------------------------------------------------------------
Write-Host ""
if ($healthOk) { Info "Stack is up and healthy - running in the background." }
else { Warn "Stack started but not all services reported healthy yet - watch the logs below." }

Write-Host ""
Write-Host "  Frontend   http://localhost:5173   (app + admin surfaces, hostname/?surface= gated)"
Write-Host "  Backend    http://localhost:8000/api/v1"
Write-Host "  Health     http://localhost:8000/api/v1/health"
Write-Host "  Dev email  http://localhost:8000/api/v1/dev/emails   (captured OTP codes + reset links)"
Write-Host ""
Write-Host "  Stop:        .\start.ps1 -Down   (or: docker compose down)" -ForegroundColor DarkGray
Write-Host "  Re-attach:   .\start.ps1 -Logs" -ForegroundColor DarkGray
Write-Host "  Admin user:  .\start.ps1 -Admin you@example.com" -ForegroundColor DarkGray
Write-Host ""

# ---- 7) stream logs live (default) -----------------------------------------
if ($Detach) {
  Info "Stack is detached. Attach anytime with:  .\start.ps1 -Logs"
  exit 0
}

Info "Streaming live logs (Ctrl-C detaches - the stack KEEPS RUNNING in the background)..."
Write-Host ""
docker compose logs -f --tail=100
