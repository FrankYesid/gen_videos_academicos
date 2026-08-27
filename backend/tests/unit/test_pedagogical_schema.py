"""Unit tests for Pedagogical schemas (Pydantic validation)."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.schemas.pedagogical import (
    CommonMistake,
    Example,
    LessonStructureItem,
    PedagogicalDesign,
    PedagogicalOutput,
)


class TestLessonStructureItemSchema:
    def test_valid_structure_item(self):
        item = LessonStructureItem(
            module="Introduction",
            topics=["What is ML?", "History"],
            order=1,
            purpose="Hook students and overview",
            duration_minutes=10,
        )
        assert item.module == "Introduction"
        assert item.order == 1
        assert item.duration_minutes == 10

    def test_order_must_be_positive(self):
        with pytest.raises(ValidationError):
            LessonStructureItem(
                module="X", topics=[], order=0
            )

    def test_defaults(self):
        item = LessonStructureItem(module="A", order=1)
        assert item.topics == []
        assert item.purpose is None
        assert item.duration_minutes is None


class TestExampleSchema:
    def test_valid_example(self):
        e = Example(
            title="Spam detection",
            description="Classify emails using Naive Bayes.",
            explanation="Step 1: tokenize, Step 2: compute priors...",
        )
        assert e.title == "Spam detection"
        assert e.explanation is not None

    def test_optional_explanation(self):
        e = Example(title="X", description="Desc")
        assert e.explanation is None

    def test_missing_title_fails(self):
        with pytest.raises(ValidationError):
            Example(title="", description="Desc")


class TestCommonMistakeSchema:
    def test_valid_mistake(self):
        m = CommonMistake(
            mistake="Overfitting the training data",
            correction="Use cross-validation and regularization.",
            context="During model training.",
        )
        assert m.mistake.startswith("Overfitting")
        assert m.context is not None

    def test_context_optional(self):
        m = CommonMistake(mistake="M", correction="C")
        assert m.context is None


class TestPedagogicalOutputSchema:
    @pytest.fixture
    def valid_payload(self):
        return {
            "general_objective": "Students will understand ML fundamentals.",
            "specific_objectives": [
                "Identify types of ML",
                "Apply classification algorithms",
            ],
            "prerequisites": ["Basic Python", "Statistics"],
            "lesson_structure": [
                {
                    "module": "Intro",
                    "topics": ["Definition", "History"],
                    "order": 1,
                }
            ],
            "examples": [
                {"title": "Spam", "description": "Email classification."}
            ],
            "common_mistakes": [
                {"mistake": "Overfit", "correction": "Use regularization."}
            ],
            "summary": "Structured introduction.",
            "estimated_duration_minutes": 45,
            "activity_suggested": "Group exercise to classify data.",
            "teaching_strategies": ["Active learning", "Think-pair-share"],
            "assessment_methods": ["In-class quiz", "Mini-project"],
        }

    def test_valid_pedagogical_output(self, valid_payload):
        result = PedagogicalOutput.model_validate(valid_payload)
        assert result.general_objective.startswith("Students")
        assert len(result.specific_objectives) == 2
        assert len(result.lesson_structure) == 1
        assert result.lesson_structure[0].order == 1
        assert result.estimated_duration_minutes == 45

    def test_duration_out_of_range_high_fails(self, valid_payload):
        valid_payload["estimated_duration_minutes"] = 300
        with pytest.raises(ValidationError):
            PedagogicalOutput.model_validate(valid_payload)

    def test_duration_zero_fails(self, valid_payload):
        valid_payload["estimated_duration_minutes"] = 0
        with pytest.raises(ValidationError):
            PedagogicalOutput.model_validate(valid_payload)

    def test_specific_objectives_empty_fails(self, valid_payload):
        valid_payload["specific_objectives"] = []
        with pytest.raises(ValidationError):
            PedagogicalOutput.model_validate(valid_payload)

    def test_empty_general_objective_fails(self, valid_payload):
        valid_payload["general_objective"] = ""
        with pytest.raises(ValidationError):
            PedagogicalOutput.model_validate(valid_payload)

    def test_defaults(self):
        minimal = {
            "general_objective": "Learn basics.",
            "specific_objectives": ["Objective 1"],
            "summary": "Summary.",
        }
        result = PedagogicalOutput.model_validate(minimal)
        assert result.prerequisites == []
        assert result.lesson_structure == []
        assert result.examples == []
        assert result.common_mistakes == []
        assert result.estimated_duration_minutes == 10
        assert result.activity_suggested is None
        assert result.teaching_strategies == []
        assert result.assessment_methods == []


class TestPedagogicalDesignSchema:
    def test_valid_pedagogical_design(self):
        d = PedagogicalDesign(
            general_objective="Goal.",
            specific_objectives=["O1"],
            summary="Summary.",
        )
        assert d.general_objective == "Goal."
        assert d.estimated_duration_minutes == 10
