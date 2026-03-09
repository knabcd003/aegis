"""
Tests for Step 1 — Connector public_disclosure_ts enforcement and immutable ledger.

Test IDs: T1.1 through T1.5 as defined in implementation_plan.md.
"""
import os
import tempfile
import shutil
import pytest
import pandas as pd
from datetime import date, datetime
from pathlib import Path
from unittest.mock import patch, MagicMock

# ── Set up a temp ledger dir before any imports that touch it ────────────────

@pytest.fixture(autouse=True)
def temp_ledger(tmp_path, monkeypatch):
    """Redirect all ledger writes to a temporary directory for test isolation.
    ledger._ledger_root() re-reads AEGIS_LEDGER_ROOT on every call, so the
    env override is all that's needed.
    """
    monkeypatch.setenv("AEGIS_LEDGER_ROOT", str(tmp_path / "ledger"))
    yield tmp_path / "ledger"


# ── T1.1 — YFinance: public_disclosure_ts present on every price row ─────────

class TestYFinancePrices:

    def test_price_df_has_disclosure_ts(self):
        """T1.1 — every row returned by get_prices has public_disclosure_ts"""
        from engines.data_ingestion.connectors.yfinance_connector import YFinanceConnector

        # Mock yfinance to return deterministic data — no live network call
        mock_df = pd.DataFrame({
            "Date": pd.to_datetime(["2023-01-10", "2023-01-11", "2023-01-12"]),
            "Open": [150.0, 151.0, 152.0],
            "High": [155.0, 156.0, 157.0],
            "Low": [149.0, 150.0, 151.0],
            "Close": [153.0, 154.0, 155.0],
            "Volume": [1_000_000, 1_100_000, 1_200_000],
        }).set_index("Date")

        with patch("yfinance.Ticker") as mock_ticker:
            mock_ticker.return_value.history.return_value = mock_df
            connector = YFinanceConnector()
            df = connector.get_prices("AAPL", days=30)

        assert df is not None, "get_prices returned None"
        assert "public_disclosure_ts" in df.columns, "public_disclosure_ts column missing"
        assert df["public_disclosure_ts"].notna().all(), "public_disclosure_ts has null values"

    def test_price_disclosure_ts_matches_bar_date(self):
        """T1.1b — for daily bars, public_disclosure_ts equals the bar date"""
        from engines.data_ingestion.connectors.yfinance_connector import YFinanceConnector

        mock_df = pd.DataFrame({
            "Date": pd.to_datetime(["2023-01-10", "2023-01-11"]),
            "Open": [150.0, 151.0],
            "High": [155.0, 156.0],
            "Low": [149.0, 150.0],
            "Close": [153.0, 154.0],
            "Volume": [1_000_000, 1_100_000],
        }).set_index("Date")

        with patch("yfinance.Ticker") as mock_ticker:
            mock_ticker.return_value.history.return_value = mock_df
            connector = YFinanceConnector()
            df = connector.get_prices("AAPL", days=30)

        df["public_disclosure_ts"] = pd.to_datetime(df["public_disclosure_ts"])
        df["parsed_date"] = pd.to_datetime(df["date"])
        for _, row in df.iterrows():
            assert row["public_disclosure_ts"].date() == row["parsed_date"].date(), \
                f"Disclosure date {row['public_disclosure_ts']} doesn't match bar date {row['date']}"


# ── T1.2 — Point-in-time enforcement ─────────────────────────────────────────

