import os
import argparse
import mlflow
import json
from datetime import datetime

from config.manager import ConfigManager
from engines.sandbox.orchestrator import SandboxOrchestrator
from engines.analyst.improvement_agent import ImprovementAgent

def run_loop(base_config_path: str, iterations: int):
    # Initialize components
    orchestrator = SandboxOrchestrator(script_path="scripts/run_subprocess_backtest.py")
    agent = ImprovementAgent(provider="ollama", model="qwen2.5:3b")
    
    # Load base config
    from config.schema import AegisConfig
    current_config = ConfigManager.load(base_config_path)
    
    print("\n" + "="*80)
    print(f"🚀 STARTING AUTONOMOUS OPTIMIZATION LOOP ({iterations} ITERATIONS)")
    print(f"Base Configuration: {base_config_path}")
    print("="*80 + "\n")
    
    best_sharpe = -999.0
    best_config = current_config.model_dump()
    
    for i in range(1, iterations + 1):
        print(f"\n--- [Iteration {i}/{iterations}] ---")
        
        # 1. Generate run ID for this iteration
        unique_run_id = f"opt_loop_{datetime.now().strftime('%Y%m%d_%H%M%S')}_iter{i}"
        
        # We need to construct a fresh config object since Pydantic models are mostly immutable
        # or we just re-instantiate from the dict
        run_config_dict = current_config.model_dump()
        run_config_dict["config_id"] = unique_run_id
        current_config = AegisConfig(**run_config_dict)
        
        # 2. Run Sandbox (Subprocess)
        print("⏳ Running Backtest Sandbox...")
        try:
            run_id = orchestrator.run_simulation(current_config)
        except Exception as e:
            print(f"❌ Subprocess Crashed: {e}")
            break
            
        # 3. Fetch Metrics from MLflow to pass to Agent
        mlflow.set_tracking_uri("sqlite:///mlflow.db")
        run = mlflow.get_run(run_id)
        metrics = run.data.metrics
        
        opt_sharpe = metrics.get("opt_sharpe", 0.0)
        opt_return = metrics.get("opt_total_return", 0.0)
        
        print("\n📈 [Live Iteration Results]")
        print(f"   Sharpe (Train): {opt_sharpe:.2f}")
        print(f"   Return (Train): {opt_return:.2%}")
        
        # Track best config
        if opt_sharpe > best_sharpe:
            best_sharpe = opt_sharpe
            best_config = current_config.model_dump()
            print("   ⭐ NEW BEST CONFIGURATION ⭐")

        # Skip improvement on the last iteration
        if i == iterations:
            break
            
        print("\n🧠 Invoking Improvement Agent...")
        trace_path = f"debug/traces/recommendation_trace_{run_id}.jsonl"
        
        try:
            # 4. Agent proposes mutation based on traces & metrics
            proposal = agent.analyze_run(
                config_dump=current_config.model_dump(),
                metrics=metrics,
                trace_path=trace_path
            )
            
            mut = proposal.mutation
            print("\n💡 [Agent Proposal]")
            print(f"   Parameter: {mut.target_parameter}")
            print(f"   Change:    {mut.current_value} -> {mut.proposed_value}")
            print(f"   Rationale: {mut.rationale}")
            
            # 5. Apply Mutation
            new_config_dict = agent.apply_mutation(current_config.model_dump(), proposal)
            
            # Re-validate with Pydantic
            current_config = AegisConfig(**new_config_dict)
            
        except Exception as e:
            print(f"⚠️ Agent failed to propose valid mutation: {e}")
            print("Falling back to random mutation or aborting...")
            break

    print("\n" + "="*80)
    print("🏁 OPTIMIZATION LOOP COMPLETE")
    print(f"Best Sharpe achieved (Train): {best_sharpe:.2f}")
    
    # Save the best config
    output_path = "config/templates/optimized_best.json"
    with open(output_path, "w") as f:
        json.dump(best_config, f, indent=4)
        
    print(f"Saved optimized template to: {output_path}")
    print("="*80 + "\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config/templates/debug_aapl_v1.json")
    parser.add_argument("--iterations", type=int, default=3)
    args = parser.parse_args()
    
    run_loop(args.config, args.iterations)
