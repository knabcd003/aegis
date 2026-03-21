"""
Tests for Sentinel State Manager (Phase 4 Step 3).

Tests verify:
  - Sentinel deployment and lifecycle (deploy, pause, resume, deactivate)
  - Paper portfolio: open position, close position, NAV tracking
  - Close signal integration: exit checks trigger on heartbeat
  - Signal Card generation for CLOSE signals
  - ACCEPT/DECLINE flow: paper execution + counterfactual tracking
  - known_universe.json: created on deploy, updated on position changes
"""
import pytest
import json
import os
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from engines.sentinel.state_manager import (
    SentinelStateManager,
    Sentinel,
    SentinelStatus,
    SignalCard,
    PaperPortfolio,
    Position,
)
from engines.sentinel.close_signal_generator import (
    EntryStateSnapshot,
    CloseSignal,
    ExitType,
)


# ---------- Fixtures ----------

@pytest.fixture
def mock_data_engine():
    de = MagicMock()
    de.list_connectors.return_value = ["yfinance", "fred"]
    return de


@pytest.fixture
def mock_health_monitor():
    hm = MagicMock()
    hm.is_any_connector_offline.return_value = False
    hm.is_any_connector_degraded.return_value = False
    hm.can_generate_signals.return_value = True
    return hm


@pytest.fixture
def state_manager(mock_data_engine, mock_health_monitor):
    return SentinelStateManager(mock_data_engine, mock_health_monitor)


@pytest.fixture
def sample_config():
    return {
        "asset_universe": {"tickers": ["AAPL", "MSFT"]},
        "exit_conditions": {
            "target_price": None,
            "stop_loss_price": None,
            "max_hold_days": 90,
            "max_portfolio_drawdown_pct": 0.15,
        },
    }


# ---------- Deployment ----------

class TestDeployment:
    def test_deploy_sentinel(self, state_manager, sample_config):
        sentinel = state_manager.deploy_sentinel("sent_001", sample_config, "mlflow_run_123")
        assert sentinel.sentinel_id == "sent_001"
        assert sentinel.status == SentinelStatus.ACTIVE
        assert "sent_001" in state_manager.sentinels

    def test_deploy_duplicate_raises(self, state_manager, sample_config):
        state_manager.deploy_sentinel("sent_001", sample_config, "run_1")
        with pytest.raises(ValueError, match="already deployed"):
            state_manager.deploy_sentinel("sent_001", sample_config, "run_2")

    def test_known_universe_written_on_deploy(self, state_manager, sample_config, tmp_path):
        state_manager.KNOWN_UNIVERSE_DIR = str(tmp_path)
        state_manager.deploy_sentinel("sent_001", sample_config, "run_1")

        path = tmp_path / "sent_001_universe.json"
        assert path.exists()
        data = json.loads(path.read_text())
        assert data["sentinel_id"] == "sent_001"
        assert "holdings" in data

    def test_initial_cash_configurable(self, state_manager, sample_config):
        sentinel = state_manager.deploy_sentinel(
            "sent_002", sample_config, "run_2", initial_cash=50000.0
        )
        assert sentinel.portfolio.cash == 50000.0
        assert sentinel.portfolio.nav == 50000.0


# ---------- Lifecycle ----------

class TestLifecycle:
    def test_pause_and_resume(self, state_manager, sample_config):
        state_manager.deploy_sentinel("sent_001", sample_config, "run_1")
        state_manager.pause_sentinel("sent_001", "Connector issue")
        assert state_manager.sentinels["sent_001"].status == SentinelStatus.PAUSED

        state_manager.resume_sentinel("sent_001")
        assert state_manager.sentinels["sent_001"].status == SentinelStatus.ACTIVE

    def test_deactivate(self, state_manager, sample_config):
        state_manager.deploy_sentinel("sent_001", sample_config, "run_1")
        state_manager.deactivate_sentinel("sent_001", "Strategy failed")
        assert state_manager.sentinels["sent_001"].status == SentinelStatus.DEACTIVATED


# ---------- Paper Portfolio ----------