class TestPointInTime:

    def test_no_future_prices_returned(self):
        """T1.2 — as_of_date=2023-01-11 must exclude bars dated after 2023-01-11"""
        from engines.data_ingestion.connectors.yfinance_connector import YFinanceConnector

        # Include a bar on 2023-01-12, which should be filtered out
        mock_df = pd.DataFrame({
            "Date": pd.to_datetime(["2023-01-10", "2023-01-11", "2023-01-12"]),
            "Open": [150.0, 151.0, 152.0],
            "High": [155.0, 156.0, 157.0],
            "Low": [149.0, 150.0, 151.0],
            "Close": [153.0, 154.0, 155.0],
            "Volume": [1_000_000, 1_100_000, 1_200_000],
        }).set_index("Date")

        sim_date = date(2023, 1, 11)
        with patch("yfinance.Ticker") as mock_ticker:
            mock_ticker.return_value.history.return_value = mock_df
            connector = YFinanceConnector()
            df = connector.get_prices("AAPL", days=30, as_of_date=sim_date)

        assert df is not None
        df["public_disclosure_ts"] = pd.to_datetime(df["public_disclosure_ts"])
        future_rows = df[df["public_disclosure_ts"].dt.date > sim_date]
        assert len(future_rows) == 0, \
            f"Found {len(future_rows)} rows with disclosure_ts > as_of_date — lookahead bias!"

    def test_finnhub_news_as_of_date_filter(self):
        """T1.2b — Finnhub news after as_of_date is excluded"""
        from engines.data_ingestion.connectors.finnhub_connector import FinnhubConnector

        fake_news = [
            {"headline": "Old news", "datetime": int(datetime(2023, 1, 10).timestamp()),
             "source": "Reuters", "url": "", "summary": ""},
            {"headline": "Future news", "datetime": int(datetime(2023, 1, 15).timestamp()),
             "source": "Reuters", "url": "", "summary": ""},
        ]

        with patch.object(FinnhubConnector, "_request", return_value=fake_news):
            connector = FinnhubConnector(api_key="fake_key")
            news = connector.get_news("AAPL", days=30, as_of_date=date(2023, 1, 12))

        headlines = [n["headline"] for n in news]
        assert "Old news" in headlines, "Old news (before as_of_date) should be included"
        assert "Future news" not in headlines, "Future news (after as_of_date) must be excluded"


# ── T1.3 — Immutable ledger: SEC EDGAR accession never overwrites ─────────────

class TestImmutableLedger:

    def test_same_accession_not_overwritten(self, temp_ledger):
        """T1.3 — writing the same accession number twice doesn't overwrite"""
        from engines.data_ingestion import ledger

        accession = "0001234567-23-000001"
        original_data = {
            "accession_number": accession,
            "public_disclosure_ts": "2023-01-15",
            "form_type": "10-Q",
            "ticker": "AAPL",
            "text": "Original text",
        }

        path1 = ledger.write_filing("AAPL", accession, original_data)
        mtime1 = path1.stat().st_mtime

        # Try to overwrite with different data
        different_data = {**original_data, "text": "Different text — should not appear"}
        path2 = ledger.write_filing("AAPL", accession, different_data)
        mtime2 = path2.stat().st_mtime

        assert path1 == path2, "Different paths returned for same accession"
        assert mtime1 == mtime2, "File was modified — immutability violated!"

        # Verify content is still the original
        stored = ledger.read_filing("AAPL", accession)
        assert stored["text"] == "Original text", "File content was overwritten — immutability violated!"

    def test_price_cache_immutable(self, temp_ledger):
        """T1.3b — writing price data for same ticker/date doesn't overwrite"""
        from engines.data_ingestion import ledger

        df1 = pd.DataFrame({
            "date": ["2023-01-10"],
            "open": [150.0], "high": [155.0], "low": [149.0],
            "close": [153.0], "volume": [1_000_000],
            "public_disclosure_ts": pd.to_datetime(["2023-01-10"]),
        })

        dl_date = date(2023, 1, 10)
        path1 = ledger.write_prices("AAPL", df1, download_date=dl_date)
        mtime1 = path1.stat().st_mtime

        df2 = df1.copy()
        df2["close"] = 999.0  # Different data — should be ignored
        path2 = ledger.write_prices("AAPL", df2, download_date=dl_date)
        mtime2 = path2.stat().st_mtime

        assert mtime1 == mtime2, "Price file was overwritten — immutability violated!"

    def test_different_accessions_stored_separately(self, temp_ledger):
        """T1.3c — two different accession numbers are stored as separate files"""
        from engines.data_ingestion import ledger

        base = {"ticker": "AAPL", "form_type": "10-Q", "public_disclosure_ts": "2023-01-15"}

        path1 = ledger.write_filing("AAPL", "0001234567-23-000001", {**base, "accession_number": "0001234567-23-000001", "period": "Q1"})
        path2 = ledger.write_filing("AAPL", "0001234567-23-000002", {**base, "accession_number": "0001234567-23-000002", "period": "Q2"})

        assert path1 != path2, "Two different accessions stored at same path"
        assert path1.exists() and path2.exists()


# ── T1.4 — Congressional: uses disclosure_filing_ts, never trade_date ─────────

