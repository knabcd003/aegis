import pytest
from datetime import datetime
from unittest.mock import MagicMock

from engines.sentinel.state_manager import SentinelStateManager, SignalCard

def test_deploy_sentinel():
    data_engine = MagicMock()
    health_monitor = MagicMock()
    
    manager = SentinelStateManager(data_engine, health_monitor)
    
    config = {"version": "1.0", "sandbox": {"capital": 50000}}
    sentinel = manager.deploy_sentinel("test_sentinel_1", config, "run_id_123")
    
    # Assert successfully deployed
    assert "test_sentinel_1" in manager.sentinels
    assert sentinel.promoted_run_id == "run_id_123"
    assert sentinel.portfolio.nav == 50000

def test_evaluate_pipeline_offline_connector_blocks_signals():
    data_engine = MagicMock()
    health_monitor = MagicMock()
    health_monitor.can_generate_signals.return_value = False  # OFFLINE state
    
    manager = SentinelStateManager(data_engine, health_monitor)
    manager.deploy_sentinel("test_1", {"asset_universe": {"tickers": ["AAPL"]}}, "run_123")
    
    # Normally this would trigger pipeline, we want to ensure it bails out early
    manager.evaluate_pipeline(datetime.now())
    # Pending cards should be strictly 0 because generation was suspended
    assert len(manager.sentinels["test_1"].pending_cards) == 0

def test_queue_and_process_signal_card():
    manager = SentinelStateManager(MagicMock(), MagicMock())
    manager.deploy_sentinel("test_1", {}, "run_123")
    
    card = SignalCard(
        sentinel_id="test_1",
        ticker="AAPL",
        decision="BUY",
        thesis="Strong fundamentals.",
        quant_anchors={"vpin": 0.2},
        sub_agent_votes={"Risk Agent": "APPROVED"},
        confidence=0.85
    )
    
    manager.queue_signal_card(card)
    
    assert len(manager.sentinels["test_1"].pending_cards) == 1
    
    # Accept the card
    success = manager.process_review(card.card_id, "test_1", "ACCEPTED")
    assert success is True
    
    # Card should be moved out of pending queue
    assert len(manager.sentinels["test_1"].pending_cards) == 0
    assert card.status == "ACCEPTED"
