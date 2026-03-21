"""
Tests for Phase 5.2 Multi-Provider Router & Quota Tracker.
"""
import os
import tempfile
import json
from datetime import datetime, timedelta
import yaml
import pytest

from engines.system.llm_router.quota_tracker import QuotaTracker
from engines.system.llm_router.router import ProviderRouter, RoutingDecision

@pytest.fixture
def mock_config(tmp_path):
    config = {
        "providers": [
            {"id": "local/qwen3:8b", "tier": 0, "limits": {"rpd": None}},
            {"id": "groq/llama-4-scout", "tier": 1, "limits": {"rpd": 1000}},
            {"id": "groq/qwen3-32b", "tier": 2, "limits": {"rpd": 1000}},
            {"id": "groq/kimi-k2", "tier": 3, "limits": {"rpd": 1000}},
            {"id": "groq/gpt-oss-120b", "tier": 4, "limits": {"rpd": 1000}},
            {"id": "gemini-2.5-flash", "tier": 5, "limits": {"rpd": 500}},
            {"id": "openrouter/:free", "tier": 6, "limits": {"rpd": 200}},
            {"id": "claude-sonnet-4-6", "tier": 7, "limits": {"rpd": None}, "critical_fallback_depth": 3},
            {"id": "deepseek/v2", "tier": 8, "limits": {"rpd": 1000}}
        ],
        "role_assignments": {
            "strategy_generation": {
                "primary": "claude-sonnet-4-6",
                "fallback_chain": ["gemini-2.5-flash", "groq/gpt-oss-120b", "groq/kimi-k2", "groq/qwen3-32b", "groq/llama-4-scout", "openrouter/:free", "local/qwen3:8b"],
                "is_critical": True
            },
            "fast_eval": {
                "primary": "groq/llama-4-scout",
                "fallback_chain": ["local/qwen3:8b"],
                "is_critical": False
            },
            "schema_routing": {
                "primary": "local/qwen3:8b",
                "fallback_chain": [],
                "is_critical": False
            }
        },
        "settings": {
            "context_size_threshold_tokens": 50000,
            "context_override_provider": "gemini-2.5-flash",
            "exclude_providers": ["deepseek/*"],
            "severely_degraded_fallback_depth": 2
        }
    }
    path = tmp_path / "test_llm_providers.yaml"
    with open(path, "w") as f:
        yaml.dump(config, f)
    return str(path)


@pytest.fixture
def quota_providers(mock_config):
    with open(mock_config, "r") as f:
        config = yaml.safe_load(f)
    return {p["id"]: p for p in config["providers"]}


# ═══════════════════════════════════════════════════════════════════════════════
# Quota Tracker Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestQuotaTracker:
    @pytest.fixture
    def tracker(self, tmp_path, quota_providers):
        return QuotaTracker(providers=quota_providers, persist_path=str(tmp_path / "quota.json"))

    def test_initial_state(self, tracker):
        assert tracker.get_quota("groq/llama-4-scout") == 0
        assert tracker.is_exhausted("groq/llama-4-scout") is False
        assert tracker._utc_date == datetime.utcnow().date().isoformat()

    def test_increment(self, tracker):
        tracker.increment("groq/llama-4-scout", 50)
        assert tracker.get_quota("groq/llama-4-scout") == 50

    def test_exhaustion(self, tracker):
        tracker.increment("gemini-2.5-flash", 500)
        assert tracker.is_exhausted("gemini-2.5-flash") is True

    def test_midnight_reset_on_load(self, tmp_path, quota_providers):
        path = str(tmp_path / "quota.json")
        yesterday = (datetime.utcnow() - timedelta(days=1)).date().isoformat()
        with open(path, "w") as f:
            json.dump({
                "utc_date": yesterday,
                "usage": {"gemini-2.5-flash": 500}
            }, f)
            
        tracker = QuotaTracker(providers=quota_providers, persist_path=path)
        assert tracker.get_quota("gemini-2.5-flash") == 0
        assert tracker.is_exhausted("gemini-2.5-flash") is False
        assert tracker._utc_date == datetime.utcnow().date().isoformat()

    def test_midnight_reset_on_increment_simulate_time_passing(self, tmp_path, quota_providers):
        tracker = QuotaTracker(providers=quota_providers, persist_path=str(tmp_path / "quota.json"))
        tracker.increment("gemini-2.5-flash", 500)
        assert tracker.is_exhausted("gemini-2.5-flash") is True
        
        # Simulate time passing
        tracker._utc_date = (datetime.utcnow() - timedelta(days=1)).date().isoformat()
        
        # The next call should reset it
        assert tracker.is_exhausted("gemini-2.5-flash") is False
        assert tracker.get_quota("gemini-2.5-flash") == 0

    def test_persistence_roundtrip(self, tmp_path, quota_providers):
        path = str(tmp_path / "quota.json")
        t1 = QuotaTracker(providers=quota_providers, persist_path=path)
        t1.increment("groq/kimi-k2", 150)
        
        t2 = QuotaTracker(providers=quota_providers, persist_path=path)
        assert t2.get_quota("groq/kimi-k2") == 150


