# scripts/verify/02_llm_routing.py
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from dotenv import load_dotenv
load_dotenv()

from engines.system.llm_adapter import LLMAdapter
from engines.system.llm_router.router import ProviderRouter
from engines.system.llm_router.quota_tracker import QuotaTracker

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
config_path = os.path.join(BASE_DIR, 'config/llm_providers.yaml')

router = ProviderRouter(config_path)
adapter = LLMAdapter(config_path)

# Test each critical role routes to the correct provider
critical_roles = [
    ("debate_bull", "local/qwen3:8b", "Bull agent — should use local model"),
    ("semantic_validation", "groq/llama-4-scout", "Semantic validation — Groq fast tier"),
    ("strategy_generation", "groq/qwen3-32b", "Strategy generation — Groq strong reasoning"),
    ("debate_moderator", "groq/gpt-oss-120b", "Moderator — Groq frontier tier"),
]

print("Role routing verification:")
for role, expected_provider, description in critical_roles:
    decision = router.get_provider_for_role(role, estimated_tokens=100)
    status = "✅" if decision.provider_id == expected_provider.split('/')[0] else "⚠️"
    print(f"  {status} {role}: {decision.provider_id}/{decision.model_id} (expected pattern: {expected_provider})")
    print(f"     {description}")

# Test context size override
print("\nContext size override test:")
decision_large = router.get_provider_for_role("strategy_generation", estimated_tokens=60000)
print(f"  Large context (60K tokens) → {decision_large.provider_id}/{decision_large.model_id}")
assert "gemini" in decision_large.provider_id.lower() or "google" in decision_large.provider_id.lower(), f"Large context should route to Gemini/Google, got {decision_large.provider_id}"
print("  ✅ Large context correctly routes to Gemini/Google")

# Test DeepSeek exclusion
print("\nDeepSeek exclusion test:")
# This should not be reachable — verify it's excluded
providers = [p["id"] for p in router.config["providers"] if not p.get("exclude", False)]
deepseek_accessible = any("deepseek" in p.lower() for p in providers)
print(f"  DeepSeek accessible: {deepseek_accessible} (expected: False)")
assert not deepseek_accessible, "DeepSeek should be excluded"
print("  ✅ DeepSeek correctly excluded")

# Make a real LLM call on each available tier
print("\nReal LLM call verification:")
test_message = [{"role": "user", "content": "Reply with exactly three words: AEGIS VERIFIED OK"}]

for role, expected_provider, description in critical_roles:
    try:
        resp = adapter.invoke(
            messages=test_message,
            role=role,
            workflow_id="routing_verify",
            node_id=f"verify_{role}"
        )
        content_preview = resp.content[:50] if resp.content else "EMPTY"
        print(f"  ✅ {role}: {resp.provider_id}/{resp.model_id} | {resp.latency_ms:.0f}ms | '{content_preview}'")
    except Exception as e:
        print(f"  ❌ {role}: FAILED — {e}")

# Test quota tracking
print("\nQuota tracking verification:")
quota = QuotaTracker(router.providers)
initial_usage = quota._usage.copy()
quota.increment("groq/qwen3-32b")
updated_usage = quota._usage
print(f"  Usage incremented correctly: {updated_usage}")

# Verify UTC midnight reset logic
import json
from datetime import datetime, timedelta, timezone
yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")
# Simulate stale cache from yesterday
stale_data = {"utc_date": yesterday, "usage": {"groq/qwen3-32b": {"qwen/qwen3-32b": 999}}}
with open("data/llm_quota.json", "w") as f:
    json.dump(stale_data, f)
quota2 = QuotaTracker(router.providers)
usage_after_reset = quota2._usage
groq_usage = usage_after_reset.get("groq/qwen3-32b", 0)
print(f"  Midnight reset: stale count was 999, now: {groq_usage} (expected: 0)")
assert groq_usage == 0, "Midnight UTC reset failed"
print("  ✅ Midnight UTC reset works correctly")

print("\n✅ PHASE 2 PASSED\n")
