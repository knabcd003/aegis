import pytest
import json
from engines.analyst.supervisor import AgenticSupervisor

# IMPORTANT: This test requires a running LLM. 
# It runs against the local Ollama qwen3:4b node to prevent prompt regression.
# If the format or rationale quality degrades, this test will fail.

@pytest.fixture(scope="module")
def supervisor():
    # Only load the small 3B model for fast CI testing
    return AgenticSupervisor(model="qwen3:4b", provider="ollama")


def test_strong_buy_golden_file(supervisor):
    """
    Simulates a highly bullish scenario:
    - Massive $5M insider buying cluster
    - Earnings revisions strictly up (magnitude: 0.15)
    - Macro environment benign (VIX = 14)
    """
    context = {
        "earnings_revision": {
            "direction": "up",
            "magnitude": 0.15,
            "momentum": "accelerating",
            "revision_date": "2024-05-01"
        },
        "insider_activity": {
            "insider_type": "C-Suite",
            "transaction": "BUY",
            "cluster_buy": True,
            "cluster_size": 5,
            "notional_value": 5000000,
            "congressional": []
        },
        "macro": {
            "vix": 14.2
        }
    }
    
    result = supervisor.run(ticker="NVDA", date="2024-05-05", fundamental_context=context)
    
    # 1. Structural Output Constraints
    assert result["action"] == "BUY"
    assert result["conviction"] >= 0.7  # Should have high conviction
    
    # 2. Golden File Rationale Constraints (Glass Box)
    trace = " ".join(result["reasoning_trace"]).lower()
    
    # The Prompt MUST have recognized and cited the Insider Cluster Buy
    assert "insider" in trace or "cluster" in trace, "Prompt regression: Did not cite the $5M insider buy."
    
    # The Prompt MUST have recognized the massive earnings acceleration
    assert "earnings" in trace or "revision" in trace, "Prompt regression: Did not cite the earnings revision."
    
    # The Risk node must have approved
    assert "approved" in trace, "Risk Node incorrectly vetoed a benign macro environment."


def test_risk_veto_golden_file(supervisor):
    """
    Simulates a dangerous scenario:
    - Normal fundamental data (Analyst should say BUY)
    - Extreme macro VIX over 45 (Risk Manager MUST Veto)
    """
    context = {
        "macro": {
            "vix": 48.5  # Extreme panic
        }
    }
    
    # We test the RiskManagerNode directly to ensure we isolate its prompt logic
    # rather than letting the Analyst node preemptively downgrade it to HOLD.
    from engines.analyst.risk_manager import RiskManagerNode
    from engines.analyst.state import AgentState
    
    risk_node = RiskManagerNode(supervisor.llm)
    
    state: AgentState = {
        "ticker": "SPY",
        "date": "2024-08-05",
        "fundamental_context": context,
        "reasoning_trace": [],
        "analyst_proposal": {"action": "BUY", "conviction": 0.9, "rationale": "High earnings."},
        "risk_veto": False,
        "compliance_veto": False,
        "final_decision": {}
    }
    
    result = risk_node(state)
    
    # 1. Structural output constraints
    assert result["risk_veto"] is True
    assert result["final_decision"]["action"] == "HOLD"
    assert result["final_decision"]["conviction"] == 0.0
    
    # 2. Golden File Rationale Constraints
    trace = " ".join(result["reasoning_trace"]).lower()
    
    assert "veto" in trace or "vetoed" in trace, "Risk Manager failed to veto extreme VIX."
    assert "vix" in trace or "macro" in trace, "Risk did not cite the VIX constraint."
