import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class QuotaTracker:
    def __init__(self, providers: Dict[str, Any], persist_path: str = "data/llm_quota.json"):
        """
        providers: Dict of provider_id -> complete provider config dict
        (from the yaml file).
        """
        self.persist_path = persist_path
        self._usage: Dict[str, int] = {}
        self._utc_date: str = ""
        self.providers = providers
        self._load()

    def _get_current_utc_date(self) -> str:
        return datetime.utcnow().date().isoformat()

    def _check_and_reset_midnight(self) -> None:
        """If it's a new UTC day, reset usage to 0."""
        current_date = self._get_current_utc_date()
        if self._utc_date != current_date:
            logger.info(f"Midnight UTC reset triggered. Rolling over to {current_date}.")
            self._usage = {p_id: 0 for p_id in self.providers}
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

    def get_limit(self, model: str) -> Optional[int]:
        if model not in self.providers:
            return 0
        limits = self.providers[model].get("limits", {})
        return limits.get("rpd")

    def is_exhausted(self, model: str) -> bool:
        self._check_and_reset_midnight()
        limit = self.get_limit(model)
        if limit is None:
            return False  # Unlimited
        return self._usage.get(model, 0) >= limit

    def increment(self, model: str, amount: int = 1) -> None:
        self._check_and_reset_midnight()
        self._usage[model] = self._usage.get(model, 0) + amount
        self._save()

    def mark_exhausted(self, model: str) -> None:
        """Force a provider to skip iteration fallback by saturating its limit."""
        self._check_and_reset_midnight()
        limit = self.get_limit(model)
        if limit is not None:
            self._usage[model] = limit
            self._save()

    def can_accommodate(self, model: str, amount: int = 1) -> bool:
        """Check if quota remains before initiating a physical HTTP dispatch."""
        self._check_and_reset_midnight()
        limit = self.get_limit(model)
        if limit is None:
            return True
        return (self._usage.get(model, 0) + amount) <= limit
