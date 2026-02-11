param(
  [string]$DataDir = "backend/data",
  [string]$BackupDir = "backup",
  [int]$KeepDays = 30
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$resolvedDataDir = Join-Path $repoRoot $DataDir
$resolvedBackupDir = Join-Path $repoRoot $BackupDir

if (-not (Test-Path $resolvedDataDir)) {
  throw "Data directory not found: $resolvedDataDir"
}

New-Item -ItemType Directory -Force -Path $resolvedBackupDir | Out-Null

$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$zipPath = Join-Path $resolvedBackupDir ("data-backup-{0}.zip" -f $timestamp)

Compress-Archive -Path (Join-Path $resolvedDataDir "*") -DestinationPath $zipPath -CompressionLevel Optimal -Force

$deadline = (Get-Date).AddDays(-$KeepDays)
Get-ChildItem -Path $resolvedBackupDir -Filter "data-backup-*.zip" |
  Where-Object { $_.LastWriteTime -lt $deadline } |
  ForEach-Object { Remove-Item -Force $_.FullName }

Write-Output "Backup created: $zipPath"