class TestPaperPortfolio:
    def test_open_and_close_position(self):
        portfolio = PaperPortfolio(100000.0)
        snapshot = EntryStateSnapshot(
            ticker="AAPL", entry_price=150.0, entry_date=datetime(2024, 1, 15),
            fundamental_metrics={}, thesis_summary="Test",
            target_price=180.0, stop_loss_price=135.0,
        )
        success = portfolio.open_position("AAPL", 100, 150.0, datetime(2024, 1, 15), snapshot)
        assert success is True
        assert portfolio.cash == 85000.0
        assert "AAPL" in portfolio.positions
        assert portfolio.nav == 100000.0  # NAV unchanged at entry

        trade = portfolio.close_position("AAPL", 170.0, datetime(2024, 3, 1), "Target")
        assert trade is not None
        assert trade["pnl"] == 2000.0
        assert "AAPL" not in portfolio.positions
        assert portfolio.cash == 102000.0

    def test_insufficient_cash(self):
        portfolio = PaperPortfolio(1000.0)
        snapshot = EntryStateSnapshot(
            ticker="AAPL", entry_price=150.0, entry_date=datetime(2024, 1, 1),
            fundamental_metrics={}, thesis_summary="Test",
        )
        success = portfolio.open_position("AAPL", 100, 150.0, datetime(2024, 1, 1), snapshot)
        assert success is False
        assert portfolio.cash == 1000.0

    def test_high_water_mark_updates(self):
        portfolio = PaperPortfolio(100000.0)
        snapshot = EntryStateSnapshot(
            ticker="AAPL", entry_price=150.0, entry_date=datetime(2024, 1, 1),
            fundamental_metrics={}, thesis_summary="Test",
        )
        portfolio.open_position("AAPL", 100, 150.0, datetime(2024, 1, 1), snapshot)
        portfolio.update_prices({"AAPL": 170.0})  # NAV goes up
        assert portfolio.high_water_mark == 102000.0  # 85k cash + 17k position

        portfolio.update_prices({"AAPL": 140.0})  # NAV drops
        assert portfolio.high_water_mark == 102000.0  # HWM stays at peak

    def test_nav_tracking(self):
        portfolio = PaperPortfolio(100000.0)
        assert portfolio.nav == 100000.0

        snapshot = EntryStateSnapshot(
            ticker="AAPL", entry_price=100.0, entry_date=datetime(2024, 1, 1),
            fundamental_metrics={}, thesis_summary="Test",
        )
        portfolio.open_position("AAPL", 100, 100.0, datetime(2024, 1, 1), snapshot)
        assert portfolio.nav == 100000.0  # Entry: 100 shares * $100 = $10k, cash = $90k

        portfolio.update_prices({"AAPL": 110.0})
        assert portfolio.nav == 101000.0  # $90k + 100 * $110 = $101k


# ---------- Close Signal Integration ----------

class TestCloseSignalIntegration:
    def _setup_position(self, state_manager, sample_config, tmp_path):
        """Deploy sentinel and manually inject a position."""
        state_manager.KNOWN_UNIVERSE_DIR = str(tmp_path)
        sentinel = state_manager.deploy_sentinel("sent_001", sample_config, "run_1")

        snapshot = EntryStateSnapshot(
            ticker="AAPL", entry_price=150.0, entry_date=datetime(2024, 1, 15),
            fundamental_metrics={"eps": 6.5},
            thesis_summary="iPhone cycle",
            target_price=180.0, stop_loss_price=135.0, max_hold_days=90,
        )
        sentinel.portfolio.open_position("AAPL", 100, 150.0, datetime(2024, 1, 15), snapshot)
        return sentinel

    def test_stop_triggered_generates_close_card(self, state_manager, sample_config, tmp_path):
        sentinel = self._setup_position(state_manager, sample_config, tmp_path)

        signals = state_manager.evaluate_close_signals(
            sentinel_id="sent_001",
            current_prices={"AAPL": 130.0},  # Below stop of $135
            current_date=datetime(2024, 2, 1),
            current_fundamentals={"AAPL": {"eps": 6.4}},
        )
        assert len(signals) == 1
        assert signals[0].exit_type == ExitType.STOP_TRIGGERED
        assert len(sentinel.pending_cards) == 1
        assert sentinel.pending_cards[0].decision == "CLOSE"

    def test_no_exit_no_card(self, state_manager, sample_config, tmp_path):
        sentinel = self._setup_position(state_manager, sample_config, tmp_path)

        signals = state_manager.evaluate_close_signals(
            sentinel_id="sent_001",
            current_prices={"AAPL": 160.0},  # Normal price
            current_date=datetime(2024, 2, 1),
            current_fundamentals={"AAPL": {"eps": 6.4}},
        )
        assert len(signals) == 0
        assert len(sentinel.pending_cards) == 0

    def test_paused_sentinel_skipped(self, state_manager, sample_config, tmp_path):
        sentinel = self._setup_position(state_manager, sample_config, tmp_path)
        state_manager.pause_sentinel("sent_001")

        signals = state_manager.evaluate_close_signals(
            sentinel_id="sent_001",
            current_prices={"AAPL": 100.0},  # Way below stop
            current_date=datetime(2024, 2, 1),
            current_fundamentals={"AAPL": {"eps": 6.4}},
        )
        assert len(signals) == 0  # Paused = no evaluation


# ---------- ACCEPT/DECLINE Flow ----------

