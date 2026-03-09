from typing import Dict, Any

class SignalGate:
    """
    Evaluates compiled fundamental signals against the provided configuration gate.
    """
    @staticmethod
    def evaluate(signals: Dict[str, Any], gate_config: Dict[str, Any]) -> bool:
        """
        Input: all engine outputs (dict) + gate config (dict)
        Output: True (gate passed) or False (no signal)
        
        Logs gate result + margin per condition (future use by Phase 2 Uncertainty Scorer).
        """
        if not gate_config:
            # If the gate is entirely empty, it passes immediately
            return True
            
        passed = True
        margin_per_condition = {}

        # 1. FinBERT Sentiment Gate
        if "finbert_above" in gate_config and gate_config["finbert_above"] is not None:
            threshold = gate_config["finbert_above"]
            score = signals.get("finbert_score", 0.0)
            margin = score - threshold
            margin_per_condition["finbert"] = margin
            if margin < 0:
                passed = False

        # 2. Earnings Revision Gate
        if "earnings_revision_direction" in gate_config and gate_config["earnings_revision_direction"]:
            required_dir = gate_config["earnings_revision_direction"]
            actual_dir = signals.get("earnings_revision", {}).get("direction", "flat")
            
            # Simple margin for boolean text match
            margin_per_condition["earnings_revision"] = 1.0 if actual_dir == required_dir else -1.0
            if actual_dir != required_dir:
                passed = False
                
        # 3. Insider Activity Gate
        if "insider_cluster" in gate_config and gate_config["insider_cluster"]:
             required_cluster = gate_config["insider_cluster"]
             # If required, check if cluster_buy is True
             actual_cluster = signals.get("insider_activity", {}).get("cluster_buy", False)
             margin_per_condition["insider_cluster"] = 1.0 if actual_cluster == required_cluster else -1.0
             if actual_cluster != required_cluster:
                 passed = False

        signals["_gate_margin"] = margin_per_condition
        return passed
