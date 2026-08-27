from __future__ import annotations

import json
from typing import Any, TypeVar

from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import get_settings
from app.core.exceptions import AIServiceError
from app.core.logging import get_logger


def _normalize_json_schema_for_openai(schema: dict[str, Any]) -> dict[str, Any]:
    """Mutates and returns the schema so that OpenAI ``strict: true`` accepts it.

    OpenAI rules for ``response_format.json_schema`` with ``strict: true``:
      1. Every ``type: object`` MUST declare ``additionalProperties: false``.
      2. Every ``type: object`` MUST list ALL its properties inside ``required``,
         even properties that have defaults / default factories.
      3. Nested ``$defs`` (and any other inner schemas) also must comply with 1 & 2.
    """
    def _walk(node: Any) -> None:
        if isinstance(node, dict):
            if node.get("type") == "object":
                node["additionalProperties"] = False
                props = node.get("properties")
                if isinstance(props, dict):
                    node["required"] = sorted(props.keys())
                    for value in props.values():
                        _walk(value)
            # Handle top-level / non-object containers that still have defs/props.
            if "items" in node:
                _walk(node["items"])
            for key in ("anyOf", "oneOf", "allOf"):
                if key in node and isinstance(node[key], list):
                    for sub in node[key]:
                        _walk(sub)
            if "$defs" in node and isinstance(node["$defs"], dict):
                for value in node["$defs"].values():
                    _walk(value)
        elif isinstance(node, list):
            for item in node:
                _walk(item)

    _walk(schema)
    return schema

settings = get_settings()
logger = get_logger(__name__)

T = TypeVar("T", bound=BaseModel)

try:
    from openai import OpenAI as _OpenAIClient

    _HAS_OPENAI = True
except ImportError:  # pragma: no cover
    _OpenAIClient = None  # type: ignore[assignment]
    _HAS_OPENAI = False


class OpenAIService:
    """Service for interacting with OpenAI API with structured outputs."""

    def __init__(self) -> None:
        if not settings.OPENAI_API_KEY:
            raise AIServiceError("OPENAI_API_KEY is not configured")
        if not _HAS_OPENAI:  # pragma: no cover
            raise AIServiceError(
                "openai package is not installed. Install backend/requirements.txt."
            )

        self.client = _OpenAIClient(
            api_key=settings.OPENAI_API_KEY,
            timeout=60.0,
        )
        self.model = settings.OPENAI_MODEL
        self.temperature = settings.OPENAI_TEMPERATURE

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    def chat_completion(
        self,
        messages: list[dict[str, str]],
        response_format: dict[str, Any] | None = None,
        max_tokens: int | None = None,
    ) -> dict[str, Any]:
        """Basic chat completion with optional structured output."""
        try:
            params: dict[str, Any] = {
                "model": self.model,
                "messages": messages,
                "temperature": self.temperature,
            }
            
            if response_format:
                params["response_format"] = response_format
            
            if max_tokens:
                params["max_tokens"] = max_tokens

            response = self.client.chat.completions.create(**params)
            
            return response.model_dump()
            
        except Exception as exc:
            logger.error("openai_completion_failed", error=str(exc))
            raise AIServiceError(f"OpenAI API error: {exc}") from exc

    def structured_completion(
        self,
        messages: list[dict[str, str]],
        response_schema: type[T],
        max_tokens: int | None = None,
    ) -> T:
        """Chat completion with structured output using JSON Schema."""
        try:
            # Convert Pydantic model to JSON Schema and normalize for OpenAI strict rules
            schema = _normalize_json_schema_for_openai(response_schema.model_json_schema())

            # Use OpenAI's structured output format
            response_format = {
                "type": "json_schema",
                "json_schema": {
                    "name": response_schema.__name__,
                    "strict": True,
                    "schema": schema,
                },
            }
            
            response = self.chat_completion(
                messages=messages,
                response_format=response_format,
                max_tokens=max_tokens,
            )
            
            # Extract and parse the structured response
            content = response["choices"][0]["message"]["content"]
            parsed_data = json.loads(content)
            
            # Validate and return Pydantic model
            return response_schema.model_validate(parsed_data)
            
        except Exception as exc:
            logger.error("structured_completion_failed", error=str(exc))
            raise AIServiceError(f"Structured completion failed: {exc}") from exc

    def simple_completion(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int | None = None,
    ) -> str:
        """Simple completion for text-only responses."""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        
        response = self.chat_completion(messages, max_tokens=max_tokens)
        return response["choices"][0]["message"]["content"]

    @staticmethod
    def is_configured() -> bool:
        """Check if OpenAI service is properly configured."""
        return bool(settings.OPENAI_API_KEY)


