from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.core.exceptions import DocumentExtractionError
from app.core.logging import get_logger

logger = get_logger(__name__)

try:
    import fitz  # PyMuPDF
except Exception:  # pragma: no cover
    fitz = None  # type: ignore[assignment]


@dataclass
class ExtractionResult:
    page_count: int
    text: str
    language: str | None = None
    metadata: dict | None = None


class ExtractionService:
    """Extracts text and metadata from PDF files using PyMuPDF."""

    @classmethod
    def _ensure_fitz(cls) -> None:
        if fitz is None:
            raise DocumentExtractionError(
                "PyMuPDF is not installed. Install with: pip install PyMuPDF"
            )

    @classmethod
    def extract(cls, file_path: str | Path) -> ExtractionResult:
        cls._ensure_fitz()
        p = Path(file_path)
        if not p.exists():
            raise DocumentExtractionError(f"PDF not found: {p}")
        if p.stat().st_size == 0:
            raise DocumentExtractionError("PDF file is empty (0 bytes).")

        try:
            doc = fitz.open(p)  # type: ignore[union-attr]
        except Exception as exc:
            raise DocumentExtractionError(
                f"Failed to open PDF (invalid/corrupt): {exc}"
            ) from exc

        try:
            page_count = doc.page_count
            chunks: list[str] = []
            for page in doc:
                try:
                    txt = page.get_text("text") or ""
                    chunks.append(txt)
                except Exception as exc:
                    logger.warning(
                        "pdf_page_extraction_failed",
                        page_number=page.number + 1,
                        error=str(exc),
                    )
                    chunks.append("")

            text = "\n\n".join(chunks).strip()

            if not text:
                raise DocumentExtractionError(
                    "PDF does not contain extractable text. It may be a scanned image; OCR is not yet implemented in the MVP."
                )

            metadata = dict(doc.metadata or {})
            language: str | None = None
            if metadata:
                language = metadata.get("language") or None

            return ExtractionResult(
                page_count=page_count,
                text=text,
                language=language,
                metadata=metadata,
            )
        finally:
            doc.close()

    @classmethod
    def estimate_pages(cls, file_bytes: bytes) -> int | None:
        """Fast (but approximate) page count by parsing bytes without disk I/O.

        Returns None if count cannot be determined.
        """
        if not file_bytes:
            return None
        try:
            import re

            matches = re.findall(rb"/Type\s*/Page[^s]", file_bytes)
            if matches:
                return len(matches)
        except Exception:
            pass
        return None
