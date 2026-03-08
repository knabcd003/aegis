import os
from dotenv import load_dotenv

from engines.sandbox.orchestrator import SandboxOrchestrator

def run_sandbox_test():
    print("=" * 60)
    print("🚀 INITIALIZING MLFLOW SANDBOX ORCHESTRATOR TEST")
    print("=" * 60)
    
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ERROR: ANTHROPIC_API_KEY is not set.")
        return

    print("\n[System] Booting Sandbox Orchestrator & Optuna Engine...")
    try:
        orchestrator = SandboxOrchestrator(experiment_name="Aegis_Phase3_Final_Test")
    except Exception as e:
        print(f"Failed to initialize Sandbox Orchestrator: {e}")
        return

    print("\n[Test] Running 2-Trial Optuna Hyperparameter Sweep...")
    print(" > The Orchestrator will vary the VPIN threshold and execute the LangGraph.")
    print(" > All execution logic will be internally tracked by MLflow SQLite.")
    
    try:
        study = orchestrator.run_sweep(n_trials=2)
        
        print("\n" + "=" * 50)
        print("📊 OPTUNA SWEEP RESULTS:")
        print("=" * 50)
        print(f"Best Configuration Found:")
        print(f" > VPIN Threshold: {study.best_params['vpin_threshold']}")
        print(f" > Simulated PnL:  {study.best_value}%")
        
        print("\n✅ SUCCESS: The Sandbox successfully executed automated sweeps and tracked them via Optuna.")
        print(" > Local MLflow DB saved to 'mlflow.db'.")
        
    except Exception as e:
        print(f"\n❌ Sandbox sweep failed: {e}")

if __name__ == "__main__":
    load_dotenv()
    run_sandbox_test()
