from __future__ import annotations

import json
from typing import Optional

from PySide6.QtCore import QObject, QProcess, Signal, Slot

from vidflow.core.system import format_bytes, format_eta, format_speed
from vidflow.models import DownloadRequest, DownloadStatus, DownloadUpdate
from vidflow.services.ytdlp import build_download_command


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


class DownloadWorker(QObject):
    progress = Signal(str)
    finished = Signal(str)

    def __init__(self, request: DownloadRequest):
        super().__init__()
        self.request = request
        self.process: QProcess | None = None
        self._buffer = ""
        self._canceled = False
        self._terminal_emitted = False
        self._last_error_line = ""
        self._last_percent = -1.0
        self._processing_emitted = False

    def _update(
        self,
        status: DownloadStatus,
        *,
        percent: float | None = None,
        speed_text: str = "—",
        eta_text: str = "—",
        bytes_text: str = "—",
        message: str = "",
    ) -> DownloadUpdate:
        return DownloadUpdate(
            job_id=self.request.job_id,
            title=self.request.title,
            folder=self.request.folder,
            status=status,
            percent=self._last_percent if percent is None else percent,
            speed_text=speed_text,
            eta_text=eta_text,
            bytes_text=bytes_text,
            message=message,
        )

    def _emit_progress(self, update: DownloadUpdate):
        self.progress.emit(json.dumps(update.to_dict(), ensure_ascii=False))

    def _emit_finished(self, update: DownloadUpdate):
        if self._terminal_emitted:
            return
        self._terminal_emitted = True
        self.finished.emit(json.dumps(update.to_dict(), ensure_ascii=False))

    @Slot()
    def start(self):
        try:
            program, args = build_download_command(self.request)
        except Exception as exc:
            self._emit_finished(
                self._update(
                    DownloadStatus.ERROR,
                    percent=self._last_percent,
                    message=str(exc),
                )
            )
            return

        self.process = QProcess(self)
        self.process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self.process.setProgram(program)
        self.process.setArguments(args)
        self.process.started.connect(self._on_started)
        self.process.readyReadStandardOutput.connect(self._on_ready_read)
        self.process.errorOccurred.connect(self._on_process_error)
        self.process.finished.connect(self._on_process_finished)
        self.process.start()

    def _on_started(self):
        self._emit_progress(
            self._update(
                DownloadStatus.PREPARING,
                percent=-1.0,
                message="Preparando descarga...",
            )
        )

    @Slot()
    def cancel(self):
        self._canceled = True

        if self.process is None:
            self._emit_finished(
                self._update(
                    DownloadStatus.CANCELED,
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

    def _emit_processing(self, message: str):
        if self._processing_emitted:
            return

        self._processing_emitted = True
        percent = max(self._last_percent, 99.0)
        self._last_percent = percent
        self._emit_progress(
            self._update(
                DownloadStatus.PROCESSING,
                percent=percent,
                message=message,
            )
        )

    def _handle_line(self, line: str):
        if not line:
            return

        if "ERROR:" in line:
            self._last_error_line = line.strip()

        if not line.startswith("PROGRESS:"):
            self._handle_regular_line(line)
            return

        raw = line.replace("PROGRESS:", "", 1)
        parts = raw.split("|")
        if len(parts) != 8:
            return

        _ext_raw, _format_raw, status_raw, downloaded_raw, total_raw, total_est_raw, speed_raw, eta_raw = parts
        if status_raw == "finished":
            self._last_percent = max(self._last_percent, 99.0)
            return

        downloaded = _to_int(downloaded_raw)
        total = _to_int(total_raw) or _to_int(total_est_raw)
        speed = _to_float(speed_raw)
        eta = _to_float(eta_raw)

        percent = -1.0
        if downloaded is not None and total:
            percent = round((downloaded / total) * 100, 2)
            percent = min(percent, 99.0)
            if self._last_percent >= 0:
                percent = max(percent, self._last_percent)

        if percent >= 0:
            self._last_percent = percent

        bytes_text = (
            f"{format_bytes(downloaded)} / {format_bytes(total)}"
            if downloaded is not None and total is not None
            else format_bytes(downloaded)
        )

        self._processing_emitted = False
        self._emit_progress(
            self._update(
                DownloadStatus.DOWNLOADING,
                percent=percent,
                speed_text=format_speed(speed),
                eta_text=format_eta(eta),
                bytes_text=bytes_text,
                message="Descargando...",
            )
        )

    def _handle_regular_line(self, line: str):
        processing_markers = {
            "Merging formats into": "Fusionando audio y video...",
            "Extracting audio": "Extrayendo audio...",
            "Destination:": "Preparando archivo...",
            "Deleting original file": "Limpiando archivos temporales...",
            "Fixing MPEG-TS in MP4 container": "Ajustando contenedor MP4...",
            "Post-process file": "Procesando archivo...",
            "Remuxing video from": "Optimizando contenedor...",
        }

        for marker, message in processing_markers.items():
            if marker in line and marker != "Destination:":
                self._emit_processing(message)
                return

    def _on_process_error(self, _error):
        if self._terminal_emitted:
            return

        if self._canceled:
            self._emit_finished(
                self._update(
                    DownloadStatus.CANCELED,
                    percent=self._last_percent,
                    message="Descarga cancelada",
                )
            )
            return

        message = "No se pudo iniciar el proceso de descarga"
        if self.process:
            message = self.process.errorString() or message

        self._emit_finished(
            self._update(
                DownloadStatus.ERROR,
                percent=self._last_percent,
                message=message,
            )
        )

    def _on_process_finished(self, exit_code, _exit_status):
        if self._terminal_emitted:
            return

        if self._canceled:
            self._emit_finished(
                self._update(
                    DownloadStatus.CANCELED,
                    percent=self._last_percent,
                    message="Descarga cancelada",
                )
            )
            return

        if exit_code == 0:
            self._emit_finished(
                self._update(
                    DownloadStatus.COMPLETED,
                    percent=100.0,
                    message="Descarga completada",
                )
            )
            return

        message = self._last_error_line or f"La descarga falló (código {exit_code})"
        if message.startswith("ERROR:"):
            message = message.replace("ERROR:", "", 1).strip()

        self._emit_finished(
            self._update(
                DownloadStatus.ERROR,
                percent=self._last_percent,
                message=message,
            )
        )
