# Backend (FastAPI + uv)

## Run
```bash
uv sync
uv run uvicorn app.main:app --reload
```

## API Overview
- `GET /health/`: health check
- `POST /ai/chat`: AI gateway entry
- `GET/POST /tasks/`: task list/create
- `DELETE /tasks/{id}`: delete task
- `GET/POST /assets/transactions`: wallet transaction list/create
- `DELETE /assets/transactions/{id}`: delete transaction
- `GET /assets/cash-total`: cash total summary
- `GET /assets/accounts`: account list
- `GET /assets/category-summary`: category summary
- `GET /assets/monthly-summary`: monthly summary
- `GET/POST /assets/investment/logs`: investment logs list/create
- `DELETE /assets/investment/logs/{id}`: delete investment log
- `GET/POST /feed/`: activity feed
- `DELETE /feed/{id}`: delete activity
- `GET/POST /knowledge/`: knowledge entries
- `DELETE /knowledge/{id}`: delete entry
- `GET/PUT /settings/`: app settings

## Persistence
- Data is persisted as JSON files in `backend/data/`.
- Current files: `tasks.json`, `feed.json`, `knowledge.json`, `assets.json`, `settings.json`.
