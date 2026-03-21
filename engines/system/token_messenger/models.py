from enum import Enum
import time
import secrets
from pydantic import BaseModel, Field

class WorkflowStage(str, Enum):
    BACKTEST   = "backtest"
    AUDIT      = "audit"
    PROMOTION  = "promotion"
    DEPLOYMENT = "deployment"

class WorkflowToken(BaseModel):
    """
    Cryptographic single-use credential for the MCP Token Messenger pattern.
    Validates sequencing and configuration integrity across pipeline boundaries.
    """
    token_value: str = Field(description="secrets.token_urlsafe(32)")
    workflow_id: str
    stage: WorkflowStage
    config_hash: str = Field(description="sha256 of strategy config at issue time")
    issued_at: float
    expires_at: float
    consumed: bool = False
