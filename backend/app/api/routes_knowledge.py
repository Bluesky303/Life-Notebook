from datetime import datetime

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.core.json_store import read_json, write_json

router = APIRouter(prefix="/knowledge", tags=["knowledge"])

_KNOWLEDGE_FILE = "knowledge.json"
_DEFAULT_ENTRIES = [
    {
        "id": 1,
        "kind": "entry",
        "title": "新芯片词条：NPU 架构速记",
        "markdown": "## 核心点\n- 关注 TOPS/W\n- 关注内存带宽\n- 关注量化支持",
        "updated_at": "2026-02-07T21:30:00",
    },
    {
        "id": 2,
        "kind": "blog",
        "title": "一次接口超时排查记录",
        "markdown": "## 现象\n请求偶发超时\n\n## 定位\n发现重试参数过小\n\n## 结论\n提高超时并增加日志维度",
        "updated_at": "2026-02-08T09:10:00",
    },
]


class EntryCreate(BaseModel):
    kind: str
    title: str
    markdown: str


class EntryOut(EntryCreate):
    id: int
    updated_at: datetime


def _load_entries() -> list[EntryOut]:
    rows = read_json(_KNOWLEDGE_FILE, _DEFAULT_ENTRIES)
    return [EntryOut.model_validate(row) for row in rows]


def _save_entries(entries: list[EntryOut]) -> None:
    write_json(_KNOWLEDGE_FILE, [item.model_dump(mode="json") for item in entries])


@router.get("/", response_model=list[EntryOut])
def list_entries(kind: str | None = Query(default=None), q: str | None = Query(default=None)) -> list[EntryOut]:
    rows = _load_entries()

    if kind:
        rows = [row for row in rows if row.kind == kind]

    if q:
        q_lower = q.lower()
        rows = [row for row in rows if q_lower in row.title.lower() or q_lower in row.markdown.lower()]

    return sorted(rows, key=lambda row: row.updated_at, reverse=True)


@router.post("/", response_model=EntryOut)
def create_entry(payload: EntryCreate) -> EntryOut:
    entries = _load_entries()
    next_id = max([row.id for row in entries], default=0) + 1
    entry = EntryOut(id=next_id, updated_at=datetime.utcnow(), **payload.model_dump())
    entries.append(entry)
    _save_entries(entries)
    return entry


@router.delete("/{entry_id}")
def delete_entry(entry_id: int) -> dict[str, int | bool]:
    entries = _load_entries()
    new_entries = [row for row in entries if row.id != entry_id]
    if len(new_entries) == len(entries):
        raise HTTPException(status_code=404, detail="entry not found")

    _save_entries(new_entries)
    return {"deleted": True, "id": entry_id}
