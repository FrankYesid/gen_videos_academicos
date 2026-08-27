from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.agents.base_agent import BaseAgent
from app.core.config import get_settings
from app.core.logging import get_logger
from app.schemas.pedagogical import PedagogicalOutput

logger = get_logger(__name__)
settings = get_settings()


class PedagogicalAgent(BaseAgent):
    """Agent for designing pedagogical structure and learning objectives from academic content."""

    def __init__(self, prompt_version: str | None = None) -> None:
        version = prompt_version or settings.PEDAGOGICAL_PROMPT_VERSION
        super().__init__(name="PedagogicalAgent", prompt_version=version)

    def get_system_prompt(self) -> str:
        """Load and return the system prompt from the prompts file."""
        prompt_path = Path(__file__).parent.parent / "prompts" / "pedagogical.txt"
        try:
            with open(prompt_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as exc:
            logger.error("failed_to_load_pedagogical_prompt", error=str(exc))
            # Fallback prompt
            return """
You are an expert instructional designer. Transform the analyzed academic content into a structured pedagogical design that maximizes learning effectiveness.

Create learning objectives, lesson structure, teaching strategies, examples, common mistakes, and assessment methods based on the provided analysis.
Ensure alignment between objectives, content, activities, and assessment.
"""

    def get_user_prompt(self, input_data: dict[str, Any]) -> str:
        """Generate user prompt based on input data from analysis."""
        analysis = input_data.get("analysis", {})
        title = analysis.get("title", "Unknown Course")
        subject = analysis.get("subject", "Unknown Subject")
        level = analysis.get("level", "intermediate")
        summary = analysis.get("summary", "")
        main_topics = analysis.get("main_topics", [])
        concepts = analysis.get("concepts", [])
        prerequisites = analysis.get("prerequisites", [])
        
        # Format concepts for the prompt
        concepts_text = "\n".join([
            f"- {c.get('concept', '')}: {c.get('description', '')}" 
            for c in concepts[:8]  # Limit to 8 concepts to avoid token limits
        ])
        
        prompt = f"""
Design a comprehensive pedagogical structure for the following course:

**Course Information:**
- Title: {title}
- Subject: {subject}
- Level: {level}
- Summary: {summary}

**Main Topics:**
{', '.join(main_topics[:6])}

**Key Concepts:**
{concepts_text}

**Identified Prerequisites:**
{', '.join(prerequisites)}

Based on this analysis, create a detailed pedagogical design that includes:
1. Clear general and specific learning objectives
2. Structured lesson breakdown with logical sequencing
3. Effective teaching strategies for this content
4. Practical examples and illustrations
5. Common student mistakes and corrections
6. Appropriate assessment methods
7. An engaging learning activity
8. Realistic duration estimation

The design should be appropriate for a {level} level course and consider the identified prerequisites.
"""
        return prompt

    def get_response_schema(self) -> type[PedagogicalOutput]:
        """Return the PedagogicalOutput schema for structured response."""
        return PedagogicalOutput

    def design_pedagogy(
        self,
        db: Session,
        course_id: uuid.UUID,
        analysis_data: dict[str, Any],
    ) -> PedagogicalOutput:
        """Design pedagogical structure based on course analysis."""
        input_data = {
            "analysis": analysis_data,
        }
        
        return self.execute(
            db=db,
            course_id=course_id,
            input_data=input_data,
            max_tokens=4000,  # Allow for detailed pedagogical design
        )