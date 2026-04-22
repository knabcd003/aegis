"""
Provider Setup Router — /api/setup

Endpoints:
  GET  /current-providers   — reads existing YAML + .env
  POST /validate-provider   — makes a real test call to a provider
  POST /save-provider       — writes provider to YAML, key to .env
  POST /validate-finnhub    — tests Finnhub API key with real AAPL quote
  GET  /readiness           — checks minimum viable pipeline config
"""
import os
import time
import yaml
import re
from typing import Optional, List, Dict, Any
from pathlib import Path

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

# ── Paths ────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
YAML_PATH = PROJECT_ROOT / "config" / "llm_providers.yaml"
ENV_PATH = PROJECT_ROOT / ".env"


# ── Request/Response Models ──────────────────────────────────────────────

class ProviderValidationRequest(BaseModel):
    provider_type: str       # "cloud" | "openai_compatible" | "ollama"
    provider_name: str       # "groq", "anthropic", "gemini", etc.
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model: str

class SaveProviderRequest(BaseModel):
    provider_id: str
    display_name: str
    provider_type: str
    provider_name: str
    model: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    daily_quota: Optional[int] = None
    cost_per_1k: float = 0.0

class FinnhubValidationRequest(BaseModel):
    api_key: str

class RemoveProviderRequest(BaseModel):
    provider_id: str


from api.services.user_profile import UserProfileService

# ── User Profile Helpers ──────────────────────────────────────────────────

def _load_yaml() -> dict:
    return UserProfileService().get_provider_config("default")

def _save_yaml(config: dict) -> None:
    UserProfileService().save_provider_config("default", config)

def _write_to_env(key: str, value: str) -> None:
    """We keep this name for compatibility in this file, but it saves to the DB."""
    # Convert env var name (e.g. GROQ_API_KEY) to service name (e.g. groq)
    # The frontend usually sends provider_name="groq", we will handle setting the key directly in the route,
    # but for compatibility where this is called:
    service = key.replace('_API_KEY', '').replace('_SECRET_KEY', '').lower()
    UserProfileService().set_api_key("default", service, value)

# ── LiteLLM Model String Builder ────────────────────────────────────────

def build_litellm_model_string(provider: str, model: str) -> str:
    prefixes = {
        "groq": "groq",
        "anthropic": "anthropic",
        "gemini": "gemini",
        "openrouter": "openrouter",
        "mistral": "mistral",
        "together": "together_ai",
    }
    prefix = prefixes.get(provider, provider)
    return f"{prefix}/{model}"


# ── Tier Inference ───────────────────────────────────────────────────────

def _infer_tier(provider_name: str) -> str:
    tier_map = {
        "ollama": "ollama",
        "groq": "groq_fast",
        "anthropic": "anthropic",
        "gemini": "gemini",
        "openrouter": "openrouter_free",
        "mistral": "mistral",
        "together": "together",
    }
    return tier_map.get(provider_name, "groq_fast")


# ── Role Assignment (THE SEAM) ──────────────────────────────────────────

TIER_ORDER = {
    "ollama": 0,
    "openrouter_free": 1,
    "groq_fast": 2,
    "groq_strong": 3,
    "groq_frontier": 4,
    "gemini": 5,
    "anthropic": 6,
}

