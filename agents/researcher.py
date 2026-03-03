import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Dict, Any, List
from tools.market_api import AlpacaClient, FMPClient
from langchain_core.prompts import PromptTemplate
from datetime import datetime

class ResearcherAgent:
    """
    Ingests market data from Alpaca and fundamental data from FMP.
    Produces a clean JSON structure for downstream agents.
    """
    def __init__(self):
        self.alpaca = AlpacaClient()
        self.fmp = FMPClient()
        
    def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes the research step.
        Input state must have 'ticker'.
        """
        ticker = state.get("ticker")
        if not ticker:
            raise ValueError("Researcher Agent requires a 'ticker' in the state.")
            
        print(f"[Researcher] Gathering data for {ticker}...")
        
        try:
            # 1. Get 30 days of price action
            prices = self.alpaca.get_historical_prices(ticker, days=30)
            
            # 2. Get current fundamental metrics (P/E ratio etc)
            metrics = self.fmp.get_company_metrics(ticker)
            
            # 3. Get recent earnings transcript summary
            # Default to most recent likely quarter for demonstration
            now = datetime.now()
            year = now.year if now.month > 3 else now.year - 1
            quarter = (now.month - 1) // 3
            if quarter == 0: quarter = 4
                
            transcript = self.fmp.get_earnings_transcript_summary(ticker, year=year, quarter=quarter)
            
            # 4. Moving Averages
            technicals = self.fmp.get_moving_averages(ticker)
            
            research_data = {
                "ticker": ticker,
                "timestamp": datetime.now().isoformat(),
                "prices_30d_summary": {
                    "count": len(prices),
                    "latest_close": prices[-1]["close"] if prices else None,
                    "oldest_close": prices[0]["close"] if prices else None,
                },
                "metrics": metrics,
                "technicals": technicals,
                "transcript_summary": transcript
            }
            
            # Also attach raw price data to state for Quant calculate_sma etc
            state["prices"] = prices
            state["research_data"] = research_data
            
            print(f"[Researcher] Successfully compiled profile for {ticker}.")
            return state
            
        except Exception as e:
            print(f"[Researcher] Error during execution: {e}")
            state["error"] = str(e)
            return state
