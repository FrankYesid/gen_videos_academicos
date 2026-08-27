from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.agents.analyzer_agent import AnalyzerAgent
from app.core.database import get_db
from app.core.exceptions import ValidationError
from app.core.logging import get_logger
from app.core.security import build_success_response, get_request_id
from app.models.course import Course, CourseStatus
from app.models.document import Document
from app.schemas.analysis import Analysis, Concept

logger = get_logger(__name__)

router = APIRouter(prefix="/analysis", tags=["Analysis"])

DbSession = Annotated[Session, Depends(get_db)]


def _course_analysis_to_schema(course: Course) -> Analysis:
    """Convert stored course analysis data to Analysis schema."""
    concepts_data = course.concepts or []
    concepts = [
        Concept(
            concept=c.get("concept", ""),
            description=c.get("description", ""),
            source_pages=c.get("source_pages", []),
        )
        for c in concepts_data
    ]

    return Analysis(
        title=course.title or "",
        subject=course.subject or "",
        level=course.level or "intermediate",
        language=course.language,
        summary=course.description or "",
        main_topics=course.main_topics or [],
        prerequisites=course.prerequisites or [],
        concepts=concepts,
        keywords=course.keywords or [],
    )


@router.post(
    "/courses/{course_id}",
    summary="Analyze course document with AI",
    status_code=status.HTTP_200_OK,
    response_model_exclude_none=True,
)
async def analyze_course(
    request: Request,
    course_id: uuid.UUID,
    db: DbSession,
    force_regenerate: Annotated[
        bool,
        Query(description="Force regeneration even if analysis exists"),
    ] = False,
):
    """Run the Analyzer Agent on a course's document to extract structured information."""
    rid = get_request_id(request)

    course = db.get(Course, course_id)
    if course is None:
        raise HTTPException(status_code=404, detail=f"Course {course_id} not found")

    document = db.get(Document, course.document_id)
    if document is None:
        raise HTTPException(status_code=404, detail=f"Document {course.document_id} not found")

    if not document.extracted_text:
        raise HTTPException(
            status_code=400,
            detail="Document text has not been extracted yet. Please wait for extraction to complete.",
        )

    if course.title and course.subject and not force_regenerate:
        logger.info("analysis_already_exists", course_id=str(course_id))
        return build_success_response(
            data={
                "analysis": _course_analysis_to_schema(course).model_dump(),
                "cached": True,
            },
            request_id=rid,
        )

    if course.status not in {
        CourseStatus.CREATED,
        CourseStatus.UPLOADED,
        CourseStatus.EXTRACTING,
        CourseStatus.FAILED,
    } and not force_regenerate:
        raise ValidationError(
            f"Cannot analyze course in status {course.status!r}. "
            f"Allowed: CREATED, UPLOADED, EXTRACTING, FAILED"
        )

    try:
        from app.services.course_service import CourseService

        CourseService.transition_to(
            db, course_id, CourseStatus.ANALYZING, progress=10, current_step="Analyzing document content with AI"
        )
        db.refresh(course)

        agent = AnalyzerAgent()
        analysis_result = agent.analyze_document(
            db=db,
            course_id=course_id,
            document_text=document.extracted_text,
            filename=document.filename,
            page_count=document.page_count or 0,
        )

        concepts_dump = [c.model_dump() for c in analysis_result.concepts]

        course.title = analysis_result.title
        course.subject = analysis_result.subject
        course.level = analysis_result.level
        course.language = analysis_result.language
        course.description = analysis_result.summary
        course.main_topics = analysis_result.main_topics
        course.prerequisites = analysis_result.prerequisites
        course.concepts = concepts_dump
        course.keywords = analysis_result.keywords
        course.current_step = "Analysis completed - pedagogical design pending"
        course.progress = 25
        course.status = CourseStatus.ANALYZING
        db.commit()
        db.refresh(course)

        if CourseStatus.can_transition(course.status, CourseStatus.PEDAGOGICAL_DESIGN):
            course.status = CourseStatus.PEDAGOGICAL_DESIGN
            course.current_step = "Analysis completed - pedagogical design pending"
            db.commit()
            db.refresh(course)

        logger.info(
            "course_analyzed",
            course_id=str(course_id),
            title=analysis_result.title,
            concepts_count=len(analysis_result.concepts),
        )

        analysis_response = Analysis(
            title=analysis_result.title,
            subject=analysis_result.subject,
            level=analysis_result.level,
            language=analysis_result.language,
            summary=analysis_result.summary,
            main_topics=analysis_result.main_topics,
            prerequisites=analysis_result.prerequisites,
            concepts=analysis_result.concepts,
            keywords=analysis_result.keywords,
        )

        return build_success_response(
            data={
                "analysis": analysis_response.model_dump(),
                "course_id": str(course_id),
                "cached": False,
            },
            request_id=rid,
        )

    except Exception as exc:
        logger.error("analysis_failed", course_id=str(course_id), error=str(exc))
        try:
            from app.services.course_service import CourseService

            CourseService.mark_failed(db, course_id, f"Analysis failed: {exc}")
        except Exception:
            pass
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(exc)}")


@router.get(
    "/courses/{course_id}",
    summary="Get existing analysis for a course",
    status_code=status.HTTP_200_OK,
    response_model_exclude_none=True,
)
async def get_analysis(
    request: Request,
    course_id: uuid.UUID,
    db: DbSession,
):
    """Get the existing analysis for a course."""
    rid = get_request_id(request)

    course = db.get(Course, course_id)
    if course is None:
        raise HTTPException(status_code=404, detail=f"Course {course_id} not found")

    if not course.title or not course.subject:
        raise HTTPException(
            status_code=404,
            detail="No analysis found for this course. Please run analysis first.",
        )

    return build_success_response(
        data={
            "analysis": _course_analysis_to_schema(course).model_dump(),
        },
        request_id=rid,
    )
