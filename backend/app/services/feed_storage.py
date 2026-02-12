from datetime import UTC, datetime

from sqlalchemy import select

from app.core.db import SessionLocal, init_db
from app.core.json_store import read_json
from app.models.feed import FeedRecord

_FEED_FILE = "feed.json"


def _normalize_datetime(value: str | datetime) -> datetime:
    if isinstance(value, str):
        value = datetime.fromisoformat(value)
    if value.tzinfo:
        return value.astimezone(UTC).replace(tzinfo=None)
    return value


def _bootstrap_if_empty() -> None:
    with SessionLocal() as db:
        has_data = db.execute(select(FeedRecord.id).limit(1)).first() is not None
        if has_data:
            return
        rows = read_json(_FEED_FILE, [])
        for row in rows:
            db.add(
                FeedRecord(
                    id=int(row.get("id", 0)) or None,
                    category=str(row.get("category", "")),
                    content=str(row.get("content", "")),
                    created_at=_normalize_datetime(row.get("created_at", datetime.now(UTC))),
                )
            )
        db.commit()


def list_feeds(limit: int = 20) -> list[dict]:
    init_db()
    _bootstrap_if_empty()
    with SessionLocal() as db:
        rows = db.execute(select(FeedRecord).order_by(FeedRecord.id.desc()).limit(max(1, limit))).scalars().all()
        return [
            {"id": row.id, "category": row.category, "content": row.content, "created_at": row.created_at}
            for row in rows
        ]


def create_feed(category: str, content: str) -> dict:
    init_db()
    with SessionLocal() as db:
        row = FeedRecord(category=category, content=content, created_at=datetime.utcnow())
        db.add(row)
        db.commit()
        db.refresh(row)
        return {"id": row.id, "category": row.category, "content": row.content, "created_at": row.created_at}


def delete_feed(feed_id: int) -> bool:
    init_db()
    with SessionLocal() as db:
        row = db.get(FeedRecord, feed_id)
        if not row:
            return False
        db.delete(row)
        db.commit()
        return True
