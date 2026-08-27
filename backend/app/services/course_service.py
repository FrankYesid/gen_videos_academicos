from __future__ import annotations

import uuid
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.core.logging import get_logger
from app.models.course import Course, CourseStatus
from app.models.document import Document
from app.schemas.course import CourseCreate, CourseUpdate

logger = get_logger(__name__)


class CourseService:
    """Business logic for courses lifecycle."""

    # ---------- Read ----------
    @staticmethod
    def list(db: Session, skip: int = 0, limit: int = 100) -> Sequence[Course]:
        stmt = (
            select(Course)
            .options(joinedload(Course.document))
            .order_by(Course.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return db.execute(stmt).scalars().unique().all()

    @staticmethod
    def get_by_id(db: Session, course_id: uuid.UUID, *, load_related: bool = False) -> Course:
        stmt = select(Course).where(Course.id == course_id)
        if load_related:
            stmt = stmt.options(
                joinedload(Course.document),
                joinedload(Course.lessons),
                joinedload(Course.agent_runs),
            )
            row = db.execute(stmt).scalars().unique().first()
        else:
            row = db.execute(stmt).scalars().first()
        if row is None:
            raise NotFoundError(f"Course {course_id} not found.")
        return row

    # ---------- Mutations ----------
    @staticmethod
    def create(db: Session, data: CourseCreate) -> Course:
        payload = data.model_dump(exclude_unset=True)
        if "document_id" in payload and payload["document_id"] is not None:
            doc = db.get(Document, payload["document_id"])
            if doc is None:
                raise ValidationError(
                    f"document_id {payload['document_id']} does not exist."
                )
        course = Course(**payload)
        db.add(course)
        db.commit()
        db.refresh(course)
        logger.info("course_created", course_id=str(course.id))
        return course

    @staticmethod
    def create_for_document(
        db: Session,
        document: Document,
        *,
        title: str | None = None,
        language: str | None = None,
    ) -> Course:
        payload = CourseCreate(
            document_id=document.id,
            title=title,
            language=language or document.language or "es",
        )
        return CourseService.create(db, payload)

    @staticmethod
    def update(db: Session, course_id: uuid.UUID, data: CourseUpdate) -> Course:
        course = CourseService.get_by_id(db, course_id)
        payload = data.model_dump(exclude_unset=True)
        new_status = payload.get("status")
        if new_status and not CourseStatus.can_transition(course.status, new_status):
            raise ConflictError(
                f"Invalid workflow transition: {course.status} → {new_status}. "
                f"Allowed: {sorted(CourseStatus.all())}"
            )
        for k, v in payload.items():
            setattr(course, k, v)
        db.commit()
        db.refresh(course)
        logger.info(
            "course_updated",
            course_id=str(course.id),
            fields=sorted(payload.keys()),
        )
        return course

    @staticmethod
    def delete(db: Session, course_id: uuid.UUID) -> None:
        course = CourseService.get_by_id(db, course_id)
        db.delete(course)
        db.commit()
        logger.info("course_deleted", course_id=str(course_id))

    # ---------- State machine helpers ----------
    @staticmethod
    def transition_to(
        db: Session,
        course_id: uuid.UUID,
        new_status: str,
        *,
        progress: int | None = None,
        current_step: str | None = None,
    ) -> Course:
        payload: dict[str, object] = {"status": new_status}
        if progress is not None:
            payload["progress"] = progress
        if current_step is not None:
            payload["current_step"] = current_step
        update = CourseUpdate.model_validate(payload)
        return CourseService.update(db, course_id, update)

    @staticmethod
    def mark_failed(db: Session, course_id: uuid.UUID, error: str) -> Course:
        return CourseService.update(
            db,
            course_id,
            CourseUpdate(status=CourseStatus.FAILED, error_message=str(error)),
        )
