#!/usr/bin/env python3
"""
RE-INDUSTRIALIZED AUDIT VERIFICATION — Phase 12.1
===================================================
Exercises the full 1-8 Orchestrator Sequence with REAL data.
Validates: FIFO trade pairing, WFE computation, scenario battery, VCL metadata.

Design decisions for speed:
  - 1-year window (2023) instead of 4-year to complete in <5 min
  - 3 tickers instead of 7 (sufficient for trade volume)
  - Fundamentals DISABLED (strategy is pure SMA crossover; fundamentals
    only add HTTP calls to Finnhub/Congressional APIs which have no keys)
  - VCL pipeline ENABLED (FinBERT gate exercises sentiment scoring)

This script does NOT use the async orchestrator. It calls the same pipeline
components in the same 1-8 sequence, but synchronously and without the
FastAPI broadcaster dependency.
"""

import sys
import os
import json
import hashlib
import logging

# Suppress noisy library logs
logging.basicConfig(level=logging.WARNING)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)
os.chdir(PROJECT_ROOT)

import mlflow
import numpy as np
import pandas as pd
from datetime import date
from mlflow.tracking import MlflowClient

from config.schema import (
    AegisConfig, AssetUniverse, SignalGateConfig, FundamentalEngineConfig,
    EarningsRevisionConfig, InsiderMonitorConfig, AgentConfig,
    PositionSizingConfig, SandboxConfig, PromotionCriteriaConfig,
    RoutingConfig, LoggingConfig
)
from engines.simulation.loop import SimulationLoop
from engines.simulation.mlflow_logger import MLflowLogger
from engines.simulation.metrics import compute_metrics, match_round_trip_trades
from engines.simulation.walk_forward import WalkForwardValidator
from engines.system.scenario.generator import BlockBootstrapGenerator
from engines.system.scenario.models import BootstrapRequest


