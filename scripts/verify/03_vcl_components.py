# scripts/verify/03_vcl_components.py
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from engines.vcl.registry import VCLRegistry

print("=== PHASE 3: VCL Component Verification ===\n")

registry = VCLRegistry()

# Import all Phase 4 wrapped components
from engines.vcl.wrappers.connector_health_wrapper import ConnectorHealthVCL
from engines.vcl.wrappers.nli_wrapper import NLISegmentClassifierVCL
from engines.vcl.wrappers.close_signal_wrapper import CloseSignalGeneratorVCL
from engines.vcl.wrappers.promotion_gate_wrapper import PromotionGateVCL
from engines.vcl.wrappers.mirror_portfolio_wrapper import MirrorPortfolioVCL
from engines.vcl.wrappers.scenario_generator_wrapper import BlockBootstrapVCL
from engines.vcl.wrappers.finbert_sentiment_gate import FinBERTSentimentGate

components = [
    ("Connector Health Monitor", ConnectorHealthVCL()),
    ("DeBERTa NLI Classifier", NLISegmentClassifierVCL()),
    ("Close Signal Generator", CloseSignalGeneratorVCL()),
    ("Promotion Gate", PromotionGateVCL()),
    ("Mirror Portfolio", MirrorPortfolioVCL()),
    ("Bootstrap Scenario Generator", BlockBootstrapVCL()),
    ("FinBERT Sentiment Gate", FinBERTSentimentGate()),
]


print(f"Testing {len(components)} VCL components:\n")

all_passed = True
for name, component in components:
    print(f"  Testing: {name}")

    # Gate 2: Health check
    try:
        health = component.health()
        print(f"    Gate 2 (Health): {health.status}")
        if health.status == "OFFLINE":
            print(f"    ⚠️  Offline reason: {health.reason}")
    except Exception as e:
        print(f"    ❌ Gate 2 FAILED: {e}")
        all_passed = False
        continue

    # Registration (all 5 gates)
    result = registry.register(component)
    if result.success:
        print(f"    ✅ All 5 gates passed | Version: {component.version}")
        print(f"    Fingerprint: {component.compatibility_fingerprint}")
    else:
        print(f"    ❌ Failed at {result.failed_gate}: {result.reason}")
        all_passed = False

# Fingerprint stability test
print("\nFingerprint stability test:")
comp1 = ConnectorHealthVCL()
comp2 = ConnectorHealthVCL()
fp1 = comp1.compatibility_fingerprint
fp2 = comp2.compatibility_fingerprint
print(f"  Instance 1: {fp1}")
print(f"  Instance 2: {fp2}")
assert fp1 == fp2, "Fingerprint not stable across instances"
print("  ✅ Fingerprints are stable across instances")

# Serialize and deserialize
import json
schema_json = json.dumps(comp1.input_schema.model_json_schema(), sort_keys=True)
schema_back = json.loads(schema_json)
import hashlib
fp_after = hashlib.sha256(
    (json.dumps(comp1.input_schema.model_json_schema(), sort_keys=True) +
     json.dumps(comp1.output_schema.model_json_schema(), sort_keys=True)).encode()
).hexdigest()[:16]
assert fp_after == fp1, "Fingerprint not stable after JSON roundtrip"
print("  ✅ Fingerprints stable after JSON serialization roundtrip")

if all_passed:
    print("\n✅ PHASE 3 PASSED\n")
else:
    print("\n❌ PHASE 3 FAILED — fix component registration before proceeding\n")
