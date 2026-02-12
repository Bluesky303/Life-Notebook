from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, ValidationError

from app.core.json_store import DATA_DIR
from app.schemas.assets import TransactionCreate, TransactionOut
from app.schemas.tasks import TaskCreate, TaskOut
from app.services.assets_storage import cash_total as db_asset_cash_total
from app.services.assets_storage import create_transaction as db_asset_create_transaction
from app.services.assets_storage import list_accounts as db_asset_list_accounts
from app.services.feed_storage import create_feed as db_create_feed
from app.services.feed_storage import list_feeds as db_list_feeds
from app.services.knowledge_storage import create_entry as db_create_entry
from app.services.knowledge_storage import delete_entry as db_delete_entry
from app.services.knowledge_storage import list_entries as db_list_entries
from app.services.settings_storage import get_settings as db_get_settings
from app.services.settings_storage import update_settings as db_update_settings
from app.services.task_storage import load_tasks as db_load_tasks, replace_tasks as db_replace_tasks

mcp = FastMCP("life-notebook")

AUDIT_FILE = DATA_DIR / "mcp_audit.log"


class SettingsPayload(BaseModel):
    default_provider: str
    model_name: str
    theme: str
    local_only: bool




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
    return db_load_tasks()


def _save_tasks(tasks: list[TaskOut]) -> None:
    db_replace_tasks(tasks)



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
    is_recurring_template: bool = False,
    recurrence_freq: str | None = None,
    recurrence_interval: int = 1,
    recurrence_weekdays: list[int] | None = None,
    recurrence_until: str | None = None,
) -> dict[str, Any]:
    """Create one task."""
    planned_start_dt = _parse_datetime(planned_start_at) if planned_start_at else (_parse_datetime(start_at) if start_at else None)
    planned_end_dt = _parse_datetime(planned_end_at) if planned_end_at else (_parse_datetime(end_at) if end_at else None)
    actual_start_dt = _parse_datetime(actual_start_at) if actual_start_at else None
    actual_end_dt = _parse_datetime(actual_end_at) if actual_end_at else None
    completed_dt = _parse_datetime(completed_at) if completed_at else None
    recurrence_until_dt = _parse_datetime(recurrence_until) if recurrence_until else None

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
            is_recurring_template=is_recurring_template,
            recurrence=(
                {
                    "freq": recurrence_freq,
                    "interval": recurrence_interval,
                    "weekdays": recurrence_weekdays,
                    "until": recurrence_until_dt,
                }
                if recurrence_freq
                else None
            ),
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
    is_recurring_template: bool | None = None,
    recurrence_freq: str | None = None,
    recurrence_interval: int | None = None,
    recurrence_weekdays: list[int] | None = None,
    recurrence_until: str | None = None,
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
    if is_recurring_template is not None:
        merged["is_recurring_template"] = is_recurring_template
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
    if recurrence_freq is not None:
        merged["recurrence"] = {
            "freq": recurrence_freq,
            "interval": recurrence_interval if recurrence_interval is not None else 1,
            "weekdays": recurrence_weekdays,
            "until": _parse_datetime(recurrence_until) if recurrence_until else None,
        }

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
    rows = db_list_feeds(limit=max(1, min(limit, 200)))
    return [
        {
            "id": int(row["id"]),
            "category": str(row["category"]),
            "content": str(row["content"]),
            "created_at": row["created_at"].isoformat() if hasattr(row["created_at"], "isoformat") else str(row["created_at"]),
        }
        for row in rows
    ]


@mcp.tool()
def feed_add(category: str, content: str) -> dict[str, Any]:
    """Create one feed item."""
    item = db_create_feed(category, content)
    _append_audit("feed_add", {"id": item["id"], "category": category})
    return {
        "id": int(item["id"]),
        "category": str(item["category"]),
        "content": str(item["content"]),
        "created_at": item["created_at"].isoformat() if hasattr(item["created_at"], "isoformat") else str(item["created_at"]),
    }


@mcp.tool()
def knowledge_list(kind: str | None = None, query: str | None = None, limit: int = 30) -> list[dict[str, Any]]:
    """List knowledge entries by kind/query."""
    rows = db_list_entries(kind=kind, q=query)[: max(1, min(limit, 200))]
    return [
        {
            "id": int(row["id"]),
            "kind": str(row["kind"]),
            "title": str(row["title"]),
            "markdown": str(row["markdown"]),
            "updated_at": row["updated_at"].isoformat() if hasattr(row["updated_at"], "isoformat") else str(row["updated_at"]),
        }
        for row in rows
    ]


@mcp.tool()
def knowledge_add(kind: str, title: str, markdown: str) -> dict[str, Any]:
    """Create one knowledge entry."""
    if kind not in {"entry", "blog"}:
        raise ValueError("kind must be entry or blog")
    item = db_create_entry(kind=kind, title=title, markdown=markdown)
    _append_audit("knowledge_add", {"id": item["id"], "kind": kind})
    return {
        "id": int(item["id"]),
        "kind": str(item["kind"]),
        "title": str(item["title"]),
        "markdown": str(item["markdown"]),
        "updated_at": item["updated_at"].isoformat() if hasattr(item["updated_at"], "isoformat") else str(item["updated_at"]),
    }


@mcp.tool()
def knowledge_delete(entry_id: int, confirm: bool = False) -> dict[str, Any]:
    """Delete one knowledge entry (confirm=true required)."""
    if not confirm:
        raise ValueError("confirm must be true to delete knowledge entry")
    ok = db_delete_entry(entry_id)
    if not ok:
        raise ValueError("entry not found")
    _append_audit("knowledge_delete", {"id": entry_id})
    return {"deleted": True, "id": entry_id}


@mcp.tool()
def asset_list_accounts() -> list[dict[str, Any]]:
    """List asset accounts."""
    return db_asset_list_accounts()


@mcp.tool()
def asset_cash_total() -> dict[str, str]:
    """Get total cash across cash accounts."""
    return db_asset_cash_total()


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

    try:
        row = db_asset_create_transaction(payload.model_dump())
    except ValueError as exc:
        raise ValueError(str(exc)) from exc
    _append_audit("asset_record_transaction", {"id": row["id"], "account": account, "tx_type": tx_type})
    return TransactionOut.model_validate(row).model_dump(mode="json")


@mcp.tool()
def settings_get() -> dict[str, Any]:
    """Get current app settings."""
    row = db_get_settings()
    return SettingsPayload.model_validate(row).model_dump(mode="json")


@mcp.tool()
def settings_update(
    default_provider: str | None = None,
    model_name: str | None = None,
    theme: str | None = None,
    local_only: bool | None = None,
) -> dict[str, Any]:
    """Partially update app settings."""
    row = db_get_settings()
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
    out = db_update_settings(out)
    _append_audit("settings_update", {"keys": updated_keys})
    return out


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