class TestAcceptDecline:
    def _deploy_with_buy_card(self, state_manager, sample_config, tmp_path):
        state_manager.KNOWN_UNIVERSE_DIR = str(tmp_path)
        sentinel = state_manager.deploy_sentinel("sent_001", sample_config, "run_1")

        card = SignalCard(
            sentinel_id="sent_001", ticker="MSFT", decision="BUY",
            shares=50, price=380.0, portfolio_pct=0.19,
            target_price=420.0, stop_loss_price=350.0,
            hold_duration_days=60, thesis="Cloud growth",
            confidence=0.85,
        )
        sentinel.pending_cards.append(card)
        return sentinel, card

    def test_accept_buy_opens_position(self, state_manager, sample_config, tmp_path):
        sentinel, card = self._deploy_with_buy_card(state_manager, sample_config, tmp_path)

        result = state_manager.process_review("sent_001", card.card_id, "ACCEPTED", 380.0)
        assert result["executed"] is True
        assert "MSFT" in sentinel.portfolio.positions
        assert sentinel.portfolio.positions["MSFT"].shares == 50

    def test_decline_buy_does_not_open(self, state_manager, sample_config, tmp_path):
        sentinel, card = self._deploy_with_buy_card(state_manager, sample_config, tmp_path)

        result = state_manager.process_review("sent_001", card.card_id, "DECLINED", 380.0)
        assert result["executed"] is False
        assert "MSFT" not in sentinel.portfolio.positions
        assert result["counterfactual_tracked"] is True

    def test_accept_close_removes_position(self, state_manager, sample_config, tmp_path):
        state_manager.KNOWN_UNIVERSE_DIR = str(tmp_path)
        sentinel = state_manager.deploy_sentinel("sent_001", sample_config, "run_1")

        # Open a position first
        snapshot = EntryStateSnapshot(
            ticker="AAPL", entry_price=150.0, entry_date=datetime(2024, 1, 15),
            fundamental_metrics={}, thesis_summary="Test",
            target_price=180.0, stop_loss_price=135.0,
        )
        sentinel.portfolio.open_position("AAPL", 100, 150.0, datetime(2024, 1, 15), snapshot)

        # Create a CLOSE card
        card = SignalCard(
            sentinel_id="sent_001", ticker="AAPL", decision="CLOSE",
            shares=100, price=180.0, portfolio_pct=0.18,
            target_price=180.0, stop_loss_price=135.0,
            hold_duration_days=30, thesis="Target reached",
            confidence=0.9,
        )
        card.close_signal = CloseSignal(
            ticker="AAPL", exit_type=ExitType.TARGET_APPROACHED,
            reason="Target reached", urgency="end_of_day",
            current_price=180.0, entry_price=150.0,
            unrealized_pnl_pct=0.2, supporting_data={},
        )
        sentinel.pending_cards.append(card)

        result = state_manager.process_review("sent_001", card.card_id, "ACCEPTED", 180.0)
        assert result["executed"] is True
        assert "AAPL" not in sentinel.portfolio.positions
        assert result["trade"]["pnl"] == 3000.0  # (180-150) * 100

    def test_card_moves_to_history(self, state_manager, sample_config, tmp_path):
        sentinel, card = self._deploy_with_buy_card(state_manager, sample_config, tmp_path)
        card_id = card.card_id

        state_manager.process_review("sent_001", card_id, "ACCEPTED", 380.0)
        assert len(sentinel.pending_cards) == 0
        assert len(sentinel.card_history) == 1
        assert sentinel.card_history[0].card_id == card_id


# ---------- Known Universe ----------

class TestKnownUniverse:
    def test_universe_updated_on_position_change(self, state_manager, sample_config, tmp_path):
        state_manager.KNOWN_UNIVERSE_DIR = str(tmp_path)
        sentinel = state_manager.deploy_sentinel("sent_001", sample_config, "run_1")

        # Add a BUY card and accept it
        card = SignalCard(
            sentinel_id="sent_001", ticker="AAPL", decision="BUY",
            shares=100, price=150.0, portfolio_pct=0.15,
            target_price=180.0, stop_loss_price=135.0,
            hold_duration_days=90, thesis="iPhone cycle",
            confidence=0.8,
        )
        sentinel.pending_cards.append(card)
        state_manager.process_review("sent_001", card.card_id, "ACCEPTED", 150.0)

        path = tmp_path / "sent_001_universe.json"
        data = json.loads(path.read_text())
        assert len(data["holdings"]) == 1
        assert data["holdings"][0]["ticker"] == "AAPL"

    def test_get_known_universe_structure(self, state_manager, sample_config, tmp_path):
        state_manager.KNOWN_UNIVERSE_DIR = str(tmp_path)
        state_manager.deploy_sentinel("sent_001", sample_config, "run_1")

        universe = state_manager.get_known_universe("sent_001")
        assert "sentinel_id" in universe
        assert "generated_at" in universe
        assert "holdings" in universe
        assert "macro_watches" in universe


# ---------- State API ----------

class TestSentinelState:
    def test_get_state(self, state_manager, sample_config, tmp_path):
        state_manager.KNOWN_UNIVERSE_DIR = str(tmp_path)
        state_manager.deploy_sentinel("sent_001", sample_config, "run_1")

        state = state_manager.get_sentinel_state("sent_001")
        assert state["sentinel_id"] == "sent_001"
        assert state["status"] == "active"
        assert "portfolio" in state
        assert "pending_cards" in state
        assert "gap_analysis" in state
