import pytest
import time
from unittest.mock import patch

from engines.system.token_messenger.models import WorkflowStage
from engines.system.token_messenger.messenger import TokenMessenger, SequenceViolationError
from engines.system.token_messenger.store import _store

@pytest.fixture(autouse=True)
def clean_store():
    """Ensure a clean in-memory token store before each test."""
    _store.clear()
    yield

@pytest.fixture
def messenger():
    return TokenMessenger()

def test_correct_lifecycle(messenger):
    """BACKTEST -> AUDIT -> PROMOTION -> DEPLOYMENT without errors."""
    workflow_id = "wf_123"
    config_hash = "abc123hash"
    
    # 1. Issue Backtest Token
    t_backtest = messenger.issue(workflow_id, WorkflowStage.BACKTEST, config_hash)
    
    # 2. Consume Backtest -> Issue Audit
    t_audit = messenger.consume_and_issue(
        t_backtest, workflow_id, WorkflowStage.BACKTEST, config_hash, WorkflowStage.AUDIT
    )
    assert t_audit != t_backtest
    
    # 3. Consume Audit -> Issue Promotion
    t_promo = messenger.consume_and_issue(
        t_audit, workflow_id, WorkflowStage.AUDIT, config_hash, WorkflowStage.PROMOTION
    )
    
    # 4. Consume Promotion -> Issue Deployment
    t_deploy = messenger.consume_and_issue(
        t_promo, workflow_id, WorkflowStage.PROMOTION, config_hash, WorkflowStage.DEPLOYMENT
    )
    
    assert _store[workflow_id].stage == WorkflowStage.DEPLOYMENT
    assert _store[workflow_id].consumed is False

def test_replay_attack(messenger):
    """Consume a token, try to use the same token_value again -> SequenceViolationError."""
    workflow_id = "wf_replay"
    config_hash = "hash"
    
    t_backtest = messenger.issue(workflow_id, WorkflowStage.BACKTEST, config_hash)
    
    # Legitimate consume
    messenger.consume_and_issue(
        t_backtest, workflow_id, WorkflowStage.BACKTEST, config_hash, WorkflowStage.AUDIT
    )
    
    # Replay attack with same token
    with pytest.raises(SequenceViolationError, match="Token already consumed|Token value mismatch"):
        messenger.consume_and_issue(
            t_backtest, workflow_id, WorkflowStage.BACKTEST, config_hash, WorkflowStage.AUDIT
        )

def test_stage_skip(messenger):
    """Issue at BACKTEST, attempt to consume expecting PROMOTION -> rejected."""
    workflow_id = "wf_skip"
    config_hash = "hash"
    
    t_backtest = messenger.issue(workflow_id, WorkflowStage.BACKTEST, config_hash)
    
    # User tries to bypass AUDIT stage verification
    with pytest.raises(SequenceViolationError, match="Expected stage"):
        messenger.consume_and_issue(
            t_backtest, workflow_id, WorkflowStage.PROMOTION, config_hash, WorkflowStage.DEPLOYMENT
        )

def test_config_drift(messenger):
    """Issue with hash A, consume with hash B -> rejected."""
    workflow_id = "wf_drift"
    config_hash_A = "hash_A"
    config_hash_B = "hash_B"
    
    t_backtest = messenger.issue(workflow_id, WorkflowStage.BACKTEST, config_hash_A)
    
    # User modified config during backtest to sneak changes into Audit
    with pytest.raises(SequenceViolationError, match="Config modified"):
        messenger.consume_and_issue(
            t_backtest, workflow_id, WorkflowStage.BACKTEST, config_hash_B, WorkflowStage.AUDIT
        )

def test_expiry(messenger):
    """Issue a token, set expires_at to time.time() - 1, attempt consume -> rejected."""
    workflow_id = "wf_expire"
    config_hash = "hash"
    
    t_backtest = messenger.issue(workflow_id, WorkflowStage.BACKTEST, config_hash)
    
    # Artificially expire the token in the store
    _store[workflow_id].expires_at = time.time() - 1.0
    
    with pytest.raises(SequenceViolationError, match="Token expired"):
        messenger.consume_and_issue(
            t_backtest, workflow_id, WorkflowStage.BACKTEST, config_hash, WorkflowStage.AUDIT
        )
