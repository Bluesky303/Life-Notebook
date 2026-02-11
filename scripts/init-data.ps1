param(
  [string]$DataDir = "backend/data"
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$resolvedDataDir = Join-Path $repoRoot $DataDir

New-Item -ItemType Directory -Force -Path $resolvedDataDir | Out-Null

$defaults = @{
  "tasks.json" = @()
  "feed.json" = @()
  "knowledge.json" = @()
  "assets.json" = @{
    accounts = @()
    transactions = @()
    investment_logs = @()
  }
  "settings.json" = @{
    default_provider = "codex"
    model_name = "gpt-5-codex"
    theme = "sci-fi"
    local_only = $true
  }
}

foreach ($name in $defaults.Keys) {
  $path = Join-Path $resolvedDataDir $name
  if (-not (Test-Path $path)) {
    $json = $defaults[$name] | ConvertTo-Json -Depth 10
    Set-Content -Encoding utf8 -Path $path -Value $json
    Write-Output "Initialized: $path"
  }
}

$gitkeep = Join-Path $resolvedDataDir ".gitkeep"
if (-not (Test-Path $gitkeep)) {
  Set-Content -Encoding utf8 -Path $gitkeep -Value ""
}

Write-Output "Data initialization completed."
