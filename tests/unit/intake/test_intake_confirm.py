import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)

@patch("api.routers.intake_confirm.llm_adapter.invoke")
def test_intake_confirm_cross_section_synthesis(mock_invoke):
    import json
    class MockAdapterRes:
        pass
    mock_res = MockAdapterRes()
    mock_res.content = json.dumps({
        "regime_universe_pairs": [
            {
                "regime": "Post-FDA Approval Catalyst",
                "universe": "Biotech",
                "rationale": "User wants to trade biotech companies specifically following FDA approval catalysts."
            }
        ],
        "macro_views": [],
        "filing_notes_contradictions": [
            "User wants highly profitable companies but prefers early-stage biotech which rarely have earnings."
        ]
    })
    mock_invoke.return_value = mock_res
    
    schema_payload = {
        "_schema_version": "v9.0",
        "mandate_hard_constraints": {
            "investable_capital": 50000,
            "max_portfolio_drawdown_pct": 0.15,
            "max_concurrent_live_strategies": 5,
            "horizon_allocation": [
                {"label": "swing", "capital_weight": 1.0}
            ],
            "universe_hard_filters": {
                "sectors_of_interest": ["Biotech"]
            }
        },
        "performance_targets": {
            "target_annual_return_pct": 0.20
        },
        "universe_mandate": {
            "fundamental_screens": "Must be highly profitable with strong earnings."
        },
        "strategy_intent": {
            "catalyst_preferences": "FDA Approvals"
        },
        "mandate_priority_hierarchy": {
            "ordered_priorities": [
                {"rank": 1, "dimension": "risk_control"},
                {"rank": 2, "dimension": "return_target"},
                {"rank": 3, "dimension": "universe_specificity"}
            ],
            "trade_off_philosophy": "Risk first."
        }
    }
    
    response = client.post("/api/intake/confirm/review", json=schema_payload)
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["is_valid"] is True
    assert len(data["hard_errors"]) == 0
    assert len(data["cross_section_contradictions"]) == 1
    assert "profitable" in data["cross_section_contradictions"][0]
    
    updated_schema = data["schema_updated"]
    
    # Check regime_universe_pairs
    assert "strategy_intent" in updated_schema
    assert len(updated_schema["strategy_intent"]["regime_universe_pairs"]) == 1
    assert updated_schema["strategy_intent"]["regime_universe_pairs"][0]["universe"] == "Biotech"
    
    # Check filing_notes.contradictions
    assert "filing_notes" in updated_schema
    assert len(updated_schema["filing_notes"]["contradictions"]) == 1
    
    # Check tradeoff philosophy is intact
    assert updated_schema["mandate_priority_hierarchy"]["trade_off_philosophy"] == "Risk first."

def test_intake_confirm_deterministic_failures():
    schema_payload = {
        "_schema_version": "v9.0",
        "mandate_hard_constraints": {
            "investable_capital": 50000,
            "max_portfolio_drawdown_pct": 0.10,
            "account_type": "401k",
            "universe_hard_filters": {
                "asset_classes_permitted": ["Individual Stocks"]
            },
            "horizon_allocation": [
                {"label": "swing", "capital_weight": 0.8} # sums to 0.8!
            ]
        },
        "performance_targets": {
            "target_annual_return_pct": 0.30 # 3.0 sharpe!
        }
    }
    
    response = client.post("/api/intake/confirm/review", json=schema_payload)
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["is_valid"] is False
    assert len(data["hard_errors"]) == 3
    
    errors = " ".join(data["hard_errors"])
    assert "401k" in errors
    assert "sum to 1.0" in errors
    assert "unrealistic Sharpe ratio" in errors
