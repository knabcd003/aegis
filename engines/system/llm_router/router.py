"""
Multi-Provider Static Router.

Determines the best provider based on static routing rules, context size, 
quota availability, and a fallback chain.

Tiers:
  Tier 0 — local/qwen3:8b (unlimited)
  Tier 1 — groq/llama-4-scout (1K RPD)
  Tier 2 — groq/qwen3-32b (1K RPD)
  Tier 3 — groq/kimi-k2 (1K RPD)
  Tier 4 — groq/gpt-oss-120b (1K RPD)
  Tier 5 — gemini-2.5-flash (500 RPD)
  Tier 6 — openrouter/:free (200 RPD shared)
  Tier 7 — claude-sonnet-4-6 ($20 budget)
"""
from dataclasses import dataclass
from typing import Dict, Any, List, Optional
from engines.system.llm_router.quota_tracker import QuotaTracker


CRITICAL_ROLES = {
    "strategy_generation",
    "debate_moderator", 
    "final_audit_score",
    "improvement_analyzer"
}


FALLBACK_CHAIN = [
    "claude-sonnet-4-6",     # Tier 7
    "gemini-2.5-flash",      # Tier 5
    "groq/gpt-oss-120b",     # Tier 4
    "groq/kimi-k2",          # Tier 3
    "groq/qwen3-32b",        # Tier 2
    "groq/llama-4-scout",    # Tier 1
    "openrouter/:free",      # Tier 6
    "local/qwen3:8b"         # Tier 0 (Terminal)
]


# Default assignments mapping a role to its primary intended model
PRIMARY_ROLES = {
    "strategy_generation": "claude-sonnet-4-6",
    "debate_moderator": "claude-sonnet-4-6",
    "final_audit_score": "claude-sonnet-4-6",
    "improvement_analyzer": "claude-sonnet-4-6",
    
    "debate_bull": "groq/gpt-oss-120b",
    "debate_bear": "groq/qwen3-32b",
    "fast_eval": "groq/llama-4-scout",
    "schema_routing": "local/qwen3:8b",
    "nli_prefilter": "local/qwen3:8b",
}


@dataclass
class RoutingDecision:
    provider_id: str
    model_id: str
    was_primary: bool
    fallback_reason: str
    session_quality: str      # "nominal", "degraded", "severely_degraded"
    quota_state: Dict[str, Any]


class ProviderRouter:
    def __init__(self, quota_tracker: Optional[QuotaTracker] = None):
        self.quota = quota_tracker or QuotaTracker()

    def _split_provider_model(self, full_id: str) -> tuple[str, str]:
        if "/" in full_id:
            return full_id.split("/", 1)
        if full_id.startswith("claude-"):
            return "anthropic", full_id
        if full_id.startswith("gemini-"):
            return "google", full_id
        return "unknown", full_id

    def get_provider_for_role(self, role: str, estimated_tokens: int = 0) -> RoutingDecision:
        quota_state = { "usage": dict(self.quota._usage) }
        
        # 1. Context Size Override
        if estimated_tokens > 50_000:
            if not self.quota.is_exhausted("gemini-2.5-flash"):
                p, m = self._split_provider_model("gemini-2.5-flash")
                return RoutingDecision(
                    provider_id=p, model_id=m, was_primary=False,
                    fallback_reason="context_size_override",
                    session_quality=self._evaluate_quality(role, "gemini-2.5-flash"),
                    quota_state=quota_state
                )

        # 2. Get Primary Target
        target = PRIMARY_ROLES.get(role, "local/qwen3:8b")
        
        # 3. Check Quota & Walk Chain if needed
        was_primary = True
        fallback_reason = "none"
        chosen_model = target

        if self.quota.is_exhausted(target):
            was_primary = False
            fallback_reason = "quota_exhausted"
            
            # Find target's position in the chain to walk down
            try:
                start_idx = FALLBACK_CHAIN.index(target) + 1
            except ValueError:
                start_idx = 0
            
            chosen_model = "local/qwen3:8b" # default fallback
            for model_id in FALLBACK_CHAIN[start_idx:]:
                if not self.quota.is_exhausted(model_id):
                    chosen_model = model_id
                    break

        # 4. Evaluate Session Quality
        quality = self._evaluate_quality(role, chosen_model)

        # Build response
        p, m = self._split_provider_model(chosen_model)
        return RoutingDecision(
            provider_id=p, model_id=m,
            was_primary=was_primary,
            fallback_reason=fallback_reason,
            session_quality=quality,
            quota_state=quota_state,
        )

    def _evaluate_quality(self, role: str, chosen_model: str) -> str:
        """
        Evaluate degradation state.
        
        Rules for Critical Roles:
        - No fallback -> "nominal"
        - Groq tier fallback -> "degraded"
        - OpenRouter or Local Qwen -> "severely_degraded"
        
        Rules for Non-Critical Roles:
        - Always "nominal" (by blueprint design, only critical fallbacks impact gate).
        """
        if role not in CRITICAL_ROLES:
            return "nominal"
            
        target = PRIMARY_ROLES.get(role, "local/qwen3:8b")
        if chosen_model == target:
            return "nominal"
            
        # It fell back from target
        if chosen_model.startswith("groq/") or chosen_model.startswith("gemini-"):
            return "degraded"
            
        if chosen_model in ("openrouter/:free", "local/qwen3:8b"):
            return "severely_degraded"
            
        # Safety net (e.g. somehow hit something else)
        return "degraded"
