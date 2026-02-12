from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, ValidationError

from app.core.json_store import DATA_DIR, read_json, write_json
from app.schemas.assets import TransactionCreate, TransactionOut
from app.schemas.tasks import TaskCreate, TaskOut

mcp = FastMCP("life-notebook")

TASKS_FILE = "tasks.json"
FEED_FILE = "feed.json"
KNOWLEDGE_FILE = "knowledge.json"
ASSETS_FILE = "assets.json"
SETTINGS_FILE = "settings.json"

AUDIT_FILE = DATA_DIR / "mcp_audit.log"

DEFAULT_ASSETS = {
    "accounts": [
        {"name": "WeChat Wallet", "is_cash": True, "balance": "0.00"},
        {"name": "Alipay Wallet", "is_cash": True, "balance": "0.00"},
        {"name": "Alipay Investment", "is_cash": False, "balance": "0.00"},
    ],
    "transactions": [],
    "investment_logs": [],
}


class SettingsPayload(BaseModel):
    default_provider: str
    model_name: str
    theme: str
    local_only: bool




DEFAULT_SETTINGS = SettingsPayload(
    default_provider="codex",
    model_name="gpt-5-codex",
    theme="sci-fi",
    local_only=True,
).model_dump(mode="json")


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _append_audit(tool: str, payload: dict[str, Any]) -> None:
    row = {"time": _now_iso(), "tool": tool, "payload": payload}
    line = f"{row}\n"
    AUDIT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with AUDIT_FILE.open("a", encoding="utf-8") as f:
        f.write(line)


def _next_id(rows: list[dict[str, Any]]) -> int:
    return max([int(row.get("id", 0)) for row in rows], default=0) + 1


def _parse_datetime(value: str) -> datetime:
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(text)
    except ValueError as exc:
        raise ValueError("datetime must be ISO8601 format") from exc


def _parse_decimal(amount: str) -> Decimal:
    try:
        value = Decimal(amount)
    except InvalidOperation as exc:
        raise ValueError("amount must be a valid decimal string") from exc
    if value <= 0:
        raise ValueError("amount must be greater than 0")
    return value


def _load_tasks() -> list[TaskOut]:
    rows = read_json(TASKS_FILE, [])
    return [TaskOut.model_validate(row) for row in rows]


def _save_tasks(tasks: list[TaskOut]) -> None:
    write_json(TASKS_FILE, [row.model_dump(mode="json", by_alias=True) for row in tasks])



def _load_feed() -> list[dict[str, Any]]:
    return read_json(FEED_FILE, [])


def _save_feed(rows: list[dict[str, Any]]) -> None:
    write_json(FEED_FILE, rows)


def _load_knowledge() -> list[dict[str, Any]]:
    return read_json(KNOWLEDGE_FILE, [])


def _save_knowledge(rows: list[dict[str, Any]]) -> None:
    write_json(KNOWLEDGE_FILE, rows)


def _load_assets() -> dict[str, Any]:
    return read_json(ASSETS_FILE, DEFAULT_ASSETS)


def _save_assets(state: dict[str, Any]) -> None:
    write_json(ASSETS_FILE, state)


def _load_settings() -> dict[str, Any]:
    return read_json(SETTINGS_FILE, DEFAULT_SETTINGS)


@mcp.tool()
def health_ping() -> dict[str, str]:
    """Health check for MCP server."""
    return {"status": "ok", "time": _now_iso()}


@mcp.tool()
def task_list(limit: int = 50) -> list[dict[str, Any]]:
    """List tasks ordered by id desc."""
    tasks = list(reversed(_load_tasks()))
    return [row.model_dump(mode="json") for row in tasks[: max(1, min(limit, 200))]]


@mcp.tool()
def task_create(
    title: str,
    category: str = "general",
    importance: str = "medium",
    task_type: str = "task",
    status: str = "todo",
    start_at: str | None = None,
    end_at: str | None = None,
    planned_start_at: str | None = None,
    planned_end_at: str | None = None,
    actual_start_at: str | None = None,
    actual_end_at: str | None = None,
    completed_at: str | None = None,
    note: str | None = None,
) -> dict[str, Any]:
    """Create one task."""
    planned_start_dt = _parse_datetime(planned_start_at) if planned_start_at else (_parse_datetime(start_at) if start_at else None)
    planned_end_dt = _parse_datetime(planned_end_at) if planned_end_at else (_parse_datetime(end_at) if end_at else None)
    actual_start_dt = _parse_datetime(actual_start_at) if actual_start_at else None
    actual_end_dt = _parse_datetime(actual_end_at) if actual_end_at else None
    completed_dt = _parse_datetime(completed_at) if completed_at else None

    if planned_start_dt and planned_end_dt and planned_end_dt <= planned_start_dt:
        raise ValueError("end_at must be later than start_at")
    if actual_start_dt and actual_end_dt and actual_end_dt <= actual_start_dt:
        raise ValueError("actual_end_at must be later than actual_start_at")

    try:
        payload = TaskCreate(
            title=title,
            category=category,
            importance=importance,
            type=task_type,
            status=status,
            planned_start_at=planned_start_dt,
            planned_end_at=planned_end_dt,
            actual_start_at=actual_start_dt,
            actual_end_at=actual_end_dt,
            completed_at=completed_dt,
            note=note,
        )
    except ValidationError as exc:
        raise ValueError(str(exc)) from exc

    tasks = _load_tasks()
    next_id = max([row.id for row in tasks], default=0) + 1
    task = TaskOut(id=next_id, **payload.model_dump(by_alias=True))
    tasks.append(task)
    _save_tasks(tasks)
    body = task.model_dump(mode="json")
    _append_audit("task_create", {"id": next_id, "title": title})
    return body


