from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

PLAN_SEPARATOR = "|||"


def resolve_executable(name: str) -> str:
    path = shutil.which(name)
    if not path:
        raise RuntimeError(f"{name} no está instalado o no está en el PATH")
    return str(Path(path).resolve())


def ensure_output_folder(folder: str) -> str:
    folder_path = Path(folder).expanduser().resolve()
    folder_path.mkdir(parents=True, exist_ok=True)
    return str(folder_path)


def _safe_int(value: Any) -> int | None:
    try:
        if value in (None, "", "none"):
            return None
        return int(value)
    except Exception:
        return None


def _safe_float(value: Any) -> float | None:
    try:
        if value in (None, "", "none"):
            return None
        return float(value)
    except Exception:
        return None


def _format_duration(seconds: Any) -> str:
    seconds = _safe_int(seconds)
    if not seconds:
        return "—"

    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60

    if h > 0:
        return f"{h}:{m:02}:{s:02}"
    return f"{m}:{s:02}"


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


def _filesize_of(item: dict[str, Any]) -> int | None:
    return _safe_int(item.get("filesize")) or _safe_int(item.get("filesize_approx"))


def _video_variant_score(item: dict[str, Any]) -> tuple:
    fps = _safe_int(item.get("fps")) or 0
    tbr = _safe_float(item.get("tbr")) or 0.0
    ext = (item.get("ext") or "").lower()
    dynamic_range = str(item.get("dynamic_range") or "").upper()

    hdr_bonus = 1 if dynamic_range not in ("", "SDR", "UNKNOWN", "NONE") else 0
    ext_bonus = 1 if ext == "mp4" else 0

    return (fps, hdr_bonus, tbr, ext_bonus)


def _is_video(item: dict[str, Any]) -> bool:
    return (item.get("vcodec") or "") != "none"


def _is_audio_only(item: dict[str, Any]) -> bool:
    return (item.get("vcodec") or "") == "none"


def _is_progressive(item: dict[str, Any]) -> bool:
    return (item.get("vcodec") or "") != "none" and (item.get("acodec") or "") != "none"


def _height_of(item: dict[str, Any]) -> int | None:
    return _safe_int(item.get("height"))


def _build_mp4_dash_selector(height: int) -> str:
    return (
        f"bestvideo[height={height}][ext=mp4]+bestaudio[ext=m4a]/"
        f"bestvideo*[height={height}][ext=mp4]+bestaudio[ext=m4a]/"
        f"best[height={height}][ext=mp4]/"
        f"bestvideo[height<={height}][ext=mp4]+bestaudio[ext=m4a]/"
        f"bestvideo*[height<={height}][ext=mp4]+bestaudio[ext=m4a]/"
        f"best[height<={height}][ext=mp4]/best"
    )


def _build_general_dash_selector(height: int) -> str:
    return (
        f"bestvideo[height={height}]+bestaudio/"
        f"bestvideo*[height={height}]+bestaudio/"
        f"best[height={height}]/"
        f"bestvideo[height<={height}]+bestaudio/"
        f"bestvideo*[height<={height}]+bestaudio/"
        f"best[height<={height}]/best"
    )


def _encode_plan(mode: str, container: str, selector: str) -> str:
    return f"{mode}{PLAN_SEPARATOR}{container}{PLAN_SEPARATOR}{selector}"


def _decode_plan(value: str) -> tuple[str, str, str]:
    if PLAN_SEPARATOR in value:
        parts = value.split(PLAN_SEPARATOR, 2)
        if len(parts) == 3:
            return parts[0], parts[1], parts[2]

    # Compatibilidad con formatos viejos:
    # no forzar merge ni mp4
    return "single", "", value


