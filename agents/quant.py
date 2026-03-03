import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Dict, Any
from tools.calculators import TradingCalculators
from tools.market_api import AlpacaClient
from config.manager import ConfigManager

class QuantAgent:
    """
    Pure Python mathematical router.
    Uses traditional quants models (Kelly, SMA) to dictate position size.
    """
    def __init__(self):
        self.alpaca = AlpacaClient()

    def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes the quant step.
        """
        ticker = state.get("ticker")
        prices = state.get("prices", [])
        research_data = state.get("research_data", {})
        
        print(f"[Quant] Calculating position size for {ticker}...")
        
        try:
            current_cash = self.alpaca.get_account_balance()
            
            # 1. Simple Technical Filter
            # If price < 50 SMA, do not buy (Trend Following)
            close_prices = [p["close"] for p in prices]
            sma_20 = TradingCalculators.calculate_sma(close_prices, periods=20)
            latest_price = close_prices[-1] if close_prices else 0.0
            
            technical_signal = "NEUTRAL"
            if sma_20 and latest_price > sma_20:
                technical_signal = "BULLISH"
            elif sma_20 and latest_price < sma_20:
                technical_signal = "BEARISH"
                
            # 2. Size the position
            # We use a fixed risk proxy for this prototype based on technicals
            win_rate_proxy = 0.55 if technical_signal == "BULLISH" else 0.45
            kelly_pct = TradingCalculators.calculate_kelly_criterion(
                win_rate=win_rate_proxy, 
                win_loss_ratio=1.5, # Assume 1.5 R:R in our system
                fraction=0.5
            )
            
            # 3. Apply User Configuration Limits
            config = ConfigManager.load_config()
            max_pct = config.get("max_position_size_pct", 1.0)
            final_allocation_pct = min(kelly_pct, max_pct)
            
            allocation_usd = TradingCalculators.calculate_position_size_usd(current_cash, final_allocation_pct)
            
            # Calculate integer shares
            if latest_price > 0:
                shares = int(allocation_usd // latest_price)
            else:
                shares = 0
                
            quant_data = {
                "technical_signal": technical_signal,
                "sma_20": sma_20,
                "latest_price": latest_price,
                "kelly_percentage": kelly_pct,
                "recommended_allocation_usd": allocation_usd,
                "recommended_shares": shares,
                "decision": "PROCEED" if shares > 0 and technical_signal != "BEARISH" else "SKIP"
            }
            
            state["quant_data"] = quant_data
            
            print(f"[Quant] Result: {quant_data['decision']} - Size: {shares} shares (${allocation_usd:.2f})")
            return state
            
        except Exception as e:
            print(f"[Quant] Error during execution: {e}")
            state["error"] = str(e)
            return state
