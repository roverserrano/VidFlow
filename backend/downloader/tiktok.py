from __future__ import annotations

from backend.downloader.base import Downloader
from backend.models import DownloadRequest, DownloadResult, MediaMetadata, Platform
from backend.services.ytdlp_service import CancelCheck, ProgressCallback, ytdlp_service


class TikTokDownloader(Downloader):
    platform = Platform.TIKTOK

    def analyze(self, url: str) -> MediaMetadata:
        return ytdlp_service.analyze(url, self.platform)

    def download(
        self,
        request: DownloadRequest,
        *,
        job_id: str,
        emit: ProgressCallback,
        should_cancel: CancelCheck,
    ) -> DownloadResult:
        return ytdlp_service.download(
            request,
            platform=self.platform,
            job_id=job_id,
            emit=emit,
            should_cancel=should_cancel,
        )

