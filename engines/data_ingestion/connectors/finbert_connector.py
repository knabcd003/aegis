"""
FinBERT Connector — NLP sentiment scoring for financial text.

This is a PROCESSOR connector. It takes text from other connectors
(news headlines, SEC filings, earnings transcripts) and returns sentiment scores.
Runs locally on CPU — no API key, no cost.

v6 update:
- score_news_items() and score_text() inherit public_disclosure_ts from the
  source item's public_disclosure_ts field. FinBERT does not have its own
  disclosure date — it inherits it from whatever source article it processes.
- The sentiment score reflects what was knowable on the source article's date.
"""
from typing import Dict, List, Optional, Any
from datetime import date, datetime

from engines.data_ingestion.base_connector import BaseConnector


class FinBERTConnector(BaseConnector):
    """
    Scores financial text for sentiment using FinBERT.
    Lazy-loads model on first use (~430MB, then cached locally).
    """

    MODEL_NAME = "ProsusAI/finbert"

    def __init__(self):
        self._pipeline = None  # Lazy loaded
        self._last_successful_fetch_ts: Optional[datetime] = None

    @property
    def name(self) -> str:
        return "finbert"

    @property
    def provides_prices(self) -> bool:
        return False

    @property
    def provides_fundamentals(self) -> bool:
        return False

    @property
    def provides_news(self) -> bool:
        return False  # It processes news, doesn't fetch it

    def _load_model(self):
        """Lazy load the FinBERT model (downloads ~430MB on first run)."""
        if self._pipeline is None:
            # Lazy imports of heavy dependencies — keeps module importable in tests
            # without triggering a 430MB download or requiring torch to be installed.
            from transformers import pipeline as hf_pipeline
            print(f"[{self.name}] Loading FinBERT model (first time may download ~430MB)...")
            self._pipeline = hf_pipeline(
                "text-classification",
                model=self.MODEL_NAME,
                tokenizer=self.MODEL_NAME,
                device=-1,      # CPU
                top_k=None,     # Return all class probabilities
            )
            print(f"[{self.name}] Model loaded successfully")

    # ── Core Sentiment Scoring ───────────────────────────────────────────

    def score_text(self, text: str, source_disclosure_ts: Optional[str] = None) -> Dict[str, Any]:
        """
        Score a single piece of text for financial sentiment.

        Args:
            text: Text to score (truncated to 512 tokens internally)
            source_disclosure_ts: ISO date string from the source article's
                public_disclosure_ts. If provided, propagated to the output.
                This is the date the sentiment was knowable, not today.

        Returns:
            {
                "text": "...",
                "sentiment": "positive" | "negative" | "neutral",
                "score": 0.92,
                "positive": 0.92, "negative": 0.03, "neutral": 0.05,
                "public_disclosure_ts": "2023-01-15"  # inherited from source
            }
        """
        self._load_model()
        truncated = text[:512]

        try:
            results = self._pipeline(truncated)
            scores = {r["label"]: round(r["score"], 4) for r in results[0]}
            best = max(results[0], key=lambda x: x["score"])

            self._last_successful_fetch_ts = datetime.utcnow()
            return {
                "text": text[:200],
                "sentiment": best["label"],
                "score": round(best["score"], 4),
                "positive": scores.get("positive", 0),
                "negative": scores.get("negative", 0),
                "neutral": scores.get("neutral", 0),
                # Inherit public_disclosure_ts from source — FinBERT has no timestamp of its own
                "public_disclosure_ts": source_disclosure_ts or date.today().isoformat(),
            }
        except Exception as e:
            print(f"[{self.name}] Error scoring text: {e}")
            return {
                "text": text[:200],
                "sentiment": "error",
                "score": 0,
                "positive": 0, "negative": 0, "neutral": 0,
                "public_disclosure_ts": source_disclosure_ts or date.today().isoformat(),
            }

    def score_batch(self, texts: List[str], source_disclosure_ts_list: Optional[List[Optional[str]]] = None) -> List[Dict[str, Any]]:
        """
        Score multiple texts in a batch.

        Args:
            texts: List of text to score
            source_disclosure_ts_list: Optional list of public_disclosure_ts strings
                (one per text). If provided, propagated to each output dict.
        """
        self._load_model()
        ts_list = source_disclosure_ts_list or [None] * len(texts)

        results = []
        batch_size = 32
        for i in range(0, len(texts), batch_size):
            batch = [t[:512] for t in texts[i:i + batch_size]]
            batch_ts = ts_list[i:i + batch_size]
            try:
                batch_results = self._pipeline(batch)
                for j, text_results in enumerate(batch_results):
                    scores = {r["label"]: round(r["score"], 4) for r in text_results}
                    best = max(text_results, key=lambda x: x["score"])
                    results.append({
                        "text": texts[i + j][:200],
                        "sentiment": best["label"],
                        "score": round(best["score"], 4),
                        "positive": scores.get("positive", 0),
                        "negative": scores.get("negative", 0),
                        "neutral": scores.get("neutral", 0),
                        "public_disclosure_ts": batch_ts[j] or date.today().isoformat(),
                    })
            except Exception as e:
                print(f"[{self.name}] Batch error at index {i}: {e}")
                for j in range(len(batch)):
                    results.append({
                        "text": texts[i + j][:200],
                        "sentiment": "error",
                        "score": 0,
                        "positive": 0, "negative": 0, "neutral": 0,
                        "public_disclosure_ts": batch_ts[j] or date.today().isoformat(),
                    })

        self._last_successful_fetch_ts = datetime.utcnow()
        return results

    def score_news_items(self, news_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Score a list of news items (from YFinance/Finnhub connector format).
        Adds sentiment fields to each news item dict.

        Critically: inherits public_disclosure_ts from each news item's own
        public_disclosure_ts field. The sentiment score has the same knowability
        date as the article it was derived from.
        """
        if not news_items:
            return []

        headlines = [item.get("headline", "") for item in news_items]
        # Inherit each article's public_disclosure_ts
        ts_list = [item.get("public_disclosure_ts") for item in news_items]
        scores = self.score_batch(headlines, source_disclosure_ts_list=ts_list)

        enriched = []
        for item, score in zip(news_items, scores):
            enriched_item = {**item}
            enriched_item["sentiment"] = score["sentiment"]
            enriched_item["sentiment_score"] = score["score"]
            enriched_item["sentiment_positive"] = score["positive"]
            enriched_item["sentiment_negative"] = score["negative"]
            enriched_item["sentiment_neutral"] = score["neutral"]
            # public_disclosure_ts is already in item — score inherits it, no overwrite
            enriched.append(enriched_item)

        return enriched

    # ── BaseConnector interface ──────────────────────────────────────────

    def get_prices(self, ticker: str, days: int = 30, interval: str = "1d",
                   as_of_date: Optional[date] = None):
        return None

    def get_fundamentals(self, ticker: str, as_of_date: Optional[date] = None):
        return None

    def get_news(self, ticker: str, days: int = 7, as_of_date: Optional[date] = None):
        return []

    def health_check(self) -> bool:
        try:
            result = self.score_text("Apple reported strong earnings")
            return result["sentiment"] in ("positive", "negative", "neutral")
        except Exception:
            return False
