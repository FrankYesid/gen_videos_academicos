from __future__ import annotations

import uuid
from typing import Annotated, List

from fastapi import APIRouter, Depends, File, Query, Request, UploadFile, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.logging import get_logger
from app.core.security import build_success_response, get_request_id
from app.schemas.course import CourseRead
from app.schemas.document import DocumentListItem, DocumentRead
from app.services.document_service import DocumentService

logger = get_logger(__name__)

router = APIRouter(prefix="/documents", tags=["Documents"])

DbSession = Annotated[Session, Depends(get_db)]


@router.post(
    "",
    summary="Upload a PDF document",
    status_code=status.HTTP_201_CREATED,
    response_model_exclude_none=True,
)
async def upload_document(
    request: Request,
    file: Annotated[UploadFile, File(..., description="PDF file to upload")],
    db: DbSession,
    create_course: Annotated[
        bool,
        Query(description="Automatically create a Course record for this document"),
    ] = True,
    run_extraction: Annotated[
        bool,
        Query(description="Run text extraction immediately after upload"),
    ] = True,
):
    rid = get_request_id(request)
    document, course = await DocumentService.process_upload(
        db,
        file,
        create_course=create_course,
        run_extraction=run_extraction,
    )
    data = {
        "document": DocumentRead.model_validate(document).model_dump(),
        "course": CourseRead.model_validate(course).model_dump() if course else None,
    }
    existing_doc = DocumentService.get_by_hash(db, document.file_hash)
    return build_success_response(
        data=data,
        request_id=rid,
        meta={"deduplicated": existing_doc is not None and course is None},
        status_code=status.HTTP_201_CREATED,
    )


@router.get("", summary="List documents", response_model_exclude_none=True)
async def list_documents(
    request: Request,
    db: DbSession,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
):
    docs = DocumentService.list(db, skip=skip, limit=limit)
    items: List[dict] = [DocumentListItem.model_validate(d).model_dump() for d in docs]
    return build_success_response(
        data={"items": items, "count": len(items), "skip": skip, "limit": limit},
        request_id=get_request_id(request),
    )


@router.get(
    "/{document_id}",
    summary="Get document details",
    response_model_exclude_none=True,
)
async def get_document(
    request: Request,
    document_id: uuid.UUID,
    db: DbSession,
    include_text: Annotated[
        bool, Query(description="Include extracted text in response")
    ] = False,
):
    doc = DocumentService.get_by_id(db, document_id)
    data = DocumentRead.model_validate(doc).model_dump()
    if include_text and doc.extracted_text:
        data["extracted_text_preview"] = (
            doc.extracted_text[:2000] + ("…" if len(doc.extracted_text) > 2000 else "")
        )
        data["extracted_text_length"] = len(doc.extracted_text)
    return build_success_response(data=data, request_id=get_request_id(request))


@router.delete(
    "/{document_id}",
    summary="Delete a document",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_document(
    document_id: uuid.UUID,
    db: DbSession,
):
    DocumentService.delete(db, document_id)
    return JSONResponse(status_code=status.HTTP_204_NO_CONTENT, content=None)
