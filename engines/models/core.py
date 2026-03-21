from datetime import datetime
from pydantic import BaseModel, Field

class PriceBar(BaseModel):
    timestamp: datetime
    open: float = Field(ge=0)
    high: float = Field(ge=0)
    low: float = Field(ge=0)
    close: float = Field(ge=0)
    volume: int = Field(ge=0)


class PortfolioPosition(BaseModel):
    ticker: str
    quantity: float
    average_cost: float
    current_price: float
    market_value: float


class MirrorPortfolioState(BaseModel):
    cash_balance: float = Field(ge=0)
    total_equity: float = Field(ge=0)
    positions: list[PortfolioPosition] = Field(default_factory=list)


class SentinelState(BaseModel):
    sentinel_id: str
    status: str
    active: bool
    # We will expand this as we port Sentinel State Manager, 
    # but providing the structural shell now.


class SignalCardPayload(BaseModel):
    strategy_id: str
    ticker: str
    action: str  # BUY, SELL, HOLD
    confidence: float = Field(ge=0, le=1)
    reasoning: str
