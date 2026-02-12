# MCP Server (Codex)

This project includes a local MCP server so Codex can read/write notebook data through controlled tools.

## Location

- Server module: `backend/mcp_server/server.py`
- Run command:

```powershell
cd backend
uv run python -m mcp_server.server
```

The server runs over stdio (MCP default transport).

## Tool Groups

- Tasks:
  - `task_list`
  - `task_create` (supports planned/actual time, status, note, type, recurring template fields)
  - `task_update` (supports planned/actual time, status, note, type, completed_at, recurring template fields)
  - `task_mark_done`
  - `task_delete` (requires `confirm=true`)
- Tasks also include sleep entries via `task_create`/`task_update` with `type="sleep"`.
- Feed:
  - `feed_list`
  - `feed_add`
- Knowledge:
  - `knowledge_list`
  - `knowledge_add`
  - `knowledge_delete` (requires `confirm=true`)
- Assets:
  - `asset_list_accounts`
  - `asset_cash_total`
  - `asset_record_transaction`
- Settings:
  - `settings_get`
  - `settings_update`
- Utility:
  - `health_ping`

## Safety

- Destructive tools require `confirm=true`.
- All write operations append an audit line to:
  - `backend/data/mcp_audit.log`

## Suggested Codex MCP Config

Use this command for the server entry:

```json
{
  "mcpServers": {
    "life-notebook": {
      "command": "uv",
      "args": [
        "run",
        "python",
        "-m",
        "mcp_server.server"
      ],
      "cwd": "C:/Users/Blue_sky303/Arepo/ai-life-notebook/backend"
    }
  }
}
```

Adjust `cwd` if your repo path changes.
