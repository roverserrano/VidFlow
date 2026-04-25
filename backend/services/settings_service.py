from __future__ import annotations

import json
from pathlib import Path
from threading import Lock

from backend.config import runtime_paths
from backend.models import UserSettings


class SettingsService:
    def __init__(self) -> None:
        self._paths = runtime_paths()
        self._lock = Lock()

    def default_download_directory(self) -> str:
        for name in ("Downloads", "Descargas"):
            downloads = Path.home() / name
            if downloads.exists():
                return str(downloads)
        return str(Path.home())

    def read(self) -> UserSettings:
        with self._lock:
            if not self._paths.settings_file.exists():
                return UserSettings(download_directory=self.default_download_directory())

            try:
                data = json.loads(self._paths.settings_file.read_text(encoding="utf-8"))
            except Exception:
                data = {}

            settings = UserSettings(**data)
            if not settings.download_directory:
                settings.download_directory = self.default_download_directory()
            return settings

    def write(self, settings: UserSettings) -> UserSettings:
        with self._lock:
            self._paths.settings_file.parent.mkdir(parents=True, exist_ok=True)
            self._paths.settings_file.write_text(
                settings.model_dump_json(indent=2),
                encoding="utf-8",
            )
            return settings

    def patch(self, changes: dict) -> UserSettings:
        current = self.read().model_dump()
        current.update({key: value for key, value in changes.items() if value is not None})
        return self.write(UserSettings(**current))


settings_service = SettingsService()
