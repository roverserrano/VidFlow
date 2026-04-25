from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.api.downloads import router as downloads_router
from backend.api.health import router as health_router
from backend.api.history import router as history_router
from backend.api.metadata import router as metadata_router
from backend.api.settings import router as settings_router
from backend.config import APP_NAME, APP_VERSION
from backend.models.errors import VidFlowError
from backend.services.settings_service import settings_service
from backend.utils.logging import configure_logging


def create_app() -> FastAPI:
    configure_logging(settings_service.read().log_level)

    app = FastAPI(title=APP_NAME, version=APP_VERSION)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "file://"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(VidFlowError)
    async def vidflow_exception_handler(_request: Request, exc: VidFlowError):
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": exc.code, "message": exc.message}},
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(_request: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content={"error": {"code": "internal_error", "message": str(exc)}},
        )

    app.include_router(health_router)
    app.include_router(metadata_router)
    app.include_router(downloads_router)
    app.include_router(settings_router)
    app.include_router(history_router)
    return app


app = create_app()


def run() -> None:
    import uvicorn

    from backend.config import backend_host, backend_port

    uvicorn.run("backend.main:app", host=backend_host(), port=backend_port(), reload=False)
