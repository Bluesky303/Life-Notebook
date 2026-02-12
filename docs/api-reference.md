# API Reference

Base URL (local): `http://localhost:8000`

## Health
- `GET /health/`
  - Response: `{ "status": "ok" }`

## AI
- `POST /ai/chat`
  - Body: `{ "provider": "codex|openai-compatible|ollama", "session_id": "...", "prompt": "..." }`
- `POST /ai/parse-record`
  - Body: `{ "text": "..." }`
  - Response includes detected type/category and extracted fields.

## Tasks
- `GET /tasks/`
- `POST /tasks/`
  - Body: `{ "title", "category", "importance", "start_at", "end_at" }`
- `DELETE /tasks/{task_id}`

## Feed (Activity)
- `GET /feed/`
- `POST /feed/`
  - Body: `{ "category", "content" }`
- `DELETE /feed/{feed_id}`

## Knowledge
- `GET /knowledge/?kind=entry|blog&q=keyword`
- `GET /knowledge/{entry_id}`
- `POST /knowledge/`
  - Body: `{ "kind": "entry|blog", "title", "markdown" }`
- `DELETE /knowledge/{entry_id}`

## Sleep
- `GET /sleep/logs`
- `POST /sleep/logs`
  - Body: `{ "start_at", "end_at", "note" }`
- `DELETE /sleep/logs/{log_id}`

## Assets
### Accounts
- `GET /assets/accounts`

### Transactions
- `GET /assets/transactions?category=...&month=YYYY-MM`
- `POST /assets/transactions`
  - Body: `{ "account", "type": "income|expense", "category", "amount", "happened_on", "note" }`
- `DELETE /assets/transactions/{transaction_id}`

### Summary
- `GET /assets/cash-total`
- `GET /assets/category-summary?month=YYYY-MM`
- `GET /assets/monthly-summary`

### Investment Logs
- `GET /assets/investment/logs`
- `POST /assets/investment/logs`
  - Body: `{ "happened_on", "invested", "daily_profit", "note" }`
- `DELETE /assets/investment/logs/{log_id}`
- `GET /assets/investment/trend`

## Settings
- `GET /settings/`
- `PUT /settings/`
  - Body: `{ "default_provider", "model_name", "theme", "local_only" }`

## Persistence
- Data files are persisted in `backend/data/`.
- Current files:
  - `backend/data/tasks.json`
  - `backend/data/feed.json`
  - `backend/data/knowledge.json`
  - `backend/data/sleep.json`
  - `backend/data/assets.json`
  - `backend/data/settings.json`
