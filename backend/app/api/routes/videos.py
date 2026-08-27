from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Body, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.logging import get_logger
from app.core.security import build_success_response, get_request_id
from app.models.course import Course, CourseStatus as CS
from app.models.lesson import Lesson
from app.models.video import Video, VideoStatus
from app.schemas.script import ScriptOutput
from app.schemas.video import VideoRead, VideoStatusResponse
from app.services.course_service import CourseService
from app.services.heygen_service import get_heygen_provider

logger = get_logger(__name__)

router = APIRouter(prefix="/videos", tags=["Videos"])

DbSession = Annotated[Session, Depends(get_db)]


class GenerateVideoRequest(BaseModel):
    lesson_id: uuid.UUID
    provider: str = "mock"


def _script_from_course(course: Course) -> ScriptOutput:
    if course.script_data:
        try:
            return ScriptOutput(**course.script_data)
        except Exception as exc:
            logger.warning("script_data_invalid", course_id=str(course.id), error=str(exc))
    return ScriptOutput(
        title=course.title or f"Course {str(course.id)[:8]}",
        scenes=[],
        total_duration_seconds=course.estimated_duration_minutes * 60 if course.estimated_duration_minutes else 300,
        introduction="",
        conclusion="",
        target_audience="",
    )


@router.post(
    "/generate",
    summary="Generate video for a lesson using HeyGen (or mock)",
    status_code=status.HTTP_201_CREATED,
)
async def generate_video(
    request: Request,
    body: GenerateVideoRequest,
    db: DbSession,
):
    rid = get_request_id(request)

    lesson = db.get(Lesson, body.lesson_id)
    if lesson is None:
        raise HTTPException(status_code=404, detail=f"Lesson {body.lesson_id} not found")

    course = db.get(Course, lesson.course_id)
    if course is None:
        raise HTTPException(status_code=404, detail=f"Course {lesson.course_id} not found")

    try:
        CourseService.transition_to(
            db,
            course.id,
            CS.VIDEO_GENERATING,
            progress=75,
            current_step="Submitting video generation request to provider",
        )
        db.refresh(course)
    except Exception as exc:
        logger.warning("video_generating_transition_skipped", course_id=str(course.id), error=str(exc))

    script = _script_from_course(course)
    provider = get_heygen_provider(body.provider)

    provider_response = provider.generate_video(lesson.id, script)

    video = Video(
        lesson_id=lesson.id,
        provider=body.provider,
        provider_video_id=provider_response.provider_video_id,
        job_id=provider_response.provider_video_id,
        status=VideoStatus.SUBMITTED,
        request_payload={"script_title": script.title, "provider": body.provider},
    )
    db.add(video)
    db.commit()
    db.refresh(video)

    if provider_response.status == VideoStatus.COMPLETED:
        video.status = VideoStatus.COMPLETED
        video.video_url = provider_response.video_url
        video.thumbnail_url = provider_response.thumbnail_url
        video.duration = provider_response.duration
        video.completed_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(video)

    try:
        CourseService.transition_to(
            db,
            course.id,
            CS.VIDEO_PROCESSING,
            progress=80,
            current_step="Video is being processed by the provider",
        )
    except Exception as exc:
        logger.warning("video_processing_transition_skipped", course_id=str(course.id), error=str(exc))

    if provider_response.status == VideoStatus.COMPLETED:
        try:
            CourseService.transition_to(
                db,
                course.id,
                CS.VIDEO_READY,
                progress=90,
                current_step="Video generation completed",
            )
        except Exception as exc:
            logger.warning("video_ready_transition_skipped", course_id=str(course.id), error=str(exc))

    return build_success_response(
        data=VideoRead.model_validate(video).model_dump(),
        request_id=rid,
        status_code=status.HTTP_201_CREATED,
    )


@router.get(
    "/{video_id}/status",
    summary="Check video generation status and update DB row",
)
async def get_video_status(
    request: Request,
    video_id: uuid.UUID,
    db: DbSession,
):
    rid = get_request_id(request)

    video = db.get(Video, video_id)
    if video is None:
        raise HTTPException(status_code=404, detail=f"Video {video_id} not found")

    lesson = db.get(Lesson, video.lesson_id)
    course = db.get(Course, lesson.course_id) if lesson else None

    if video.status == VideoStatus.COMPLETED:
        response = VideoStatusResponse(
            provider_video_id=video.provider_video_id or str(video.id),
            status=video.status,
            progress=100,
            message="Video is completed",
            video_url=video.video_url,
            thumbnail_url=video.thumbnail_url,
            duration=video.duration,
        )
        return build_success_response(data=response.model_dump(), request_id=rid)

    provider = get_heygen_provider(video.provider)
    status_response = provider.check_status(
        provider_video_id=video.provider_video_id or str(video.id),
        job_id=video.job_id,
    )

    new_status = status_response.status
    if new_status != video.status:
        video.status = new_status
    if status_response.video_url:
        video.video_url = status_response.video_url
    if status_response.thumbnail_url:
        video.thumbnail_url = status_response.thumbnail_url
    if status_response.duration is not None:
        video.duration = int(status_response.duration)
    if status_response.status == VideoStatus.COMPLETED and video.completed_at is None:
        video.completed_at = datetime.now(timezone.utc)
    if status_response.status == VideoStatus.FAILED and status_response.message:
        video.error_message = status_response.message

    db.commit()
    db.refresh(video)

    if course is not None:
        if status_response.status == VideoStatus.COMPLETED:
            try:
                CourseService.transition_to(
                    db,
                    course.id,
                    CS.VIDEO_READY,
                    progress=90,
                    current_step="Video ready for QA review",
                )
            except Exception as exc:
                logger.warning("video_ready_transition_skipped", course_id=str(course.id), error=str(exc))
        elif status_response.status == VideoStatus.FAILED:
            try:
                CourseService.mark_failed(
                    db, course.id, f"Video generation failed: {status_response.message or 'unknown error'}"
                )
            except Exception as exc:
                logger.warning("video_failed_mark_failed_skipped", course_id=str(course.id), error=str(exc))

    return build_success_response(data=status_response.model_dump(), request_id=rid)


@router.get(
    "/courses/{course_id}/latest",
    summary="Get latest video for the first lesson of a course",
)
async def get_course_latest_video(
    request: Request,
    course_id: uuid.UUID,
    db: DbSession,
):
    rid = get_request_id(request)

    course = db.get(Course, course_id)
    if course is None:
        raise HTTPException(status_code=404, detail=f"Course {course_id} not found")

    stmt_first_lesson = (
        select(Lesson)
        .where(Lesson.course_id == course_id)
        .order_by(Lesson.created_at.asc())
        .limit(1)
    )
    first_lesson = db.execute(stmt_first_lesson).scalars().first()
    if first_lesson is None:
        raise HTTPException(status_code=404, detail=f"No lessons found for course {course_id}")

    stmt_latest_video = (
        select(Video)
        .where(Video.lesson_id == first_lesson.id)
        .order_by(Video.created_at.desc())
        .limit(1)
    )
    latest_video = db.execute(stmt_latest_video).scalars().first()
    if latest_video is None:
        raise HTTPException(status_code=404, detail=f"No videos found for course {course_id}")

    return build_success_response(
        data=VideoRead.model_validate(latest_video).model_dump(),
        request_id=rid,
    )
