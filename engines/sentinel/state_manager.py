"""
Sentinel State Manager (Phase 4 — Complete)

Orchestrates live deployed strategies:
  - Manages Sentinel lifecycle (deploy, pause, deactivate)
  - Runs signal evaluation pipeline on heartbeat
  - Integrates CloseSignalGenerator for exit checks on open positions
  - Maintains paper portfolio with real position tracking
  - Generates Signal Cards for user review
  - Writes known_universe.json for OpenClaw consumption
  - Tracks counterfactual via MirrorPortfolio
"""
import json
import uuid
import logging
import os
from datetime import datetime, date
from typing import Dict, Any, List, Optional
from enum import Enum

from pydantic import BaseModel, Field
from engines.vcl.component import VCLComponent, HealthStatus, HealthResult, ComponentRole

from engines.monitoring.connector_health import ConnectorHealthMonitor
from engines.data_ingestion.data_engine import DataEngine
from engines.sentinel.close_signal_generator import (
    CloseSignalGenerator,
    EntryStateSnapshot,
    CloseSignal,
    ExitType,
)
from engines.sentinel.mirror_portfolio import CounterfactualTracker

logger = logging.getLogger(__name__)


class SentinelStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"       # Temporarily paused (connector issues, etc.)
    REVIEW = "review"       # Tier 3 event triggered — awaiting user review
    DEACTIVATED = "deactivated"


class SignalCard:
    """A generated recommendation pending user review."""
    def __init__(
        self,
        sentinel_id: str,
        ticker: str,
        decision: str,
        shares: int,
        price: float,
        portfolio_pct: float,
        target_price: Optional[float],
        stop_loss_price: Optional[float],
        hold_duration_days: int,
        thesis: str,
        confidence: float,
        session_quality: str = "nominal",
    ):
        self.card_id = str(uuid.uuid4())
        self.sentinel_id = sentinel_id
        self.ticker = ticker
        self.decision = decision  # "BUY" | "CLOSE"
        self.shares = shares
        self.price = price
        self.portfolio_pct = portfolio_pct
        self.target_price = target_price
        self.stop_loss_price = stop_loss_price
        self.hold_duration_days = hold_duration_days
        self.thesis = thesis
        self.confidence = confidence
        self.session_quality = session_quality
        self.generated_at = datetime.utcnow()
        self.status = "PENDING"  # PENDING → ACCEPTED | DECLINED

        # Close signal info (filled for CLOSE cards)
        self.close_signal: Optional[CloseSignal] = None

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "card_id": self.card_id,
            "sentinel_id": self.sentinel_id,
            "ticker": self.ticker,
            "decision": self.decision,
            "shares": self.shares,
            "price": self.price,
            "portfolio_pct": self.portfolio_pct,
            "target_price": self.target_price,
            "stop_loss_price": self.stop_loss_price,
            "hold_duration_days": self.hold_duration_days,
            "thesis": self.thesis,
            "confidence": self.confidence,
            "session_quality": self.session_quality,
            "generated_at": self.generated_at.isoformat(),
            "status": self.status,
        }
        if self.close_signal:
            d["close_signal"] = self.close_signal.to_dict()
        return d


class Position:
    """A tracked position in the paper portfolio."""
    def __init__(
        self,
        ticker: str,
        shares: int,
        entry_price: float,
        entry_date: datetime,
        snapshot: EntryStateSnapshot,
    ):
        self.ticker = ticker
        self.shares = shares
        self.entry_price = entry_price
        self.entry_date = entry_date
        self.current_price = entry_price
        self.snapshot = snapshot

    @property
    def market_value(self) -> float:
        return self.shares * self.current_price

    @property
    def unrealized_pnl(self) -> float:
        return (self.current_price - self.entry_price) * self.shares

    @property
    def unrealized_pnl_pct(self) -> float:
        if self.entry_price == 0:
            return 0.0
        return (self.current_price - self.entry_price) / self.entry_price

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ticker": self.ticker,
            "shares": self.shares,
            "entry_price": self.entry_price,
            "entry_date": self.entry_date.isoformat() if isinstance(self.entry_date, (datetime, date)) else str(self.entry_date),
            "current_price": self.current_price,
            "market_value": self.market_value,
            "unrealized_pnl": self.unrealized_pnl,
            "unrealized_pnl_pct": self.unrealized_pnl_pct,
        }


