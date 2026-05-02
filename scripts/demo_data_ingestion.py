import os
from datetime import date
from dotenv import load_dotenv

# Load API keys
load_dotenv()

from engines.data_ingestion.connectors.yfinance_connector import YFinanceConnector
from engines.data_ingestion.connectors.sec_edgar_connector import SECEdgarConnector
from engines.data_ingestion.connectors.finnhub_connector import FinnhubConnector
from engines.data_ingestion.connectors.fred_connector import FREDConnector
from engines.data_ingestion.connectors.congressional_connector import CongressionalConnector
from engines.data_ingestion import ledger

def run_live_demo(ticker="TSLA"):
    print(f"=== Aegis AI Step 1: Live Data Ingestion Engine ===")
    print(f"Target Ticker: {ticker}")
    print(f"Simulation Date (as_of_date): Today ({date.today()})\n")
    
    # 1. YFinance Prices + Ledger
    print("--- 1. YFinance (Prices) ---")
    yf = YFinanceConnector()
    prices = yf.get_prices(ticker, days=3)
    print(f"Fetched {len(prices)} days of price history.")
    print(f"Latest close: ${prices['close'].iloc[-1]:.2f} (Public Disclosure TS: {prices['public_disclosure_ts'].iloc[-1].date()})")
    
    # 2. Finnhub (News & Earnings)
    print("\n--- 2. Finnhub (News & Estimates) ---")
    if os.getenv("FINNHUB_API_KEY"):
        fh = FinnhubConnector()
        news = fh.get_news(ticker, days=3)
        print(f"Fetched {len(news)} recent news articles.")
        if news:
            print(f"Latest Headline: '{news[0]['headline']}'")
            print(f"Published TS: {news[0]['public_disclosure_ts']}")
        
        revisions = fh.get_earnings_revisions(ticker)
        print(f"Fetched {len(revisions)} earnings consensus records.")
    else:
        print("Skipped (FINNHUB_API_KEY missing)")

    # 3. Congressional Disclosures
    print("\n--- 3. Congressional STOCK Act ---")
    try:
        cong = CongressionalConnector()
        print("Fetching recent trades (may take a few seconds)...")
        trades = cong.get_disclosures(ticker, days_back=90)
        print(f"Found {len(trades)} recent congressional disclosures for {ticker}.")
        for t in trades[:2]:
            print(f" - {t['transaction_type']} {t['ticker']} | Traded: {t['trade_date']} | Filed/Public: {t['disclosure_filing_ts']}")
    except Exception as e:
        print(f"Skipped due to error: {e}")

    # 4. SEC EDGAR (Filings)
    print("\n--- 4. SEC EDGAR (10-K Filings) ---")
    try:
        edgar = SECEdgarConnector()
        filings = edgar.get_filings_list(ticker, filing_type="10-K", count=1)
        if filings:
            accession = filings[0]['accession_number']
            print(f"Latest 10-K Accession: {accession}")
            print(f"Filed/Public TS: {filings[0]['public_disclosure_ts']}")
            print(f"Ledger cached? {ledger.filing_exists(ticker, accession)}")
        else:
            print("No recent 10-K found.")
    except Exception as e:
        print(f"Skipped due to error: {e}")

    # 5. FRED (Macro)
    print("\n--- 5. FRED (Macro Indicators) ---")
    if os.getenv("FRED_API_KEY"):
        fred = FREDConnector()
        macro = fred.get_macro()
        print(f"Macro Data Source: {macro['source']}")
        if "treasury_10y" in macro:
            print(f"10Y Treasury Yield: {macro['treasury_10y']['value']}% (Public TS: {macro['treasury_10y']['public_disclosure_ts']})")
    else:
        print("Skipped (FRED_API_KEY missing)")

    print("\n=== Live Demo Complete ===")
    stats = ledger.ledger_stats()
    print(f"Ledger Size: {stats.get('total_size_mb', 0):.2f} MB ({stats.get('total_files', 0)} files cached)")

if __name__ == "__main__":
    import sys
    ticker = sys.argv[1] if len(sys.argv) > 1 else "TSLA"
    run_live_demo(ticker)
