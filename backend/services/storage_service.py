from __future__ import annotations

import shutil
from pathlib import Path

from backend.models import StorageInfo
from backend.models.errors import VidFlowError
from backend.utils.formatting import format_bytes


def ensure_directory(path: str | None) -> Path:
    if not path:
        raise VidFlowError("Debes seleccionar una carpeta de destino.", code="missing_output_dir")

    directory = Path(path).expanduser().resolve()
    directory.mkdir(parents=True, exist_ok=True)
    if not directory.is_dir():
        raise VidFlowError("La ruta seleccionada no es una carpeta valida.", code="invalid_output_dir")
    return directory


def storage_info(path: str | None) -> StorageInfo:
    directory = Path(path or Path.home()).expanduser()
    exists = directory.exists()
    target = directory if exists else directory.parent
    while not target.exists() and target != target.parent:
        target = target.parent

    usage = shutil.disk_usage(target)
    return StorageInfo(
        path=str(directory),
        exists=exists,
        total_bytes=usage.total,
        used_bytes=usage.used,
        free_bytes=usage.free,
        total_text=format_bytes(usage.total),
        used_text=format_bytes(usage.used),
        free_text=format_bytes(usage.free),
    )


def find_created_file(directory: Path, basename: str) -> Path | None:
    candidates = sorted(
        directory.glob(f"{basename}.*"),
        key=lambda item: item.stat().st_mtime if item.exists() else 0,
        reverse=True,
    )
    for candidate in candidates:
        if candidate.is_file() and not candidate.name.endswith(".part"):
            return candidate
    return None
