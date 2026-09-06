from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.agents.base_agent import BaseAgent
from app.core.config import get_settings
from app.core.logging import get_logger
from app.schemas.qa import QAOutput

logger = get_logger(__name__)
settings = get_settings()


class QAAgent(BaseAgent):
    """Agent for reviewing educational content quality (QA) before final approval."""

    def __init__(self, prompt_version: str | None = None) -> None:
        version = prompt_version or settings.QA_PROMPT_VERSION
        super().__init__(name="QAAgent", prompt_version=version)

    def get_system_prompt(self) -> str:
        """Load and return the system prompt from the prompts file."""
        prompt_path = Path(__file__).parent.parent / "prompts" / "qa.txt"
        try:
            with open(prompt_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as exc:
            logger.error("failed_to_load_qa_prompt", error=str(exc))
            return """
You are an expert educational content QA reviewer. Evaluate the generated video script, pedagogical design, and analysis. Provide scores 0-100, flag issues (low/medium/high severity categories: narration accuracy, visuals appropriateness, duration pacing, engagement level, pedagogical alignment, clarity, accessibility, completeness). Make approved if score>=QA_MIN_SCORE or rejected. Include list of string recommendations for improvement. Always follow JSON structure.
"""

    def get_user_prompt(self, input_data: dict[str, Any]) -> str:
        """Generate user prompt based on input data from script, analysis, and pedagogical design."""
        analysis = input_data.get("analysis", {})
        pedagogical_design = input_data.get("pedagogical_design", {})
        script = input_data.get("script", {})
        video_metadata = input_data.get("video_metadata", {})
        qa_min_score = input_data.get("qa_min_score", 80)

        title = analysis.get("title", "Unknown Course")
        objectives = pedagogical_design.get("specific_objectives", [])
        script_scenes = script.get("scenes", [])
        scenes_count = len(script_scenes)
        intro = script.get("introduction", "")
        conclusion = script.get("conclusion", "")
        video_url = video_metadata.get("url", "N/A")
        video_duration = video_metadata.get("duration", "N/A")

        objectives_text = "\n".join([f"- {obj}" for obj in objectives[:5]])
        prompt = f"""
Please perform a comprehensive QA review on the following educational video content:

**Course Information:**
- Course Title: {title}
- Video URL: {video_url}
- Video Duration: {video_duration}
- Total Scenes: {scenes_count}

**Learning Objectives:**
{objectives_text}

**Script Introduction:**
{intro}

**Script Conclusion:**
{conclusion}

**Evaluation Criteria (score 0-100):**
1. Narration accuracy - factual correctness and script quality
2. Visuals appropriateness - visual instructions and scene descriptions
3. Duration pacing - appropriate timing per scene and overall
4. Engagement level - ability to maintain student interest
5. Pedagogical alignment - alignment with learning objectives
6. Clarity - explainability and logical flow
7. Accessibility - language and content accessibility
8. Completeness - covers all required topics

**QA Minimum Score Threshold:**
Score must be >= {qa_min_score} for status "approved", otherwise status is "rejected".

Provide a detailed QA review following the JSON structure, including:
- Overall score (0-100)
- Approved/rejected status
- List of issues with category, severity (low/medium/high), description, optional suggestion and scene_id
- List of general recommendations for improvement
- Executive summary of the review
"""
        return prompt

    def get_response_schema(self) -> type[QAOutput]:
        """Return the QAOutput schema for structured response."""
        return QAOutput

    async def run_qa(
        self,
        db: Session,
        course_id: uuid.UUID,
        qa_min_score: int = 80,
        analysis_data: dict[str, Any] | None = None,
        pedagogical_data: dict[str, Any] | None = None,
        script_data: dict[str, Any] | None = None,
        video_metadata: dict[str, Any] | None = None,
    ) -> QAOutput:
        """Execute QA review on course content."""
        input_data = {
            "analysis": analysis_data or {},
            "pedagogical_design": pedagogical_data or {},
            "script": script_data or {},
            "video_metadata": video_metadata or {},
            "qa_min_score": qa_min_score,
        }

        return await self.execute(
            db=db,
            course_id=course_id,
            input_data=input_data,
            max_tokens=4000,
        )
