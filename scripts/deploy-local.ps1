param(
  [switch]$SkipInstall,
  [switch]$SkipFrontend,
  [switch]$SkipBackend
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot

Write-Output "[1/5] Initializing local data files..."
& (Join-Path $PSScriptRoot "init-data.ps1")

Write-Output "[2/5] Backing up local data..."
& (Join-Path $PSScriptRoot "backup-data.ps1")

Write-Output "[3/5] Verifying local data..."
& (Join-Path $PSScriptRoot "verify-data.ps1")

if (-not $SkipInstall) {
  if (-not $SkipBackend) {
    Write-Output "[4/5] Installing backend dependencies (uv sync)..."
    Push-Location (Join-Path $repoRoot "backend")
    uv sync
    Pop-Location
  }

  if (-not $SkipFrontend) {
    Write-Output "[4/5] Installing frontend dependencies (npm install)..."
    Push-Location (Join-Path $repoRoot "frontend")
    npm install
    Pop-Location
  }
}

Write-Output "[5/5] Starting services..."

if (-not $SkipBackend) {
  $backendDir = Join-Path $repoRoot "backend"
  Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "cd '$backendDir'; uv run uvicorn app.main:app --host 0.0.0.0 --port 8000"
  ) | Out-Null
  Write-Output "Backend started at http://localhost:8000"
}

if (-not $SkipFrontend) {
  $frontendDir = Join-Path $repoRoot "frontend"
  Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "cd '$frontendDir'; npm run dev"
  ) | Out-Null
  Write-Output "Frontend started at http://localhost:3000"
}

Write-Output "Deploy completed."
