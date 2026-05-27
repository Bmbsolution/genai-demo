"""ServiceCat FastAPI application factory and ASGI entrypoint."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from servicecat.config import get_settings
from servicecat.errors import ServiceCatError
from servicecat.http import close_http_client

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from fastapi import Request


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Application lifespan; closes the shared HTTP client on shutdown."""
    yield
    await close_http_client()


def create_app() -> FastAPI:
    """Build and configure the FastAPI application."""
    settings = get_settings()
    app = FastAPI(title="ServiceCat API", version="0.1.0", lifespan=lifespan)

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

    return app


app = create_app()
