from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path


def app_root() -> Path:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(getattr(sys, "_MEIPASS"))
    return Path(__file__).resolve().parents[2]


def ensure_output_folder(folder: str) -> str:
    folder_path = Path(folder).expanduser().resolve()
    folder_path.mkdir(parents=True, exist_ok=True)
    return str(folder_path)


def _candidate_names(name: str) -> list[str]:
    if os.name == "nt" and not name.lower().endswith(".exe"):
        return [f"{name}.exe", name]
    return [name]


def resolve_executable(name: str, *, env_var: str | None = None) -> str:
    env_value = os.environ.get(env_var or "")
    if env_value:
        path = Path(env_value).expanduser()
        if path.is_file():
            return str(path.resolve())

    root = app_root()
    candidate_dirs = [
        root / "bin",
        root / "vendor" / "bin",
        Path.cwd() / "bin",
    ]

    for directory in candidate_dirs:
        for candidate_name in _candidate_names(name):
            path = directory / candidate_name
            if path.is_file():
                return str(path.resolve())

    path = shutil.which(name)
    if path:
        return str(Path(path).resolve())

    raise RuntimeError(
        f"No se encontró {name}. Instálalo, agrégalo al PATH o define "
        f"{env_var or name.upper()} con la ruta del ejecutable."
    )


def format_bytes(value: int | None) -> str:
    if value is None:
        return "—"

    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(value)
    unit = 0

    while size >= 1024 and unit < len(units) - 1:
        size /= 1024
        unit += 1

    if unit == 0:
        return f"{int(size)} {units[unit]}"
    return f"{size:.1f} {units[unit]}"


def format_speed(value: float | None) -> str:
    if value is None:
        return "—"
    return f"{format_bytes(int(value))}/s"


def format_eta(value: float | None) -> str:
    if value is None:
        return "—"

    total = int(value)
    hours = total // 3600
    minutes = (total % 3600) // 60
    seconds = total % 60

    if hours > 0:
        return f"{hours}:{minutes:02}:{seconds:02}"
    return f"{minutes}:{seconds:02}"


def format_duration(seconds: object) -> str:
    try:
        total = int(seconds) if seconds not in (None, "", "none") else 0
    except Exception:
        total = 0

    if total <= 0:
        return "—"

    hours = total // 3600
    minutes = (total % 3600) // 60
    seconds_value = total % 60

    if hours > 0:
        return f"{hours}:{minutes:02}:{seconds_value:02}"
    return f"{minutes}:{seconds_value:02}"
