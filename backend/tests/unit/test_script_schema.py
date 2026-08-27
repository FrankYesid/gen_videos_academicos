"""Unit tests for Script schemas (Pydantic validation)."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.schemas.script import Scene, Script, ScriptOutput


class TestSceneSchema:
    def test_valid_scene(self):
        scene = Scene(
            id=1,
            title="Introduction to ML",
            duration_seconds=60,
            narration="Welcome to machine learning.",
            visual_instruction="Title screen with animations.",
            on_screen_text="What is Machine Learning?",
            educational_purpose="Hook viewer interest",
        )
        assert scene.id == 1
        assert scene.title == "Introduction to ML"
        assert scene.duration_seconds == 60
        assert scene.camera_angle is None
        assert scene.background is None
        assert scene.audio_cue is None

    def test_required_fields(self):
        with pytest.raises(ValidationError):
            Scene(
                id=1,
                title="X",
                narration="Y",
                visual_instruction="Z",
                on_screen_text="A",
                educational_purpose="B",
            )

    def test_duration_min_5_fails(self):
        with pytest.raises(ValidationError):
            Scene(
                id=1,
                title="X",
                duration_seconds=4,
                narration="Y",
                visual_instruction="Z",
                on_screen_text="A",
                educational_purpose="B",
            )

    def test_duration_max_600_fails(self):
        with pytest.raises(ValidationError):
            Scene(
                id=1,
                title="X",
                duration_seconds=601,
                narration="Y",
                visual_instruction="Z",
                on_screen_text="A",
                educational_purpose="B",
            )

    def test_duration_boundary_min(self):
        scene = Scene(
            id=1,
            title="X",
            duration_seconds=5,
            narration="Y",
            visual_instruction="Z",
            on_screen_text="A",
            educational_purpose="B",
        )
        assert scene.duration_seconds == 5

    def test_duration_boundary_max(self):
        scene = Scene(
            id=1,
            title="X",
            duration_seconds=600,
            narration="Y",
            visual_instruction="Z",
            on_screen_text="A",
            educational_purpose="B",
        )
        assert scene.duration_seconds == 600

    def test_id_min_1_fails(self):
        with pytest.raises(ValidationError):
            Scene(
                id=0,
                title="X",
                duration_seconds=30,
                narration="Y",
                visual_instruction="Z",
                on_screen_text="A",
                educational_purpose="B",
            )

    def test_id_boundary_min(self):
        scene = Scene(
            id=1,
            title="X",
            duration_seconds=30,
            narration="Y",
            visual_instruction="Z",
            on_screen_text="A",
            educational_purpose="B",
        )
        assert scene.id == 1

    def test_title_min_length_1_fails(self):
        with pytest.raises(ValidationError):
            Scene(
                id=1,
                title="",
                duration_seconds=30,
                narration="Y",
                visual_instruction="Z",
                on_screen_text="A",
                educational_purpose="B",
            )

    def test_optional_fields(self):
        scene = Scene(
            id=1,
            title="T",
            duration_seconds=30,
            narration="N",
            visual_instruction="V",
            on_screen_text="O",
            educational_purpose="E",
            camera_angle="Wide shot",
            background="Gradient",
            audio_cue="Music",
        )
        assert scene.camera_angle == "Wide shot"
        assert scene.background == "Gradient"
        assert scene.audio_cue == "Music"


class TestScriptOutputSchema:
    @pytest.fixture
    def base_scenes(self):
        return [
            Scene(
                id=1,
                title="Scene 1",
                duration_seconds=45,
                narration="Narration 1",
                visual_instruction="Visual 1",
                on_screen_text="Text 1",
                educational_purpose="Purpose 1",
            ),
            Scene(
                id=2,
                title="Scene 2",
                duration_seconds=60,
                narration="Narration 2",
                visual_instruction="Visual 2",
                on_screen_text="Text 2",
                educational_purpose="Purpose 2",
            ),
        ]

    def test_valid_script_output(self, base_scenes):
        output = ScriptOutput(
            title="Machine Learning Video",
            scenes=base_scenes,
            total_duration_seconds=105,
            introduction="Welcome to ML.",
            conclusion="Thanks for watching.",
            target_audience="Beginner learners",
            tone="educational",
            notes="Use smooth transitions.",
        )
        assert output.title == "Machine Learning Video"
        assert len(output.scenes) == 2
        assert output.total_duration_seconds == 105
        assert output.tone == "educational"
        assert output.notes == "Use smooth transitions."

    def test_total_duration_min_10_fails(self):
        with pytest.raises(ValidationError):
            ScriptOutput(
                title="X",
                scenes=[
                    Scene(id=1, title="S1", duration_seconds=5, narration="N", visual_instruction="V", on_screen_text="O", educational_purpose="E"),
                    Scene(id=2, title="S2", duration_seconds=4, narration="N", visual_instruction="V", on_screen_text="O", educational_purpose="E"),
                ],
                total_duration_seconds=9,
                introduction="Intro",
                conclusion="Conclusion",
                target_audience="Audience",
            )

    def test_total_duration_boundary(self):
        output = ScriptOutput(
            title="X",
            scenes=[
                Scene(id=1, title="S1", duration_seconds=5, narration="N", visual_instruction="V", on_screen_text="O", educational_purpose="E"),
                Scene(id=2, title="S2", duration_seconds=5, narration="N", visual_instruction="V", on_screen_text="O", educational_purpose="E"),
            ],
            total_duration_seconds=10,
            introduction="Intro",
            conclusion="Conclusion",
            target_audience="Audience",
        )
        assert output.total_duration_seconds == 10

    def test_scenes_min_length_2_fails(self):
        with pytest.raises(ValidationError):
            ScriptOutput(
                title="X",
                scenes=[
                    Scene(id=1, title="S1", duration_seconds=30, narration="N", visual_instruction="V", on_screen_text="O", educational_purpose="E"),
                ],
                total_duration_seconds=30,
                introduction="Intro",
                conclusion="Conclusion",
                target_audience="Audience",
            )

    def test_title_min_length_1_fails(self, base_scenes):
        with pytest.raises(ValidationError):
            ScriptOutput(
                title="",
                scenes=base_scenes,
                total_duration_seconds=105,
                introduction="Intro",
                conclusion="Conclusion",
                target_audience="Audience",
            )

    def test_defaults_tone_and_notes(self, base_scenes):
        output = ScriptOutput(
            title="Video Title",
            scenes=base_scenes,
            total_duration_seconds=105,
            introduction="Intro",
            conclusion="Conclusion",
            target_audience="Audience",
        )
        assert output.tone == "educational"
        assert output.notes is None

    def test_valid_script_output_with_5_scenes(self):
        scenes = []
        for i in range(5):
            scenes.append(Scene(
                id=i + 1,
                title=f"Scene {i + 1}",
                duration_seconds=30 + i * 10,
                narration=f"Narration for scene {i + 1}.",
                visual_instruction=f"Visual instructions for scene {i + 1}.",
                on_screen_text=f"Key point {i + 1}",
                educational_purpose=f"Teach concept {i + 1}",
                camera_angle="Medium shot" if i % 2 == 0 else None,
            ))

        output = ScriptOutput(
            title="Comprehensive ML Course",
            scenes=scenes,
            total_duration_seconds=250,
            introduction="Welcome to this comprehensive course on machine learning fundamentals.",
            conclusion="You've completed the course. Practice what you've learned!",
            target_audience="Intermediate computer science students",
            tone="professional and engaging",
            notes="Include pauses after key concepts for reflection.",
        )

        assert len(output.scenes) == 5
        assert output.total_duration_seconds == 250
        assert output.scenes[0].id == 1
        assert output.scenes[4].id == 5
        assert output.scenes[0].duration_seconds == 30
        assert output.scenes[4].duration_seconds == 70
        assert output.tone == "professional and engaging"
        assert output.notes is not None
        assert output.scenes[0].camera_angle == "Medium shot"
        assert output.scenes[1].camera_angle is None


class TestScriptSchema:
    @pytest.fixture
    def two_scenes(self):
        return [
            Scene(id=1, title="S1", duration_seconds=30, narration="N1", visual_instruction="V1", on_screen_text="T1", educational_purpose="P1"),
            Scene(id=2, title="S2", duration_seconds=45, narration="N2", visual_instruction="V2", on_screen_text="T2", educational_purpose="P2"),
        ]

    def test_valid_script(self, two_scenes):
        script = Script(
            title="ML 101",
            scenes=two_scenes,
            total_duration_seconds=75,
            introduction="Hi.",
            conclusion="Bye.",
            target_audience="Beginners",
        )
        assert script.title == "ML 101"
        assert len(script.scenes) == 2
        assert script.tone == "educational"
        assert script.notes is None

    def test_script_title_empty_fails(self, two_scenes):
        with pytest.raises(ValidationError):
            Script(
                title="",
                scenes=two_scenes,
                total_duration_seconds=75,
                introduction="Intro",
                conclusion="Conclusion",
                target_audience="A",
            )
