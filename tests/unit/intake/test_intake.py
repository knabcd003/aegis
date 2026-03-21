"""
Comprehensive tests for Phase 5.1 — Intake System.

Covers:
  - MandateProfile: immutability, Path A mapping, Path B schema, builder context
  - UserIntent: factories, has_preference, builder context
  - Contradiction detection: each rule, no false positives
  - Confirmation screen: structure, product boundary messaging
  - StrategyArchetypePool: register, persist, cosine similarity, exclusion context
"""
import os
import json
import pytest
import tempfile
from datetime import datetime

from engines.intake.mandate_profile import MandateProfile, _coerce_pct
from engines.intake.user_intent import UserIntent, MacroView, NO_PREFERENCE
from engines.intake.contradiction import detect_contradictions, Contradiction
from engines.intake.confirmation import build_confirmation
from engines.intake.archetype_pool import (
    StrategyArchetype,
    StrategyArchetypePool,
    STRATEGY_CATEGORIES,
)


# ═══════════════════════════════════════════════════════════════════════════════
# MandateProfile Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestMandateProfileImmutability:
    def test_frozen_raises_on_assignment(self):
        m = MandateProfile.from_path_a("conservative", "swing")
        with pytest.raises(AttributeError):
            m.risk_tolerance = "aggressive"

    def test_frozen_raises_on_drawdown_change(self):
        m = MandateProfile.from_path_a("moderate", "swing")
        with pytest.raises(AttributeError):
            m.max_drawdown_target = 0.99


class TestMandateProfilePathA:
    def test_conservative_thresholds(self):
        m = MandateProfile.from_path_a("conservative", "swing")
        assert m.max_drawdown_target == 0.10
        assert m.max_position_pct == 0.02
        assert m.stop_loss_range == (0.01, 0.03)
        assert m.leverage_permitted is False

    def test_moderate_thresholds(self):
        m = MandateProfile.from_path_a("moderate", "swing")
        assert m.max_drawdown_target == 0.15
        assert m.max_position_pct == 0.05
        assert m.stop_loss_range == (0.02, 0.05)

    def test_aggressive_thresholds(self):
        m = MandateProfile.from_path_a("aggressive", "position")
        assert m.max_drawdown_target == 0.35
        assert m.max_position_pct == 0.10
        assert m.stop_loss_range == (0.03, 0.08)
        assert m.leverage_permitted is True

    def test_day_horizon(self):
        m = MandateProfile.from_path_a("moderate", "day")
        assert m.holding_period_range == (0, 1)
        assert "equities" in m.allowed_asset_classes

    def test_swing_horizon(self):
        m = MandateProfile.from_path_a("moderate", "swing")
        assert m.holding_period_range == (3, 21)
        assert "options" in m.allowed_asset_classes

    def test_position_horizon(self):
        m = MandateProfile.from_path_a("moderate", "position")
        assert m.holding_period_range == (21, 120)
        assert "bonds" in m.allowed_asset_classes

    def test_case_insensitive_risk(self):
        m = MandateProfile.from_path_a("Conservative", "swing")
        assert m.risk_tolerance == "conservative"

    def test_whitespace_tolerance(self):
        m = MandateProfile.from_path_a("  moderate  ", "  swing  ")
        assert m.risk_tolerance == "moderate"

    def test_invalid_risk_raises(self):
        with pytest.raises(ValueError, match="Invalid risk_tolerance"):
            MandateProfile.from_path_a("yolo", "swing")

    def test_invalid_horizon_raises(self):
        with pytest.raises(ValueError, match="Invalid time_horizon"):
            MandateProfile.from_path_a("moderate", "weekly")

    def test_mandate_id_generated(self):
        m = MandateProfile.from_path_a("moderate", "swing")
        assert len(m.mandate_profile_id) > 0

    def test_schema_version_set(self):
        m = MandateProfile.from_path_a("moderate", "swing")
        assert m.schema_version == "v7.0"


