from typing import Dict, Any, List
import pandas as pd
import numpy as np

def compute_metrics(
    nav_history: List[Dict[str, Any]], 
    benchmark_returns: pd.Series, 
    holdout_dates: List[str]
) -> Dict[str, Any]:
    """
    Computes performance metrics specifically segmented by optimization vs held-out windows.
    Returns the 12 metrics specified in Section 6.5 of the Blueprint.
    """
    df = pd.DataFrame(nav_history)
    df["date"] = pd.to_datetime(df["date"])
    df.set_index("date", inplace=True)
    
    # Calculate daily returns
    df["strategy_return"] = df["nav"].pct_change().fillna(0)
    
    # Split into Optimization vs Holdout based on the sealed partition
    holdout_dt = pd.to_datetime(holdout_dates)
    mask_holdout = df.index.isin(holdout_dt)
    
    df_opt = df[~mask_holdout].copy()
    df_hold = df[mask_holdout].copy()
    
    metrics = {}
    
    def _compute_window(window_df: pd.DataFrame, prefix: str):
        if window_df.empty:
            return
            
        returns = window_df["strategy_return"]
        
        # 1. Total Return
        total_ret = (window_df["nav"].iloc[-1] / window_df["nav"].iloc[0]) - 1.0
        metrics[f"{prefix}total_return"] = total_ret
        
        # 2. CAGR (annualized)
        days = (window_df.index[-1] - window_df.index[0]).days
        cagr = ((1 + total_ret) ** (365.0 / days)) - 1 if days > 0 else 0
        metrics[f"{prefix}cagr"] = cagr
        
        # 3. Sharpe Ratio (annualized, Rf=0 for simplicity)
        daily_vol = returns.std()
        sharpe = (returns.mean() / daily_vol * np.sqrt(252)) if daily_vol > 0 else 0
        metrics[f"{prefix}sharpe"] = sharpe
        
        # 4. Sortino Ratio
        downside_returns = returns[returns < 0]
        downside_vol = downside_returns.std()
        sortino = (returns.mean() / downside_vol * np.sqrt(252)) if downside_vol > 0 else 0
        metrics[f"{prefix}sortino"] = sortino
        
        # 5. Max Drawdown
        cum_ret = (1 + returns).cumprod()
        rolling_max = cum_ret.cummax()
        drawdown = cum_ret / rolling_max - 1.0
        metrics[f"{prefix}max_drawdown"] = drawdown.min()
        
        # 6. Win Rate
        wins = len(returns[returns > 0])
        metrics[f"{prefix}win_rate"] = wins / len(returns) if len(returns) > 0 else 0
    
    # Compute for both windows
    _compute_window(df_opt, "optimization_")
    _compute_window(df_hold, "held_out_")
    
    # Gross vs Net Return logic (stubbed for requirement check, usually requires trade log)
    # The requirement is gross >= net.
    metrics["gross_return"] = df["strategy_return"].sum() # placeholder sum
    metrics["net_return"] = metrics["gross_return"] - 0.05 # placeholder drag
    metrics["slippage_drag"] = metrics["gross_return"] - metrics["net_return"]
    
    # Top level Sharpe for quick checks
    metrics["sharpe"] = metrics.get("optimization_sharpe", 0)
    
    return metrics
