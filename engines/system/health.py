import os
import time
import json
import requests
import psutil
from dotenv import load_dotenv
from typing import Dict, Any, List, Optional
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage

class HealthCheck:
    """
    Utility for verifying the system's readiness (API keys, Ollama, Models, System Resources).
    """
    
    REQUIRED_ENV_VARS = ["FINNHUB_API_KEY"]
    MEMORY_THRESHOLD_GB = 4.0
    COLD_START_MAX = 45.0
    WARM_MAX = 10.0
    
    def __init__(self, model: Optional[str] = None):
        load_dotenv()
        self.model = model
        
    def check_env(self) -> Dict[str, bool]:
        """Verify required environment variables."""
        status = {}
        for var in self.REQUIRED_ENV_VARS:
            val = os.getenv(var)
            status[var] = val is not None and len(val) > 0
        return status

    def check_memory(self) -> Dict[str, Any]:
        """Check available unified memory."""
        mem = psutil.virtual_memory()
        available_gb = mem.available / (1024**3)
        return {
            "ok": available_gb >= self.MEMORY_THRESHOLD_GB,
            "available_gb": round(available_gb, 2),
            "total_gb": round(mem.total / (1024**3), 2)
        }

    def check_ollama_daemon(self) -> bool:
        """Check if Ollama daemon is reachable."""
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            return response.status_code == 200
        except Exception:
            return False

    def check_model_pulled(self, model_name: str) -> bool:
        """Check if a specific model is pulled in Ollama."""
        try:
            response = requests.get("http://localhost:11434/api/tags")
            if response.status_code != 200:
                return False
            
            models = response.json().get("models", [])
            model_names = [m["name"] for m in models]
            # Handle both 'model' and 'model:latest' equivalence
            return model_name in model_names or f"{model_name}:latest" in model_names
        except Exception:
            return False

    def check_inference_health(self, model_name: str) -> Dict[str, Any]:
        """
        Perform a 2-stage dry-run inference to check for cold-start and warm-start latency.
        """
        llm = ChatOllama(model=model_name, temperature=0.0)
        
        # 1. Cold Start Run
        start_c = time.time()
        try:
            _ = llm.invoke([HumanMessage(content="hi")])
            latency_c = time.time() - start_c
        except Exception as e:
            return {"ok": False, "error": f"Cold start failed: {e}", "cold_latency": 0}
            
        # 2. Warm Start Run
        start_w = time.time()
        try:
            response = llm.invoke([HumanMessage(content="hi")])
            latency_w = time.time() - start_w
        except Exception as e:
            return {"ok": False, "error": f"Warm start failed: {e}", "cold_latency": round(latency_c, 2)}

        cold_ok = latency_c <= self.COLD_START_MAX
        warm_ok = latency_w <= self.WARM_MAX
        
        return {
            "ok": cold_ok and warm_ok,
            "cold_latency": round(latency_c, 2),
            "warm_latency": round(latency_w, 2),
            "response": response.content.strip(),
            "is_slow": not warm_ok,
            "error": None if (cold_ok and warm_ok) else f"Latency out of bounds (Cold: {round(latency_c, 1)}s, Warm: {round(latency_w, 1)}s)"
        }

    def run_all(self) -> Dict[str, Any]:
        """Execute all health checks."""
        results = {
            "environment": self.check_env(),
            "memory": self.check_memory(),
            "ollama_online": self.check_ollama_daemon(),
            "model_readiness": {},
            "inference": {}
        }
        
        model_name = self.model
        if model_name:
            model_pulled = self.check_model_pulled(model_name)
            results["model_readiness"] = {model_name: model_pulled}
            if model_pulled and results["ollama_online"]:
                results["inference"] = self.check_inference_health(model_name)
            else:
                results["inference"] = {"ok": False, "error": "Model not available or Ollama offline"}
                
        return results
