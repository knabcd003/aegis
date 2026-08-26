from collections import defaultdict
from datetime import date, timedelta
import hashlib
from typing import Dict, Any, List, Optional

import pandas as pd
import numpy as np

from config.schema import AegisConfig
from engines.data_ingestion.connectors.yfinance_connector import YFinanceConnector
from engines.fundamental.earnings_revision_tracker import EarningsRevisionTracker
from engines.fundamental.insider_activity_monitor import InsiderActivityMonitor
from engines.fundamental.macro_overlay import MacroOverlay
from engines.fundamental.signal_gate import SignalGate
import logging

logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(level=logging.INFO)

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
        self.entry_dates: Dict[str, date] = {} # Ticker -> Date of entry
        self.entry_prices: Dict[str, float] = {} # Ticker -> Entry Fill Price
        
        self.trade_log: List[Dict[str, Any]] = []
        self.nav_history: List[Dict[str, Any]] = []
        self.gate_events: List[Dict[str, Any]] = []
        self.trace_events: List[Dict[str, Any]] = []
        self.node_latencies_log: List[Dict[str, Any]] = [] # [{ticker, date, node, latency}]
        
        # Determine holdout dates immediately
        seed_int = int(hashlib.md5(self.run_id.encode('utf-8'), usedforsecurity=False).hexdigest(), 16) % (2**32)
        np.random.seed(seed_int)
        
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

    def compile_signals(self, ticker: str, as_of: date, price_cache: Optional[Dict[str, pd.DataFrame]] = None) -> Dict[str, Any]:
        """Compile Phase 1 signals for a given day. Optimized to use memory cache."""
        signals = {}
        
        if self.config.fundamental_engine.earnings_revision.enabled:
            signals["earnings_revision"] = self.er_tracker.compute(ticker, as_of)
            
        if self.config.fundamental_engine.insider_monitor.enabled:
            cluster_window = self.config.fundamental_engine.insider_monitor.cluster_window_days
            signals["insider_activity"] = self.im_monitor.compute(ticker, as_of, cluster_window)
            
        gate_type = getattr(self.config.signal_gate, "type", None)
        if gate_type == "technical":
            fast = getattr(self.config.signal_gate, "fast_sma_days", 20)
            slow = getattr(self.config.signal_gate, "slow_sma_days", 50)
            
            # --- OPTIMIZATION: Use pre-fetched price_cache if available ---
            df = None
            as_of_str = as_of.isoformat()
            if price_cache and ticker in price_cache:
                c_df = price_cache[ticker]
                # df["date"] is expected to be string YYYY-MM-DD
                mask = c_df["date"] <= as_of_str
                df = c_df[mask].tail(slow + 5)
            else:
                # Fallback to slow disk read if no cache provided
                df = self.yf.get_prices(ticker, days=slow+10, as_of_date=as_of)

            if df is not None and not df.empty and len(df) > slow:
                closes = df["close"].values
                signals["fast_sma"] = closes[-fast:].mean()
                signals["slow_sma"] = closes[-slow:].mean()
                signals["prev_fast_sma"] = closes[-(fast+1):-1].mean()
                signals["prev_slow_sma"] = closes[-(slow+1):-1].mean()
            else:
                signals["fast_sma"] = 0.0
                signals["slow_sma"] = 0.0
                signals["prev_fast_sma"] = 0.0
                signals["prev_slow_sma"] = 0.0
            
        return signals

    def run_fold(
        self,
        trading_dates: List[date],
        price_cache: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Run simulation over an explicit list of trading dates using pre-fetched prices.
        Used primarily by WalkForwardValidator to avoid state pollution or logging side effects.
        """
        self.cash = self.config.position_sizing.capital
        self.positions = defaultdict(float)
        self.entry_dates = {}
        self.entry_prices = {}
        fold_trade_log: List[Dict[str, Any]] = []
        fold_nav_history: List[Dict[str, Any]] = []
        pending_orders: List[Dict[str, Any]] = []

        for current_date_obj in trading_dates:
            current_date = current_date_obj.isoformat()
            daily_nav = self.cash

            # 1. Execute pending orders at OPEN
            executed_orders = []
            for order in pending_orders:
                ticker = order["ticker"]
                action = order["action"]
                shares = order["shares"]

                open_price = 0.0
                if ticker in price_cache:
                    df = price_cache[ticker]
                    mask = df["date"] == current_date
                    if mask.any():
                        open_price = float(df.loc[mask, "open"].iloc[0])
                
                if open_price <= 0:
                    continue

                slippage_ps = self._calculate_slippage(
                    order["signal_price"], open_price, shares, action
                )

                if action == "BUY":
                    fill_price = open_price + slippage_ps
                    cost = fill_price * shares
                    if cost <= self.cash:
                        self.cash -= cost
                        self.positions[ticker] += shares
                        self.entry_dates[ticker] = current_date_obj
                        self.entry_prices[ticker] = fill_price
                        order["fill_price"] = fill_price
                        order["fill_date"] = current_date_obj
                        order["slippage_drag_usd"] = slippage_ps * shares
                        fold_trade_log.append(order)
                        executed_orders.append(order)
                elif action == "SELL":
                    fill_price = open_price - slippage_ps
                    if self.positions[ticker] >= shares:
                        self.positions[ticker] -= shares
                        if self.positions[ticker] <= 0:
                            self.entry_dates.pop(ticker, None)
                            self.entry_prices.pop(ticker, None)
                        self.cash += fill_price * shares
                        order["fill_price"] = fill_price
                        order["fill_date"] = current_date_obj
                        order["slippage_drag_usd"] = slippage_ps * shares
                        fold_trade_log.append(order)
                        executed_orders.append(order)

            pending_orders = [o for o in pending_orders if o not in executed_orders]

            # 2. Mark to market
            for ticker, shares in self.positions.items():
                if shares > 0:
                    price = 0.0
                    if ticker in price_cache:
                        df = price_cache[ticker]
                        mask = df["date"] == current_date
                        if mask.any():
                            price = float(df.loc[mask, "close"].iloc[0])
                    daily_nav += shares * price

            fold_nav_history.append({"date": current_date_obj, "nav": daily_nav})

            # 3. Signal generation & order placement
            for ticker in self.config.asset_universe.tickers:
                price = 0.0
                if ticker in price_cache:
                    df = price_cache[ticker]
                    mask = df["date"] == current_date
                    if mask.any():
                        price = float(df.loc[mask, "close"].iloc[0])
                
                if price <= 0:
                    continue

                signals = self.compile_signals(ticker, current_date_obj, price_cache=price_cache)

                if not self.config.agent.enabled:
                    passed, sell_signal = SignalGate.evaluate(
                        signals,
                        self.config.signal_gate.model_dump(exclude_none=True),
                    )
                    
                    # VCL Pipeline Chaining & Metadata Propagation
                    vcl_pipeline = getattr(self.config.signal_gate, "vcl_pipeline", [])
                    vcl_metadata = {"sentiment_score": None, "gate_blocked": None} # Priority 3: Null safety
                    if passed and vcl_pipeline:
                        for component_id in vcl_pipeline:
                            res = self._execute_vcl_gate(component_id, ticker, current_date_obj, passed)
                            passed = res["passed"]
                            vcl_metadata.update({k: v for k, v in res.items() if k != "passed"})
                            
                            if not passed:
                                vcl_metadata["gate_blocked"] = component_id
                                break
                    
                    conviction = 1.0
                else:
                    # Agentic (Omitted for briefness, would normally follow similar pattern)
                    passed = False
                    sell_signal = False
                    conviction = 0.0
                    vcl_metadata = {"sentiment_score": None, "gate_blocked": None}

                current_holdings = self.positions[ticker]

                if passed and current_holdings == 0:
                    max_alloc = (
                        self.config.position_sizing.max_position_pct
                        * self.config.position_sizing.capital
                        * conviction
                    )
                    shares_to_buy = int(max_alloc / price)
                    if shares_to_buy > 0:
                        order = {
                            "ticker": ticker, "action": "BUY", "shares": shares_to_buy,
                            "signal_date": current_date_obj, "signal_price": price,
                        }
                        order.update(vcl_metadata)
                        pending_orders.append(order)
                elif current_holdings > 0:
                    entry_date = self.entry_dates.get(ticker, current_date_obj)
                    held_days = (current_date_obj - entry_date).days
                    
                    stop_loss_pct = getattr(self.config.sandbox, "stop_loss_pct", None)
                    max_hold_days = getattr(self.config.sandbox, "max_hold_days", None)
                    
                    sl_triggered = False
                    if stop_loss_pct is not None:
                        entry_pr = self.entry_prices.get(ticker, price)
                        if price <= entry_pr * (1.0 - stop_loss_pct):
                            sl_triggered = True
                            
                    mh_triggered = False
                    if max_hold_days is not None and held_days >= max_hold_days:
                        mh_triggered = True
                        
                    if sl_triggered or mh_triggered or (sell_signal and held_days >= self.config.sandbox.min_hold_days):
                        order = {
                            "ticker": ticker, "action": "SELL", "shares": current_holdings,
                            "signal_date": current_date_obj, "signal_price": price,
                        }
                        order.update(vcl_metadata)
                        pending_orders.append(order)

        return {
            "nav_history": fold_nav_history,
            "trade_log": fold_trade_log,
        }


    def run(self, start_date: date, end_date: date, holdout_dates: Optional[List[date]] = None) -> Dict[str, Any]:
        """
        Run the daily vectorized simulation loop with optimized pre-fetching.
        Now accepts explicit holdout_dates to obey orchestrator's deterministic sealing (Priority 2).
        """
        print(f"[{self.run_id}] Starting Phase 1 Simulation: {start_date} to {end_date}")
        
        # 1b. Pre-fetch prices for the entire window to avoid O(N*T) disk I/O bottleneck
        print(f"[{self.run_id}] Pre-fetching price history for {len(self.config.asset_universe.tickers)} tickers...")
        price_cache: Dict[str, pd.DataFrame] = {}
        calendar_days = (end_date - start_date).days + 100
        for ticker in self.config.asset_universe.tickers:
            df = self.yf.get_prices(ticker, days=calendar_days, as_of_date=end_date)
            if df is not None:
                price_cache[ticker] = df

        # Filter all_dates to only include actual market trading days (excluding US market holidays)
        valid_trading_dates = set()
        for ticker, df in price_cache.items():
            if "date" in df.columns and not df.empty:
                dates_in_range = pd.to_datetime(df["date"]).dt.date
                mask = (dates_in_range >= start_date) & (dates_in_range <= end_date)
                valid_trading_dates.update(dates_in_range[mask])

        if valid_trading_dates:
            all_dates = sorted(list(valid_trading_dates))
        else:
            all_dates = pd.date_range(start_date, end_date, freq='B').date.tolist()
        
        if holdout_dates is None:
            num_holdout = int(len(all_dates) * 0.2)
            holdout_dates = sorted(all_dates[-num_holdout:])

        opt_dates = sorted(all_dates[:-len(holdout_dates)])
        
        # State tracking for execution
        pending_orders = [] # [{ticker, action, shares, signal_date, signal_price}]
        
        # 2. Daily Loop
        for current_date_obj in all_dates:
            current_date = current_date_obj.isoformat()
            daily_nav = self.cash
            
            # 2a. Execute pending orders at the OPEN of this new day
            executed_orders = []
            for order in pending_orders:
                ticker = order["ticker"]
                action = order["action"]
                shares = order["shares"]
                
                # Use cache instead of disk/network
                open_price = 0.0
                if ticker in price_cache:
                    df = price_cache[ticker]
                    # df["date"] is a string YYYY-MM-DD
                    mask = df["date"] == current_date
                    if mask.any():
                        open_price = float(df.loc[mask, "open"].iloc[0])
                
                if open_price <= 0:
                    continue 
                    
                slippage_ps = self._calculate_slippage(order["signal_price"], open_price, shares, action)
                
                if action == "BUY":
                    fill_price = open_price + slippage_ps
                    cost = fill_price * shares
                    if cost <= self.cash:
                        self.cash -= cost
                        self.positions[ticker] += shares
                        self.entry_dates[ticker] = current_date_obj
                        self.entry_prices[ticker] = fill_price
                        order["fill_price"] = fill_price
                        order["fill_date"] = current_date_obj
                        order["slippage_drag_usd"] = slippage_ps * shares
                        self.trade_log.append(order)
                        executed_orders.append(order)
                elif action == "SELL":
                    fill_price = open_price - slippage_ps
                    revenue = fill_price * shares
                    if self.positions[ticker] >= shares:
                        self.positions[ticker] -= shares
                        if self.positions[ticker] <= 0:
                            self.entry_dates.pop(ticker, None)
                            self.entry_prices.pop(ticker, None)
                        self.cash += revenue
                        order["fill_price"] = fill_price
                        order["fill_date"] = current_date_obj
                        order["slippage_drag_usd"] = slippage_ps * shares
                        self.trade_log.append(order)
                        executed_orders.append(order)

            # Remove executed orders
            pending_orders = [o for o in pending_orders if o not in executed_orders]
            
            # 2b. Mark to market currently held positions
            for ticker, shares in self.positions.items():
                if shares > 0:
                    # Use cache instead of disk/network
                    price = 0.0
                    if ticker in price_cache:
                        df = price_cache[ticker]
                        mask = df["date"] == current_date
                        if mask.any():
                            price = float(df.loc[mask, "close"].iloc[0])
                    daily_nav += (shares * price)
            
            self.nav_history.append({"date": current_date_obj, "nav": daily_nav})
            
            # 2c. Signal Generation & Gate Evaluation on Universe
            for ticker in self.config.asset_universe.tickers:
                # Use cache instead of disk/network
                price = 0.0
                if ticker in price_cache:
                    df = price_cache[ticker]
                    mask = df["date"] == current_date
                    if mask.any():
                        price = float(df.loc[mask, "close"].iloc[0])
                
                if price <= 0:
                    continue
                    
                # Compile fundamental engine outputs
                signals = self.compile_signals(ticker, current_date_obj, price_cache=price_cache)
                
                # Diagnostic: Log signals for first 10 days and any day where SMA is non-zero
                if current_date_obj <= (all_dates[10] if len(all_dates) > 10 else all_dates[-1]) or signals.get("fast_sma", 0) > 0:
                     logger.debug(f"Signals for {ticker} on {current_date}: {signals}")

                # If agents disabled, fallback to legacy Signal Gate
                if not self.config.agent.enabled:
                    passed, sell_signal = SignalGate.evaluate(signals, self.config.signal_gate.model_dump(exclude_none=True))
                    
                    # FIX 3: VCL Pipeline Chaining & Metadata Propagation
                    vcl_pipeline = getattr(self.config.signal_gate, "vcl_pipeline", [])
                    vcl_metadata = {"sentiment_score": None, "gate_blocked": None} # Priority 3: Null safety
                    if passed and vcl_pipeline:
                        ticker_date = current_date_obj
                        for component_id in vcl_pipeline:
                            # Lazy load and execute VCL component
                            res = self._execute_vcl_gate(component_id, ticker, ticker_date, passed)
                            passed = res["passed"]
                            vcl_metadata.update({k: v for k, v in res.items() if k != "passed"})
                            
                            if not passed:
                                logger.info(f"Signal BLOCKED by VCL component {component_id} for {ticker} on {ticker_date}")
                                vcl_metadata["gate_blocked"] = component_id
                                break
                    
                    conviction = 1.0 # default scalar for legacy

                    
                    self.gate_events.append({
                        "date": current_date_obj, "ticker": ticker, 
                        "gate_result": passed, "margin_per_condition": signals.get("_gate_margin", {}),
                        **vcl_metadata
                    })
                    if passed:
                        logger.info(f"BUY signal fired: {ticker} on {current_date}")
                else:
                    # v6 Agentic Mesh Routing — ARCHIVED
                    # The v6 AgenticSupervisor has been moved to _v6_archive/analyst/.
                    # v7 uses the autonomous pipeline (Builder → Validator → Backtest → FinDebate → Promotion Gate)
                    # via AegisState and Token Messenger, not per-ticker agent routing.
                    raise RuntimeError(
                        "config.agent.enabled=True uses the v6 AgenticSupervisor which has been archived. "
                        "v7 uses the autonomous pipeline. Set agent.enabled=False or migrate to v7 pipeline."
                    )
                
                # Generate Buy/Sell Signals
                current_holdings = self.positions[ticker]
                
                if passed and current_holdings == 0:
                    # Determine Position Size based on live NAV / current portfolio equity
                    current_equity = daily_nav if daily_nav > 0 else self.capital
                    max_alloc = self.config.position_sizing.max_position_pct * current_equity * conviction
                    shares_to_buy = int(max_alloc / price)
                    
                    if shares_to_buy > 0:
                        pending_orders.append({
                            "ticker": ticker,
                            "action": "BUY",
                            "shares": shares_to_buy,
                            "signal_date": current_date_obj,
                            "signal_price": price
                        })
                elif current_holdings > 0:
                    entry_date = self.entry_dates.get(ticker, current_date_obj)
                    held_days = (current_date_obj - entry_date).days
                    
                    stop_loss_pct = getattr(self.config.sandbox, "stop_loss_pct", None)
                    max_hold_days = getattr(self.config.sandbox, "max_hold_days", None)
                    
                    sl_triggered = False
                    if stop_loss_pct is not None:
                        entry_pr = self.entry_prices.get(ticker, price)
                        if price <= entry_pr * (1.0 - stop_loss_pct):
                            sl_triggered = True
                            
                    mh_triggered = False
                    if max_hold_days is not None and held_days >= max_hold_days:
                        mh_triggered = True
                        
                    if sl_triggered or mh_triggered or (sell_signal and held_days >= self.config.sandbox.min_hold_days):
                        pending_orders.append({
                            "ticker": ticker,
                            "action": "SELL",
                            "shares": current_holdings,
                            "signal_date": current_date_obj,
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
            "trace_events": self.trace_events,
            "node_latencies_log": self.node_latencies_log
        }
        
        logger.info(f"Simulation complete. Total trades executed: {len(self.trade_log)}")
        logger.info(f"NAV series length: {len(self.nav_history)}")
        logger.info(f"Final NAV: {self.nav_history[-1]['nav'] if self.nav_history else 'EMPTY'}")

        return loop_results

    def _execute_vcl_gate(self, component_id: str, ticker: str, date_obj: date, upstream_signal: bool) -> Dict[str, Any]:
        """
        Executes a single VCL gate component using its execute() method with auto-discovery.
        """
        if not hasattr(self, "_vcl_registry"):
            from engines.vcl.registry import VCLRegistry, VCLRegistrationError
            import importlib
            import pkgutil
            import engines.vcl.wrappers
            from engines.vcl.component import VCLComponent

            self._vcl_registry = VCLRegistry()
            
            # Auto-discovery: Scans wrappers/ and registers all VCLComponent subclasses
            wrappers_pkg = engines.vcl.wrappers
            for _, name, is_pkg in pkgutil.iter_modules(wrappers_pkg.__path__):
                if is_pkg: continue
                
                module = importlib.import_module(f"engines.vcl.wrappers.{name}")
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (isinstance(attr, type) and 
                        issubclass(attr, VCLComponent) and 
                        attr is not VCLComponent and
                        attr.__module__ == module.__name__): # Only native definitions
                        
                        try:
                            # Guarded registration: Run all 5 gates
                            comp_instance = attr()
                            result = self._vcl_registry.register(comp_instance)
                            
                            if not result.success:
                                # Industrial Requirement: Raise startup error on broken components
                                raise VCLRegistrationError(
                                    f"VCL Component {attr.__name__} (ID: {comp_instance.component_id}) "
                                    f"failed gate {result.failed_gate}: {result.reason}. "
                                    "Industrialization requires all VCL components to be HEALTHY at startup."
                                )
                        except (TypeError, Exception) as e:
                            # If it requires arguments and isn't a simple wrapper, skip or log
                            if isinstance(e, VCLRegistrationError): raise
                            logger.info(f"Skipping auto-discovery for {attr_name}: {e}")
                            continue

            logger.info(f"VCL Registry initialized with {len(self._vcl_registry._components)} components.")

        component = self._vcl_registry._components.get(component_id)
        if not component:
            logger.error(f"VCL component {component_id} not found in registry")
            return {"passed": upstream_signal, "reason": "component_not_found"}

        try:
            input_data = component.input_schema(
                ticker=ticker,
                date=date_obj,
                upstream_signal=upstream_signal,
                # For FinBERT gate specifically; others might need more mapping
                min_sentiment_score=getattr(self.config.signal_gate, "min_sentiment_score", 0.0) 
            )
            output = component.execute(input_data)
            out_dict = output.model_dump()
            # Normalize 'signal' to 'passed' for internal loop logic
            out_dict["passed"] = out_dict.get("signal", upstream_signal)
            return out_dict
        except Exception as e:
            logger.error(f"Failed to execute VCL component {component_id}: {e}")
            return {"passed": upstream_signal, "reason": str(e)}

