from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field

# ---------------------------------------------------------
# Sub-Schemas
# ---------------------------------------------------------

class AssetUniverse(BaseModel):
    tickers: List[str]
    benchmark: str = "SPY"


class SignalGateConfig(BaseModel):
    finbert_above: Optional[float] = None
    earnings_revision_direction: Optional[Literal["up", "down", "flat"]] = None


class EarningsRevisionConfig(BaseModel):
    enabled: bool = False
    warn_threshold: float = 0.02


class InsiderMonitorConfig(BaseModel):
    enabled: bool = False
    cluster_window_days: int = 45


class FundamentalEngineConfig(BaseModel):
    earnings_revision: EarningsRevisionConfig
    insider_monitor: InsiderMonitorConfig


class PositionSizingConfig(BaseModel):
    capital: float
    max_position_pct: float
    method: Literal["equal_weight", "conviction_weight"] = "equal_weight"


class PromotionCriteriaConfig(BaseModel):
    held_out_sharpe_min: float = 0.85
    held_out_degradation_max: float = 0.35


class SandboxConfig(BaseModel):
    slippage_bps: int = 15
    min_hold_days: int = 5
    promotion_criteria: PromotionCriteriaConfig


class LoggingConfig(BaseModel):
    depth: Literal["minimal", "production", "debug"] = "production"


class RoutingConfig(BaseModel):
    mode: Literal["build", "eval", "live"] = "build"
    logging: LoggingConfig


class AgentConfig(BaseModel):
    enabled: bool = False
    provider: Literal["ollama", "openai", "anthropic"] = "ollama"
    model: str = "qwen2.5:3b"

# ---------------------------------------------------------
# Main Schema
# ---------------------------------------------------------

class AegisConfig(BaseModel):
    config_id: str
    version: str
    asset_universe: AssetUniverse
    signal_gate: SignalGateConfig
    fundamental_engine: FundamentalEngineConfig
    agent: AgentConfig
    position_sizing: PositionSizingConfig
    sandbox: SandboxConfig
    routing: RoutingConfig
    
    # These fields are populated by ConfigManager, not the JSON
    fingerprint: Optional[str] = Field(default=None, exclude=True)
    run_id: Optional[str] = Field(default=None, exclude=True)
