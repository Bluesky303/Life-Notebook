# Backend (FastAPI + uv)

## Run
```bash
uv sync
uv run uvicorn app.main:app --reload
```

## API Overview
- `GET /health/`: health check
- `POST /ai/chat`: AI gateway entry
- `POST /ai/parse-record`: parse natural language into structured suggestion
- `GET/POST /tasks/`: task list/create (task + sleep unified model)
- `PUT /tasks/{id}`: update task fields/status/plan/actual times
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
- `GET /knowledge/{id}`: knowledge entry detail
- `DELETE /knowledge/{id}`: delete entry
- `GET/POST /sleep/logs`: legacy compatibility endpoints
- `DELETE /sleep/logs/{id}`: legacy compatibility endpoint
- `GET/PUT /settings/`: app settings

## Persistence
- Data is persisted as JSON files in `backend/data/`.
- Current files: `tasks.json`, `feed.json`, `knowledge.json`, `sleep.json`, `assets.json`, `settings.json`.

## Reference
- Full API reference: `docs/api-reference.md`
