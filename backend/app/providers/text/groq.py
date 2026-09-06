from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import get_settings
from app.core.exceptions import AIServiceError
from app.core.logging import get_logger
from app.providers.text.base import TextGenerationProvider

logger = get_logger(__name__)
settings = get_settings()

try:
    from groq import Groq as _GroqClient
    _HAS_GROQ = True
except ImportError:
    _GroqClient = None  # type: ignore[assignment]
    _HAS_GROQ = False


class GroqProvider(TextGenerationProvider):
    """Groq provider for text generation with structured outputs."""

    def __init__(self) -> None:
        if not settings.GROQ_API_KEY:
            raise AIServiceError("GROQ_API_KEY is not configured")
        if not _HAS_GROQ:
            raise AIServiceError(
                "groq package is not installed. Install with: pip install groq"
            )

        self.client = _GroqClient(api_key=settings.GROQ_API_KEY)
        self.model = settings.GROQ_MODEL
        self.temperature = settings.GROQ_TEMPERATURE

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        max_tokens: int | None = None,
        temperature: float = 0.2,
        **kwargs: Any,
    ) -> str:
        """Generate text response from a prompt."""
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            params: dict[str, Any] = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
            }

            if max_tokens:
                params["max_tokens"] = max_tokens

            response = self.client.chat.completions.create(**params)
            return response.choices[0].message.content or ""

        except Exception as exc:
            logger.error("groq_generation_failed", error=str(exc))
            raise AIServiceError(f"Groq API error: {exc}") from exc

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    async def generate_structured(
        self,
        prompt: str,
        response_schema: type[BaseModel],
        system_prompt: str | None = None,
        max_tokens: int | None = None,
        temperature: float = 0.2,
        **kwargs: Any,
    ) -> BaseModel:
        """Generate structured response using a Pydantic schema."""
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            
            # Add JSON schema instruction to the prompt
            json_schema = json.dumps(response_schema.model_json_schema(), indent=2)
            structured_prompt = f"""
Please respond with valid JSON that matches this schema:

{json_schema}

Your response:
{prompt}
"""
            messages.append({"role": "user", "content": structured_prompt})

            params: dict[str, Any] = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "response_format": {"type": "json_object"},
            }

            if max_tokens:
                params["max_tokens"] = max_tokens

            response = self.client.chat.completions.create(**params)
            content = response.choices[0].message.content or ""

            # Parse and validate JSON response
            parsed_data = json.loads(content)
            return response_schema.model_validate(parsed_data)

        except Exception as exc:
            logger.error("groq_structured_generation_failed", error=str(exc))
            raise AIServiceError(f"Groq structured generation failed: {exc}") from exc

    def is_configured(self) -> bool:
        """Check if Groq provider is properly configured."""
        return bool(settings.GROQ_API_KEY) and _HAS_GROQ


