"""Unit tests for Analysis schemas (Pydantic validation)."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.schemas.analysis import Analysis, AnalysisOutput, Concept


class TestConceptSchema:
    def test_valid_concept(self):
        c = Concept(
            concept="Regression",
            description="Statistical method for modeling relationships",
            source_pages=[2, 5],
        )
        assert c.concept == "Regression"
        assert c.description.startswith("Statistical")
        assert c.source_pages == [2, 5]

    def test_concept_empty_description_fails(self):
        with pytest.raises(ValidationError):
            Concept(concept="X", description="", source_pages=[])

    def test_concept_empty_name_fails(self):
        with pytest.raises(ValidationError):
            Concept(concept="", description="something")

    def test_concept_defaults(self):
        c = Concept(concept="A", description="desc")
        assert c.source_pages == []


class TestAnalysisOutputSchema:
    @pytest.fixture
    def valid_payload(self):
        return {
            "title": "Intro to ML",
            "subject": "Computer Science",
            "level": "intermediate",
            "language": "es",
            "summary": "Overview of machine learning algorithms.",
            "main_topics": ["Supervised", "Unsupervised"],
            "prerequisites": ["Python", "Stats"],
            "concepts": [
                {
                    "concept": "Supervised Learning",
                    "description": "Learning from labeled data.",
                    "source_pages": [1],
                }
            ],
            "keywords": ["ml", "ai"],
        }

    def test_valid_analysis_output(self, valid_payload):
        result = AnalysisOutput.model_validate(valid_payload)
        assert result.title == "Intro to ML"
        assert result.level == "intermediate"
        assert len(result.concepts) == 1
        assert result.concepts[0].concept == "Supervised Learning"

    def test_analysis_invalid_level_fails(self, valid_payload):
        valid_payload["level"] = "expert"
        with pytest.raises(ValidationError):
            AnalysisOutput.model_validate(valid_payload)

    def test_analysis_missing_title_fails(self, valid_payload):
        del valid_payload["title"]
        with pytest.raises(ValidationError):
            AnalysisOutput.model_validate(valid_payload)

    def test_analysis_blank_title_fails(self, valid_payload):
        valid_payload["title"] = ""
        with pytest.raises(ValidationError):
            AnalysisOutput.model_validate(valid_payload)

    def test_analysis_language_too_long_fails(self, valid_payload):
        valid_payload["language"] = "spanish-is-a-long-value"
        with pytest.raises(ValidationError):
            AnalysisOutput.model_validate(valid_payload)

    def test_analysis_defaults(self):
        minimal = {
            "title": "T",
            "subject": "S",
            "level": "beginner",
            "language": "en",
            "summary": "summary text.",
        }
        result = AnalysisOutput.model_validate(minimal)
        assert result.main_topics == []
        assert result.prerequisites == []
        assert result.concepts == []
        assert result.keywords == []


class TestAnalysisSchema:
    def test_analysis_valid(self):
        a = Analysis(
            title="T",
            subject="S",
            level="advanced",
            language="es",
            summary="Summary of content.",
        )
        assert a.level == "advanced"
        assert a.main_topics == []

    def test_analysis_invalid_level_fails(self):
        with pytest.raises(ValidationError):
            Analysis(
                title="T",
                subject="S",
                level="godlike",
                language="es",
                summary="text",
            )
