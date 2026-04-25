from __future__ import annotations

from urllib.parse import urlparse

from backend.models import Platform
from backend.models.errors import VidFlowError


YOUTUBE_HOSTS = {"youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be", "music.youtube.com"}
TIKTOK_HOSTS = {"tiktok.com", "www.tiktok.com", "vm.tiktok.com", "vt.tiktok.com"}
FACEBOOK_HOSTS = {
    "facebook.com",
    "www.facebook.com",
    "m.facebook.com",
    "fb.watch",
    "www.fb.watch",
}


def detect_platform(url: str) -> Platform:
    parsed = urlparse((url or "").strip())
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise VidFlowError("URL no valida.", code="invalid_url")

    host = parsed.netloc.lower().split(":")[0]
    if host in YOUTUBE_HOSTS or host.endswith(".youtube.com"):
        return Platform.YOUTUBE
    if host in TIKTOK_HOSTS or host.endswith(".tiktok.com"):
        return Platform.TIKTOK
    if host in FACEBOOK_HOSTS or host.endswith(".facebook.com"):
        return Platform.FACEBOOK

    raise VidFlowError("Plataforma no soportada. Usa YouTube, TikTok o Facebook.", code="unsupported_platform")

