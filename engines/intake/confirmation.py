"""
Confirmation Screen Data Layer — produces plain-language summary for UI.

build_confirmation(mandate, intent) -> dict

Returns a structured dict the UI renders directly.
Includes hard constraint box, product boundary messaging for catalyst-driven
desires, and any detected contradictions.
"""
from typing import Dict, Any, List, Optional

from engines.intake.mandate_profile import MandateProfile
from engines.intake.user_intent import UserIntent
from engines.intake.contradiction import detect_contradictions, Contradiction


# Catalyst-driven desire keywords that trigger product boundary messaging
_CATALYST_KEYWORDS = {
    "fda", "pdufa", "earnings", "catalyst", "announcement", "pre-announcement",
    "insider", "front-run", "beat the market", "first mover", "breaking news",
    "real-time", "alpha before", "before anyone",
}

_PRODUCT_BOUNDARY_MESSAGE = (
    "Aegis captures post-catalyst signal — momentum and positioning "
    "in the days after FDA events and earnings, not pre-announcement alpha. "
    "The system will not outrace institutional traders to the first tick."
)


def build_confirmation(
    mandate: MandateProfile,
    intent: UserIntent,
) -> Dict[str, Any]:
    """
    Build the confirmation screen data for UI rendering.

    Returns:
        {
            "desire_summary": str,
            "hard_constraints": {...},
            "product_boundary": Optional[str],
            "contradictions": [...],
            "risk_warning": Optional[str],
        }
    """
    stop_lo, stop_hi = mandate.stop_loss_range
    hold_lo, hold_hi = mandate.holding_period_range

    # Hard constraints box
    hard_constraints = {
        "max_drawdown": f"{mandate.max_drawdown_target:.0%}",
        "max_position_size": f"{mandate.max_position_pct:.0%} per trade",
        "stop_loss_range": f"{stop_lo:.0%} – {stop_hi:.0%} per trade",
        "holding_period": f"{hold_lo} – {hold_hi} days",
        "leverage": "Permitted" if mandate.leverage_permitted else "Not permitted",
        "asset_classes": list(mandate.allowed_asset_classes),
    }

    # Check for catalyst-driven desires → product boundary messaging
    product_boundary = None
    if intent.has_preference:
        desire_lower = intent.raw_desire.lower()
        if any(kw in desire_lower for kw in _CATALYST_KEYWORDS):
            product_boundary = _PRODUCT_BOUNDARY_MESSAGE

    # Detect contradictions
    contradictions = detect_contradictions(mandate, intent)

    # Risk warning for aggressive profiles
    risk_warning = None
    if mandate.risk_tolerance == "aggressive":
        risk_warning = (
            f"Your {mandate.max_drawdown_target:.0%} drawdown limit means "
            f"the portfolio could lose up to {mandate.max_drawdown_target:.0%} "
            f"of its value before the kill switch fires. "
            f"Make sure this level of risk is acceptable to you."
        )

    return {
        "desire_summary": _summarize_desire(intent),
        "hard_constraints": hard_constraints,
        "product_boundary": product_boundary,
        "contradictions": [
            {
                "rule_id": c.rule_id,
                "severity": c.severity,
                "message": c.message,
                "resolution_hint": c.resolution_hint,
            }
            for c in contradictions
        ],
        "risk_warning": risk_warning,
    }


def _summarize_desire(intent: UserIntent) -> str:
    """Build a plain-language summary of what the user wants."""
    if not intent.has_preference:
        return "No specific preference — the system will explore freely within your constraints."

    parts = [f"You want to: {intent.raw_desire}"]

    if intent.sectors_of_interest:
        parts.append(f"Focus on: {', '.join(intent.sectors_of_interest)}")

    if intent.sectors_to_avoid:
        parts.append(f"Avoid: {', '.join(intent.sectors_to_avoid)}")

    if intent.catalyst_types:
        parts.append(f"Catalyst types: {', '.join(intent.catalyst_types)}")

    return ". ".join(parts) + "."
