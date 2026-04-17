# scripts/verify/09_signal_card.py
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from dotenv import load_dotenv
load_dotenv()

print("=== PHASE 9: Signal Card & Freshness Validator ===\n")

from engines.sentinel.freshness_validator import (
    FreshnessValidator, FRESHNESS_THRESHOLDS
)
from engines.sentinel.price_feed import FinnhubPriceFeed
from unittest.mock import patch, MagicMock

# Test 1: Fresh signal on nominal session
print("Test 1: Fresh signal, nominal session → ACCEPT enabled")
os.environ["FINNHUB_API_KEY"] = "verify_mock_001"
feed = FinnhubPriceFeed()
validator = FreshnessValidator(price_feed=feed)

mock_signal = MagicMock()
mock_signal.signal_id = "test_signal_001"
mock_signal.ticker = "AAPL"
mock_signal.price = 180.00
mock_signal.volatility_bucket = "medium_volatility"
mock_signal.freshness_threshold = FRESHNESS_THRESHOLDS["medium_volatility"]
mock_signal.session_quality = "nominal"

with patch.object(FinnhubPriceFeed, 'get_mid_price', return_value=180.50):
    state = validator.validate_signal_freshness(mock_signal)

print(f"  Current price: ${state.current_price:.2f}")
print(f"  Intended entry: ${state.intended_entry:.2f}")
print(f"  Deviation: {state.price_deviation_pct:.2%}")
print(f"  Is fresh: {state.is_fresh}")
print(f"  Accept enabled: {state.accept_enabled}")
print(f"  Failure reason: {state.failure_reason}")
assert state.is_fresh, "Should be fresh"
assert state.accept_enabled, "Should be enabled"
assert state.failure_reason is None, "No failure reason expected"
print("  ✅ PASS")

# Test 2: Stale signal
print("\nTest 2: Stale signal (price moved 2%) → ACCEPT disabled")
with patch.object(FinnhubPriceFeed, 'get_mid_price', return_value=183.65):
    stale_state = validator.validate_signal_freshness(mock_signal)

print(f"  Deviation: {stale_state.price_deviation_pct:.2%}")
print(f"  Is fresh: {stale_state.is_fresh}")
print(f"  Accept enabled: {stale_state.accept_enabled}")
print(f"  Failure reason: {stale_state.failure_reason}")
assert not stale_state.is_fresh, "Should be stale"
assert not stale_state.accept_enabled, "Should be disabled"
assert stale_state.failure_reason == "price_stale", f"Wrong reason: {stale_state.failure_reason}"
print("  ✅ PASS")

# Test 3: Re-evaluation trigger
print("\nTest 3: Large price move (>2x threshold) → Re-evaluation triggered")
with patch.object(FinnhubPriceFeed, 'get_mid_price', return_value=190.00):
    reval_state = validator.validate_signal_freshness(mock_signal)

print(f"  Deviation: {reval_state.price_deviation_pct:.2%}")
print(f"  Reeval triggered: {reval_state.reeval_triggered}")
assert reval_state.reeval_triggered, "Re-evaluation should be triggered"
print("  ✅ PASS")

# Test 4: Degraded session overrides freshness
print("\nTest 4: Fresh price but degraded session → ACCEPT disabled")
degraded_signal = MagicMock()
degraded_signal.signal_id = "test_signal_002"
degraded_signal.ticker = "AAPL"
degraded_signal.price = 180.00
degraded_signal.volatility_bucket = "medium_volatility"
degraded_signal.freshness_threshold = FRESHNESS_THRESHOLDS["medium_volatility"]
degraded_signal.session_quality = "degraded"  # degraded session

with patch.object(FinnhubPriceFeed, 'get_mid_price', return_value=180.10):
    degraded_state = validator.validate_signal_freshness(degraded_signal)

print(f"  Is fresh: {degraded_state.is_fresh} (price is fine)")
print(f"  Session quality: degraded")
print(f"  Accept enabled: {degraded_state.accept_enabled}")
print(f"  Failure reason: {degraded_state.failure_reason}")
assert degraded_state.is_fresh, "Price should be fresh"
assert not degraded_state.accept_enabled, "Degraded session should disable ACCEPT"
assert degraded_state.failure_reason == "degraded_session"
print("  ✅ PASS")

# Test 5: Price feed timeout
print("\nTest 5: Finnhub timeout → ACCEPT disabled (fail closed)")
with patch.object(FinnhubPriceFeed, 'get_mid_price', return_value=None):
    timeout_state = validator.validate_signal_freshness(mock_signal)

print(f"  Accept enabled: {timeout_state.accept_enabled}")
print(f"  Failure reason: {timeout_state.failure_reason}")
assert not timeout_state.accept_enabled, "Timeout should disable ACCEPT"
assert timeout_state.failure_reason == "price_feed_timeout"
print("  ✅ PASS")

# Test 6: Speculative (biotech) uses tighter threshold
print("\nTest 6: Speculative volatility bucket uses tighter threshold")
speculative_threshold = FRESHNESS_THRESHOLDS["speculative"]
medium_threshold = FRESHNESS_THRESHOLDS["medium_volatility"]
print(f"  Speculative threshold: {speculative_threshold:.1%}")
print(f"  Medium threshold: {medium_threshold:.1%}")
assert speculative_threshold < medium_threshold, "Speculative should have tighter threshold"
print("  ✅ Speculative threshold is correctly tighter")

print("\n✅ PHASE 9 PASSED\n")
