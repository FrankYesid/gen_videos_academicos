from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.agents.base_agent import BaseAgent
from app.core.config import get_settings
from app.core.logging import get_logger
from app.schemas.analysis import AnalysisOutput

logger = get_logger(__name__)
settings = get_settings()


class AnalyzerAgent(BaseAgent):
    """Agent for analyzing academic PDF content and extracting structured information."""

    def __init__(self, prompt_version: str | None = None) -> None:
        version = prompt_version or settings.ANALYZER_PROMPT_VERSION
        super().__init__(name="AnalyzerAgent", prompt_version=version)

    def get_system_prompt(self) -> str:
        """Load and return the system prompt from the prompts file."""
        prompt_path = Path(__file__).parent.parent / "prompts" / "analyzer.txt"
        try:
            with open(prompt_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as exc:
            logger.error("failed_to_load_analyzer_prompt", error=str(exc))
            # Fallback prompt
            return """
You are an expert academic content analyzer. Analyze the provided text and extract structured information including title, subject, level, summary, topics, concepts, and keywords.
Be accurate, faithful to the source text, and maintain academic standards.
"""

    def get_user_prompt(self, input_data: dict[str, Any]) -> str:
        """Generate user prompt based on input data."""
        text = input_data.get("text", "")
        filename = input_data.get("filename", "unknown")
        page_count = input_data.get("page_count", 0)
        
        prompt = f"""
Please analyze the following academic content from the document "{filename}" ({page_count} pages):

{text[:15000]}  # Limit to first 15000 characters to avoid token limits

Provide a comprehensive analysis following the guidelines in the system prompt.
"""
        return prompt

    def get_response_schema(self) -> type[AnalysisOutput]:
        """Return the AnalysisOutput schema for structured response."""
        return AnalysisOutput

    def analyze_document(
        self,
        db: Session,
        course_id: uuid.UUID,
        document_text: str,
        filename: str,
        page_count: int,
    ) -> AnalysisOutput:
        """Analyze a document and return structured analysis."""
        input_data = {
            "text": document_text,
            "filename": filename,
            "page_count": page_count,
        }
        
        return self.execute(
            db=db,
            course_id=course_id,
            input_data=input_data,
            max_tokens=4000,  # Allow for detailed structured output
        )