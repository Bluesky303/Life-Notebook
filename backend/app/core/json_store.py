import json
from pathlib import Path
from threading import Lock
from typing import Any

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

_STORE_LOCK = Lock()


def _path(name: str) -> Path:
    return DATA_DIR / name


def read_json(name: str, default: Any) -> Any:
    file_path = _path(name)
    with _STORE_LOCK:
        if not file_path.exists():
            file_path.write_text(json.dumps(default, ensure_ascii=False, indent=2), encoding="utf-8")
            return default

        raw = file_path.read_text(encoding="utf-8")
        if not raw.strip():
            file_path.write_text(json.dumps(default, ensure_ascii=False, indent=2), encoding="utf-8")
            return default

        return json.loads(raw)


def write_json(name: str, data: Any) -> None:
    file_path = _path(name)
    with _STORE_LOCK:
        file_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
