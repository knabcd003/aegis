import os
import requests
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class ConfigurationError(Exception):
    pass

class FinnhubPriceFeed:
    """Live price feed using Finnhub's free basic quote endpoint."""
    
    def __init__(self):
        self.api_key = os.getenv("FINNHUB_API_KEY")
        if not self.api_key:
            raise ConfigurationError(
                "FINNHUB_API_KEY environment variable is missing. "
                "Required for live Signal Card Freshness validation."
            )
        self.base_url = "https://finnhub.io/api/v1/quote"
        self.timeout = 2.0  # Strict 2-second timeout

    def get_mid_price(self, ticker: str) -> Optional[float]:
        """
        Fetches current price for a ticker. 
        Returns None on timeout or network error to ensure fails-closed behavior.
        """
        try:
            response = requests.get(
                self.base_url,
                params={"symbol": ticker, "token": self.api_key},
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()
            
            # Finnhub /quote response format:
            # c: Current price
            current_price = data.get("c")
            if current_price is None or current_price == 0:
                return None
                
            return float(current_price)
            
        except requests.exceptions.RequestException as e:
            logger.warning(f"Finnhub price feed unreachable for {ticker}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching price for {ticker}: {e}")
            return None
