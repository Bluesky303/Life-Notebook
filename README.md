# AI Life Notebook

Monorepo for a personal AI-managed life notebook.

## Tech Stack
- Frontend: Next.js (App Router + TypeScript)
- Backend: FastAPI (Python, managed by uv)
- Database: PostgreSQL (planned, SQLAlchemy-ready structure)

## Structure
- `frontend/`: Web app UI
- `backend/`: API and AI gateway
- `docs/`: Planning docs

## Collaboration
- Branch workflow: `docs/git-workflow.md`
- Development model: GitHub Issue -> `feature/*` -> PR to `dev` -> review -> merge
- API reference: `docs/api-reference.md`
- Local deploy guide: `docs/deploy-local.md`

## Quick Start

### Backend (uv)
```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

Frontend default URL: `http://localhost:3000`
Backend default URL: `http://localhost:8000`

## Local Data Ops
- Initialize missing data files (clean clone safe):
```bash
powershell -ExecutionPolicy Bypass -File scripts/init-data.ps1
```
- Fresh installs start with empty records; wallet/investment accounts are pre-created with `0.00` balance.
- Backup data (zip to `backup/`):
```bash
powershell -ExecutionPolicy Bypass -File scripts/backup-data.ps1
```
- Verify data files before deploy:
```bash
powershell -ExecutionPolicy Bypass -File scripts/verify-data.ps1
```

## One-Click Local Deploy
```bash
powershell -ExecutionPolicy Bypass -File scripts/deploy-local.ps1
```
- This script will:
  - initialize missing data files
  - backup `backend/data` to a zip archive
  - verify data file integrity
  - install dependencies (`uv sync`, `npm install`)
  - start backend and frontend in new PowerShell windows
