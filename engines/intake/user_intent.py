"""
UserIntent — soft preferences that guide strategy generation.

Mutable (not frozen). Captures what the user wants to explore,
distinct from MandateProfile which captures absolute limits.

Two factory methods:
  - from_path_a(): takes raw desire text, sets has_preference flag
  - from_schema(): populates all fields from validated Path B JSON
"""
from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from datetime import datetime


# Sentinel value for "no preference"
NO_PREFERENCE = "no specific preference — optimize for risk profile"


@dataclass
class MacroView:
    """A stated macro thesis from the user."""
    view: str          # e.g. "Rate cuts imminent"
    conviction: str    # "low" | "medium" | "high"
    timeframe: str     # "near-term" | "medium-term" | "long-term"


@dataclass
class UserIntent:
    raw_desire: str                                # preserved verbatim always
    has_preference: bool                           # True if raw_desire != NO_PREFERENCE
    universe_tags: List[str] = field(default_factory=list)
    strategy_character: str = ""                   # e.g. "momentum", "mean-reversion"
    sectors_of_interest: List[str] = field(default_factory=list)
    sectors_to_avoid: List[str] = field(default_factory=list)
    market_cap_range: Optional[Tuple[str, str]] = None  # ("small", "mid") etc.
    catalyst_types: List[str] = field(default_factory=list)
    macro_views: List[MacroView] = field(default_factory=list)
    exclusions: List[str] = field(default_factory=list)
    notes: Optional[str] = None
    intake_path: str = "A"                         # "A" | "B"
    intake_schema_version: str = "v7.0"

    # ── Path A Factory ────────────────────────────────────────────────────

    @classmethod
    def from_path_a(cls, raw_desire: str) -> "UserIntent":
        """
        Factory for Path A (simple UI).

        The only input is the free-text desire field.
        has_preference is simply: raw_desire != NO_PREFERENCE.
        Everything else stays empty — the Builder explores freely.
        """
        desire = (raw_desire or "").strip()
        if not desire:
            desire = NO_PREFERENCE

        return cls(
            raw_desire=desire,
            has_preference=(desire != NO_PREFERENCE),
            intake_path="A",
        )

    # ── Path B Factory ────────────────────────────────────────────────────

    @classmethod
    def from_schema(cls, schema: dict) -> "UserIntent":
        """
        Factory for Path B (comprehensive JSON schema import).

        Includes normalization for LLM-produced inconsistencies.
        """
        required = schema.get("required", {})
        universe = schema.get("universe", {})
        strategy = schema.get("strategy_character", {})
        constraints = schema.get("constraints", {})

        raw_desire = _norm_str(required.get("raw_desire", ""))
        if not raw_desire:
            raw_desire = NO_PREFERENCE

        # Parse macro views
        raw_macro = schema.get("macro_views", [])
        macro_views = []
        for mv in raw_macro:
            if isinstance(mv, dict):
                macro_views.append(MacroView(
                    view=_norm_str(mv.get("view", "")),
                    conviction=_norm_str(mv.get("conviction", "medium")),
                    timeframe=_norm_str(mv.get("timeframe", "medium-term")),
                ))

        # Parse market cap range
        market_cap = universe.get("market_cap_range")
        if isinstance(market_cap, list) and len(market_cap) == 2:
            market_cap_range = (str(market_cap[0]).strip(), str(market_cap[1]).strip())
        elif isinstance(market_cap, str) and market_cap.strip():
            market_cap_range = (market_cap.strip(), market_cap.strip())
        else:
            market_cap_range = None

        return cls(
            raw_desire=raw_desire,
            has_preference=(raw_desire != NO_PREFERENCE),
            universe_tags=_norm_list(universe.get("asset_classes", [])),
            strategy_character=_norm_str(
                strategy.get("preferred_regimes", [""])[0]
                if isinstance(strategy.get("preferred_regimes"), list) and strategy.get("preferred_regimes")
                else strategy.get("preferred_regimes", "")
            ),
            sectors_of_interest=_norm_list(universe.get("sectors_of_interest", [])),
            sectors_to_avoid=_norm_list(universe.get("sectors_to_avoid", [])),
            market_cap_range=market_cap_range,
            catalyst_types=_norm_list(strategy.get("catalyst_types", [])),
            macro_views=macro_views,
            exclusions=_norm_list(constraints.get("esg_exclusions", []))
                       + _norm_list(universe.get("exclude_tickers", [])),
            notes=_norm_str(schema.get("notes", "")) or None,
            intake_path="B",
            intake_schema_version=schema.get("_schema_version", "v7.0"),
        )

    # ── Builder Context ───────────────────────────────────────────────────

    def to_builder_context(self) -> str:
        """
        Structured plain-text for prompt injection into the Builder.
        Produces the desire and soft preferences in prompt-ready format.
        """
        lines = ["=== USER INTENT (soft preferences — guide generation) ==="]
        lines.append(f"User desire: {self.raw_desire}")

        if not self.has_preference:
            lines.append("No specific preference stated — explore freely within constraints.")
            return "\n".join(lines)

        if self.strategy_character:
            lines.append(f"Strategy character: {self.strategy_character}")

        if self.sectors_of_interest:
            lines.append(f"Sectors of interest: {', '.join(self.sectors_of_interest)}")

        if self.sectors_to_avoid:
            lines.append(f"Sectors to avoid: {', '.join(self.sectors_to_avoid)}")

        if self.catalyst_types:
            lines.append(f"Catalyst types: {', '.join(self.catalyst_types)}")

        if self.market_cap_range:
            lines.append(f"Market cap range: {self.market_cap_range[0]} – {self.market_cap_range[1]}")

        if self.universe_tags:
            lines.append(f"Universe tags: {', '.join(self.universe_tags)}")

        if self.macro_views:
            views = [f"{mv.view} ({mv.conviction} conviction, {mv.timeframe})" for mv in self.macro_views]
            lines.append(f"Macro views: {'; '.join(views)}")

        if self.exclusions:
            lines.append(f"Exclusions: {', '.join(self.exclusions)}")

        if self.notes:
            lines.append(f"Notes: {self.notes}")

        lines.append("")
        lines.append("These preferences guide strategy exploration but are NOT hard constraints.")
        return "\n".join(lines)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _norm_str(value) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _norm_list(value) -> List[str]:
    if not isinstance(value, list):
        return []
    return [str(v).strip() for v in value if v is not None and str(v).strip()]
