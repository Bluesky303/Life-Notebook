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

        raw_bytes = file_path.read_bytes()
        had_bom = raw_bytes.startswith(b"\xef\xbb\xbf")
        raw = raw_bytes.decode("utf-8-sig")

        if not raw.strip():
            file_path.write_text(json.dumps(default, ensure_ascii=False, indent=2), encoding="utf-8")
            return default

        data = json.loads(raw)

        # Normalize BOM files back to plain UTF-8 for stable subsequent reads.
        if had_bom:
            file_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

        return data


def write_json(name: str, data: Any) -> None:
    file_path = _path(name)
    with _STORE_LOCK:
        file_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
