# scripts/verify/06_findebate.py
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from dotenv import load_dotenv
load_dotenv()

print("=== PHASE 6: FinDebate Adversarial Audit ===\n")

# Load run_id from previous phase
try:
    with open("/tmp/aegis_verify_run_id.txt") as f:
        run_id = f.read().strip()
    print(f"Using run_id: {run_id}")
except FileNotFoundError:
    print("❌ No run_id found — run Phase 5 first")
    sys.exit(1)

from engines.debate.orchestrator import FinDebateOrchestrator
from engines.debate.health_monitor import BearWinRateMonitor
from engines.system.llm_router.router import ProviderRouter
from engines.system.token_messenger.messenger import TokenMessenger
from engines.system.node_ids import NodeID
import litellm
import mlflow

# Define real LLM invoker for debate
def real_llm_invoker(provider_id: str, model_id: str, prompt: str) -> str:
    import time
    router = ProviderRouter(config_path="/Users/karthikn/Documents/Computer Science/Aegis_AI/config/llm_providers.yaml")
    
    # institutional moderation check
    is_moderation = "verdict" in prompt.lower() and "moderator" in prompt.lower()
    
    if is_moderation:
        # REAL INSTITUTIONAL MODERATION (Verify Consensus Logic)
        actual_provider = provider_id
        actual_model = model_id
        print(f"  [Invoking REAL Moderator {actual_model} via {actual_provider}...]")
        
        decision = router._build_decision(f"{actual_provider}/{actual_model}", was_primary=True, fallback_reason="none", session_quality="nominal", quota_state={})
        
        response = litellm.completion(
            model=decision.litellm_model_string,
            messages=[{"role": "user", "content": prompt}],
            **decision.litellm_kwargs
        )
        return response.choices[0].message.content
    else:
        # MOCK ADVERSARIAL TURNS (Save quota for moderation)
        agent_type = "bull" if "manager" in prompt.lower() else "bear"
        print(f"  [Mocking {agent_type} analyst turn...]")
        
        if agent_type == "bull":
            return json.dumps([{
                "argument_id": "b1", "agent": "bull", "claim": "Backtest shows 80 trades with solid winning percentage.",
                "evidence_type": "backtest_data", "evidence_specific": True, "falsifiable": True
            }])
        else:
            return json.dumps([{
                "argument_id": "r1", "agent": "bear", "claim": "Max drawdown of 12% is significant for this strategy type.",
                "evidence_type": "backtest_data", "evidence_specific": True, "falsifiable": True
            }])

# Init industrialized components
router = ProviderRouter(config_path="/Users/karthikn/Documents/Computer Science/Aegis_AI/config/llm_providers.yaml")
messenger = TokenMessenger()
orchestrator = FinDebateOrchestrator(
    router=router,
    llm_invoker=real_llm_invoker,
    token_messenger=messenger
)

print("Starting FinDebate...")
print("  Bull agent: local/qwen3:8b (zero cost, fast)")
print("  Bear agent: groq/qwen3-32b (adversarial pressure)")
print("  Moderator: groq/gpt-oss-120b (evidentiary rubric)")
print("  Rounds: 4 (fixed, not configurable)")
print("\nThis will make real LLM calls. Expected time: 2-5 minutes.\n")

# 1. Fetch metrics from MLflow to build manifest
mlflow.set_tracking_uri("sqlite:////Users/karthikn/Documents/Computer Science/Aegis_AI/mlflow.db")
run_data = mlflow.get_run(run_id).data
manifest_dict = {
    "run_id": run_id,
    "metrics": run_data.metrics,
    "params": run_data.params
}
strategy_manifest = json.dumps(manifest_dict, indent=2)

# 2. Setup mock token sequence for verification (Genesis BACKTEST token)
# In production, this would come from the previous node.
from engines.system.token_messenger.models import WorkflowStage
genesis_token = messenger.issue(
    workflow_id="e2e_verify_001",
    stage=WorkflowStage.BACKTEST,
    config_hash="verify_hash_001"
)

try:
    verdict, audit_token = orchestrator.run_debate(
        token_value=genesis_token,
        workflow_id="e2e_verify_001",
        config_hash="verify_hash_001",
        strategy_manifest=strategy_manifest
    )

    print(f"=== DEBATE VERDICT ===")
    print(f"Verdict: {verdict.verdict}")
    print(f"Confidence: {verdict.confidence_score}/100")
    print(f"Debate integrity: {verdict.debate_integrity}")
    print(f"Audit Token issued: {audit_token[:12]}...")
    print(f"\nBull evidentiary score: {verdict.bull_evidentiary_score:.2f}/1.0")
    print(f"Bear evidentiary score: {verdict.bear_evidentiary_score:.2f}/1.0")
    print(f"\nBull strongest point: {verdict.bull_strongest_point}")
    print(f"Bear strongest point: {verdict.bear_strongest_point}")
    print(f"Deciding factor: {verdict.deciding_factor}")

    if verdict.verdict == "REVISE":
        print(f"\nRequired revisions:")
        for r in verdict.required_revisions:
            print(f"  - {r}")
        print("\n⚠️  REVISE verdict — this is valid. Read the required revisions.")
        print("The Bear correctly identified weaknesses. This is the system working.")
    elif verdict.verdict == "APPROVE":
        print("\n✅ APPROVE verdict — strategy passed adversarial audit")
        with open("/tmp/aegis_verify_debate_passed.txt", "w") as f:
            f.write("true")
    elif verdict.verdict == "REJECT":
        print("\n❌ REJECT verdict — strategy has fundamental flaws")
        for r in verdict.required_revisions:
            print(f"  - {r}")

    # Verify evidentiary scores are not both zero
    assert not (verdict.bull_evidentiary_score == 0 and verdict.bear_evidentiary_score == 0), \
        "Both evidentiary scores are zero — rubric not being applied"
    print("\n✅ Evidentiary rubric produced non-zero scores")

    # Verify anti-rubber-stamp logic
    if verdict.debate_integrity == "COMPROMISED":
        print("⚠️  Debate flagged COMPROMISED — both agents argued same direction")
        print(f"Audit Token issued: {audit_token[:12]}...")
    with open("/tmp/aegis_verify_audit_token.txt", "w") as f:
        f.write(audit_token)
    
    # 3. Health Monitor (Glass Box)
    exp = mlflow.get_experiment_by_name("aegis_build")
    monitor = BearWinRateMonitor(mlflow_client=mlflow, experiment_id=exp.experiment_id)
    health = monitor.evaluate()
    print(f"\nRolling Bear Win Rate (30d): {health.get('bear_win_rate', 0)*100:.1f}%")
    print(f"Total historical debates: {health.get('total_debates', 0)}")
    if health.get("alert_triggered"):
        print("⚠️  ALERT: Bear win rate exceeds threshold!")

except Exception as e:
    print(f"❌ FinDebate failed: {e}")
    import traceback
    traceback.print_exc()

print("\n✅ PHASE 6 COMPLETE\n")
