"""
MandateProfile — frozen hard constraints for a trading mandate.

Immutable after creation. Captures the absolute limits the system will never exceed.
Two factory methods:
  - from_path_a(): deterministic mapping from 3 simple UI inputs
  - from_schema(): validated + normalized Path B JSON import

Thresholds are conservative by design:
  conservative → 10% drawdown, 2% position, 1-3% stop
  moderate     → 15% drawdown, 5% position, 2-5% stop
  aggressive   → 35% drawdown, 10% position, 3-8% stop
"""
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Tuple, List, Optional


SCHEMA_VERSION = "v7.0"


@dataclass(frozen=True)
class MandateProfile:
    risk_tolerance: str            # "conservative" | "moderate" | "aggressive"
    max_drawdown_target: float     # e.g. 0.10 = 10%
    max_position_pct: float        # e.g. 0.02 = 2%
    max_account_risk_pct: float    # total account risk per trade
    stop_loss_range: Tuple[float, float]      # (min%, max%) e.g. (0.01, 0.03)
    holding_period_range: Tuple[int, int]     # (min_days, max_days)
    allowed_asset_classes: Tuple[str, ...]    # immutable sequence
    leverage_permitted: bool
    mandate_profile_id: str
    created_at: datetime
    schema_version: str

    # ── Path A: Deterministic Mapping ─────────────────────────────────────

    # Lookup tables — no LLM, pure mapping
    _RISK_MAP = {
        "conservative": {
            "max_drawdown_target": 0.10,
            "max_position_pct": 0.02,
            "max_account_risk_pct": 0.01,
            "stop_loss_range": (0.01, 0.03),
            "leverage_permitted": False,
        },
        "moderate": {
            "max_drawdown_target": 0.15,
            "max_position_pct": 0.05,
            "max_account_risk_pct": 0.03,
            "stop_loss_range": (0.02, 0.05),
            "leverage_permitted": False,
        },
        "aggressive": {
            "max_drawdown_target": 0.35,
            "max_position_pct": 0.10,
            "max_account_risk_pct": 0.05,
            "stop_loss_range": (0.03, 0.08),
            "leverage_permitted": True,
        },
    }

    _HORIZON_MAP = {
        "day": {
            "holding_period_range": (0, 1),
            "allowed_asset_classes": ("equities", "etfs"),
        },
        "swing": {
            "holding_period_range": (3, 21),
            "allowed_asset_classes": ("equities", "etfs", "options"),
        },
        "position": {
            "holding_period_range": (21, 120),
            "allowed_asset_classes": ("equities", "etfs", "options", "bonds"),
        },
    }

    @classmethod
    def from_path_a(
        cls,
        risk_tolerance: str,
        time_horizon: str,
        capital: Optional[float] = None,
        raw_desire: str = "",
    ) -> "MandateProfile":
        """
        Factory for Path A (simple UI).

        Args:
            risk_tolerance: "conservative" | "moderate" | "aggressive"
            time_horizon: "day" | "swing" | "position"
            capital: Investable capital (informational, doesn't change constraints)
            raw_desire: Free text (used by UserIntent, not MandateProfile)
        """
        risk_key = _normalize_string(risk_tolerance)
        horizon_key = _normalize_string(time_horizon)

        if risk_key not in cls._RISK_MAP:
            raise ValueError(
                f"Invalid risk_tolerance: '{risk_tolerance}'. "
                f"Must be one of: {list(cls._RISK_MAP.keys())}"
            )
        if horizon_key not in cls._HORIZON_MAP:
            raise ValueError(
                f"Invalid time_horizon: '{time_horizon}'. "
                f"Must be one of: {list(cls._HORIZON_MAP.keys())}"
            )

        risk = cls._RISK_MAP[risk_key]
        horizon = cls._HORIZON_MAP[horizon_key]

        return cls(
            risk_tolerance=risk_key,
            max_drawdown_target=risk["max_drawdown_target"],
            max_position_pct=risk["max_position_pct"],
            max_account_risk_pct=risk["max_account_risk_pct"],
            stop_loss_range=risk["stop_loss_range"],
            holding_period_range=horizon["holding_period_range"],
            allowed_asset_classes=tuple(horizon["allowed_asset_classes"]),
            leverage_permitted=risk["leverage_permitted"],
            mandate_profile_id=str(uuid.uuid4()),
            created_at=datetime.utcnow(),
            schema_version=SCHEMA_VERSION,
        )

    # ── Path B: Schema Import ─────────────────────────────────────────────

    @classmethod
    def from_schema(cls, schema: dict) -> "MandateProfile":
        """
        Factory for Path B (comprehensive JSON schema import).

        Includes a normalization pass for LLM-produced inconsistencies:
          - Case normalization ("Conservative" → "conservative")
          - Whitespace stripping
          - Numeric string coercion ("20" → 20)
          - Percentage normalization (20 → 0.20 if > 1)
        """
        # Normalize the entire schema first
        schema = _normalize_schema(schema)

        required = schema.get("required", {})
        constraints = schema.get("constraints", {})

        # Extract risk tolerance (required)
        risk_tolerance = _normalize_string(required.get("risk_tolerance", "moderate"))
        if risk_tolerance not in cls._RISK_MAP:
            risk_tolerance = "moderate"  # safe default

        # Extract time horizon
        time_horizon = _normalize_string(required.get("time_horizon", "swing"))
        if time_horizon not in cls._HORIZON_MAP:
            time_horizon = "swing"

        # Get base from lookup tables
        risk = cls._RISK_MAP[risk_tolerance]
        horizon = cls._HORIZON_MAP[time_horizon]

        # Override with explicit schema values if provided
        max_dd = _coerce_pct(required.get("max_drawdown_pct", risk["max_drawdown_target"]))
        max_pos = _coerce_pct(constraints.get("max_single_position_pct", risk["max_position_pct"]))
        leverage = bool(constraints.get("leverage", risk["leverage_permitted"]))

        return cls(
            risk_tolerance=risk_tolerance,
            max_drawdown_target=max_dd,
            max_position_pct=max_pos,
            max_account_risk_pct=risk["max_account_risk_pct"],
            stop_loss_range=risk["stop_loss_range"],
            holding_period_range=horizon["holding_period_range"],
            allowed_asset_classes=tuple(horizon["allowed_asset_classes"]),
            leverage_permitted=leverage,
            mandate_profile_id=str(uuid.uuid4()),
            created_at=datetime.utcnow(),
            schema_version=schema.get("_schema_version", SCHEMA_VERSION),
        )

    # ── Builder Context ───────────────────────────────────────────────────

    def to_builder_context(self) -> str:
        """
        Structured plain-text for prompt injection into the Builder.
        The Supervisor injects this into every Builder call.
        """
        stop_lo, stop_hi = self.stop_loss_range
        hold_lo, hold_hi = self.holding_period_range

        lines = [
            "=== HARD CONSTRAINTS (non-negotiable) ===",
            f"Risk tolerance: {self.risk_tolerance}",
            f"Max portfolio drawdown: {self.max_drawdown_target:.0%}",
            f"Max position size: {self.max_position_pct:.0%} of portfolio per trade",
            f"Max account risk: {self.max_account_risk_pct:.0%} per trade",
            f"Stop-loss range: {stop_lo:.0%} – {stop_hi:.0%} per trade",
            f"Holding period: {hold_lo} – {hold_hi} days",
            f"Allowed asset classes: {', '.join(self.allowed_asset_classes)}",
            f"Leverage permitted: {'Yes' if self.leverage_permitted else 'No'}",
            "",
            "The strategy MUST respect all constraints above.",
            "Any generated config that violates these limits will be rejected.",
        ]
        return "\n".join(lines)


# ── Normalization Helpers ─────────────────────────────────────────────────────

def _normalize_string(value) -> str:
    """Normalize a string: lowercase, strip whitespace."""
    if value is None:
        return ""
    return str(value).strip().lower()


def _coerce_pct(value) -> float:
    """
    Coerce a value to a decimal percentage.
    Handles: 20 → 0.20, "20" → 0.20, 0.20 → 0.20, "0.20" → 0.20
    """
    if value is None:
        return 0.0
    try:
        v = float(value)
    except (ValueError, TypeError):
        return 0.0
    # If > 1, assume it's a whole-number percentage
    if v > 1.0:
        return v / 100.0
    return v


def _normalize_schema(schema: dict) -> dict:
    """
    Normalize an entire Path B schema for LLM-produced inconsistencies.
    Strips whitespace from string values, normalizes casing on known enum fields.
    """
    normalized = {}
    for key, value in schema.items():
        if isinstance(value, dict):
            normalized[key] = _normalize_schema(value)
        elif isinstance(value, str):
            normalized[key] = value.strip()
        elif isinstance(value, list):
            normalized[key] = [
                item.strip() if isinstance(item, str) else item
                for item in value
            ]
        else:
            normalized[key] = value
    return normalized
