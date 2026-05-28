"""ServiceCat FastAPI application factory and ASGI entrypoint."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from servicecat.config import get_settings
from servicecat.errors import ServiceCatError
from servicecat.http import close_http_client
from servicecat.redis_client import close_redis
from servicecat.routers import (
    audit,
    auth,
    scorecard_runs,
    service_dependencies,
    services,
    workspaces,
)

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from fastapi import Request


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Application lifespan; releases shared clients on shutdown."""
    yield
    await close_http_client()
    await close_redis()


def create_app() -> FastAPI:
    """Build and configure the FastAPI application."""
    settings = get_settings()
    app = FastAPI(title="ServiceCat API", version="0.1.0", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allow_origins,
        allow_origin_regex=settings.cors_allow_origin_regex,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health", tags=["meta"])
    async def health() -> dict[str, dict[str, str]]:
        return {"data": {"status": "ok", "environment": settings.environment}}

    @app.exception_handler(ServiceCatError)
    async def handle_domain_error(_: Request, exc: ServiceCatError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "details": exc.details,
                },
            },
        )

    app.include_router(auth.router)
    app.include_router(workspaces.router)
    app.include_router(audit.router)
    app.include_router(services.router)
    app.include_router(service_dependencies.router)
    app.include_router(scorecard_runs.router)
    return app


app = create_app()
