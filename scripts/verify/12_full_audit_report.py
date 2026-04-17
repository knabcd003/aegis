# scripts/verify/12_full_audit_report.py
import sys, os, subprocess, json
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

print("=== PHASE 12: Full Pipeline Audit Report ===\n")
print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

phases = [
    ("01_intake_path_a.py",    "Path A Intake"),
    ("01b_intake_path_b.py",   "Path B Intake"),
    ("01c_archetype_pool.py",  "Strategy Archetype Pool"),
    ("02_llm_routing.py",      "LLM Routing & Providers"),
    ("03_vcl_components.py",   "VCL Component Registry"),
    ("04_token_messenger.py",  "Token Messenger Security"),
    ("05_real_backtest.py",    "Real Backtest (5-15 min)"),
    ("06_findebate.py",        "FinDebate Adversarial Audit"),
    ("07_promotion_gate.py",   "Promotion Gate Evaluation"),
    ("08_scenario_battery.py", "Bootstrap Scenario Battery"),
    ("09_signal_card.py",      "Signal Card & Freshness"),
    ("10_websocket.py",        "WebSocket Event Pipeline"),
    ("11_live_proving_ground.py", "5-Min Live Proving Ground"),
]

results = {}
verify_dir = "/Users/karthikn/Documents/Computer Science/Aegis_AI/scripts/verify"

for script, description in phases:
    script_path = os.path.join(verify_dir, script)
    if not os.path.exists(script_path):
        results[description] = ("SKIPPED", "Script not found")
        continue

    print(f"Running: {description}...")
    
    # Quick report check for heavy phases
    success_file = f"/tmp/aegis_verify_{script.replace('.py', '')}_passed.txt"
    if os.getenv("QUICK_REPORT") == "true" and os.path.exists(success_file):
        print(f"  ✅ PASSED (from state file)")
        results[description] = ("PASSED", None)
        continue

    try:
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            timeout=1800
        )

        if result.returncode == 0:
            results[description] = ("PASSED", None)
            print(f"  ✅ PASSED")
        else:
            last_error = result.stderr.strip().split('\n')[-1] if result.stderr else "Unknown error"
            results[description] = ("FAILED", last_error)
            print(f"  ❌ FAILED: {last_error}")
    except subprocess.TimeoutExpired:
        results[description] = ("FAILED", "Timeout expired (1800s)")
        print(f"  ❌ FAILED: Timeout")
    except Exception as e:
        results[description] = ("FAILED", str(e))
        print(f"  ❌ FAILED: {e}")

print("\n" + "="*60)
print("AEGIS AI v7 — END-TO-END VERIFICATION REPORT")
print("="*60)

passed = sum(1 for s, _ in results.values() if s == "PASSED")
failed = sum(1 for s, _ in results.values() if s == "FAILED")
skipped = sum(1 for s, _ in results.values() if s == "SKIPPED")
total = len(results)

print(f"\nTotal: {total} | Passed: {passed} | Failed: {failed} | Skipped: {skipped}")
print(f"Score: {passed}/{total - skipped} ({passed/(total-skipped)*100:.0f}%)\n")

for description, (status, error) in results.items():
    icon = "✅" if status == "PASSED" else "❌" if status == "FAILED" else "⏭️"
    print(f"  {icon} {description}")
    if error:
        print(f"       Error: {error}")

if failed == 0:
    print("\n🎉 ALL PHASES PASSED — Pipeline is verified and ready")
    print("Proceed to: Phase 6 (Interactive Flow Editor) or production deployment")
else:
    print(f"\n⚠️  {failed} PHASE(S) FAILED — fix before proceeding")
    print("Each failed phase above has a specific error message to diagnose from")

# Save report
report = {
    "timestamp": datetime.now().isoformat(),
    "results": {k: {"status": v[0], "error": v[1]} for k, v in results.items()},
    "summary": {"passed": passed, "failed": failed, "skipped": skipped, "total": total}
}

os.makedirs("data/verification_reports", exist_ok=True)
report_path = f"data/verification_reports/e2e_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
with open(report_path, "w") as f:
    json.dump(report, f, indent=2)

print(f"\nFull report saved: {report_path}")
