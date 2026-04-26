from __future__ import annotations

from typing import Any

from backend.models import FormatOption
from backend.utils.formatting import format_bytes


def _safe_int(value: Any) -> int | None:
    try:
        if value in (None, "", "none", "NA"):
            return None
        return int(float(value))
    except Exception:
        return None


def _safe_float(value: Any) -> float:
    try:
        if value in (None, "", "none", "NA"):
            return 0.0
        return float(value)
    except Exception:
        return 0.0


def _text(item: dict[str, Any], key: str) -> str:
    return str(item.get(key) or "").lower().strip()


def _height(item: dict[str, Any]) -> int | None:
    return _safe_int(item.get("height"))


def _fps(item: dict[str, Any]) -> int | None:
    return _safe_int(item.get("fps"))


def _filesize(item: dict[str, Any]) -> int | None:
    return _safe_int(item.get("filesize")) or _safe_int(item.get("filesize_approx"))


def _vcodec(item: dict[str, Any]) -> str:
    return _text(item, "vcodec")


def _acodec(item: dict[str, Any]) -> str:
    return _text(item, "acodec")


def _ext(item: dict[str, Any]) -> str:
    return _text(item, "ext")


def _is_video(item: dict[str, Any]) -> bool:
    return _vcodec(item) not in {"", "none"}


def _is_progressive(item: dict[str, Any]) -> bool:
    return _is_video(item) and _acodec(item) not in {"", "none"}


def _is_h264(item: dict[str, Any]) -> bool:
    return _vcodec(item).startswith(("avc1", "avc3", "h264"))


def _codec_label(item: dict[str, Any]) -> str:
    codec = _vcodec(item)
    if _is_h264(item):
        return "H.264"
    if codec.startswith("av01") or "av1" in codec:
        return "AV1"
    if codec.startswith("vp9"):
        return "VP9"
    if codec.startswith(("hvc1", "hev1", "hevc")):
        return "HEVC"
    return (item.get("vcodec") or "video").upper()


def _score(item: dict[str, Any]) -> tuple:
    return (
        1 if _is_h264(item) else 0,
        1 if _ext(item) == "mp4" else 0,
        _fps(item) or 0,
        _safe_float(item.get("tbr")),
        _filesize(item) or 0,
    )


def _is_facebook(raw: dict[str, Any]) -> bool:
    extractor = str(raw.get("extractor_key") or raw.get("extractor") or "").lower()
    return "facebook" in extractor


def _is_tiktok(raw: dict[str, Any]) -> bool:
    extractor = str(raw.get("extractor_key") or raw.get("extractor") or "").lower()
    return "tiktok" in extractor


def _tiktok_selector_for_height(height: int) -> str:
    return (
        f"best[height<={height}][ext=mp4][format_id*=h264][acodec^=mp4a]/"
        f"best[height<={height}][ext=mp4][vcodec^=avc1][acodec^=mp4a]/"
        f"best[height<={height}][ext=mp4][vcodec^=h264][acodec^=mp4a]/"
        f"best[ext=mp4][format_id*=h264][acodec^=mp4a]/"
        "best[ext=mp4][vcodec^=avc1][acodec^=mp4a]"
    )


def _selector_for_height(height: int, *, facebook_mode: bool = False, tiktok_mode: bool = False) -> str:
    if tiktok_mode:
        return _tiktok_selector_for_height(height)

    if facebook_mode:
        return (
            f"best[height<={height}][ext=mp4][vcodec^=avc1][acodec^=mp4a]/"
            f"best[height<={height}][ext=mp4][vcodec!*=av01][vcodec!*=vp9][vcodec!*=hvc1][vcodec!*=hev1][vcodec!*=hevc][vcodec!*=h265][vcodec!*=dvh1][vcodec!*=dvhe]/"
            f"best[ext=mp4][vcodec^=avc1][acodec^=mp4a]/"
            f"best[ext=mp4][vcodec!*=av01][vcodec!*=vp9][vcodec!*=hvc1][vcodec!*=hev1][vcodec!*=hevc][vcodec!*=h265][vcodec!*=dvh1][vcodec!*=dvhe]/"
            "best"
        )

    return (
        f"bestvideo[height<={height}][ext=mp4][vcodec^=avc]+bestaudio[ext=m4a]/"
        f"bestvideo[height<={height}][ext=mp4][vcodec!*=av01][vcodec!*=vp9][vcodec!*=hvc1][vcodec!*=hev1][vcodec!*=hevc][vcodec!*=h265][vcodec!*=dvh1][vcodec!*=dvhe]+bestaudio[ext=m4a]/"
        f"best[height<={height}][ext=mp4][vcodec^=avc1][acodec^=mp4a]/"
        f"best[height<={height}][ext=mp4][acodec^=mp4a][vcodec!*=av01][vcodec!*=vp9][vcodec!*=hvc1][vcodec!*=hev1][vcodec!*=hevc][vcodec!*=h265][vcodec!*=dvh1][vcodec!*=dvhe]/"
        f"bestvideo[height<={height}]+bestaudio/best[height<={height}]/best"
    )


