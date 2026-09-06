from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.agents.base_agent import BaseAgent
from app.core.config import get_settings
from app.core.logging import get_logger
from app.schemas.script import ScriptOutput

logger = get_logger(__name__)
settings = get_settings()


class ScriptAgent(BaseAgent):
    """Agent for generating video scripts with scenes, narration, and visual instructions."""

    def __init__(self, prompt_version: str | None = None) -> None:
        version = prompt_version or settings.SCRIPT_PROMPT_VERSION
        super().__init__(name="ScriptAgent", prompt_version=version)

    def get_system_prompt(self) -> str:
        """Load and return the system prompt from the prompts file."""
        prompt_path = Path(__file__).parent.parent / "prompts" / "script.txt"
        try:
            with open(prompt_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as exc:
            logger.error("failed_to_load_script_prompt", error=str(exc))
            # Fallback prompt
            return """
You are an expert video scriptwriter specializing in educational content. Transform the pedagogical design into a comprehensive video script with detailed scenes, narration, and visual instructions.

Create engaging scenes with clear educational purpose, appropriate pacing, and professional visual design.
Ensure the script aligns with learning objectives and maintains viewer engagement throughout.
"""

    def get_user_prompt(self, input_data: dict[str, Any]) -> str:
        """Generate user prompt based on input data from pedagogical design."""
        pedagogical = input_data.get("pedagogical_design", {})
        analysis = input_data.get("analysis", {})
        
        general_objective = pedagogical.get("general_objective", "")
        specific_objectives = pedagogical.get("specific_objectives", [])
        lesson_structure = pedagogical.get("lesson_structure", [])
        examples = pedagogical.get("examples", [])
        common_mistakes = pedagogical.get("common_mistakes", [])
        estimated_duration = pedagogical.get("estimated_duration_minutes", 10)
        teaching_strategies = pedagogical.get("teaching_strategies", [])
        
        title = analysis.get("title", "Unknown Course")
        level = analysis.get("level", "intermediate")
        subject = analysis.get("subject", "Unknown Subject")
        
        # Format lesson structure
        structure_text = "\n".join([
            f"{i+1}. {item.get('module', '')}: {', '.join(item.get('topics', []))} ({item.get('duration_minutes', 10)} min)"
            for i, item in enumerate(lesson_structure[:6])
        ])
        
        # Format objectives
        objectives_text = "\n".join([f"- {obj}" for obj in specific_objectives[:5]])
        
        # Format examples
        examples_text = "\n".join([
            f"- {ex.get('title', '')}: {ex.get('description', '')}"
            for ex in examples[:4]
        ])
        
        prompt = f"""
Create a professional educational video script for the following course:

**Course Information:**
- Title: {title}
- Subject: {subject}
- Level: {level}
- Estimated Duration: {estimated_duration} minutes

**Learning Objectives:**
{objectives_text}

**Lesson Structure:**
{structure_text}

**Teaching Strategies:**
{', '.join(teaching_strategies[:4])}

**Examples to Include:**
{examples_text}

**Common Mistakes to Address:**
{', '.join([mistake.get('mistake', '') for mistake in common_mistakes[:3]])}

Based on this pedagogical design, create a detailed video script that includes:
1. An engaging introduction that hooks viewers and presents objectives
2. 4-8 well-structured scenes covering the main content
3. Clear narration with conversational tone and appropriate pacing
4. Detailed visual instructions for each scene
5. Appropriate on-screen text for key concepts
6. Educational purpose for each scene
7. A memorable conclusion that reinforces learning

Target the script to {level} level learners and use the teaching strategies identified above.
Ensure smooth transitions between scenes and maintain engagement throughout.
"""
        return prompt

    def get_response_schema(self) -> type[ScriptOutput]:
        """Return the ScriptOutput schema for structured response."""
        return ScriptOutput

    async def generate_script(
        self,
        db: Session,
        course_id: uuid.UUID,
        pedagogical_data: dict[str, Any],
        analysis_data: dict[str, Any],
    ) -> ScriptOutput:
        """Generate video script based on pedagogical design and analysis."""
        input_data = {
            "pedagogical_design": pedagogical_data,
            "analysis": analysis_data,
        }
        
        return await self.execute(
            db=db,
            course_id=course_id,
            input_data=input_data,
            max_tokens=4000,  # Allow for detailed script generation
        )