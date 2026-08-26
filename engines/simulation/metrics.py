"""
Metrics Calculator (Phase 5 — Complete)

Computes all performance metrics required by the Promotion Gate:
  1. Total return (optimization + held-out)
  2. CAGR
  3. Sharpe ratio (optimization + held-out)
  4. Sortino ratio
  5. Max drawdown (optimization + held-out)
  6. Win rate
  7. Trade count
  8. Profit factor
  9. P-value (bootstrap permutation test)
 10. Walk-forward efficiency (computed via WalkForwardValidator, stubbed here)

Correlation with existing promoted strategies is handled at the Promotion Gate level,
not here, because it requires access to the MLflow registry.
"""

from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np


def match_round_trip_trades(trade_log: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Matches BUY → SELL entries in the trade log into round-trip trades
    with individual P&L. Uses FIFO matching per ticker.

    Returns a list of completed round-trip trades, each with:
      - ticker, entry_price, exit_price, shares, pnl, pnl_pct, hold_days
    """
    # Separate buys and sells, sorted by fill_date
    buys_by_ticker: Dict[str, List[Dict]] = {}
    sells_by_ticker: Dict[str, List[Dict]] = {}

    for trade in trade_log:
        if trade.get("fill_date") is None:
            continue  # unfilled order
        ticker = trade["ticker"]
        if trade["action"] == "BUY":
            buys_by_ticker.setdefault(ticker, []).append(trade)
        elif trade["action"] == "SELL":
            sells_by_ticker.setdefault(ticker, []).append(trade)

    round_trips = []

    for ticker, sells in sells_by_ticker.items():
        buys = buys_by_ticker.get(ticker, [])
        # Sort both by fill_date for FIFO matching
        buys.sort(key=lambda t: str(t["fill_date"]))
        sells.sort(key=lambda t: str(t["fill_date"]))

        buy_idx = 0
        for sell in sells:
            if buy_idx >= len(buys):
                break

            buy = buys[buy_idx]
            buy_idx += 1

            shares = min(buy["shares"], sell["shares"])
            entry_price = buy["fill_price"]
            exit_price = sell["fill_price"]
            pnl = (exit_price - entry_price) * shares
            pnl_pct = (exit_price - entry_price) / entry_price if entry_price > 0 else 0.0

            # Compute hold days
            buy_date = buy["fill_date"]
            sell_date = sell["fill_date"]
            if hasattr(buy_date, "toordinal"):
                hold_days = (sell_date - buy_date).days
            else:
                # If dates are strings, parse them
                from datetime import date as dt_date
                if isinstance(buy_date, str):
                    buy_date = pd.to_datetime(buy_date).date()
                    sell_date = pd.to_datetime(sell_date).date()
                hold_days = (sell_date - buy_date).days

            round_trips.append({
                "ticker": ticker,
                "entry_price": entry_price,
                "exit_price": exit_price,
                "shares": shares,
                "pnl": pnl,
                "pnl_pct": pnl_pct,
                "hold_days": hold_days,
                "entry_date": buy["fill_date"],
                "exit_date": sell["fill_date"],
            })

    return round_trips


def compute_trade_count(round_trips: List[Dict[str, Any]]) -> int:
    """Count completed round-trip trades."""
    return len(round_trips)


def compute_profit_factor(round_trips: List[Dict[str, Any]]) -> float:
    """
    Profit factor = sum of winning trade P&L / abs(sum of losing trade P&L).
    Returns inf if no losing trades, 0.0 if no winning trades, 0.0 if no trades.
    """
    if not round_trips:
        return 0.0

    gross_profit = sum(t["pnl"] for t in round_trips if t["pnl"] > 0)
    gross_loss = abs(sum(t["pnl"] for t in round_trips if t["pnl"] < 0))

    if gross_loss == 0:
        return float("inf") if gross_profit > 0 else 0.0

    return gross_profit / gross_loss


def compute_bootstrap_pvalue(
    round_trips: List[Dict[str, Any]],
    n_permutations: int = 5000,
    seed: Optional[int] = None,
) -> float:
    """
    Bootstrap sign-randomization test for strategy Sharpe ratio.

    Null hypothesis: each trade's return is equally likely to be positive or negative.

    Procedure:
      1. Compute real Sharpe from round-trip trade returns.
      2. Randomly flip the sign of each trade return N times, compute Sharpe on each.
      3. P-value = fraction of sign-randomized Sharpes >= real Sharpe.

    This tests whether the strategy's positive performance is distinguishable from
    random chance, not just whether trade ordering matters.

    Returns p-value in [0, 1]. Lower = more statistically significant.
    """
    if len(round_trips) < 5:
        return 1.0  # Not enough trades for meaningful test

    returns = np.array([t["pnl_pct"] for t in round_trips])

    # Real Sharpe (annualized assuming ~252 trading days per year)
    real_mean = returns.mean()
    real_std = returns.std()
    if real_std == 0:
        return 1.0
    real_sharpe = real_mean / real_std * np.sqrt(252)

    # Sign-randomization test
    rng = np.random.RandomState(seed)
    exceed_count = 0
    for _ in range(n_permutations):
        # Randomly flip sign of each return (simulate null: 50/50 win/loss)
        signs = rng.choice([-1, 1], size=len(returns))
        randomized = returns * signs
        rand_mean = randomized.mean()
        rand_std = randomized.std()
        if rand_std == 0:
            continue
        rand_sharpe = rand_mean / rand_std * np.sqrt(252)
        if rand_sharpe >= real_sharpe:
            exceed_count += 1

    return exceed_count / n_permutations


def compute_win_rate(round_trips: List[Dict[str, Any]]) -> float:
    """Win rate = fraction of profitable round-trip trades."""
    if not round_trips:
        return 0.0
    wins = sum(1 for t in round_trips if t["pnl"] > 0)
    return wins / len(round_trips)


def compute_max_drawdown(nav_series: pd.Series) -> float:
    """Maximum drawdown from a NAV series. Returns a negative number (e.g., -0.15)."""
    if nav_series.empty:
        return 0.0
    cummax = nav_series.cummax()
    drawdown = (nav_series - cummax) / cummax
    return float(drawdown.min())


def compute_sharpe(returns: pd.Series) -> float:
    """Annualized Sharpe ratio (Rf=0). Returns 0.0 if returns are empty, std is zero, or std is NaN."""
    if returns.empty:
        return 0.0
    std = returns.std()
    if pd.isna(std) or std == 0:
        return 0.0
    return float(returns.mean() / std * np.sqrt(252))


def compute_walk_forward_efficiency(
    fold_oos_sharpes: List[float],
    full_is_sharpe: float,
) -> float:
    """
    Walk-Forward Efficiency = mean(OOS Sharpe across k folds) / full IS Sharpe.

    Returns 0.0 if IS Sharpe <= 0 (no positive in-sample performance) or if
    no fold results are provided. Negative WFE values are allowed — they
    indicate the strategy actively loses money out-of-sample.
    """
    if full_is_sharpe <= 0 or not fold_oos_sharpes:
        return 0.0
    return float(np.mean(fold_oos_sharpes) / full_is_sharpe)

def compute_sortino(returns: pd.Series) -> float:
    """Annualized Sortino ratio."""
    if returns.empty:
        return 0.0
    downside = returns[returns < 0]
    if downside.empty:
        return 0.0
    std = downside.std()
    if pd.isna(std) or std == 0:
        return 0.0
    return float(returns.mean() / std * np.sqrt(252))


import logging

logger = logging.getLogger(__name__)

def compute_metrics(
    nav_history: List[Dict[str, Any]],
    trade_log: List[Dict[str, Any]],
    holdout_dates: List[str],
    benchmark_returns: Optional[pd.Series] = None,
) -> Dict[str, Any]:
    """
    Computes all Promotion Gate metrics from simulation results.
    """
    logger.info(f"compute_metrics called with {len(trade_log)} trades, {len(nav_history)} NAV points")
    
    # Build NAV DataFrame
    df = pd.DataFrame(nav_history)
    if df.empty:
        return {"error": "empty_nav_history"}

    df["date"] = pd.to_datetime(df["date"])
    df.set_index("date", inplace=True)
    df["returns"] = df["nav"].pct_change().fillna(0)

    # Split into optimization vs holdout
    holdout_dt = set(pd.to_datetime(holdout_dates).date)
    mask_holdout = df.index.map(lambda x: x.date() in holdout_dt)

    df_opt = df[~mask_holdout].copy()
    df_hold = df[mask_holdout].copy()

    metrics: Dict[str, Any] = {}

    # --- Per-partition metrics ---
    def _compute_partition(partition_df: pd.DataFrame, prefix: str):
        if partition_df.empty:
            return

        returns = partition_df["returns"]
        nav = partition_df["nav"]

        # Total return
        total_ret = (nav.iloc[-1] / nav.iloc[0]) - 1.0 if nav.iloc[0] > 0 else 0.0
        metrics[f"{prefix}total_return"] = float(total_ret)

        # CAGR
        days = (partition_df.index[-1] - partition_df.index[0]).days
        cagr = ((1 + total_ret) ** (365.0 / days)) - 1 if days > 0 else 0.0
        metrics[f"{prefix}cagr"] = float(cagr)

        # Sharpe
        metrics[f"{prefix}sharpe"] = compute_sharpe(returns)

        # Sortino
        metrics[f"{prefix}sortino"] = compute_sortino(returns)

        # Max drawdown
        metrics[f"{prefix}max_drawdown"] = compute_max_drawdown(nav)

    _compute_partition(df_opt, "optimization_")
    _compute_partition(df_hold, "held_out_")

    # --- Trade-level metrics (partitioned by exit date) ---
    round_trips = match_round_trip_trades(trade_log)

    opt_round_trips = []
    hold_round_trips = []
    for rt in round_trips:
        exit_d = rt["exit_date"]
        if hasattr(exit_d, "date") and callable(getattr(exit_d, "date")):
            exit_d = exit_d.date()
        elif isinstance(exit_d, str):
            exit_d = pd.to_datetime(exit_d).date()
        
        if exit_d in holdout_dt:
            hold_round_trips.append(rt)
        else:
            opt_round_trips.append(rt)

    metrics["optimization_trade_count"] = compute_trade_count(opt_round_trips)
    metrics["optimization_profit_factor"] = compute_profit_factor(opt_round_trips)
    metrics["optimization_win_rate"] = compute_win_rate(opt_round_trips)
    metrics["optimization_bootstrap_pvalue"] = compute_bootstrap_pvalue(opt_round_trips, seed=42)

    metrics["held_out_trade_count"] = compute_trade_count(hold_round_trips)
    metrics["held_out_profit_factor"] = compute_profit_factor(hold_round_trips)
    metrics["held_out_win_rate"] = compute_win_rate(hold_round_trips)
    metrics["held_out_bootstrap_pvalue"] = compute_bootstrap_pvalue(hold_round_trips, seed=42)

    # Full session aggregates
    metrics["trade_count"] = compute_trade_count(round_trips)
    metrics["profit_factor"] = compute_profit_factor(round_trips)
    metrics["win_rate"] = compute_win_rate(round_trips)
    metrics["bootstrap_pvalue"] = compute_bootstrap_pvalue(round_trips, seed=42)

    # Walk-forward efficiency — computed externally by WalkForwardValidator
    # (requires k-fold simulation runs). Stub at 0.0 here; the caller
    # (run_backtest.py) overwrites this with the real value from
    # WalkForwardValidator.run().
    metrics["walk_forward_efficiency"] = 0.0

    # Correlation with existing — returns 0.0 until promoted strategy registry populated.
    # The Promotion Gate handles the actual correlation check against MLflow.
    metrics["correlation_with_existing"] = 0.0

    # Held-out degradation: ratio of held-out Sharpe to optimization Sharpe
    opt_sharpe = metrics.get("optimization_sharpe", 0.0)
    hold_sharpe = metrics.get("held_out_sharpe", 0.0)
    if opt_sharpe > 0:
        metrics["held_out_degradation"] = 1.0 - (hold_sharpe / opt_sharpe)
    else:
        metrics["held_out_degradation"] = 1.0  # No optimization performance = max degradation

    # Convenience aliases for Promotion Gate field names
    metrics["sharpe"] = metrics.get("optimization_sharpe", 0.0)
    metrics["max_drawdown"] = metrics.get("optimization_max_drawdown", 0.0)

    # Cap infinite profit factor for MLflow (can't log inf)
    if metrics["profit_factor"] == float("inf"):
        metrics["profit_factor"] = 999.0

    return metrics
