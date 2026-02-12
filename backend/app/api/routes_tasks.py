from datetime import UTC, date, datetime, time, timedelta

from fastapi import APIRouter, HTTPException

from app.schemas.tasks import RecurrenceRule, TaskCreate, TaskOut, TaskUpdate
from app.services.task_storage import load_tasks, replace_tasks

router = APIRouter(prefix="/tasks", tags=["tasks"])

_RECURRING_HORIZON_DAYS = 30


def _normalize_status(value: str | None) -> str:
    if value in {"todo", "in_progress", "done", "skipped"}:
        return value
    return "todo"


def _normalize_task_type(value: str | None) -> str:
    if value in {"task", "sleep"}:
        return value
    return "task"


def _normalize_datetime(value: datetime | str | None) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, str):
        return datetime.fromisoformat(value)
    if value.tzinfo:
        return value.astimezone(UTC).replace(tzinfo=None)
    return value


def _validate_time_range(start_at: datetime | None, end_at: datetime | None, label: str) -> None:
    if start_at and end_at and end_at <= start_at:
        raise HTTPException(status_code=400, detail=f"{label} end_at must be later than start_at")


def _normalize_recurrence(value: dict | RecurrenceRule | None) -> RecurrenceRule | None:
    if value is None:
        return None
    row = RecurrenceRule.model_validate(value)
    if row.until is not None:
        row.until = _normalize_datetime(row.until)
    return row


def _load_tasks() -> list[TaskOut]:
    return load_tasks()


def _save_tasks(tasks: list[TaskOut]) -> None:
    replace_tasks(tasks)


def _next_task_id(tasks: list[TaskOut]) -> int:
    return max([task.id for task in tasks], default=0) + 1


