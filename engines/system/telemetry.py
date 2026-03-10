import time
import json
import os
from datetime import datetime
from typing import Dict, Any, List

class PipelineTelemetry:
    """
    Utility for tracking node-level performance and quality metrics within the agent mesh.
    """
    def __init__(self, log_dir: str = "debug/telemetry"):
        self.log_dir = log_dir
        os.makedirs(self.log_dir, exist_ok=True)
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = os.path.join(self.log_dir, f"pipeline_{self.session_id}.jsonl")
        self.events = []

    def log_node_execution(self, ticker: str, date: str, node_name: str, duration_sec: float, outcome: Dict[str, Any]):
        event = {
            "timestamp": datetime.now().isoformat(),
            "ticker": ticker,
            "date": date,
            "node": node_name,
            "duration_sec": round(float(duration_sec), 3),
            "outcome": outcome
        }
        with open(self.log_file, "a") as f:
            f.write(json.dumps(event) + "\n")
        self.events.append(event)

    def get_summary(self) -> str:
        if not self.events:
            return "No telemetry data collected."
        
        node_stats: Dict[str, Dict[str, Any]] = {}
        for e in self.events:
            n = str(e.get("node", "UNK"))
            if n not in node_stats:
                node_stats[n] = {"count": 0, "total_time": 0.0, "vetos": 0}
            node_stats[n]["count"] += 1
            
            # Type-safe access to duration_sec
            d = e.get("duration_sec", 0.0)
            if isinstance(d, (int, float)):
                node_stats[n]["total_time"] += float(d)
            
            outcome = e.get("outcome", {})
            if isinstance(outcome, dict) and outcome.get("risk_veto"):
                node_stats[n]["vetos"] += 1
        
        summary = "Pipeline Performance Summary:\n"
        for n, stats in node_stats.items():
            avg_time = stats["total_time"] / stats["count"]
            summary += f"- {n}: {stats['count']} calls, Avg Latency: {avg_time:.2f}s"
            if stats["vetos"] > 0:
                summary += f", Vetos: {stats['vetos']}"
            summary += "\n"
        return summary

# Global instance for easy access
monitor = PipelineTelemetry()
