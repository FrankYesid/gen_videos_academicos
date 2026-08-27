"""Unit tests for MockOpenAIService outputs and agent prompt construction."""
from __future__ import annotations

import pytest

from app.schemas.analysis import AnalysisOutput, Concept
from app.schemas.pedagogical import PedagogicalOutput
from app.services.openai_service import MockOpenAIService


class TestMockOpenAIService:
    def setup_method(self):
        self.service = MockOpenAIService()

    def test_is_configured_true(self):
        assert MockOpenAIService.is_configured() is True

    def test_structured_completion_analysis_output(self):
        result = self.service.structured_completion(
            messages=[{"role": "user", "content": "test"}],
            response_schema=AnalysisOutput,
        )
        assert isinstance(result, AnalysisOutput)
        assert result.title == "Machine Learning Fundamentals"
        assert result.subject == "Computer Science"
        assert result.level == "intermediate"
        assert result.language == "es"
        assert len(result.concepts) > 0
        assert all(isinstance(c, Concept) for c in result.concepts)
        assert len(result.main_topics) > 0
        assert len(result.prerequisites) > 0
        assert len(result.keywords) > 0

    def test_structured_completion_pedagogical_output(self):
        result = self.service.structured_completion(
            messages=[{"role": "user", "content": "test"}],
            response_schema=PedagogicalOutput,
        )
        assert isinstance(result, PedagogicalOutput)
        assert len(result.general_objective) > 0
        assert len(result.specific_objectives) >= 3
        assert len(result.lesson_structure) >= 3
        assert result.lesson_structure[0].order == 1
        assert len(result.examples) >= 2
        assert len(result.common_mistakes) >= 2
        assert result.estimated_duration_minutes >= 1
        assert result.estimated_duration_minutes <= 180
        assert len(result.teaching_strategies) > 0
        assert len(result.assessment_methods) > 0

    def test_simple_completion_returns_string(self):
        result = self.service.simple_completion("sys", "user")
        assert isinstance(result, str)
        assert len(result) > 0


class TestAnalyzerAgentPrompts:
    def test_get_system_prompt(self):
        from app.agents.analyzer_agent import AnalyzerAgent

        agent = AnalyzerAgent()
        prompt = agent.get_system_prompt()
        assert isinstance(prompt, str)
        assert len(prompt) > 50

    def test_get_user_prompt(self):
        from app.agents.analyzer_agent import AnalyzerAgent

        agent = AnalyzerAgent()
        input_data = {
            "text": "This is an academic document about linear algebra and matrices.",
            "filename": "math_notes.pdf",
            "page_count": 12,
        }
        prompt = agent.get_user_prompt(input_data)
        assert "math_notes.pdf" in prompt
        assert "12" in prompt
        assert "linear algebra" in prompt

    def test_response_schema(self):
        from app.agents.analyzer_agent import AnalyzerAgent
        from app.schemas.analysis import AnalysisOutput

        agent = AnalyzerAgent()
        assert agent.get_response_schema() is AnalysisOutput


class TestPedagogicalAgentPrompts:
    def test_get_system_prompt(self):
        from app.agents.pedagogical_agent import PedagogicalAgent

        agent = PedagogicalAgent()
        prompt = agent.get_system_prompt()
        assert isinstance(prompt, str)
        assert len(prompt) > 50

    def test_get_user_prompt(self):
        from app.agents.pedagogical_agent import PedagogicalAgent

        agent = PedagogicalAgent()
        analysis_data = {
            "title": "Intro to ML",
            "subject": "CS",
            "level": "intermediate",
            "summary": "ML basics.",
            "main_topics": ["Supervised", "Unsupervised"],
            "concepts": [
                {"concept": "Regression", "description": "Modeling."},
                {"concept": "Classification", "description": "Labels."},
            ],
            "prerequisites": ["Python"],
        }
        prompt = agent.get_user_prompt({"analysis": analysis_data})
        assert "Intro to ML" in prompt
        assert "intermediate" in prompt
        assert "Regression" in prompt

    def test_response_schema(self):
        from app.agents.pedagogical_agent import PedagogicalAgent
        from app.schemas.pedagogical import PedagogicalOutput

        agent = PedagogicalAgent()
        assert agent.get_response_schema() is PedagogicalOutput