class TestMandateProfilePathB:
    def _make_schema(self, **overrides):
        schema = {
            "_schema_version": "v7.0",
            "_path": "B",
            "required": {
                "risk_tolerance": "moderate",
                "max_drawdown_pct": 15,
                "time_horizon": "swing",
                "raw_desire": "momentum strategies",
            },
            "constraints": {
                "leverage": False,
                "max_single_position_pct": 5,
            },
        }
        for k, v in overrides.items():
            if "." in k:
                parts = k.split(".")
                d = schema
                for p in parts[:-1]:
                    d = d.setdefault(p, {})
                d[parts[-1]] = v
            else:
                schema[k] = v
        return schema

    def test_basic_schema_import(self):
        m = MandateProfile.from_schema(self._make_schema())
        assert m.risk_tolerance == "moderate"
        assert m.max_drawdown_target == 0.15

    def test_numeric_string_coercion(self):
        """LLM might produce "20" instead of 20."""
        m = MandateProfile.from_schema(
            self._make_schema(**{"required.max_drawdown_pct": "20"})
        )
        assert m.max_drawdown_target == 0.20

    def test_whole_number_pct_normalization(self):
        """20 → 0.20 (not 20.0)"""
        m = MandateProfile.from_schema(
            self._make_schema(**{"required.max_drawdown_pct": 20})
        )
        assert m.max_drawdown_target == 0.20

    def test_decimal_pct_passthrough(self):
        """0.15 stays 0.15"""
        m = MandateProfile.from_schema(
            self._make_schema(**{"required.max_drawdown_pct": 0.15})
        )
        assert m.max_drawdown_target == 0.15

    def test_case_normalization(self):
        """'Conservative' → 'conservative'"""
        m = MandateProfile.from_schema(
            self._make_schema(**{"required.risk_tolerance": "  Conservative  "})
        )
        assert m.risk_tolerance == "conservative"

    def test_unknown_risk_defaults_moderate(self):
        m = MandateProfile.from_schema(
            self._make_schema(**{"required.risk_tolerance": "super risky"})
        )
        assert m.risk_tolerance == "moderate"


class TestMandateBuilderContext:
    def test_builder_context_contains_constraints(self):
        m = MandateProfile.from_path_a("conservative", "swing")
        ctx = m.to_builder_context()
        assert "HARD CONSTRAINTS" in ctx
        assert "10%" in ctx
        assert "2%" in ctx
        assert "Leverage permitted: No" in ctx

    def test_builder_context_aggressive_shows_leverage(self):
        m = MandateProfile.from_path_a("aggressive", "swing")
        ctx = m.to_builder_context()
        assert "Leverage permitted: Yes" in ctx
        assert "35%" in ctx


class TestCoercePct:
    def test_whole_number(self):
        assert _coerce_pct(20) == 0.20

    def test_decimal(self):
        assert _coerce_pct(0.15) == 0.15

    def test_string_whole(self):
        assert _coerce_pct("20") == 0.20

    def test_string_decimal(self):
        assert _coerce_pct("0.15") == 0.15

    def test_none(self):
        assert _coerce_pct(None) == 0.0

    def test_invalid(self):
        assert _coerce_pct("not a number") == 0.0


# ═══════════════════════════════════════════════════════════════════════════════
# UserIntent Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestUserIntentPathA:
    def test_has_preference_true(self):
        i = UserIntent.from_path_a("risky biotech stocks")
        assert i.has_preference is True
        assert i.raw_desire == "risky biotech stocks"

    def test_has_preference_false_no_preference(self):
        i = UserIntent.from_path_a(NO_PREFERENCE)
        assert i.has_preference is False

    def test_empty_string_defaults(self):
        i = UserIntent.from_path_a("")
        assert i.has_preference is False
        assert i.raw_desire == NO_PREFERENCE

    def test_none_defaults(self):
        i = UserIntent.from_path_a(None)
        assert i.has_preference is False

    def test_intake_path_is_a(self):
        i = UserIntent.from_path_a("anything")
        assert i.intake_path == "A"


class TestUserIntentPathB:
    def _make_schema(self):
        return {
            "_schema_version": "v7.0",
            "_path": "B",
            "required": {"raw_desire": "Momentum in tech sector"},
            "universe": {
                "asset_classes": ["equities", "etfs"],
                "sectors_of_interest": ["technology", "AI"],
                "sectors_to_avoid": ["energy"],
                "exclude_tickers": ["TSLA"],
                "market_cap_range": ["mid", "large"],
            },
            "strategy_character": {
                "preferred_regimes": ["momentum"],
                "catalyst_types": ["earnings", "FDA"],
            },
            "macro_views": [
                {"view": "Rate cuts coming", "conviction": "high", "timeframe": "near-term"}
            ],
            "constraints": {
                "esg_exclusions": ["tobacco", "firearms"],
            },
            "notes": "Focus on US markets only",
        }

    def test_schema_import_desire(self):
        i = UserIntent.from_schema(self._make_schema())
        assert i.raw_desire == "Momentum in tech sector"
        assert i.has_preference is True

    def test_schema_import_sectors(self):
        i = UserIntent.from_schema(self._make_schema())
        assert "technology" in i.sectors_of_interest
        assert "energy" in i.sectors_to_avoid

    def test_schema_import_exclusions(self):
        i = UserIntent.from_schema(self._make_schema())
        assert "tobacco" in i.exclusions
        assert "TSLA" in i.exclusions

    def test_schema_import_macro_views(self):
        i = UserIntent.from_schema(self._make_schema())
        assert len(i.macro_views) == 1
        assert i.macro_views[0].view == "Rate cuts coming"

    def test_schema_import_market_cap(self):
        i = UserIntent.from_schema(self._make_schema())
        assert i.market_cap_range == ("mid", "large")

    def test_intake_path_is_b(self):
        i = UserIntent.from_schema(self._make_schema())
        assert i.intake_path == "B"

    def test_schema_import_notes(self):
        i = UserIntent.from_schema(self._make_schema())
        assert i.notes == "Focus on US markets only"


