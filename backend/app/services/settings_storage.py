from app.core.db import SessionLocal, init_db
from app.core.json_store import read_json
from app.models.setting import SettingRecord

_SETTINGS_FILE = "settings.json"
_DEFAULT_SETTINGS = {
    "default_provider": "codex",
    "model_name": "gpt-5-codex",
    "theme": "sci-fi",
    "local_only": True,
}


def _bootstrap_if_empty() -> None:
    with SessionLocal() as db:
        row = db.get(SettingRecord, 1)
        if row:
            return
        payload = read_json(_SETTINGS_FILE, _DEFAULT_SETTINGS)
        db.add(
            SettingRecord(
                id=1,
                default_provider=str(payload.get("default_provider", "codex")),
                model_name=str(payload.get("model_name", "gpt-5-codex")),
                theme=str(payload.get("theme", "sci-fi")),
                local_only=bool(payload.get("local_only", True)),
            )
        )
        db.commit()


def get_settings() -> dict:
    init_db()
    _bootstrap_if_empty()
    with SessionLocal() as db:
        row = db.get(SettingRecord, 1)
        if not row:
            return dict(_DEFAULT_SETTINGS)
        return {
            "default_provider": row.default_provider,
            "model_name": row.model_name,
            "theme": row.theme,
            "local_only": row.local_only,
        }


def update_settings(payload: dict) -> dict:
    init_db()
    _bootstrap_if_empty()
    with SessionLocal() as db:
        row = db.get(SettingRecord, 1)
        if not row:
            row = SettingRecord(id=1, **_DEFAULT_SETTINGS)
            db.add(row)
        row.default_provider = str(payload["default_provider"])
        row.model_name = str(payload["model_name"])
        row.theme = str(payload["theme"])
        row.local_only = bool(payload["local_only"])
        db.commit()
        return {
            "default_provider": row.default_provider,
            "model_name": row.model_name,
            "theme": row.theme,
            "local_only": row.local_only,
        }
