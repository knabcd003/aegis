from pydantic import BaseModel, Field
from typing import List

class ScenarioSummary(BaseModel):
    scenario_id: str
    description: str
    pass_status: bool
    max_drawdown: float

class ScenarioBatteryResult(BaseModel):
    scenarios_run:         int
    scenarios_passed:      int
    pass_rate:             float
    worst_case_drawdown:   float
    expected_shortfall_95: float
    battery_passed:        bool      # True iff pass_rate >= 0.70
    failing_scenarios:     List[ScenarioSummary]
    generator_type:        str       # "block_bootstrap" | "wgan_gp"

class BootstrapRequest(BaseModel):
    strategy_returns: List[float]
    mandate_max_drawdown: float
    num_scenarios: int = Field(default=100)
    block_size_days: int = Field(default=20)
    scenario_length_days: int = Field(default=252)
