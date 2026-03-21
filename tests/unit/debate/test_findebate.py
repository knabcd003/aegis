import pytest
import json
from unittest.mock import MagicMock

from engines.debate.models import DebateArgumentScore, EvidenceType
from engines.debate.compressor import DebateCompressor
from engines.debate.orchestrator import FinDebateOrchestrator
from engines.system.token_messenger.messenger import TokenMessenger
from engines.system.token_messenger.models import WorkflowStage
from engines.system.token_messenger.store import _store

def test_evidentiary_weight_override():
    """Verify the server-side @model_validator explicitly overrides evidentiary_weight."""
    # Agent tries to cheat and assert a 1.0 weight for a pure assertion
    cheating_input = {
        "argument_id": "arg_1",
        "agent": "bull",
        "claim": "Stonks go up",
        "evidence_type": "assertion_only",
        "evidence_specific": False,
        "falsifiable": False,
        "evidentiary_weight": 1.0  # Cheating!
    }
    
    score = DebateArgumentScore(**cheating_input)
    assert score.evidentiary_weight == 0.0, "Validator failed to override cheating weight"

def test_compress_to_schema():
    """Verify compress_to_schema produces schema-valid data under budget, retaining key claims."""
    mock_router = MagicMock()
    
    # Simulate the LLM structured extraction output
    mock_llm_response = '''
    [
        {
            "argument_id": "arg_comp",
            "agent": "bear",
            "claim": "The Sharpe ratio dropped by 20% in the 2020 crash.",
            "evidence_type": "backtest_data",
            "evidence_specific": true,
            "falsifiable": true
        }
    ]
    '''
    
    def dummy_invoker(provider_id, model_id, prompt):
        return mock_llm_response

    compressor = DebateCompressor(mock_router, dummy_invoker)
    
    # A massive 5K token raw text
    massive_raw = "Fluff preamble... " * 1000 + "The Sharpe ratio dropped by 20% in the 2020 crash." + " Fluff postamble" * 1000
    
    compressed_args = compressor.compress_to_schema(massive_raw, "bear")
    
    assert len(compressed_args) == 1
    assert compressed_args[0].claim == "The Sharpe ratio dropped by 20% in the 2020 crash."
    assert compressed_args[0].evidence_type == EvidenceType.BACKTEST_DATA
    
    # Check token budget representation (string length proxy)
    json_repr = json.dumps([a.model_dump() for a in compressed_args])
    assert len(json_repr) < 12000, "Compressed output is too large, exceeding 3K token proxy"

def test_orchestrator_token_routing():
    """Verify TokenMessenger successfully routes BACKTEST -> AUDIT upon orchestrator run."""
    _store.clear()
    
    messenger = TokenMessenger()
    mock_router = MagicMock()
    
    workflow_id = "wf_1"
    config_hash = "hash_xyz"
    
    # Issue initial Backtest token
    t_backtest = messenger.issue(workflow_id, WorkflowStage.BACKTEST, config_hash)
    
    # Mock LLM to fast-track the debate loop
    def dummy_llm(*args, **kwargs):
        # We need the moderator specifically to output a JSON verdict
        if "Moderator" in args[2]:
            return '''
            {
                "confidence_score": 90,
                "verdict": "APPROVE",
                "bull_evidentiary_score": 0.8,
                "bear_evidentiary_score": 0.4,
                "bull_strongest_point": "a",
                "bear_strongest_point": "b",
                "deciding_factor": "c",
                "debate_integrity": "NOMINAL",
                "required_revisions": []
            }
            '''
        # For compress_to_schema calls during bull/bear
        return "[]"
        
    orchestrator = FinDebateOrchestrator(
        router=mock_router,
        llm_invoker=dummy_llm,
        token_messenger=messenger,
        mlflow_client=None
    )
    
    verdict, t_audit = orchestrator.run_debate(
        token_value=t_backtest,
        workflow_id=workflow_id,
        config_hash=config_hash,
        strategy_manifest="mock manifest",
        num_rounds=1
    )
    
    assert verdict.verdict == "APPROVE"
    assert t_audit != t_backtest
    assert _store[workflow_id].stage == WorkflowStage.AUDIT
    assert _store[workflow_id].consumed is False
