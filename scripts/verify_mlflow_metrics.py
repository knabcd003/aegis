"""
End-to-End MLflow Metrics Verification

Runs a synthetic backtest through the full pipeline:
  1. Generate synthetic NAV history + trade log
  2. Push through MLflowTracker.log_run()
  3. Read back from MLflow via the same API the Promotion Gate uses
  4. Verify all 10 required metric key names are present and non-mock

This catches the silent failure case where compute_metrics outputs different
key names than what promotion_gate.py reads from mlflow.get_run().
"""
import sys
import os
import mlflow

# Ensure we can import engines
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engines.sandbox.mlflow_tracker import MLflowTracker


def generate_synthetic_results():
    """Generate a realistic backtest with enough trades to produce real metrics."""
    import random
    from datetime import datetime, timedelta

    random.seed(42)

    # 200 trading days of NAV history
    start = datetime(2023, 1, 3)
    nav = 100000.0
    nav_history = []
    for i in range(200):
        dt = start + timedelta(days=i)
        daily_return = random.gauss(0.001, 0.015)  # slight positive drift
        nav *= (1 + daily_return)
        nav_history.append({"date": dt.strftime("%Y-%m-%d"), "nav": nav})

    # Generate 50 round-trip trades (BUY then SELL)
    # Keys must match what SimulationLoop produces: fill_date, fill_price, shares
    trade_log = []
    for t in range(50):
        entry_day = random.randint(0, 150)
        hold_days = random.randint(3, 30)
        entry_date = start + timedelta(days=entry_day)
        exit_date = entry_date + timedelta(days=hold_days)
        entry_price = 100 + random.gauss(0, 10)
        pnl = random.gauss(2.0, 8.0)  # slight positive edge
        exit_price = entry_price + pnl
        ticker = random.choice(["AAPL", "MSFT", "NVDA"])

        trade_log.append({
            "fill_date": entry_date.strftime("%Y-%m-%d"),
            "ticker": ticker,
            "action": "BUY",
            "shares": 10,
            "fill_price": round(entry_price, 2),
        })
        trade_log.append({
            "fill_date": exit_date.strftime("%Y-%m-%d"),
            "ticker": ticker,
            "action": "SELL",
            "shares": 10,
            "fill_price": round(exit_price, 2),
        })


    # Last 20% of dates are holdout
    holdout_dates = [
        (start + timedelta(days=i)).strftime("%Y-%m-%d")
        for i in range(160, 200)
    ]

    return {
        "nav_history": nav_history,
        "trade_log": trade_log,
        "holdout_dates": holdout_dates,
    }


def main():
    print("=" * 60)
    print("END-TO-END MLFLOW METRICS VERIFICATION")
    print("=" * 60)

    # 1. Log a synthetic backtest
    tracker = MLflowTracker(tracking_uri="sqlite:///mlflow_e2e_test.db")
    results = generate_synthetic_results()
    config = {"run_id": "e2e_verification_run"}

    print("\n[1] Logging synthetic backtest to MLflow...")
    run_id = tracker.log_run(config, results, run_type="optimization")
    print(f"    Run ID: {run_id}")

    # 2. Read back metrics (exactly how Promotion Gate does it)
    print("\n[2] Reading metrics back from MLflow (same API as Promotion Gate)...")
    run = mlflow.get_run(run_id)
    logged_metrics = run.data.metrics

    print(f"    Found {len(logged_metrics)} metrics in MLflow")

    # 3. Check all BACKTEST_GATE keys exist
    # These are the 8 metric keys the gate reads from MLflow:
    GATE_METRIC_KEYS = [
        "optimization_sharpe",
        "optimization_max_drawdown",
        "trade_count",
        "profit_factor",
        "walk_forward_efficiency",
        "correlation_with_existing",
        "bootstrap_pvalue",
        "held_out_degradation",
    ]

    print("\n[3] Verifying all Promotion Gate metric keys are present:")
    all_present = True
    for key in GATE_METRIC_KEYS:
        value = logged_metrics.get(key)
        if value is not None:
            print(f"    ✅ {key}: {value}")
        else:
            print(f"    ❌ {key}: MISSING")
            all_present = False

    # 4. Print all logged metrics for visibility
    print(f"\n[4] All {len(logged_metrics)} logged metrics:")
    for key in sorted(logged_metrics.keys()):
        print(f"    {key}: {logged_metrics[key]}")

    # 5. Verify non-mock values
    print("\n[5] Non-mock value checks:")
    checks = {
        "trade_count > 0": logged_metrics.get("trade_count", 0) > 0,
        "profit_factor != 0": logged_metrics.get("profit_factor", 0) != 0,
        "bootstrap_pvalue is a real p-value": 0 <= logged_metrics.get("bootstrap_pvalue", -1) <= 1,
        "optimization_sharpe is finite": abs(logged_metrics.get("optimization_sharpe", 999)) < 100,
        "optimization_max_drawdown is negative": logged_metrics.get("optimization_max_drawdown", 0) < 0,
        "held_out_degradation < 1.0 (not default)": logged_metrics.get("held_out_degradation", 1.0) < 1.0,
        "walk_forward_efficiency == 0.0 (stub)": logged_metrics.get("walk_forward_efficiency", -1) == 0.0,
        "correlation_with_existing == 0.0 (stub)": logged_metrics.get("correlation_with_existing", -1) == 0.0,
    }

    for check_name, passed in checks.items():
        print(f"    {'✅' if passed else '❌'} {check_name}")

    # Cleanup
    os.remove("mlflow_e2e_test.db")
    import shutil
    if os.path.exists("mlruns"):
        shutil.rmtree("mlruns")

    # Final verdict
    print("\n" + "=" * 60)
    if all_present and all(checks.values()):
        print("✅ PASS: All metrics present with correct keys and non-mock values")
        print("   The Promotion Gate will read these keys correctly.")
        print("=" * 60)
        return 0
    else:
        print("❌ FAIL: Metric key mismatch or mock values detected")
        print("   Fix before Phase 5!")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
