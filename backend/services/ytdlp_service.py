from __future__ import annotations

import logging
import math
import re
import subprocess
from pathlib import Path
from typing import Callable

from pydantic import ValidationError

from backend.models import (
    DownloadRequest,
    DownloadResult,
    DownloadStatus,
    DownloadType,
    MediaMetadata,
    Platform,
    ProgressEvent,
)
from backend.models.errors import VidFlowError, humanize_download_error
from backend.services.ffmpeg_service import resolve_tool
from backend.services.format_selector import (
    build_quality_options,
    default_video_selector,
    progressive_video_selector,
    _tiktok_selector_for_height,
)
from backend.services.storage_service import ensure_directory, find_created_file
from backend.utils.filenames import build_download_basename
from backend.utils.formatting import format_duration, format_eta, format_speed, format_bytes

logger = logging.getLogger(__name__)


class DownloadCanceled(Exception):
    pass


ProgressCallback = Callable[[ProgressEvent], None]
CancelCheck = Callable[[], bool]


class YtDlpService:
    def _parse_requested_height(self, resolution: str | None) -> int | None:
        if not resolution:
            return None
        match = re.search(r"(\d{3,4})", str(resolution))
        if not match:
            return None
        try:
            return int(match.group(1))
        except ValueError:
            return None

    def _normalize_duration(self, value) -> int | None:
        try:
            if value in (None, "", "none"):
                return None
            seconds = float(value)
        except (TypeError, ValueError):
            return None

        if not math.isfinite(seconds) or seconds < 0:
            return None
        return int(round(seconds))

    def _ydl_class(self):
        try:
            from yt_dlp import YoutubeDL
        except Exception as exc:
            raise VidFlowError(
                "yt-dlp no esta disponible. Instala las dependencias del backend.",
                code="missing_ytdlp",
                status_code=500,
            ) from exc
        return YoutubeDL

    def analyze(self, url: str, platform: Platform) -> MediaMetadata:
        YoutubeDL = self._ydl_class()
        options = {
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
            "skip_download": True,
            "socket_timeout": 20,
        }

        try:
            with YoutubeDL(options) as ydl:
                raw = ydl.extract_info(url, download=False)
        except Exception as exc:
            raise VidFlowError(humanize_download_error(exc), code="metadata_error") from exc

        if not isinstance(raw, dict):
            raise VidFlowError("No se pudo leer la informacion del video.", code="metadata_error")

        duration = self._normalize_duration(raw.get("duration"))

        try:
            return MediaMetadata(
                title=str(raw.get("title") or "Video"),
                webpage_url=str(raw.get("webpage_url") or url),
                platform=platform,
                duration=duration,
                duration_text=format_duration(duration),
                thumbnail=str(raw.get("thumbnail") or ""),
                formats=build_quality_options(raw),
                raw={
                    "id": raw.get("id"),
                    "extractor": raw.get("extractor_key") or raw.get("extractor"),
                },
            )
        except ValidationError as exc:
            logger.exception("Metadata validation failed")
            raise VidFlowError(
                "No se pudo interpretar los metadatos del video.",
                code="metadata_parse_error",
            ) from exc

    def _run_ffmpeg(self, ffmpeg: str, arguments: list[str]) -> bool:
        command = [ffmpeg, *arguments]
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        if result.returncode != 0:
            logger.warning("ffmpeg command failed: %s", result.stderr.strip() or result.stdout.strip())
            return False
        return True

    def _ensure_facebook_playable(self, file_path: Path, ffmpeg: str | None) -> Path:
        if not ffmpeg:
            return file_path

        converted = file_path.with_name(f"{file_path.stem}.vf_fixed.mp4")
        ok = self._run_ffmpeg(
            ffmpeg,
            [
                "-y",
                "-i",
                str(file_path),
                "-c:v",
                "libx264",
                "-preset",
                "veryfast",
                "-crf",
                "18",
                "-c:a",
                "aac",
                "-b:a",
                "192k",
                "-movflags",
                "+faststart",
                str(converted),
            ],
        )
        if ok and converted.exists():
            file_path.unlink(missing_ok=True)
            final_mp4 = file_path.with_suffix(".mp4")
            if final_mp4.exists():
                final_mp4.unlink(missing_ok=True)
            converted.replace(final_mp4)
            return final_mp4

        converted.unlink(missing_ok=True)
        fallback = file_path.with_suffix(".mkv")
        ok = self._run_ffmpeg(
            ffmpeg,
            [
                "-y",
                "-i",
                str(file_path),
                "-c",
                "copy",
                str(fallback),
            ],
        )
        if ok and fallback.exists():
            file_path.unlink(missing_ok=True)
            return fallback
        return file_path

    def _ensure_h264_aac_mp4(self, file_path: Path, ffmpeg: str | None) -> Path:
        if not ffmpeg:
            return file_path

        converted = file_path.with_name(f"{file_path.stem}.vf_compat.mp4")
        ok = self._run_ffmpeg(
            ffmpeg,
            [
                "-y",
                "-i",
                str(file_path),
                "-c:v",
                "libx264",
                "-preset",
                "veryfast",
                "-crf",
                "20",
                "-c:a",
                "aac",
                "-b:a",
                "192k",
                "-movflags",
                "+faststart",
                str(converted),
            ],
        )
        if ok and converted.exists():
            file_path.unlink(missing_ok=True)
            final_mp4 = file_path.with_suffix(".mp4")
            if final_mp4.exists():
                final_mp4.unlink(missing_ok=True)
            converted.replace(final_mp4)
            return final_mp4
        converted.unlink(missing_ok=True)
        return file_path

    def download(
        self,
        request: DownloadRequest,
        *,
        platform: Platform,
        job_id: str,
        emit: ProgressCallback,
        should_cancel: CancelCheck,
    ) -> DownloadResult:
        YoutubeDL = self._ydl_class()
        output_dir = ensure_directory(request.output_dir)
        resolution = request.resolution or ("audio" if request.download_type == DownloadType.AUDIO else "best")
        basename = build_download_basename(request.title, resolution)
        output_template = str(output_dir / f"{basename}.%(ext)s")
        ffmpeg = resolve_tool("ffmpeg", "VIDFLOW_FFMPEG")

        emit(
            ProgressEvent(
                job_id=job_id,
                status=DownloadStatus.PREPARING,
                percent=0,
                message="Preparando descarga...",
            )
        )

        def progress_hook(data: dict) -> None:
            if should_cancel():
                raise DownloadCanceled()

            status = data.get("status")
            if status == "downloading":
                total = data.get("total_bytes") or data.get("total_bytes_estimate")
                downloaded = data.get("downloaded_bytes")
                percent = None
                if total and downloaded:
                    percent = min(round((downloaded / total) * 100, 2), 99.0)

                emit(
                    ProgressEvent(
                        job_id=job_id,
                        status=DownloadStatus.DOWNLOADING,
                        percent=percent,
                        speed=format_speed(data.get("speed")),
                        eta=format_eta(data.get("eta")),
                        downloaded=(
                            f"{format_bytes(downloaded)} / {format_bytes(total)}"
                            if downloaded and total
                            else format_bytes(downloaded)
                        ),
                        message="Descargando...",
                    )
                )
            elif status == "finished":
                emit(
                    ProgressEvent(
                        job_id=job_id,
                        status=DownloadStatus.PROCESSING,
                        percent=99,
                        message="Procesando archivo...",
                    )
                )

        options = self._download_options(
            request=request,
            platform=platform,
            output_template=output_template,
            ffmpeg=ffmpeg,
            progress_hook=progress_hook,
        )

        try:
            with YoutubeDL(options) as ydl:
                ydl.download([request.url])
        except DownloadCanceled:
            raise
        except Exception as exc:
            logger.exception("Download failed")
            raise VidFlowError(humanize_download_error(exc), code="download_error") from exc

        created = find_created_file(output_dir, basename)
        if not created:
            raise VidFlowError("La descarga termino, pero no se encontro el archivo final.", code="missing_output")

        if platform == Platform.FACEBOOK and request.download_type == DownloadType.VIDEO:
            emit(
                ProgressEvent(
                    job_id=job_id,
                    status=DownloadStatus.PROCESSING,
                    percent=99,
                    message="Optimizando video de Facebook para compatibilidad...",
                )
            )
            created = self._ensure_facebook_playable(created, ffmpeg)
        elif platform == Platform.TIKTOK and request.download_type == DownloadType.VIDEO:
            emit(
                ProgressEvent(
                    job_id=job_id,
                    status=DownloadStatus.PROCESSING,
                    percent=99,
                    message="Optimizando video para maxima compatibilidad...",
                )
            )
            created = self._ensure_h264_aac_mp4(created, ffmpeg)

        result = DownloadResult(
            job_id=job_id,
            title=request.title,
            platform=platform,
            download_type=request.download_type,
            format=created.suffix.replace(".", "").lower(),
            file_path=str(created),
            thumbnail=request.thumbnail,
        )
        emit(
            ProgressEvent(
                job_id=job_id,
                status=DownloadStatus.COMPLETED,
                percent=100,
                message="Descarga completada.",
                file_path=str(created),
            )
        )
        return result

    def _download_options(
        self,
        *,
        request: DownloadRequest,
        platform: Platform,
        output_template: str,
        ffmpeg: str | None,
        progress_hook: Callable[[dict], None],
    ) -> dict:
        options = {
            "outtmpl": output_template,
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
            "windowsfilenames": True,
            "progress_hooks": [progress_hook],
            "continuedl": True,
            "retries": 3,
            "fragment_retries": 3,
        }

        if ffmpeg:
            options["ffmpeg_location"] = str(Path(ffmpeg).parent)

        if request.download_type == DownloadType.AUDIO:
            codec = "vorbis" if request.audio_format.value == "ogg" else request.audio_format.value
            options.update(
                {
                    "format": "bestaudio/best",
                    "postprocessors": [
                        {
                            "key": "FFmpegExtractAudio",
                            "preferredcodec": codec,
                            "preferredquality": "192",
                        }
                    ],
                }
            )
            return options

        requested_height = self._parse_requested_height(request.resolution)
        if platform == Platform.TIKTOK:
            selector = _tiktok_selector_for_height(requested_height or 2160)
        else:
            selector = request.format_selector or default_video_selector(facebook_mode=platform == Platform.FACEBOOK)
        if not ffmpeg:
            # Without ffmpeg, merged DASH downloads fail; use progressive MP4 fallback.
            selector = _tiktok_selector_for_height(requested_height or 2160) if platform == Platform.TIKTOK else progressive_video_selector(requested_height)

        options.update(
            {
                "format": selector,
            }
        )
        if ffmpeg:
            options["merge_output_format"] = "mp4"
        return options


ytdlp_service = YtDlpService()
