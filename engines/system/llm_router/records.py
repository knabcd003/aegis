"""
Model Call Record for MLflow telemetry.

Captures all context about a routing decision and the execution of 
the call, including quality classification and quota state.
"""
from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class ModelCallRecord:
    role: str
    provider: str
    model: str
    
    # Context injected by the Router
    was_primary_model: bool
    fallback_reason: str
    session_quality: str      # "nominal", "degraded", "severely_degraded"
    quota_at_call: Dict[str, Any]
    
    # Telemetry filled by the caller after execution
    prompt_tokens: int = 0
    completion_tokens: int = 0
    latency_ms: float = 0.0
    success: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "role": self.role,
            "provider": self.provider,
            "model": self.model,
            "was_primary_model": self.was_primary_model,
            "fallback_reason": self.fallback_reason,
            "session_quality": self.session_quality,
            "quota_at_call": self.quota_at_call,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "latency_ms": self.latency_ms,
            "success": self.success,
        }
