from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class Platform(StrEnum):
    YOUTUBE = "youtube"
    TIKTOK = "tiktok"
    FACEBOOK = "facebook"


class DownloadType(StrEnum):
    VIDEO = "video"
    AUDIO = "audio"


class AudioFormat(StrEnum):
    MP3 = "mp3"
    M4A = "m4a"
    OGG = "ogg"


class DownloadStatus(StrEnum):
    ANALYZING = "analyzing"
    QUEUED = "queued"
    PREPARING = "preparing"
    DOWNLOADING = "downloading"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"
    CANCELED = "canceled"


class FormatOption(BaseModel):
    id: str
    label: str
    selector: str
    resolution: str = "best"
    height: int | None = None
    fps: int | None = None
    ext: str = "mp4"
    codec: str = ""
    filesize: int | None = None
    filesize_text: str = "-"
    is_native_mp4: bool = False


class MetadataRequest(BaseModel):
    url: str = Field(min_length=1)


class MediaMetadata(BaseModel):
    title: str
    webpage_url: str
    platform: Platform
    duration: int | None = None
    duration_text: str = "-"
    thumbnail: str = ""
    formats: list[FormatOption] = Field(default_factory=list)
    raw: dict[str, Any] = Field(default_factory=dict)


class DownloadRequest(BaseModel):
    url: str = Field(min_length=1)
    title: str = "video"
    platform: Platform | None = None
    thumbnail: str = ""
    download_type: DownloadType = DownloadType.VIDEO
    format_selector: str | None = None
    resolution: str | None = None
    audio_format: AudioFormat = AudioFormat.MP3
    output_dir: str | None = None


class ProgressEvent(BaseModel):
    job_id: str
    status: DownloadStatus
    percent: float | None = None
    speed: str = "-"
    eta: str = "-"
    downloaded: str = "-"
    message: str = ""
    file_path: str | None = None
    error: str | None = None


class DownloadResult(BaseModel):
    job_id: str
    title: str
    platform: Platform
    download_type: DownloadType
    format: str
    file_path: str
    thumbnail: str = ""


class DownloadJobSnapshot(BaseModel):
    job_id: str
    status: DownloadStatus
    title: str
    platform: Platform | None = None
    download_type: DownloadType
    percent: float | None = None
    message: str = ""
