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
- `GET /tasks/day?date_str=YYYY-MM-DD`
  - Returns tasks overlapping that day (supports cross-day tasks)
- `POST /tasks/`
  - Body: `{ "title", "category", "type", "status", "importance", "planned_start_at", "planned_end_at", "actual_start_at", "actual_end_at", "completed_at", "note", "is_recurring_template", "recurrence", "template_id" }`
- `PUT /tasks/{task_id}`
  - Body: same fields as above, supports partial update
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

## Sleep (Legacy Compatibility)
- Existing `/sleep/logs` endpoints are retained for compatibility.
- New workflow should manage sleep via `/tasks/` with `type = "sleep"`.

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
- Tasks are persisted in SQLite: `backend/data/life_notebook.db`.
- Other modules currently use JSON files in `backend/data/`.
- Current JSON files:
  - `backend/data/feed.json`
  - `backend/data/knowledge.json`
  - `backend/data/sleep.json`
  - `backend/data/assets.json`
  - `backend/data/settings.json`
