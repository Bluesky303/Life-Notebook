param(
  [string]$DataDir = "backend/data"
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$resolvedDataDir = Join-Path $repoRoot $DataDir

New-Item -ItemType Directory -Force -Path $resolvedDataDir | Out-Null

function Convert-ToStableJson {
  param($Value)

  if ($Value -is [System.Array] -and $Value.Count -eq 0) {
    return "[]"
  }

  return $Value | ConvertTo-Json -Depth 10
}

$defaults = @{
  "tasks.json" = @()
  "feed.json" = @()
  "knowledge.json" = @()
  "sleep.json" = @()
  "assets.json" = @{
    accounts = @(
      @{
        name = "微信钱包"
        is_cash = $true
        balance = "0.00"
      },
      @{
        name = "支付宝钱包"
        is_cash = $true
        balance = "0.00"
      },
      @{
        name = "支付宝理财"
        is_cash = $false
        balance = "0.00"
      }
    )
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
    $json = Convert-ToStableJson $defaults[$name]
    Set-Content -Encoding utf8 -Path $path -Value $json
    Write-Output "Initialized: $path"
  }
}

$gitkeep = Join-Path $resolvedDataDir ".gitkeep"
if (-not (Test-Path $gitkeep)) {
  Set-Content -Encoding utf8 -Path $gitkeep -Value ""
}

Write-Output "Data initialization completed."
