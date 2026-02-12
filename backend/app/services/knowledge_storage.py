from datetime import UTC, datetime

from sqlalchemy import select

from app.core.db import SessionLocal, init_db
from app.core.json_store import read_json
from app.models.knowledge import KnowledgeRecord

_KNOWLEDGE_FILE = "knowledge.json"


def _normalize_datetime(value: str | datetime) -> datetime:
    if isinstance(value, str):
        value = datetime.fromisoformat(value)
    if value.tzinfo:
        return value.astimezone(UTC).replace(tzinfo=None)
    return value


def _bootstrap_if_empty() -> None:
    with SessionLocal() as db:
        has_data = db.execute(select(KnowledgeRecord.id).limit(1)).first() is not None
        if has_data:
            return
        rows = read_json(_KNOWLEDGE_FILE, [])
        for row in rows:
            db.add(
                KnowledgeRecord(
                    id=int(row.get("id", 0)) or None,
                    kind=str(row.get("kind", "entry")),
                    title=str(row.get("title", "")),
                    markdown=str(row.get("markdown", "")),
                    updated_at=_normalize_datetime(row.get("updated_at", datetime.now(UTC))),
                )
            )
        db.commit()


def list_entries(kind: str | None = None, q: str | None = None) -> list[dict]:
    init_db()
    _bootstrap_if_empty()
    with SessionLocal() as db:
        rows = db.execute(select(KnowledgeRecord)).scalars().all()
        result: list[dict] = []
        for row in rows:
            if kind and row.kind != kind:
                continue
            if q:
                text = q.lower()
                if text not in row.title.lower() and text not in row.markdown.lower():
                    continue
            result.append(
                {
                    "id": row.id,
                    "kind": row.kind,
                    "title": row.title,
                    "markdown": row.markdown,
                    "updated_at": row.updated_at,
                }
            )
        return sorted(result, key=lambda item: item["updated_at"], reverse=True)


def create_entry(kind: str, title: str, markdown: str) -> dict:
    init_db()
    with SessionLocal() as db:
        row = KnowledgeRecord(kind=kind, title=title, markdown=markdown, updated_at=datetime.utcnow())
        db.add(row)
        db.commit()
        db.refresh(row)
        return {
            "id": row.id,
            "kind": row.kind,
            "title": row.title,
            "markdown": row.markdown,
            "updated_at": row.updated_at,
        }


def get_entry(entry_id: int) -> dict | None:
    init_db()
    _bootstrap_if_empty()
    with SessionLocal() as db:
        row = db.get(KnowledgeRecord, entry_id)
        if not row:
            return None
        return {
            "id": row.id,
            "kind": row.kind,
            "title": row.title,
            "markdown": row.markdown,
            "updated_at": row.updated_at,
        }


def delete_entry(entry_id: int) -> bool:
    init_db()
    with SessionLocal() as db:
        row = db.get(KnowledgeRecord, entry_id)
        if not row:
            return False
        db.delete(row)
        db.commit()
        return True
