from fastapi import APIRouter
from pydantic import BaseModel

from app.core.json_store import read_json, write_json

router = APIRouter(prefix="/settings", tags=["settings"])

_SETTINGS_FILE = "settings.json"


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
    row = read_json(_SETTINGS_FILE, _DEFAULT_SETTINGS.model_dump(mode="json"))
    return SettingsPayload.model_validate(row)


@router.put("/", response_model=SettingsPayload)
def update_settings(payload: SettingsPayload) -> SettingsPayload:
    write_json(_SETTINGS_FILE, payload.model_dump(mode="json"))
    return payload
