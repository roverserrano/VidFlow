from __future__ import annotations

import json
from datetime import datetime
from threading import RLock
from uuid import uuid4

from backend.config import runtime_paths
from backend.models import DownloadResult


class HistoryService:
    def __init__(self) -> None:
        self._paths = runtime_paths()
        self._lock = RLock()

    def list(self) -> list[dict]:
        with self._lock:
            if not self._paths.history_file.exists():
                return []
            try:
                data = json.loads(self._paths.history_file.read_text(encoding="utf-8"))
            except Exception:
                return []
            return data if isinstance(data, list) else []

    def add(self, result: DownloadResult) -> dict:
        with self._lock:
            items = self.list()
            entry = result.model_dump(mode="json")
            entry["id"] = str(uuid4())
            entry["created_at"] = datetime.now().isoformat(timespec="seconds")
            items.insert(0, entry)
            self._paths.history_file.parent.mkdir(parents=True, exist_ok=True)
            self._paths.history_file.write_text(
                json.dumps(items[:500], ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            return entry

    def delete(self, item_id: str) -> bool:
        with self._lock:
            items = self.list()
            next_items = [item for item in items if item.get("id") != item_id]
            self._paths.history_file.write_text(
                json.dumps(next_items, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            return len(next_items) != len(items)


history_service = HistoryService()
