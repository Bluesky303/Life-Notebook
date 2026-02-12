from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class TaskRecord(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False, default="general")
    importance: Mapped[str] = mapped_column(String(20), nullable=False, default="medium")
    task_type: Mapped[str] = mapped_column(String(20), nullable=False, default="task")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="todo")

    planned_start_at: Mapped[DateTime | None] = mapped_column(DateTime, nullable=True)
    planned_end_at: Mapped[DateTime | None] = mapped_column(DateTime, nullable=True)
    actual_start_at: Mapped[DateTime | None] = mapped_column(DateTime, nullable=True)
    actual_end_at: Mapped[DateTime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[DateTime | None] = mapped_column(DateTime, nullable=True)

    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    is_recurring_template: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    recurrence_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    template_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
