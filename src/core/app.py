"""FastAPI app factory with modular routers."""

from __future__ import annotations

import time
import uuid

from fastapi import FastAPI, Request

from src.api.routes import agents, auth, chat, health, history, report, upload
from src.core.container import ServiceContainer


def create_app() -> FastAPI:
    app = FastAPI(
        title="Calvados Science Assistance API",
        description="Backend platform for external n8n orchestration of TZ analysis agents",
        version="0.1.0",
    )
    app.state.container = ServiceContainer()

    @app.middleware("http")
    async def request_logger(request: Request, call_next):
        request_id = str(uuid.uuid4())
        started = time.perf_counter()
        request.state.request_id = request_id
        response = await call_next(request)
        elapsed_ms = (time.perf_counter() - started) * 1000
        user_id = getattr(request.state, "user_id", None)
        app.state.container.repository.save_api_log(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            user_id=user_id,
            status_code=response.status_code,
            latency_ms=round(elapsed_ms, 2),
        )
        response.headers["X-Request-ID"] = request_id
        return response

    app.include_router(health.router)
    app.include_router(auth.router, prefix="/auth", tags=["auth"])
    app.include_router(upload.router, prefix="/api", tags=["upload"])
    app.include_router(history.router, prefix="/api", tags=["history"])
    app.include_router(chat.router, prefix="/api", tags=["chat"])
    app.include_router(report.router, prefix="/api", tags=["report"])
    app.include_router(agents.router, prefix="/agent", tags=["agents"])
    return app
