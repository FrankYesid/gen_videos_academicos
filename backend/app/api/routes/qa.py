from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.agents.qa_agent import QAAgent
from app.core.config import get_settings
from app.core.database import get_db
from app.core.exceptions import ValidationError
from app.core.logging import get_logger
from app.core.security import build_success_response, get_request_id
from app.models.course import Course, CourseStatus
from app.models.lesson import Lesson
from app.models.video import Video
from app.schemas.course import CourseRead
from app.schemas.qa import QAIssue, QAResult
from app.services.course_service import CourseService

logger = get_logger(__name__)
settings = get_settings()

router = APIRouter(prefix="/qa", tags=["QA"])

DbSession = Annotated[Session, Depends(get_db)]


def _course_to_qa_schema(course: Course) -> QAResult:
    """Convert stored course QA data to QAResult schema."""
    data = course.qa_data or {}
    issues_data = data.get("issues", [])
    issues = [QAIssue(**issue) for issue in issues_data]

    return QAResult(
        score=course.qa_score or data.get("score", 0),
        status=course.qa_status or data.get("status", "rejected"),
        issues=issues,
        recommendations=data.get("recommendations", []),
        summary=data.get("summary"),
    )


@router.post(
    "/courses/{course_id}/review",
    summary="Run QA review on a course",
    status_code=status.HTTP_200_OK,
    response_model_exclude_none=True,
)
async def review_course_qa(
    request: Request,
    course_id: uuid.UUID,
    db: DbSession,
    force_regenerate: Annotated[
        bool,
        Depends(lambda: False),
    ] = False,
):
    """Execute QA Agent to review script, pedagogical design, and video quality."""
    rid = get_request_id(request)

    try:
        course = CourseService.get_by_id(db, course_id, load_related=True)
    except Exception:
        raise HTTPException(status_code=404, detail=f"Course {course_id} not found")

    allowed_statuses = {
        CourseStatus.VIDEO_READY,
        CourseStatus.SCRIPT_VALIDATED,
    }
    if course.status not in allowed_statuses and not force_regenerate:
        raise HTTPException(
            status_code=409,
            detail=f"Cannot run QA review in status {course.status!r}. "
            f"Allowed: VIDEO_READY, SCRIPT_VALIDATED",
        )

    try:
        if course.status != CourseStatus.QA:
            CourseService.transition_to(
                db,
                course_id,
                CourseStatus.QA,
                progress=92,
                current_step="Running QA review on script and video",
            )
            db.refresh(course)

        analysis_data = {
            "title": course.title,
            "subject": course.subject,
            "level": course.level or "intermediate",
            "summary": course.description or "",
            "main_topics": course.main_topics or [],
            "concepts": course.concepts or [],
            "prerequisites": course.prerequisites or [],
        }

        pedagogical_data = course.pedagogical_data or {}
        script_data = course.script_data or {}

        video_metadata: dict[str, object] = {}
        first_lesson: Lesson | None = None
        for lesson in course.lessons:
            first_lesson = lesson
            break

        if first_lesson is not None:
            first_video: Video | None = None
            for video in first_lesson.videos:
                first_video = video
                break
            if first_video is not None:
                video_metadata = {
                    "url": first_video.video_url or "",
                    "duration": first_video.duration or 0,
                }

        qa_min_score = settings.QA_MIN_SCORE or 80

        agent = QAAgent()
        qa_result = agent.run_qa(
            db=db,
            course_id=course.id,
            qa_min_score=qa_min_score,
            analysis_data=analysis_data,
            pedagogical_data=pedagogical_data,
            script_data=script_data,
            video_metadata=video_metadata,
        )

        course.qa_data = qa_result.model_dump(mode="json")
        course.qa_score = qa_result.score
        course.qa_status = qa_result.status

        if qa_result.status == "approved":
            course.progress = 100
            course.status = CourseStatus.COMPLETED
            course.current_step = "QA review approved - course completed"
        else:
            course.current_step = f"QA review rejected (score={qa_result.score}) - revisions required"

        db.commit()
        db.refresh(course)

        logger.info(
            "qa_review_completed",
            course_id=str(course_id),
            score=qa_result.score,
            status=qa_result.status,
            issues_count=len(qa_result.issues),
        )

        qa_response = _course_to_qa_schema(course)

        return build_success_response(
            data={
                "qa": qa_response.model_dump(),
                "course": CourseRead.model_validate(course).model_dump(),
            },
            request_id=rid,
        )

    except Exception as exc:
        logger.error("qa_review_failed", course_id=str(course_id), error=str(exc))
        try:
            CourseService.mark_failed(db, course_id, f"QA review failed: {exc}")
        except Exception:
            pass
        raise HTTPException(status_code=500, detail=f"QA review failed: {str(exc)}")


@router.get(
    "/courses/{course_id}",
    summary="Get existing QA review result for a course",
    status_code=status.HTTP_200_OK,
    response_model_exclude_none=True,
)
async def get_course_qa(
    request: Request,
    course_id: uuid.UUID,
    db: DbSession,
):
    """Get the existing QA review result for a course."""
    rid = get_request_id(request)

    course = db.get(Course, course_id)
    if course is None:
        raise HTTPException(status_code=404, detail=f"Course {course_id} not found")

    if not course.qa_data and course.qa_score is None:
        raise HTTPException(
            status_code=404,
            detail="No QA review found for this course. Please run QA review first.",
        )

    return build_success_response(
        data={
            "qa": _course_to_qa_schema(course).model_dump(),
        },
        request_id=rid,
    )
