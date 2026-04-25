from __future__ import annotations

from backend.downloader.facebook import FacebookDownloader
from backend.downloader.tiktok import TikTokDownloader
from backend.downloader.youtube import YouTubeDownloader
from backend.models import Platform
from backend.models.errors import VidFlowError


DOWNLOADERS = {
    Platform.YOUTUBE: YouTubeDownloader(),
    Platform.TIKTOK: TikTokDownloader(),
    Platform.FACEBOOK: FacebookDownloader(),
}


def get_downloader(platform: Platform):
    try:
        return DOWNLOADERS[platform]
    except KeyError as exc:
        raise VidFlowError("Plataforma no soportada.", code="unsupported_platform") from exc

