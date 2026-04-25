from __future__ import annotations

import re
import unicodedata
from datetime import datetime


RESERVED_NAMES = {
    "con",
    "prn",
    "aux",
    "nul",
    "com1",
    "com2",
    "com3",
    "com4",
    "com5",
    "com6",
    "com7",
    "com8",
    "com9",
    "lpt1",
    "lpt2",
    "lpt3",
    "lpt4",
    "lpt5",
    "lpt6",
    "lpt7",
    "lpt8",
    "lpt9",
}


def sanitize_title(value: str, *, max_length: int = 90) -> str:
    normalized = unicodedata.normalize("NFKD", value or "video")
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "_", ascii_text).strip("_").lower()
    cleaned = re.sub(r"_+", "_", cleaned)
    cleaned = cleaned[:max_length].strip("_")

    if not cleaned:
        cleaned = "video"
    if cleaned in RESERVED_NAMES:
        cleaned = f"{cleaned}_video"
    return cleaned


def timestamp_slug(now: datetime | None = None) -> str:
    return (now or datetime.now()).strftime("%Y%m%d_%H%M%S")


def build_download_basename(title: str, resolution: str | None, *, now: datetime | None = None) -> str:
    safe_title = sanitize_title(title)
    safe_resolution = sanitize_title(resolution or "best", max_length=24)
    return f"{safe_title}_{safe_resolution}_{timestamp_slug(now)}"

