from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any


class DownloadStatus(StrEnum):
    QUEUED = "queued"
    PREPARING = "preparing"
    DOWNLOADING = "downloading"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"
    CANCELED = "canceled"


class DownloadKind(StrEnum):
    VIDEO = "video"
    AUDIO = "audio"


class CompatibilityMode(StrEnum):
    COMPATIBLE = "compatible"
    ORIGINAL = "original"


@dataclass(slots=True)
class FormatOption:
    plan: str
    label: str
    resolution: str
    note: str
    height: int | None = None
    fps: int | None = None
    ext: str = ""
    codec: str = ""
    filesize: int | None = None
    filesize_text: str = "—"
    compatibility: str = "good"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class MediaInfo:
    title: str
    webpage_url: str
    extractor: str
    duration: int | None
    duration_text: str
    thumbnail: str
    formats: list[FormatOption] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["formats"] = [item.to_dict() for item in self.formats]
        return data


@dataclass(slots=True)
class DownloadRequest:
    job_id: str
    title: str
    url: str
    folder: str
    format_plan: str
    kind: DownloadKind
    audio_format: str = "mp3"
    compatibility_mode: CompatibilityMode = CompatibilityMode.COMPATIBLE


@dataclass(slots=True)
class DownloadUpdate:
    job_id: str
    title: str
    folder: str
    status: DownloadStatus
    percent: float = -1.0
    speed_text: str = "—"
    eta_text: str = "—"
    bytes_text: str = "—"
    message: str = ""

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["status"] = str(self.status)
        return data
