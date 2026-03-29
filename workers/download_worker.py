from __future__ import annotations

import json
from typing import Optional

from PySide6.QtCore import QObject, QProcess, Signal, Slot

from services.ytdlp_service import build_download_command


def _to_int(value: str) -> Optional[int]:
    try:
        if value in ("", "NA", "None", "null"):
            return None
        return int(float(value))
    except Exception:
        return None


def _to_float(value: str) -> Optional[float]:
    try:
        if value in ("", "NA", "None", "null"):
            return None
        return float(value)
    except Exception:
        return None


def _format_bytes(value: Optional[int]) -> str:
    if value is None:
        return "—"

    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(value)
    unit = 0

    while size >= 1024 and unit < len(units) - 1:
        size /= 1024
        unit += 1

    if unit == 0:
        return f"{int(size)} {units[unit]}"
    return f"{size:.1f} {units[unit]}"


def _format_speed(value: Optional[float]) -> str:
    if value is None:
        return "—"
    return f"{_format_bytes(int(value))}/s"


def _format_eta(value: Optional[float]) -> str:
    if value is None:
        return "—"

    total = int(value)
    h = total // 3600
    m = (total % 3600) // 60
    s = total % 60

    if h > 0:
        return f"{h}:{m:02}:{s:02}"
    return f"{m}:{s:02}"


class DownloadWorker(QObject):
    progress = Signal(str)
    finished = Signal(str)

    def __init__(
        self,
        *,
        job_id: str,
        title: str,
        url: str,
        folder: str,
        format_id: str,
        extract_audio: bool,
        audio_format: str,
    ):
        super().__init__()
        self.job_id = job_id
        self.title = title or "Sin título"
        self.url = url
        self.folder = folder
        self.format_id = format_id
        self.extract_audio = extract_audio
        self.audio_format = audio_format or "mp3"

        self.process: Optional[QProcess] = None
        self._buffer = ""
        self._canceled = False
        self._terminal_emitted = False
        self._last_error_line = ""
        self._last_percent = -1.0

    def _payload(
        self,
        *,
        status: str,
        percent: float = -1.0,
        speed_text: str = "—",
        eta_text: str = "—",
        bytes_text: str = "—",
        message: str = "",
    ) -> dict:
        return {
            "job_id": self.job_id,
            "title": self.title,
            "folder": self.folder,
            "status": status,
            "percent": percent,
            "speed_text": speed_text,
            "eta_text": eta_text,
            "bytes_text": bytes_text,
            "message": message,
        }

    def _emit_progress(self, payload: dict):
        self.progress.emit(json.dumps(payload, ensure_ascii=False))

    def _emit_finished(self, payload: dict):
        if self._terminal_emitted:
            return
        self._terminal_emitted = True
        self.finished.emit(json.dumps(payload, ensure_ascii=False))

    @Slot()
    def start(self):
        try:
            yt_dlp_path, args = build_download_command(
                url=self.url,
                folder=self.folder,
                format_id=self.format_id,
                extract_audio=self.extract_audio,
                audio_format=self.audio_format,
            )
        except Exception as e:
            self._emit_finished(
                self._payload(
                    status="error",
                    percent=self._last_percent,
                    message=str(e),
                )
            )
            return

        self.process = QProcess(self)
        self.process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self.process.setProgram(yt_dlp_path)
        self.process.setArguments(args)

        self.process.started.connect(self._on_started)
        self.process.readyReadStandardOutput.connect(self._on_ready_read)
        self.process.errorOccurred.connect(self._on_process_error)
        self.process.finished.connect(self._on_process_finished)

        self.process.start()

    def _on_started(self):
        # El bridge ya agregó la fila "En cola..."
        pass

    @Slot()
    def cancel(self):
        self._canceled = True

        if self.process is None:
            self._emit_finished(
                self._payload(
                    status="canceled",
                    percent=self._last_percent,
                    message="Descarga cancelada",
                )
            )
            return

        if self.process.state() != QProcess.ProcessState.NotRunning:
            self.process.terminate()
            if not self.process.waitForFinished(2000):
                self.process.kill()

    def _on_ready_read(self):
        if not self.process:
            return

        chunk = bytes(self.process.readAllStandardOutput()).decode("utf-8", errors="replace")
        self._buffer += chunk

        while "\n" in self._buffer:
            line, self._buffer = self._buffer.split("\n", 1)
            self._handle_line(line.strip())

    def _handle_line(self, line: str):
        if not line:
            return

        if "ERROR:" in line:
            self._last_error_line = line.strip()

        if not line.startswith("PROGRESS:"):
            if (
                "Merging formats into" in line
                or "Fixing MPEG-TS in MP4 container" in line
                or "Deleting original file" in line
            ):
                self._emit_progress(
                    self._payload(
                        status="processing",
                        percent=100.0,
                        speed_text="—",
                        eta_text="—",
                        bytes_text="—",
                        message="Procesando archivo...",
                    )
                )
            return

        raw = line.replace("PROGRESS:", "", 1)
        parts = raw.split("|")

        if len(parts) != 8:
            return

        _ext_raw, _info_format_raw, status_raw, downloaded_raw, total_raw, total_est_raw, speed_raw, eta_raw = parts

        downloaded = _to_int(downloaded_raw)
        total = _to_int(total_raw) or _to_int(total_est_raw)
        speed = _to_float(speed_raw)
        eta = _to_float(eta_raw)

        percent = -1.0
        if downloaded is not None and total:
            percent = round((downloaded / total) * 100, 2)

        self._last_percent = percent if percent >= 0 else self._last_percent

        speed_text = _format_speed(speed)
        eta_text = _format_eta(eta)
        bytes_text = (
            f"{_format_bytes(downloaded)} / {_format_bytes(total)}"
            if downloaded is not None and total is not None
            else _format_bytes(downloaded)
        )

        if status_raw == "finished":
            self._emit_progress(
                self._payload(
                    status="processing",
                    percent=100.0,
                    speed_text="—",
                    eta_text="—",
                    bytes_text=bytes_text,
                    message="Procesando archivo...",
                )
            )
            return

        self._emit_progress(
            self._payload(
                status="downloading",
                percent=percent,
                speed_text=speed_text,
                eta_text=eta_text,
                bytes_text=bytes_text,
                message="Descargando...",
            )
        )

    def _on_process_error(self, _error):
        if self._terminal_emitted:
            return

        message = "No se pudo iniciar el proceso de descarga"
        if self.process:
            message = self.process.errorString() or message

        if self._canceled:
            self._emit_finished(
                self._payload(
                    status="canceled",
                    percent=self._last_percent,
                    message="Descarga cancelada",
                )
            )
            return

        self._emit_finished(
            self._payload(
                status="error",
                percent=self._last_percent,
                message=message,
            )
        )

    def _on_process_finished(self, exit_code, _exit_status):
        if self._terminal_emitted:
            return

        if self._canceled:
            self._emit_finished(
                self._payload(
                    status="canceled",
                    percent=self._last_percent,
                    message="Descarga cancelada",
                )
            )
            return

        if exit_code == 0:
            self._emit_finished(
                self._payload(
                    status="completed",
                    percent=100.0,
                    message="Descarga completada",
                )
            )
            return

        message = self._last_error_line or f"La descarga falló (código {exit_code})"
        if message.startswith("ERROR:"):
            message = message.replace("ERROR:", "", 1).strip()

        self._emit_finished(
            self._payload(
                status="error",
                percent=self._last_percent,
                message=message,
            )
        )