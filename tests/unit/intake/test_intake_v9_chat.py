import pytest
from fastapi.testclient import TestClient
from api.main import app
import json

client = TestClient(app)

def test_v9_path_b_validation():
    # Load the blank schema to use as a starting point
    with open("docs_v7/updated_intake/aegis_intake_schema_v9_example.json", "r") as f:
        schema = json.load(f)
    
    # We should be able to validate the example schema
    response = client.post("/api/intake/validate", json=schema)
    assert response.status_code == 200
    data = response.json()
    assert data["is_valid"] is True
    assert "Max Drawdown" in data["mandate_summary"]
    assert len(data["hard_errors"]) == 0

def test_v9_path_a_normal_flow():
    # Stage 0
    resp0 = client.post("/api/intake/chat", json={"message": "init"})
    assert resp0.status_code == 200
    data0 = resp0.json()
    session_id = data0["session_id"]
    assert data0["current_stage"] == 1
    
    # Stage 1 (Mock LLM immediately populates capital/account)
    resp1 = client.post("/api/intake/chat", json={"session_id": session_id, "message": "I have 100k"})
    data1 = resp1.json()
    assert data1["current_stage"] == 2 # Advances because mock fills capital/account
    assert data1["schema_wip"]["mandate_hard_constraints"]["investable_capital"] == 100000

    # Stage 2 (Mock LLM populates drawdown limit)
    resp2 = client.post("/api/intake/chat", json={"session_id": session_id, "message": "15% drawdown limit"})
    data2 = resp2.json()
    assert data2["schema_wip"]["mandate_hard_constraints"]["max_portfolio_drawdown_pct"] == 0.15

    # If we stopped here, we could validate the schema_wip
    validate_resp = client.post("/api/intake/validate", json=data2["schema_wip"])
    val_data = validate_resp.json()
    assert val_data["is_valid"] is True # Mock ensures required fields exist