class MockGroqProvider(TextGenerationProvider):
    """Mock Groq provider for testing without API calls."""

    def __init__(self) -> None:
        logger.warning("Using MockGroqProvider - no real API calls will be made")

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        max_tokens: int | None = None,
        temperature: float = 0.2,
        **kwargs: Any,
    ) -> str:
        """Return mock text response."""
        return "This is a mock response from the Groq provider."

    async def generate_structured(
        self,
        prompt: str,
        response_schema: type[BaseModel],
        system_prompt: str | None = None,
        max_tokens: int | None = None,
        temperature: float = 0.2,
        **kwargs: Any,
    ) -> BaseModel:
        """Return mock structured data based on the schema."""
        try:
            from app.schemas.analysis import AnalysisOutput, Concept
            from app.schemas.pedagogical import (
                PedagogicalOutput,
                LessonStructureItem,
                Example,
                CommonMistake,
            )
            from app.schemas.script import ScriptOutput, Scene
        except ImportError:
            return response_schema()

        if response_schema.__name__ == "AnalysisOutput":
            return AnalysisOutput(
                title="Machine Learning Fundamentals",
                subject="Computer Science",
                level="intermediate",
                language="es",
                summary="Introduction to core machine learning concepts and algorithms.",
                main_topics=[
                    "Supervised Learning",
                    "Unsupervised Learning",
                    "Neural Networks",
                    "Model Evaluation"
                ],
                concepts=[
                    Concept(
                        concept="Supervised Learning",
                        description="Learning from labeled data to make predictions",
                        source_pages=[1, 2]
                    ),
                    Concept(
                        concept="Unsupervised Learning",
                        description="Finding patterns in unlabeled data",
                        source_pages=[3, 4]
                    )
                ],
                prerequisites=["Basic Python", "Linear Algebra", "Statistics"],
                keywords=["machine learning", "AI", "algorithms", "data science"]
            )

        if response_schema.__name__ == "PedagogicalOutput":
            return PedagogicalOutput(
                general_objective="Students will understand fundamental machine learning concepts and be able to apply basic algorithms to solve problems.",
                specific_objectives=[
                    "Identify and explain different types of machine learning algorithms",
                    "Apply supervised learning techniques to classification problems",
                    "Evaluate model performance using appropriate metrics",
                    "Understand the ethical implications of ML applications"
                ],
                prerequisites=["Basic Python programming", "Linear algebra fundamentals", "Statistics basics"],
                lesson_structure=[
                    LessonStructureItem(
                        module="Introduction to Machine Learning",
                        topics=["ML definition", "Types of ML", "ML applications"],
                        order=1,
                        purpose="Provide overview and context",
                        duration_minutes=15
                    ),
                    LessonStructureItem(
                        module="Supervised Learning",
                        topics=["Classification", "Regression", "Algorithms"],
                        order=2,
                        purpose="Core ML concepts",
                        duration_minutes=25
                    ),
                    LessonStructureItem(
                        module="Model Evaluation",
                        topics=["Metrics", "Cross-validation", "Overfitting"],
                        order=3,
                        purpose="Assessment techniques",
                        duration_minutes=20
                    )
                ],
                examples=[
                    Example(
                        title="Email Spam Classification",
                        description="Using Naive Bayes to classify emails as spam or not spam",
                        explanation="Shows practical application of classification algorithms"
                    ),
                    Example(
                        title="House Price Prediction",
                        description="Using linear regression to predict house prices based on features",
                        explanation="Demonstrates regression techniques"
                    )
                ],
                common_mistakes=[
                    CommonMistake(
                        mistake="Overfitting the training data",
                        correction="Use cross-validation and regularization techniques",
                        context="When models perform well on training data but poorly on new data"
                    ),
                    CommonMistake(
                        mistake="Ignoring data preprocessing",
                        correction="Always clean, normalize, and explore data before modeling",
                        context="Skipping essential data preparation steps"
                    )
                ],
                summary="This lesson uses a combination of theoretical explanations, practical examples, and hands-on exercises to build foundational ML knowledge.",
                estimated_duration_minutes=60,
                activity_suggested="Students will work in small groups to implement a simple classification algorithm using provided datasets.",
                teaching_strategies=["Active learning", "Collaborative problem-solving", "Formative assessment"],
                assessment_methods=["In-class exercises", "Group project", "Final quiz"]
            )

        if response_schema.__name__ == "ScriptOutput":
            return ScriptOutput(
                title="Machine Learning Fundamentals - Educational Video",
                scenes=[
                    Scene(
                        id=1,
                        title="Introduction to Machine Learning",
                        duration_seconds=45,
                        narration="Welcome to this comprehensive introduction to machine learning. In this video, we'll explore the fundamental concepts that power AI systems all around us.",
                        visual_instruction="Opening shot with montage of ML applications. Title appears with animated text effect.",
                        on_screen_text="What is Machine Learning?",
                        educational_purpose="Hook viewer interest and establish context",
                        camera_angle="Medium shot with dynamic camera movement",
                        background="Modern tech office with AI visualization screens",
                        audio_cue="Upbeat, modern electronic background music"
                    ),
                    Scene(
                        id=2,
                        title="Types of Machine Learning",
                        duration_seconds=60,
                        narration="Machine learning isn't just one thing - it's actually several different approaches. The three main types are supervised learning, unsupervised learning, and reinforcement learning.",
                        visual_instruction="Split screen showing three columns with icons for each ML type.",
                        on_screen_text="Supervised • Unsupervised • Reinforcement",
                        educational_purpose="Categorize ML approaches and provide overview",
                        camera_angle="Wide shot with text overlays",
                        background="Clean gradient background with animated icons",
                        audio_cue="Soft transition sound between sections"
                    )
                ],
                total_duration_seconds=105,
                introduction="Welcome to this comprehensive introduction to machine learning. Today we'll explore the fundamental concepts that power AI systems all around us.",
                conclusion="Machine learning is transforming how we solve complex problems. As you continue your journey, you'll discover even more powerful techniques and applications.",
                target_audience="Beginner to intermediate learners interested in AI and data science",
                tone="educational and engaging",
                notes="Ensure smooth transitions between scenes. Use consistent color coding for related concepts."
            )

        return response_schema()

    def is_configured(self) -> bool:
        """Mock provider is always configured."""
        return True


def get_groq_provider() -> TextGenerationProvider:
    """Factory function to get the appropriate Groq provider."""
    if not GroqProvider.is_configured():
        logger.warning("Groq not configured, using mock provider")
        return MockGroqProvider()
    return GroqProvider()
