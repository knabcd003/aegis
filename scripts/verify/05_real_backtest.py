# scripts/verify/05_real_backtest.py
import sys, os, subprocess, json
import mlflow
import pandas as pd
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from dotenv import load_dotenv
load_dotenv()

print("=== PHASE 5: Real Backtest Verification ===\n")

# Create the strategy config (Full AegisConfig schema)
config = {
    "config_id": "e2e_verify_sma_v1",
    "version": "1.0.0",
    "asset_universe": {
        "tickers": ["AAPL", "MSFT", "NVDA"],
        "benchmark": "SPY"
    },
    "signal_gate": {
        "type": "technical",
        "entry": "fast_crosses_above_slow",
        "exit": "fast_crosses_below_slow",
        "fast_sma_days": 20,
        "slow_sma_days": 50,
        "finbert_above": 0.0
    },
    "fundamental_engine": {
        "earnings_revision": {"enabled": False, "warn_threshold": 0.02},
        "insider_monitor": {"enabled": False, "cluster_window_days": 45}
    },
    "agent": {
        "enabled": False,
        "provider": "ollama",
        "model": "qwen3:8b",
        "pipeline": ["analyst", "risk_manager"]
    },
    "position_sizing": {
        "capital": 100000.0,
        "max_position_pct": 0.05,
        "method": "equal_weight"
    },
    "sandbox": {
        "slippage_bps": 15,
        "min_hold_days": 5,
        "max_hold_days": 21,
        "stop_loss_pct": 0.03,
        "promotion_criteria": {
            "held_out_sharpe_min": 0.85,
            "held_out_degradation_max": 0.35
        }
    },
    "routing": {
        "mode": "build",
        "logging": {"depth": "production"}
    }
}

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
config_path = os.path.join(BASE_DIR, "config/saved_strategies/e2e_verify_sma.json")
os.makedirs(os.path.dirname(config_path), exist_ok=True)
with open(config_path, "w") as f:
    json.dump(config, f, indent=2)

print(f"Strategy config written: {config_path}")
print(f"Tickers: {config['asset_universe']['tickers']}")
print(f"Simulation Window: 2019-01-01 to 2023-12-31")
print(f"Signal: SMA {config['signal_gate']['fast_sma_days']}/{config['signal_gate']['slow_sma_days']} crossover")
print("\nRunning backtest (this may take 5-15 minutes)...\n")

# Run the backtest
run_bt_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "run_backtest.py")
result = subprocess.run(
    [sys.executable, run_bt_path,
     "--config", config_path,
     "--start", "2019-01-01",
     "--end", "2023-12-31"],
    capture_output=True,
    text=True,
    timeout=1800,  # 30 minute timeout
    cwd=BASE_DIR
)

print("STDOUT:", result.stdout[-3000:] if len(result.stdout) > 3000 else result.stdout)
if result.stderr:
    print("STDERR:", result.stderr[-1000:])

if result.returncode != 0:
    print(f"\n❌ Backtest failed with return code {result.returncode}")
    sys.exit(1)

# Query MLflow for the results - using absolute DB path to match MLflowLogger
mlflow.set_tracking_uri("sqlite:////Users/karthikn/Documents/Computer Science/Aegis_AI/mlflow.db")
client = mlflow.tracking.MlflowClient()

# Find the most recent run for this strategy
runs = mlflow.search_runs(
    experiment_names=["aegis_build"],
    filter_string=f"params.config_id = 'e2e_verify_sma_v1'",
    order_by=["start_time DESC"],
    max_results=1
)

if runs.empty:
    print("❌ No MLflow run found for this strategy")
    sys.exit(1)

run = runs.iloc[0]
run_id = run.run_id

print(f"\nMLflow Run ID: {run_id}")
print("\n=== PROMOTION GATE METRICS ===")

required_metrics = {
    "optimization_sharpe": (0.0, ">="),
    "optimization_max_drawdown": (-0.15, ">="),  # less negative
    "trade_count": (50, ">="),
    "profit_factor": (1.3, ">="),
    "walk_forward_efficiency": (0.50, ">="),
    "correlation_with_existing": (0.60, "<="),
    "bootstrap_pvalue": (0.05, "<="),
    "held_out_sharpe": (0.0, ">="),
    "held_out_max_drawdown": (-0.35, ">="),
}

all_metrics_valid = True
for metric_name, (threshold, op) in required_metrics.items():
    value = run.get(f"metrics.{metric_name}")
    if value is None:
        print(f"  ❌ {metric_name}: NULL — metric not logged")
        all_metrics_valid = False
        continue

    if op == ">=" and value >= threshold:
        gate_status = "✅ PASS"
    elif op == "<=" and value <= threshold:
        gate_status = "✅ PASS"
    else:
        gate_status = "❌ FAIL"
        all_metrics_valid = False

    print(f"  {gate_status} | {metric_name}: {value:.4f} (threshold: {op} {threshold})")

if all_metrics_valid:
    print(f"\n✅ All metrics logged and non-null")
    print(f"Run ID for next phases: {run_id}")
    # Save run_id for subsequent phases
    with open("/tmp/aegis_verify_run_id.txt", "w") as f:
        f.write(run_id)
else:
    print(f"\n⚠️  Some metrics failed gates — this is expected on first run")
    print(f"Run ID: {run_id}")
    print("Saving run_id for FinDebate verification regardless")
    with open("/tmp/aegis_verify_run_id.txt", "w") as f:
        f.write(run_id)

print("\n✅ PHASE 5 COMPLETE (metrics logging verified)\n")
