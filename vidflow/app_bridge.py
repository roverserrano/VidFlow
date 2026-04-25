from __future__ import annotations

import json
from uuid import uuid4

from PySide6.QtCore import QObject, QMetaObject, QThread, Qt, QUrl, Signal, Slot
from PySide6.QtGui import QDesktopServices

from vidflow.models import CompatibilityMode, DownloadKind, DownloadRequest, DownloadStatus, DownloadUpdate
from vidflow.workers.analysis import AnalysisWorker
from vidflow.workers.download import DownloadWorker


class AppBridge(QObject):
    analysisStarted = Signal()
    analysisFinished = Signal(str)
    analysisError = Signal(str)

    downloadAdded = Signal(str)
    downloadUpdated = Signal(str)

    toastRequested = Signal(str, str)

    def __init__(self):
        super().__init__()
        self._analysis_thread: QThread | None = None
        self._analysis_worker: AnalysisWorker | None = None
        self._download_threads: dict[str, QThread] = {}
        self._download_workers: dict[str, DownloadWorker] = {}

    @Slot(str)
    def analyzeUrl(self, url: str):
        url = (url or "").strip()
        if not url:
            self.analysisError.emit("Debes pegar una URL")
            self.toastRequested.emit("error", "Debes pegar una URL")
            return

        if self._analysis_thread and self._analysis_thread.isRunning():
            self.toastRequested.emit("info", "Ya hay un análisis en curso")
            return

        self.analysisStarted.emit()

        thread = QThread(self)
        worker = AnalysisWorker(url)
        worker.moveToThread(thread)

        thread.started.connect(worker.run)
        worker.finished.connect(self.analysisFinished)
        worker.failed.connect(self.analysisError)
        worker.finished.connect(lambda _payload: self.toastRequested.emit("success", "URL analizada correctamente"))
        worker.failed.connect(lambda message: self.toastRequested.emit("error", message))
        worker.finished.connect(thread.quit)
        worker.failed.connect(thread.quit)
        thread.finished.connect(worker.deleteLater)
        thread.finished.connect(self._clear_analysis_refs)
        thread.finished.connect(thread.deleteLater)

        self._analysis_thread = thread
        self._analysis_worker = worker
        thread.start()

    def _clear_analysis_refs(self):
        self._analysis_thread = None
        self._analysis_worker = None

    @Slot(str, str, str, bool, str, str, str)
    def downloadMedia(
        self,
        url: str,
        folder: str,
        format_plan: str,
        extract_audio: bool,
        audio_format: str,
        title: str,
        compatibility_mode: str,
    ):
        url = (url or "").strip()
        folder = (folder or "").strip()
        format_plan = (format_plan or "").strip()
        audio_format = (audio_format or "mp3").strip().lower()
        title = (title or "Sin título").strip()
        compatibility_mode = (compatibility_mode or CompatibilityMode.COMPATIBLE).strip().lower()

        if not url:
            self.toastRequested.emit("error", "La URL está vacía")
            return
        if not folder:
            self.toastRequested.emit("error", "Debes seleccionar una carpeta")
            return
        if not extract_audio and not format_plan:
            self.toastRequested.emit("error", "Debes seleccionar una calidad de video")
            return

        try:
            compatibility = CompatibilityMode(compatibility_mode)
        except ValueError:
            compatibility = CompatibilityMode.COMPATIBLE

        request = DownloadRequest(
            job_id=str(uuid4()),
            title=title,
            url=url,
            folder=folder,
            format_plan=format_plan,
            kind=DownloadKind.AUDIO if extract_audio else DownloadKind.VIDEO,
            audio_format=audio_format or "mp3",
            compatibility_mode=compatibility,
        )

        queued = DownloadUpdate(
            job_id=request.job_id,
            title=request.title,
            folder=request.folder,
            status=DownloadStatus.QUEUED,
            percent=-1.0,
            message="En cola...",
        )
        self.downloadAdded.emit(json.dumps(queued.to_dict(), ensure_ascii=False))

        thread = QThread(self)
        worker = DownloadWorker(request)
        worker.moveToThread(thread)

        thread.started.connect(worker.start)
        worker.progress.connect(self.downloadUpdated)
        worker.finished.connect(self.downloadUpdated)
        worker.finished.connect(self._handle_terminal_download)
        worker.finished.connect(thread.quit)
        thread.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(lambda job_id=request.job_id: self._cleanup_download(job_id))

        self._download_threads[request.job_id] = thread
        self._download_workers[request.job_id] = worker

        thread.start()
        self.toastRequested.emit("info", f"Descarga añadida: {title}")

    def _handle_terminal_download(self, payload: str):
        try:
            data = json.loads(payload)
        except Exception:
            return

        status = data.get("status")
        title = data.get("title") or "Descarga"
        if status == DownloadStatus.COMPLETED:
            self.toastRequested.emit("success", f"Completado: {title}")
        elif status == DownloadStatus.CANCELED:
            self.toastRequested.emit("info", f"Cancelado: {title}")
        elif status == DownloadStatus.ERROR:
            self.toastRequested.emit("error", data.get("message") or "La descarga falló")

    def _cleanup_download(self, job_id: str):
        self._download_threads.pop(job_id, None)
        self._download_workers.pop(job_id, None)

    @Slot(str)
    def cancelDownload(self, job_id: str):
        worker = self._download_workers.get(job_id)
        if not worker:
            return

        QMetaObject.invokeMethod(
            worker,
            "cancel",
            Qt.ConnectionType.QueuedConnection,
        )

    @Slot(str)
    def openFolder(self, folder: str):
        if not folder:
            self.toastRequested.emit("error", "La carpeta no es válida")
            return

        ok = QDesktopServices.openUrl(QUrl.fromLocalFile(folder))
        if not ok:
            self.toastRequested.emit("error", "No se pudo abrir la carpeta")
