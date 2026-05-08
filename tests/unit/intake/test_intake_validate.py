import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)

@patch("api.routers.intake_validate.llm_adapter.invoke")
def test_intake_validate_contradiction(mock_invoke):
    import json
    class MockAdapterRes:
        pass
    mock_res = MockAdapterRes()
    mock_res.content = json.dumps({
        "prose_fields": {
            "risk_profile.summary": "[EXPLICIT] User claims to be conservative but trades penny stocks."
        },
        "gap_questions": [],
        "contradictions": [
            {
                "field": "Risk Tolerance",
                "issue": "You specified conservative risk limits (15% drawdown) but your detail text says 'I love trading volatile penny stocks', which is a high-risk approach."
            }
        ]
    })
    mock_invoke.return_value = mock_res
    
    response = client.post("/api/intake/validate/validate_section", json={
        "section_id": 2,
        "structured_fields": {
            "drawdown": 15,
            "concurrent": 5,
            "leverage": False
        },
        "detail_text": "I love trading volatile penny stocks."
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["section_complete"] is False
    assert len(data["contradictions"]) == 1
    assert "penny stocks" in data["contradictions"][0]["issue"]
    
@patch("api.routers.intake_validate.llm_adapter.invoke")
def test_intake_validate_gap(mock_invoke):
    import json
    class MockAdapterRes:
        pass
    mock_res = MockAdapterRes()
    mock_res.content = json.dumps({
        "prose_fields": {},
        "gap_questions": ["Can you explain what type of ETFs you are interested in?"],
        "contradictions": []
    })
    mock_invoke.return_value = mock_res
    
    response = client.post("/api/intake/validate/validate_section", json={
        "section_id": 4,
        "structured_fields": {
            "assets": ["ETFs"],
            "sectors": [],
            "volume": 1000000
        },
        "detail_text": "I like ETFs."
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["section_complete"] is False
    assert len(data["gap_questions"]) == 1
    assert "ETFs" in data["gap_questions"][0]

def test_intake_validate_empty_detail():
    # Detail text is empty, should fail fast
    response = client.post("/api/intake/validate/validate_section", json={
        "section_id": 1,
        "structured_fields": {
            "capital": 100000
        },
        "detail_text": "  "
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["section_complete"] is False
    assert len(data["gap_questions"]) == 1
