# Aegis AI — Test Log

> Record of every test executed, results, and failures encountered.

---

## Phase 1: Data Ingestion Engine

### yfinance Connector Tests — Mar 3, 2026

| # | Test | Ticker | Result | Details |
|---|------|--------|--------|---------|
| 1 | `get_prices()` 30 days | AAPL | ✅ Pass | 20 bars, range 2026-02-02 to 2026-03-02. Columns: date, open, high, low, close, volume |
| 2 | `get_fundamentals()` | AAPL | ✅ Pass | P/E 33.3, market cap $3.87T, EPS $7.91, analyst: buy, target $293.29, sector: Technology |
| 3 | `get_news()` | AAPL | ✅ Pass | 10 headlines returned. Sources: Yahoo Finance, Simply Wall St. Top: "Apple unveils new MacBooks powered by M5 chips" |
| 4 | `get_prices()` 30 days | NVDA | ✅ Pass | 20 bars, latest close $182.48 |
| 5 | `get_fundamentals()` | NVDA | ✅ Pass | P/E 36.7, market cap $4.37T, analyst: strong_buy, target $264.25 |
| 6 | `get_prices()` invalid ticker | ZZZZZZ | ✅ Pass | Returns None gracefully, no crash. Error logged: "No price data returned for ZZZZZZ" |
| 7 | `health_check()` | AAPL | ✅ Pass | Returns True |

**Summary:** 7/7 tests passed. yfinance connector successfully returns real market data for valid tickers and handles invalid tickers gracefully.

---

## Pending Tests

### Data Engine (registry + cache)
- [ ] Multiple connectors register correctly
- [ ] Fallback: if yfinance fails, tries Alpaca
- [ ] Parquet cache saves data locally
- [ ] Cache serves stale data when API is down
- [ ] Cache TTL respects freshness windows

### Expanded yfinance
- [ ] `get_financials()` returns balance sheet / income / cash flow
- [ ] `get_options()` returns options chain with IV
- [ ] `get_insider_activity()` returns insider transactions
- [ ] `get_short_interest()` returns short data

### FRED Connector
- [ ] Connects with API key
- [ ] Returns macro indicators (fed funds, CPI, GDP, unemployment)

### FinBERT Connector
- [ ] Model loads on CPU
- [ ] Scores positive headline correctly
- [ ] Scores negative headline correctly
- [ ] Handles empty/malformed text

### Alpaca Connector
- [ ] Authenticates with API key
- [ ] Returns prices (backup path)
- [ ] Places paper trade
- [ ] Gets account balance

### SEC EDGAR Connector
- [ ] Fetches 10-K filing for a ticker
- [ ] Returns parsed text sections

### Finnhub Connector
- [ ] Authenticates with API key
- [ ] Returns earnings transcript
