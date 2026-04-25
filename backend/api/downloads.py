from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from backend.models import DownloadJobSnapshot, DownloadRequest
from backend.services.download_manager import download_manager

router = APIRouter(prefix="/downloads", tags=["downloads"])


@router.post("", response_model=DownloadJobSnapshot)
def start_download(payload: DownloadRequest) -> DownloadJobSnapshot:
    return download_manager.start(payload)


@router.get("/{job_id}", response_model=DownloadJobSnapshot)
def download_status(job_id: str) -> DownloadJobSnapshot:
    return download_manager.snapshot(job_id)


@router.get("/{job_id}/events")
def download_events(job_id: str):
    return StreamingResponse(
        download_manager.event_stream(job_id),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/{job_id}/cancel", response_model=DownloadJobSnapshot)
def cancel_download(job_id: str) -> DownloadJobSnapshot:
    return download_manager.cancel(job_id)

