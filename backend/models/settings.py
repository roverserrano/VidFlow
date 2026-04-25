from __future__ import annotations

from pydantic import BaseModel, Field


class UserSettings(BaseModel):
    download_directory: str | None = None
    audio_format: str = "mp3"
    theme: str = "system"
    log_level: str = "INFO"


class StorageInfo(BaseModel):
    path: str
    exists: bool
    total_bytes: int = 0
    used_bytes: int = 0
    free_bytes: int = 0
    total_text: str = "-"
    used_text: str = "-"
    free_text: str = "-"

