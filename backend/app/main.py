from __future__ import annotations

import re
from typing import Awaitable, Callable

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import Response

from app.api.router import api_router
from app.core.config import get_settings
from app.core.database import init_db
from app.core.exceptions import (
    AIServiceError,
    AppBaseError,
    ConflictError,
    DocumentExtractionError,
    HeyGenAPIError,
    NotFoundError,
    UnauthorizedError,
    ValidationError,
    VideoGenerationError,
    WorkflowError,
)
from app.core.logging import configure_logging, get_logger
from app.core.security import CustomJSONResponse, build_error_response, build_success_response, get_request_id

settings = get_settings()
configure_logging()
logger = get_logger(__name__)

app = FastAPI(
    title=settings.APP_NAME,
    version="0.2.0",
    description="AI Course Video Generator - API",
    debug=settings.APP_DEBUG,
    default_response_class=CustomJSONResponse,
)

def _assemble_allow_origins(user_origins: list[str] | str) -> list[str]:
    if isinstance(user_origins, str):
        user_origins = [s.strip() for s in user_origins.split(",") if s.strip()]
    safe_defaults = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
        "http://frontend:5173",
        "http://frontend:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]
    merged = list(dict.fromkeys([*list(user_origins), *safe_defaults]))
    return [o.rstrip("/") for o in merged if o]

_ALLOWED_ORIGINS = _assemble_allow_origins(settings.CORS_ORIGINS)
_ALLOWED_ORIGIN_REGEX = re.compile(r"^https?://(localhost|127\.0\.0\.1|frontend|0\.0\.0\.0)(:\d+)?$")

def _origin_is_allowed(origin: str) -> bool:
    clean = (origin or "").rstrip("/")
    if not clean:
        return False
    if clean in _ALLOWED_ORIGINS:
        return True
    return bool(_ALLOWED_ORIGIN_REGEX.match(clean))

app.add_middleware(
    CORSMiddleware,
    allow_origins=_ALLOWED_ORIGINS,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1|frontend|0\.0\.0\.0)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "Content-Disposition", "Content-Length"],
    max_age=3600,
)


@app.middleware("http")
async def cors_headers_everywhere(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    origin = request.headers.get("origin")
    try:
        response = await call_next(request)
    except Exception as exc:  # pragma: no cover
        logger.error("cors_middleware_unhandled_exception_fallback", path=request.url.path, error=str(exc))
        resp = build_error_response(
            error_code="INTERNAL_ERROR",
            message="Internal server error",
            details=str(exc) if settings.APP_DEBUG else None,
            request_id=get_request_id(request),
            status_code=500,
        )
        response = resp

    if origin and _origin_is_allowed(origin):
        existing = response.headers.get("access-control-allow-origin")
        if not existing:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Allow-Methods"] = "GET,POST,PUT,PATCH,DELETE,OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type,Authorization,X-Requested-With,Accept,Origin"
            response.headers["Access-Control-Expose-Headers"] = "X-Request-ID,Content-Disposition,Content-Length"
    if "vary" not in response.headers or "Origin" not in response.headers.get("vary", ""):
        vary = response.headers.get("vary", "")
        response.headers["Vary"] = f"{vary}, Origin".strip(", ")
    return response


app.include_router(api_router)


@app.on_event("startup")
async def on_startup() -> None:
    logger.info("application_starting", env=settings.APP_ENV)
    try:
        init_db()
        logger.info("database_initialized")
    except Exception as exc:  # pragma: no cover
        logger.warning("database_init_failed", error=str(exc))


@app.exception_handler(AppBaseError)
async def app_base_error_handler(request: Request, exc: AppBaseError):
    req_id = get_request_id(request)
    logger.error(
        "application_error",
        request_id=req_id,
        code=exc.code,
        message=exc.message,
        path=request.url.path,
    )
    return build_error_response(
        error_code=exc.code,
        message=exc.message,
        details=exc.details,
        request_id=req_id,
        status_code=exc.status_code,
    )


@app.exception_handler(Exception)
async def unhandled_error_handler(request: Request, exc: Exception):
    req_id = get_request_id(request)
    logger.exception(
        "unhandled_exception",
        request_id=req_id,
        path=request.url.path,
        error=str(exc),
    )
    return build_error_response(
        error_code="INTERNAL_ERROR",
        message="Internal server error",
        details=str(exc) if settings.APP_DEBUG else None,
        request_id=req_id,
        status_code=500,
    )


@app.get("/", include_in_schema=False)
async def root():
    return {
        "name": settings.APP_NAME,
        "version": "0.2.0",
        "docs": "/docs",
        "health": "/api/v1/health",
    }
