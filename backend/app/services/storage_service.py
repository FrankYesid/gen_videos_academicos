from __future__ import annotations

import hashlib
import os
import shutil
from pathlib import Path
from typing import Tuple

from app.core.config import get_settings
from app.core.exceptions import ValidationError
from app.core.logging import get_logger

settings = get_settings()
logger = get_logger(__name__)

ALLOWED_MIME_TYPES: set[str] = {"application/pdf"}
ALLOWED_EXTENSIONS: set[str] = {".pdf"}


class StorageService:
    """Manages file storage using SHA-256 for idempotent de-duplication."""

    @staticmethod
    def compute_sha256(file_bytes: bytes) -> str:
        return hashlib.sha256(file_bytes).hexdigest()

    @staticmethod
    def validate_file(
        filename: str,
        mime_type: str,
        file_bytes: bytes,
        max_size_mb: int | None = None,
    ) -> None:
        max_mb = max_size_mb or settings.MAX_FILE_SIZE_MB
        max_bytes = max_mb * 1024 * 1024

        if not filename:
            raise ValidationError("Filename cannot be empty.")

        ext = Path(filename).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise ValidationError(
                f"Invalid file extension '{ext}'. Allowed: {sorted(ALLOWED_EXTENSIONS)}"
            )

        if mime_type not in ALLOWED_MIME_TYPES:
            raise ValidationError(
                f"Invalid MIME type '{mime_type}'. Allowed: {sorted(ALLOWED_MIME_TYPES)}"
            )

        size = len(file_bytes)
        if size <= 0:
            raise ValidationError("File is empty.")
        if size > max_bytes:
            raise ValidationError(
                f"File too large: {size} bytes exceeds {max_bytes} bytes ({max_mb} MB)."
            )

    @classmethod
    def storage_dir(cls) -> Path:
        base = Path(settings.STORAGE_BASE_PATH)
        directory = base / "documents"
        directory.mkdir(parents=True, exist_ok=True)
        return directory

    @classmethod
    def _path_for_hash(cls, sha256: str) -> Path:
        return cls.storage_dir() / f"{sha256}.pdf"

    @classmethod
    def save(cls, filename: str, mime_type: str, file_bytes: bytes) -> Tuple[str, Path]:
        """Save a validated file to disk.

        Returns (sha256, absolute_file_path). If the file already existed
        (same SHA-256), the path is returned without rewriting the bytes.
        """
        cls.validate_file(filename, mime_type, file_bytes)
        sha256 = cls.compute_sha256(file_bytes)
        target_path = cls._path_for_hash(sha256)

        if not target_path.exists():
            tmp_path = target_path.with_suffix(".part")
            try:
                tmp_path.write_bytes(file_bytes)
                os.replace(tmp_path, target_path)
            except Exception as exc:
                if tmp_path.exists():
                    tmp_path.unlink(missing_ok=True)
                raise ValidationError(f"Failed to store file: {exc}") from exc
            logger.info(
                "file_stored",
                sha256=sha256[:16],
                filename=filename,
                size=len(file_bytes),
            )
        else:
            logger.info(
                "file_deduplicated",
                sha256=sha256[:16],
                filename=filename,
                size=len(file_bytes),
            )

        return sha256, target_path.resolve()

    @staticmethod
    def read_bytes(file_path: str | Path) -> bytes:
        p = Path(file_path)
        if not p.exists():
            raise FileNotFoundError(f"File not found: {p}")
        return p.read_bytes()

    @staticmethod
    def delete(file_path: str | Path) -> bool:
        p = Path(file_path)
        if p.exists():
            p.unlink()
            return True
        return False

    @classmethod
    def exists_for_hash(cls, sha256: str) -> Path | None:
        p = cls._path_for_hash(sha256)
        return p.resolve() if p.exists() else None

    @staticmethod
    def _secure_filename(filename: str) -> str:
        """Strip path separators and control characters."""
        bad = '<>:"/\\|?*\x00\x1f'
        cleaned = "".join(ch for ch in filename if ch not in bad).strip()
        return cleaned or "unnamed.pdf"

    @classmethod
    def clear_storage(cls) -> int:
        """Remove all stored documents. Returns count deleted."""
        directory = cls.storage_dir()
        count = 0
        for child in directory.iterdir():
            if child.is_file():
                child.unlink()
                count += 1
        return count
