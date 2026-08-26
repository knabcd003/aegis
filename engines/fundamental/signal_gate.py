from typing import Dict, Any

class SignalGate:
    """
    Evaluates compiled fundamental signals against the provided configuration gate.
    """
    @staticmethod
    def evaluate(signals: Dict[str, Any], gate_config: Dict[str, Any]) -> tuple[bool, bool]:
        """
        Input: all engine outputs (dict) + gate config (dict)
        Output: (entry_passed: bool, exit_passed: bool)
        
        Logs gate result + margin per condition (future use by Phase 2 Uncertainty Scorer).
        """
        if not gate_config:
            # If the gate is entirely empty, it passes immediately
            return True, False
            
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

        # 4. Technical Gate
        if gate_config.get("type", "") == "technical":
            entry_type = gate_config.get("entry")
            exit_type = gate_config.get("exit")
            fast = signals.get("fast_sma", 0.0)
            slow = signals.get("slow_sma", 0.0)
            p_fast = signals.get("prev_fast_sma", 0.0)
            p_slow = signals.get("prev_slow_sma", 0.0)
            
            entry_passed = False
            exit_passed = False
            
            if entry_type == "fast_crosses_above_slow" or not entry_type or entry_type == "3_month_trailing_total_return":
                entry_passed = (fast > slow and p_fast <= p_slow) or (fast > slow and p_fast == 0.0)
            
            if exit_type == "fast_crosses_below_slow" or not exit_type or "rank" in str(exit_type):
                exit_passed = (fast < slow and p_fast >= p_slow)
                
            return entry_passed, exit_passed

        signals["_gate_margin"] = margin_per_condition
        return passed, not passed
