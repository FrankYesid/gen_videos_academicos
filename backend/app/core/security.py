from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import Request
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class CustomJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle UUID and datetime objects."""
    
    def default(self, obj):
        if isinstance(obj, uuid.UUID):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


class CustomJSONResponse(JSONResponse):
    """Custom JSON response with custom encoder."""
    
    def render(self, content: any) -> bytes:
        return json.dumps(
            content,
            ensure_ascii=False,
            allow_nan=False,
            indent=None,
            separators=(",", ":"),
            cls=CustomJSONEncoder,
        ).encode("utf-8")


def get_request_id(request: Request) -> str:
    request_id = request.headers.get("X-Request-ID")
    return request_id or str(uuid.uuid4())


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def sha256_file(file_bytes: bytes) -> str:
    import hashlib

    return hashlib.sha256(file_bytes).hexdigest()


def build_success_response(
    data: Any,
    request_id: str | None = None,
    meta: Dict[str, Any] | None = None,
    status_code: int = 200,
) -> CustomJSONResponse:
    body: Dict[str, Any] = {
        "success": True,
        "data": data,
        "error": None,
        "meta": {
            "request_id": request_id,
            "timestamp": utcnow().isoformat(),
            **(meta or {}),
        },
    }
    return CustomJSONResponse(content=body, status_code=status_code)


def build_error_response(
    error_code: str,
    message: str,
    details: Any = None,
    request_id: str | None = None,
    status_code: int = 400,
) -> CustomJSONResponse:
    body: Dict[str, Any] = {
        "success": False,
        "data": None,
        "error": {
            "code": error_code,
            "message": message,
            "details": details,
        },
        "meta": {
            "request_id": request_id,
            "timestamp": utcnow().isoformat(),
        },
    }
    return CustomJSONResponse(content=body, status_code=status_code)
