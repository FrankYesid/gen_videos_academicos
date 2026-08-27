"""Unit tests for course workflow state transitions and statuses."""
from __future__ import annotations

import pytest

from app.models.course import CourseStatus


class TestCourseStatus:
    def test_all_statuses_present(self):
        expected = {
            "CREATED",
            "UPLOADED",
            "EXTRACTING",
            "ANALYZING",
            "PEDAGOGICAL_DESIGN",
            "SCRIPT_GENERATED",
            "SCRIPT_VALIDATED",
            "VIDEO_GENERATING",
            "VIDEO_PROCESSING",
            "VIDEO_READY",
            "QA",
            "COMPLETED",
            "FAILED",
        }
        assert set(CourseStatus.all()) == expected

    @pytest.mark.parametrize(
        "from_status,to_status,expected",
        [
            # Phase 1-2 transitions
            (CourseStatus.CREATED, CourseStatus.UPLOADED, True),
            (CourseStatus.CREATED, CourseStatus.FAILED, True),
            (CourseStatus.CREATED, CourseStatus.ANALYZING, False),
            # Extraction -> Analyzing
            (CourseStatus.EXTRACTING, CourseStatus.ANALYZING, True),
            (CourseStatus.EXTRACTING, CourseStatus.FAILED, True),
            (CourseStatus.EXTRACTING, CourseStatus.COMPLETED, False),
            # Analyzing -> Pedagogical (Fase 3)
            (CourseStatus.ANALYZING, CourseStatus.PEDAGOGICAL_DESIGN, True),
            (CourseStatus.ANALYZING, CourseStatus.FAILED, True),
            (CourseStatus.ANALYZING, CourseStatus.SCRIPT_GENERATED, False),
            # Pedagogical -> Script (Fase 4)
            (CourseStatus.PEDAGOGICAL_DESIGN, CourseStatus.SCRIPT_GENERATED, True),
            (CourseStatus.PEDAGOGICAL_DESIGN, CourseStatus.FAILED, True),
            (CourseStatus.PEDAGOGICAL_DESIGN, CourseStatus.ANALYZING, False),
            # Script -> Validation
            (CourseStatus.SCRIPT_GENERATED, CourseStatus.SCRIPT_VALIDATED, True),
            (CourseStatus.SCRIPT_GENERATED, CourseStatus.PEDAGOGICAL_DESIGN, True),
            (CourseStatus.SCRIPT_GENERATED, CourseStatus.FAILED, True),
            # Video pipeline
            (CourseStatus.SCRIPT_VALIDATED, CourseStatus.VIDEO_GENERATING, True),
            (CourseStatus.SCRIPT_VALIDATED, CourseStatus.SCRIPT_GENERATED, True),
            (CourseStatus.VIDEO_GENERATING, CourseStatus.VIDEO_PROCESSING, True),
            (CourseStatus.VIDEO_PROCESSING, CourseStatus.VIDEO_READY, True),
            (CourseStatus.VIDEO_READY, CourseStatus.QA, True),
            # QA -> Completed
            (CourseStatus.QA, CourseStatus.COMPLETED, True),
            (CourseStatus.QA, CourseStatus.SCRIPT_GENERATED, True),
            # Terminal states
            (CourseStatus.COMPLETED, CourseStatus.ANALYZING, False),
            (CourseStatus.COMPLETED, CourseStatus.COMPLETED, False),
            # FAILED -> retry states
            (CourseStatus.FAILED, CourseStatus.UPLOADED, True),
            (CourseStatus.FAILED, CourseStatus.EXTRACTING, True),
            (CourseStatus.FAILED, CourseStatus.ANALYZING, True),
            (CourseStatus.FAILED, CourseStatus.SCRIPT_GENERATED, True),
            (CourseStatus.FAILED, CourseStatus.VIDEO_GENERATING, True),
            (CourseStatus.FAILED, CourseStatus.COMPLETED, False),
        ],
    )
    def test_can_transition(self, from_status, to_status, expected):
        assert CourseStatus.can_transition(from_status, to_status) is expected

    def test_phase3_4_workflow_chain(self):
        """Verify the typical chain for Fase 3 and 4 transitions."""
        chain = [
            CourseStatus.CREATED,
            CourseStatus.UPLOADED,
            CourseStatus.EXTRACTING,
            CourseStatus.ANALYZING,
            CourseStatus.PEDAGOGICAL_DESIGN,
            CourseStatus.SCRIPT_GENERATED,
            CourseStatus.SCRIPT_VALIDATED,
        ]
        for current, next_step in zip(chain[:-1], chain[1:]):
            assert CourseStatus.can_transition(current, next_step) is True, (
                f"Invalid transition {current} -> {next_step}"
            )