# ═══════════════════════════════════════════════════════════════════════════════
# Provider Router Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestProviderRouter:
    @pytest.fixture
    def router(self, tmp_path, mock_config, quota_providers):
        qt = QuotaTracker(providers=quota_providers, persist_path=str(tmp_path / "quota.json"))
        return ProviderRouter(config_path=mock_config, quota_tracker=qt)

    def test_basic_routing_nominal(self, router):
        decision = router.get_provider_for_role("strategy_generation")
        assert decision.was_primary is True
        assert decision.provider_id == "anthropic"
        assert decision.model_id == "claude-sonnet-4-6"
        assert decision.session_quality == "nominal"
        assert decision.fallback_reason == "none"

    def test_large_context_override(self, router):
        # Even if role is schema_routing (local), large context goes to Gemini flash
        decision = router.get_provider_for_role("schema_routing", estimated_tokens=60_000)
        assert decision.was_primary is False
        assert decision.provider_id == "google"
        assert decision.model_id == "gemini-2.5-flash"
        assert decision.fallback_reason == "context_size_override"

    def test_large_context_gemini_exhausted(self, router):
        # If gemini is exhausted, it falls back to normal routing
        router.quota.increment("gemini-2.5-flash", 500)
        decision = router.get_provider_for_role("strategy_generation", estimated_tokens=60_000)
        assert decision.was_primary is True  # normal routing took over
        assert decision.model_id == "claude-sonnet-4-6"

    def test_fallback_chain_trigger(self, router):
        # Exhaust Claude - Wait, claude has None limit here, we should just test Gemini exhaustion to GPT
        router.quota.increment("claude-sonnet-4-6", 200) # Since it's unlimited, this doesn't exhaust it. Let's make it exhausted by removing it for test or just exhausting Gemini.
        
        # Let's override claude's limit temporarily for the test to trigger fallback
        router.quota.providers["claude-sonnet-4-6"]["limits"]["rpd"] = 200
        router.quota.increment("claude-sonnet-4-6", 200)

        decision = router.get_provider_for_role("strategy_generation")
        
        # Next in chain after claude is gemini
        assert decision.was_primary is False
        assert decision.fallback_reason == "quota_exhausted"
        assert decision.provider_id == "google"
        assert decision.model_id == "gemini-2.5-flash"
        # Strategy Gen is critical; 1 step fallback is "degraded" (since crit fallback depth is 3)
        assert decision.session_quality == "degraded"

    def test_fallback_chain_deep(self, router):
        router.quota.providers["claude-sonnet-4-6"]["limits"]["rpd"] = 200
        router.quota.increment("claude-sonnet-4-6", 200)
        router.quota.increment("gemini-2.5-flash", 500)
        router.quota.increment("groq/gpt-oss-120b", 1000)
        router.quota.increment("groq/kimi-k2", 1000)
        router.quota.increment("groq/qwen3-32b", 1000)
        router.quota.increment("groq/llama-4-scout", 1000)
        
        # Everything exhausted except openrouter and local
        decision = router.get_provider_for_role("strategy_generation")
        assert decision.was_primary is False
        assert decision.provider_id == "openrouter"
        assert decision.model_id == ":free"
        
        # Target was critical; fallback deep to openrouter is "severely_degraded"
        # depth is 6 steps down.
        assert decision.session_quality == "severely_degraded"

    def test_non_critical_role_quality(self, router):
        # Exhaust fast_eval (groq/llama-4-scout)
        router.quota.increment("groq/llama-4-scout", 1000)
        decision = router.get_provider_for_role("fast_eval")
        
        assert decision.was_primary is False
        assert decision.provider_id == "local" # next in fast_eval chain
        assert decision.model_id == "qwen3:8b"
        
        # Because fast_eval is non-critical, quality remains nominal
        assert decision.session_quality == "nominal"

    def test_exclude_provider(self, router):
        # We mapped strategy_generation to claude.
        # But let's verify deepseek/v2 is excluded entirely if we try to route to it.
        # Deepseek is in providers list and setting exclude_providers=["deepseek/*"].
        assert router._is_excluded("deepseek/v2") is True

    def test_validation_fails_no_unlimited(self, tmp_path):
        config = {
            "providers": [{"id": "groq", "limits": {"rpd": 1000}}],
            "role_assignments": {
                "role1": {"primary": "groq", "fallback_chain": []}
            }
        }
        path = tmp_path / "bad.yaml"
        with open(path, "w") as f:
            yaml.dump(config, f)
            
        with pytest.raises(ValueError, match="no unlimited provider"):
            ProviderRouter(config_path=str(path))
