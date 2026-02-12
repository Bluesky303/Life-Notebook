param(
  [string]$DataDir = "backend/data"
)

$ErrorActionPreference = "Stop"

function Assert-True {
  param(
    [bool]$Condition,
    [string]$Message
  )

  if (-not $Condition) {
    throw $Message
  }
}

function Has-Prop {
  param(
    $Object,
    [string]$Name
  )

  return $null -ne ($Object.PSObject.Properties[$Name])
}

function Read-JsonFile {
  param([string]$Path)

  $raw = Get-Content -Raw -Encoding utf8 -Path $Path
  Assert-True ($raw.Trim().Length -gt 0) "JSON file is empty: $Path"
  return $raw | ConvertFrom-Json
}

$repoRoot = Split-Path -Parent $PSScriptRoot
$resolvedDataDir = Join-Path $repoRoot $DataDir

Assert-True (Test-Path $resolvedDataDir) "Data directory not found: $resolvedDataDir"

$required = @(
  "tasks.json",
  "feed.json",
  "knowledge.json",
  "sleep.json",
  "assets.json",
  "settings.json"
)

foreach ($file in $required) {
  $fullPath = Join-Path $resolvedDataDir $file
  Assert-True (Test-Path $fullPath) "Missing data file: $file"
}

$tasks = Read-JsonFile (Join-Path $resolvedDataDir "tasks.json")
Assert-True ($tasks -is [System.Array]) "tasks.json must be an array"
foreach ($row in $tasks) {
  Assert-True (Has-Prop $row "id") "tasks.json entry missing id"
  Assert-True (Has-Prop $row "title") "tasks.json entry missing title"
  Assert-True (Has-Prop $row "importance") "tasks.json entry missing importance"
}

$feed = Read-JsonFile (Join-Path $resolvedDataDir "feed.json")
Assert-True ($feed -is [System.Array]) "feed.json must be an array"

$knowledge = Read-JsonFile (Join-Path $resolvedDataDir "knowledge.json")
Assert-True ($knowledge -is [System.Array]) "knowledge.json must be an array"
foreach ($row in $knowledge) {
  Assert-True (Has-Prop $row "id") "knowledge.json entry missing id"
  Assert-True (Has-Prop $row "kind") "knowledge.json entry missing kind"
  Assert-True (Has-Prop $row "markdown") "knowledge.json entry missing markdown"
}

$sleep = Read-JsonFile (Join-Path $resolvedDataDir "sleep.json")
Assert-True ($sleep -is [System.Array]) "sleep.json must be an array"
foreach ($row in $sleep) {
  Assert-True (Has-Prop $row "id") "sleep.json entry missing id"
  Assert-True (Has-Prop $row "start_at") "sleep.json entry missing start_at"
  Assert-True (Has-Prop $row "end_at") "sleep.json entry missing end_at"
}

$assets = Read-JsonFile (Join-Path $resolvedDataDir "assets.json")
Assert-True (Has-Prop $assets "accounts") "assets.json missing accounts"
Assert-True (Has-Prop $assets "transactions") "assets.json missing transactions"
Assert-True (Has-Prop $assets "investment_logs") "assets.json missing investment_logs"

$settings = Read-JsonFile (Join-Path $resolvedDataDir "settings.json")
Assert-True (Has-Prop $settings "default_provider") "settings.json missing default_provider"
Assert-True (Has-Prop $settings "model_name") "settings.json missing model_name"
Assert-True (Has-Prop $settings "theme") "settings.json missing theme"
Assert-True (Has-Prop $settings "local_only") "settings.json missing local_only"

Write-Output "Data verification passed."
