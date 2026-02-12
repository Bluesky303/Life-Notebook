from datetime import datetime

from fastapi import APIRouter, HTTPException

from app.core.json_store import read_json, write_json
from app.schemas.tasks import TaskCreate, TaskOut

router = APIRouter(prefix="/tasks", tags=["tasks"])

_TASKS_FILE = "tasks.json"
_DEFAULT_TASKS: list[dict] = []


def _load_tasks() -> list[TaskOut]:
    rows = read_json(_TASKS_FILE, _DEFAULT_TASKS)
    return [TaskOut.model_validate(row) for row in rows]


def _save_tasks(tasks: list[TaskOut]) -> None:
    write_json(_TASKS_FILE, [task.model_dump(mode="json") for task in tasks])


@router.get("/", response_model=list[TaskOut])
def list_tasks() -> list[TaskOut]:
    return _load_tasks()


@router.post("/", response_model=TaskOut)
def create_task(payload: TaskCreate) -> TaskOut:
    if payload.start_at and payload.end_at and payload.end_at <= payload.start_at:
        raise HTTPException(status_code=400, detail="end_at must be later than start_at")

    tasks = _load_tasks()
    next_id = max([task.id for task in tasks], default=0) + 1
    task = TaskOut(id=next_id, **payload.model_dump())
    tasks.append(task)
    _save_tasks(tasks)
    return task


@router.delete("/{task_id}")
def delete_task(task_id: int) -> dict[str, int | bool]:
    tasks = _load_tasks()
    new_tasks = [task for task in tasks if task.id != task_id]
    if len(new_tasks) == len(tasks):
        raise HTTPException(status_code=404, detail="task not found")

    _save_tasks(new_tasks)
    return {"deleted": True, "id": task_id}
