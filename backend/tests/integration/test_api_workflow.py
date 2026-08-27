from __future__ import annotations

import pytest


class TestHealthEndpoint:
    def test_health_endpoint(self, client):
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        payload = response.json()
        assert payload.get("success") is True
        data = payload["data"]
        assert data["status"] == "ok"


class TestCoursesEndpoints:
    def test_list_courses_empty(self, client):
        response = client.get("/api/v1/courses")
        assert response.status_code == 200
        payload = response.json()
        assert payload.get("success") is True
        data = payload["data"]
        assert "count" in data
        assert isinstance(data["count"], int)
        assert data["count"] >= 0
        assert "items" in data

    def test_create_course(self, client):
        body = {
            "title": "Curso Integración E2E",
            "subject": "Testing",
            "level": "intermediate",
            "language": "es",
            "estimated_duration_minutes": 15,
        }
        response = client.post("/api/v1/courses", json=body)
        assert response.status_code == 201
        payload = response.json()
        assert payload.get("success") is True
        data = payload["data"]
        assert data["id"] is not None
        assert data["status"] == "CREATED"
        assert data["title"] == body["title"]
        assert data["subject"] == body["subject"]
        assert data["level"] == body["level"]
        assert data["language"] == body["language"]
        assert data["estimated_duration_minutes"] == body["estimated_duration_minutes"]


class TestFullWorkflow:
    @pytest.fixture
    def created_course(self, client):
        body = {
            "title": "Curso Integración E2E",
            "subject": "Testing",
            "level": "intermediate",
            "language": "es",
            "estimated_duration_minutes": 15,
        }
        response = client.post("/api/v1/courses", json=body)
        assert response.status_code == 201
        payload = response.json()
        assert payload.get("success") is True
        return payload["data"]

    def test_full_workflow_process_sync_completed(self, client, created_course):
        course_id = created_course["id"]

        process_body = {
            "provider": "mock",
            "skip_qa": False,
            "auto_approve_script": True,
            "run_async": False,
        }
        response = client.post(
            f"/api/v1/workflow/courses/{course_id}/process",
            json=process_body,
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload.get("success") is True
        data = payload["data"]

        assert data["final_status"] == "COMPLETED"
        assert data["final_progress"] == 100

        steps_completed = data.get("steps_completed", [])
        assert "analysis" in steps_completed
        assert "pedagogical_design" in steps_completed
        assert "script" in steps_completed
        assert "script_approved" in steps_completed
        assert "video_generate" in steps_completed
        assert "qa" in steps_completed

        course_resp = client.get(f"/api/v1/courses/{course_id}")
        assert course_resp.status_code == 200
        course_payload = course_resp.json()
        assert course_payload.get("success") is True
        course_data = course_payload["data"]
        assert course_data["progress"] == 100
        assert course_data["status"] == "COMPLETED"


class TestArtifactEndpointsAfterWorkflow:
    @pytest.fixture
    def processed_course_id(self, client):
        body = {
            "title": "Curso Prueba Artefactos",
            "subject": "Testing",
            "level": "beginner",
            "language": "es",
            "estimated_duration_minutes": 20,
        }
        create_resp = client.post("/api/v1/courses", json=body)
        assert create_resp.status_code == 201
        create_payload = create_resp.json()
        assert create_payload.get("success") is True
        course_id = create_payload["data"]["id"]

        process_body = {
            "provider": "mock",
            "skip_qa": False,
            "auto_approve_script": True,
            "run_async": False,
        }
        process_resp = client.post(
            f"/api/v1/workflow/courses/{course_id}/process",
            json=process_body,
        )
        assert process_resp.status_code == 200
        proc_payload = process_resp.json()
        assert proc_payload.get("success") is True
        data = proc_payload["data"]
        assert data["final_status"] == "COMPLETED"
        return course_id

    def test_get_analysis_after_workflow(self, client, processed_course_id):
        course_id = processed_course_id
        response = client.get(f"/api/v1/courses/{course_id}/analysis")
        assert response.status_code == 200
        payload = response.json()
        assert payload.get("success") is True
        analysis = payload["data"]["analysis"]

        concepts = analysis.get("concepts", [])
        assert isinstance(concepts, list)
        assert len(concepts) >= 0

        main_topics = analysis.get("main_topics", [])
        assert isinstance(main_topics, list)

    def test_get_pedagogical_design_after_workflow(self, client, processed_course_id):
        course_id = processed_course_id
        response = client.get(f"/api/v1/courses/{course_id}/pedagogical-design")
        assert response.status_code == 200
        payload = response.json()
        assert payload.get("success") is True
        pedagogical = payload["data"]["pedagogical_design"]

        general_objective = pedagogical.get("general_objective", "")
        assert isinstance(general_objective, str)
        assert len(general_objective) > 0

        lesson_structure = pedagogical.get("lesson_structure", [])
        assert isinstance(lesson_structure, list)
        assert len(lesson_structure) > 0

    def test_get_script_after_workflow(self, client, processed_course_id):
        course_id = processed_course_id
        response = client.get(f"/api/v1/courses/{course_id}/script")
        assert response.status_code == 200
        payload = response.json()
        assert payload.get("success") is True
        script = payload["data"]["script"]

        title = script.get("title", "")
        assert isinstance(title, str)
        assert len(title) > 0

        scenes = script.get("scenes", [])
        assert isinstance(scenes, list)
        assert len(scenes) >= 2

        total_duration = script.get("total_duration_seconds", 0)
        assert isinstance(total_duration, (int, float))
        assert total_duration >= 30

    def test_get_qa_after_workflow(self, client, processed_course_id):
        course_id = processed_course_id
        response = client.get(f"/api/v1/courses/{course_id}/qa")
        assert response.status_code == 200
        payload = response.json()
        assert payload.get("success") is True
        qa = payload["data"]["qa"]

        score = qa.get("score")
        assert isinstance(score, (int, float))
        assert 0 <= score <= 100

        status = qa.get("status")
        assert status in ("approved", "rejected")

    def test_get_course_status(self, client, processed_course_id):
        course_id = processed_course_id
        response = client.get(f"/api/v1/courses/{course_id}/status")
        assert response.status_code == 200
        payload = response.json()
        assert payload.get("success") is True
        data = payload["data"]

        assert data["progress"] == 100
        assert data["status"] == "COMPLETED"

        qa_data = data.get("qa")
        assert qa_data is not None
        assert isinstance(qa_data, dict)
        assert "status" in qa_data
        assert "score" in qa_data
