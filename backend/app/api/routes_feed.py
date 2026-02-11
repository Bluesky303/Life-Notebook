from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.json_store import read_json, write_json

router = APIRouter(prefix="/feed", tags=["feed"])

_FEED_FILE = "feed.json"


class FeedCreate(BaseModel):
    category: str
    content: str


class FeedOut(FeedCreate):
    id: int
    created_at: datetime


def _load_feeds() -> list[FeedOut]:
    rows = read_json(_FEED_FILE, [])
    return [FeedOut.model_validate(row) for row in rows]


def _save_feeds(feeds: list[FeedOut]) -> None:
    write_json(_FEED_FILE, [item.model_dump(mode="json") for item in feeds])


@router.get("/", response_model=list[FeedOut])
def list_feed() -> list[FeedOut]:
    feeds = _load_feeds()
    return list(reversed(feeds[-20:]))


@router.post("/", response_model=FeedOut)
def create_feed(payload: FeedCreate) -> FeedOut:
    feeds = _load_feeds()
    next_id = max([item.id for item in feeds], default=0) + 1
    item = FeedOut(id=next_id, created_at=datetime.utcnow(), **payload.model_dump())
    feeds.append(item)
    _save_feeds(feeds)
    return item


@router.delete("/{feed_id}")
def delete_feed(feed_id: int) -> dict[str, int | bool]:
    feeds = _load_feeds()
    new_feeds = [item for item in feeds if item.id != feed_id]
    if len(new_feeds) == len(feeds):
        raise HTTPException(status_code=404, detail="feed not found")

    _save_feeds(new_feeds)
    return {"deleted": True, "id": feed_id}
