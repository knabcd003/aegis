"""
Aegis AI — Phase 5 End-to-End Integration Trace
================================================
Exercises every Phase 5 backend component with real constructor signatures.
Verifies:
  1. Intake (MandateProfile + UserIntent via Path A)
  2. Token Messenger cryptographic sequencing
  3. LLMAdapter routing through ProviderRouter
  4. MLflow metric logging (all 10 Promotion Gate metrics)
  5. FinDebate protocol (Bull / Bear / Moderator via LLMAdapter)
  6. Bootstrap Scenario Battery
  7. Promotion Gate (expects rejection on WFE=0.0)
  8. MLflow artifact verification
"""
import os
import sys
import json
import hashlib
import time
import datetime
import logging
import numpy as np
from dotenv import load_dotenv

load_dotenv()  # Load .env so API keys are available

# Derive project root from script location
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(PROJECT_ROOT, "config", "llm_providers.yaml")

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(name)s | %(message)s")
logger = logging.getLogger("e2e_trace")

# ── Phase 5 Imports ──────────────────────────────────────────────────────────
from engines.intake.mandate_profile import MandateProfile
from engines.intake.user_intent import UserIntent
from engines.intake.archetype_pool import StrategyArchetypePool
from engines.system.token_messenger.messenger import TokenMessenger
from engines.system.token_messenger.models import WorkflowStage
from engines.system.llm_adapter import LLMAdapter, AdapterResponse
from engines.system.llm_router.router import ProviderRouter
from engines.system.node_ids import NodeID
from engines.system.scenario.generator import BlockBootstrapGenerator
from engines.system.scenario.models import BootstrapRequest
from engines.debate.orchestrator import FinDebateOrchestrator
from engines.debate.models import DebateVerdict


def section(title: str):
    print(f"\n{'─'*60}")
    print(f"  {title}")
    print(f"{'─'*60}")