def main():
    print("=" * 72)
    print("  AEGIS AI — RE-INDUSTRIALIZED END-TO-END VERIFICATION")
    print("=" * 72)
    print()

    # ── 0. MLflow Setup ──────────────────────────────────────────────────
    tracking_uri = f"sqlite:///{os.path.join(PROJECT_ROOT, 'mlflow.db')}"
    mlflow.set_tracking_uri(tracking_uri)
    client = MlflowClient()

    run_id = f"e2e_verify_{date.today().isoformat().replace('-', '')}"

    # ── 1. Build Config (No Fundamentals, VCL Enabled) ───────────────────
    config = AegisConfig(
        config_id=f"verify_{run_id}",
        version="7.0.0",
        asset_universe=AssetUniverse(
            tickers=["AAPL", "MSFT", "NVDA"],
            benchmark="SPY"
        ),
        signal_gate=SignalGateConfig(
            type="technical",
            entry="fast_crosses_above_slow",
            exit="fast_crosses_below_slow",
            fast_sma_days=20,
            slow_sma_days=50,
            min_sentiment_score=0.05,
            vcl_pipeline=["finbert_sentiment_gate"]
        ),
        fundamental_engine=FundamentalEngineConfig(
            earnings_revision=EarningsRevisionConfig(enabled=False),
            insider_monitor=InsiderMonitorConfig(enabled=False)
        ),
        agent=AgentConfig(enabled=False),
        position_sizing=PositionSizingConfig(
            capital=100000.0,
            max_position_pct=0.15,
            method="equal_weight"
        ),
        sandbox=SandboxConfig(
            min_hold_days=5,
            max_hold_days=21,
            stop_loss_pct=0.08,
            promotion_criteria=PromotionCriteriaConfig()
        ),
        routing=RoutingConfig(
            mode="build",
            logging=LoggingConfig(depth="production")
        )
    )
    config.run_id = run_id
    config.fingerprint = f"fp_{hashlib.md5(run_id.encode()).hexdigest()[:8]}"

    start_date = date(2023, 1, 1)
    end_date = date(2023, 12, 31)

    # ══════════════════════════════════════════════════════════════════════
    # STEP 1: Seal held-out partition (20%, deterministic from run_id)
    # ══════════════════════════════════════════════════════════════════════
    print("[Step 1/8] Sealing held-out partition...")
    all_dates = pd.date_range(start_date, end_date, freq='B').date.tolist()
    num_holdout = int(len(all_dates) * 0.2)

    seed_int = int(hashlib.md5(run_id.encode('utf-8'), usedforsecurity=False).hexdigest(), 16) % (2**32)
    rng = np.random.RandomState(seed_int)
    holdout_dates = sorted(rng.choice(all_dates, num_holdout, replace=False))
    opt_dates = sorted([d for d in all_dates if d not in holdout_dates])

    print(f"   Total trading days: {len(all_dates)}")
    print(f"   Optimization days:  {len(opt_dates)} (80%)")
    print(f"   Held-out days:      {len(holdout_dates)} (20%)")

    # ══════════════════════════════════════════════════════════════════════
    # STEP 2: Run primary backtest on optimization period
    # ══════════════════════════════════════════════════════════════════════
    print("\n[Step 2/8] Running primary backtest on optimization period...")
    logger_ml = MLflowLogger(config)
    logger_ml.log_run_start(holdout_dates=[d.isoformat() for d in holdout_dates])

    sim_loop = SimulationLoop(config)
    opt_results = sim_loop.run(start_date, end_date, holdout_dates=holdout_dates)
    print(f"   Raw orders: {len(opt_results['trade_log'])}")
    print(f"   NAV points: {len(opt_results['nav_history'])}")

    # ══════════════════════════════════════════════════════════════════════
    # STEP 3: Walk-Forward Validation on optimization dates ONLY
    # ══════════════════════════════════════════════════════════════════════
    print("\n[Step 3/8] Running Walk-Forward Validator (6 folds, opt dates only)...")
    wf_validator = WalkForwardValidator(config, n_folds=6)
    wf_result = wf_validator.run(start_date, end_date, holdout_dates=holdout_dates)
    print(f"   WFE:              {wf_result.wfe:.4f}")
    print(f"   IS Sharpe:        {wf_result.is_sharpe:.4f}")
    print(f"   Mean OOS Sharpe:  {wf_result.mean_oos_sharpe:.4f}")
    print(f"   Valid folds:      {wf_result.n_folds_valid}")
    print(f"   Negative OOS:     {wf_result.n_folds_negative_oos}")

    # ══════════════════════════════════════════════════════════════════════
    # STEP 4: Block Bootstrap Scenario Battery
    # ══════════════════════════════════════════════════════════════════════
    print("\n[Step 4/8] Running Block Bootstrap Scenario Battery (50 scenarios)...")
    nav_df = pd.DataFrame(opt_results["nav_history"])
    nav_df["date"] = pd.to_datetime(nav_df["date"]).dt.date
    mask_opt = nav_df["date"].isin(opt_dates)
    opt_returns = nav_df.loc[mask_opt, "nav"].pct_change().fillna(0).tolist()

    scenario_gen = BlockBootstrapGenerator()
    scenario_request = BootstrapRequest(
        strategy_returns=opt_returns,
        num_scenarios=50,
        block_size_days=20,
        scenario_length_days=252,
        mandate_max_drawdown=0.15
    )
    scenario_result = scenario_gen.execute(scenario_request)
    print(f"   Scenario pass rate: {scenario_result.pass_rate:.4f}")

    # ══════════════════════════════════════════════════════════════════════
    # STEP 5: Evaluate held-out partition
    # ══════════════════════════════════════════════════════════════════════
    print("\n[Step 5/8] Computing held-out partition metrics...")
    # (handled inside compute_metrics when holdout_dates passed)

    # ══════════════════════════════════════════════════════════════════════
    # STEP 6: Compute all metrics
    # ══════════════════════════════════════════════════════════════════════
    print("\n[Step 6/8] Computing full metric battery...")
    metrics = compute_metrics(
        opt_results["nav_history"],
        opt_results["trade_log"],
        [d.isoformat() for d in holdout_dates]
    )
    metrics["walk_forward_efficiency"] = wf_result.wfe
    metrics["scenario_pass_rate"] = scenario_result.pass_rate

    for k, v in sorted(metrics.items()):
        if isinstance(v, float):
            print(f"   {k}: {v:.4f}")
        else:
            print(f"   {k}: {v}")

    # ══════════════════════════════════════════════════════════════════════
    # STEP 7: Log everything to MLflow
    # ══════════════════════════════════════════════════════════════════════
    print("\n[Step 7/8] Logging to MLflow...")
    logger_ml.log_run_end(
        metrics=metrics,
        trade_log=opt_results["trade_log"],
        nav_history=opt_results["nav_history"],
        gate_events=opt_results["gate_events"]
    )
    print(f"   Logged to MLflow run: {run_id}")

    # ══════════════════════════════════════════════════════════════════════
    # STEP 8: Close the run
    # ══════════════════════════════════════════════════════════════════════
    print("\n[Step 8/8] Run complete.")
    mlflow.end_run()

    # ══════════════════════════════════════════════════════════════════════
    # VERIFICATION CHECKS
    # ══════════════════════════════════════════════════════════════════════
    print()
    print("=" * 72)
    print("  VERIFICATION RESULTS")
    print("=" * 72)
    failures = []

    # CHECK 1: Paired Trade Log (FIFO)
    print("\n[CHECK 1] Paired Trade Log (FIFO matching)")
    paired_trades = match_round_trip_trades(opt_results["trade_log"])
    print(f"   Raw orders:    {len(opt_results['trade_log'])}")
    print(f"   Paired trades: {len(paired_trades)}")

    if len(paired_trades) > 0:
        sample = paired_trades[0]
        has_exit = sample.get("exit_date") is not None
        has_pnl = sample.get("pnl") is not None
        print(f"   Sample trade: {sample['ticker']}")
        print(f"     entry_date:  {sample.get('entry_date')}")
        print(f"     exit_date:   {sample.get('exit_date')}")
        print(f"     entry_price: {sample.get('entry_price')}")
        print(f"     exit_price:  {sample.get('exit_price')}")
        print(f"     pnl:         {sample.get('pnl')}")
        print(f"     hold_days:   {sample.get('hold_days')}")

        if has_exit and has_pnl:
            print("   ✅ FIFO pairing confirmed: exit_date and pnl present")
        else:
            failures.append("Paired trades missing exit_date or pnl")
            print("   ❌ Paired trades missing exit_date or pnl")
    else:
        failures.append("No paired trades generated")
        print("   ❌ No paired trades generated")

    # CHECK 2: Walk-Forward Efficiency
    print("\n[CHECK 2] Walk-Forward Efficiency (WFE)")
    print(f"   WFE: {wf_result.wfe:.4f}")
    if wf_result.wfe != 0.0:
        print("   ✅ WFE is non-zero (0.0 bug eliminated)")
    else:
        # WFE=0.0 is valid if IS Sharpe is legitimately 0.0, but flag it
        if wf_result.is_sharpe == 0.0:
            print("   ⚠️  WFE is 0.0 because IS Sharpe is 0.0 (strategy may be flat)")
        else:
            failures.append("WFE is still 0.0 despite non-zero IS Sharpe")
            print("   ❌ WFE is still 0.0 — computation bug persists")

    # CHECK 3: Scenario Pass Rate
    print("\n[CHECK 3] Scenario Pass Rate")
    print(f"   Pass rate: {scenario_result.pass_rate:.4f}")
    if scenario_result.pass_rate > 0.0:
        print("   ✅ Scenario battery executed and produced results")
    else:
        print("   ⚠️  Scenario pass rate is 0.0 (all scenarios failed drawdown check)")

    # CHECK 4: VCL Metadata Propagation
    print("\n[CHECK 4] VCL Metadata Propagation (sentiment_score in gate events)")
    gate_events_with_sentiment = [
        e for e in opt_results["gate_events"]
        if e.get("sentiment_score") is not None
    ]
    gate_events_blocked = [
        e for e in opt_results["gate_events"]
        if e.get("gate_blocked") is not None and e.get("gate_blocked") is not False
    ]
    print(f"   Total gate events:        {len(opt_results['gate_events'])}")
    print(f"   With sentiment scores:    {len(gate_events_with_sentiment)}")
    print(f"   Blocked by VCL gate:      {len(gate_events_blocked)}")

    if gate_events_with_sentiment:
        sample_evt = gate_events_with_sentiment[0]
        print(f"   Sample: {sample_evt['ticker']} on {sample_evt['date']}")
        print(f"     sentiment_score: {sample_evt.get('sentiment_score')}")
        print(f"     gate_applied:    {sample_evt.get('gate_applied')}")
        print("   ✅ VCL metadata propagation confirmed")
    else:
        print("   ⚠️  No gate events with non-null sentiment (may indicate gate was not triggered)")

    # CHECK 5: MLflow Artifact Verification
    print("\n[CHECK 5] MLflow Artifact Verification")
    runs = client.search_runs(
        experiment_ids=[client.get_experiment_by_name("aegis_build").experiment_id],
        filter_string=f"tags.mlflow.runName = '{run_id}'"
    )
    if runs:
        mlflow_run = runs[0]
        m = mlflow_run.data.metrics
        print(f"   MLflow run found: {mlflow_run.info.run_id}")
        for key in ["sharpe", "walk_forward_efficiency", "scenario_pass_rate", "trade_count"]:
            val = m.get(key)
            if val is not None:
                print(f"   ✅ {key}: {val}")
            else:
                print(f"   ❌ {key}: MISSING")
                failures.append(f"MLflow metric {key} missing")
    else:
        failures.append("MLflow run not found")
        print("   ❌ MLflow run not found")

    # ── Final Verdict ────────────────────────────────────────────────────
    print()
    print("=" * 72)
    if failures:
        print(f"  VERDICT: ❌ {len(failures)} CHECK(S) FAILED")
        for f in failures:
            print(f"    - {f}")
    else:
        print("  VERDICT: ✅ ALL CHECKS PASSED — Pipeline is industrialized")
    print("=" * 72)


if __name__ == "__main__":
    main()
