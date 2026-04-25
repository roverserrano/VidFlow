from __future__ import annotations

from abc import ABC, abstractmethod

from backend.models import DownloadRequest, DownloadResult, MediaMetadata, Platform, ProgressEvent
from backend.services.ytdlp_service import CancelCheck, ProgressCallback


class Downloader(ABC):
    platform: Platform

    @abstractmethod
    def analyze(self, url: str) -> MediaMetadata:
        raise NotImplementedError

    @abstractmethod
    def download(
        self,
        request: DownloadRequest,
        *,
        job_id: str,
        emit: ProgressCallback,
        should_cancel: CancelCheck,
    ) -> DownloadResult:
        raise NotImplementedError

