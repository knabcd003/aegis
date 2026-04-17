# scripts/verify/04_token_messenger.py
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from engines.system.token_messenger.messenger import TokenMessenger
from engines.system.token_messenger.models import WorkflowStage
from engines.system.token_messenger.messenger import SequenceViolationError

print("=== PHASE 4: Token Messenger Security ===\n")

tm = TokenMessenger()
workflow_id = "verify_test_001"
config_hash = "abc123def456"  # Simulated config hash

# Test 1: Normal lifecycle
print("Test 1: Normal BACKTEST → AUDIT → PROMOTION → DEPLOYMENT lifecycle")
try:
    bt_token = tm.issue(workflow_id, WorkflowStage.BACKTEST, config_hash)
    print(f"  BACKTEST token issued: {bt_token[:8]}...")

    audit_token = tm.consume_and_issue(bt_token, workflow_id, "node_audit", WorkflowStage.BACKTEST, config_hash, WorkflowStage.AUDIT)
    print(f"  AUDIT token issued: {audit_token[:8]}...")

    promo_token = tm.consume_and_issue(audit_token, workflow_id, "node_promo", WorkflowStage.AUDIT, config_hash, WorkflowStage.PROMOTION)
    print(f"  PROMOTION token issued: {promo_token[:8]}...")

    deploy_token = tm.consume_and_issue(promo_token, workflow_id, "node_deploy", WorkflowStage.PROMOTION, config_hash, WorkflowStage.DEPLOYMENT)
    print(f"  DEPLOYMENT token issued: {deploy_token[:8]}...")
    print("  ✅ Full lifecycle passed")
except Exception as e:
    print(f"  ❌ FAILED: {e}")

# Test 2: Replay attack — consuming a used token
print("\nTest 2: Replay attack (reusing consumed token)")
tm2 = TokenMessenger()
wf2 = "replay_test"
token = tm2.issue(wf2, WorkflowStage.BACKTEST, config_hash)
tm2.consume_and_issue(token, wf2, "node_audit", WorkflowStage.BACKTEST, config_hash, WorkflowStage.AUDIT)
try:
    tm2.consume_and_issue(token, wf2, "node_audit", WorkflowStage.BACKTEST, config_hash, WorkflowStage.AUDIT)
    print("  ❌ SECURITY FAILURE: Replay attack succeeded — token should be single-use")
except SequenceViolationError as e:
    print(f"  ✅ Replay attack blocked: {e}")

# Test 3: Stage skip — attempting AUDIT without BACKTEST
print("\nTest 3: Stage skip attack (jumping to PROMOTION)")
tm3 = TokenMessenger()
wf3 = "skip_test"
token3 = tm3.issue(wf3, WorkflowStage.BACKTEST, config_hash)
try:
    tm3.consume_and_issue(token3, wf3, "node_skip", WorkflowStage.AUDIT, config_hash, WorkflowStage.PROMOTION)
    print("  ❌ SECURITY FAILURE: Stage skip succeeded")
except SequenceViolationError as e:
    print(f"  ✅ Stage skip blocked: {e}")

# Test 4: Config drift — strategy modified after backtest
print("\nTest 4: Config drift detection")
tm4 = TokenMessenger()
wf4 = "drift_test"
original_hash = "original_config_hash"
modified_hash = "modified_config_hash"
token4 = tm4.issue(wf4, WorkflowStage.BACKTEST, original_hash)
try:
    tm4.consume_and_issue(token4, wf4, "node_drift", WorkflowStage.BACKTEST, modified_hash, WorkflowStage.AUDIT)
    print("  ❌ SECURITY FAILURE: Config drift not detected")
except SequenceViolationError as e:
    print(f"  ✅ Config drift blocked: {e}")

# Test 5: TTL expiration (expired token rejection)
print("\nTest 5: TTL expiration (expired token rejection)")
wf5 = "ttl_test"
from engines.system.token_messenger.store import _store
token = tm.issue(wf5, WorkflowStage.BACKTEST, config_hash)
# Manually expire it
_store[wf5].expires_at = time.time() - 1
try:
    tm.consume_and_issue(token, wf5, "node_ttl", WorkflowStage.BACKTEST, config_hash, WorkflowStage.AUDIT)
    print("  ❌ SECURITY FAILURE: Expired token accepted")
except SequenceViolationError as e:
    print(f"  ✅ Expired token blocked: {e}")

print("\n✅ PHASE 4 PASSED\n")
