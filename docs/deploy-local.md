# Local Deploy Guide

This project currently targets single-machine deployment on your laptop.

## 1) Initialize Data (clean clone safe)
```bash
powershell -ExecutionPolicy Bypass -File scripts/init-data.ps1
```
- Creates missing files in `backend/data/` with safe defaults.
- Fresh installs start with empty records; wallet/investment accounts are pre-created with `0.00` balance.
- Tasks now persist to SQLite database: `backend/data/life_notebook.db`.

## 2) Backup Data
```bash
powershell -ExecutionPolicy Bypass -File scripts/backup-data.ps1
```
- Output: zip archives in `backup/` named `data-backup-YYYYMMDD-HHMMSS.zip`.
- Old archives are auto-cleaned (default keep: 30 days).

## 3) Verify Data Integrity
```bash
powershell -ExecutionPolicy Bypass -File scripts/verify-data.ps1
```
- Validates required files in `backend/data/` and basic JSON structure.

## 4) One-Click Local Deploy
```bash
powershell -ExecutionPolicy Bypass -File scripts/deploy-local.ps1
```
- Runs initialize + backup + verify first.
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
