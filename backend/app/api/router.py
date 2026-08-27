from fastapi import APIRouter

from app.api.routes import analysis, courses, documents, health, pedagogical, qa, script, videos, workflow

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(health.router)
api_router.include_router(documents.router)
api_router.include_router(courses.router)
api_router.include_router(analysis.router)
api_router.include_router(pedagogical.router)
api_router.include_router(script.router)
api_router.include_router(videos.router)
api_router.include_router(qa.router)
api_router.include_router(workflow.router)