class TestUserIntentBuilderContext:
    def test_no_preference_context(self):
        i = UserIntent.from_path_a("")
        ctx = i.to_builder_context()
        assert "No specific preference" in ctx
        assert "explore freely" in ctx

    def test_preference_context_contains_desire(self):
        i = UserIntent.from_path_a("biotech momentum")
        ctx = i.to_builder_context()
        assert "biotech momentum" in ctx

    def test_schema_context_contains_sectors(self):
        schema = {
            "required": {"raw_desire": "tech momentum"},
            "universe": {"sectors_of_interest": ["technology"], "sectors_to_avoid": ["energy"]},
            "strategy_character": {},
            "constraints": {},
        }
        i = UserIntent.from_schema(schema)
        ctx = i.to_builder_context()
        assert "technology" in ctx
        assert "energy" in ctx


# ═══════════════════════════════════════════════════════════════════════════════
# Contradiction Detection Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestContradictionRule1:
    """Conservative drawdown + aggressive/speculative desire."""

    def test_fires_on_speculative_desire(self):
        m = MandateProfile.from_path_a("conservative", "swing")
        i = UserIntent.from_path_a("I want risky speculative stocks")
        contradictions = detect_contradictions(m, i)
        rule_ids = [c.rule_id for c in contradictions]
        assert "CONSERVATIVE_AGGRESSIVE_DESIRE" in rule_ids

    def test_no_fire_on_moderate_with_speculative(self):
        m = MandateProfile.from_path_a("moderate", "swing")
        i = UserIntent.from_path_a("I want risky speculative stocks")
        contradictions = detect_contradictions(m, i)
        rule_ids = [c.rule_id for c in contradictions]
        assert "CONSERVATIVE_AGGRESSIVE_DESIRE" not in rule_ids

    def test_no_fire_on_conservative_with_safe_desire(self):
        m = MandateProfile.from_path_a("conservative", "swing")
        i = UserIntent.from_path_a("dividend stocks for income")
        contradictions = detect_contradictions(m, i)
        rule_ids = [c.rule_id for c in contradictions]
        assert "CONSERVATIVE_AGGRESSIVE_DESIRE" not in rule_ids


class TestContradictionRule2:
    """Leverage + conservative risk tolerance."""

    def test_fires_on_leverage_conservative(self):
        # This can only happen via Path B where leverage is set explicitly
        schema = {
            "required": {"risk_tolerance": "conservative", "time_horizon": "swing"},
            "constraints": {"leverage": True},
        }
        m = MandateProfile.from_schema(schema)
        i = UserIntent.from_path_a("anything")
        contradictions = detect_contradictions(m, i)
        rule_ids = [c.rule_id for c in contradictions]
        assert "LEVERAGE_CONSERVATIVE" in rule_ids

    def test_no_fire_aggressive_leverage(self):
        m = MandateProfile.from_path_a("aggressive", "swing")
        i = UserIntent.from_path_a("anything")
        contradictions = detect_contradictions(m, i)
        rule_ids = [c.rule_id for c in contradictions]
        assert "LEVERAGE_CONSERVATIVE" not in rule_ids


class TestContradictionRule3:
    """Exclusion conflicts with sector interest."""

    def test_fires_on_overlap(self):
        m = MandateProfile.from_path_a("moderate", "swing")
        i = UserIntent(
            raw_desire="tech focus",
            has_preference=True,
            sectors_of_interest=["technology", "biotech"],
            exclusions=["biotech"],
        )
        contradictions = detect_contradictions(m, i)
        rule_ids = [c.rule_id for c in contradictions]
        assert "EXCLUSION_INTEREST_CONFLICT" in rule_ids

    def test_no_fire_no_overlap(self):
        m = MandateProfile.from_path_a("moderate", "swing")
        i = UserIntent(
            raw_desire="tech focus",
            has_preference=True,
            sectors_of_interest=["technology"],
            exclusions=["tobacco"],
        )
        contradictions = detect_contradictions(m, i)
        rule_ids = [c.rule_id for c in contradictions]
        assert "EXCLUSION_INTEREST_CONFLICT" not in rule_ids


