from datetime import UTC, datetime

from sqlalchemy import select

from app.core.db import SessionLocal, init_db
from app.core.json_store import read_json
from app.models.sleep import SleepLogRecord

_SLEEP_FILE = "sleep.json"


def _normalize_datetime(value: str | datetime) -> datetime:
    if isinstance(value, str):
        value = datetime.fromisoformat(value)
    if value.tzinfo:
        return value.astimezone(UTC).replace(tzinfo=None)
    return value


def _bootstrap_if_empty() -> None:
    with SessionLocal() as db:
        has_data = db.execute(select(SleepLogRecord.id).limit(1)).first() is not None
        if has_data:
            return
        rows = read_json(_SLEEP_FILE, [])
        for row in rows:
            db.add(
                SleepLogRecord(
                    id=int(row.get("id", 0)) or None,
                    start_at=_normalize_datetime(row.get("start_at", datetime.now(UTC))),
                    end_at=_normalize_datetime(row.get("end_at", datetime.now(UTC))),
                    note=row.get("note"),
                )
            )
        db.commit()


def list_sleep_logs() -> list[dict]:
    init_db()
    _bootstrap_if_empty()
    with SessionLocal() as db:
        rows = db.execute(select(SleepLogRecord).order_by(SleepLogRecord.end_at.desc())).scalars().all()
        return [{"id": row.id, "start_at": row.start_at, "end_at": row.end_at, "note": row.note} for row in rows]


def create_sleep_log(start_at: datetime, end_at: datetime, note: str | None = None) -> dict:
    init_db()
    with SessionLocal() as db:
        row = SleepLogRecord(start_at=_normalize_datetime(start_at), end_at=_normalize_datetime(end_at), note=note)
        db.add(row)
        db.commit()
        db.refresh(row)
        return {"id": row.id, "start_at": row.start_at, "end_at": row.end_at, "note": row.note}


def delete_sleep_log(log_id: int) -> bool:
    init_db()
    with SessionLocal() as db:
        row = db.get(SleepLogRecord, log_id)
        if not row:
            return False
        db.delete(row)
        db.commit()
        return True
