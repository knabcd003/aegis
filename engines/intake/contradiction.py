"""
Contradiction Detection — deterministic rules for intake validation.

Pure function: detect_contradictions(mandate, intent) -> list[Contradiction]

All rules are hardcoded boolean expressions — no NLP, no LLM.
Contradictions are warnings, not hard blocks. User resolves before confirming.
"""
from dataclasses import dataclass
from typing import List

from engines.intake.mandate_profile import MandateProfile
from engines.intake.user_intent import UserIntent


@dataclass
class Contradiction:
    rule_id: str
    severity: str         # "warning" (always — contradictions don't hard block)
    message: str
    resolution_hint: str


# Aggressive/speculative keywords that conflict with conservative risk
_AGGRESSIVE_KEYWORDS = {
    "speculative", "risky", "aggressive", "yolo", "meme", "penny",
    "high risk", "moonshot", "gamble", "volatile", "leveraged",
    "day trade", "day trading", "scalp", "scalping",
}

# High-volatility sectors that conflict with conservative drawdowns
_HIGH_VOL_SECTORS = {
    "biotech", "cannabis", "crypto", "cryptocurrency", "meme stocks",
    "penny stocks", "spac", "junior mining", "small-cap biotech",
}


def detect_contradictions(
    mandate: MandateProfile,
    intent: UserIntent,
) -> List[Contradiction]:
    """
    Check for contradictions between hard constraints and stated intent.
    Returns all detected contradictions (does not short-circuit).
    """
    contradictions: List[Contradiction] = []

    # Rule 1: Conservative drawdown + aggressive/speculative desire
    if mandate.risk_tolerance == "conservative" and intent.has_preference:
        desire_lower = intent.raw_desire.lower()
        matched = [kw for kw in _AGGRESSIVE_KEYWORDS if kw in desire_lower]
        if matched:
            contradictions.append(Contradiction(
                rule_id="CONSERVATIVE_AGGRESSIVE_DESIRE",
                severity="warning",
                message=(
                    f"Your risk tolerance is conservative (max {mandate.max_drawdown_target:.0%} drawdown) "
                    f"but your desire mentions aggressive terms: {', '.join(matched)}."
                ),
                resolution_hint=(
                    "Either raise your risk tolerance to 'moderate' or 'aggressive', "
                    "or adjust your desire to match conservative expectations."
                ),
            ))

    # Rule 2: Leverage requested + conservative risk tolerance
    if mandate.leverage_permitted and mandate.risk_tolerance == "conservative":
        contradictions.append(Contradiction(
            rule_id="LEVERAGE_CONSERVATIVE",
            severity="warning",
            message=(
                "Leverage is enabled but risk tolerance is conservative. "
                "Leveraged positions amplify both gains and losses, "
                "conflicting with a conservative drawdown target."
            ),
            resolution_hint=(
                "Disable leverage for conservative profiles, "
                "or raise risk tolerance to 'moderate' or 'aggressive'."
            ),
        ))

    # Rule 3: Ticker/sector exclusion conflicts with stated sector interest
    if intent.exclusions and intent.sectors_of_interest:
        exclusions_lower = {e.lower() for e in intent.exclusions}
        interests_lower = {s.lower() for s in intent.sectors_of_interest}
        overlap = exclusions_lower & interests_lower
        if overlap:
            contradictions.append(Contradiction(
                rule_id="EXCLUSION_INTEREST_CONFLICT",
                severity="warning",
                message=(
                    f"You excluded {', '.join(overlap)} but also listed them "
                    f"as sectors of interest. These are mutually exclusive."
                ),
                resolution_hint=(
                    "Remove the conflicting items from either your exclusions "
                    "or your sectors of interest."
                ),
            ))

    # Rule 4: Day-trading time horizon + conservative drawdown
    if (mandate.holding_period_range[1] <= 1 and
            mandate.risk_tolerance == "conservative"):
        contradictions.append(Contradiction(
            rule_id="DAY_TRADE_CONSERVATIVE",
            severity="warning",
            message=(
                "Day trading with a conservative drawdown target "
                f"({mandate.max_drawdown_target:.0%}) is very constrained. "
                "Intraday volatility may trigger your drawdown limit frequently."
            ),
            resolution_hint=(
                "Consider a longer holding period (swing), or raise your "
                "drawdown tolerance to accommodate intraday swings."
            ),
        ))

    # Rule 5: Leverage + day trading + conservative risk tolerance
    # (Deterministic replacement for "never lose money" NLP detection)
    if (mandate.leverage_permitted and
            mandate.holding_period_range[1] <= 1 and
            mandate.risk_tolerance == "conservative"):
        contradictions.append(Contradiction(
            rule_id="LEVERAGED_DAY_CONSERVATIVE",
            severity="warning",
            message=(
                "Leveraged day trading with conservative risk tolerance is "
                "a dangerous combination. Leveraged intraday positions can "
                "exceed your drawdown budget in a single session."
            ),
            resolution_hint=(
                "This combination should be avoided. Either disable leverage, "
                "extend your holding period, or raise your risk tolerance."
            ),
        ))

    return contradictions