class TestContradictionRule4:
    """Day trading + conservative drawdown."""

    def test_fires_on_day_conservative(self):
        m = MandateProfile.from_path_a("conservative", "day")
        i = UserIntent.from_path_a("anything")
        contradictions = detect_contradictions(m, i)
        rule_ids = [c.rule_id for c in contradictions]
        assert "DAY_TRADE_CONSERVATIVE" in rule_ids

    def test_no_fire_swing_conservative(self):
        m = MandateProfile.from_path_a("conservative", "swing")
        i = UserIntent.from_path_a("anything")
        contradictions = detect_contradictions(m, i)
        rule_ids = [c.rule_id for c in contradictions]
        assert "DAY_TRADE_CONSERVATIVE" not in rule_ids


class TestContradictionRule5:
    """Leverage + day trading + conservative."""

    def test_fires_on_all_three(self):
        schema = {
            "required": {"risk_tolerance": "conservative", "time_horizon": "day"},
            "constraints": {"leverage": True},
        }
        m = MandateProfile.from_schema(schema)
        i = UserIntent.from_path_a("anything")
        contradictions = detect_contradictions(m, i)
        rule_ids = [c.rule_id for c in contradictions]
        assert "LEVERAGED_DAY_CONSERVATIVE" in rule_ids


class TestNoFalsePositives:
    """A perfectly valid moderate swing mandate should produce zero contradictions."""

    def test_clean_moderate_swing(self):
        m = MandateProfile.from_path_a("moderate", "swing")
        i = UserIntent.from_path_a("momentum tech stocks")
        contradictions = detect_contradictions(m, i)
        assert len(contradictions) == 0


# ═══════════════════════════════════════════════════════════════════════════════
# Confirmation Screen Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestConfirmation:
    def test_structure(self):
        m = MandateProfile.from_path_a("moderate", "swing")
        i = UserIntent.from_path_a("tech stocks")
        conf = build_confirmation(m, i)
        assert "desire_summary" in conf
        assert "hard_constraints" in conf
        assert "contradictions" in conf
        assert "risk_warning" in conf

    def test_hard_constraints_values(self):
        m = MandateProfile.from_path_a("moderate", "swing")
        i = UserIntent.from_path_a("anything")
        conf = build_confirmation(m, i)
        hc = conf["hard_constraints"]
        assert hc["max_drawdown"] == "15%"
        assert hc["max_position_size"] == "5% per trade"

    def test_catalyst_product_boundary(self):
        m = MandateProfile.from_path_a("moderate", "swing")
        i = UserIntent.from_path_a("I want FDA catalyst stocks")
        conf = build_confirmation(m, i)
        assert conf["product_boundary"] is not None
        assert "post-catalyst" in conf["product_boundary"]

    def test_no_boundary_for_normal_desire(self):
        m = MandateProfile.from_path_a("moderate", "swing")
        i = UserIntent.from_path_a("tech momentum")
        conf = build_confirmation(m, i)
        assert conf["product_boundary"] is None

    def test_aggressive_risk_warning(self):
        m = MandateProfile.from_path_a("aggressive", "swing")
        i = UserIntent.from_path_a("anything")
        conf = build_confirmation(m, i)
        assert conf["risk_warning"] is not None
        assert "35%" in conf["risk_warning"]

    def test_no_risk_warning_for_conservative(self):
        m = MandateProfile.from_path_a("conservative", "swing")
        i = UserIntent.from_path_a("anything")
        conf = build_confirmation(m, i)
        assert conf["risk_warning"] is None


# ═══════════════════════════════════════════════════════════════════════════════
# StrategyArchetypePool Tests
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.fixture
def pool_path(tmp_path):
    return str(tmp_path / "test_pool.json")


@pytest.fixture
def pool(pool_path):
    return StrategyArchetypePool(persist_path=pool_path)


class TestArchetypeRegistration:
    def test_register_and_list(self, pool):
        a = StrategyArchetype(
            name="momentum-tech",
            category="momentum",
            feature_vector=[1.0, 0.0, 0.0, 0.0, 0.0],
            description="Momentum in tech sector",
        )
        pool.register(a)
        assert pool.count() == 1
        assert pool.list_all()[0].name == "momentum-tech"

    def test_get_by_name(self, pool):
        a = StrategyArchetype(
            name="mean-rev-energy",
            category="mean-reversion",
            feature_vector=[0.0, 1.0, 0.0, 0.0, 0.0],
            description="Mean reversion in energy",
        )
        pool.register(a)
        found = pool.get_by_name("mean-rev-energy")
        assert found is not None
        assert found.category == "mean-reversion"

    def test_get_by_name_missing(self, pool):
        assert pool.get_by_name("nonexistent") is None


