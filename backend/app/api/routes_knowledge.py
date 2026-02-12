from datetime import datetime

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.services.knowledge_storage import create_entry as db_create_entry
from app.services.knowledge_storage import delete_entry as db_delete_entry
from app.services.knowledge_storage import get_entry as db_get_entry
from app.services.knowledge_storage import list_entries as db_list_entries

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


class EntryCreate(BaseModel):
    kind: str
    title: str
    markdown: str


class EntryOut(EntryCreate):
    id: int
    updated_at: datetime


@router.get("/", response_model=list[EntryOut])
def list_entries(kind: str | None = Query(default=None), q: str | None = Query(default=None)) -> list[EntryOut]:
    rows = db_list_entries(kind=kind, q=q)
    return [EntryOut.model_validate(row) for row in rows]


@router.post("/", response_model=EntryOut)
def create_entry(payload: EntryCreate) -> EntryOut:
    row = db_create_entry(payload.kind, payload.title, payload.markdown)
    return EntryOut.model_validate(row)


@router.get("/{entry_id}", response_model=EntryOut)
def get_entry(entry_id: int) -> EntryOut:
    row = db_get_entry(entry_id)
    if not row:
        raise HTTPException(status_code=404, detail="entry not found")
    return EntryOut.model_validate(row)


@router.delete("/{entry_id}")
def delete_entry(entry_id: int) -> dict[str, int | bool]:
    ok = db_delete_entry(entry_id)
    if not ok:
        raise HTTPException(status_code=404, detail="entry not found")
    return {"deleted": True, "id": entry_id}