def default_video_selector(*, facebook_mode: bool = False, tiktok_mode: bool = False) -> str:
    if tiktok_mode:
        return _tiktok_selector_for_height(2160)

    if facebook_mode:
        return (
            "best[ext=mp4][vcodec^=avc1][acodec^=mp4a]/"
            "best[ext=mp4][vcodec!*=av01][vcodec!*=vp9][vcodec!*=hvc1][vcodec!*=hev1][vcodec!*=hevc][vcodec!*=h265][vcodec!*=dvh1][vcodec!*=dvhe]/"
            "best"
        )

    return (
        "bestvideo[ext=mp4][vcodec^=avc]+bestaudio[ext=m4a]/"
        "bestvideo[ext=mp4][vcodec!*=av01][vcodec!*=vp9][vcodec!*=hvc1][vcodec!*=hev1][vcodec!*=hevc][vcodec!*=h265][vcodec!*=dvh1][vcodec!*=dvhe]+bestaudio[ext=m4a]/"
        "best[ext=mp4][vcodec^=avc1][acodec^=mp4a]/"
        "best[ext=mp4][acodec^=mp4a][vcodec!*=av01][vcodec!*=vp9][vcodec!*=hvc1][vcodec!*=hev1][vcodec!*=hevc][vcodec!*=h265][vcodec!*=dvh1][vcodec!*=dvhe]/"
        "bestvideo+bestaudio/best"
    )


def progressive_video_selector(height: int | None = None) -> str:
    height_filter = f"[height<={height}]" if height else ""
    return (
        f"best{height_filter}[ext=mp4][vcodec^=avc1][acodec^=mp4a]/"
        f"best{height_filter}[ext=mp4][acodec^=mp4a][vcodec!*=av01][vcodec!*=vp9][vcodec!*=hvc1][vcodec!*=hev1][vcodec!*=hevc][vcodec!*=h265][vcodec!*=dvh1][vcodec!*=dvhe]/"
        f"best[ext=mp4][vcodec^=avc1][acodec^=mp4a]/"
        f"best[ext=mp4][acodec^=mp4a][vcodec!*=av01][vcodec!*=vp9][vcodec!*=hvc1][vcodec!*=hev1][vcodec!*=hevc][vcodec!*=h265][vcodec!*=dvh1][vcodec!*=dvhe]/"
        "best"
    )


def build_quality_options(raw: dict[str, Any]) -> list[FormatOption]:
    formats = raw.get("formats") or []
    facebook_mode = _is_facebook(raw)
    tiktok_mode = _is_tiktok(raw)
    videos = [item for item in formats if _is_video(item) and _height(item)]
    heights = sorted({_height(item) for item in videos if _height(item)}, reverse=True)
    options: list[FormatOption] = []

    for height in heights:
        same_height = [item for item in videos if _height(item) == height]
        if not same_height:
            continue
        best = sorted(same_height, key=_score, reverse=True)[0]
        fps = _fps(best)
        codec = _codec_label(best)
        ext = _ext(best) or "mp4"
        label_parts = [f"{height}p"]
        if fps and fps >= 50:
            label_parts.append(f"{fps} fps")
        label_parts.extend([codec, ext.upper()])

        options.append(
            FormatOption(
                id=f"{height}p",
                label=" · ".join(label_parts),
                selector=_selector_for_height(height, facebook_mode=facebook_mode, tiktok_mode=tiktok_mode),
                resolution=f"{height}p",
                height=height,
                fps=fps,
                ext=ext,
                codec=codec,
                filesize=_filesize(best),
                filesize_text=format_bytes(_filesize(best)),
                is_native_mp4=ext == "mp4" and _is_h264(best) and _is_progressive(best),
            )
        )

    if not options:
        options.append(
            FormatOption(
                id="best",
                label="Mejor calidad disponible",
                selector=default_video_selector(facebook_mode=facebook_mode, tiktok_mode=tiktok_mode),
                resolution="best",
            )
        )

    return options
