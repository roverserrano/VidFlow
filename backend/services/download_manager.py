from __future__ import annotations

import json
import logging
import queue
import threading
from dataclasses import dataclass, field
from uuid import uuid4

from backend.downloader import get_downloader
from backend.models import (
    DownloadJobSnapshot,
    DownloadRequest,
    DownloadStatus,
    ProgressEvent,
)
from backend.models.errors import VidFlowError, humanize_download_error
from backend.services.history_service import history_service
from backend.services.settings_service import settings_service
from backend.utils.platform_detect import detect_platform

logger = logging.getLogger(__name__)


@dataclass
class ActiveJob:
    job_id: str
    request: DownloadRequest
    events: queue.Queue[ProgressEvent] = field(default_factory=queue.Queue)
    status: DownloadStatus = DownloadStatus.QUEUED
    percent: float | None = None
    message: str = "En cola..."
    cancel_requested: bool = False
    thread: threading.Thread | None = None


class DownloadManager:
    def __init__(self) -> None:
        self._jobs: dict[str, ActiveJob] = {}
        self._lock = threading.RLock()

    def start(self, request: DownloadRequest) -> DownloadJobSnapshot:
        platform = request.platform or detect_platform(request.url)
        request.platform = platform
        if request.output_dir is None:
            request.output_dir = settings_service.read().download_directory

        job = ActiveJob(job_id=str(uuid4()), request=request)
        with self._lock:
            self._jobs[job.job_id] = job

        self._emit(
            job,
            ProgressEvent(
                job_id=job.job_id,
                status=DownloadStatus.QUEUED,
                percent=0,
                message="En cola...",
            ),
        )

        worker = threading.Thread(target=self._run, args=(job, platform), daemon=True)
        job.thread = worker
        worker.start()
        return self.snapshot(job.job_id)

    def snapshot(self, job_id: str) -> DownloadJobSnapshot:
        job = self.get(job_id)
        return DownloadJobSnapshot(
            job_id=job.job_id,
            status=job.status,
            title=job.request.title,
            platform=job.request.platform,
            download_type=job.request.download_type,
            percent=job.percent,
            message=job.message,
        )

    def get(self, job_id: str) -> ActiveJob:
        with self._lock:
            job = self._jobs.get(job_id)
        if not job:
            raise VidFlowError("Descarga no encontrada.", code="job_not_found", status_code=404)
        return job

    def cancel(self, job_id: str) -> DownloadJobSnapshot:
        job = self.get(job_id)
        job.cancel_requested = True
        self._emit(
            job,
            ProgressEvent(
                job_id=job.job_id,
                status=DownloadStatus.CANCELED,
                percent=job.percent,
                message="Cancelando descarga...",
            ),
        )
        return self.snapshot(job_id)

    def _run(self, job: ActiveJob, platform) -> None:
        downloader = get_downloader(platform)
        try:
            result = downloader.download(
                job.request,
                job_id=job.job_id,
                emit=lambda event: self._emit(job, event),
                should_cancel=lambda: job.cancel_requested,
            )
            history_service.add(result)
        except Exception as exc:
            if job.cancel_requested:
                self._emit(
                    job,
                    ProgressEvent(
                        job_id=job.job_id,
                        status=DownloadStatus.CANCELED,
                        percent=job.percent,
                        message="Descarga cancelada.",
                    ),
                )
                return

            logger.exception("Download job failed")
            message = exc.message if isinstance(exc, VidFlowError) else humanize_download_error(exc)
            self._emit(
                job,
                ProgressEvent(
                    job_id=job.job_id,
                    status=DownloadStatus.ERROR,
                    percent=job.percent,
                    message=message,
                    error=message,
                ),
            )

    def _emit(self, job: ActiveJob, event: ProgressEvent) -> None:
        job.status = event.status
        job.percent = event.percent
        job.message = event.message
        job.events.put(event)

    def event_stream(self, job_id: str):
        job = self.get(job_id)
        while True:
            try:
                event = job.events.get(timeout=30)
            except queue.Empty:
                yield "event: ping\ndata: {}\n\n"
                continue

            yield f"data: {json.dumps(event.model_dump(mode='json'), ensure_ascii=False)}\n\n"
            if event.status in {DownloadStatus.COMPLETED, DownloadStatus.ERROR, DownloadStatus.CANCELED}:
                break


download_manager = DownloadManager()
