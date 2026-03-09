from datetime import date
from typing import Dict, Any
from engines.data_ingestion.connectors.finnhub_connector import FinnhubConnector


class EarningsRevisionTracker:
    """
    Tracks earnings estimate revisions to compute momentum and direction.
    """
    def __init__(self):
        self.fh = FinnhubConnector()

    def compute(self, ticker: str, as_of_date: date) -> Dict[str, Any]:
        """
        Input: Finnhub estimate history for a ticker + `as_of_date`
        Output: {direction: "up"|"down"|"flat", magnitude: float, momentum: "accelerating"|"stable"|"decelerating", revision_date: date}
        Point-in-time: only revisions where `public_disclosure_ts <= as_of_date`
        """
        # Fetch point-in-time earnings revisions
        # finnhub connector already handles public_disclosure_ts <= as_of_date 
        revisions = self.fh.get_earnings_revisions(ticker, as_of_date=as_of_date)
        
        if not revisions:
            return {
                "direction": "flat",
                "magnitude": 0.0,
                "momentum": "stable",
                "revision_date": None
            }

        # The revisions come back sorted latest first
        latest = revisions[0]
        
        # Determine direction based on the latest revisions 'up' vs 'down' counts
        # This is a simplified proxy - real logic might compare eps estimates over time
        up_revisions = latest.get("up", 0)
        down_revisions = latest.get("down", 0)
        
        if up_revisions > down_revisions:
            direction = "up"
        elif down_revisions > up_revisions:
            direction = "down"
        else:
            direction = "flat"
            
        magnitude = float(up_revisions - down_revisions) / max(1, up_revisions + down_revisions)
        momentum = "stable"
        if magnitude > 0.5:
            momentum = "accelerating"
        elif magnitude < -0.5:
            momentum = "decelerating"
            
        try:
            rev_date = date.fromisoformat(latest.get("public_disclosure_ts", ""))
        except Exception:
            rev_date = as_of_date

        return {
            "direction": direction,
            "magnitude": magnitude,
            "momentum": momentum,
            "revision_date": rev_date
        }
