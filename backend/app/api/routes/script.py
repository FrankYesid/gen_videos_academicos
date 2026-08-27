from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.agents.script_agent import ScriptAgent
from app.core.database import get_db
from app.core.exceptions import ValidationError
from app.core.logging import get_logger
from app.core.security import build_success_response, get_request_id
from app.models.course import Course, CourseStatus
from app.models.lesson import Lesson
from app.models.scene import Scene as SceneModel
from app.schemas.course import CourseRead
from app.schemas.script import Scene, Script

logger = get_logger(__name__)

router = APIRouter(prefix="/scripts", tags=["Script"])

DbSession = Annotated[Session, Depends(get_db)]


def _course_to_script_schema(course: Course) -> Script:
    data = course.script_data or {}

    scenes = [Scene(**s) for s in data.get("scenes", [])]

    return Script(
        title=data.get("title", ""),
        scenes=scenes,
        total_duration_seconds=data.get("total_duration_seconds", 0),
        introduction=data.get("introduction", ""),
        conclusion=data.get("conclusion", ""),
        target_audience=data.get("target_audience", ""),
        tone=data.get("tone", "educational"),
        notes=data.get("notes"),
    )


@router.post(
    "/courses/{course_id}/generate",
    summary="Generate video script for a course",
    status_code=status.HTTP_200_OK,
    response_model_exclude_none=True,
)
async def generate_script(
    request: Request,
    course_id: uuid.UUID,
    db: DbSession,
    force_regenerate: Annotated[
        bool,
        Query(description="Force regeneration even if script exists"),
    ] = False,
):
    rid = get_request_id(request)

    course = db.get(Course, course_id)
    if course is None:
        raise HTTPException(status_code=404, detail=f"Course {course_id} not found")

    if not course.pedagogical_data:
        raise HTTPException(
            status_code=400,
            detail="Pedagogical design must be generated first. Please run pedagogical design before script generation.",
        )

    if course.script_data and not force_regenerate:
        logger.info("script_already_exists", course_id=str(course_id))
        return build_success_response(
            data={
                "script": _course_to_script_schema(course).model_dump(),
                "course": CourseRead.model_validate(course).model_dump(),
                "scenes_created": len(course.script_data.get("scenes", [])),
                "cached": True,
            },
            request_id=rid,
        )

    allowed_statuses = {
        CourseStatus.PEDAGOGICAL_DESIGN,
        CourseStatus.SCRIPT_GENERATED,
        CourseStatus.SCRIPT_VALIDATED,
        CourseStatus.FAILED,
    }
    if course.status not in allowed_statuses and not force_regenerate:
        raise ValidationError(
            f"Cannot generate script in status {course.status!r}. "
            f"Allowed: PEDAGOGICAL_DESIGN, SCRIPT_GENERATED, SCRIPT_VALIDATED, FAILED"
        )

    try:
        from app.services.course_service import CourseService

        CourseService.transition_to(
            db,
            course_id,
            CourseStatus.SCRIPT_GENERATED,
            progress=50,
            current_step="Generating script",
        )
        db.refresh(course)

        concepts_dump = course.concepts or []
        analysis_dict = {
            "title": course.title,
            "subject": course.subject,
            "level": course.level or "intermediate",
            "concepts": concepts_dump,
            "main_topics": course.main_topics or [],
            "prerequisites": course.prerequisites or [],
            "keywords": course.keywords or [],
        }

        agent = ScriptAgent()
        script_result = agent.generate_script(
            db=db,
            course_id=course_id,
            pedagogical_data=course.pedagogical_data or {},
            analysis_data=analysis_dict,
        )

        course.script_data = script_result.model_dump(mode="json")

        existing_lesson = None
        for lesson in course.lessons:
            existing_lesson = lesson
            break

        if existing_lesson is None:
            lesson = Lesson(
                course_id=course.id,
                title=course.title or "Generated Lesson",
                status="SCRIPT_GENERATED",
            )
            db.add(lesson)
            db.commit()
            db.refresh(lesson)
            lesson_id = lesson.id
            logger.info("lesson_created", course_id=str(course_id), lesson_id=str(lesson_id))
        else:
            existing_lesson.title = course.title or existing_lesson.title
            existing_lesson.status = "SCRIPT_GENERATED"
            db.commit()
            db.refresh(existing_lesson)
            lesson_id = existing_lesson.id
            logger.info("lesson_updated", course_id=str(course_id), lesson_id=str(lesson_id))

        db.execute(delete(SceneModel).where(SceneModel.lesson_id == lesson_id))
        db.commit()

        scenes_created = 0
        for i, scene in enumerate(script_result.scenes):
            scene_db = SceneModel(
                lesson_id=lesson_id,
                order_index=i,
                title=scene.title,
                narration=scene.narration,
                visual_instruction=scene.visual_instruction,
                on_screen_text=scene.on_screen_text,
                duration_seconds=scene.duration_seconds,
                educational_purpose=scene.educational_purpose,
            )
            db.add(scene_db)
            scenes_created += 1

        CourseService.transition_to(
            db,
            course_id,
            CourseStatus.SCRIPT_GENERATED,
            progress=60,
            current_step="Script generated - validation pending",
        )
        db.refresh(course)

        db.commit()
        db.refresh(course)

        logger.info(
            "script_generated",
            course_id=str(course_id),
            scenes_count=scenes_created,
            total_duration=script_result.total_duration_seconds,
        )

        script_response = Script(
            title=script_result.title,
            scenes=script_result.scenes,
            total_duration_seconds=script_result.total_duration_seconds,
            introduction=script_result.introduction,
            conclusion=script_result.conclusion,
            target_audience=script_result.target_audience,
            tone=script_result.tone,
            notes=script_result.notes,
        )

        return build_success_response(
            data={
                "script": script_response.model_dump(),
                "course": CourseRead.model_validate(course).model_dump(),
                "scenes_created": scenes_created,
                "cached": False,
            },
            request_id=rid,
        )

    except Exception as exc:
        logger.error("script_generation_failed", course_id=str(course_id), error=str(exc))
        try:
            from app.services.course_service import CourseService

            CourseService.mark_failed(db, course_id, f"Script generation failed: {exc}")
        except Exception:
            pass
        raise HTTPException(status_code=500, detail=f"Script generation failed: {str(exc)}")


@router.get(
    "/courses/{course_id}",
    summary="Get existing script for a course",
    status_code=status.HTTP_200_OK,
    response_model_exclude_none=True,
)
async def get_script(
    request: Request,
    course_id: uuid.UUID,
    db: DbSession,
):
    rid = get_request_id(request)

    course = db.get(Course, course_id)
    if course is None:
        raise HTTPException(status_code=404, detail=f"Course {course_id} not found")

    if not course.script_data:
        raise HTTPException(
            status_code=404,
            detail="No script found for this course. Please generate script first.",
        )

    return build_success_response(
        data={
            "script": _course_to_script_schema(course).model_dump(),
        },
        request_id=rid,
    )
