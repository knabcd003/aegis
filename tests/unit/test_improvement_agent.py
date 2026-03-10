import pytest
from unittest.mock import patch, MagicMock
from engines.analyst.improvement_agent import ImprovementAgent, ConfigMutationProposal, ParameterMutation

@pytest.fixture
def agent():
    with patch("engines.analyst.improvement_agent.ChatOllama") as mock_ollama:
        # Mock LLM is just a pass-through for the parser test
        return ImprovementAgent(provider="ollama")

def test_apply_mutation_valid(agent):
    current_config = {
        "sandbox": {
            "slippage_bps": 10
        },
        "quant_engine": {
            "vpin": {
                "toxicity_threshold": 0.85
            }
        }
    }
    
    proposal = ConfigMutationProposal(
        mutation=ParameterMutation(
            proposal_id="p1",
            target_category="quant_engine",
            target_parameter="quant_engine.vpin.toxicity_threshold",
            current_value=0.85,
            proposed_value=0.80,
            rationale="Lower threshold to capture more trades."
        )
    )
    
    new_config = agent.apply_mutation(current_config, proposal)
    
    assert new_config["sandbox"]["slippage_bps"] == 10
    assert new_config["quant_engine"]["vpin"]["toxicity_threshold"] == 0.80
    assert isinstance(new_config["quant_engine"]["vpin"]["toxicity_threshold"], float)

def test_apply_mutation_creates_missing_keys(agent):
    current_config = {
        "quant_engine": {}
    }
    
    proposal = ConfigMutationProposal(
        mutation=ParameterMutation(
            proposal_id="p2",
            target_category="quant_engine",
            target_parameter="quant_engine.vpin.enabled",
            current_value=False,
            proposed_value=True,
            rationale="Enable VPIN."
        )
    )
    
    new_config = agent.apply_mutation(current_config, proposal)
    
    assert new_config["quant_engine"]["vpin"]["enabled"] is True

def test_apply_mutation_type_coercion(agent):
    current_config = {
        "sandbox": {
            "min_hold_days": 5
        }
    }
    
    # Propose a string that should be coerced to int
    proposal = ConfigMutationProposal(
        mutation=ParameterMutation(
            proposal_id="p3",
            target_category="sandbox",
            target_parameter="sandbox.min_hold_days",
            current_value=5,
            proposed_value="7", # String instead of int
            rationale="Hold longer."
        )
    )
    
    new_config = agent.apply_mutation(current_config, proposal)
    
    assert new_config["sandbox"]["min_hold_days"] == 7
    assert isinstance(new_config["sandbox"]["min_hold_days"], int)