def _assign_roles(providers: List[dict]) -> dict:
    """
    Maps available providers to pipeline roles.

    This function is the seam between user-facing setup and
    internal pipeline architecture. When pipelines become
    dynamically assembled, only this function changes.

    Current behavior: fixed role assignment based on provider
    capability tier. Strongest available model gets the most
    critical roles. Unlimited provider always gets terminal_fallback.
    """
    if not providers:
        return {}

    unlimited = [p for p in providers
                 if p.get("limits", {}).get("rpd") is None and not p.get("exclude", False)]
    limited = [p for p in providers
               if p.get("limits", {}).get("rpd") is not None and not p.get("exclude", False)]

    # Sort limited by tier (strongest first)
    limited.sort(
        key=lambda p: TIER_ORDER.get(p.get("tier", "groq_fast"), 2),
        reverse=True
    )

    assignments = {}

    # Terminal fallback must be unlimited
    if unlimited:
        fallback = unlimited[0]
        assignments["terminal_fallback"] = {
            "primary": fallback["id"],
            "fallback_chain": [],
            "is_critical": False
        }
        assignments["debate_bull"] = {
            "primary": fallback["id"],
            "fallback_chain": [],
            "is_critical": False
        }
        assignments["json_parsing"] = {
            "primary": fallback["id"],
            "fallback_chain": [],
            "is_critical": False
        }
        assignments["schema_routing"] = {
            "primary": fallback["id"],
            "fallback_chain": [],
            "is_critical": False
        }
        assignments["nli_prefilter"] = {
            "primary": fallback["id"],
            "fallback_chain": [],
            "is_critical": False
        }

    # Assign critical roles to strongest available limited provider
    if limited:
        strongest = limited[0]
        fallback_chain = (
            [p["id"] for p in limited[1:]] +
            [p["id"] for p in unlimited]
        )

        critical_roles = [
            "strategy_generation",
            "debate_moderator",
            "debate_bear",
            "improvement_analyzer",
            "final_audit_score",
        ]

        for role in critical_roles:
            assignments[role] = {
                "primary": strongest["id"],
                "fallback_chain": fallback_chain,
                "is_critical": True
            }

    # Assign supporting roles to next best provider
    if len(limited) >= 2:
        supporting = limited[1]
        supporting_roles = [
            "semantic_validation",
            "structured_extraction",
            "debate_compression",
        ]
        for role in supporting_roles:
            assignments[role] = {
                "primary": supporting["id"],
                "fallback_chain": (
                    [p["id"] for p in limited if p["id"] != supporting["id"]] +
                    [p["id"] for p in unlimited]
                ),
                "is_critical": False
            }

    # Large context always goes to Gemini if available
    gemini = next(
        (p for p in providers if "gemini" in p["id"].lower()),
        None
    )
    if gemini:
        assignments["large_context"] = {
            "primary": gemini["id"],
            "fallback_chain": [p["id"] for p in limited[:1]],
            "is_critical": False
        }

    return assignments


# ══════════════════════════════════════════════════════════════════════════
# ENDPOINTS
# ══════════════════════════════════════════════════════════════════════════

@router.get("/current-providers")
async def get_current_providers():
    """Read existing YAML + .env and return what's already configured."""
    config = _load_yaml()
    providers = config.get("providers", [])

    result = []
    for p in providers:
        provider_name = p["id"].split("/")[0]
        # Local ollama doesn't need a key
        if p.get("type") == "ollama":
            has_key = True
        else:
            has_key = bool(UserProfileService().get_api_key("default", provider_name))
            
        result.append({
            **p,
            "key_configured": has_key,
        })

    return {
        "providers": result,
        "role_assignments": config.get("role_assignments", {}),
        "has_finnhub": bool(UserProfileService().get_api_key("default", "finnhub")),
    }


@router.post("/validate-provider")
async def validate_provider(body: ProviderValidationRequest):
    """Makes a real test call to the provider. No mocking."""
    import litellm

    start = time.time()

    try:
        if body.provider_type == "ollama":
            import requests as req_lib
            r = req_lib.post(
                "http://localhost:11434/api/generate",
                json={"model": body.model, "prompt": "OK", "stream": False},
                timeout=10
            )
            if r.status_code != 200:
                return {"valid": False, "error": f"Ollama returned {r.status_code}"}
            latency = int((time.time() - start) * 1000)
            return {"valid": True, "latency_ms": latency, "model": body.model}

        elif body.provider_type == "openai_compatible":
            response = litellm.completion(
                model=f"openai/{body.model}",
                messages=[{"role": "user", "content": "Reply with: OK"}],
                api_key=body.api_key,
                api_base=body.base_url,
                max_tokens=5,
                num_retries=0,
            )

        else:  # cloud provider
            model_string = build_litellm_model_string(body.provider_name, body.model)
            response = litellm.completion(
                model=model_string,
                messages=[{"role": "user", "content": "Reply with: OK"}],
                api_key=body.api_key,
                max_tokens=5,
                num_retries=0,
            )

        latency = int((time.time() - start) * 1000)
        return {"valid": True, "latency_ms": latency, "model": body.model}

    except Exception as e:
        return {"valid": False, "error": str(e)}


