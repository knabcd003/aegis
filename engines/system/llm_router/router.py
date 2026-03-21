"""
Multi-Provider Config-Driven Router.

Reads from `config/llm_providers.yaml` to determine available models, roles, 
and fallback chains. Enforces that every role's routing pathway terminates in 
an unlimited-quota provider to prevent total system stalls.
"""
import copy
import fnmatch
from dataclasses import dataclass
from typing import Dict, Any, List, Optional
import yaml

from engines.system.llm_router.quota_tracker import QuotaTracker


@dataclass
class RoutingDecision:
    provider_id: str
    model_id: str
    was_primary: bool
    fallback_reason: str
    session_quality: str      # "nominal", "degraded", "severely_degraded"
    quota_state: Dict[str, Any]


class ProviderRouter:
    def __init__(self, config_path: str = "config/llm_providers.yaml", quota_tracker: Optional[QuotaTracker] = None):
        self.config_path = config_path
        self._load_config()
        self.quota = quota_tracker or QuotaTracker(providers=self.providers)

    def _load_config(self) -> None:
        """Load and validate the YAML config."""
        with open(self.config_path, "r") as f:
            self.config = yaml.safe_load(f)

        # Build lookup tables
        self.providers = {p["id"]: p for p in self.config.get("providers", [])}
        self.roles = self.config.get("role_assignments", {})
        self.settings = self.config.get("settings", {})

        self.context_threshold = self.settings.get("context_size_threshold_tokens", 50000)
        self.context_override = self.settings.get("context_override_provider", "gemini-2.5-flash")
        self.exclude_patterns = self.settings.get("exclude_providers", [])
        self.severe_depth = self.settings.get("severely_degraded_fallback_depth", 2)

        self._validate_fallback_chains()

    def _validate_fallback_chains(self) -> None:
        """
        Critical safety check: Ensure that every role has at least one
        reachable provider in its chain (primary or fallback) with NO rpd limit.
        Otherwise, the entire pipeline can stall.
        Also validates that no explicitly excluded provider is present in the chain.
        """
        for role, assignment in self.roles.items():
            chain = [assignment["primary"]] + assignment.get("fallback_chain", [])
            has_unlimited = False
            
            for provider_id in chain:
                if self._is_excluded(provider_id):
                    raise ValueError(
                        f"Configuration Error: Role '{role}' includes excluded provider "
                        f"'{provider_id}' in its fallback chain. An excluded provider "
                        f"must not be relied upon for routing."
                    )
                
                # If provider doesn't exist, we skip logic checks (could be local stub)
                if provider_id not in self.providers:
                    continue
                    
                limit = self.providers[provider_id].get("limits", {}).get("rpd")
                if limit is None:
                    has_unlimited = True
                    # Don't break here, we need to check the rest of the chain for excluded providers
                    
            if not has_unlimited:
                raise ValueError(
                    f"Configuration Error: Role '{role}' has no unlimited provider "
                    f"in its fallback chain. This can cause pipeline stalls."
                )

    def _is_excluded(self, provider_id: str) -> bool:
        """Check if provider is manually excluded in config or settings."""
        if provider_id not in self.providers:
            # If it's not in providers but matches an exclude pattern, it's excluded
            for pattern in self.exclude_patterns:
                if fnmatch.fnmatch(provider_id, pattern):
                    return True
            return False
            
        if self.providers[provider_id].get("exclude", False):
            return True
        for pattern in self.exclude_patterns:
            if fnmatch.fnmatch(provider_id, pattern):
                return True
        return False

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
        if estimated_tokens > self.context_threshold:
            if not self._is_excluded(self.context_override) and not self.quota.is_exhausted(self.context_override):
                p, m = self._split_provider_model(self.context_override)
                return RoutingDecision(
                    provider_id=p, model_id=m, was_primary=False,
                    fallback_reason="context_size_override",
                    session_quality=self._evaluate_quality(role, self.context_override, 1),
                    quota_state=quota_state
                )

        # 2. Lookup role
        assignment = self.roles.get(role)
        if not assignment:
            # Fallback for completely unknown roles
            return self._build_terminal_fallback(role, quota_state)

        target = assignment["primary"]
        fallback_chain = assignment.get("fallback_chain", [])

        # 3. Check Quota & Walk Chain
        was_primary = True
        fallback_reason = "none"
        chosen_model = target
        depth_walked = 0

        # Primary check
        if self._is_excluded(target) or self.quota.is_exhausted(target):
            was_primary = False
            fallback_reason = "quota_exhausted" if not self._is_excluded(target) else "provider_excluded"
            chosen_model = None

            # Walk fallbacks
            for i, fallback_id in enumerate(fallback_chain):
                if not self._is_excluded(fallback_id) and not self.quota.is_exhausted(fallback_id):
                    chosen_model = fallback_id
                    depth_walked = i + 1
                    break

        if not chosen_model:
            # Absolute worst case (should be caught by validate_fallback_chains but just in case)
            return self._build_terminal_fallback(role, quota_state)

        # 4. Evaluate Session Quality
        quality = self._evaluate_quality(role, chosen_model, depth_walked)

        # Build response
        p, m = self._split_provider_model(chosen_model)
        return RoutingDecision(
            provider_id=p, model_id=m,
            was_primary=was_primary,
            fallback_reason=fallback_reason,
            session_quality=quality,
            quota_state=quota_state,
        )

    def _build_terminal_fallback(self, role: str, quota_state: Dict[str, Any]) -> RoutingDecision:
        """When everything fails or config is missing, return safe default."""
        fallback = "local/qwen3:8b"
        p, m = self._split_provider_model(fallback)
        return RoutingDecision(
            provider_id=p, model_id=m,
            was_primary=False,
            fallback_reason="terminal_fallback",
            session_quality="severely_degraded" if self.roles.get(role, {}).get("is_critical", False) else "nominal",
            quota_state=quota_state
        )

    def _evaluate_quality(self, role: str, chosen_model: str, depth_walked: int) -> str:
        """
        Evaluate degradation state based on config.
        If role is not critical, always nominal.
        If depth == 0, nominal.
        If depth >= severely_degraded_fallback_depth OR the provider explicitly
        defines critical_fallback_depth and depth >= that, severely_degraded.
        Enforces that per-provider critical_fallback_depth cannot be higher 
        than the global severely_degraded_fallback_depth ceiling.
        """
        assignment = self.roles.get(role, {})
        if not assignment.get("is_critical", False):
            return "nominal"
            
        if depth_walked == 0:
            return "nominal"
            
        provider_cfg = self.providers.get(chosen_model, {})
        # Global ceiling is self.severe_depth. Use minimum of global and per-provider setting.
        crit_depth = min(
            self.severe_depth,
            provider_cfg.get("critical_fallback_depth", self.severe_depth)
        )

        if depth_walked >= crit_depth:
            return "severely_degraded"
            
        return "degraded"

