from __future__ import annotations

from fastapi import APIRouter

from backend.config import APP_VERSION
from backend.services.ffmpeg_service import dependency_versions

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
def healthcheck() -> dict:
    return {
        "ok": True,
        "version": APP_VERSION,
        "dependencies": dependency_versions(),
    }

