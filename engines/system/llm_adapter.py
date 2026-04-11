import time
import logging
import litellm
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from litellm import RateLimitError

from engines.system.llm_router.router import ProviderRouter, RoutingDecision
from engines.system.llm_router.budget_tracker import ClaudeBudgetTracker
from api.routers.pipeline_events import broadcaster

logger = logging.getLogger(__name__)

class AllProvidersExhaustedError(Exception):
    def __init__(self, role: str, attempted: set):
        super().__init__(f"Total fallback exhaustion for role '{role}'. Attempted providers: {attempted}")
        self.role = role
        self.attempted = attempted

class QuotaExhaustedError(Exception):
    pass

@dataclass
class AdapterResponse:
    content: str
    provider_id: str
    model_id: str
    was_primary: bool
    fallback_reason: str
    session_quality: str
    prompt_tokens: int
    completion_tokens: int
    estimated_cost_usd: float
    latency_ms: float

    @classmethod
    def from_litellm(
        cls, 
        response: Any, 
        decision: RoutingDecision, 
        cost: float, 
        latency_ms: float
    ):
        usage = getattr(response, "usage", None)
        pt = usage.prompt_tokens if usage else 0
        ct = usage.completion_tokens if usage else 0
        
        content = ""
        if hasattr(response, "choices") and len(response.choices) > 0:
            content = response.choices[0].message.content or ""
            
        return cls(
            content=content,
            provider_id=decision.provider_id,
            model_id=decision.model_id,
            was_primary=decision.was_primary,
            fallback_reason=decision.fallback_reason,
            session_quality=decision.session_quality,
            prompt_tokens=pt,
            completion_tokens=ct,
            estimated_cost_usd=cost,
            latency_ms=latency_ms
        )

class LLMAdapter:
    def __init__(self, config_path: str = "config/llm_providers.yaml"):
        self.router = ProviderRouter(config_path=config_path)
        self.quota = self.router.quota
        self.claude_budget = ClaudeBudgetTracker()
        
        # Pull claude limits from settings
        self.settings = self.router.settings
        self.claude_budget_limit = self.settings.get("claude_budget_total_usd", 20.0)

    def invoke(
        self, 
        messages: List[Dict[str, str]], 
        role: str,
        workflow_id: str,
        node_id: str, 
        estimated_tokens: int = 0
    ) -> AdapterResponse:
        """
        Iteratively safely dispatches execution down the fallback chain.
        Ensures strict mathematical isolation of the Claude API budget.
        """
        attempted = set()
        
        while True:
            decision = self.router.get_provider_for_role(
                role, estimated_tokens, exclude=attempted
            )
            
            full_provider_id = f"{decision.provider_id}/{decision.model_id}"
            
            if full_provider_id in attempted or decision.model_id in attempted or decision.provider_id in attempted:
                raise AllProvidersExhaustedError(role, attempted)

            # Route gate condition check
            if not self.quota.can_accommodate(full_provider_id):
                attempted.add(full_provider_id)
                self.quota.mark_exhausted(full_provider_id)
                continue
                
            # Claude Explicit Financial Lock
            is_claude = "claude" in decision.model_id.lower() or "anthropic" in decision.provider_id.lower()
            if is_claude:
                if not self.claude_budget.can_accommodate(self.claude_budget_limit):
                    # Financially Exhausted
                    logger.warning("Claude Budget Limit Reached. Denying access securely.")
                    attempted.add(full_provider_id)
                    continue

            # Provider execution
            t_start = time.time()
            try:
                response = litellm.completion(
                    model=decision.litellm_model_string,
                    messages=messages,
                    num_retries=0, # Hardcoded zero strictly defers fallback routing safely back to Aegis
                    **decision.litellm_kwargs
                )
                
                latency_ms = (time.time() - t_start) * 1000.0
                
                # Accounting
                self.quota.increment(full_provider_id)
                
                usage = getattr(response, "usage", None)
                pt = usage.prompt_tokens if usage else 0
                ct = usage.completion_tokens if usage else 0
                
                # Calculate cost mapping
                provider_config = self.router.providers.get(full_provider_id, {})
                cost_per_1k = provider_config.get("cost_per_1k_tokens", 0.0)
                estimated_cost = ((pt + ct) / 1000.0) * cost_per_1k
                
                # Specifically update the disk DB for Claude
                if is_claude and estimated_cost > 0:
                    self.claude_budget.log_call(estimated_cost, pt, ct)
                
                # Broadcast the inference telemetry metrics
                broadcaster.broadcast_sync({
                    "event_id": f"evt_{int(time.time()*1000)}_{node_id}",
                    "workflow_id": workflow_id,
                    "timestamp": str(time.time()),
                    "event_type": "model_call",
                    "node_id": node_id,
                    "session_quality": decision.session_quality,
                    "payload": {
                        "provider_id": decision.provider_id,
                        "model_id": decision.model_id,
                        "latency_ms": latency_ms,
                        "cost": estimated_cost,
                        "tokens_total": pt + ct
                    }
                })
                
                return AdapterResponse.from_litellm(
                    response, decision, estimated_cost, latency_ms
                )
                
            except RateLimitError as e:
                logger.warning(f"RateLimitError on {full_provider_id}: {e}. Triggering iterative fallback.")
                self.quota.mark_exhausted(full_provider_id)
                attempted.add(full_provider_id)
                # Continue loop securely down the fallback tier
            except Exception as e:
                logger.error(f"Unexpected fault on {full_provider_id}: {e}.")
                attempted.add(full_provider_id)
