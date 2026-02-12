import json
from datetime import UTC, datetime

from sqlalchemy import delete, select

from app.core.db import SessionLocal, init_db
from app.core.json_store import read_json
from app.models.task import TaskRecord
from app.schemas.tasks import RecurrenceRule, TaskOut

_TASKS_FILE = "tasks.json"


def _normalize_datetime(value: datetime | str | None) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, str):
        value = datetime.fromisoformat(value)
    if value.tzinfo:
        return value.astimezone(UTC).replace(tzinfo=None)
    return value


def _normalize_status(value: str | None) -> str:
    if value in {"todo", "in_progress", "done", "skipped"}:
        return value
    return "todo"


def _normalize_task_type(value: str | None) -> str:
    if value in {"task", "sleep"}:
        return value
    return "task"


def _normalize_task_row(row: dict) -> TaskOut:
    planned_start_at = row.get("planned_start_at")
    planned_end_at = row.get("planned_end_at")
    if planned_start_at is None and row.get("start_at") is not None:
        planned_start_at = row.get("start_at")
    if planned_end_at is None and row.get("end_at") is not None:
        planned_end_at = row.get("end_at")

    task_type = row.get("type", row.get("task_type"))
    if task_type is None and row.get("category") == "睡眠":
        task_type = "sleep"

    recurrence = row.get("recurrence")
    if recurrence is not None:
        recurrence = RecurrenceRule.model_validate(recurrence)

    normalized = {
        "id": row.get("id"),
        "title": row.get("title", ""),
        "category": row.get("category", "日常"),
        "importance": row.get("importance", "medium"),
        "type": _normalize_task_type(task_type),
        "status": _normalize_status(row.get("status")),
        "planned_start_at": _normalize_datetime(planned_start_at),
        "planned_end_at": _normalize_datetime(planned_end_at),
        "actual_start_at": _normalize_datetime(row.get("actual_start_at")),
        "actual_end_at": _normalize_datetime(row.get("actual_end_at")),
        "completed_at": _normalize_datetime(row.get("completed_at")),
        "note": row.get("note"),
        "is_recurring_template": bool(row.get("is_recurring_template", False)),
        "recurrence": recurrence,
        "template_id": row.get("template_id"),
    }
    return TaskOut.model_validate(normalized)


def _record_to_task(row: TaskRecord) -> TaskOut:
    recurrence = None
    if row.recurrence_json:
        recurrence = RecurrenceRule.model_validate(json.loads(row.recurrence_json))
    return TaskOut(
        id=row.id,
        title=row.title,
        category=row.category,
        importance=row.importance,
        type=row.task_type,
        status=row.status,
        planned_start_at=row.planned_start_at,
        planned_end_at=row.planned_end_at,
        actual_start_at=row.actual_start_at,
        actual_end_at=row.actual_end_at,
        completed_at=row.completed_at,
        note=row.note,
        is_recurring_template=row.is_recurring_template,
        recurrence=recurrence,
        template_id=row.template_id,
    )


def _task_to_record(task: TaskOut) -> TaskRecord:
    recurrence_json = None
    if task.recurrence is not None:
        recurrence_json = json.dumps(task.recurrence.model_dump(mode="json"), ensure_ascii=False)
    return TaskRecord(
        id=task.id,
        title=task.title,
        category=task.category,
        importance=task.importance,
        task_type=task.task_type,
        status=task.status,
        planned_start_at=_normalize_datetime(task.planned_start_at),
        planned_end_at=_normalize_datetime(task.planned_end_at),
        actual_start_at=_normalize_datetime(task.actual_start_at),
        actual_end_at=_normalize_datetime(task.actual_end_at),
        completed_at=_normalize_datetime(task.completed_at),
        note=task.note,
        is_recurring_template=task.is_recurring_template,
        recurrence_json=recurrence_json,
        template_id=task.template_id,
    )


def _bootstrap_if_empty() -> None:
    with SessionLocal() as db:
        has_data = db.execute(select(TaskRecord.id).limit(1)).first() is not None
        if has_data:
            return
        rows = read_json(_TASKS_FILE, [])
        tasks = [_normalize_task_row(row) for row in rows]
        if not tasks:
            return
        for task in sorted(tasks, key=lambda item: item.id):
            db.add(_task_to_record(task))
        db.commit()


def load_tasks() -> list[TaskOut]:
    init_db()
    _bootstrap_if_empty()
    with SessionLocal() as db:
        rows = db.execute(select(TaskRecord).order_by(TaskRecord.id)).scalars().all()
        return [_record_to_task(row) for row in rows]


def replace_tasks(tasks: list[TaskOut]) -> None:
    init_db()
    with SessionLocal() as db:
        db.execute(delete(TaskRecord))
        for task in sorted(tasks, key=lambda item: item.id):
            db.add(_task_to_record(task))
        db.commit()
