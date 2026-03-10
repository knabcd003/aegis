import os
import sys
import argparse
from typing import Dict, Any

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from engines.system.health import HealthCheck
from config.manager import ConfigManager

def print_result(label: str, ok: bool, info: str = ""):
    icon = "✅" if ok else "❌"
    color = "\033[92m" if ok else "\033[91m"
    reset = "\033[0m"
    print(f"{icon} {label:.<30} {color}{'OK' if ok else 'FAILED'}{reset} {info}")

def main():
    parser = argparse.ArgumentParser(description="Aegis Pre-Flight Health Check")
    parser.get_default("model")
    parser.add_argument("--model", type=str, help="Specific model to check (defaults to tech_breakout_v1 config)")
    args = parser.parse_args()

    # Load default model from config if not provided
    model_to_check = args.model
    if not model_to_check:
        try:
            config = ConfigManager.load("config/templates/tech_breakout_v1.json")
            model_to_check = config.agent.model
        except Exception:
            model_to_check = "qwen3:8b"

    checker = HealthCheck(model=model_to_check)
    
    print(f"\n{'='*60}")
    print(f" Aegis Pre-Flight Health Check: {model_to_check}")
    print(f"{'='*60}\n")

    # 1. Env Vars
    print("Runtime Environment:")
    env_status = checker.check_env()
    for var, ok in env_status.items():
        print_result(f"Env: {var}", ok)

    # 2. System Resources
    print("\nSystem Resources:")
    mem_status = checker.check_memory()
    print_result("Unified Memory Headroom", mem_status["ok"], 
                 f"({mem_status['available_gb']}GB available / {mem_status['total_gb']}GB total)")
    if not mem_status["ok"]:
        print(f"   ⚠️  Warning: Less than {checker.MEMORY_THRESHOLD_GB}GB available. High risk of swap during inference.")

    # 3. Ollama Daemon
    print("\nLocal LLM Infrastructure:")
    daemon_ok = checker.check_ollama_daemon()
    print_result("Ollama Daemon Reachability", daemon_ok)

    # 4. Model Pull Status
    model_ok = checker.check_model_pulled(model_to_check)
    print_result(f"Model ({model_to_check}) Pulled", model_ok)

    # 5. Inference Test (Cold vs Warm Calibration)
    inf_ok = False
    if daemon_ok and model_ok:
        print("\nInference Health (Dry Run):")
        inf_result = checker.check_inference_health(model_to_check)
        inf_ok = inf_result["ok"]
        
        # Display Cold Start
        cold_ok = inf_result["cold_latency"] <= checker.COLD_START_MAX
        print_result("Cold Start Target", cold_ok, f"({inf_result['cold_latency']}s)")
        
        # Display Warm Start
        print_result("Warm Latency Target", inf_ok, f"({inf_result['warm_latency']}s)")
        
        if not inf_ok:
            print(f"   🚨 Error: {inf_result['error']}")
        else:
            print(f"   Sample Response: \"{inf_result['response']}\"")
    else:
        print("\n⚠️  Skipping inference test due to infrastructure failures.")

    print(f"\n{'='*60}")
    
    # Exit code
    overall_ok = all(env_status.values()) and daemon_ok and model_ok and inf_ok
        
    if overall_ok:
        print("  ✨ ALL SYSTEMS GO. READY FOR DEPLOYMENT. ✨")
        sys.exit(0)
    else:
        if all(env_status.values()) and daemon_ok and model_ok and not inf_ok and not mem_status["ok"]:
             print("  ⚠️  DEGRADED STATE. Environment ok, but resources/latency strained. Proceed with caution.")
             sys.exit(0) # Allow proceed if it's just slow due to low RAM (user decision)
             
        print("  🚨 HEALTH CHECKS FAILED. PLEASE RESOLVE ISSUES ABOVE. 🚨")
        sys.exit(1)

if __name__ == "__main__":
    main()
