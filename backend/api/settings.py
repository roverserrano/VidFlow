from __future__ import annotations

from fastapi import APIRouter

from backend.models import StorageInfo, UserSettings
from backend.services.settings_service import settings_service
from backend.services.storage_service import storage_info

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("", response_model=UserSettings)
def get_settings() -> UserSettings:
    return settings_service.read()


@router.put("", response_model=UserSettings)
def update_settings(payload: UserSettings) -> UserSettings:
    return settings_service.write(payload)


@router.patch("", response_model=UserSettings)
def patch_settings(payload: dict) -> UserSettings:
    return settings_service.patch(payload)


@router.get("/storage", response_model=StorageInfo)
def get_storage_info(path: str | None = None) -> StorageInfo:
    settings = settings_service.read()
    return storage_info(path or settings.download_directory)

