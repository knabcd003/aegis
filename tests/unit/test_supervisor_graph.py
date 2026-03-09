import pytest
from unittest.mock import patch, MagicMock
from engines.analyst.supervisor import AgenticSupervisor
from engines.analyst.state import AgentState

@patch("engines.analyst.supervisor.ChatOllama")
def test_supervisor_full_routing_approved(mock_chat):
    # Setup mock LLM responses for Analyst then Risk
    mock_chat.return_value.invoke.side_effect = [
        MagicMock(content='{"action": "BUY", "conviction": 0.9, "rationale": "Strong"}'),
        MagicMock(content='{"veto": false, "rationale": "Levels look good"}')
    ]
    
    supervisor = AgenticSupervisor(provider="ollama", model="fake-model")
    
    result = supervisor.run(
        ticker="AAPL", 
        date="2024-01-01", 
        fundamental_context={"macro": {"vix": 12.0}}
    )
    
    assert result["action"] == "BUY"
    assert result["conviction"] == 0.9
    assert len(result["reasoning_trace"]) == 2
    assert "[Analyst]" in result["reasoning_trace"][0]
    assert "[Risk]: APPROVED" in result["reasoning_trace"][1]

@patch("engines.analyst.supervisor.ChatOllama")
def test_supervisor_full_routing_vetoed(mock_chat):
    # Analyst says BUY, Risk says Veto
    mock_chat.return_value.invoke.side_effect = [
        MagicMock(content='{"action": "BUY", "conviction": 0.9, "rationale": "Strong"}'),
        MagicMock(content='{"veto": true, "rationale": "VIX spike"}')
    ]
    
    supervisor = AgenticSupervisor(provider="ollama", model="fake-model")
    
    result = supervisor.run(
        ticker="AAPL", 
        date="2024-01-01", 
        fundamental_context={"macro": {"vix": 45.0}}
    )
    
    assert result["action"] == "HOLD"
    assert result["conviction"] == 0.0
    assert len(result["reasoning_trace"]) == 2
    assert "[Risk]: VETOED" in result["reasoning_trace"][1]
