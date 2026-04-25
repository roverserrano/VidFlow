from __future__ import annotations

import base64
import json
from typing import Any

from vidflow.core.system import format_bytes
from vidflow.models import FormatOption

PLAN_PREFIX = "vf1:"


def _safe_int(value: Any) -> int | None:
    try:
        if value in (None, "", "none", "NA"):
            return None
        return int(float(value))
    except Exception:
        return None


def _safe_float(value: Any) -> float | None:
    try:
        if value in (None, "", "none", "NA"):
            return None
        return float(value)
    except Exception:
        return None


def _text(item: dict[str, Any], key: str) -> str:
    return str(item.get(key) or "").lower().strip()


def _height(item: dict[str, Any]) -> int | None:
    return _safe_int(item.get("height"))


def _fps(item: dict[str, Any]) -> int:
    return _safe_int(item.get("fps")) or 0


def _filesize(item: dict[str, Any]) -> int | None:
    return _safe_int(item.get("filesize")) or _safe_int(item.get("filesize_approx"))


def _vcodec(item: dict[str, Any]) -> str:
    return _text(item, "vcodec")


def _acodec(item: dict[str, Any]) -> str:
    return _text(item, "acodec")


def _ext(item: dict[str, Any]) -> str:
    return _text(item, "ext")


def _format_id(item: dict[str, Any]) -> str:
    return str(item.get("format_id") or "").strip()


def is_video(item: dict[str, Any]) -> bool:
    return _vcodec(item) not in ("", "none")


def is_audio_only(item: dict[str, Any]) -> bool:
    return _vcodec(item) == "none" and _acodec(item) not in ("", "none")


def is_progressive(item: dict[str, Any]) -> bool:
    return is_video(item) and _acodec(item) not in ("", "none")


def is_h264(item: dict[str, Any]) -> bool:
    codec = _vcodec(item)
    return codec.startswith(("avc1", "avc3", "h264"))


def is_av1(item: dict[str, Any]) -> bool:
    codec = _vcodec(item)
    return codec.startswith("av01") or codec == "av1" or "av1" in codec


def is_vp9(item: dict[str, Any]) -> bool:
    return _vcodec(item).startswith("vp9")


def is_aac(item: dict[str, Any]) -> bool:
    codec = _acodec(item)
    return codec.startswith(("mp4a", "aac"))


def codec_name(item: dict[str, Any]) -> str:
    codec = _vcodec(item)
    if is_h264(item):
        return "H.264"
    if is_av1(item):
        return "AV1"
    if is_vp9(item):
        return "VP9"
    if codec.startswith(("hev1", "hvc1", "hevc")):
        return "HEVC"
    return str(item.get("vcodec") or "VIDEO").upper()


def extractor_text(raw: dict[str, Any]) -> str:
    return str(raw.get("extractor_key") or raw.get("extractor") or "").strip()


def is_facebook(raw: dict[str, Any]) -> bool:
    return "facebook" in extractor_text(raw).lower()


def _quality_name(height: int) -> str:
    if height >= 2160:
        return "4K"
    if height >= 1440:
        return "2K"
    if height >= 1080:
        return "Full HD"
    if height >= 720:
        return "HD"
    return ""


def _dynamic_range(item: dict[str, Any]) -> str:
    value = str(item.get("dynamic_range") or "").upper()
    if value in ("", "SDR", "UNKNOWN", "NONE"):
        return ""
    return value


def _video_score(item: dict[str, Any]) -> tuple:
    return (
        _fps(item),
        1 if _dynamic_range(item) else 0,
        _safe_float(item.get("tbr")) or 0.0,
        1 if _ext(item) == "mp4" else 0,
        _filesize(item) or 0,
    )


def _compatibility_score(item: dict[str, Any]) -> tuple:
    return (
        1 if is_h264(item) else 0,
        1 if not is_av1(item) else 0,
        1 if not is_vp9(item) else 0,
        1 if _ext(item) == "mp4" else 0,
        1 if is_aac(item) else 0,
        _fps(item),
        _safe_float(item.get("tbr")) or 0.0,
        _filesize(item) or 0,
    )


def _pick_best(items: list[dict[str, Any]], *, compatible: bool = False) -> dict[str, Any] | None:
    if not items:
        return None
    key = _compatibility_score if compatible else _video_score
    return sorted(items, key=key, reverse=True)[0]


def _has_m4a_audio(formats: list[dict[str, Any]]) -> bool:
    return any(is_audio_only(item) and (_ext(item) in {"m4a", "mp4"} or is_aac(item)) for item in formats)


def _selector_for(item: dict[str, Any]) -> tuple[str, str, str]:
    format_id = _format_id(item)
    container = _ext(item) or "mp4"

    if is_progressive(item):
        return "single", container, format_id or "best"

    if container == "mp4":
        selector = f"{format_id}+bestaudio[ext=m4a]/{format_id}+bestaudio/{format_id}"
        return "merge", "mp4", selector

    selector = f"{format_id}+bestaudio/{format_id}/best"
    return "merge", "mkv", selector


