# scripts/verify/01_intake_path_a.py
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from engines.intake.mandate_profile import MandateProfile
from engines.intake.user_intent import UserIntent
from engines.intake.contradiction import detect_contradictions
from engines.intake.confirmation import build_confirmation
from engines.intake.archetype_pool import StrategyArchetypePool

print("=== PHASE 1A: Path A Intake ===\n")

# Simulate a user who wants to trade momentum tech stocks
mandate = MandateProfile.from_path_a(
    risk_tolerance="moderate",
    time_horizon="swing",
    capital=50000
)

intent = UserIntent.from_path_a(
    raw_desire="momentum plays on mid-cap tech stocks, looking for breakout setups"
)

print(f"MandateProfile created:")
print(f"  Risk tolerance: {mandate.risk_tolerance}")
print(f"  Max drawdown: {mandate.max_drawdown_target:.0%}")
print(f"  Max position: {mandate.max_position_pct:.0%}")
print(f"  Stop-loss range: {mandate.stop_loss_range}")
print(f"  Holding period: {mandate.holding_period_range} days")
print(f"  Mandate ID: {mandate.mandate_profile_id}")

print(f"\nUserIntent created:")
print(f"  Raw desire: {intent.raw_desire}")
print(f"  Has preference: {intent.has_preference}")
print(f"  Universe tags: {intent.universe_tags}")

# Test immutability
try:
    mandate.max_drawdown_target = 0.99
    print("\n❌ FAIL: MandateProfile is NOT frozen — should be immutable")
except Exception:
    print("\n✅ MandateProfile is correctly frozen (immutable)")

# Test contradiction detection
contradictions = detect_contradictions(mandate, intent)
print(f"\nContradictions detected: {len(contradictions)}")
for c in contradictions:
    print(f"  [{c.severity}] {c.message}")

# Test confirmation screen data
confirmation = build_confirmation(mandate, intent)
print(f"\nConfirmation screen keys: {list(confirmation.keys())}")
assert "hard_constraints" in confirmation, "Missing hard_constraints in confirmation"
assert "desire_summary" in confirmation, "Missing desire_summary in confirmation"
print("✅ Confirmation screen data structure valid")

# Test to_builder_context()
mandate_ctx = mandate.to_builder_context()
intent_ctx = intent.to_builder_context()
assert len(mandate_ctx) > 50, "Mandate context too short"
assert len(intent_ctx) > 20, "Intent context too short"
print("✅ Builder context strings generated")

print("\n✅ PHASE 1A PASSED\n")
