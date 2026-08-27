from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Request

from app.core.security import build_success_response, get_request_id

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("", summary="Health check")
async def health_check(request: Request):
    """Basic health check endpoint."""
    data = {
        "status": "ok",
        "version": "0.2.0",
        "service": "ai-course-video-generator",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    return build_success_response(data=data, request_id=get_request_id(request))
