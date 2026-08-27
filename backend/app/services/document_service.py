from __future__ import annotations

import uuid
from typing import Sequence

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.core.logging import get_logger
from app.models.document import Document, DocumentStatus
from app.models.course import Course, CourseStatus
from app.schemas.document import DocumentCreate, DocumentUpdate
from app.services.extraction_service import ExtractionService
from app.services.storage_service import StorageService
from app.services.course_service import CourseService

logger = get_logger(__name__)


class DocumentService:
    """Business logic for documents (PDFs)."""

    # ---------- Read queries ----------
    @staticmethod
    def list(db: Session, skip: int = 0, limit: int = 100) -> Sequence[Document]:
        stmt = (
            select(Document)
            .order_by(Document.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return db.execute(stmt).scalars().all()

    @staticmethod
    def get_by_id(db: Session, document_id: uuid.UUID) -> Document:
        doc = db.get(Document, document_id)
        if doc is None:
            raise NotFoundError(f"Document {document_id} not found.")
        return doc

    @staticmethod
    def get_by_hash(db: Session, sha256: str) -> Document | None:
        stmt = select(Document).where(Document.file_hash == sha256).limit(1)
        return db.execute(stmt).scalars().first()

    # ---------- Mutations ----------
    @staticmethod
    def create(db: Session, data: DocumentCreate) -> Document:
        doc = Document(**data.model_dump())
        db.add(doc)
        db.commit()
        db.refresh(doc)
        logger.info("document_created", document_id=str(doc.id), hash_prefix=doc.file_hash[:10])
        return doc

    @staticmethod
    def update(
        db: Session, document_id: uuid.UUID, data: DocumentUpdate
    ) -> Document:
        doc = DocumentService.get_by_id(db, document_id)
        payload = data.model_dump(exclude_unset=True)
        for k, v in payload.items():
            setattr(doc, k, v)
        db.commit()
        db.refresh(doc)
        return doc

    @staticmethod
    def delete(db: Session, document_id: uuid.UUID) -> None:
        doc = DocumentService.get_by_id(db, document_id)
        db.delete(doc)
        db.commit()
        logger.info("document_deleted", document_id=str(document_id))

    # ---------- Upload workflow ----------
    @staticmethod
    async def process_upload(
        db: Session,
        upload: UploadFile,
        *,
        create_course: bool = True,
        run_extraction: bool = True,
    ) -> tuple[Document, Course | None]:
        """Full upload pipeline: validate -> store hash -> persist -> extract -> create course."""

        filename_raw = upload.filename or ""
        mime_type = upload.content_type or ""
        file_bytes = await upload.read()

        if not file_bytes:
            raise ValidationError("Uploaded file is empty.")

        try:
            sha256, file_path = StorageService.save(filename_raw, mime_type, file_bytes)
        except ValidationError:
            raise
        except Exception as exc:
            raise ValidationError(f"Failed to store file: {exc}") from exc

        existing = DocumentService.get_by_hash(db, sha256)
        if existing is not None:
            logger.info(
                "document_upload_deduplicated",
                document_id=str(existing.id),
                hash_prefix=sha256[:10],
            )
            existing_course = next(iter(existing.courses), None) if existing.courses else None
            if existing_course is None and create_course:
                existing_course = CourseService.create_for_document(
                    db, existing, title=existing.filename
                )
            return existing, existing_course

        safe_filename = StorageService._secure_filename(filename_raw)

        doc_create = DocumentCreate(
            filename=safe_filename,
            mime_type=mime_type,
            file_size=len(file_bytes),
            file_hash=sha256,
            file_path=str(file_path),
        )
        document = DocumentService.create(db, doc_create)
        document.status = DocumentStatus.UPLOADED
        db.commit()
        db.refresh(document)

        course: Course | None = None
        if create_course:
            title = _derive_title(safe_filename)
            course = CourseService.create_for_document(db, document, title=title)
            course.status = CourseStatus.UPLOADED
            db.commit()
            db.refresh(course)

        if run_extraction:
            try:
                document.status = DocumentStatus.EXTRACTING
                if course is not None:
                    course.status = CourseStatus.EXTRACTING
                    course.current_step = "Extracting text from PDF"
                    course.progress = 10
                db.commit()

                result = ExtractionService.extract(document.file_path)
                DocumentService.update(
                    db,
                    document.id,
                    DocumentUpdate(
                        page_count=result.page_count,
                        extracted_text=result.text,
                        status=DocumentStatus.EXTRACTED,
                    ),
                )

                if course is not None:
                    course.status = CourseStatus.ANALYZING
                    course.current_step = "Text extracted — analysis pending"
                    course.progress = 20
                    if not course.title:
                        course.title = _derive_title(document.filename)
                    db.commit()
                    db.refresh(course)

            except Exception as exc:
                DocumentService.update(
                    db,
                    document.id,
                    DocumentUpdate(
                        status=DocumentStatus.FAILED,
                        error_message=str(exc),
                    ),
                )
                if course is not None:
                    course.status = CourseStatus.FAILED
                    course.error_message = str(exc)
                    db.commit()
                raise

        return document, course


def _derive_title(filename: str) -> str:
    # Strip extension, replace underscores/dashes with spaces, title-case
    from pathlib import Path

    stem = Path(filename).stem
    cleaned = stem.replace("_", " ").replace("-", " ").strip()
    return cleaned or "Untitled Course"
