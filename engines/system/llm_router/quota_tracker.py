"""
Quota Tracker for the LLM Router.

Persists to JSON with a `utc_date` field. On load or increment, if the 
current UTC date does not match the stored `utc_date`, it zeros out usage 
and updates the date. This ensures pristine tracking across process restarts 
or machine reboots.
"""
import os
import json
import logging
from datetime import datetime
from typing import Dict

logger = logging.getLogger(__name__)

# Hardcoded daily limits from the blueprint
DEFAULT_LIMITS = {
    "local/qwen3:8b": float('inf'),        # unlimited
    "groq/llama-4-scout": 1000,
    "groq/qwen3-32b": 1000,
    "groq/kimi-k2": 1000,
    "groq/gpt-oss-120b": 1000,
    "gemini-2.5-flash": 500,
    "openrouter/:free": 200,               # shared limit pool
    "claude-sonnet-4-6": 200,              # using $20 proxy limit for calls
}


class QuotaTracker:
    def __init__(self, persist_path: str = "data/llm_quota.json"):
        self.persist_path = persist_path
        self._usage: Dict[str, int] = {}
        self._utc_date: str = ""
        self._load()

    def _get_current_utc_date(self) -> str:
        return datetime.utcnow().date().isoformat()

    def _check_and_reset_midnight(self) -> None:
        """If it's a new UTC day, reset usage to 0."""
        current_date = self._get_current_utc_date()
        if self._utc_date != current_date:
            logger.info(f"Midnight UTC reset triggered. Rolling over to {current_date}.")
            self._usage = {model: 0 for model in DEFAULT_LIMITS}
            self._utc_date = current_date
            self._save()

    def _load(self) -> None:
        if os.path.exists(self.persist_path):
            try:
                with open(self.persist_path, "r") as f:
                    data = json.load(f)
                self._utc_date = data.get("utc_date", "")
                self._usage = data.get("usage", {})
            except (json.JSONDecodeError, IOError) as e:
                logger.error(f"Failed to load quota from {self.persist_path}: {e}")
                self._usage = {}
                self._utc_date = ""

        # Check for midnight pass
        self._check_and_reset_midnight()

    def _save(self) -> None:
        os.makedirs(os.path.dirname(self.persist_path) or ".", exist_ok=True)
        data = {
            "utc_date": self._utc_date,
            "usage": self._usage,
        }
        with open(self.persist_path, "w") as f:
            json.dump(data, f, indent=2)

    def get_quota(self, model: str) -> int:
        self._check_and_reset_midnight()
        return self._usage.get(model, 0)

    def is_exhausted(self, model: str) -> bool:
        self._check_and_reset_midnight()
        limit = DEFAULT_LIMITS.get(model, 0)
        return self._usage.get(model, 0) >= limit

    def increment(self, model: str, amount: int = 1) -> None:
        self._check_and_reset_midnight()
        self._usage[model] = self._usage.get(model, 0) + amount
        self._save()