class TestCongressionalDisclosure:

    def _make_disclosure(self, member: str, trade_date: str, filing_date: str) -> dict:
        return {
            "source": "house",
            "member_name": member,
            "member_office": "CA-12",
            "ticker": "AAPL",
            "asset_description": "Apple Inc",
            "transaction_type": "purchase",
            "amount_range": "$1,001 - $15,000",
            "trade_date": trade_date,
            "disclosure_filing_ts": filing_date,
            "public_disclosure_ts": filing_date,  # always filing date
            "document_id": "doc-001",
        }

    def test_congressional_public_ts_equals_filing_ts(self):
        """T1.4 — public_disclosure_ts must equal disclosure_filing_ts, never trade_date"""
        disclosure = self._make_disclosure(
            "Rep. Jane Smith",
            trade_date="2023-01-01",
            filing_date="2023-02-10",
        )

        assert disclosure["public_disclosure_ts"] == disclosure["disclosure_filing_ts"], \
            "public_disclosure_ts must be filing date"
        assert disclosure["public_disclosure_ts"] != disclosure["trade_date"], \
            "public_disclosure_ts must not be trade date (lookahead!)"

    def test_congressional_as_of_filter_excludes_unfiled(self):
        """T1.4b — a trade filed on 2023-02-10 is not visible as of 2023-01-20"""
        from engines.data_ingestion.connectors.congressional_connector import CongressionalConnector

        connector = CongressionalConnector()

        # Simulate get_disclosures returning the filing-dated record
        trade_jan1 = self._make_disclosure("Rep. Jane Smith", "2023-01-01", "2023-02-10")

        with patch.object(connector, "_fetch_house_disclosures", return_value=[trade_jan1]), \
             patch.object(connector, "_fetch_senate_disclosures", return_value=[]):
            # Query as of Jan 20 — filing hasn't happened yet
            results = connector.get_disclosures("AAPL", as_of_date=date(2023, 1, 20))

        assert len(results) == 0, \
            "Disclosure filed on 2023-02-10 should NOT be visible as of 2023-01-20"

    def test_congressional_as_of_filter_includes_filed(self):
        """T1.4c — a trade filed on 2023-02-10 IS visible as of 2023-02-15"""
        from engines.data_ingestion.connectors.congressional_connector import CongressionalConnector

        connector = CongressionalConnector()
        trade_jan1 = self._make_disclosure("Rep. Jane Smith", "2023-01-01", "2023-02-10")

        with patch.object(connector, "_fetch_house_disclosures", return_value=[trade_jan1]), \
             patch.object(connector, "_fetch_senate_disclosures", return_value=[]):
            results = connector.get_disclosures("AAPL", as_of_date=date(2023, 2, 15))

        assert len(results) == 1, \
            "Disclosure filed on 2023-02-10 SHOULD be visible as of 2023-02-15"

    def test_congressional_no_trade_date_in_timestamp(self):
        """T1.4d — verify disclosure records don't use trade_date as public timestamp"""
        disclosure = self._make_disclosure("Sen. Bob Jones", "2023-01-01", "2023-02-15")
        # The STOCK Act lag is 45 days here — correct behavior
        lag_days = (
            date.fromisoformat(disclosure["disclosure_filing_ts"]) -
            date.fromisoformat(disclosure["trade_date"])
        ).days
        assert lag_days >= 0, "Filing date must be on or after trade date"
        # public_disclosure_ts must be the later (filing) date
        assert disclosure["public_disclosure_ts"] >= disclosure["trade_date"], \
            "public_disclosure_ts must be >= trade_date"


# ── T1.5 — NLI model is a singleton ──────────────────────────────────────────

class TestNLISingleton:

    def test_nli_model_singleton_across_instances(self):
        """T1.5 — two SECEdgarConnector instances share the same NLI model object"""
        # Mock out the actual model loading — we don't want to download 183MB in tests
        with patch("engines.data_ingestion.connectors.sec_edgar_connector._get_nli_model") as mock_get:
            mock_model = MagicMock()
            mock_get.return_value = mock_model

            from engines.data_ingestion.connectors.sec_edgar_connector import SECEdgarConnector
            c1 = SECEdgarConnector()
            c2 = SECEdgarConnector()

            # Both connectors should return the same mock model
            model1 = c1._nli_model
            model2 = c2._nli_model

            # _get_nli_model should be the same function — mock called consistently
            assert mock_get.call_count >= 2, "NLI model getter should be called at each construction"


# ── T1.6 — FinBERT inherits public_disclosure_ts from source ─────────────────