def _month_add(value: date, months: int) -> date:
    y = value.year + ((value.month - 1 + months) // 12)
    m = ((value.month - 1 + months) % 12) + 1
    if m == 2:
        leap = (y % 4 == 0 and y % 100 != 0) or (y % 400 == 0)
        day_cap = 29 if leap else 28
    elif m in {4, 6, 9, 11}:
        day_cap = 30
    else:
        day_cap = 31
    return date(y, m, min(value.day, day_cap))


def _iter_recurrence_starts(
    seed_start: datetime,
    rule: RecurrenceRule,
    window_start: datetime,
    window_end: datetime,
) -> list[datetime]:
    interval = max(1, int(rule.interval))
    starts: list[datetime] = []
    seed_start = _normalize_datetime(seed_start) or seed_start
    window_start = _normalize_datetime(window_start) or window_start
    window_end = _normalize_datetime(window_end) or window_end

    if rule.freq == "daily":
        current = seed_start
        while current < window_start:
            current += timedelta(days=interval)
        while current <= window_end:
            if rule.until and current > rule.until:
                break
            starts.append(current)
            current += timedelta(days=interval)
        return starts

    if rule.freq == "weekly":
        weekdays = sorted(set(rule.weekdays or [seed_start.weekday()]))
        start_day = window_start.date()
        end_day = window_end.date()
        total_days = (end_day - start_day).days + 1
        seed_day = seed_start.date()
        seed_time = seed_start.time()
        for offset in range(total_days):
            d = start_day + timedelta(days=offset)
            if d < seed_day or d.weekday() not in weekdays:
                continue
            week_delta = (d - seed_day).days // 7
            if week_delta % interval != 0:
                continue
            current = datetime.combine(d, seed_time)
            if rule.until and current > rule.until:
                continue
            starts.append(current)
        return starts

    if rule.freq == "monthly":
        current_day = seed_start.date()
        current = seed_start
        while current < window_start:
            current_day = _month_add(current_day, interval)
            current = datetime.combine(current_day, seed_start.time())
        while current <= window_end:
            if rule.until and current > rule.until:
                break
            starts.append(current)
            current_day = _month_add(current_day, interval)
            current = datetime.combine(current_day, seed_start.time())
        return starts

    # yearly
    current = seed_start
    while current < window_start:
        current = datetime.combine(date(current.year + interval, current.month, current.day), current.time())
    while current <= window_end:
        if rule.until and current > rule.until:
            break
        starts.append(current)
        current = datetime.combine(date(current.year + interval, current.month, current.day), current.time())
    return starts


def _materialize_template_instances(
    tasks: list[TaskOut],
    template: TaskOut,
    window_start: datetime,
    window_end: datetime,
    keep_finished: bool = True,
) -> bool:
    if not template.is_recurring_template or template.recurrence is None:
        return False
    if not template.planned_start_at or not template.planned_end_at:
        return False

    changed = False
    duration = template.planned_end_at - template.planned_start_at
    if duration <= timedelta(0):
        return False

    if not keep_finished:
        keep_rows: list[TaskOut] = []
        for row in tasks:
            if row.template_id != template.id:
                keep_rows.append(row)
                continue
            if row.status == "done":
                keep_rows.append(row)
            else:
                changed = True
        tasks[:] = keep_rows

    existing_starts = {
        row.planned_start_at
        for row in tasks
        if row.template_id == template.id and row.planned_start_at is not None
    }
    next_id = _next_task_id(tasks)

    starts = _iter_recurrence_starts(template.planned_start_at, template.recurrence, window_start, window_end)
    for start_at in starts:
        if start_at in existing_starts:
            continue
        tasks.append(
            TaskOut(
                id=next_id,
                title=template.title,
                category=template.category,
                importance=template.importance,
                type=template.task_type,
                status="todo",
                planned_start_at=start_at,
                planned_end_at=start_at + duration,
                actual_start_at=None,
                actual_end_at=None,
                completed_at=None,
                note=template.note,
                is_recurring_template=False,
                recurrence=None,
                template_id=template.id,
            )
        )
        existing_starts.add(start_at)
        next_id += 1
        changed = True
    return changed


def _ensure_recurring_instances(tasks: list[TaskOut]) -> bool:
    now = datetime.now()
    window_start = datetime.combine(now.date(), time.min)
    window_end = window_start + timedelta(days=_RECURRING_HORIZON_DAYS)
    changed = False
    for template in [row for row in tasks if row.is_recurring_template]:
        changed = _materialize_template_instances(tasks, template, window_start, window_end) or changed
    return changed


def _normalize_task_payload_for_write(payload: TaskCreate | TaskUpdate, merged: dict | None = None) -> dict:
    body = payload.model_dump(by_alias=True, exclude_unset=isinstance(payload, TaskUpdate))
    if merged is not None:
        merged.update(body)
        body = merged
    if "status" in body:
        body["status"] = _normalize_status(body.get("status"))
    if "type" in body:
        body["type"] = _normalize_task_type(body.get("type"))
    if "recurrence" in body and body["recurrence"] is not None:
        body["recurrence"] = RecurrenceRule.model_validate(body["recurrence"]).model_dump(mode="python")
    for key in ("planned_start_at", "planned_end_at", "actual_start_at", "actual_end_at", "completed_at"):
        if key in body:
            body[key] = _normalize_datetime(body.get(key))
    return body


def _task_range(task: TaskOut) -> tuple[datetime | None, datetime | None]:
    start_at = task.actual_start_at or task.planned_start_at
    end_at = task.actual_end_at or task.planned_end_at
    return start_at, end_at


@router.get("/", response_model=list[TaskOut])
def list_tasks(include_templates: bool = False) -> list[TaskOut]:
    tasks = _load_tasks()
    changed = _ensure_recurring_instances(tasks)
    if changed:
        _save_tasks(tasks)
    rows = tasks if include_templates else [item for item in tasks if not item.is_recurring_template]
    return list(sorted(rows, key=lambda item: item.planned_start_at or datetime.max))


@router.get("/day", response_model=list[TaskOut])
def list_tasks_by_day(date_str: str, include_templates: bool = False) -> list[TaskOut]:
    target_day = date.fromisoformat(date_str)
    day_start = datetime.combine(target_day, time.min)
    day_end = day_start + timedelta(days=1)

    tasks = _load_tasks()
    changed = _ensure_recurring_instances(tasks)
    if changed:
        _save_tasks(tasks)
    rows = tasks if include_templates else [item for item in tasks if not item.is_recurring_template]

    result: list[TaskOut] = []
    for item in rows:
        start_at, end_at = _task_range(item)
        if not start_at or not end_at:
            continue
        if start_at < day_end and end_at > day_start:
            result.append(item)
    return list(sorted(result, key=lambda item: _task_range(item)[0] or datetime.max))


@router.post("/", response_model=TaskOut)
def create_task(payload: TaskCreate) -> TaskOut:
    _validate_time_range(payload.planned_start_at, payload.planned_end_at, "planned")
    _validate_time_range(payload.actual_start_at, payload.actual_end_at, "actual")
    if payload.is_recurring_template:
        if payload.recurrence is None:
            raise HTTPException(status_code=400, detail="recurrence is required when is_recurring_template=true")
        if not payload.planned_start_at or not payload.planned_end_at:
            raise HTTPException(status_code=400, detail="planned_start_at and planned_end_at are required for recurring template")

    tasks = _load_tasks()
    next_id = _next_task_id(tasks)

    body = _normalize_task_payload_for_write(payload)
    status = body.get("status", "todo")
    completed_at = body.get("completed_at")
    if status == "done" and completed_at is None:
        completed_at = datetime.now(UTC)
    if status != "done":
        completed_at = None
    body["completed_at"] = completed_at

    task = TaskOut(id=next_id, **body)
    tasks.append(task)

    if task.is_recurring_template:
        now = datetime.now()
        window_start = datetime.combine(now.date(), time.min)
        window_end = window_start + timedelta(days=_RECURRING_HORIZON_DAYS)
        _materialize_template_instances(tasks, task, window_start, window_end)

    _save_tasks(tasks)
    return task


@router.put("/{task_id}", response_model=TaskOut)
def update_task(task_id: int, payload: TaskUpdate) -> TaskOut:
    tasks = _load_tasks()
    task_index = next((idx for idx, task in enumerate(tasks) if task.id == task_id), None)
    if task_index is None:
        raise HTTPException(status_code=404, detail="task not found")

    current = tasks[task_index]
    merged = current.model_dump(by_alias=True)
    merged = _normalize_task_payload_for_write(payload, merged=merged)

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

    if updated.is_recurring_template:
        if updated.recurrence is None:
            raise HTTPException(status_code=400, detail="recurrence is required when is_recurring_template=true")
        now = datetime.now()
        window_start = datetime.combine(now.date(), time.min)
        window_end = window_start + timedelta(days=_RECURRING_HORIZON_DAYS)
        _materialize_template_instances(tasks, updated, window_start, window_end, keep_finished=False)

    _save_tasks(tasks)
    return updated


@router.delete("/{task_id}")
def delete_task(task_id: int) -> dict[str, int | bool]:
    tasks = _load_tasks()
    target = next((task for task in tasks if task.id == task_id), None)
    if target is None:
        raise HTTPException(status_code=404, detail="task not found")

    if target.is_recurring_template:
        new_tasks = [task for task in tasks if task.id != task_id and task.template_id != task_id]
    else:
        new_tasks = [task for task in tasks if task.id != task_id]

    _save_tasks(new_tasks)
    return {"deleted": True, "id": task_id}
