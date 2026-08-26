import os
import sys
import json
import uuid
from datetime import date
from dotenv import load_dotenv

load_dotenv()

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import mlflow
from config.schema import AegisConfig
from engines.simulation.loop import SimulationLoop
from engines.simulation.mlflow_logger import MLflowLogger
from engines.simulation.metrics import compute_metrics
from engines.simulation.walk_forward import WalkForwardValidator
from engines.system.scenario.generator import BlockBootstrapGenerator
from engines.system.scenario.models import BootstrapRequest

from engines.debate.orchestrator import FinDebateOrchestrator
from engines.sentinel.promotion_gate import PromotionGate
from engines.monitoring.connector_health import ConnectorHealthMonitor
from engines.system.llm_router.router import ProviderRouter
from engines.system.llm_adapter import LLMAdapter
from engines.system.token_messenger.messenger import TokenMessenger
from engines.system.token_messenger.models import WorkflowStage

def main():
    print("==========================================================================")
    print("      AEGIS AI — END-TO-END VERIFICATION RUN (EVIDENCE GENERATOR)         ")
    print("==========================================================================\n")

    # 1. Load strategy config
    strategy_path = sys.argv[1] if len(sys.argv) > 1 else "config/saved_strategies/sector_rotation.json"
    thresholds_path = sys.argv[2] if len(sys.argv) > 2 else "config/gate_thresholds/sector_rotation_v1.json"
    print(f"[1/5] Loading strategy config from '{strategy_path}'...")
    print(f"      Loading gate thresholds from '{thresholds_path}'...")
    with open(strategy_path, "r") as f:
        config_raw = json.load(f)
    
    config = AegisConfig.model_validate(config_raw)
    run_id = f"run_e2e_{uuid.uuid4().hex[:8]}"
    config.run_id = run_id
    print(f"      Assigned Run ID: {run_id}")
    print(f"      Universe: {config.asset_universe.tickers}")
    print(f"      Signal Gate: Fast SMA {config.signal_gate.fast_sma_days}d / Slow SMA {config.signal_gate.slow_sma_days}d")
    print(f"      Position Sizing: Fixed {config.position_sizing.max_position_pct*100}% max_position_pct, Capital: ${config.position_sizing.capital:,.2f}")

    # 2. Set up MLflow
    mlflow_db = "sqlite:///" + os.path.abspath("mlflow.db")
    mlflow.set_tracking_uri(mlflow_db)
    print(f"      MLflow Tracking URI: {mlflow_db}")

    # 3. Execute Day-by-Day Point-in-Time Simulation Loop
    print("\n[2/5] Running daily simulation loop (2019-01-01 to 2023-12-31)...")
    start_date = date(2019, 1, 1)
    end_date = date(2023, 12, 31)

    # Contiguous 20% trailing holdout partition
    import pandas as pd
    all_dates = pd.date_range(start_date, end_date, freq='B').date.tolist()
    num_holdout = int(len(all_dates) * 0.2)
    opt_dates = sorted(all_dates[:-num_holdout])
    holdout_dates = sorted(all_dates[-num_holdout:])

    print(f"      Total trading days: {len(all_dates)}")
    print(f"      In-Sample Optimization days (80%): {len(opt_dates)} ({opt_dates[0]} to {opt_dates[-1]})")
    print(f"      Contiguous Out-of-Sample Holdout days (20%): {len(holdout_dates)} ({holdout_dates[0]} to {holdout_dates[-1]})")

    sim_loop = SimulationLoop(config)
    ml_logger = MLflowLogger(config)

    ml_logger.log_run_start(holdout_dates=[d.isoformat() for d in holdout_dates])
    sim_results = sim_loop.run(start_date, end_date, holdout_dates=holdout_dates)

    # 4. Compute Metrics & Scenario Battery
    print("\n[3/5] Computing Walk-Forward Efficiency & Scenario Battery...")
    wf_validator = WalkForwardValidator(config, n_folds=6)
    wf_result = wf_validator.run(start_date, end_date, holdout_dates=holdout_dates)

    scenario_gen = BlockBootstrapGenerator()
    nav_df = pd.DataFrame(sim_results["nav_history"])
    nav_df["date"] = pd.to_datetime(nav_df["date"]).dt.date
    mask_opt = nav_df["date"].isin(opt_dates)
    opt_returns = nav_df.loc[mask_opt, "nav"].pct_change().fillna(0).tolist()

    scenario_request = BootstrapRequest(
        strategy_returns=opt_returns,
        num_scenarios=50,
        block_size_days=20,
        scenario_length_days=252,
        mandate_max_drawdown=0.15
    )
    scenario_result = scenario_gen.execute(scenario_request)

    metrics = compute_metrics(
        sim_results["nav_history"],
        sim_results["trade_log"],
        [d.isoformat() for d in holdout_dates]
    )
    metrics["walk_forward_efficiency"] = wf_result.wfe
    metrics["scenario_pass_rate"] = scenario_result.pass_rate

    # Flag low sample size partitions (< 20 trades)
    opt_trades = metrics.get("optimization_trade_count", 0)
    hold_trades = metrics.get("held_out_trade_count", 0)
    metrics["optimization_partition_low_confidence"] = bool(opt_trades < 20)
    metrics["held_out_partition_low_confidence"] = bool(hold_trades < 20)

    ml_logger.log_run_end(
        metrics=metrics,
        trade_log=sim_results["trade_log"],
        nav_history=sim_results["nav_history"],
        gate_events=sim_results["gate_events"]
    )

    # Standing Sanity Check: Automated Outlier Daily Return Check (threshold: +/- 15%)
    nav_check_df = pd.DataFrame(sim_results["nav_history"])
    nav_check_df["daily_return"] = nav_check_df["nav"].pct_change().fillna(0)
    outliers = nav_check_df[nav_check_df["daily_return"].abs() > 0.15]
    if not outliers.empty:
        print(f"\n⚠️ SANITY CHECK WARNING: {len(outliers)} daily NAV return(s) exceeded +/-15% threshold!")
        for idx, r in outliers.iterrows():
            print(f"   Date: {r['date']} | NAV: ${r['nav']:,.2f} | Return: {r['daily_return']*100:+.2f}%")
    else:
        print("\n✅ STANDING SANITY CHECK PASSED: All daily NAV returns are strictly within +/-15% bounds.")

    print("      Quantitative Metrics Summary:")
    for k, v in metrics.items():
        if isinstance(v, float):
            print(f"        - {k}: {v:.4f}")
        else:
            print(f"        - {k}: {v}")

    # 5. Run FinDebate Adversarial Audit
    print("\n[4/5] Running FinDebate Adversarial Audit (4-Round Protocol)...")
    llm_adapter = LLMAdapter(config_path="config/llm_providers.yaml")

    def e2e_llm_invoker(provider_id: str, model_id: str, prompt: str) -> str:
        role = "debate_moderator"
        if "long-only" in prompt.lower():
            role = "debate_bull"
        elif "short-seller" in prompt.lower():
            role = "debate_bear"

        res = llm_adapter.invoke(
            messages=[{"role": "user", "content": prompt}],
            role=role,
            workflow_id=run_id,
            node_id="findebate"
        )
        return res.content

    router = ProviderRouter(config_path="config/llm_providers.yaml")
    messenger = TokenMessenger()
    orchestrator = FinDebateOrchestrator(
        router=router,
        llm_invoker=e2e_llm_invoker,
        token_messenger=messenger
    )

    manifest_metrics = dict(metrics)
    manifest_metrics["metric_notes"] = {
        "held_out_sharpe_change_pct": f"{metrics.get('held_out_sharpe_change_pct', 0.0):.4f} (Positive = OOS Sharpe outperformed IS Sharpe. Negative = OOS Sharpe degraded vs IS Sharpe)",
        "correlation_with_existing": "0.0000 (Hardcoded stub: no existing promoted strategies in MLflow registry to measure portfolio correlation against)",
        "low_confidence_rule": "Partitions with trade_count < 20 have low_confidence: true. Discount evidentiary weight for low-sample metrics."
    }

    strategy_manifest = json.dumps({
        "config_id": config.config_id,
        "run_id": run_id,
        "asset_universe": config.asset_universe.model_dump(),
        "position_sizing": config.position_sizing.model_dump(),
        "metrics": manifest_metrics
    }, indent=2)

    genesis_token = messenger.issue(
        workflow_id=run_id,
        stage=WorkflowStage.BACKTEST,
        config_hash="cfg_hash_e2e"
    )

    try:
        verdict, audit_token = orchestrator.run_debate(
            token_value=genesis_token,
            workflow_id=run_id,
            config_hash="cfg_hash_e2e",
            strategy_manifest=strategy_manifest,
            num_rounds=2
        )
        print("\n==================== RAW DEBATE VERDICT JSON ====================")
        print(json.dumps(verdict.model_dump(), indent=2))
        print("=================================================================\n")

        # 6. Evaluate Promotion Gate (Deterministic Numeric Threshold Check)
        print("[5/5] Evaluating Promotion Gate (Deterministic Numeric Threshold Check)...")
        from engines.data_ingestion.data_engine import DataEngine
        from engines.data_ingestion.connectors.yfinance_connector import YFinanceConnector
        data_engine = DataEngine(data_dir="./data")
        yf_conn = YFinanceConnector()
        data_engine.register(yf_conn, priority=1)
        health_monitor = ConnectorHealthMonitor(data_engine)
        health_monitor.run_health_checks()
        promotion_gate = PromotionGate(health_monitor=health_monitor, thresholds_path=thresholds_path)

        gate_result = promotion_gate.evaluate_backtest(
            run_id=ml_logger._mlflow_run_id,
            session_quality="nominal",
            scenario_pass_rate=scenario_result.pass_rate,
            debate_confidence=verdict.confidence_score
        )

        print("\n==================== PROMOTION GATE RESULT ====================")
        print(f"Gate Stage: {gate_result.stage.value}")
        print(f"Passed: {gate_result.passed}")
        print(f"Reason: {gate_result.reason}")
        if gate_result.failures:
            print("Failures:")
            for f in gate_result.failures:
                print(f"  ❌ {f}")
        print("=================================================================\n")

    except Exception as e:
        print(f"❌ FinDebate Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