class TestArchetypePersistence:
    def test_persist_and_reload(self, pool_path):
        pool1 = StrategyArchetypePool(persist_path=pool_path)
        pool1.register(StrategyArchetype(
            name="test-strat",
            category="momentum",
            feature_vector=[0.5, 0.5, 0.0],
            description="Test",
        ))
        assert pool1.count() == 1

        # Create new pool from same path — should load from JSON
        pool2 = StrategyArchetypePool(persist_path=pool_path)
        assert pool2.count() == 1
        assert pool2.list_all()[0].name == "test-strat"
        assert pool2.list_all()[0].feature_vector == [0.5, 0.5, 0.0]

    def test_feature_vector_survives_json_roundtrip(self, pool_path):
        """Ensure feature vectors stored as plain lists survive JSON roundtrip."""
        pool = StrategyArchetypePool(persist_path=pool_path)
        vec = [0.1, 0.2, 0.8, 0.0, 0.5]
        pool.register(StrategyArchetype(
            name="test",
            category="momentum",
            feature_vector=vec,
            description="Test",
        ))

        # Reload
        pool2 = StrategyArchetypePool(persist_path=pool_path)
        assert pool2.list_all()[0].feature_vector == vec


class TestCosineSimilarity:
    def test_identical_vectors(self, pool):
        sim = pool.compute_similarity([1.0, 0.0, 0.0], [1.0, 0.0, 0.0])
        assert abs(sim - 1.0) < 1e-6

    def test_orthogonal_vectors(self, pool):
        sim = pool.compute_similarity([1.0, 0.0, 0.0], [0.0, 1.0, 0.0])
        assert abs(sim) < 1e-6

    def test_opposite_vectors(self, pool):
        sim = pool.compute_similarity([1.0, 0.0], [-1.0, 0.0])
        assert abs(sim + 1.0) < 1e-6

    def test_zero_vector(self, pool):
        sim = pool.compute_similarity([0.0, 0.0], [1.0, 0.0])
        assert sim == 0.0

    def test_is_too_similar_true(self, pool):
        pool.register(StrategyArchetype(
            name="existing",
            category="momentum",
            feature_vector=[1.0, 0.0, 0.0],
            description="Exists",
        ))
        assert pool.is_too_similar([0.99, 0.01, 0.0], threshold=0.70) is True

    def test_is_too_similar_false(self, pool):
        pool.register(StrategyArchetype(
            name="existing",
            category="momentum",
            feature_vector=[1.0, 0.0, 0.0],
            description="Exists",
        ))
        assert pool.is_too_similar([0.0, 1.0, 0.0], threshold=0.70) is False


class TestExclusionContext:
    def test_empty_pool_context(self, pool):
        ctx = pool.get_exclusion_context()
        assert "No strategies have been promoted" in ctx
        assert "full freedom" in ctx

    def test_populated_pool_context(self, pool):
        pool.register(StrategyArchetype(
            name="momentum-tech",
            category="momentum",
            feature_vector=[1.0, 0.0, 0.0],
            description="Tech momentum",
        ))
        pool.register(StrategyArchetype(
            name="momentum-bio",
            category="momentum",
            feature_vector=[0.9, 0.1, 0.0],
            description="Bio momentum",
        ))

        ctx = pool.get_exclusion_context()
        assert "momentum-tech" in ctx
        assert "momentum-bio" in ctx
        assert "Underrepresented" in ctx
        assert "mean-reversion" in ctx.lower() or "mean-reversion" in ctx

    def test_overrepresented_flag(self, pool):
        for i in range(3):
            pool.register(StrategyArchetype(
                name=f"momentum-{i}",
                category="momentum",
                feature_vector=[1.0, 0.0, float(i)],
                description=f"Momentum {i}",
            ))
        ctx = pool.get_exclusion_context()
        assert "Overrepresented" in ctx
        assert "momentum" in ctx.lower()

    def test_find_most_similar(self, pool):
        pool.register(StrategyArchetype(
            name="existing",
            category="momentum",
            feature_vector=[1.0, 0.0, 0.0],
            description="Exists",
        ))
        result = pool.find_most_similar([0.9, 0.1, 0.0])
        assert result is not None
        archetype, sim = result
        assert archetype.name == "existing"
        assert sim > 0.9
