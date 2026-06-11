"""Gatherly FastAPI application factory and ASGI entrypoint."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

from fastapi import FastAPI, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from gatherly.config import get_settings
from gatherly.db import init_db
from gatherly.errors import GatherlyError
from gatherly.routers import auth, events, guests, rsvp

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from fastapi import Request


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Create the schema on startup (SQLite demo — no migrations)."""
    await init_db()
    yield


def create_app() -> FastAPI:
    """Build and configure the FastAPI application."""
    settings = get_settings()
    app = FastAPI(title="Gatherly API", version="0.1.0", lifespan=lifespan)

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

    @app.exception_handler(GatherlyError)
    async def handle_domain_error(_: Request, exc: GatherlyError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": exc.code, "message": exc.message, "details": exc.details}},
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Request validation failed.",
                    "details": {"errors": jsonable_encoder(exc.errors())},
                },
            },
        )

    app.include_router(auth.router)
    app.include_router(events.router)
    app.include_router(guests.router)
    app.include_router(rsvp.router)
    return app


app = create_app()
