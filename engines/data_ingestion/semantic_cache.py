"""
Semantic Cache Layer.

A local SQLite-backed cache designed specifically to bypass LLM inference
bottlenecks during Optuna hyperparameter sweeps and headless backtesting.

Instead of asking Qwen 2.5 to read the same 10-K a thousand times during
a parameter search, we hash the `[system_prompt + document_text + query]`.
If that exact combination exists in the cache, we return the cached JSON
instead of spinning up the GPU.
"""

import sqlite3
import hashlib
import json
import logging
from typing import Optional, Any
from pathlib import Path

class SemanticCache:
    def __init__(self, db_path: str = "data/semantic_cache.db"):
        """Initializes the SQLite cache database for LLM inference."""
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(self.__class__.__name__)
        self._init_db()

    def _init_db(self):
        """Creates the cache table if it doesn't exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS llm_cache (
                prompt_hash TEXT PRIMARY KEY,
                model_name TEXT,
                response_text TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()

    def _generate_hash(self, model_name: str, system_prompt: str, user_prompt: str) -> str:
        """
        Creates a deterministic SHA-256 hash for the given LLM parameters.
        Includes the model name to prevent collisions if we swap from Qwen to Llama.
        """
        raw_string = f"{model_name}||{system_prompt}||{user_prompt}"
        return hashlib.sha256(raw_string.encode('utf-8')).hexdigest()

    def get_cached_response(self, model_name: str, system_prompt: str, user_prompt: str) -> Optional[str]:
        """
        Checks the SQLite database for a pre-computed response to this exact prompt.
        """
        prompt_hash = self._generate_hash(model_name, system_prompt, user_prompt)
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT response_text FROM llm_cache WHERE prompt_hash = ?
            ''', (prompt_hash,))
            result = cursor.fetchone()
            conn.close()
            
            if result:
                self.logger.debug(f"[SemanticCache HIT] Model: {model_name}")
                return result[0]
            
            self.logger.debug(f"[SemanticCache MISS] Model: {model_name}")
            return None
            
        except sqlite3.Error as e:
            self.logger.error(f"Semantic Cache DB Error (Read): {e}")
            return None

    def save_response(self, model_name: str, system_prompt: str, user_prompt: str, response_text: str):
        """
        Saves a successful LLM inference response to the cache for future use.
        """
        prompt_hash = self._generate_hash(model_name, system_prompt, user_prompt)
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO llm_cache (prompt_hash, model_name, response_text)
                VALUES (?, ?, ?)
            ''', (prompt_hash, model_name, response_text))
            conn.commit()
            conn.close()
            self.logger.debug(f"[SemanticCache SAVED] Model: {model_name}")
        except sqlite3.Error as e:
            self.logger.error(f"Semantic Cache DB Error (Write): {e}")

    def clear_cache(self):
        """Wipes the entire cache. Use when doing a hard reset of an experiment."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('DELETE FROM llm_cache')
            conn.commit()
            conn.close()
            self.logger.info("Semantic Cache cleared.")
        except sqlite3.Error as e:
            self.logger.error(f"Semantic Cache DB Error (Clear): {e}")
