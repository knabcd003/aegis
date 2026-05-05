import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from api.main import app
import json
from engines.system.llm_adapter import AdapterResponse

client = TestClient(app)

@pytest.fixture(autouse=True)
def mock_llm_adapter():
    with patch("api.routers.intake_chat.llm_adapter.invoke") as mock_invoke:
        def side_effect(messages, role, workflow_id, node_id, **kwargs):
            stage = int(node_id.split("_")[-1])
            content = ""
            if stage == 1:
                content = '{"conversational_message": "stage 1", "schema_patch": {"mandate_hard_constraints": {"investable_capital": 100000, "account_type": "margin"}}}'
            elif stage == 2:
                content = '{"conversational_message": "stage 2", "schema_patch": {"mandate_hard_constraints": {"max_portfolio_drawdown_pct": 0.15}, "risk_profile": {"volatility_tolerance": "high"}}}'
            elif stage == 3:
                content = '{"conversational_message": "stage 3", "schema_patch": {"performance_targets": {"target_annual_return_pct": 0.30}, "mandate_hard_constraints": {"horizon_allocation": [{"label": "swing", "capital_weight": 1.0}]}}}'
            elif stage == 4:
                content = '{"conversational_message": "stage 4", "schema_patch": {"universe_mandate": {"raw_desire": "Tech momentum"}, "strategy_intent": {"catalyst_preferences": "earnings"}}}'
            elif stage == 5:
                content = '{"conversational_message": "stage 5", "schema_patch": {"mandate_hard_constraints": {"max_concurrent_live_strategies": 5}}}'
            elif stage == 6:
                content = '{"conversational_message": "stage 6", "schema_patch": {"mandate_priority_hierarchy": {"ordered_priorities": [{"rank": 1, "dimension": "risk_control"}]}}}'
            elif stage == 7:
                last_msg = messages[-1]["content"].lower()
                if "wait" in last_msg or "actually" in last_msg or "no" in last_msg:
                    content = '{"conversational_message": "revised", "schema_patch": {"mandate_hard_constraints": {"max_portfolio_drawdown_pct": 0.20}}}'
                elif "contradict" in last_msg:
                    content = '{"conversational_message": "contradict", "schema_patch": {"filing_notes": {"contradictions": ["User wants safe returns but asked for penny stocks."]}}}'
                else:
                    content = '{"conversational_message": "final", "schema_patch": {}}'
                    
            return AdapterResponse(
                content=content, provider_id="mock", model_id="mock", was_primary=True,
                fallback_reason="none", session_quality="nominal", prompt_tokens=10,
                completion_tokens=10, estimated_cost_usd=0.0, latency_ms=10.0
            )
            
        mock_invoke.side_effect = side_effect
        yield mock_invoke


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
