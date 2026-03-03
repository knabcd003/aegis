import json
import os
from typing import Dict, Any

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config", "user_preferences.json")

class ConfigManager:
    @staticmethod
    def load_config() -> Dict[str, Any]:
        """Loads the user preferences from the JSON config."""
        if not os.path.exists(CONFIG_PATH):
            return {
                "philosophy": "value",
                "max_pe_ratio": 15,
                "sectors": ["tech", "healthcare"],
                "risk_tolerance": "moderate",
                "max_position_size_pct": 0.10,
                "deployment_amount": 50000
            }
            
        with open(CONFIG_PATH, "r") as f:
            return json.load(f)
            
    @staticmethod
    def save_config(new_config: Dict[str, Any]) -> bool:
        """Saves updated user preferences to the JSON config."""
        try:
            with open(CONFIG_PATH, "w") as f:
                json.dump(new_config, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False
