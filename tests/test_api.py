import json
import pytest


class TestListSessions:
    def test_list_sessions(self, flask_client):
        response = flask_client.get("/api/sessions")
        assert response.status_code == 200, (
            f"GET /api/sessions should return 200, got {response.status_code}"
        )
        data = response.get_json()
        assert isinstance(data, list), "response should be a JSON list"

    def test_list_sessions_contains_files(self, flask_client):
        response = flask_client.get("/api/sessions")
        data = response.get_json()
        assert "sprint_session_001.csv" in data, (
            "response should contain sprint_session_001.csv"
        )
        assert "sprint_session_002.csv" in data, (
            "response should contain sprint_session_002.csv"
        )


class TestGetSessionSummary:
    def test_get_session_summary(self, flask_client):
        response = flask_client.get("/api/sessions/sprint_session_001.csv")
        assert response.status_code == 200, (
            f"GET /api/sessions/sprint_session_001.csv should return 200, "
            f"got {response.status_code}"
        )

    def test_get_session_summary_fields(self, flask_client):
        response = flask_client.get("/api/sessions/sprint_session_001.csv")
        data = response.get_json()
        expected_keys = [
            "filename",
            "total_reps",
            "total_distance",
            "total_duration",
            "avg_stroke_rate",
            "avg_stroke_length",
            "strokes",
        ]
        for key in expected_keys:
            assert key in data, f"response JSON should have key '{key}'"


class TestGetSessionStrokes:
    def test_get_session_strokes(self, flask_client):
        response = flask_client.get(
            "/api/sessions/sprint_session_001.csv/strokes"
        )
        assert response.status_code == 200, (
            f"GET .../strokes should return 200, got {response.status_code}"
        )
        data = response.get_json()
        assert isinstance(data, list), "strokes response should be a list"
        assert len(data) > 0, "strokes list should be non-empty"


class TestGetForceVelocity:
    def test_get_force_velocity(self, flask_client):
        response = flask_client.get(
            "/api/sessions/sprint_session_001.csv/force-velocity"
        )
        assert response.status_code == 200, (
            f"GET .../force-velocity should return 200, got {response.status_code}"
        )
        data = response.get_json()
        assert isinstance(data, list), "force-velocity response should be a list"
        assert len(data) > 0, "force-velocity list should be non-empty"


class TestGetPhaseBreakdown:
    def test_get_phase_breakdown(self, flask_client):
        response = flask_client.get(
            "/api/sessions/sprint_session_001.csv/phase-breakdown"
        )
        assert response.status_code == 200, (
            f"GET .../phase-breakdown should return 200, got {response.status_code}"
        )
        data = response.get_json()
        assert isinstance(data, dict), "phase-breakdown response should be a dict"
        assert len(data) > 0, "phase-breakdown dict should be non-empty"


class TestErrorHandling:
    def test_get_session_not_found(self, flask_client):
        response = flask_client.get("/api/sessions/nonexistent.csv")
        assert response.status_code == 404, (
            f"GET /api/sessions/nonexistent.csv should return 404, "
            f"got {response.status_code}"
        )


class TestServeIndex:
    def test_serve_index(self, flask_client):
        response = flask_client.get("/")
        assert response.status_code == 200, (
            f"GET / should return 200, got {response.status_code}"
        )
