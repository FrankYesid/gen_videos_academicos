from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.agents.pedagogical_agent import PedagogicalAgent
from app.core.database import get_db
from app.core.exceptions import ValidationError
from app.core.logging import get_logger
from app.core.security import build_success_response, get_request_id
from app.models.course import Course, CourseStatus
from app.models.lesson import Lesson
from app.schemas.pedagogical import (
    CommonMistake,
    Example,
    LessonStructureItem,
    PedagogicalDesign,
)

logger = get_logger(__name__)

router = APIRouter(prefix="/pedagogical", tags=["Pedagogical"])

DbSession = Annotated[Session, Depends(get_db)]


def _course_to_pedagogical_schema(course: Course) -> PedagogicalDesign:
    """Convert stored course pedagogical data to PedagogicalDesign schema."""
    data = course.pedagogical_data or {}

    lesson_structure_items = [
        LessonStructureItem(**item) for item in data.get("lesson_structure", [])
    ]
    examples = [Example(**ex) for ex in data.get("examples", [])]
    common_mistakes = [CommonMistake(**cm) for cm in data.get("common_mistakes", [])]

    return PedagogicalDesign(
        general_objective=data.get("general_objective", ""),
        specific_objectives=data.get("specific_objectives", []),
        prerequisites=data.get("prerequisites", []),
        lesson_structure=lesson_structure_items,
        examples=examples,
        common_mistakes=common_mistakes,
        summary=data.get("summary", ""),
        estimated_duration_minutes=course.estimated_duration_minutes
        or data.get("estimated_duration_minutes", 10),
        activity_suggested=data.get("activity_suggested"),
        teaching_strategies=data.get("teaching_strategies", []),
        assessment_methods=data.get("assessment_methods", []),
    )


