"""
Tests for Phase 5.2 Multi-Provider Router & Quota Tracker.
"""
import os
import tempfile
import json
from datetime import datetime, timedelta
import pytest

from engines.system.llm_router.quota_tracker import QuotaTracker, DEFAULT_LIMITS
from engines.system.llm_router.router import ProviderRouter, RoutingDecision


# ═══════════════════════════════════════════════════════════════════════════════
# Quota Tracker Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestQuotaTracker:
    @pytest.fixture
    def tracker(self, tmp_path):
        return QuotaTracker(persist_path=str(tmp_path / "quota.json"))

    def test_initial_state(self, tracker):
        assert tracker.get_quota("groq/llama-4-scout") == 0
        assert tracker.is_exhausted("groq/llama-4-scout") is False
        assert tracker._utc_date == datetime.utcnow().date().isoformat()

    def test_increment(self, tracker):
        tracker.increment("groq/llama-4-scout", 50)
        assert tracker.get_quota("groq/llama-4-scout") == 50

    def test_exhaustion(self, tracker):
        limit = DEFAULT_LIMITS["gemini-2.5-flash"]
        tracker.increment("gemini-2.5-flash", limit)
        assert tracker.is_exhausted("gemini-2.5-flash") is True

    def test_midnight_reset_on_load(self, tmp_path):
        path = str(tmp_path / "quota.json")
        yesterday = (datetime.utcnow() - timedelta(days=1)).date().isoformat()
        with open(path, "w") as f:
            json.dump({
                "utc_date": yesterday,
                "usage": {"gemini-2.5-flash": 500}
            }, f)
            
        tracker = QuotaTracker(persist_path=path)
        assert tracker.get_quota("gemini-2.5-flash") == 0
        assert tracker.is_exhausted("gemini-2.5-flash") is False
        assert tracker._utc_date == datetime.utcnow().date().isoformat()

    def test_midnight_reset_on_increment_simulate_time_passing(self, tmp_path):
        tracker = QuotaTracker(persist_path=str(tmp_path / "quota.json"))
        tracker.increment("gemini-2.5-flash", 500)
        assert tracker.is_exhausted("gemini-2.5-flash") is True
        
        # Simulate time passing
        tracker._utc_date = (datetime.utcnow() - timedelta(days=1)).date().isoformat()
        
        # The next call should reset it
        assert tracker.is_exhausted("gemini-2.5-flash") is False
        assert tracker.get_quota("gemini-2.5-flash") == 0

    def test_persistence_roundtrip(self, tmp_path):
        path = str(tmp_path / "quota.json")
        t1 = QuotaTracker(persist_path=path)
        t1.increment("groq/kimi-k2", 150)
        
        t2 = QuotaTracker(persist_path=path)
        assert t2.get_quota("groq/kimi-k2") == 150


# ═══════════════════════════════════════════════════════════════════════════════
# Provider Router Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestProviderRouter:
    @pytest.fixture
    def router(self, tmp_path):
        qt = QuotaTracker(persist_path=str(tmp_path / "quota.json"))
        return ProviderRouter(quota_tracker=qt)

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
        # Exhaust Claude
        router.quota.increment("claude-sonnet-4-6", 200)
        decision = router.get_provider_for_role("strategy_generation")
        
        # Next in chain after claude is gemini
        assert decision.was_primary is False
        assert decision.fallback_reason == "quota_exhausted"
        assert decision.provider_id == "google"
        assert decision.model_id == "gemini-2.5-flash"
        # Strategy Gen is critical; fallback to Gemini is "degraded"
        assert decision.session_quality == "degraded"

    def test_fallback_chain_deep(self, router):
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
        assert decision.session_quality == "severely_degraded"

    def test_non_critical_role_quality(self, router):
        # Exhaust fast_eval (groq/llama-4-scout)
        router.quota.increment("groq/llama-4-scout", 1000)
        decision = router.get_provider_for_role("fast_eval")
        
        assert decision.was_primary is False
        assert decision.provider_id == "openrouter" # next after llama-4-scout
        assert decision.model_id == ":free"
        
        # Because fast_eval is non-critical, quality remains nominal
        assert decision.session_quality == "nominal"