class PaperPortfolio:
    """Real paper portfolio with proper position tracking."""
    def __init__(self, initial_cash: float):
        self.initial_cash = initial_cash
        self.cash = initial_cash
        self.positions: Dict[str, Position] = {}
        self.closed_trades: List[Dict[str, Any]] = []
        self.high_water_mark = initial_cash

    @property
    def nav(self) -> float:
        return self.cash + sum(p.market_value for p in self.positions.values())

    def update_high_water_mark(self):
        """Update HWM after price updates."""
        current_nav = self.nav
        if current_nav > self.high_water_mark:
            self.high_water_mark = current_nav

    def open_position(
        self,
        ticker: str,
        shares: int,
        price: float,
        entry_date: datetime,
        snapshot: EntryStateSnapshot,
    ) -> bool:
        """Opens a new position. Returns False if insufficient cash."""
        cost = shares * price
        if cost > self.cash:
            logger.warning(f"Insufficient cash for {ticker}: need ${cost:.2f}, have ${self.cash:.2f}")
            return False

        self.cash -= cost
        self.positions[ticker] = Position(
            ticker=ticker,
            shares=shares,
            entry_price=price,
            entry_date=entry_date,
            snapshot=snapshot,
        )
        logger.info(f"Opened position: {shares} shares of {ticker} @ ${price:.2f}")
        return True

    def close_position(self, ticker: str, price: float, close_date: datetime, reason: str) -> Optional[Dict[str, Any]]:
        """Closes a position and records the trade."""
        if ticker not in self.positions:
            return None

        position = self.positions[ticker]
        revenue = position.shares * price
        self.cash += revenue

        trade_record = {
            "ticker": ticker,
            "entry_price": position.entry_price,
            "exit_price": price,
            "shares": position.shares,
            "pnl": (price - position.entry_price) * position.shares,
            "pnl_pct": (price - position.entry_price) / position.entry_price if position.entry_price > 0 else 0,
            "entry_date": str(position.entry_date),
            "exit_date": str(close_date),
            "exit_reason": reason,
        }
        self.closed_trades.append(trade_record)
        del self.positions[ticker]

        logger.info(f"Closed {ticker}: {trade_record['pnl_pct']:+.1%} ({reason})")
        return trade_record

    def update_prices(self, prices: Dict[str, float]):
        """Mark-to-market all positions."""
        for ticker, price in prices.items():
            if ticker in self.positions:
                self.positions[ticker].current_price = price
        self.update_high_water_mark()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cash": self.cash,
            "nav": self.nav,
            "high_water_mark": self.high_water_mark,
            "positions": {
                ticker: pos.to_dict() for ticker, pos in self.positions.items()
            },
            "num_closed_trades": len(self.closed_trades),
        }


class Sentinel:
    """A promoted strategy running in live monitoring."""
    def __init__(
        self,
        sentinel_id: str,
        config: Dict[str, Any],
        promoted_run_id: str,
        initial_cash: float = 100000.0,
    ):
        self.sentinel_id = sentinel_id
        self.config = config
        self.promoted_run_id = promoted_run_id
        self.status = SentinelStatus.ACTIVE
        self.deployed_at = datetime.utcnow()

        # Paper portfolio
        self.portfolio = PaperPortfolio(initial_cash)

        # Counterfactual tracking
        self.counterfactual = CounterfactualTracker(sentinel_id, initial_cash)

        # Close signal generator from config
        exit_config = config.get("exit_conditions", {})
        self.close_generator = CloseSignalGenerator.from_config(exit_config)

        # Signal card queue
        self.pending_cards: List[SignalCard] = []
        self.card_history: List[SignalCard] = []

    def get_tickers(self) -> List[str]:
        """Get the asset universe for this sentinel."""
        return self.config.get("asset_universe", {}).get("tickers", [])


class SentinelStateInput(BaseModel):
    sentinel_id: str = Field(min_length=1)
    current_prices: Dict[str, float] = Field(default_factory=dict)
    current_date: datetime = Field(default_factory=datetime.utcnow)
    current_fundamentals: Dict[str, Dict[str, float]] = Field(default_factory=dict)


class SentinelStateOutput(BaseModel):
    close_signals: List[CloseSignal] = Field(default_factory=list)


