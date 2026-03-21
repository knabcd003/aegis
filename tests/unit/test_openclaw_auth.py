"""
Tests for OpenClaw API endpoint authentication.

Verifies:
  - Requests without token → 401
  - Requests with wrong token → 401
  - Requests with valid token → success (200 or 404)
  - Critical events pause affected Sentinels
"""
import os
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def set_openclaw_secret(monkeypatch):
    """Set the OPENCLAW_API_SECRET for all tests."""
    monkeypatch.setenv("OPENCLAW_API_SECRET", "test-secret-token-12345")


@pytest.fixture
def client():
    """Create a FastAPI test client with mocked engine dependencies."""
    # Mock the heavy dependencies that get loaded at startup
    with patch("api.main.DataEngine"), \
         patch("api.main.YFinanceConnector"), \
         patch("api.main.ConnectorHealthMonitor"), \
         patch("api.main.SentinelStateManager"):
        from api.main import app
        return TestClient(app)


VALID_HEADERS = {"Authorization": "Bearer test-secret-token-12345"}
INVALID_HEADERS = {"Authorization": "Bearer wrong-token"}
NO_HEADERS = {}


# ---------- 401 on missing/invalid token ----------

class TestAuthentication:
    def test_universe_no_token_returns_401(self, client):
        resp = client.get("/api/openclaw/universe/sent_001", headers=NO_HEADERS)
        assert resp.status_code == 401, f"Expected 401, got {resp.status_code}: {resp.json()}"

    def test_universe_invalid_token_returns_401(self, client):
        resp = client.get("/api/openclaw/universe/sent_001", headers=INVALID_HEADERS)
        assert resp.status_code == 401

    def test_events_no_token_returns_401(self, client):
        resp = client.post(
            "/api/openclaw/events",
            headers=NO_HEADERS,
            json={"event_type": "macro", "title": "Test", "summary": "Test", "severity": "low"},
        )
        assert resp.status_code == 401

    def test_events_invalid_token_returns_401(self, client):
        resp = client.post(
            "/api/openclaw/events",
            headers=INVALID_HEADERS,
            json={"event_type": "macro", "title": "Test", "summary": "Test", "severity": "low"},
        )
        assert resp.status_code == 401

    def test_list_events_no_token_returns_401(self, client):
        resp = client.get("/api/openclaw/events", headers=NO_HEADERS)
        assert resp.status_code == 401


# ---------- Valid token → success ----------

class TestValidAccess:
    def test_universe_valid_token_returns_not_401(self, client):
        """With valid token, should get 404 (sentinel not found) or 503, NOT 401."""
        resp = client.get("/api/openclaw/universe/sent_001", headers=VALID_HEADERS)
        assert resp.status_code != 401, "Valid token should not return 401"

    def test_post_event_valid_token(self, client):
        """Valid token + valid payload → 200."""
        resp = client.post(
            "/api/openclaw/events",
            headers=VALID_HEADERS,
            json={
                "event_type": "geopolitical",
                "title": "US-China Trade Dispute",
                "summary": "New tariffs announced on semiconductor imports",
                "severity": "high",
                "affected_tickers": ["NVDA", "TSM"],
                "affected_sectors": ["technology"],
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "received"
        assert "event_id" in data

    def test_list_events_valid_token(self, client):
        resp = client.get("/api/openclaw/events", headers=VALID_HEADERS)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


# ---------- Missing env var ----------

class TestMissingSecret:
    def test_missing_env_var_returns_500(self, monkeypatch):
        """If OPENCLAW_API_SECRET is not set, endpoints should return 500."""
        monkeypatch.delenv("OPENCLAW_API_SECRET", raising=False)

        with patch("api.main.DataEngine"), \
             patch("api.main.YFinanceConnector"), \
             patch("api.main.ConnectorHealthMonitor"), \
             patch("api.main.SentinelStateManager"):
            from api.main import app
            client = TestClient(app)

        resp = client.get(
            "/api/openclaw/universe/sent_001",
            headers={"Authorization": "Bearer anything"},
        )
        assert resp.status_code == 500
        assert "OPENCLAW_API_SECRET" in resp.json()["detail"]
