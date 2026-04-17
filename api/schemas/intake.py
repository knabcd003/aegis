from pydantic import BaseModel
from typing import Optional, List, Dict

class IntakeDraft(BaseModel):
    risk_tolerance: str
    time_horizon: str
    max_drawdown_target: float
    raw_desire: str
    is_path_b: bool = False
    tickers: Optional[List[str]] = None

class ValidationResponse(BaseModel):
    mandate_summary: Dict[str, str]
    contradictions: List[str]
    is_valid: bool

class ConfirmResponse(BaseModel):
    workflow_id: str
    status: str