class SentinelStateManager(VCLComponent):
    """
    Manages all live Sentinels and orchestrates the signal and close pipeline.
    """
    KNOWN_UNIVERSE_DIR = "data/known_universe"
    component_id = "aegis.system.sentinel_state_manager"
    version = "1.0.0"
    role = ComponentRole.EXECUTOR
    input_schema = SentinelStateInput
    output_schema = SentinelStateOutput

    def __init__(self, data_engine: DataEngine, health_monitor: ConnectorHealthMonitor):
        self.data_engine = data_engine
        self.health_monitor = health_monitor
        self.sentinels: Dict[str, Sentinel] = {}

    def execute(self, input_data: SentinelStateInput) -> SentinelStateOutput:
        """VCL standard execute hook."""
        signals = self.evaluate_close_signals(
            sentinel_id=input_data.sentinel_id,
            current_prices=input_data.current_prices,
            current_date=input_data.current_date,
            current_fundamentals=input_data.current_fundamentals
        )
        return SentinelStateOutput(close_signals=signals)

    def health(self) -> HealthResult:
        """Sentinel State Manager health depends on connector health monitor."""
        if self.health_monitor.is_any_connector_offline():
            return HealthResult(status=HealthStatus.DEGRADED, reason="Underlying connectors offline")
        return HealthResult(status=HealthStatus.HEALTHY)



    def deploy_sentinel(
        self,
        sentinel_id: str,
        config: Dict[str, Any],
        promoted_run_id: str,
        initial_cash: float = 100000.0,
    ) -> Sentinel:
        """Deploy a promoted strategy as a live Sentinel."""
        if sentinel_id in self.sentinels:
            raise ValueError(f"Sentinel {sentinel_id} already deployed")

        sentinel = Sentinel(sentinel_id, config, promoted_run_id, initial_cash)
        self.sentinels[sentinel_id] = sentinel

        # Write initial known universe
        self._write_known_universe(sentinel)

        logger.info(f"Deployed Sentinel {sentinel_id} (run: {promoted_run_id})")
        return sentinel

    def pause_sentinel(self, sentinel_id: str, reason: str = "Manual pause"):
        """Temporarily pause a sentinel."""
        sentinel = self._get_sentinel(sentinel_id)
        sentinel.status = SentinelStatus.PAUSED
        logger.info(f"Paused Sentinel {sentinel_id}: {reason}")

    def resume_sentinel(self, sentinel_id: str):
        """Resume a paused sentinel."""
        sentinel = self._get_sentinel(sentinel_id)
        if sentinel.status == SentinelStatus.PAUSED:
            sentinel.status = SentinelStatus.ACTIVE
            logger.info(f"Resumed Sentinel {sentinel_id}")

    def deactivate_sentinel(self, sentinel_id: str, reason: str = "Manual deactivation"):
        """Permanently deactivate a sentinel."""
        sentinel = self._get_sentinel(sentinel_id)
        sentinel.status = SentinelStatus.DEACTIVATED
        logger.info(f"Deactivated Sentinel {sentinel_id}: {reason}")

    def evaluate_close_signals(
        self,
        sentinel_id: str,
        current_prices: Dict[str, float],
        current_date: datetime,
        current_fundamentals: Dict[str, Dict[str, float]],
    ) -> List[CloseSignal]:
        """
        Check all open positions against the 5 exit rules.
        Returns a list of triggered CloseSignals (one per position that should close).
        """
        sentinel = self._get_sentinel(sentinel_id)

        if sentinel.status != SentinelStatus.ACTIVE:
            return []

        # Update prices first
        sentinel.portfolio.update_prices(current_prices)

        close_signals: List[CloseSignal] = []

        for ticker, position in list(sentinel.portfolio.positions.items()):
            price = current_prices.get(ticker, position.current_price)
            fundamentals = current_fundamentals.get(ticker, {})

            signal = sentinel.close_generator.evaluate_position(
                current_price=price,
                current_date=current_date,
                current_fundamentals=fundamentals,
                portfolio_nav=sentinel.portfolio.nav,
                portfolio_high_water_mark=sentinel.portfolio.high_water_mark,
                snapshot=position.snapshot,
            )

            if signal:
                close_signals.append(signal)

                # Generate a Close Signal Card
                card = SignalCard(
                    sentinel_id=sentinel_id,
                    ticker=ticker,
                    decision="CLOSE",
                    shares=position.shares,
                    price=price,
                    portfolio_pct=position.market_value / sentinel.portfolio.nav if sentinel.portfolio.nav > 0 else 0,
                    target_price=position.snapshot.target_price,
                    stop_loss_price=position.snapshot.stop_loss_price,
                    hold_duration_days=(current_date - position.entry_date).days if isinstance(position.entry_date, datetime) else 0,
                    thesis=f"Exit: {signal.exit_type.value} — {signal.reason}",
                    confidence=1.0 if signal.urgency == "immediate" else 0.8,
                )
                card.close_signal = signal
                sentinel.pending_cards.append(card)

        return close_signals

    def process_review(
        self,
        sentinel_id: str,
        card_id: str,
        action: str,
        execution_price: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Process user ACCEPT/DECLINE on a Signal Card.

        - ACCEPT: Paper portfolio executes. Counterfactual also tracks.
        - DECLINE: Paper portfolio does NOT execute. Counterfactual tracks the hypothetical.
        """
        sentinel = self._get_sentinel(sentinel_id)

        card = None
        for c in sentinel.pending_cards:
            if c.card_id == card_id:
                card = c
                break

        if card is None:
            raise ValueError(f"Card {card_id} not found in Sentinel {sentinel_id}")

        price = execution_price or card.price
        card.status = action
        now = datetime.utcnow()

        result = {
            "card_id": card_id,
            "action": action,
            "ticker": card.ticker,
            "decision": card.decision,
        }

        if card.decision == "BUY":
            # Counterfactual always executes
            sentinel.counterfactual.handle_signal_resolution(
                ticker=card.ticker,
                decision="BUY",
                action=action,
                execution_price=price,
                quantity=card.shares,
                current_date=now,
            )

            if action == "ACCEPTED":
                # Create entry state snapshot
                snapshot = EntryStateSnapshot(
                    ticker=card.ticker,
                    entry_price=price,
                    entry_date=now,
                    fundamental_metrics={},  # Populated by data engine at signal time
                    thesis_summary=card.thesis,
                    target_price=card.target_price,
                    stop_loss_price=card.stop_loss_price,
                    max_hold_days=card.hold_duration_days,
                )
                success = sentinel.portfolio.open_position(
                    ticker=card.ticker,
                    shares=card.shares,
                    price=price,
                    entry_date=now,
                    snapshot=snapshot,
                )
                result["executed"] = success
                if success:
                    self._write_known_universe(sentinel)
            else:
                result["executed"] = False
                result["counterfactual_tracked"] = True

        elif card.decision == "CLOSE":
            # Counterfactual tracks the close
            sentinel.counterfactual.handle_signal_resolution(
                ticker=card.ticker,
                decision="SELL",
                action=action,
                execution_price=price,
                quantity=card.shares,
                current_date=now,
            )

            if action == "ACCEPTED":
                trade = sentinel.portfolio.close_position(
                    ticker=card.ticker,
                    price=price,
                    close_date=now,
                    reason=card.close_signal.exit_type.value if card.close_signal else "Manual",
                )
                result["executed"] = trade is not None
                result["trade"] = trade
                if trade:
                    self._write_known_universe(sentinel)
            else:
                result["executed"] = False
                result["counterfactual_tracked"] = True

        # Move to history
        sentinel.pending_cards.remove(card)
        sentinel.card_history.append(card)

        logger.info(f"Processed card {card_id}: {action} {card.decision} {card.ticker}")
        return result

    def get_sentinel_state(self, sentinel_id: str) -> Dict[str, Any]:
        """Full state of a sentinel for API/UI."""
        sentinel = self._get_sentinel(sentinel_id)
        return {
            "sentinel_id": sentinel_id,
            "status": sentinel.status.value,
            "deployed_at": sentinel.deployed_at.isoformat(),
            "promoted_run_id": sentinel.promoted_run_id,
            "portfolio": sentinel.portfolio.to_dict(),
            "pending_cards": [c.to_dict() for c in sentinel.pending_cards],
            "card_history_count": len(sentinel.card_history),
            "gap_analysis": sentinel.counterfactual.get_gap_analysis(),
        }

    def get_known_universe(self, sentinel_id: str) -> Dict[str, Any]:
        """
        Returns the Known Universe for OpenClaw consumption.
        Contains holdings, dependency maps, and macro watches.
        """
        sentinel = self._get_sentinel(sentinel_id)

        holdings = []
        for ticker, position in sentinel.portfolio.positions.items():
            holdings.append({
                "ticker": ticker,
                "thesis": position.snapshot.thesis_summary,
                "entry_price": position.entry_price,
                "entry_date": str(position.entry_date),
                "position_pct": position.market_value / sentinel.portfolio.nav if sentinel.portfolio.nav > 0 else 0,
                "dependency_map": {
                    "commodity_inputs": [],
                    "geographic_risk": [],
                    "macro_sensitivities": [],
                    "key_customers": [],
                    "regulatory_exposure": [],
                },
            })

        return {
            "sentinel_id": sentinel_id,
            "generated_at": datetime.utcnow().isoformat(),
            "holdings": holdings,
            "macro_watches": [],
            "upcoming_events": [],
        }

    def _write_known_universe(self, sentinel: Sentinel):
        """Write known_universe.json for OpenClaw to read."""
        universe = self.get_known_universe(sentinel.sentinel_id)

        os.makedirs(self.KNOWN_UNIVERSE_DIR, exist_ok=True)
        path = os.path.join(self.KNOWN_UNIVERSE_DIR, f"{sentinel.sentinel_id}_universe.json")
        with open(path, "w") as f:
            json.dump(universe, f, indent=2)

        logger.info(f"Wrote known universe for {sentinel.sentinel_id} to {path}")

    def _get_sentinel(self, sentinel_id: str) -> Sentinel:
        if sentinel_id not in self.sentinels:
            raise ValueError(f"Sentinel {sentinel_id} not found")
        return self.sentinels[sentinel_id]
