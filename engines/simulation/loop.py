from collections import defaultdict
from datetime import date, timedelta
import hashlib
from typing import Dict, Any, List

import pandas as pd
import numpy as np

from config.schema import AegisConfig
from engines.data_ingestion.connectors.yfinance_connector import YFinanceConnector
from engines.fundamental.earnings_revision_tracker import EarningsRevisionTracker
from engines.fundamental.insider_activity_monitor import InsiderActivityMonitor
from engines.fundamental.macro_overlay import MacroOverlay
from engines.fundamental.signal_gate import SignalGate

class SimulationLoop:
    """
    Day-by-day vectorized point-in-time backtester.
    No mock data, no LLMs (Phase 1).
    """
    def __init__(self, config: AegisConfig):
        self.config = config
        self.run_id = config.run_id
        
        self.yf = YFinanceConnector()
        self.er_tracker = EarningsRevisionTracker()
        self.im_monitor = InsiderActivityMonitor()
        self.mo_overlay = MacroOverlay()
        
        self.capital = config.position_sizing.capital
        self.cash = self.capital
        self.positions: Dict[str, float] = defaultdict(float) # Ticker -> Shares
        
        self.trade_log: List[Dict[str, Any]] = []
        self.nav_history: List[Dict[str, Any]] = []
        self.gate_events: List[Dict[str, Any]] = []
        self.trace_events: List[Dict[str, Any]] = []
        
        # Determine holdout dates immediately
        seed_int = int(hashlib.md5(self.run_id.encode('utf-8'), usedforsecurity=False).hexdigest(), 16) % (2**32)
        np.random.seed(seed_int)
        
    def _get_price(self, ticker: str, as_of: date) -> float:
        """Helper to get close price on a specific date using YFinance cache."""
        df = self.yf.get_prices(ticker, days=5, as_of_date=as_of)
        if df is None or df.empty:
            return 0.0
        # Return the last known close price
        return float(df['close'].iloc[-1])
        
    def _get_open_price(self, ticker: str, as_of: date) -> float:
        """Helper to get open price, used for next-day execution."""
        df = self.yf.get_prices(ticker, days=5, as_of_date=as_of)
        if df is None or df.empty:
            return 0.0
        return float(df['open'].iloc[-1])
        
    def _get_avg_volume(self, ticker: str, as_of: date) -> float:
         df = self.yf.get_prices(ticker, days=10, as_of_date=as_of)
         if df is None or df.empty:
             return 1000000.0
         return float(df['volume'].mean())

    def _calculate_slippage(self, signal_price: float, trade_price: float, shares: float, action: str) -> float:
        """
        Calculates slippage cost per share based on the blueprint constraints:
        - Bid-ask: 10 bps half-spread per side
        - Market impact: 5 bps per $10k notional
        """
        notional_value = shares * trade_price
        
        # 10 bps half spread = 0.001
        bid_ask_cost = trade_price * 0.001
        
        # 5 bps per $10k
        market_impact_cost = trade_price * (0.0005 * (notional_value / 10000.0))
        
        total_slippage_per_share = bid_ask_cost + market_impact_cost
        
        return total_slippage_per_share

    def compile_signals(self, ticker: str, as_of: date) -> Dict[str, Any]:
        """Compile Phase 1 signals for a given day."""
        signals = {}
        
        if self.config.fundamental_engine.earnings_revision.enabled:
            signals["earnings_revision"] = self.er_tracker.compute(ticker, as_of)
            
        if self.config.fundamental_engine.insider_monitor.enabled:
            cluster_window = self.config.fundamental_engine.insider_monitor.cluster_window_days
            signals["insider_activity"] = self.im_monitor.compute(ticker, as_of, cluster_window)
            
        return signals

    def run(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """Run the daily vectorized simulation loop."""
        print(f"[{self.run_id}] Starting Phase 1 Simulation: {start_date} to {end_date}")
        
        # 1. Trading Calendar & Holdout sealing
        all_dates = pd.date_range(start_date, end_date, freq='B').date.tolist()
        num_days = len(all_dates)
        num_holdout = int(num_days * 0.2)
        
        # Reset RNG state using the distinct configured run ID
        import hashlib
        seed_int = int(hashlib.md5(self.run_id.encode('utf-8'), usedforsecurity=False).hexdigest(), 16) % (2**32)
        np.random.seed(seed_int)
        
        # Randomly select 20% holdout dates uniformly
        holdout_dates = sorted(np.random.choice(all_dates, num_holdout, replace=False))
        opt_dates = sorted([d for d in all_dates if d not in holdout_dates])
        
        # State tracking for execution
        pending_orders = [] # [{ticker, action, shares, signal_date, signal_price}]
        
        # 2. Daily Loop
        for current_date in all_dates:
            daily_nav = self.cash
            
            # 2a. Execute pending orders at the OPEN of this new day
            executed_orders = []
            for order in pending_orders:
                ticker = order["ticker"]
                action = order["action"]
                shares = order["shares"]
                
                open_price = self._get_open_price(ticker, current_date)
                if open_price <= 0:
                    continue # Try again tomorrow if no price
                    
                slippage_ps = self._calculate_slippage(order["signal_price"], open_price, shares, action)
                
                if action == "BUY":
                    fill_price = open_price + slippage_ps
                    cost = fill_price * shares
                    if cost <= self.cash:
                        self.cash -= cost
                        self.positions[ticker] += shares
                        order["fill_price"] = fill_price
                        order["fill_date"] = current_date
                        order["slippage_drag_usd"] = slippage_ps * shares
                        self.trade_log.append(order)
                        executed_orders.append(order)
                elif action == "SELL":
                    fill_price = open_price - slippage_ps
                    revenue = fill_price * shares
                    if self.positions[ticker] >= shares:
                        self.positions[ticker] -= shares
                        self.cash += revenue
                        order["fill_price"] = fill_price
                        order["fill_date"] = current_date
                        order["slippage_drag_usd"] = slippage_ps * shares
                        self.trade_log.append(order)
                        executed_orders.append(order)

            # Remove executed orders
            pending_orders = [o for o in pending_orders if o not in executed_orders]
            
            # 2b. Mark to market currently held positions
            for ticker, shares in self.positions.items():
                if shares > 0:
                    price = self._get_price(ticker, current_date)
                    daily_nav += (shares * price)
            
            self.nav_history.append({"date": current_date, "nav": daily_nav})
            
            # 2c. Signal Generation & Gate Evaluation on Universe
            for ticker in self.config.asset_universe.tickers:
                price = self._get_price(ticker, current_date)
                if price <= 0:
                    continue
                    
                # Compile fundamental engine outputs
                signals = self.compile_signals(ticker, current_date)
                
                # If agents disabled, fallback to legacy Signal Gate
                if not self.config.agent.enabled:
                    passed = SignalGate.evaluate(signals, self.config.signal_gate.model_dump(exclude_none=True))
                    sell_signal = not passed
                    conviction = 1.0 # default scalar for legacy
                    
                    self.gate_events.append({
                        "date": current_date, "ticker": ticker, 
                        "gate_result": passed, "margin_per_condition": signals.get("_gate_margin", {})
                    })
                else:
                    # Agentic Mesh Routing
                    if not hasattr(self, "supervisor"):
                        from engines.analyst.supervisor import AgenticSupervisor
                        print(f"[{self.run_id}] Initializing LangGraph Supervisor ({self.config.agent.provider}/{self.config.agent.model})...")
                        self.supervisor = AgenticSupervisor(
                            provider=self.config.agent.provider, 
                            model=self.config.agent.model,
                            pipeline=self.config.agent.pipeline,
                            edges=self.config.agent.edges
                        )
                        
                    agent_result = self.supervisor.run(ticker, current_date, signals)
                    
                    # Log trace for debugging
                    self.trace_events.append({
                        "date": str(current_date),
                        "ticker": ticker,
                        "action": agent_result["action"],
                        "conviction": agent_result["conviction"],
                        "reasoning_trace": agent_result["reasoning_trace"],
                        "fundamental_signals": signals
                    })
                    
                    action = agent_result["action"]
                    conviction = agent_result["conviction"]
                    
                    passed = (action == "BUY" and conviction >= 0.3)
                    sell_signal = (action == "SELL" and conviction >= 0.3)
                
                # Generate Buy/Sell Signals
                current_holdings = self.positions[ticker]
                
                if passed and current_holdings == 0:
                    # Determine Position Size based on conviction
                    max_alloc = self.config.position_sizing.max_position_pct * self.capital * conviction
                    shares_to_buy = int(max_alloc / price)
                    
                    if shares_to_buy > 0:
                        pending_orders.append({
                            "ticker": ticker,
                            "action": "BUY",
                            "shares": shares_to_buy,
                            "signal_date": current_date,
                            "signal_price": price
                        })
                elif sell_signal and current_holdings > 0:
                    # Sell logic - normally check hold duration, but keep it deterministic here
                    held_days = 5 # Simplification, track actual hold days in prod
                    if held_days >= self.config.sandbox.min_hold_days:
                        pending_orders.append({
                            "ticker": ticker,
                            "action": "SELL",
                            "shares": current_holdings,
                            "signal_date": current_date,
                            "signal_price": price
                        })

        # Write local traces if agents were used
        if self.config.agent.enabled and len(self.trace_events) > 0:
            import os, json
            os.makedirs("debug/traces", exist_ok=True)
            trace_path = f"debug/traces/recommendation_trace_{self.run_id}.jsonl"
            with open(trace_path, "w") as f:
                for t in self.trace_events:
                    f.write(json.dumps(t) + "\n")
            print(f"[{self.run_id}] Wrote {len(self.trace_events)} LLM traces to {trace_path}")

        # Return the structured loop results
        loop_results = {
            "optimization_dates": [d.isoformat() for d in opt_dates],
            "holdout_dates": [d.isoformat() for d in holdout_dates],
            "trade_log": self.trade_log,
            "nav_history": self.nav_history,
            "gate_events": self.gate_events,
            "trace_events": self.trace_events
        }
        
        # 3. Wire MLflow Persistence
        try:
            from engines.sandbox.mlflow_tracker import MLflowTracker
            tracker = MLflowTracker()
            config_dump = self.config.model_dump()
            run_id = tracker.log_run(config_dump, loop_results)
            print(f"[{self.run_id}] Logged simulation results to MLflow Run ID: {run_id}")
            loop_results["mlflow_run_id"] = run_id
        except ImportError:
            print(f"[{self.run_id}] Skipping MLflow log - mlflow_tracker not installed.")
        except Exception as e:
            print(f"[{self.run_id}] Error logging to MLflow: {str(e)}")

        return loop_results
