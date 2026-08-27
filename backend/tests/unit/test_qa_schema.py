"""Unit tests for QA schemas (Pydantic validation)."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.schemas.qa import QAIssue, QAOutput, QAResult


class TestQAIssueSchema:
    def test_valid_qa_issue(self):
        issue = QAIssue(
            category="narration accuracy",
            severity="medium",
            description="La narración contiene errores gramaticales en la sección 2",
            suggestion="Revisar la redacción de la narración",
            scene_id=1,
        )
        assert issue.category == "narration accuracy"
        assert issue.severity == "medium"
        assert issue.description.startswith("La narración")
        assert issue.suggestion is not None
        assert issue.scene_id == 1

    def test_qa_issue_missing_description_fails(self):
        with pytest.raises(ValidationError):
            QAIssue(
                category="visuals appropriateness",
                severity="low",
                description="",
            )

    def test_qa_issue_invalid_severity_fails(self):
        with pytest.raises(ValidationError):
            QAIssue(
                category="clarity",
                severity="critical",
                description="Descripción del problema",
            )

    def test_qa_issue_valid_severity_low(self):
        issue = QAIssue(
            category="engagement level",
            severity="low",
            description="Poco compromiso visual",
        )
        assert issue.severity == "low"

    def test_qa_issue_valid_severity_high(self):
        issue = QAIssue(
            category="pedagogical alignment",
            severity="high",
            description="Contenido no alineado con objetivos",
        )
        assert issue.severity == "high"

    def test_qa_issue_defaults(self):
        issue = QAIssue(
            category="completeness",
            severity="medium",
            description="Falta contenido sobre el tema X",
        )
        assert issue.suggestion is None
        assert issue.scene_id is None


class TestQAOutputSchema:
    def test_qa_output_score_zero_valid(self):
        output = QAOutput(
            score=0,
            status="rejected",
        )
        assert output.score == 0
        assert output.status == "rejected"

    def test_qa_output_score_hundred_valid(self):
        output = QAOutput(
            score=100,
            status="approved",
        )
        assert output.score == 100
        assert output.status == "approved"

    def test_qa_output_score_negative_fails(self):
        with pytest.raises(ValidationError):
            QAOutput(
                score=-1,
                status="rejected",
            )

    def test_qa_output_score_over_hundred_fails(self):
        with pytest.raises(ValidationError):
            QAOutput(
                score=101,
                status="approved",
            )

    def test_qa_output_invalid_status_fails(self):
        with pytest.raises(ValidationError):
            QAOutput(
                score=80,
                status="pending",
            )

    def test_qa_output_defaults_qa_version(self):
        output = QAOutput(
            score=75,
            status="rejected",
        )
        assert output.qa_version == "1.0"

    def test_qa_output_approved_status(self):
        output = QAOutput(
            score=90,
            status="approved",
        )
        assert output.status == "approved"

    def test_qa_output_rejected_status(self):
        output = QAOutput(
            score=50,
            status="rejected",
        )
        assert output.status == "rejected"

    def test_qa_output_full_payload(self):
        issues = [
            QAIssue(
                category="clarity",
                severity="medium",
                description="Ejemplo confuso",
            )
        ]
        output = QAOutput(
            score=85,
            status="approved",
            issues=issues,
            recommendations=["Mejorar introducción"],
            summary="Buen curso en general",
            approved_at="2026-08-23T10:00:00Z",
            qa_version="1.0",
        )
        assert len(output.issues) == 1
        assert output.issues[0].category == "clarity"
        assert len(output.recommendations) == 1
        assert output.summary == "Buen curso en general"
        assert output.approved_at is not None


class TestQAResultSchema:
    def test_qa_result_valid(self):
        result = QAResult(
            score=85,
            status="approved",
        )
        assert result.score == 85
        assert result.status == "approved"
        assert result.issues == []
        assert result.recommendations == []
        assert result.summary is None
