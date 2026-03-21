import os
import json
import logging
from typing import Dict, Any, List
import datetime

logger = logging.getLogger(__name__)

class ClaudeBudgetTracker:
    """
    Persistently tracking Claude API spend across process restarts to
    protect the physical bill from breaching predefined boundaries.
    """
    def __init__(self, storage_path: str = "data/claude_budget.json"):
        self.storage_path = storage_path
        self.state = self._load_state()

    def _load_state(self) -> Dict[str, Any]:
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "r") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load Claude budget state, resetting to $0.0: {e}")
                
        # Initialize default
        state = {
            "total_spent_usd": 0.0,
            "calls": []
        }
        self._save_state(state)
        return state

    def _save_state(self, state: Dict[str, Any]) -> None:
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
            with open(self.storage_path, "w") as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to persist Claude budget state: {e}")

    def current_spend(self) -> float:
        return self.state.get("total_spent_usd", 0.0)

    def can_accommodate(self, budget_limit_usd: float) -> bool:
        """
        Enforce a strict 99% boundary of the absolute limit.
        """
        if budget_limit_usd <= 0:
            return False
        return self.current_spend() < (budget_limit_usd * 0.99)

    def log_call(self, cost: float, prompt_tokens: int, completion_tokens: int) -> None:
        """
        Increment the tracker and explicitly commit to JSON disk storage.
        """
        self.state["total_spent_usd"] += cost
        
        call_record = {
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "cost_usd": cost,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens
        }
        self.state.setdefault("calls", []).append(call_record)
        
        # Keep only the last 1000 calls to prevent file bloat
        if len(self.state["calls"]) > 1000:
            self.state["calls"] = self.state["calls"][-1000:]
            
        self._save_state(self.state)
        logger.info(f"Claude Call Logged: ${cost:.5f}. Running Total: ${self.current_spend():.3f}")
