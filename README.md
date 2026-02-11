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
