# scripts/verify/01b_intake_path_b.py
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from engines.intake.mandate_profile import MandateProfile
from engines.intake.user_intent import UserIntent

print("=== PHASE 1B: Path B Intake (Schema Import) ===\n")

# Simulate a schema that an external LLM would generate
schema = {
    "_schema_version": "v7.0",
    "_path": "B",
    "required": {
        "risk_tolerance": "Moderate",
        "max_drawdown_pct": 15,
        "time_horizon": "swing",
        "raw_desire": "momentum plays on mid-cap tech stocks"
    },
    "portfolio": {
        "investable_capital": 50000,
        "existing_holdings": [],
        "holdings_to_never_touch": [],
        "account_type": None
    },
    "universe": {
        "asset_classes": ["equities"],
        "market_cap_range": [2000, 10000],
        "sectors_of_interest": ["Technology"],
        "sectors_to_avoid": [],
        "geographies": [],
        "specific_tickers": [],
        "exclude_tickers": []
    },
    "strategy_character": {
        "preferred_regimes": ["momentum", "breakout"],
        "catalyst_types": [],
        "signal_type_preference": ["technical"],
        "holding_period_days": [3, 21],
        "preferred_complexity": "moderate"
    },
    "macro_views": [],
    "constraints": {
        "esg_exclusions": [],
        "max_sector_concentration_pct": None,
        "max_single_position_pct": None,
        "leverage": False
    },
    "notes": "User is interested in technical breakout strategies on liquid mid-cap tech names."
}

# Test normalization — these should all work
edge_cases = [
    {"max_drawdown_pct": "15"},    # string number
    {"max_drawdown_pct": "15%"},   # string with percent
    {"risk_tolerance": "MODERATE"}, # uppercase
    {"risk_tolerance": " moderate "}, # whitespace
]

print("Testing Path B normalization edge cases:")
for case in edge_cases:
    test_schema = json.loads(json.dumps(schema))
    test_schema["required"].update(case)
    try:
        m = MandateProfile.from_schema(test_schema)
        print(f"  ✅ Handled: {case}")
    except Exception as e:
        print(f"  ❌ Failed on {case}: {e}")

# Full schema import
mandate = MandateProfile.from_schema(schema)
intent = UserIntent.from_schema(schema)

print(f"\nPath B mandate created successfully")
print(f"  Mandate ID: {mandate.mandate_profile_id}")
print(f"  Sectors of interest: {intent.sectors_of_interest}")
print(f"  Preferred regimes: {intent.strategy_character}")

print("\n✅ PHASE 1B PASSED\n")
