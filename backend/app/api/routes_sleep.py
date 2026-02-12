from fastapi import APIRouter, HTTPException

from app.schemas.sleep import SleepLogCreate, SleepLogOut
from app.services.sleep_storage import create_sleep_log as db_create_sleep_log
from app.services.sleep_storage import delete_sleep_log as db_delete_sleep_log
from app.services.sleep_storage import list_sleep_logs as db_list_sleep_logs

router = APIRouter(prefix="/sleep", tags=["sleep"])


@router.get("/logs", response_model=list[SleepLogOut])
def list_sleep_logs() -> list[SleepLogOut]:
    rows = db_list_sleep_logs()
    return [SleepLogOut.model_validate(row) for row in rows]


@router.post("/logs", response_model=SleepLogOut)
def create_sleep_log(payload: SleepLogCreate) -> SleepLogOut:
    if payload.end_at <= payload.start_at:
        raise HTTPException(status_code=400, detail="end_at must be later than start_at")

    row = db_create_sleep_log(payload.start_at, payload.end_at, payload.note)
    return SleepLogOut.model_validate(row)


@router.delete("/logs/{log_id}")
def delete_sleep_log(log_id: int) -> dict[str, int | bool]:
    ok = db_delete_sleep_log(log_id)
    if not ok:
        raise HTTPException(status_code=404, detail="sleep log not found")

    return {"deleted": True, "id": log_id}