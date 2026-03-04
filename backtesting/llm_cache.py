"""
LLM Response Cache — Deterministic caching for LLM thesis generation.
First call hits the model; subsequent calls with same input return cached response.
Eliminates LLM costs on backtest re-runs.
"""
import os
import json
import hashlib
from typing import Optional

CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "cache")
CACHE_FILE = os.path.join(CACHE_DIR, "thesis_cache.json")


class LLMCache:
    """
    Simple hash-based cache for LLM responses.
    Key = SHA-256 hash of the full prompt string.
    Value = the raw LLM response text.
    """

    def __init__(self):
        os.makedirs(CACHE_DIR, exist_ok=True)
        self._cache = self._load()

    def _load(self) -> dict:
        if os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {}
        return {}

    def _save(self):
        with open(CACHE_FILE, "w") as f:
            json.dump(self._cache, f, indent=2)

    @staticmethod
    def _hash_prompt(prompt: str) -> str:
        return hashlib.sha256(prompt.encode("utf-8")).hexdigest()

    def get(self, prompt: str) -> Optional[str]:
        """Returns cached response if it exists, else None."""
        key = self._hash_prompt(prompt)
        return self._cache.get(key)

    def put(self, prompt: str, response: str):
        """Stores a response in the cache."""
        key = self._hash_prompt(prompt)
        self._cache[key] = response
        self._save()

    def has(self, prompt: str) -> bool:
        return self._hash_prompt(prompt) in self._cache

    def stats(self) -> dict:
        return {
            "cached_responses": len(self._cache),
            "cache_file": CACHE_FILE,
        }

    def clear(self):
        self._cache.clear()
        self._save()
