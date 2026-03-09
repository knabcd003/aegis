from datetime import date, timedelta
from typing import Dict, Any, List

from engines.data_ingestion.connectors.finnhub_connector import FinnhubConnector
from engines.data_ingestion.connectors.congressional_connector import CongressionalConnector


class InsiderActivityMonitor:
    """
    Monitors SEC Form 4 and Congressional STOCK Act disclosures to detect insider clusters.
    """
    def __init__(self):
        self.fh = FinnhubConnector()
        self.cg = CongressionalConnector()

    def compute(self, ticker: str, as_of_date: date, cluster_window_days: int = 45) -> Dict[str, Any]:
        """
        Input: SEC Form 4 filings + Congressional STOCK Act disclosures, `as_of_date`, `cluster_window_days`
        Output: {insider_type: str, transaction: "BUY"|"SELL", cluster_buy: bool, cluster_size: int, congressional: list}
        Point-in-time: edgar_accession_ts <= as_of_date for Form 4; disclosure_filing_ts <= as_of_date for Congressional
        """
        # Fetch point-in-time insider transactions (Form 4 mostly via Finnhub)
        # Note: finnhub connector applies public_disclosure_ts <= as_of_date
        insiders = self.fh.get_insider_transactions(ticker, as_of_date=as_of_date)
        
        cluster_cutoff = (as_of_date - timedelta(days=cluster_window_days)).isoformat()
        
        recent_insider_buys = [
            t for t in insiders 
            if t.get("public_disclosure_ts", "") >= cluster_cutoff 
            and (t.get("transaction_type") == "Buy" or t.get("change", 0) > 0)
        ]
        
        # Fetch Congressional disclosures
        congressional = self.cg.get_disclosures(ticker, days_back=cluster_window_days, as_of_date=as_of_date)
        recent_cong_buys = [
            c for c in congressional 
            if c.get("public_disclosure_ts", "") >= cluster_cutoff
            and c.get("transaction_type", "").lower() in ["purchase", "buy"]
        ]
        
        total_buy_cluster_size = len(recent_insider_buys) + len(recent_cong_buys)
        
        cluster_buy = total_buy_cluster_size >= 3
        transaction_type = "BUY" if total_buy_cluster_size > 0 else "SELL"
        
        insider_type = "mixed" if (recent_insider_buys and recent_cong_buys) else \
                       "corporate" if recent_insider_buys else \
                       "congressional" if recent_cong_buys else "none"
                       
        return {
            "insider_type": insider_type,
            "transaction": transaction_type,
            "cluster_buy": cluster_buy,
            "cluster_size": total_buy_cluster_size,
            "congressional": congressional
        }
