from __future__ import annotations

from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings

settings = get_settings()

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    echo=settings.APP_DEBUG,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    import importlib

    model_modules = [
        "document",
        "course",
        "lesson",
        "scene",
        "video",
        "agent_run",
    ]
    for module_name in model_modules:
        try:
            importlib.import_module(f"app.models.{module_name}")
        except ImportError:
            pass

    # Note: Tables are created via Alembic migrations, not automatically
    # Base.metadata.create_all(bind=engine)
