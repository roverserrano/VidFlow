from __future__ import annotations

import os
import shutil
from pathlib import Path

from backend.config import project_root


def _candidate_names(name: str) -> list[str]:
    if os.name == "nt" and not name.endswith(".exe"):
        return [f"{name}.exe", name]
    return [name]


def resolve_tool(name: str, env_var: str | None = None) -> str | None:
    env_value = os.environ.get(env_var or "")
    if env_value and Path(env_value).expanduser().is_file():
        return str(Path(env_value).expanduser().resolve())

    root = project_root()
    candidate_dirs = [
        root / "resources" / "bin",
        root / "resources" / "bin" / name,
        root / "resources" / "bin" / "ffmpeg",
        root / "bin",
        root / "vendor" / "bin",
    ]

    for directory in candidate_dirs:
        for candidate_name in _candidate_names(name):
            candidate = directory / candidate_name
            if candidate.is_file():
                return str(candidate.resolve())

    found = shutil.which(name)
    return str(Path(found).resolve()) if found else None


def dependency_versions() -> dict[str, str | None]:
    return {
        "ffmpeg": resolve_tool("ffmpeg", "VIDFLOW_FFMPEG"),
        "yt-dlp": resolve_tool("yt-dlp", "VIDFLOW_YTDLP"),
    }

