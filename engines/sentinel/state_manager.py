"""
Sentinel State Manager (Phase 4)
Orchestrates live deployment of Promoted Configurations.
Runs the live signal pipeline, manages Signal Card queues, and tracks NAV.
"""
import uuid
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from engines.monitoring.connector_health import ConnectorHealthMonitor
from engines.data_ingestion.data_engine import DataEngine
class Portfolio:
    """Stub for paper portfolio tracking (to be expanded in Step 24)."""
    def __init__(self, initial_cash: float):
        self.nav = initial_cash
        self.positions = {}

logger = logging.getLogger(__name__)

class SignalCard:
    """A generated recommendation pending user review."""
    def __init__(self, sentinel_id: str, ticker: str, decision: str, thesis: str, 
                 quant_anchors: Dict[str, Any], sub_agent_votes: Dict[str, str], confidence: float):
        self.card_id = str(uuid.uuid4())
        self.sentinel_id = sentinel_id
        self.ticker = ticker
        self.decision = decision
        self.thesis = thesis
        self.quant_anchors = quant_anchors
        self.sub_agent_votes = sub_agent_votes
        self.confidence = confidence
        self.generated_at = datetime.now()
        self.status = "PENDING"  # PENDING, ACCEPTED, DECLINED

class Sentinel:
    """A promoted configuration running live."""
    def __init__(self, sentinel_id: str, config: Dict[str, Any], promoted_run_id: str):
        self.sentinel_id = sentinel_id
        self.config = config
        self.promoted_run_id = promoted_run_id
        self.is_active = True
        self.portfolio = Portfolio(initial_cash=config.get("sandbox", {}).get("capital", 100000))
        self.pending_cards: List[SignalCard] = []

class SentinelStateManager:
    """
    Manages all live Sentinels and orchestrates the signal pipeline.
    """
    def __init__(self, data_engine: DataEngine, health_monitor: ConnectorHealthMonitor):
        self.data_engine = data_engine
        self.health_monitor = health_monitor
        self.sentinels: Dict[str, Sentinel] = {}

    def deploy_sentinel(self, sentinel_id: str, config: Dict[str, Any], promoted_run_id: str) -> Sentinel:
        """Deploy a new promoted configuration as a live Sentinel."""
        if sentinel_id in self.sentinels:
            raise ValueError(f"Sentinel {sentinel_id} is already deployed.")
        
        # In a real system, we'd verify the promoted_run_id was actually promoted in MLflow
        
        sentinel = Sentinel(sentinel_id, config, promoted_run_id)
        self.sentinels[sentinel_id] = sentinel
        logger.info(f"Deployed Sentinel: {sentinel_id} (Config version: {config.get('version')})")
        return sentinel

    def evaluate_pipeline(self, current_date: datetime):
        """
        Evaluate the live market data for all active Sentinels and generate cards.
        """
        if not self.health_monitor.can_generate_signals():
            logger.warning("Signal generation suspended due to OFFLINE connectors.")
            return

        for sentinel_id, sentinel in self.sentinels.items():
            if not sentinel.is_active:
                continue

            # 1. Fetch live data for configured universe
            tickers = sentinel.config.get("asset_universe", {}).get("tickers", [])
            for ticker in tickers:
                # In full implementation:
                # 2. Run Quant Engine
                # 3. gating logic -> invoke LangGraph Analyst Engine
                # 4. If BUY/SELL recommendation generated -> Queue Signal Card
                
                # Mock generation for testing queue
                pass

    def queue_signal_card(self, card: SignalCard):
        """Add a Signal Card to the Sentinel's queue for human review."""
        if card.sentinel_id not in self.sentinels:
            raise ValueError(f"Unknown Sentinel ID: {card.sentinel_id}")
            
        self.sentinels[card.sentinel_id].pending_cards.append(card)
        logger.info(f"Queued Signal Card {card.card_id} for {card.sentinel_id}: {card.decision} {card.ticker}")

    def process_review(self, card_id: str, sentinel_id: str, action: str):
        """User accepts or declines a Signal Card."""
        sentinel = self.sentinels.get(sentinel_id)
        if not sentinel:
            raise ValueError("Sentinel not found")

        for card in sentinel.pending_cards:
            if card.card_id == card_id:
                card.status = action
                logger.info(f"User {action} Signal Card {card_id}")
                
                # If ACCEPTED, the Sentinel's paper portfolio executes it
                if action == "ACCEPTED":
                    # MOCK execution logic
                    pass
                
                # Move to historical ledger (omitted for brevity)
                sentinel.pending_cards.remove(card)
                return True
        return False
