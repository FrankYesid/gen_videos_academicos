from __future__ import annotations


class AppBaseError(Exception):
    """Base exception for all application errors."""

    code: str = "INTERNAL_ERROR"
    status_code: int = 500

    def __init__(self, message: str, details: object | None = None):
        super().__init__(message)
        self.message = message
        self.details = details


class ValidationError(AppBaseError):
    code = "VALIDATION_ERROR"
    status_code = 400


class DocumentExtractionError(AppBaseError):
    code = "DOCUMENT_EXTRACTION_ERROR"
    status_code = 422


class AIServiceError(AppBaseError):
    code = "AI_SERVICE_ERROR"
    status_code = 502


class HeyGenAPIError(AppBaseError):
    code = "HEYGEN_API_ERROR"
    status_code = 502


class VideoGenerationError(AppBaseError):
    code = "VIDEO_GENERATION_ERROR"
    status_code = 500


class WorkflowError(AppBaseError):
    code = "WORKFLOW_ERROR"
    status_code = 409


class NotFoundError(AppBaseError):
    code = "NOT_FOUND"
    status_code = 404


class UnauthorizedError(AppBaseError):
    code = "UNAUTHORIZED"
    status_code = 401


class ConflictError(AppBaseError):
    code = "CONFLICT"
    status_code = 409
