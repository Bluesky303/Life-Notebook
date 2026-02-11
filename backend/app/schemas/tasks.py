from datetime import datetime
from pydantic import BaseModel


class TaskCreate(BaseModel):
    title: str
    category: str
    importance: str
    start_at: datetime | None = None
    end_at: datetime | None = None


class TaskOut(TaskCreate):
    id: int
