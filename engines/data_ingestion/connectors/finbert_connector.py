"""
FinBERT Connector — NLP sentiment scoring for financial text.

This is a PROCESSOR connector, not a data source. It takes text from other
connectors (news headlines, SEC filings, earnings transcripts) and returns
sentiment scores. Runs locally on CPU — no API key, no cost.

Uses the ProsusAI/finbert model from Hugging Face.
"""
import torch
from typing import Dict, List, Optional, Any
from transformers import BertTokenizer, BertForSequenceClassification, pipeline

from engines.data_ingestion.base_connector import BaseConnector


class FinBERTConnector(BaseConnector):
    """
    Scores financial text for sentiment using FinBERT.
    Lazy-loads model on first use (~500MB download, then cached).
    """

    MODEL_NAME = "ProsusAI/finbert"

    def __init__(self):
        self._pipeline = None  # Lazy loaded

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
        """Lazy load the FinBERT model (downloads ~500MB on first run)."""
        if self._pipeline is None:
            print(f"[{self.name}] Loading FinBERT model (first time may download ~500MB)...")
            self._pipeline = pipeline(
                "text-classification",
                model=self.MODEL_NAME,
                tokenizer=self.MODEL_NAME,
                device=-1,  # CPU
                top_k=None,  # Return all class probabilities
            )
            print(f"[{self.name}] Model loaded successfully")

    # ── Core Sentiment Scoring ───────────────────────────────────────────

    def score_text(self, text: str) -> Dict[str, Any]:
        """
        Score a single piece of text for financial sentiment.

        Returns:
            {
                "text": "Apple beats Q4 estimates...",
                "sentiment": "positive",
                "score": 0.92,
                "positive": 0.92,
                "negative": 0.03,
                "neutral": 0.05
            }
        """
        self._load_model()

        # FinBERT has a 512 token limit — truncate if needed
        truncated = text[:512]

        try:
            results = self._pipeline(truncated)

            # results is [[{label, score}, ...]] — extract probabilities
            scores = {r["label"]: round(r["score"], 4) for r in results[0]}

            best = max(results[0], key=lambda x: x["score"])

            return {
                "text": text[:200],  # Keep a preview
                "sentiment": best["label"],
                "score": round(best["score"], 4),
                "positive": scores.get("positive", 0),
                "negative": scores.get("negative", 0),
                "neutral": scores.get("neutral", 0),
            }
        except Exception as e:
            print(f"[{self.name}] Error scoring text: {e}")
            return {
                "text": text[:200],
                "sentiment": "error",
                "score": 0,
                "positive": 0,
                "negative": 0,
                "neutral": 0,
            }

    def score_batch(self, texts: List[str]) -> List[Dict[str, Any]]:
        """
        Score multiple texts in a batch (more efficient than individual calls).

        Returns list of sentiment dicts, one per input text.
        """
        self._load_model()

        results = []
        # Process in chunks of 32 to manage memory
        batch_size = 32
        for i in range(0, len(texts), batch_size):
            batch = [t[:512] for t in texts[i:i + batch_size]]
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
                    })
            except Exception as e:
                print(f"[{self.name}] Batch error at index {i}: {e}")
                for j in range(len(batch)):
                    results.append({
                        "text": texts[i + j][:200],
                        "sentiment": "error",
                        "score": 0,
                        "positive": 0,
                        "negative": 0,
                        "neutral": 0,
                    })

        return results

    def score_news_items(self, news_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Score a list of news items (from yfinance/Finnhub connector format).
        Adds sentiment fields to each news item dict.
        """
        if not news_items:
            return []

        headlines = [item.get("headline", "") for item in news_items]
        scores = self.score_batch(headlines)

        enriched = []
        for item, score in zip(news_items, scores):
            enriched_item = {**item}
            enriched_item["sentiment"] = score["sentiment"]
            enriched_item["sentiment_score"] = score["score"]
            enriched_item["sentiment_positive"] = score["positive"]
            enriched_item["sentiment_negative"] = score["negative"]
            enriched_item["sentiment_neutral"] = score["neutral"]
            enriched.append(enriched_item)

        return enriched

    # ── BaseConnector interface (not a data source) ──────────────────────

    def get_prices(self, ticker: str, days: int = 30):
        return None

    def get_fundamentals(self, ticker: str):
        return None

    def get_news(self, ticker: str, days: int = 7):
        return []

    def health_check(self) -> bool:
        """Check if model loads and can score text."""
        try:
            result = self.score_text("Apple reported strong earnings")
            return result["sentiment"] in ("positive", "negative", "neutral")
        except Exception:
            return False
