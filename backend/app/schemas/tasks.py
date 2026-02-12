from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class RecurrenceRule(BaseModel):
    freq: Literal["daily", "weekly", "monthly", "yearly"]
    interval: int = 1
    weekdays: list[int] | None = None
    until: datetime | None = None


class TaskCreate(BaseModel):
    title: str
    category: str
    importance: str
    task_type: str = Field(default="task", alias="type")
    status: str = "todo"
    planned_start_at: datetime | None = None
    planned_end_at: datetime | None = None
    actual_start_at: datetime | None = None
    actual_end_at: datetime | None = None
    completed_at: datetime | None = None
    note: str | None = None
    is_recurring_template: bool = False
    recurrence: RecurrenceRule | None = None
    template_id: int | None = None

    model_config = ConfigDict(populate_by_name=True)


class TaskUpdate(BaseModel):
    title: str | None = None
    category: str | None = None
    importance: str | None = None
    task_type: str | None = Field(default=None, alias="type")
    status: str | None = None
    planned_start_at: datetime | None = None
    planned_end_at: datetime | None = None
    actual_start_at: datetime | None = None
    actual_end_at: datetime | None = None
    completed_at: datetime | None = None
    note: str | None = None
    is_recurring_template: bool | None = None
    recurrence: RecurrenceRule | None = None
    template_id: int | None = None

    model_config = ConfigDict(populate_by_name=True)


class TaskOut(TaskCreate):
    id: int
