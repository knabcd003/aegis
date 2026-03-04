# Aegis AI — Current Phase

> **Phase 1: Data Ingestion Engine**
> Last updated: Mar 3, 2026

---

## What We're Building

A pluggable data ingestion engine that pulls market data from multiple sources, normalizes it into a standard format, caches it in Parquet, and serves it through a single interface. All downstream systems (Quant, Analyst, Sentinel) consume from this engine — they never touch external APIs directly.

## Progress

```
[██████░░░░░░░░░░░░░░] 30%
```

### Done
- [x] `base_connector.py` — abstract interface
- [x] `yfinance_connector.py` — prices, fundamentals, news (tested ✅)
- [x] Frontend nuked (kept design system)
- [x] Old backend nuked

### Building Now
- [ ] Expand yfinance connector: financials, options, insiders, short interest
- [ ] `data_engine.py` — connector registry + Parquet cache

### Up Next
- [ ] `fred_connector.py` — macro data
- [ ] `finbert_connector.py` — NLP sentiment
- [ ] `sec_edgar_connector.py` — SEC filing text
- [ ] `finnhub_connector.py` — earnings transcripts
- [ ] `alpaca_connector.py` — backup prices + trade execution

## Current File Structure

```
Aegis_AI/
├── engines/
│   └── data_ingestion/
│       ├── base_connector.py      ✅ Done
│       ├── data_engine.py         🔨 Next
│       └── connectors/
│           ├── yfinance_connector.py  ✅ Done
│           ├── fred_connector.py      ⬜ Pending
│           ├── finbert_connector.py   ⬜ Pending
│           ├── alpaca_connector.py    ⬜ Pending
│           ├── sec_edgar_connector.py ⬜ Pending
│           └── finnhub_connector.py   ⬜ Pending
├── config/
│   ├── manager.py
│   └── user_preferences.json
├── frontend/src/
│   ├── index.css              ✅ Design system kept
│   └── main.tsx               ✅ Entry point kept
├── BUILD_LOG.md
├── TEST_LOG.md
├── CURRENT_PHASE.md           ← you are here
├── requirements.txt
└── .env
```

## Decisions Made This Phase

| Decision | Rationale |
|----------|-----------|
| yfinance as primary data source | Free, no key, covers ~70% of all data needs |
| Dropped FMP entirely | yfinance provides same fundamentals for free |
| Parquet + DuckDB for storage | Columnar storage + SQL queries, no server |
| MLflow for experiment tracking | Free, local, Databricks-style dashboard |
| FinBERT for NLP (not Claude) | $0 local inference on CPU for sentiment scoring |

## Blockers

None. Current phase requires no API keys (yfinance is free).
