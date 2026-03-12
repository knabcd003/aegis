import asyncio
import json
import uuid
import sys

from api.routers.systems import generate_system, GenerateSystemRequest
from engines.simulation_loop.orchestrator import SimulationOrchestrator

async def run_test():
    print("1. Requesting generated config from API...")
    req = GenerateSystemRequest(
        thesis="Semiconductor capex and AI data center buildout lead to sustained revenue beats for NVDA and AMD.",
        trading_style="swing",
        risk_tolerance="conservative",
        diversification="concentrated"
    )
    res = await generate_system(req)
    config = res["config"]
    print(f"-> Generated Config ID: {config['config_id']}")
    print(f"-> Selected Connectors: {config['data_engine']['connectors']}")
    print(json.dumps(config, indent=2))
    
    print("\n2. Executing Quick Iteration via SimulationOrchestrator...")
    try:
        # Mocking the orchestrator run for the scope of the test script to ensure schema is valid
        # In a real quick iteration, it would execute LangGraph
        orchestrator = SimulationOrchestrator(
            db_path="./mlflow.db",
            data_dir="./data"
        )
        
        # Override the universe to be small for a fast test
        config["asset_universe"]["tickers"] = ["NVDA"]
        
        # Force a quick run
        results = await orchestrator.run_backtest(
            agent_config=config,
            start_date="2025-01-01",
            end_date="2025-01-05" 
        )
        print("-> Execution successful! Schema is valid.")
        
    except Exception as e:
        print(f"-> Execution FAILED: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(run_test())