class MockOpenAIService:
    """Mock OpenAI service for testing without API calls."""

    def __init__(self) -> None:
        logger.warning("Using MockOpenAIService - no real API calls will be made")

    def structured_completion(
        self,
        messages: list[dict[str, str]],
        response_schema: type[T],
        max_tokens: int | None = None,
    ) -> T:
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
            # Fallback if schemas not available
            return response_schema()
        
        if response_schema.__name__ == "AnalysisOutput":
            # Return mock analysis data
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
            # Return mock pedagogical data
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
            # Return mock script data
            from app.schemas.script import Scene
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
                    ),
                    Scene(
                        id=3,
                        title="How Supervised Learning Works",
                        duration_seconds=90,
                        narration="Let's dive deeper into supervised learning, the most common type we encounter. Imagine you're teaching a child to recognize different animals - you show them pictures of cats and dogs, labeling each one.",
                        visual_instruction="Animation showing data points being classified. Color-coded points move to their respective categories.",
                        on_screen_text="Learning from Labeled Examples",
                        educational_purpose="Explain supervised learning with relatable analogy",
                        camera_angle="Close-up on animation with text callouts",
                        background="Dark background with bright, colorful data visualization",
                        audio_cue="Gentle, encouraging background music"
                    ),
                    Scene(
                        id=4,
                        title="Real-World Applications",
                        duration_seconds=60,
                        narration="The applications of supervised learning are everywhere. Email spam filters, recommendation engines, and medical diagnosis systems all use this technology.",
                        visual_instruction="Rapid montage of real applications with ML processing visualization.",
                        on_screen_text="Email • Recommendations • Healthcare",
                        educational_purpose="Show practical relevance and applications",
                        camera_angle="Medium shots with smooth transitions",
                        background="Varied backgrounds matching each application context",
                        audio_cue="Dynamic, energetic music during montage"
                    ),
                    Scene(
                        id=5,
                        title="Key Takeaways and Next Steps",
                        duration_seconds=45,
                        narration="To wrap up, supervised learning learns from labeled examples to make predictions, it's incredibly versatile and powers many applications we use daily.",
                        visual_instruction="Summary graphic with key points. End screen appears with resources and next steps.",
                        on_screen_text="Keep Learning!",
                        educational_purpose="Reinforce main concepts and provide closure",
                        camera_angle="Medium shot on summary graphic",
                        background="Inspiring gradient background with upward motion graphics",
                        audio_cue="Inspiring, forward-looking music"
                    )
                ],
                total_duration_seconds=300,
                introduction="Welcome to this comprehensive introduction to machine learning. Today we'll explore the fundamental concepts that power AI systems all around us.",
                conclusion="Machine learning is transforming how we solve complex problems. As you continue your journey, you'll discover even more powerful techniques and applications.",
                target_audience="Beginner to intermediate learners interested in AI and data science",
                tone="educational and engaging",
                notes="Ensure smooth transitions between scenes. Use consistent color coding for related concepts."
            )
        
        if response_schema.__name__ == "QAOutput":
            from app.schemas.qa import QAIssue, QAOutput
            return QAOutput(
                score=90,
                status="approved",
                issues=[
                    QAIssue(
                        category="narration accuracy",
                        severity="low",
                        description="Minor typo in scene 3 narration",
                        suggestion="Fix punctuation in paragraph 2",
                        scene_id=3,
                    )
                ],
                recommendations=[
                    "Consider adding more visual examples in concept explanation section",
                    "Slightly reduce scene 2 duration to improve pacing",
                ],
                summary="Overall high quality script with excellent pedagogical alignment and engaging narration",
                qa_version="1.0",
            )

        # For other schemas, return a basic instance
        return response_schema()

    def simple_completion(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int | None = None,
    ) -> str:
        """Return mock text response."""
        return "This is a mock response from the OpenAI service."

    @staticmethod
    def is_configured() -> bool:
        """Mock service is always configured."""
        return True


def get_openai_service() -> OpenAIService | MockOpenAIService:
    """Factory function to get the appropriate OpenAI service."""
    if not OpenAIService.is_configured():
        logger.warning("OpenAI not configured, using mock service")
        return MockOpenAIService()
    return OpenAIService()
