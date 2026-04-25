from __future__ import annotations

import json
import subprocess
from pathlib import Path

from vidflow.core.system import ensure_output_folder, format_duration, resolve_executable
from vidflow.models import CompatibilityMode, DownloadKind, DownloadRequest, MediaInfo
from vidflow.services.format_selector import build_quality_options, decode_plan, extractor_text


def analyze_media(url: str) -> MediaInfo:
    url = (url or "").strip()
    if not url.startswith(("http://", "https://")):
        raise ValueError("URL inválida")

    yt_dlp_path = resolve_executable("yt-dlp", env_var="VIDFLOW_YTDLP")
    result = subprocess.run(
        [yt_dlp_path, "-J", "--no-playlist", url],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )

    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip() or "No se pudo analizar la URL"
        raise RuntimeError(message)

    raw = json.loads(result.stdout)
    return MediaInfo(
        title=raw.get("title") or "Sin título",
        duration=raw.get("duration"),
        duration_text=format_duration(raw.get("duration")),
        thumbnail=raw.get("thumbnail") or "",
        extractor=extractor_text(raw) or "Desconocido",
        webpage_url=raw.get("webpage_url") or url,
        formats=build_quality_options(raw),
    )


def _progress_template() -> str:
    return (
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


def _base_args(output_folder: str, ffmpeg_path: str) -> list[str]:
    return [
        "--newline",
        "--progress",
        "--progress-delta",
        "0.3",
        "--progress-template",
        f"download:{_progress_template()}",
        "--ffmpeg-location",
        str(Path(ffmpeg_path).parent),
        "--no-playlist",
        "--windows-filenames",
        "-P",
        output_folder,
        "-o",
        "%(title).200B [%(id)s].%(ext)s",
    ]


def _selected_video_plan(request: DownloadRequest) -> dict:
    plan = decode_plan(request.format_plan)
    mode_key = (
        "original"
        if request.compatibility_mode == CompatibilityMode.ORIGINAL
        else "compatible"
    )
    selected = plan.get(mode_key) or plan.get("compatible") or plan.get("original") or {}
    return {
        "mode": selected.get("mode") or "single",
        "container": selected.get("container") or "",
        "selector": selected.get("selector") or "best",
    }


def build_download_command(request: DownloadRequest) -> tuple[str, list[str]]:
    if not request.url:
        raise ValueError("La URL está vacía")

    output_folder = ensure_output_folder(request.folder)
    yt_dlp_path = resolve_executable("yt-dlp", env_var="VIDFLOW_YTDLP")
    ffmpeg_path = resolve_executable("ffmpeg", env_var="VIDFLOW_FFMPEG")
    args = _base_args(output_folder, ffmpeg_path)

    if request.kind == DownloadKind.AUDIO:
        args += [
            "-x",
            "--audio-format",
            request.audio_format or "mp3",
            "--audio-quality",
            "0",
        ]
    else:
        if not request.format_plan:
            raise ValueError("Debes seleccionar una calidad de video")

        selected = _selected_video_plan(request)
        args += ["-f", selected["selector"]]

        if selected["mode"] == "merge" and selected["container"]:
            args += ["--merge-output-format", selected["container"]]

        if request.compatibility_mode == CompatibilityMode.COMPATIBLE:
            args += ["--remux-video", "mp4"]

    args.append(request.url)
    return yt_dlp_path, args
