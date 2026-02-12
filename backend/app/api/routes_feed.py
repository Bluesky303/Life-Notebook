from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.feed_storage import create_feed as db_create_feed
from app.services.feed_storage import delete_feed as db_delete_feed
from app.services.feed_storage import list_feeds as db_list_feeds

router = APIRouter(prefix="/feed", tags=["feed"])


class FeedCreate(BaseModel):
    category: str
    content: str


class FeedOut(FeedCreate):
    id: int
    created_at: datetime


@router.get("/", response_model=list[FeedOut])
def list_feed() -> list[FeedOut]:
    rows = db_list_feeds(limit=20)
    return [FeedOut.model_validate(row) for row in rows]


@router.post("/", response_model=FeedOut)
def create_feed(payload: FeedCreate) -> FeedOut:
    row = db_create_feed(payload.category, payload.content)
    return FeedOut.model_validate(row)


@router.delete("/{feed_id}")
def delete_feed(feed_id: int) -> dict[str, int | bool]:
    ok = db_delete_feed(feed_id)
    if not ok:
        raise HTTPException(status_code=404, detail="feed not found")
    return {"deleted": True, "id": feed_id}