@router.post("/save-provider")
async def save_provider(body: SaveProviderRequest):
    """Write provider to YAML, API key to .env. Triggers role reassignment."""
    # Write API key to .env only — never to YAML
    if body.api_key:
        env_var_name = f"{body.provider_name.upper()}_API_KEY"
        _write_to_env(env_var_name, body.api_key)

    # Load and update YAML
    config = _load_yaml()

    env_var = f"{body.provider_name.upper()}_API_KEY" if body.api_key else None

    # Determine base_url for known cloud providers routed through Groq
    base_url = body.base_url
    if body.provider_name == "groq" and not base_url:
        base_url = "https://api.groq.com/openai/v1"

    provider_entry = {
        "id": body.provider_id,
        "display_name": body.display_name,
        "tier": _infer_tier(body.provider_name),
        "type": body.provider_type,
        "model": body.model,
        "litellm_model_string": build_litellm_model_string(
            body.provider_name, body.model
        ),
        "api_key_env": env_var,
        "exclude": False,
        "limits": {
            "rpd": body.daily_quota,
            "rpm": None,
            "tpd": None,
        },
        "cost_per_1k_tokens": body.cost_per_1k,
    }

    if base_url:
        provider_entry["base_url"] = base_url

    # Remove existing entry with same id if present
    config["providers"] = [
        p for p in config["providers"]
        if p["id"] != body.provider_id
    ]
    config["providers"].append(provider_entry)

    # Reassign roles based on all current providers
    config["role_assignments"] = _assign_roles(config["providers"])

    _save_yaml(config)

    return {"success": True, "provider_id": body.provider_id}


@router.post("/remove-provider")
async def remove_provider(body: RemoveProviderRequest):
    """Remove a provider from the YAML and reassign roles."""
    config = _load_yaml()
    config["providers"] = [
        p for p in config["providers"]
        if p["id"] != body.provider_id
    ]
    config["role_assignments"] = _assign_roles(config["providers"])
    _save_yaml(config)
    return {"success": True, "removed": body.provider_id}


@router.post("/validate-finnhub")
async def validate_finnhub(body: FinnhubValidationRequest):
    """Test Finnhub API key with a real AAPL quote."""
    import requests as req_lib

    start = time.time()
    try:
        r = req_lib.get(
            "https://finnhub.io/api/v1/quote",
            params={"symbol": "AAPL", "token": body.api_key},
            timeout=5,
        )
        data = r.json()
        if "c" not in data or data["c"] == 0:
            return {"valid": False, "error": "Invalid key or no data returned"}
        latency = int((time.time() - start) * 1000)
        # Write to DB on success
        UserProfileService().set_api_key("default", "finnhub", body.api_key)
        return {
            "valid": True,
            "latency_ms": latency,
            "aapl_price": data["c"],
        }
    except Exception as e:
        return {"valid": False, "error": str(e)}


MINIMUM_REQUIRED_ROLES = [
    "strategy_generation",
    "debate_moderator",
    "terminal_fallback",
]

@router.get("/readiness")
async def check_readiness():
    """Check whether the minimum viable pipeline is configured."""
    config = _load_yaml()
    assigned = set(config.get("role_assignments", {}).keys())

    missing_roles = [r for r in MINIMUM_REQUIRED_ROLES if r not in assigned]

    # Terminal fallback must be unlimited
    fallback = config.get("role_assignments", {}).get("terminal_fallback", {})
    if fallback:
        primary_id = fallback.get("primary")
        primary = next(
            (p for p in config["providers"] if p["id"] == primary_id),
            None,
        )
        if primary and primary.get("limits", {}).get("rpd") is not None:
            missing_roles.append("terminal_fallback_must_be_unlimited")

    finnhub_key = UserProfileService().get_api_key("default", "finnhub")
    has_price_feed = bool(finnhub_key)

    return {
        "ready": len(missing_roles) == 0 and has_price_feed,
        "missing_roles": missing_roles,
        "has_price_feed": has_price_feed,
        "provider_count": len(config.get("providers", [])),
    }
