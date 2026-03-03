import os
import requests
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import alpaca_trade_api as tradeapi
from alpaca_trade_api.rest import TimeFrame
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

ALPACA_API_KEY = os.getenv("ALPACA_API_KEY")
ALPACA_SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")
ALPACA_BASE_URL = os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")
FMP_API_KEY = os.getenv("FMP_API_KEY")

class AlpacaClient:
    def __init__(self):
        """Initialize the Alpaca API client."""
        if not ALPACA_API_KEY or not ALPACA_SECRET_KEY:
            raise ValueError("Alpaca API keys are missing in the environment.")
            
        self.api = tradeapi.REST(
            key_id=ALPACA_API_KEY,
            secret_key=ALPACA_SECRET_KEY,
            base_url=ALPACA_BASE_URL,
            api_version='v2'
        )

    def get_account_balance(self) -> float:
        """Retrieves the current available cash balance."""
        try:
            account = self.api.get_account()
            return float(account.cash)
        except Exception as e:
            print(f"Error retrieving account balance: {e}")
            return 0.0

    def get_portfolio_metrics(self) -> Dict[str, Any]:
        """Retrieves full portfolio value and PnL metrics from Alpaca."""
        try:
            account = self.api.get_account()
            equity = float(account.equity)
            last_equity = float(account.last_equity)
            pnl = equity - last_equity
            pnl_pct = (pnl / last_equity * 100) if last_equity > 0 else 0.0
            
            return {
                "total_value": equity,
                "daily_pnl": pnl,
                "pnl_percentage": round(pnl_pct, 2),
                "available_cash": float(account.cash)
            }
        except Exception as e:
            print(f"Error retrieving portfolio metrics: {e}")
            return {
                "total_value": 0.0,
                "daily_pnl": 0.0,
                "pnl_percentage": 0.0,
                "available_cash": 0.0
            }

    def get_historical_prices(self, symbol: str, days: int = 30) -> List[Dict[str, Any]]:
        """
        Retrieves the last `days` of daily price action.
        """
        try:
            end = datetime.now()
            start = end - timedelta(days=days)
            
            # Format dates to RFC-3339 string format required by Alpaca v2
            start_str = start.strftime('%Y-%m-%d')
            end_str = end.strftime('%Y-%m-%d')
            
            bars = self.api.get_bars(
                symbol, 
                TimeFrame.Day, 
                start_str, 
                end_str, 
                adjustment='all'
            ).df
            
            if bars.empty:
                return []
                
            # Convert timezone-aware datetimes to strings
            return [
                {
                    "date": index.strftime('%Y-%m-%d'),
                    "close": float(row['close']),
                    "volume": int(row['volume'])
                }
                for index, row in bars.iterrows()
            ]
        except Exception as e:
            print(f"Error retrieving historical prices for {symbol}: {e}")
            return []

    def execute_trade(self, symbol: str, qty: float, side: str) -> Optional[Dict[str, Any]]:
        """
        Executes a paper trade via Alpaca.
        side: 'buy' or 'sell'
        """
        try:
            order = self.api.submit_order(
                symbol=symbol,
                qty=qty,
                side=side,
                type='market',
                time_in_force='gtc'
            )
            return {
                "id": order.id,
                "symbol": order.symbol,
                "qty": float(order.qty),
                "filled_avg_price": float(order.filled_avg_price) if order.filled_avg_price else None,
                "status": order.status,
                "side": order.side
            }
        except Exception as e:
            print(f"Error executing {side} order for {symbol}: {e}")
            return None
            
    def get_open_positions(self) -> List[Dict[str, Any]]:
        """Retrieves currently open positions."""
        try:
            positions = self.api.list_positions()
            return [
                {
                    "symbol": p.symbol,
                    "qty": float(p.qty),
                    "market_value": float(p.market_value),
                    "avg_entry_price": float(p.avg_entry_price),
                    "current_price": float(p.current_price),
                    "unrealized_pl": float(p.unrealized_pl)
                }
                for p in positions
            ]
        except Exception as e:
            print(f"Error retrieving open positions: {e}")
            return []

class FMPClient:
    def __init__(self):
        """Initialize the Financial Modeling Prep (FMP) client."""
        if not FMP_API_KEY:
            raise ValueError("FMP API key is missing in the environment.")
        self.api_key = FMP_API_KEY
        self.base_url = "https://financialmodelingprep.com/api/v3"

    def get_company_metrics(self, symbol: str) -> Dict[str, Any]:
        """Provides current metrics such as P/E ratio."""
        try:
            url = f"{self.base_url}/key-metrics-ttm/{symbol}?apikey={self.api_key}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                metrics = data[0]
                return {
                    "pe_ratio": metrics.get("peRatioTTM"),
                    "pb_ratio": metrics.get("pbRatioTTM"),
                    "roe": metrics.get("roeTTM")
                }
            return {}
        except Exception as e:
            print(f"Error retrieving metrics for {symbol}: {e}")
            return {}

    def get_earnings_transcript_summary(self, symbol: str, year: int, quarter: int) -> str:
        """
        Fetches earnings transcript. FMP provides transcript endpoints but often require premium.
        For robust local error handling, we attempt to fetch or return a graceful missing message.
        """
        try:
            url = f"{self.base_url}/earning_call_transcript/{symbol}?year={year}&quarter={quarter}&apikey={self.api_key}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data and len(data) > 0:
                    transcript = data[0].get("content", "")
                    # Return a snippet mapping to minimize token load for LLMs, or full string depending on use
                    return transcript[:2000] + "... [TRUNCATED]" if len(transcript) > 2000 else transcript
            return "Transcript not available or requires premium API tier."
        except Exception as e:
            print(f"Error retrieving transcript for {symbol}: {e}")
            return "Error retrieving transcript."
            
    def get_moving_averages(self, symbol: str) -> Dict[str, float]:
        """Retrieve SMA from FMP daily technical indicators."""
        try:
             # Just utilizing the daily price action to calculate simple MA on the client side 
             # is often more reliable and reduces API footprint, but here is the API approach.
             url = f"{self.base_url}/technical_indicator/1day/{symbol}?type=sma&period=50&apikey={self.api_key}"
             response = requests.get(url, timeout=10)
             if response.status_code == 200:
                 data = response.json()
                 if data and isinstance(data, list) and len(data) > 0:
                     latest = data[0]
                     return {
                         "sma_50": latest.get("sma"),
                         "date": latest.get("date")
                     }
             return {}
        except Exception as e:
             print(f"Error retrieving technicals for {symbol}: {e}")
             return {}
