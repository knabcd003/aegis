"""
Alpaca Connector — Backup price data source + paper trade execution.

Requires ALPACA_API_KEY and ALPACA_SECRET_KEY in environment.
Free paper trading account at https://alpaca.markets

Used as:
1. Fallback price source when yfinance fails
2. Paper trade execution for the Analyst/Sentinel engines
"""
import os
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from engines.data_ingestion.base_connector import BaseConnector


class AlpacaConnector(BaseConnector):
    """
    Fetches prices and executes paper trades via Alpaca.
    Falls back gracefully if no API keys are configured.
    """

    def __init__(self, api_key: Optional[str] = None, secret_key: Optional[str] = None,
                 paper: bool = True):
        self._api_key = api_key or os.getenv("ALPACA_API_KEY")
        self._secret_key = secret_key or os.getenv("ALPACA_SECRET_KEY")
        self._paper = paper
        self._trading_client = None
        self._data_client = None

    @property
    def name(self) -> str:
        return "alpaca"

    @property
    def provides_prices(self) -> bool:
        return True

    @property
    def provides_fundamentals(self) -> bool:
        return False

    @property
    def provides_news(self) -> bool:
        return True

    def _has_keys(self) -> bool:
        """Check if API keys are configured (not just placeholders)."""
        if not self._api_key or not self._secret_key:
            return False
        if "your_" in self._api_key.lower() or "here" in self._api_key.lower():
            return False
        return True

    def _init_clients(self) -> bool:
        """Lazy initialize Alpaca API clients."""
        if not self._has_keys():
            return False

        if self._trading_client is not None:
            return True

        try:
            from alpaca.trading.client import TradingClient
            from alpaca.data.historical import StockHistoricalDataClient

            self._trading_client = TradingClient(
                self._api_key, self._secret_key, paper=self._paper
            )
            self._data_client = StockHistoricalDataClient(
                self._api_key, self._secret_key
            )
            return True
        except ImportError:
            print(f"[{self.name}] alpaca-py not installed")
            return False
        except Exception as e:
            print(f"[{self.name}] Error initializing clients: {e}")
            return False

    # ── Price Data (backup source) ───────────────────────────────────────

    def get_prices(self, ticker: str, days: int = 30):
        """Fetch daily OHLCV bars from Alpaca as backup to yfinance."""
        if not self._init_clients():
            if not self._has_keys():
                print(f"[{self.name}] No API keys configured. Set ALPACA_API_KEY in .env")
            return None

        try:
            import pandas as pd
            from alpaca.data.requests import StockBarsRequest
            from alpaca.data.timeframe import TimeFrame

            end = datetime.now()
            start = end - timedelta(days=days)

            request = StockBarsRequest(
                symbol_or_symbols=ticker,
                timeframe=TimeFrame.Day,
                start=start,
                end=end,
            )

            bars = self._data_client.get_stock_bars(request)
            df = bars.df.reset_index()

            if df.empty:
                return None

            df = df.rename(columns={
                "timestamp": "date",
                "open": "open",
                "high": "high",
                "low": "low",
                "close": "close",
                "volume": "volume",
            })
            df = df[["date", "open", "high", "low", "close", "volume"]].copy()
            df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
            return df

        except Exception as e:
            print(f"[{self.name}] Error fetching prices for {ticker}: {e}")
            return None

    # ── Paper Trading ────────────────────────────────────────────────────

    def get_account(self) -> Optional[Dict[str, Any]]:
        """Get paper trading account info."""
        if not self._init_clients():
            return None

        try:
            account = self._trading_client.get_account()
            return {
                "buying_power": float(account.buying_power),
                "portfolio_value": float(account.portfolio_value),
                "cash": float(account.cash),
                "equity": float(account.equity),
                "last_equity": float(account.last_equity),
                "status": account.status.value if hasattr(account.status, 'value') else str(account.status),
            }
        except Exception as e:
            print(f"[{self.name}] Error getting account: {e}")
            return None

    def get_positions(self) -> List[Dict[str, Any]]:
        """Get current open positions."""
        if not self._init_clients():
            return []

        try:
            positions = self._trading_client.get_all_positions()
            return [
                {
                    "ticker": pos.symbol,
                    "qty": float(pos.qty),
                    "market_value": float(pos.market_value),
                    "avg_entry_price": float(pos.avg_entry_price),
                    "current_price": float(pos.current_price),
                    "unrealized_pl": float(pos.unrealized_pl),
                    "unrealized_plpc": float(pos.unrealized_plpc),
                    "side": pos.side.value if hasattr(pos.side, 'value') else str(pos.side),
                }
                for pos in positions
            ]
        except Exception as e:
            print(f"[{self.name}] Error getting positions: {e}")
            return []

    def place_order(self, ticker: str, qty: float, side: str = "buy",
                    order_type: str = "market") -> Optional[Dict[str, Any]]:
        """
        Place a paper trade order.

        Args:
            ticker: Stock symbol
            qty: Number of shares (supports fractional)
            side: "buy" or "sell"
            order_type: "market" or "limit"
        """
        if not self._init_clients():
            return None

        try:
            from alpaca.trading.requests import MarketOrderRequest
            from alpaca.trading.enums import OrderSide, TimeInForce

            order_side = OrderSide.BUY if side.lower() == "buy" else OrderSide.SELL

            order_data = MarketOrderRequest(
                symbol=ticker,
                qty=qty,
                side=order_side,
                time_in_force=TimeInForce.DAY,
            )

            order = self._trading_client.submit_order(order_data)

            return {
                "order_id": str(order.id),
                "ticker": order.symbol,
                "qty": float(order.qty) if order.qty else qty,
                "side": side,
                "type": order_type,
                "status": order.status.value if hasattr(order.status, 'value') else str(order.status),
                "submitted_at": str(order.submitted_at),
            }
        except Exception as e:
            print(f"[{self.name}] Error placing order: {e}")
            return None

    # ── News ─────────────────────────────────────────────────────────────

    def get_news(self, ticker: str, days: int = 7) -> List[Dict[str, Any]]:
        """Fetch news from Alpaca's news API."""
        if not self._init_clients():
            return []

        try:
            from alpaca.data.requests import NewsRequest
            from alpaca.data.historical.news import NewsClient

            news_client = NewsClient(self._api_key, self._secret_key)
            request = NewsRequest(symbols=ticker, limit=20)
            news = news_client.get_news(request)

            return [
                {
                    "headline": item.headline,
                    "date": str(item.created_at),
                    "source": item.source,
                    "url": item.url,
                }
                for item in news.news
            ]
        except Exception as e:
            print(f"[{self.name}] Error fetching news: {e}")
            return []

    # ── BaseConnector interface ──────────────────────────────────────────

    def get_fundamentals(self, ticker: str):
        return None

    def health_check(self) -> bool:
        """Check if Alpaca API is accessible."""
        if not self._has_keys():
            print(f"[{self.name}] No API keys configured")
            return False
        account = self.get_account()
        return account is not None
