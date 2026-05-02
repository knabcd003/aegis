import sqlite3
import json
import os
from typing import Optional, Dict, Any, List
from pathlib import Path
from api.services.crypto import encrypt_key, decrypt_key

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DB_PATH = PROJECT_ROOT / "aegis.db"
ENV_PATH = PROJECT_ROOT / ".env"

class UserProfileService:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(UserProfileService, cls).__new__(cls)
            cls._instance._init_db()
        return cls._instance

    def _init_db(self):
        """Initialize SQLite database with required tables."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_profiles (
                user_id TEXT PRIMARY KEY,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                provider_config TEXT
            )
            ''')
            
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_api_keys (
                user_id TEXT,
                service_name TEXT,
                encrypted_key TEXT,
                PRIMARY KEY (user_id, service_name),
                FOREIGN KEY (user_id) REFERENCES user_profiles(user_id)
            )
            ''')
            
            conn.commit()

    def _get_connection(self):
        return sqlite3.connect(str(DB_PATH))

    def get_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT provider_config FROM user_profiles WHERE user_id = ?', (user_id,))
            row = cursor.fetchone()
            if row:
                config_str = row[0]
                if config_str:
                    return json.loads(config_str)
                return {}
            return None

    def set_api_key(self, user_id: str, service: str, key: str) -> None:
        if not key:
            # If empty key is passed, we might want to delete it or store empty. We will delete.
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM user_api_keys WHERE user_id = ? AND service_name = ?', (user_id, service))
                conn.commit()
            return

        encrypted = encrypt_key(key)
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
            INSERT INTO user_api_keys (user_id, service_name, encrypted_key)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id, service_name) DO UPDATE SET encrypted_key = excluded.encrypted_key
            ''', (user_id, service, encrypted))
            conn.commit()

    def get_api_key(self, user_id: str, service: str) -> Optional[str]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT encrypted_key FROM user_api_keys WHERE user_id = ? AND service_name = ?', (user_id, service))
            row = cursor.fetchone()
            if row and row[0]:
                return decrypt_key(row[0])
            return None

    def get_provider_config(self, user_id: str) -> Dict[str, Any]:
        profile = self.get_profile(user_id)
        if profile is not None:
            return profile
            
        # Default empty config
        return {
            "providers": [],
            "role_assignments": {},
            "settings": {
                "context_size_threshold_tokens": 50000,
                "context_override_provider": "gemini-2.5-flash",
                "exclude_providers": ["deepseek/*"],
                "severely_degraded_fallback_depth": 2,
            }
        }

    def save_provider_config(self, user_id: str, config: Dict[str, Any]) -> None:
        config_str = json.dumps(config)
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
            INSERT INTO user_profiles (user_id, provider_config)
            VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE SET provider_config = excluded.provider_config
            ''', (user_id, config_str))
            conn.commit()


def create_default_user():
    """
    Creates the implicit single user.
    Seeds API keys from .env for development.
    In production, user enters keys through setup UI.
    """
    service = UserProfileService()
    
    # Check if default user already exists
    if service.get_profile("default") is not None:
        return  # Already initialized
        
    # Save a default config to create the user profile
    service.save_provider_config("default", {
        "providers": [],
        "role_assignments": {},
        "settings": {
            "context_size_threshold_tokens": 50000,
            "context_override_provider": "gemini-2.5-flash",
            "exclude_providers": ["deepseek/*"],
            "severely_degraded_fallback_depth": 2,
        }
    })
    
    # Reload .env into memory if needed
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=ENV_PATH)
    
    # Seed LLM keys from environment
    for provider, env_var in [
        ("groq",        "GROQ_API_KEY"),
        ("gemini",      "GEMINI_API_KEY"),
        ("anthropic",   "ANTHROPIC_API_KEY"),
        ("openrouter",  "OPENROUTER_API_KEY"),
        ("openai",      "OPENAI_API_KEY"),
        ("cerebras",    "CEREBRAS_API_KEY"),
    ]:
        key = os.getenv(env_var)
        if key:
            service.set_api_key("default", provider, key)
    
    # Seed data keys from environment
    for external_service, env_var in [
        ("finnhub",     "FINNHUB_API_KEY"),
        ("alpaca_key",  "ALPACA_API_KEY"),
        ("alpaca_secret", "ALPACA_SECRET_KEY"),
        ("fred",        "FRED_API_KEY"),
        ("sec_edgar",   "SEC_EDGAR_EMAIL"),
    ]:
        key = os.getenv(env_var)
        if key:
            service.set_api_key("default", external_service, key)

    # Optional: we could load llm_providers.yaml and migrate it into the db as well,
    # but the instructions say the test user seeds from .env for keys. We can seed the config
    # from the existing yaml if it exists to preserve the test setup.
    YAML_PATH = PROJECT_ROOT / "config" / "llm_providers.yaml"
    if YAML_PATH.exists():
        import yaml
        with open(YAML_PATH, "r") as f:
            legacy_config = yaml.safe_load(f)
            if legacy_config:
                service.save_provider_config("default", legacy_config)
