from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


APP_NAME = "VidFlow"
APP_VERSION = "0.3.0"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8716


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _platform_dir(kind: str) -> Path:
    override = os.environ.get(f"VIDFLOW_{kind.upper()}_DIR")
    if override:
        return Path(override).expanduser().resolve()

    try:
        from platformdirs import user_config_dir, user_data_dir, user_log_dir

        if kind == "config":
            return Path(user_config_dir(APP_NAME, APP_NAME))
        if kind == "data":
            return Path(user_data_dir(APP_NAME, APP_NAME))
        if kind == "log":
            return Path(user_log_dir(APP_NAME, APP_NAME))
    except Exception:
        pass

    base = Path.home() / ".vidflow"
    return base / kind


@dataclass(frozen=True)
class RuntimePaths:
    root: Path
    config_dir: Path
    data_dir: Path
    log_dir: Path
    settings_file: Path
    history_file: Path
    backend_log: Path


def runtime_paths() -> RuntimePaths:
    config_dir = _platform_dir("config")
    data_dir = _platform_dir("data")
    log_dir = _platform_dir("log")

    config_dir = _ensure_writable(config_dir, "config")
    data_dir = _ensure_writable(data_dir, "data")
    log_dir = _ensure_writable(log_dir, "log")

    return RuntimePaths(
        root=project_root(),
        config_dir=config_dir,
        data_dir=data_dir,
        log_dir=log_dir,
        settings_file=config_dir / "settings.json",
        history_file=data_dir / "history.json",
        backend_log=log_dir / "backend.log",
    )


def _ensure_writable(directory: Path, kind: str) -> Path:
    try:
        directory.mkdir(parents=True, exist_ok=True)
        probe = directory / ".write-test"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink(missing_ok=True)
        return directory
    except OSError:
        fallback = Path(os.environ.get("TMPDIR", "/tmp")) / "vidflow" / kind
        fallback.mkdir(parents=True, exist_ok=True)
        return fallback


def backend_host() -> str:
    return os.environ.get("VIDFLOW_BACKEND_HOST", DEFAULT_HOST)


def backend_port() -> int:
    try:
        return int(os.environ.get("VIDFLOW_BACKEND_PORT", DEFAULT_PORT))
    except ValueError:
        return DEFAULT_PORT
