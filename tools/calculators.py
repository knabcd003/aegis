import math
from typing import List, Dict, Optional

class TradingCalculators:
    """
    Pure Python implementations of mathematical formulas used for position sizing
    and technical analysis. No LLM calls allowed here.
    """
    
    @staticmethod
    def calculate_kelly_criterion(win_rate: float, win_loss_ratio: float, fraction: float = 0.5) -> float:
        """
        Calculates the fractional Kelly Criterion for position sizing.
        
        Formula: Kelly % = W - [(1 - W) / R]
        W = Win probability
        R = Win/Loss ratio (Average Gain / Average Loss)
        fraction = fractional Kelly modifier (often 0.5 or 'Half Kelly' to reduce volatility)
        
        Returns the percentage of the portfolio to risk (between 0.0 and 1.0)
        """
        if win_rate < 0 or win_rate > 1:
            raise ValueError("Win rate must be between 0 and 1")
        if win_loss_ratio <= 0:
            return 0.0
            
        kelly_pct = win_rate - ((1.0 - win_rate) / win_loss_ratio)
        
        # Apply fractional multiplier
        fractional_kelly = kelly_pct * fraction
        
        # Clamp between 0 and 1 (or predefined max like 0.25)
        # We don't want to short in this long-only implementation if negative
        return max(0.0, min(1.0, fractional_kelly))

    @staticmethod
    def calculate_position_size_usd(total_capital: float, risk_percentage: float, max_allocation: float = 0.2) -> float:
        """
        Calculates exact USD allocation given a total capital base and risk percentage.
        Clamps at a max_allocation to prevent overexposure to a single asset.
        """
        if total_capital < 0:
            return 0.0
            
        allocation_pct = min(risk_percentage, max_allocation)
        return total_capital * allocation_pct

    @staticmethod
    def calculate_sma(prices: List[float], periods: int) -> Optional[float]:
        """
        Calculates a Simple Moving Average (SMA).
        """
        if not prices or len(prices) < periods or periods <= 0:
            return None
            
        # Take the most recent 'periods' prices
        recent_prices = prices[-periods:]
        return sum(recent_prices) / periods

    @staticmethod
    def calculate_stop_loss_price(entry_price: float, atr: float, multiplier: float = 2.0) -> float:
        """
        Calculates an ATR-based stop loss price for a long position.
        """
        if entry_price <= 0 or atr < 0:
            raise ValueError("Entry price and ATR must be positive")
            
        return max(0.0, entry_price - (atr * multiplier))
        
    @staticmethod
    def calculate_take_profit_price(entry_price: float, atr: float, multiplier: float = 3.0) -> float:
        """
        Calculates an ATR-based take profit price for a long position.
        """
        if entry_price <= 0 or atr < 0:
            raise ValueError("Entry price and ATR must be positive")
            
        return entry_price + (atr * multiplier)