def _height_selector(height: int, *, compatible: bool) -> tuple[str, str, str]:
    if compatible:
        selector = (
            f"bestvideo[height={height}][ext=mp4][vcodec^=avc]+bestaudio[ext=m4a]/"
            f"bestvideo[height<={height}][ext=mp4][vcodec^=avc]+bestaudio[ext=m4a]/"
            f"bestvideo[height={height}][ext=mp4]+bestaudio[ext=m4a]/"
            f"best[height={height}][ext=mp4]/best[height<={height}][ext=mp4]/best"
        )
        return "merge", "mp4", selector

    selector = (
        f"bestvideo[height={height}]+bestaudio/"
        f"bestvideo*[height={height}]+bestaudio/"
        f"best[height={height}]/"
        f"bestvideo[height<={height}]+bestaudio/"
        f"best[height<={height}]/best"
    )
    return "merge", "mkv", selector


def encode_plan(plan: dict[str, Any]) -> str:
    raw = json.dumps(plan, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return PLAN_PREFIX + base64.urlsafe_b64encode(raw).decode("ascii")


def decode_plan(value: str) -> dict[str, Any]:
    value = (value or "").strip()
    if value.startswith(PLAN_PREFIX):
        payload = value[len(PLAN_PREFIX):]
        return json.loads(base64.urlsafe_b64decode(payload.encode("ascii")).decode("utf-8"))

    return {
        "source_format_id": value,
        "original": {"mode": "single", "container": "", "selector": value or "best"},
        "compatible": {"mode": "single", "container": "", "selector": value or "best"},
    }


def _make_plan(original: dict[str, Any], compatible: dict[str, Any], height: int) -> str:
    original_mode, original_container, original_selector = _selector_for(original)
    compatible_mode, compatible_container, compatible_selector = _selector_for(compatible)

    if not compatible_selector:
        compatible_mode, compatible_container, compatible_selector = _height_selector(height, compatible=True)

    return encode_plan(
        {
            "source_format_id": _format_id(original),
            "height": height,
            "original": {
                "mode": original_mode,
                "container": original_container,
                "selector": original_selector,
            },
            "compatible": {
                "mode": compatible_mode,
                "container": compatible_container,
                "selector": compatible_selector,
            },
        }
    )


def _compatible_candidate(same_height: list[dict[str, Any]], has_m4a: bool) -> dict[str, Any] | None:
    progressive_h264_mp4 = [
        item for item in same_height
        if is_progressive(item) and _ext(item) == "mp4" and is_h264(item)
    ]
    if progressive_h264_mp4:
        return _pick_best(progressive_h264_mp4, compatible=True)

    dash_h264_mp4 = [
        item for item in same_height
        if not is_progressive(item) and _ext(item) == "mp4" and is_h264(item)
    ]
    if dash_h264_mp4 and has_m4a:
        return _pick_best(dash_h264_mp4, compatible=True)

    progressive_mp4 = [
        item for item in same_height
        if is_progressive(item) and _ext(item) == "mp4" and not is_av1(item)
    ]
    if progressive_mp4:
        return _pick_best(progressive_mp4, compatible=True)

    dash_mp4 = [
        item for item in same_height
        if not is_progressive(item) and _ext(item) == "mp4" and not is_av1(item)
    ]
    if dash_mp4 and has_m4a:
        return _pick_best(dash_mp4, compatible=True)

    non_av1 = [item for item in same_height if not is_av1(item)]
    return _pick_best(non_av1, compatible=True)


def _original_candidate(same_height: list[dict[str, Any]], *, prefer_compatible: bool) -> dict[str, Any] | None:
    progressive = [item for item in same_height if is_progressive(item)]
    if prefer_compatible:
        mp4_progressive = [item for item in progressive if _ext(item) == "mp4" and not is_av1(item)]
        if mp4_progressive:
            return _pick_best(mp4_progressive, compatible=True)

    if progressive:
        return _pick_best(progressive, compatible=prefer_compatible)
    return _pick_best(same_height, compatible=prefer_compatible)


def build_quality_options(raw: dict[str, Any]) -> list[FormatOption]:
    formats = raw.get("formats", []) or []
    video_formats = [item for item in formats if is_video(item) and _height(item) is not None]
    heights = sorted({_height(item) for item in video_formats if _height(item) is not None}, reverse=True)
    has_m4a = _has_m4a_audio(formats)
    prefer_compatible = is_facebook(raw)
    options: list[FormatOption] = []

    for height in heights:
        same_height = [item for item in video_formats if _height(item) == height]
        original = _original_candidate(same_height, prefer_compatible=prefer_compatible)
        compatible = _compatible_candidate(same_height, has_m4a) or original
        if not original or not compatible:
            continue

        original_mode, original_container, _selector = _selector_for(original)
        compatibility = "good" if is_h264(compatible) and (is_progressive(compatible) or has_m4a) else "variable"
        container = original_container or _ext(original) or "mp4"
        fps = _fps(original)
        codec = codec_name(original)
        parts = [f"{height}p"]
        quality_name = _quality_name(height)
        if quality_name:
            parts.append(quality_name)
        if fps >= 50:
            parts.append(f"{fps} fps")
        if _dynamic_range(original):
            parts.append(_dynamic_range(original))
        parts.append(codec)
        parts.append(container.upper())

        note_parts = []
        note_parts.append("Audio incluido" if original_mode == "single" else "Audio unido")
        if compatibility == "variable":
            note_parts.append("compatibilidad variable")

        options.append(
            FormatOption(
                plan=_make_plan(original, compatible, height),
                label=" · ".join(parts),
                resolution=f"{height}p",
                note=" · ".join(note_parts),
                height=height,
                fps=fps,
                ext=container,
                codec=codec,
                filesize=_filesize(original),
                filesize_text=format_bytes(_filesize(original)),
                compatibility=compatibility,
            )
        )

    return options
