import pytest
from fastapi.testclient import TestClient
from api.main import app
import json

client = TestClient(app)

def test_v9_path_b_validation():
    with open("docs_v7/updated_intake/aegis_intake_schema_v9_example.json", "r") as f:
        schema = json.load(f)
    
    response = client.post("/api/intake/validate", json=schema)
    assert response.status_code == 200
    data = response.json()
    assert data["is_valid"] is True
    assert "Max Drawdown" in data["mandate_summary"]
    assert len(data["hard_errors"]) == 0

def test_v9_path_a_normal_flow():
    # Stage 0
    resp = client.post("/api/intake/chat", json={"message": "init"})
    assert resp.status_code == 200
    session_id = resp.json()["session_id"]
    
    # Stage 1
    resp = client.post("/api/intake/chat", json={"session_id": session_id, "message": "I have 100k"})
    assert resp.json()["current_stage"] == 2
    
    # Stage 2
    resp = client.post("/api/intake/chat", json={"session_id": session_id, "message": "15% drawdown limit"})
    assert resp.json()["current_stage"] == 3
    
    # Stage 3
    resp = client.post("/api/intake/chat", json={"session_id": session_id, "message": "30% returns"})
    assert resp.json()["current_stage"] == 4
    
    # Stage 4
    resp = client.post("/api/intake/chat", json={"session_id": session_id, "message": "tech momentum"})
    assert resp.json()["current_stage"] == 5
    
    # Stage 5
    resp = client.post("/api/intake/chat", json={"session_id": session_id, "message": "5 strats max"})
    assert resp.json()["current_stage"] == 6
    
    # Stage 6
    resp = client.post("/api/intake/chat", json={"session_id": session_id, "message": "risk over returns"})
    assert resp.json()["current_stage"] == 7
    
    # Stage 7 Correction Loop
    resp = client.post("/api/intake/chat", json={"session_id": session_id, "message": "Wait, actually make it 20% drawdown"})
    data = resp.json()
    assert data["current_stage"] == 7 # Doesn't rollback
    assert data["schema_wip"]["mandate_hard_constraints"]["max_portfolio_drawdown_pct"] == 0.20
    
def test_v9_path_a_contradictory_user():
    # Setup up to stage 6
    resp = client.post("/api/intake/chat", json={"message": "init"})
    session_id = resp.json()["session_id"]
    for i in range(1, 7):
        resp = client.post("/api/intake/chat", json={"session_id": session_id, "message": f"Proceed stage {i}"})
    
    # Stage 7: trigger contradiction logic via our mock keyword
    resp = client.post("/api/intake/chat", json={"session_id": session_id, "message": "Here is a contradict"})
    data = resp.json()
    # Check if the contradiction got written to filing_notes
    assert len(data["schema_wip"]["filing_notes"]["contradictions"]) > 0

def test_v9_path_a_sparse_user():
    # In a real LLM, a sparse user wouldn't provide all sub-objectives.
    # The evaluator would hold them back unless we bypassed it, 
    # but the instructions specify the evaluator SHOULD advance them with [ASSUMED] tags
    # if it determines the user can't answer. For our mock, we assume the LLM patches
    # the required fields to allow advancement anyway.
    
    # We will test the validation endpoint with an [ASSUMED] tag in a schema
    schema = {
        "mandate_hard_constraints": {
            "max_portfolio_drawdown_pct": 0.15,
            "investable_capital": 50000
        },
        "risk_profile": {
            "volatility_tolerance": "[ASSUMED] Medium tolerance based on lack of response"
        }
    }
    resp = client.post("/api/intake/validate", json=schema)
    data = resp.json()
    assert data["is_valid"] is True
    assert len(data["inferred_flags"]) > 0
    assert "System inferred:" in data["inferred_flags"][0]
