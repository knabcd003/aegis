import pytest
from unittest.mock import MagicMock
from engines.analyst.state import AgentState
from engines.analyst.analyst import AnalystNode
from engines.analyst.risk_manager import RiskManagerNode

def test_analyst_node_parses_json():
    mock_llm = MagicMock()
    # Mock LLM to return a clean JSON string
    mock_response = MagicMock()
    mock_response.content = '{"action": "BUY", "conviction": 0.8, "rationale": "High earnings."}'
    mock_llm.invoke.return_value = mock_response
    
    node = AnalystNode(mock_llm)
    state: AgentState = {
        "ticker": "AAPL",
        "date": "2024-01-01",
        "fundamental_context": {"earnings": "up"},
        "reasoning_trace": [],
        "analyst_proposal": {},
        "risk_veto": False,
        "compliance_veto": False,
        "final_decision": {}
    }
    
    result = node(state)
    assert result["analyst_proposal"]["action"] == "BUY"
    assert result["analyst_proposal"]["conviction"] == 0.8
    assert len(result["reasoning_trace"]) == 1
    assert "High earnings" in result["reasoning_trace"][0]

def test_analyst_node_handles_malformed_json():
    mock_llm = MagicMock()
    # Mock LLM returning garbage
    mock_response = MagicMock()
    mock_response.content = 'I think you should buy it because it is good.'
    mock_llm.invoke.return_value = mock_response
    
    node = AnalystNode(mock_llm)
    state: AgentState = {
        "ticker": "AAPL", "date": "2024-01-01", "fundamental_context": {},
        "reasoning_trace": [], "analyst_proposal": {}, "risk_veto": False,
        "compliance_veto": False, "final_decision": {}
    }
    
    result = node(state)
    # Should safely fallback to HOLD and 0 conviction
    assert result["analyst_proposal"]["action"] == "HOLD"
    assert result["analyst_proposal"]["conviction"] == 0.0
    assert "JSON Parse Error" in result["reasoning_trace"][0]

def test_risk_manager_vetos_dangerous_trades():
    mock_llm = MagicMock()
    mock_response = MagicMock()
    mock_response.content = '{"veto": true, "rationale": "VIX is too high."}'
    mock_llm.invoke.return_value = mock_response
    
    node = RiskManagerNode(mock_llm)
    state: AgentState = {
        "ticker": "AAPL", "date": "2024-01-01", "fundamental_context": {"macro": {"vix": 45.0}},
        "reasoning_trace": [],
        "analyst_proposal": {"action": "BUY", "conviction": 0.9, "rationale": "Strong thesis"},
        "risk_veto": False, "compliance_veto": False, "final_decision": {}
    }
    
    result = node(state)
    assert result["risk_veto"] is True
    # The final decision must be overridden to HOLD
    assert result["final_decision"]["action"] == "HOLD"
    assert result["final_decision"]["conviction"] == 0.0
    assert "VETOED" in result["reasoning_trace"][0]

def test_risk_manager_auto_approves_holds():
    node = RiskManagerNode(MagicMock()) # LLM shouldn't even be called
    
    state: AgentState = {
        "ticker": "AAPL", "date": "2024-01-01", "fundamental_context": {},
        "reasoning_trace": [],
        "analyst_proposal": {"action": "HOLD", "conviction": 0.0, "rationale": "Nothing happening"},
        "risk_veto": False, "compliance_veto": False, "final_decision": {}
    }
    
    result = node(state)
    assert result["risk_veto"] is False
    assert "Auto-approving" in result["reasoning_trace"][0]
