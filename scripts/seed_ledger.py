import yfinance as yf
from datetime import date
from engines.data_ingestion import ledger
import pandas as pd

tickers = ["AAPL", "MSFT", "NVDA", "GOOGL", "META"]
for ticker in tickers:
    stock = yf.Ticker(ticker)
    df = stock.history(start="2018-01-01", end="2024-01-01", interval="1d", auto_adjust=False)
    if not df.empty:
        df = df.reset_index()
        if "Datetime" in df.columns:
            df = df.rename(columns={"Datetime": "date"})
        else:
            df = df.rename(columns={"Date": "date"})
        df = df.rename(columns={"Open": "open", "High": "high", "Low": "low", "Close": "close", "Volume": "volume"})
        df = df[["date", "open", "high", "low", "close", "volume"]].copy()
        df["date"] = pd.to_datetime(df["date"]).dt.date
        df["public_disclosure_ts"] = pd.to_datetime(df["date"])
        df["date"] = df["date"].astype(str)
        ledger.write_prices(ticker, df, download_date=date.today())
        print(f"Seeded {ticker} to ledger.")
