import datetime
from typing import Optional
from pydantic import BaseModel
from engines.sentinel.state_manager import SignalCard
from engines.sentinel.price_feed import FinnhubPriceFeed, ConfigurationError

FRESHNESS_THRESHOLDS = {
    "low_volatility":    0.015,   # bonds, large-cap defensives
    "medium_volatility": 0.010,   # large-cap equities, ETFs
    "high_volatility":   0.007,   # mid-cap equities
    "speculative":       0.005,   # small-cap, biotech, crypto-adjacent
}

class SignalFreshnessState(BaseModel):
    is_fresh:              bool
    current_price:         Optional[float]
    intended_entry:        float
    price_deviation_pct:   Optional[float]
    freshness_threshold:   float
    last_checked_at:       datetime.datetime
    reeval_triggered:      bool    # True if deviation > 2x threshold
    accept_enabled:        bool    # False if stale OR degraded session
    failure_reason:        Optional[str]  # e.g. "price_feed_timeout", "price_stale", "degraded_session", "stale_and_degraded"

class FreshnessValidator:
    def __init__(self, price_feed: FinnhubPriceFeed):
        self.price_feed = price_feed

    def validate_signal_freshness(self, signal: SignalCard) -> SignalFreshnessState:
        now = datetime.datetime.now(datetime.timezone.utc)
        threshold = signal.freshness_threshold
        intended_entry = signal.price
        
        current_price = self.price_feed.get_mid_price(signal.ticker)
        
        if current_price is None or current_price <= 0:
            # Timeout or network error safely blocks the UI
            failure_reason = "price_feed_timeout"
            if signal.session_quality != "nominal":
                failure_reason = "stale_and_degraded"
                
            return SignalFreshnessState(
                is_fresh=False,
                current_price=None,
                intended_entry=intended_entry,
                price_deviation_pct=None,
                freshness_threshold=threshold,
                last_checked_at=now,
                reeval_triggered=False,
                accept_enabled=False,
                failure_reason=failure_reason
            )
            
        deviation = abs((current_price - intended_entry) / intended_entry) if intended_entry else 0.0
        
        is_fresh = (deviation <= threshold)
        reeval_triggered = (deviation > threshold * 2)
        is_nominal_session = (signal.session_quality == "nominal")
        
        accept_enabled = is_fresh and is_nominal_session
        
        failure_reason = None
        if not accept_enabled:
            # Structurally record the specific gating event to correctly inform the frontend UI
            if not is_fresh and not is_nominal_session:
                failure_reason = "stale_and_degraded"
            elif not is_fresh:
                failure_reason = "price_stale"
            elif not is_nominal_session:
                failure_reason = "degraded_session"
                
        return SignalFreshnessState(
            is_fresh=is_fresh,
            current_price=current_price,
            intended_entry=intended_entry,
            price_deviation_pct=deviation,
            freshness_threshold=threshold,
            last_checked_at=now,
            reeval_triggered=reeval_triggered,
            accept_enabled=accept_enabled,
            failure_reason=failure_reason
        )
