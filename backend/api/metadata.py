from __future__ import annotations

from fastapi import APIRouter

from backend.downloader import get_downloader
from backend.models import MediaMetadata, MetadataRequest
from backend.utils.platform_detect import detect_platform

router = APIRouter(prefix="/metadata", tags=["metadata"])


@router.post("", response_model=MediaMetadata)
def analyze_metadata(payload: MetadataRequest) -> MediaMetadata:
    platform = detect_platform(payload.url)
    downloader = get_downloader(platform)
    return downloader.analyze(payload.url)

