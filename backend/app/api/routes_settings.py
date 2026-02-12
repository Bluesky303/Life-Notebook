from fastapi import APIRouter
from pydantic import BaseModel

from app.services.settings_storage import get_settings as db_get_settings
from app.services.settings_storage import update_settings as db_update_settings

router = APIRouter(prefix="/settings", tags=["settings"])


class SettingsPayload(BaseModel):
    default_provider: str
    model_name: str
    theme: str
    local_only: bool


_DEFAULT_SETTINGS = SettingsPayload(
    default_provider="codex",
    model_name="gpt-5-codex",
    theme="sci-fi",
    local_only=True,
)


@router.get("/", response_model=SettingsPayload)
def get_settings() -> SettingsPayload:
    row = db_get_settings()
    return SettingsPayload.model_validate(row)


@router.put("/", response_model=SettingsPayload)
def update_settings(payload: SettingsPayload) -> SettingsPayload:
    row = db_update_settings(payload.model_dump(mode="json"))
    return SettingsPayload.model_validate(row)