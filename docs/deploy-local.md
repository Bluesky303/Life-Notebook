# Local Deploy Guide

This project currently targets single-machine deployment on your laptop.

## 1) Backup Data
```bash
powershell -ExecutionPolicy Bypass -File scripts/backup-data.ps1
```
- Output: zip archives in `backup/` named `data-backup-YYYYMMDD-HHMMSS.zip`.
- Old archives are auto-cleaned (default keep: 30 days).

## 2) Verify Data Integrity
```bash
powershell -ExecutionPolicy Bypass -File scripts/verify-data.ps1
```
- Validates required files in `backend/data/` and basic JSON structure.

## 3) One-Click Local Deploy
```bash
powershell -ExecutionPolicy Bypass -File scripts/deploy-local.ps1
```
- Runs backup + verify first.
- Installs dependencies (`uv sync`, `npm install`) by default.
- Starts backend and frontend in new PowerShell windows.

## Optional Flags
- Skip dependency install:
```bash
powershell -ExecutionPolicy Bypass -File scripts/deploy-local.ps1 -SkipInstall
```
- Start backend only:
```bash
powershell -ExecutionPolicy Bypass -File scripts/deploy-local.ps1 -SkipFrontend
```
- Start frontend only:
```bash
powershell -ExecutionPolicy Bypass -File scripts/deploy-local.ps1 -SkipBackend
```
