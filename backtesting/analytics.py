"""
Backtest Analytics — Computes performance metrics and failure classifications.
"""
import math
from typing import List, Dict, Any


class BacktestAnalytics:
    """
    Static methods for computing backtesting performance metrics
    from equity curve and trade log data.
    """

    @staticmethod
    def compute_metrics(
        equity_curve: List[Dict[str, Any]],
        trades: List[Dict[str, Any]],
        starting_capital: float,
    ) -> Dict[str, Any]:
        """
        Computes a full metrics summary from a completed backtest.
        """
        # ── Return ──────────────────────────────────────────────────────
        if equity_curve:
            final_equity = equity_curve[-1]["equity"]
            total_return = ((final_equity - starting_capital) / starting_capital) * 100
        else:
            total_return = 0.0

        # ── Trade stats ─────────────────────────────────────────────────
        sell_trades = [t for t in trades if t.get("side") == "sell" and t.get("pnl") is not None]
        total_trades = len(sell_trades)
        winning = [t for t in sell_trades if t["pnl"] > 0]
        losing = [t for t in sell_trades if t["pnl"] <= 0]

        win_rate = (len(winning) / total_trades * 100) if total_trades > 0 else 0.0
        avg_win = sum(t["pnl"] for t in winning) / len(winning) if winning else 0.0
        avg_loss = sum(t["pnl"] for t in losing) / len(losing) if losing else 0.0
        profit_factor = (
            abs(sum(t["pnl"] for t in winning) / sum(t["pnl"] for t in losing))
            if losing and sum(t["pnl"] for t in losing) != 0
            else float("inf") if winning else 0.0
        )

        # ── Sharpe Ratio ────────────────────────────────────────────────
        sharpe_ratio = BacktestAnalytics._compute_sharpe(equity_curve)

        # ── Max Drawdown ────────────────────────────────────────────────
        max_drawdown = BacktestAnalytics._compute_max_drawdown(equity_curve)

        # ── Per-ticker breakdown ────────────────────────────────────────
        ticker_breakdown = {}
        for t in sell_trades:
            tk = t.get("ticker", "UNKNOWN")
            if tk not in ticker_breakdown:
                ticker_breakdown[tk] = {"trades": 0, "pnl": 0.0, "wins": 0}
            ticker_breakdown[tk]["trades"] += 1
            ticker_breakdown[tk]["pnl"] += t["pnl"]
            if t["pnl"] > 0:
                ticker_breakdown[tk]["wins"] += 1

        # ── Failure classification ──────────────────────────────────────
        failure_summary = {}
        for t in losing:
            tag = t.get("failure_tag", "UNKNOWN")
            failure_summary[tag] = failure_summary.get(tag, 0) + 1

        return {
            "total_return": round(total_return, 2),
            "sharpe_ratio": round(sharpe_ratio, 2),
            "max_drawdown": round(max_drawdown, 2),
            "win_rate": round(win_rate, 1),
            "total_trades": total_trades,
            "avg_win": round(avg_win, 2),
            "avg_loss": round(avg_loss, 2),
            "profit_factor": round(profit_factor, 2) if profit_factor != float("inf") else "∞",
            "ticker_breakdown": ticker_breakdown,
            "failure_summary": failure_summary,
        }

    @staticmethod
    def _compute_sharpe(equity_curve: List[Dict[str, Any]], risk_free_rate: float = 0.05) -> float:
        """
        Computes annualized Sharpe ratio from daily equity values.
        """
        if len(equity_curve) < 2:
            return 0.0

        equities = [e["equity"] for e in equity_curve]
        daily_returns = [
            (equities[i] - equities[i - 1]) / equities[i - 1]
            for i in range(1, len(equities))
            if equities[i - 1] > 0
        ]

        if not daily_returns:
            return 0.0

        avg_return = sum(daily_returns) / len(daily_returns)
        std_return = math.sqrt(
            sum((r - avg_return) ** 2 for r in daily_returns) / len(daily_returns)
        )

        if std_return == 0:
            return 0.0

        daily_rf = risk_free_rate / 252
        sharpe = (avg_return - daily_rf) / std_return * math.sqrt(252)
        return sharpe

    @staticmethod
    def _compute_max_drawdown(equity_curve: List[Dict[str, Any]]) -> float:
        """
        Computes the maximum peak-to-trough drawdown as a percentage.
        """
        if not equity_curve:
            return 0.0

        peak = equity_curve[0]["equity"]
        max_dd = 0.0

        for point in equity_curve:
            eq = point["equity"]
            if eq > peak:
                peak = eq
            drawdown = ((peak - eq) / peak) * 100 if peak > 0 else 0.0
            max_dd = max(max_dd, drawdown)

        return max_dd

    @staticmethod
    def compare_runs(
        run_a: Dict[str, Any], run_b: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Side-by-side comparison of two backtest runs.
        """
        return {
            "run_a": {
                "run_id": run_a.get("run_id"),
                "total_return": run_a.get("total_return"),
                "sharpe_ratio": run_a.get("sharpe_ratio"),
                "max_drawdown": run_a.get("max_drawdown"),
                "win_rate": run_a.get("win_rate"),
                "total_trades": run_a.get("total_trades"),
                "equity_curve": run_a.get("equity_curve", []),
            },
            "run_b": {
                "run_id": run_b.get("run_id"),
                "total_return": run_b.get("total_return"),
                "sharpe_ratio": run_b.get("sharpe_ratio"),
                "max_drawdown": run_b.get("max_drawdown"),
                "win_rate": run_b.get("win_rate"),
                "total_trades": run_b.get("total_trades"),
                "equity_curve": run_b.get("equity_curve", []),
            },
        }