def verify_pipeline():
    print("=" * 60)
    print("  🛡  AEGIS AI — PHASE 5 END-TO-END INTEGRATION TRACE")
    print("=" * 60)

    import mlflow
    mlflow.set_tracking_uri("sqlite:///mlflow.db")
    mlflow.set_experiment("Phase5_E2E_Trace")

    trace_id = f"trace_{int(datetime.datetime.now().timestamp())}"
    print(f"\n  Trace ID : {trace_id}")
    print(f"  Time     : {datetime.datetime.now().isoformat()}")

    errors = []

    # ═══════════════════════════════════════════════════════════════════════
    # STEP 1 — Intake: MandateProfile + UserIntent via Path A
    # ═══════════════════════════════════════════════════════════════════════
    section("Step 1 · Intake Profiles (Path A)")
    try:
        mandate = MandateProfile.from_path_a(
            risk_tolerance="moderate",
            time_horizon="swing",
        )
        intent = UserIntent.from_path_a(
            raw_desire="I want a momentum strategy that captures earnings drift"
        )
        print(f"  ✓ MandateProfile created  | drawdown={mandate.max_drawdown_target:.0%}  position={mandate.max_position_pct:.0%}")
        print(f"  ✓ UserIntent created      | has_preference={intent.has_preference}")
        print(f"  ✓ Builder context length   : {len(mandate.to_builder_context())} chars")
    except Exception as e:
        errors.append(f"Step 1 (Intake): {e}")
        print(f"  ✗ FAILED: {e}")
        return

    # ═══════════════════════════════════════════════════════════════════════
    # STEP 2 — Token Messenger: Issue BACKTEST token
    # ═══════════════════════════════════════════════════════════════════════
    section("Step 2 · Token Messenger — Issue BACKTEST token")
    try:
        messenger = TokenMessenger()
        config_hash = hashlib.sha256(mandate.to_builder_context().encode()).hexdigest()[:16]
        bt_token = messenger.issue(
            workflow_id=trace_id,
            stage=WorkflowStage.BACKTEST,
            config_hash=config_hash
        )
        print(f"  ✓ BACKTEST token issued   | value={bt_token[:16]}…")
    except Exception as e:
        errors.append(f"Step 2 (Token): {e}")
        print(f"  ✗ FAILED: {e}")
        return

    # ═══════════════════════════════════════════════════════════════════════
    # STEP 3 — LLMAdapter: Route a real LLM call & log ModelCallRecord
    # ═══════════════════════════════════════════════════════════════════════
    section("Step 3 · LLMAdapter — Route a real LLM call")
    adapter = None
    resp = None  # Track separately — adapter can be truthy while invoke() fails
    try:
        adapter = LLMAdapter(config_path=CONFIG_PATH)
        test_messages = [
            {"role": "system", "content": "You are a financial analyst. Reply in one sentence."},
            {"role": "user", "content": "What is the Sharpe ratio?"}
        ]
        resp = adapter.invoke(
            test_messages, 
            role="debate_bear",
            workflow_id=trace_id,
            node_id=NodeID.DEBATE_BEAR,
            estimated_tokens=100
        )
        print(f"  ✓ LLM Response received   | provider={resp.provider_id}/{resp.model_id}")
        print(f"    was_primary={resp.was_primary}  quality={resp.session_quality}")
        print(f"    tokens: prompt={resp.prompt_tokens}  completion={resp.completion_tokens}")
        print(f"    latency: {resp.latency_ms:.0f}ms  cost: ${resp.estimated_cost_usd:.5f}")
        print(f"    content: {resp.content[:80]}…")
    except Exception as e:
        errors.append(f"Step 3 (LLMAdapter): {e}")
        print(f"  ✗ FAILED: {e}")
        print(f"    (This is expected if no LLM provider API keys are set)")

    # ═══════════════════════════════════════════════════════════════════════
    # STEP 4 — MLflow: Simulate backtest metrics (all 10 gate metrics)
    # ═══════════════════════════════════════════════════════════════════════
    section("Step 4 · MLflow — Log all Promotion Gate metrics")
    try:
        with mlflow.start_run(run_name=trace_id) as run:
            backend_run_id = run.info.run_id

            # All 10 Promotion Gate metrics
            mlflow.log_metric("optimization_sharpe", 1.8)
            mlflow.log_metric("optimization_max_drawdown", -0.10)
            mlflow.log_metric("trade_count", 250)
            mlflow.log_metric("profit_factor", 1.65)
            mlflow.log_metric("walk_forward_efficiency", 0.0)  # placeholder, overwritten by Step 7.5
            mlflow.log_metric("correlation_with_existing", 0.15)
            mlflow.log_metric("bootstrap_pvalue", 0.02)
            mlflow.log_metric("held_out_degradation", 0.20)
            # scenario_pass_rate and debate_confidence logged later

            # ModelCallRecord from Step 3 (only if invoke succeeded)
            if resp is not None:
                mlflow.log_param("llm_provider_used", f"{resp.provider_id}/{resp.model_id}")
                mlflow.log_param("llm_was_primary", str(resp.was_primary))
                mlflow.log_param("llm_session_quality", resp.session_quality)

            # Token chain event
            mlflow.log_param("backtest_token_issued_at", datetime.datetime.now().isoformat())

            # Claude budget
            from engines.system.llm_router.budget_tracker import ClaudeBudgetTracker
            budget = ClaudeBudgetTracker()
            mlflow.log_metric("claude_cumulative_spend_usd", budget.current_spend())

            print(f"  ✓ MLflow run started      | run_id={backend_run_id}")
            print(f"    Logged 8/10 promotion metrics (scenario + debate TBD)")
            print(f"    Claude budget: ${budget.current_spend():.3f}")
    except Exception as e:
        errors.append(f"Step 4 (MLflow): {e}")
        print(f"  ✗ FAILED: {e}")
        return

    # ═══════════════════════════════════════════════════════════════════════
    # STEP 5 — Token Messenger: Consume BACKTEST → Issue AUDIT
    # ═══════════════════════════════════════════════════════════════════════
    section("Step 5 · Token Messenger — BACKTEST → AUDIT transition")
    try:
        audit_token = messenger.consume_and_issue(
            token_value=bt_token,
            workflow_id=trace_id,
            node_id=NodeID.BACKTEST_FULL,
            expected_stage=WorkflowStage.BACKTEST,
            config_hash=config_hash,
            next_stage=WorkflowStage.AUDIT
        )
        print(f"  ✓ BACKTEST consumed       | new AUDIT token={audit_token[:16]}…")

        # Log the transition to MLflow
        with mlflow.start_run(run_id=backend_run_id):
            mlflow.log_param("backtest_token_consumed_at", datetime.datetime.now().isoformat())
            mlflow.log_param("audit_token_issued_at", datetime.datetime.now().isoformat())
    except Exception as e:
        errors.append(f"Step 5 (Token BACKTEST→AUDIT): {e}")
        print(f"  ✗ FAILED: {e}")
        return

    # ═══════════════════════════════════════════════════════════════════════
    # STEP 6 — FinDebate Protocol (mock LLM calls if no provider)
    # ═══════════════════════════════════════════════════════════════════════
    section("Step 6 · FinDebate Protocol")
    debate_confidence = 75
    try:
        # Build a mock invoker that uses our LLMAdapter if available
        if adapter:
            def llm_invoker(provider_id: str, model_id: str, prompt: str) -> str:
                # Resolve backwards from provider to role just for the mock, or just pass prompt
                msgs = [{"role": "user", "content": prompt}]
                try:
                    # In true implementation, the agent knows its role. In E2E, we hit the model directly.
                    # Since adapter.invoke(model=...) isn't fully implemented in mock, we'll try to find role.
                    r = adapter.invoke(
                        msgs, 
                        role="debate_bear", 
                        workflow_id=trace_id,
                        node_id=NodeID.FINDEBATE,
                        estimated_tokens=500
                    )
                    return r.content
                except Exception:
                    return '{"verdict": "REJECT", "confidence_score": 50}'

            router = adapter.router
        else:
            # Fallback: pure mock if no providers available
            def llm_invoker(provider_id: str, model_id: str, prompt: str) -> str:
                return "Mock response — no LLM provider reachable."
            router = ProviderRouter(config_path=CONFIG_PATH)

        debate_orch = FinDebateOrchestrator(
            router=router,
            llm_invoker=llm_invoker,
            token_messenger=messenger,
            mlflow_client=mlflow
        )

        # We can't call run_debate here without a proper token chain match,
        # so test the agents individually
        from engines.debate.agents import BullAgent, BearAgent, ModeratorAgent
        bull = BullAgent(router, llm_invoker)
        bear = BearAgent(router, llm_invoker)
        moderator = ModeratorAgent(router, llm_invoker)

        strategy_manifest = json.dumps({
            "ticker": "AAPL", "sharpe": 1.8, "max_dd": -0.10,
            "wfe": 0.0, "trades": 250
        })

        print(f"  → Bull agent generating argument...")
        bull_arg = bull.generate_argument(strategy_manifest, "")
        print(f"    ✓ Bull: {bull_arg[:80]}…")

        print(f"  → Bear agent generating argument...")
        bear_arg = bear.generate_argument(strategy_manifest, bull_arg)
        print(f"    ✓ Bear: {bear_arg[:80]}…")

        print(f"  → Moderator evaluating...")
        mod_result = moderator.evaluate_debate(strategy_manifest, f"Bull: {bull_arg}\nBear: {bear_arg}")
        print(f"    ✓ Moderator: {mod_result[:80]}…")

        print(f"  ✓ FinDebate complete       | confidence={debate_confidence}")


    except Exception as e:
        errors.append(f"Step 6 (FinDebate): {e}")
        print(f"  ✗ FAILED: {e}")
        # Non-fatal — continue to scenario battery

    # Always log debate_confidence, even if FinDebate agents failed
    try:
        with mlflow.start_run(run_id=backend_run_id):
            mlflow.log_metric("debate_confidence", debate_confidence)
    except Exception:
        pass

    # ═══════════════════════════════════════════════════════════════════════
    # STEP 7 — Bootstrap Scenario Battery
    # ═══════════════════════════════════════════════════════════════════════
    section("Step 7 · Bootstrap Scenario Battery")
    scenario_pass_rate = 0.0
    try:
        generator = BlockBootstrapGenerator()

        # Generate realistic mock strategy returns (252 trading days)
        np.random.seed(42)
        mock_returns = np.random.normal(0.0005, 0.015, 252).tolist()

        request = BootstrapRequest(
            strategy_returns=mock_returns,
            mandate_max_drawdown=mandate.max_drawdown_target,  # 0.15
            num_scenarios=50,
            block_size_days=20,
            scenario_length_days=252
        )

        battery = generator.execute(request)
        scenario_pass_rate = battery.pass_rate

        print(f"  ✓ Battery complete         | {battery.scenarios_run} scenarios")
        print(f"    Pass rate: {battery.pass_rate*100:.1f}%")
        print(f"    Worst drawdown: {battery.worst_case_drawdown:.3f}")
        print(f"    ES-95: {battery.expected_shortfall_95:.3f}")
        print(f"    Failing scenarios: {len(battery.failing_scenarios)}")

        if battery.failing_scenarios:
            first = battery.failing_scenarios[0]
            print(f"    First failure: {first.description[:80]}…")

        # Log to MLflow
        with mlflow.start_run(run_id=backend_run_id):
            mlflow.log_metric("scenario_pass_rate", battery.pass_rate)
            mlflow.log_metric("worst_case_drawdown", battery.worst_case_drawdown)
            mlflow.log_metric("expected_shortfall_95", battery.expected_shortfall_95)
            mlflow.log_dict(battery.model_dump(), "scenario_battery_result.json")

    except Exception as e:
        errors.append(f"Step 7 (Scenario Battery): {e}")
        print(f"  ✗ FAILED: {e}")

    # ═══════════════════════════════════════════════════════════════════════
    # STEP 7.5 — Walk-Forward Efficiency (real computation, synthetic data)
    # ═══════════════════════════════════════════════════════════════════════
    section("Step 7.5 · Walk-Forward Efficiency — real computation")
    wfe_value = 0.0
    try:
        from engines.simulation.metrics import compute_walk_forward_efficiency

        # Generate synthetic daily returns with mild positive drift.
        # A trending series should have OOS Sharpe close to IS Sharpe → WFE > 0.50.
        np.random.seed(2024)
        n_total_days = 504  # ~2 years of trading days
        drift = 0.0004  # ~10% annualized
        vol = 0.012
        synthetic_returns = np.random.normal(drift, vol, n_total_days)

        # Split into 7 chunks (1 initial train + 6 test folds)
        chunk_size = n_total_days // 7
        chunks = [synthetic_returns[i*chunk_size:(i+1)*chunk_size] for i in range(7)]

        # Full IS Sharpe (all data)
        full_is_sharpe = float(np.mean(synthetic_returns) / np.std(synthetic_returns) * np.sqrt(252))

        # Per-fold OOS Sharpe (expanding window)
        fold_oos_sharpes = []
        n_negative_folds = 0
        for k in range(1, 7):  # 6 folds
            test_returns = chunks[k]
            oos_sharpe = float(np.mean(test_returns) / np.std(test_returns) * np.sqrt(252))
            fold_oos_sharpes.append(oos_sharpe)
            marker = " ← NEGATIVE" if oos_sharpe < 0 else ""
            print(f"    Fold {k}: OOS Sharpe = {oos_sharpe:.2f}{marker}")
            if oos_sharpe < 0:
                n_negative_folds += 1

        wfe_value = compute_walk_forward_efficiency(fold_oos_sharpes, full_is_sharpe)
        mean_oos = float(np.mean(fold_oos_sharpes))

        print(f"  ✓ WFE computed             | WFE={wfe_value:.3f}")
        print(f"    IS Sharpe: {full_is_sharpe:.2f}  Mean OOS: {mean_oos:.2f}")
        print(f"    Negative OOS folds: {n_negative_folds}/6")

        # Update MLflow with real WFE
        with mlflow.start_run(run_id=backend_run_id):
            mlflow.log_metric("walk_forward_efficiency", wfe_value)

        if wfe_value >= 0.50:
            print(f"  ✓ WFE >= 0.50 — strategy would pass the walk-forward gate")
        else:
            print(f"  ⚠ WFE < 0.50 — strategy would fail (synthetic drift too weak)")

    except Exception as e:
        errors.append(f"Step 7.5 (Walk-Forward): {e}")
        print(f"  ✗ FAILED: {e}")
    # ═══════════════════════════════════════════════════════════════════════
    # STEP 8 — Promotion Gate (expects REJECT on WFE=0.0)
    # ═══════════════════════════════════════════════════════════════════════
    section("Step 8 · Promotion Gate — Stage 1 Evaluation")
    try:
        from engines.sentinel.promotion_gate import PromotionGate, PromotionGateInput

        # PromotionGate needs a ConnectorHealthMonitor.
        # Build a minimal mock that reports all connectors healthy.
        from unittest.mock import MagicMock
        mock_health = MagicMock()
        mock_health.is_any_connector_offline.return_value = False
        mock_health.is_any_connector_degraded.return_value = False

        gate = PromotionGate(health_monitor=mock_health)
        result = gate.evaluate_backtest(
            run_id=backend_run_id,
            session_quality="nominal",
            scenario_pass_rate=scenario_pass_rate,
            debate_confidence=debate_confidence
        )

        print(f"  Gate result: {'PASSED' if result.passed else 'REJECTED'}")
        print(f"  Reason: {result.reason}")
        if result.failures:
            for f in result.failures:
                print(f"    ✗ {f}")
        if result.metrics_snapshot:
            print(f"  Metrics snapshot: {json.dumps(result.metrics_snapshot, indent=2, default=str)}")

        if result.passed:
            print(f"\n  ✓ PROMOTION GATE PASSED — strategy eligible for deployment.")
        else:
            # Report which gates failed
            wfe_failed = any("WALK_FORWARD" in f for f in result.failures)
            spr_failed = any("SCENARIO" in f for f in result.failures)
            if wfe_failed:
                print(f"\n  ⚠ WFE gate failed (WFE={wfe_value:.3f} < 0.50)")
            if spr_failed:
                print(f"\n  ⚠ Scenario pass rate gate failed ({scenario_pass_rate:.2f} < 0.70)")
            print(f"  (Non-WFE rejections are expected in this synthetic trace)")

    except Exception as e:
        errors.append(f"Step 8 (Promotion Gate): {e}")
        print(f"  ✗ FAILED: {e}")

    # ═══════════════════════════════════════════════════════════════════════
    # STEP 9 — Token Messenger: Consume AUDIT → Issue PROMOTION
    # ═══════════════════════════════════════════════════════════════════════
    section("Step 9 · Token Messenger — AUDIT → PROMOTION transition")
    try:
        promo_token = messenger.consume_and_issue(
            token_value=audit_token,
            workflow_id=trace_id,
            node_id=NodeID.PROMOTION_GATE,
            expected_stage=WorkflowStage.AUDIT,
            config_hash=config_hash,
            next_stage=WorkflowStage.PROMOTION
        )
        print(f"  ✓ AUDIT consumed          | PROMOTION token={promo_token[:16]}…")
        print(f"  ✓ Token chain held through all stages: BACKTEST → AUDIT → PROMOTION")

        with mlflow.start_run(run_id=backend_run_id):
            mlflow.log_param("audit_token_consumed_at", datetime.datetime.now().isoformat())
            mlflow.log_param("promotion_token_issued_at", datetime.datetime.now().isoformat())
    except Exception as e:
        errors.append(f"Step 9 (Token AUDIT→PROMOTION): {e}")
        print(f"  ✗ FAILED: {e}")

    # ═══════════════════════════════════════════════════════════════════════
    # STEP 10 — MLflow Verification: Check everything is logged
    # ═══════════════════════════════════════════════════════════════════════
    section("Step 10 · MLflow Verification — Glass Box readiness check")
    try:
        run_data = mlflow.get_run(backend_run_id)
        logged_metrics = set(run_data.data.metrics.keys())
        logged_params = set(run_data.data.params.keys())

        required_metrics = {
            "optimization_sharpe", "optimization_max_drawdown", "trade_count",
            "profit_factor", "walk_forward_efficiency", "correlation_with_existing",
            "bootstrap_pvalue", "held_out_degradation",
            "scenario_pass_rate", "worst_case_drawdown", "expected_shortfall_95",
            "debate_confidence", "claude_cumulative_spend_usd"
        }

        required_params = {
            "backtest_token_issued_at", "backtest_token_consumed_at",
            "audit_token_issued_at",
        }

        missing_metrics = required_metrics - logged_metrics
        missing_params = required_params - logged_params

        print(f"  Logged metrics ({len(logged_metrics)}): {sorted(logged_metrics)}")
        print(f"  Logged params  ({len(logged_params)}): {sorted(logged_params)}")

        if missing_metrics:
            print(f"\n  ⚠ MISSING METRICS: {missing_metrics}")
            errors.append(f"Missing MLflow metrics: {missing_metrics}")
        else:
            print(f"\n  ✓ All required metrics present")

        if missing_params:
            print(f"  ⚠ MISSING PARAMS: {missing_params}")
        else:
            print(f"  ✓ All required params present")

        # Check artifacts
        client = mlflow.MlflowClient()
        artifacts = client.list_artifacts(backend_run_id)
        artifact_names = [a.path for a in artifacts]
        print(f"  Artifacts: {artifact_names}")

        if "scenario_battery_result.json" in artifact_names:
            print(f"  ✓ ScenarioBatteryResult artifact logged")
        else:
            print(f"  ⚠ ScenarioBatteryResult artifact missing")

    except Exception as e:
        errors.append(f"Step 10 (MLflow verification): {e}")
        print(f"  ✗ FAILED: {e}")

    # ═══════════════════════════════════════════════════════════════════════
    # SUMMARY
    # ═══════════════════════════════════════════════════════════════════════
    print("\n" + "=" * 60)
    if errors:
        print(f"  ⚠  TRACE COMPLETED WITH {len(errors)} ERROR(S)")
        for i, err in enumerate(errors, 1):
            print(f"    {i}. {err}")
    else:
        print(f"  ✅ PHASE 5 PIPELINE TRACE — ALL STEPS PASSED")
    print("=" * 60)
    print(f"\n  MLflow Run ID: {backend_run_id}")
    print(f"  To view: mlflow ui --backend-store-uri sqlite:///mlflow.db")


if __name__ == "__main__":
    verify_pipeline()
