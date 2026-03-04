"""
Backtest Runner — Day-by-day replay orchestrator.
Feeds historical snapshots through the agent pipeline using a simulated broker.
Stores all results to DuckDB for analytical queries.
"""
import os
import sys
import duckdb
import json
from datetime import datetime
from typing import List, Dict, Any, Optional

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backtesting.data_store import HistoricalDataStore
from backtesting.sim_broker import SimulatedBroker
from backtesting.llm_cache import LLMCache
from tools.calculators import TradingCalculators
from config.manager import ConfigManager

RESULTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "backtest_results")
DB_PATH = os.path.join(RESULTS_DIR, "backtests.duckdb")


class BacktestRunner:
    """
    Orchestrates a full backtest run:
    1. Iterates day-by-day through the historical window
    2. On each evaluation day, runs the Quant logic on the available data
    3. Optionally invokes LLM (with caching) to generate a thesis
    4. Records trades and marks portfolio to market
    5. Stores all results to DuckDB
    """

    def __init__(self):
        os.makedirs(RESULTS_DIR, exist_ok=True)
        self.data_store = HistoricalDataStore()
        self.llm_cache = LLMCache()
        self.db = duckdb.connect(DB_PATH)
        self._init_schema()

    def _init_schema(self):
        """Creates DuckDB tables for backtest runs and trades."""
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS backtest_runs (
                run_id INTEGER PRIMARY KEY,
                config TEXT,
                tickers TEXT,
                start_date TEXT,
                end_date TEXT,
                started_at TEXT,
                completed_at TEXT,
                total_return DOUBLE,
                sharpe_ratio DOUBLE,
                max_drawdown DOUBLE,
                win_rate DOUBLE,
                total_trades INTEGER,
                equity_curve TEXT,
                status TEXT DEFAULT 'running'
            )
        """)
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS backtest_trades (
                id INTEGER PRIMARY KEY,
                run_id INTEGER,
                ticker TEXT,
                side TEXT,
                qty DOUBLE,
                fill_price DOUBLE,
                date TEXT,
                thesis TEXT,
                pnl DOUBLE,
                exit_reason TEXT,
                failure_tag TEXT
            )
        """)
        # Auto-increment via sequences
        self.db.execute("CREATE SEQUENCE IF NOT EXISTS run_id_seq START 1")
        self.db.execute("CREATE SEQUENCE IF NOT EXISTS trade_id_seq START 1")

    def run_backtest(self, config: Dict[str, Any]) -> int:
        """
        Main entry point. Config expects:
        {
            tickers: ["AAPL", "NVDA"],
            start_date: "2024-06-01",
            end_date: "2024-12-31",
            strategy: { philosophy, max_pe_ratio, ... },
            use_llm: bool,
            eval_frequency_days: int (default 5 = weekly)
        }
        Returns the run_id.
        """
        tickers = config["tickers"]
        start_date = config["start_date"]
        end_date = config["end_date"]
        strategy = config.get("strategy", ConfigManager.load_config())
        use_llm = config.get("use_llm", False)
        eval_freq = config.get("eval_frequency_days", 5)

        deployment = strategy.get("deployment_amount", 50000)
        broker = SimulatedBroker(starting_cash=deployment)

        # Allocate a run ID
        run_id = self.db.execute("SELECT nextval('run_id_seq')").fetchone()[0]

        self.db.execute("""
            INSERT INTO backtest_runs (run_id, config, tickers, start_date, end_date, started_at, status)
            VALUES (?, ?, ?, ?, ?, ?, 'running')
        """, [run_id, json.dumps(strategy), json.dumps(tickers), start_date, end_date, datetime.now().isoformat()])

        print(f"\n[Backtest #{run_id}] Starting: {tickers} from {start_date} to {end_date}")
        print(f"[Backtest #{run_id}] Capital: ${deployment:,.2f} | LLM: {'ON' if use_llm else 'OFF (quant-only)'}")

        # Get all trading dates from the first ticker's data
        all_dates = self._get_trading_dates(tickers[0], start_date, end_date)
        if not all_dates:
            print(f"[Backtest #{run_id}] No trading dates found. Aborting.")
            return run_id

        # ── Main simulation loop ────────────────────────────────────────
        day_count = 0
        for date_str in all_dates:
            day_count += 1

            # Mark existing positions to market
            current_prices = {}
            for t in tickers:
                prices = self.data_store.get_prices(t, date_str, lookback_days=1)
                if prices:
                    current_prices[t] = prices[-1]["close"]
            broker.mark_to_market(current_prices, date_str)

            # Only evaluate on the configured frequency
            if day_count % eval_freq != 0:
                continue

            # ── Evaluate each ticker ────────────────────────────────────
            for ticker in tickers:
                prices = self.data_store.get_prices(ticker, date_str, lookback_days=30)
                if len(prices) < 10:
                    continue  # Not enough data yet

                fundamentals = self.data_store.get_fundamentals(ticker, date_str)
                close_prices = [p["close"] for p in prices]
                latest_price = close_prices[-1]

                # ── Quant Analysis ──────────────────────────────────────
                sma_20 = TradingCalculators.calculate_sma(close_prices, periods=20)
                technical_signal = "NEUTRAL"
                if sma_20 and latest_price > sma_20:
                    technical_signal = "BULLISH"
                elif sma_20 and latest_price < sma_20:
                    technical_signal = "BEARISH"

                if technical_signal == "BEARISH":
                    continue  # Skip bearish setups

                # P/E filter
                pe = fundamentals.get("pe_ratio")
                max_pe = strategy.get("max_pe_ratio", 100)
                if pe and pe > max_pe:
                    continue  # Exceeds P/E cap

                # Kelly position sizing
                win_rate_proxy = 0.55 if technical_signal == "BULLISH" else 0.45
                kelly_pct = TradingCalculators.calculate_kelly_criterion(
                    win_rate=win_rate_proxy, win_loss_ratio=1.5, fraction=0.5
                )
                max_pct = strategy.get("max_position_size_pct", 0.10)
                final_pct = min(kelly_pct, max_pct)
                allocation_usd = TradingCalculators.calculate_position_size_usd(
                    broker.get_account_balance(), final_pct
                )

                shares = int(allocation_usd // latest_price) if latest_price > 0 else 0
                if shares <= 0:
                    continue

                # Skip if we already hold this ticker
                if ticker in broker.positions:
                    continue

                # ── Execute simulated entry ─────────────────────────────
                thesis_text = ""
                if use_llm:
                    thesis_text = self._generate_thesis_cached(
                        ticker, fundamentals, {"sma_20": sma_20, "signal": technical_signal}, strategy
                    )
                    if thesis_text.upper().startswith("REJECTED"):
                        continue

                order = broker.execute_trade(ticker, qty=shares, side="buy", fill_price=latest_price)
                if order:
                    trade_id = self.db.execute("SELECT nextval('trade_id_seq')").fetchone()[0]
                    self.db.execute("""
                        INSERT INTO backtest_trades (id, run_id, ticker, side, qty, fill_price, date, thesis)
                        VALUES (?, ?, ?, 'buy', ?, ?, ?, ?)
                    """, [trade_id, run_id, ticker, shares, latest_price, date_str, thesis_text])
                    print(f"  [{date_str}] BUY {shares} {ticker} @ ${latest_price:.2f}")

            # ── Check exits for open positions ──────────────────────────
            for sym in list(broker.positions.keys()):
                pos = broker.positions[sym]
                entry = pos["avg_entry_price"]
                current = pos.get("current_price", entry)

                # ATR-based stop/take-profit
                atr_proxy = entry * 0.05
                stop = TradingCalculators.calculate_stop_loss_price(entry, atr_proxy, 2.0)
                tp = TradingCalculators.calculate_take_profit_price(entry, atr_proxy, 3.0)

                exit_reason = None
                if current <= stop:
                    exit_reason = "STOP_LOSS"
                elif current >= tp:
                    exit_reason = "TAKE_PROFIT"

                if exit_reason:
                    pnl = (current - entry) * pos["qty"]
                    failure_tag = self._classify_failure(exit_reason, pnl)
                    order = broker.execute_trade(sym, qty=pos["qty"], side="sell", fill_price=current)
                    if order:
                        trade_id = self.db.execute("SELECT nextval('trade_id_seq')").fetchone()[0]
                        self.db.execute("""
                            INSERT INTO backtest_trades (id, run_id, ticker, side, qty, fill_price, date, pnl, exit_reason, failure_tag)
                            VALUES (?, ?, ?, 'sell', ?, ?, ?, ?, ?, ?)
                        """, [trade_id, run_id, sym, pos["qty"] if "qty" in dir(pos) else order["qty"],
                              current, date_str, pnl, exit_reason, failure_tag])
                        print(f"  [{date_str}] SELL {sym} @ ${current:.2f} ({exit_reason}) P&L: ${pnl:+.2f}")

        # ── Finalize ────────────────────────────────────────────────────
        # Close any remaining open positions at last known price
        for sym in list(broker.positions.keys()):
            pos = broker.positions[sym]
            current = pos.get("current_price", pos["avg_entry_price"])
            pnl = (current - pos["avg_entry_price"]) * pos["qty"]
            broker.execute_trade(sym, qty=pos["qty"], side="sell", fill_price=current)
            trade_id = self.db.execute("SELECT nextval('trade_id_seq')").fetchone()[0]
            self.db.execute("""
                INSERT INTO backtest_trades (id, run_id, ticker, side, qty, fill_price, date, pnl, exit_reason)
                VALUES (?, ?, ?, 'sell', ?, ?, ?, ?, 'END_OF_BACKTEST')
            """, [trade_id, run_id, sym, pos["qty"], current, all_dates[-1] if all_dates else "", pnl])

        # Compute and store final metrics
        from backtesting.analytics import BacktestAnalytics
        equity_curve = broker.get_equity_curve()
        trades = self._get_run_trades(run_id)
        metrics = BacktestAnalytics.compute_metrics(equity_curve, trades, deployment)

        self.db.execute("""
            UPDATE backtest_runs SET
                completed_at = ?,
                total_return = ?,
                sharpe_ratio = ?,
                max_drawdown = ?,
                win_rate = ?,
                total_trades = ?,
                equity_curve = ?,
                status = 'completed'
            WHERE run_id = ?
        """, [
            datetime.now().isoformat(),
            metrics["total_return"],
            metrics["sharpe_ratio"],
            metrics["max_drawdown"],
            metrics["win_rate"],
            metrics["total_trades"],
            json.dumps(equity_curve),
            run_id,
        ])

        print(f"\n[Backtest #{run_id}] Complete!")
        print(f"  Return: {metrics['total_return']:+.2f}% | Sharpe: {metrics['sharpe_ratio']:.2f} | Max DD: {metrics['max_drawdown']:.2f}%")
        print(f"  Win Rate: {metrics['win_rate']:.1f}% | Trades: {metrics['total_trades']}")

        return run_id

    # ── Helpers ──────────────────────────────────────────────────────────

    def _get_trading_dates(self, ticker: str, start: str, end: str) -> List[str]:
        prices = self.data_store.get_prices(ticker, end, lookback_days=365)
        return [
            p["date"] for p in prices
            if p["date"] >= start and p["date"] <= end
        ]

    def _generate_thesis_cached(self, ticker, metrics, technicals, strategy) -> str:
        prompt = (
            f"Ticker: {ticker} | Philosophy: {strategy.get('philosophy')} | "
            f"Max P/E: {strategy.get('max_pe_ratio')} | Metrics: {metrics} | Technicals: {technicals}"
        )
        cached = self.llm_cache.get(prompt)
        if cached:
            return cached

        try:
            from langchain_ollama import ChatOllama
            llm = ChatOllama(model="phi4:14b", temperature=0.2)
            from langchain_core.prompts import PromptTemplate

            template = PromptTemplate.from_template(
                "You are a {philosophy} trading analyst. Max P/E: {max_pe}. "
                "Given {ticker}: metrics={metrics}, technicals={technicals}. "
                "Write a 2-sentence thesis. If it violates your constraints, say REJECTED first."
            )
            full_prompt = template.format(
                philosophy=strategy.get("philosophy", "value"),
                max_pe=strategy.get("max_pe_ratio", 100),
                ticker=ticker, metrics=str(metrics), technicals=str(technicals)
            )
            response = llm.invoke(full_prompt)
            result = response.content
            self.llm_cache.put(prompt, result)
            return result
        except Exception as e:
            print(f"  [LLM] Error: {e} — proceeding without thesis")
            return ""

    def _classify_failure(self, exit_reason: str, pnl: float) -> str:
        if pnl >= 0:
            return "WIN"
        if exit_reason == "STOP_LOSS":
            return "MOMENTUM_REVERSAL"
        return "THESIS_OVERFIT"

    def _get_run_trades(self, run_id: int) -> List[Dict[str, Any]]:
        result = self.db.execute(
            "SELECT * FROM backtest_trades WHERE run_id = ? ORDER BY date", [run_id]
        ).fetchall()
        columns = [desc[0] for desc in self.db.description]
        return [dict(zip(columns, row)) for row in result]

    def get_run_results(self, run_id: int) -> Optional[Dict[str, Any]]:
        result = self.db.execute(
            "SELECT * FROM backtest_runs WHERE run_id = ?", [run_id]
        ).fetchone()
        if not result:
            return None
        columns = [desc[0] for desc in self.db.description]
        data = dict(zip(columns, result))
        data["trades"] = self._get_run_trades(run_id)
        if data.get("equity_curve"):
            data["equity_curve"] = json.loads(data["equity_curve"])
        if data.get("config"):
            data["config"] = json.loads(data["config"])
        if data.get("tickers"):
            data["tickers"] = json.loads(data["tickers"])
        return data

    def list_runs(self) -> List[Dict[str, Any]]:
        result = self.db.execute(
            "SELECT run_id, tickers, start_date, end_date, total_return, sharpe_ratio, "
            "max_drawdown, win_rate, total_trades, status, completed_at "
            "FROM backtest_runs ORDER BY run_id DESC"
        ).fetchall()
        columns = [desc[0] for desc in self.db.description]
        runs = []
        for row in result:
            run = dict(zip(columns, row))
            if run.get("tickers"):
                run["tickers"] = json.loads(run["tickers"])
            runs.append(run)
        return runs
