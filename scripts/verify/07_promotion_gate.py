# scripts/verify/07_promotion_gate.py
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from dotenv import load_dotenv
load_dotenv()

print("=== PHASE 7: Promotion Gate Evaluation ===\n")

# Load run_id from previous phase
try:
    with open("/tmp/aegis_verify_run_id.txt") as f:
        run_id = f.read().strip()
except FileNotFoundError:
    print("❌ No run_id found — run Phase 5 first")
    sys.exit(1)

from engines.sentinel.promotion_gate import PromotionGate
from engines.system.token_messenger.messenger import TokenMessenger
from engines.system.token_messenger.models import WorkflowStage

tm = TokenMessenger()
workflow_id = "e2e_verify_001"

# 1. Load data from previous phases
try:
    with open("/tmp/aegis_verify_audit_token.txt") as f:
        audit_token = f.read().strip()
except FileNotFoundError:
    print("❌ No audit_token found — run Phase 6 first")
    sys.exit(1)

# 2. Setup mock health monitor for gate verification
class MockHealthMonitor:
    def is_any_connector_offline(self): return False
    def is_any_connector_degraded(self): return False

gate = PromotionGate(health_monitor=MockHealthMonitor())
config_hash = "verify_hash_001" # Matches Phase 6 genesis

print(f"Evaluating run_id: {run_id}")
print(f"Audit token loaded: {audit_token[:12]}...")
print("Applying all 10 Promotion Gate thresholds:\n")

# 3. Execute industrialized gate evaluation
import mlflow
mlflow.set_tracking_uri("sqlite:////Users/karthikn/Documents/Computer Science/Aegis_AI/mlflow.db")

result = gate.evaluate(
    run_id=run_id,
    workflow_id=workflow_id,
    audit_token=audit_token,
    config_hash=config_hash,
    session_quality="nominal",
    scenario_pass_rate=0.75, # Mocked for gate test (usually from FinDebate)
    debate_confidence=70      # Mocked for gate test (usually from FinDebate)
)

print(f"Gate result: {'✅ PASSED' if result.passed else '❌ FAILED'}")
print(f"Reason: {result.reason}")

if result.failures:
    print(f"\nFailed gates:")
    for failure in result.failures:
        print(f"  ❌ {failure}")
else:
    print("\n✅ All gates passed")

print(f"\nGate details (Metrics Snapshot):")
for metric, value in result.metrics_snapshot.items():
    print(f"  - {metric}: {value}")

if result.passed:
    print(f"\nPromotion verified for run {run_id}")
    with open("/tmp/aegis_verify_promotion_passed.txt", "w") as f:
        f.write("true")
else:
    # We still check the file to be sure 
    with open("/tmp/aegis_verify_promotion_passed.txt", "w") as f:
        f.write("false")

print("\n✅ PHASE 7 COMPLETE\n")