def _pick_best(items: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not items:
        return None
    return sorted(items, key=_video_variant_score, reverse=True)[0]


def _build_video_quality_options(raw_formats: list[dict[str, Any]]) -> list[dict[str, Any]]:
    heights = sorted(
        {
            h for h in (_height_of(item) for item in raw_formats if _is_video(item))
            if h is not None
        },
        reverse=True,
    )

    audio_m4a_exists = any(
        _is_audio_only(item) and (item.get("ext") or "").lower() in {"m4a", "mp4"}
        for item in raw_formats
    )

    qualities: list[dict[str, Any]] = []

    for height in heights:
        same_height = [item for item in raw_formats if _height_of(item) == height and _is_video(item)]

        progressive_mp4 = [
            item for item in same_height
            if _is_progressive(item) and (item.get("ext") or "").lower() == "mp4"
        ]
        progressive_any = [item for item in same_height if _is_progressive(item)]
        dash_mp4_video = [
            item for item in same_height
            if not _is_progressive(item) and (item.get("ext") or "").lower() == "mp4"
        ]

        chosen_item: dict[str, Any] | None = None
        mode = "merge"
        container = "mkv"
        selector = _build_general_dash_selector(height)
        note = "Audio unido"

        # 1) Preferimos progresivo MP4: una sola transferencia y reproducción simple
        best_progressive_mp4 = _pick_best(progressive_mp4)
        if best_progressive_mp4 is not None:
            chosen_item = best_progressive_mp4
            mode = "single"
            container = "mp4"
            selector = str(best_progressive_mp4.get("format_id", "best"))
            note = "Audio incluido"

        # 2) Si no, intentamos MP4 + M4A para fusionar a MP4 reproducible
        elif dash_mp4_video and audio_m4a_exists:
            chosen_item = _pick_best(dash_mp4_video)
            mode = "merge"
            container = "mp4"
            selector = _build_mp4_dash_selector(height)
            note = "Audio unido"

        # 3) Si no, usamos progresivo cualquiera
        else:
            best_progressive_any = _pick_best(progressive_any)
            if best_progressive_any is not None:
                chosen_item = best_progressive_any
                mode = "single"
                container = (best_progressive_any.get("ext") or "mp4").lower()
                selector = str(best_progressive_any.get("format_id", "best"))
                note = "Audio incluido"
            else:
                chosen_item = _pick_best(same_height)
                mode = "merge"
                container = "mkv"
                selector = _build_general_dash_selector(height)
                note = "Audio unido"

        if chosen_item is None:
            continue

        fps = _safe_int(chosen_item.get("fps")) or 0
        dynamic_range = str(chosen_item.get("dynamic_range") or "").upper()
        quality_name = _quality_name(height)

        label_parts = [f"{height}p"]
        if quality_name:
            label_parts.append(quality_name)
        if fps >= 50:
            label_parts.append(f"{fps} fps")
        if dynamic_range not in ("", "SDR", "UNKNOWN", "NONE"):
            label_parts.append(dynamic_range)
        label_parts.append(container.upper())

        qualities.append({
            "format_id": _encode_plan(mode, container, selector),
            "source_format_id": str(chosen_item.get("format_id", "")),
            "ext": container,
            "resolution": f"{height}p",
            "note": note,
            "label": " · ".join(label_parts),
            "height": height,
            "fps": fps,
            "kind": "video",
            "filesize": _filesize_of(chosen_item),
        })

    return qualities


def analyze_media(url: str) -> dict:
    if not url or not url.startswith(("http://", "https://")):
        raise ValueError("URL inválida")

    yt_dlp_path = resolve_executable("yt-dlp")

    result = subprocess.run(
        [yt_dlp_path, "-J", "--no-playlist", url],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "No se pudo analizar la URL")

    raw = json.loads(result.stdout)
    raw_formats = raw.get("formats", []) or []

    return {
        "title": raw.get("title", "Sin título"),
        "duration": raw.get("duration"),
        "duration_text": _format_duration(raw.get("duration")),
        "thumbnail": raw.get("thumbnail"),
        "extractor": raw.get("extractor_key") or raw.get("extractor") or "Desconocido",
        "webpage_url": raw.get("webpage_url") or url,
        "formats": _build_video_quality_options(raw_formats),
    }


def build_download_command(
    *,
    url: str,
    folder: str,
    format_id: str,
    extract_audio: bool,
    audio_format: str,
) -> tuple[str, list[str]]:
    if not url:
        raise ValueError("La URL está vacía")

    output_folder = ensure_output_folder(folder)
    yt_dlp_path = resolve_executable("yt-dlp")
    ffmpeg_path = resolve_executable("ffmpeg")

    progress_template = (
        "PROGRESS:"
        "%(info.ext|NA)s|"
        "%(info.format_id|NA)s|"
        "%(progress.status|NA)s|"
        "%(progress.downloaded_bytes|NA)s|"
        "%(progress.total_bytes|NA)s|"
        "%(progress.total_bytes_estimate|NA)s|"
        "%(progress.speed|NA)s|"
        "%(progress.eta|NA)s"
    )

    args = [
        "--newline",
        "--progress",
        "--progress-delta", "0.3",
        "--progress-template", f"download:{progress_template}",
        "--ffmpeg-location", str(Path(ffmpeg_path).parent),
        "--no-playlist",
        "-P", output_folder,
        "-o", "%(title)s.%(ext)s",
    ]

    if extract_audio:
        args += ["-x", "--audio-format", audio_format or "mp3"]
    else:
        if not format_id:
            raise ValueError("Debes seleccionar una calidad de video")

        mode, container, selector = _decode_plan(format_id)

        if mode == "single":
            args += ["-f", selector]
        else:
            args += ["-f", selector]
            if container:
                args += ["--merge-output-format", container]

    args.append(url)
    return yt_dlp_path, args