@router.post(
    "/courses/{course_id}",
    summary="Generate pedagogical design for a course",
    status_code=status.HTTP_200_OK,
    response_model_exclude_none=True,
)
async def generate_pedagogical_design(
    request: Request,
    course_id: uuid.UUID,
    db: DbSession,
    force_regenerate: Annotated[
        bool,
        Query(description="Force regeneration even if design exists"),
    ] = False,
):
    """Generate pedagogical structure and learning objectives using AI."""
    rid = get_request_id(request)

    course = db.get(Course, course_id)
    if course is None:
        raise HTTPException(status_code=404, detail=f"Course {course_id} not found")

    if not course.title or not course.subject:
        raise HTTPException(
            status_code=400,
            detail="Course must be analyzed first. Please run analysis before pedagogical design.",
        )

    if course.pedagogical_data and course.estimated_duration_minutes and not force_regenerate:
        logger.info("pedagogical_design_already_exists", course_id=str(course_id))
        return build_success_response(
            data={
                "pedagogical_design": _course_to_pedagogical_schema(course).model_dump(),
                "cached": True,
            },
            request_id=rid,
        )

    allowed_statuses = {
        CourseStatus.ANALYZING,
        CourseStatus.PEDAGOGICAL_DESIGN,
        CourseStatus.SCRIPT_GENERATED,
        CourseStatus.FAILED,
    }
    if course.status not in allowed_statuses and not force_regenerate:
        raise ValidationError(
            f"Cannot generate pedagogical design in status {course.status!r}. "
            f"Allowed: ANALYZING, PEDAGOGICAL_DESIGN, SCRIPT_GENERATED, FAILED"
        )

    try:
        from app.services.course_service import CourseService

        if course.status != CourseStatus.PEDAGOGICAL_DESIGN:
            CourseService.transition_to(
                db,
                course_id,
                CourseStatus.PEDAGOGICAL_DESIGN,
                progress=30,
                current_step="Designing pedagogical structure and learning objectives",
            )
            db.refresh(course)

        concepts_dump = course.concepts or []
        analysis_data = {
            "title": course.title,
            "subject": course.subject,
            "level": course.level or "intermediate",
            "summary": course.description or "",
            "main_topics": course.main_topics or [],
            "concepts": concepts_dump,
            "prerequisites": course.prerequisites or [],
        }

        agent = PedagogicalAgent()
        pedagogical_result = agent.design_pedagogy(
            db=db,
            course_id=course_id,
            analysis_data=analysis_data,
        )

        lesson_structure_dump = [m.model_dump() for m in pedagogical_result.lesson_structure]
        examples_dump = [e.model_dump() for e in pedagogical_result.examples]
        mistakes_dump = [m.model_dump() for m in pedagogical_result.common_mistakes]

        course.pedagogical_data = {
            "general_objective": pedagogical_result.general_objective,
            "specific_objectives": pedagogical_result.specific_objectives,
            "prerequisites": pedagogical_result.prerequisites,
            "lesson_structure": lesson_structure_dump,
            "examples": examples_dump,
            "common_mistakes": mistakes_dump,
            "summary": pedagogical_result.summary,
            "estimated_duration_minutes": pedagogical_result.estimated_duration_minutes,
            "activity_suggested": pedagogical_result.activity_suggested,
            "teaching_strategies": pedagogical_result.teaching_strategies,
            "assessment_methods": pedagogical_result.assessment_methods,
        }
        course.estimated_duration_minutes = pedagogical_result.estimated_duration_minutes
        course.current_step = "Pedagogical design completed - script generation pending"
        course.progress = 40
        course.status = CourseStatus.PEDAGOGICAL_DESIGN
        db.commit()
        db.refresh(course)

        existing_lesson = None
        for lesson in course.lessons:
            existing_lesson = lesson
            break

        if existing_lesson is None:
            lesson = Lesson(
                course_id=course.id,
                title=course.title or "Generated Lesson",
                general_objective=pedagogical_result.general_objective,
                specific_objectives=pedagogical_result.specific_objectives,
                duration=pedagogical_result.estimated_duration_minutes,
                lesson_structure=lesson_structure_dump,
                examples=examples_dump,
                common_mistakes=mistakes_dump,
                summary=pedagogical_result.summary,
                activity_suggested=pedagogical_result.activity_suggested,
                status="PEDAGOGICAL_DESIGN_COMPLETED",
            )
            db.add(lesson)
            db.commit()
            db.refresh(lesson)
            logger.info("lesson_created", course_id=str(course_id), lesson_id=str(lesson.id))
        else:
            existing_lesson.title = course.title or existing_lesson.title
            existing_lesson.general_objective = pedagogical_result.general_objective
            existing_lesson.specific_objectives = pedagogical_result.specific_objectives
            existing_lesson.duration = pedagogical_result.estimated_duration_minutes
            existing_lesson.lesson_structure = lesson_structure_dump
            existing_lesson.examples = examples_dump
            existing_lesson.common_mistakes = mistakes_dump
            existing_lesson.summary = pedagogical_result.summary
            existing_lesson.activity_suggested = pedagogical_result.activity_suggested
            existing_lesson.status = "PEDAGOGICAL_DESIGN_COMPLETED"
            db.commit()
            db.refresh(existing_lesson)
            logger.info("lesson_updated", course_id=str(course_id), lesson_id=str(existing_lesson.id))

        logger.info(
            "pedagogical_design_generated",
            course_id=str(course_id),
            duration=pedagogical_result.estimated_duration_minutes,
            modules_count=len(pedagogical_result.lesson_structure),
        )

        pedagogical_response = PedagogicalDesign(
            general_objective=pedagogical_result.general_objective,
            specific_objectives=pedagogical_result.specific_objectives,
            prerequisites=pedagogical_result.prerequisites,
            lesson_structure=pedagogical_result.lesson_structure,
            examples=pedagogical_result.examples,
            common_mistakes=pedagogical_result.common_mistakes,
            summary=pedagogical_result.summary,
            estimated_duration_minutes=pedagogical_result.estimated_duration_minutes,
            activity_suggested=pedagogical_result.activity_suggested,
            teaching_strategies=pedagogical_result.teaching_strategies,
            assessment_methods=pedagogical_result.assessment_methods,
        )

        return build_success_response(
            data={
                "pedagogical_design": pedagogical_response.model_dump(),
                "course_id": str(course_id),
                "cached": False,
            },
            request_id=rid,
        )

    except Exception as exc:
        logger.error("pedagogical_design_failed", course_id=str(course_id), error=str(exc))
        try:
            from app.services.course_service import CourseService

            CourseService.mark_failed(db, course_id, f"Pedagogical design failed: {exc}")
        except Exception:
            pass
        raise HTTPException(status_code=500, detail=f"Pedagogical design failed: {str(exc)}")


@router.get(
    "/courses/{course_id}",
    summary="Get existing pedagogical design for a course",
    status_code=status.HTTP_200_OK,
    response_model_exclude_none=True,
)
async def get_pedagogical_design(
    request: Request,
    course_id: uuid.UUID,
    db: DbSession,
):
    """Get the existing pedagogical design for a course."""
    rid = get_request_id(request)

    course = db.get(Course, course_id)
    if course is None:
        raise HTTPException(status_code=404, detail=f"Course {course_id} not found")

    if not course.pedagogical_data and not course.estimated_duration_minutes:
        raise HTTPException(
            status_code=404,
            detail="No pedagogical design found for this course. Please generate design first.",
        )

    return build_success_response(
        data={
            "pedagogical_design": _course_to_pedagogical_schema(course).model_dump(),
        },
        request_id=rid,
    )