@mcp.tool()
def task_delete(task_id: int, confirm: bool = False) -> dict[str, Any]:
    """Delete one task (confirm=true required)."""
    if not confirm:
        raise ValueError("confirm must be true to delete task")

    tasks = _load_tasks()
    new_rows = [row for row in tasks if row.id != task_id]
    if len(new_rows) == len(tasks):
        raise ValueError("task not found")

    _save_tasks(new_rows)
    _append_audit("task_delete", {"id": task_id})
    return {"deleted": True, "id": task_id}


@mcp.tool()
def task_update(
    task_id: int,
    title: str | None = None,
    category: str | None = None,
    importance: str | None = None,
    task_type: str | None = None,
    status: str | None = None,
    start_at: str | None = None,
    end_at: str | None = None,
    planned_start_at: str | None = None,
    planned_end_at: str | None = None,
    actual_start_at: str | None = None,
    actual_end_at: str | None = None,
    completed_at: str | None = None,
    note: str | None = None,
) -> dict[str, Any]:
    """Update one task. Any None field keeps original value."""
    tasks = _load_tasks()
    target = next((row for row in tasks if row.id == task_id), None)
    if not target:
        raise ValueError("task not found")

    merged = target.model_dump(mode="python")
    if title is not None:
        merged["title"] = title
    if category is not None:
        merged["category"] = category
    if importance is not None:
        merged["importance"] = importance
    if task_type is not None:
        merged["type"] = task_type
    if status is not None:
        merged["status"] = status
    if note is not None:
        merged["note"] = note
    if planned_start_at is not None:
        merged["planned_start_at"] = _parse_datetime(planned_start_at)
    elif start_at is not None:
        merged["planned_start_at"] = _parse_datetime(start_at)
    if planned_end_at is not None:
        merged["planned_end_at"] = _parse_datetime(planned_end_at)
    elif end_at is not None:
        merged["planned_end_at"] = _parse_datetime(end_at)
    if actual_start_at is not None:
        merged["actual_start_at"] = _parse_datetime(actual_start_at)
    if actual_end_at is not None:
        merged["actual_end_at"] = _parse_datetime(actual_end_at)
    if completed_at is not None:
        merged["completed_at"] = _parse_datetime(completed_at)

    if (
        merged.get("planned_start_at")
        and merged.get("planned_end_at")
        and merged["planned_end_at"] <= merged["planned_start_at"]
    ):
        raise ValueError("end_at must be later than start_at")
    if (
        merged.get("actual_start_at")
        and merged.get("actual_end_at")
        and merged["actual_end_at"] <= merged["actual_start_at"]
    ):
        raise ValueError("actual_end_at must be later than actual_start_at")

    updated = TaskOut.model_validate(merged)
    rows = [updated if row.id == task_id else row for row in tasks]
    _save_tasks(rows)
    _append_audit("task_update", {"id": task_id})
    return updated.model_dump(mode="json")


@mcp.tool()
def task_mark_done(task_id: int, done_at: str | None = None) -> dict[str, Any]:
    """Mark one task as done."""
    tasks = _load_tasks()
    target = next((row for row in tasks if row.id == task_id), None)
    if not target:
        raise ValueError("task not found")
    if target.status == "done":
        return target.model_dump(mode="json")

    end_time = _parse_datetime(done_at) if done_at else datetime.now(UTC)
    if target.actual_start_at and end_time <= target.actual_start_at:
        end_time = target.actual_start_at

    merged = target.model_dump(mode="python")
    merged["status"] = "done"
    merged["completed_at"] = end_time
    merged["actual_end_at"] = end_time
    updated = TaskOut.model_validate(merged)
    rows = [updated if row.id == task_id else row for row in tasks]
    _save_tasks(rows)
    _append_audit("task_mark_done", {"id": task_id})
    return updated.model_dump(mode="json")



@mcp.tool()
def feed_list(limit: int = 20) -> list[dict[str, Any]]:
    """List feed items, newest first."""
    rows = list(reversed(_load_feed()))
    return rows[: max(1, min(limit, 200))]


@mcp.tool()
def feed_add(category: str, content: str) -> dict[str, Any]:
    """Create one feed item."""
    rows = _load_feed()
    item = {"id": _next_id(rows), "category": category, "content": content, "created_at": _now_iso()}
    rows.append(item)
    _save_feed(rows)
    _append_audit("feed_add", {"id": item["id"], "category": category})
    return item


