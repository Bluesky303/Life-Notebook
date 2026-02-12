from fastapi import APIRouter, HTTPException

from app.core.json_store import read_json, write_json
from app.schemas.sleep import SleepLogCreate, SleepLogOut

router = APIRouter(prefix="/sleep", tags=["sleep"])

_SLEEP_FILE = "sleep.json"
_DEFAULT_LOGS: list[dict] = []


def _load_logs() -> list[SleepLogOut]:
    rows = read_json(_SLEEP_FILE, _DEFAULT_LOGS)
    return [SleepLogOut.model_validate(row) for row in rows]


def _save_logs(logs: list[SleepLogOut]) -> None:
    write_json(_SLEEP_FILE, [item.model_dump(mode="json") for item in logs])


@router.get("/logs", response_model=list[SleepLogOut])
def list_sleep_logs() -> list[SleepLogOut]:
    logs = _load_logs()
    return list(sorted(logs, key=lambda row: row.end_at, reverse=True))


@router.post("/logs", response_model=SleepLogOut)
def create_sleep_log(payload: SleepLogCreate) -> SleepLogOut:
    if payload.end_at <= payload.start_at:
        raise HTTPException(status_code=400, detail="end_at must be later than start_at")

    logs = _load_logs()
    next_id = max([item.id for item in logs], default=0) + 1
    log = SleepLogOut(id=next_id, **payload.model_dump())
    logs.append(log)
    _save_logs(logs)
    return log


@router.delete("/logs/{log_id}")
def delete_sleep_log(log_id: int) -> dict[str, int | bool]:
    logs = _load_logs()
    new_logs = [item for item in logs if item.id != log_id]
    if len(new_logs) == len(logs):
        raise HTTPException(status_code=404, detail="sleep log not found")

    _save_logs(new_logs)
    return {"deleted": True, "id": log_id}
