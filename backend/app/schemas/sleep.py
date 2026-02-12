from datetime import datetime

from pydantic import BaseModel


class SleepLogCreate(BaseModel):
    start_at: datetime
    end_at: datetime
    note: str | None = None


class SleepLogOut(SleepLogCreate):
    id: int
