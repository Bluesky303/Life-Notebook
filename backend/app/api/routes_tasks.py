from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException

from app.core.json_store import read_json, write_json
from app.schemas.tasks import TaskCreate, TaskOut, TaskUpdate

router = APIRouter(prefix="/tasks", tags=["tasks"])

_TASKS_FILE = "tasks.json"
_DEFAULT_TASKS: list[dict] = []


def _normalize_status(value: str | None) -> str:
    if value in {"todo", "in_progress", "done", "skipped"}:
        return value
    return "todo"


def _normalize_task_type(value: str | None) -> str:
    if value in {"task", "sleep"}:
        return value
    return "task"


def _validate_time_range(start_at: datetime | None, end_at: datetime | None, label: str) -> None:
    if start_at and end_at and end_at <= start_at:
        raise HTTPException(status_code=400, detail=f"{label} end_at must be later than start_at")


def _normalize_task_row(row: dict) -> TaskOut:
    # Backward-compatible migration from legacy task schema.
    planned_start_at = row.get("planned_start_at")
    planned_end_at = row.get("planned_end_at")
    if planned_start_at is None and row.get("start_at") is not None:
        planned_start_at = row.get("start_at")
    if planned_end_at is None and row.get("end_at") is not None:
        planned_end_at = row.get("end_at")

    task_type = row.get("type", row.get("task_type"))
    if task_type is None and row.get("category") == "睡眠":
        task_type = "sleep"

    normalized = {
        "id": row.get("id"),
        "title": row.get("title", ""),
        "category": row.get("category", "日常"),
        "importance": row.get("importance", "medium"),
        "type": _normalize_task_type(task_type),
        "status": _normalize_status(row.get("status")),
        "planned_start_at": planned_start_at,
        "planned_end_at": planned_end_at,
        "actual_start_at": row.get("actual_start_at"),
        "actual_end_at": row.get("actual_end_at"),
        "completed_at": row.get("completed_at"),
        "note": row.get("note"),
    }
    return TaskOut.model_validate(normalized)


def _load_tasks() -> list[TaskOut]:
    rows = read_json(_TASKS_FILE, _DEFAULT_TASKS)
    return [_normalize_task_row(row) for row in rows]


def _save_tasks(tasks: list[TaskOut]) -> None:
    write_json(_TASKS_FILE, [task.model_dump(mode="json", by_alias=True) for task in tasks])


@router.get("/", response_model=list[TaskOut])
def list_tasks() -> list[TaskOut]:
    tasks = _load_tasks()
    return list(sorted(tasks, key=lambda item: item.planned_start_at or datetime.max))


@router.post("/", response_model=TaskOut)
def create_task(payload: TaskCreate) -> TaskOut:
    _validate_time_range(payload.planned_start_at, payload.planned_end_at, "planned")
    _validate_time_range(payload.actual_start_at, payload.actual_end_at, "actual")

    tasks = _load_tasks()
    next_id = max([task.id for task in tasks], default=0) + 1

    status = _normalize_status(payload.status)
    completed_at = payload.completed_at
    if status == "done" and completed_at is None:
        completed_at = datetime.now(UTC)
    if status != "done":
        completed_at = None

    body = payload.model_dump(by_alias=True)
    body["status"] = status
    body["type"] = _normalize_task_type(body.get("type"))
    body["completed_at"] = completed_at
    task = TaskOut(id=next_id, **body)
    tasks.append(task)
    _save_tasks(tasks)
    return task


@router.put("/{task_id}", response_model=TaskOut)
def update_task(task_id: int, payload: TaskUpdate) -> TaskOut:
    tasks = _load_tasks()
    task_index = next((idx for idx, task in enumerate(tasks) if task.id == task_id), None)
    if task_index is None:
        raise HTTPException(status_code=404, detail="task not found")

    current = tasks[task_index]
    patch = payload.model_dump(exclude_unset=True, by_alias=True)
    if "status" in patch:
        patch["status"] = _normalize_status(patch["status"])
    if "type" in patch:
        patch["type"] = _normalize_task_type(patch["type"])

    merged = current.model_dump(by_alias=True)
    merged.update(patch)

    status = _normalize_status(merged.get("status"))
    merged["status"] = status
    if status == "done":
        merged["completed_at"] = merged.get("completed_at") or datetime.now(UTC)
    else:
        merged["completed_at"] = None

    _validate_time_range(merged.get("planned_start_at"), merged.get("planned_end_at"), "planned")
    _validate_time_range(merged.get("actual_start_at"), merged.get("actual_end_at"), "actual")

    updated = TaskOut.model_validate(merged)
    tasks[task_index] = updated
    _save_tasks(tasks)
    return updated


@router.delete("/{task_id}")
def delete_task(task_id: int) -> dict[str, int | bool]:
    tasks = _load_tasks()
    new_tasks = [task for task in tasks if task.id != task_id]
    if len(new_tasks) == len(tasks):
        raise HTTPException(status_code=404, detail="task not found")

    _save_tasks(new_tasks)
    return {"deleted": True, "id": task_id}