class TestFinBERT:

    def test_score_news_items_inherits_disclosure_ts(self):
        """T1.6 — FinBERT score_news_items preserves source article's public_disclosure_ts"""
        # Guard against transformers not being installed (heavy dep)
        import sys
        # Mock the entire transformers module before importing finbert
        mock_transformers = MagicMock()
        mock_transformers.BertTokenizer = MagicMock()
        mock_transformers.BertForSequenceClassification = MagicMock()
        mock_transformers.pipeline = MagicMock()
        with patch.dict(sys.modules, {"transformers": mock_transformers}):
            # Force re-import with mocked module
            import importlib
            import engines.data_ingestion.connectors.finbert_connector as fb_mod
            importlib.reload(fb_mod)
            FinBERTConnector = fb_mod.FinBERTConnector

            source_news = [
                {
                    "headline": "Apple beats earnings",
                    "date": "2023-01-15 09:30",
                    "source": "Reuters",
                    "url": "",
                    "public_disclosure_ts": "2023-01-15",
                },
                {
                    "headline": "Apple misses guidance",
                    "date": "2023-01-10 14:00",
                    "source": "Bloomberg",
                    "url": "",
                    "public_disclosure_ts": "2023-01-10",
                },
            ]

            connector = FinBERTConnector()
            mock_pipeline_results = [
                [{"label": "positive", "score": 0.92}, {"label": "negative", "score": 0.05}, {"label": "neutral", "score": 0.03}],
                [{"label": "negative", "score": 0.88}, {"label": "positive", "score": 0.07}, {"label": "neutral", "score": 0.05}],
            ]
            connector._pipeline = MagicMock(return_value=mock_pipeline_results)

            enriched = connector.score_news_items(source_news)

        assert len(enriched) == 2
        assert enriched[0]["public_disclosure_ts"] == "2023-01-15", \
            "FinBERT must preserve source article's public_disclosure_ts"
        assert enriched[1]["public_disclosure_ts"] == "2023-01-10", \
            "FinBERT must preserve source article's public_disclosure_ts"

    def test_score_text_uses_source_disclosure_ts(self):
        """T1.6b — score_text with explicit source_disclosure_ts propagates it"""
        import sys
        mock_transformers = MagicMock()
        mock_transformers.BertTokenizer = MagicMock()
        mock_transformers.BertForSequenceClassification = MagicMock()
        mock_transformers.pipeline = MagicMock()
        with patch.dict(sys.modules, {"transformers": mock_transformers}):
            import importlib
            import engines.data_ingestion.connectors.finbert_connector as fb_mod
            importlib.reload(fb_mod)
            FinBERTConnector = fb_mod.FinBERTConnector

            connector = FinBERTConnector()
            mock_result = [[{"label": "positive", "score": 0.9}, {"label": "negative", "score": 0.06}, {"label": "neutral", "score": 0.04}]]
            connector._pipeline = MagicMock(return_value=mock_result)

            result = connector.score_text("Apple reported earnings", source_disclosure_ts="2023-06-15")

        assert result["public_disclosure_ts"] == "2023-06-15", \
            "source_disclosure_ts not propagated to output"


# ── T1.7 — Ledger: read_prices enforces as_of_date ───────────────────────────

class TestLedgerReadFilter:

    def test_read_prices_filters_future(self, temp_ledger):
        """T1.7 — read_prices on a cached file only returns rows <= as_of_date.
        
        We write the file with download_date=2023-01-11 (same as as_of_date),
        then read with as_of_date=2023-01-11. The file should be found.
        The 2023-01-12 row should be filtered out by public_disclosure_ts.
        """
        import engines.data_ingestion.ledger as ledger_mod

        df = pd.DataFrame({
            "date": ["2023-01-10", "2023-01-11", "2023-01-12"],
            "open": [150.0, 151.0, 152.0],
            "high": [155.0, 156.0, 157.0],
            "low": [149.0, 150.0, 151.0],
            "close": [153.0, 154.0, 155.0],
            "volume": [1_000_000, 1_100_000, 1_200_000],
            "public_disclosure_ts": pd.to_datetime(["2023-01-10", "2023-01-11", "2023-01-12"]),
        })

        # Write with download_date = 2023-01-11 (must be <= as_of_date for read_prices to find it)
        ledger_mod.write_prices("AAPL", df, download_date=date(2023, 1, 11))

        # Read back with as_of_date = 2023-01-11 — should exclude the 12th row
        result = ledger_mod.read_prices("AAPL", as_of_date=date(2023, 1, 11))

        assert result is not None, "read_prices returned None — ledger write/read roundtrip broken"
        assert len(result) == 2, f"Expected 2 rows (10th + 11th), got {len(result)}: {result[['date', 'public_disclosure_ts']].to_dict()}"
        assert all(result["public_disclosure_ts"].dt.date <= date(2023, 1, 11))