@mcp.tool()
def knowledge_list(kind: str | None = None, query: str | None = None, limit: int = 30) -> list[dict[str, Any]]:
    """List knowledge entries by kind/query."""
    rows = _load_knowledge()
    if kind:
        rows = [row for row in rows if row.get("kind") == kind]
    if query:
        q = query.lower()
        rows = [row for row in rows if q in str(row.get("title", "")).lower() or q in str(row.get("markdown", "")).lower()]
    rows = sorted(rows, key=lambda row: str(row.get("updated_at", "")), reverse=True)
    return rows[: max(1, min(limit, 200))]


@mcp.tool()
def knowledge_add(kind: str, title: str, markdown: str) -> dict[str, Any]:
    """Create one knowledge entry."""
    if kind not in {"entry", "blog"}:
        raise ValueError("kind must be entry or blog")
    rows = _load_knowledge()
    item = {
        "id": _next_id(rows),
        "kind": kind,
        "title": title,
        "markdown": markdown,
        "updated_at": _now_iso(),
    }
    rows.append(item)
    _save_knowledge(rows)
    _append_audit("knowledge_add", {"id": item["id"], "kind": kind})
    return item


@mcp.tool()
def knowledge_delete(entry_id: int, confirm: bool = False) -> dict[str, Any]:
    """Delete one knowledge entry (confirm=true required)."""
    if not confirm:
        raise ValueError("confirm must be true to delete knowledge entry")
    rows = _load_knowledge()
    new_rows = [row for row in rows if int(row.get("id", 0)) != entry_id]
    if len(new_rows) == len(rows):
        raise ValueError("entry not found")
    _save_knowledge(new_rows)
    _append_audit("knowledge_delete", {"id": entry_id})
    return {"deleted": True, "id": entry_id}


@mcp.tool()
def asset_list_accounts() -> list[dict[str, Any]]:
    """List asset accounts."""
    state = _load_assets()
    return state.get("accounts", [])


@mcp.tool()
def asset_cash_total() -> dict[str, str]:
    """Get total cash across cash accounts."""
    state = _load_assets()
    total = Decimal("0")
    for account in state.get("accounts", []):
        if account.get("is_cash"):
            total += Decimal(str(account.get("balance", "0")))
    return {"currency": "CNY", "cash_total": f"{total:.2f}"}


@mcp.tool()
def asset_record_transaction(
    account: str,
    tx_type: str,
    category: str,
    amount: str,
    happened_on: str,
    note: str | None = None,
) -> dict[str, Any]:
    """Create one asset transaction and update account balance."""
    if tx_type not in {"income", "expense"}:
        raise ValueError("tx_type must be income or expense")
    dec_amount = _parse_decimal(amount)

    try:
        payload = TransactionCreate(
            account=account,
            type=tx_type,
            category=category,
            amount=dec_amount,
            happened_on=date.fromisoformat(happened_on),
            note=note,
        )
    except (ValidationError, ValueError) as exc:
        raise ValueError(str(exc)) from exc

    state = _load_assets()
    accounts = state.get("accounts", [])
    account_map = {row.get("name"): row for row in accounts}
    account_row = account_map.get(account)
    if not account_row:
        raise ValueError("account not found")

    rows = [TransactionOut.model_validate(row) for row in state.get("transactions", [])]
    next_id = max([row.id for row in rows], default=0) + 1
    row = TransactionOut(id=next_id, **payload.model_dump())
    rows.append(row)

    balance = Decimal(str(account_row.get("balance", "0")))
    balance = balance + dec_amount if tx_type == "income" else balance - dec_amount
    account_row["balance"] = f"{balance:.2f}"

    state["transactions"] = [item.model_dump(mode="json") for item in rows]
    _save_assets(state)
    _append_audit("asset_record_transaction", {"id": next_id, "account": account, "tx_type": tx_type})
    return row.model_dump(mode="json")


@mcp.tool()
def settings_get() -> dict[str, Any]:
    """Get current app settings."""
    row = _load_settings()
    return SettingsPayload.model_validate(row).model_dump(mode="json")


@mcp.tool()
def settings_update(
    default_provider: str | None = None,
    model_name: str | None = None,
    theme: str | None = None,
    local_only: bool | None = None,
) -> dict[str, Any]:
    """Partially update app settings."""
    row = _load_settings()
    updated_keys: list[str] = []
    if default_provider is not None:
        row["default_provider"] = default_provider
        updated_keys.append("default_provider")
    if model_name is not None:
        row["model_name"] = model_name
        updated_keys.append("model_name")
    if theme is not None:
        row["theme"] = theme
        updated_keys.append("theme")
    if local_only is not None:
        row["local_only"] = local_only
        updated_keys.append("local_only")
    out = SettingsPayload.model_validate(row).model_dump(mode="json")
    write_json(SETTINGS_FILE, out)
    _append_audit("settings_update", {"keys": updated_keys})
    return out


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
