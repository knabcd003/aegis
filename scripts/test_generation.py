import asyncio
import json
import uuid
import sys
import os

from api.routers.systems import generate_system, GenerateSystemRequest

async def run_test():
    try:
        print("1. Requesting generated config from API logic...")
        req = GenerateSystemRequest(
            thesis="Semiconductor capex and AI data center buildout lead to sustained revenue beats for NVDA and AMD.",
            trading_style="swing",
            risk_tolerance="conservative",
            diversification="concentrated"
        )
        res = await generate_system(req)
        config = res["config"]
        print(f"-> Generated Config ID: {config['config_id']}")
        
        print("\n2. Simulating Schema Validation Execution...")
        
        # We don't have the simulation_loop built yet, but we have the endpoints
        # Let's verify the generated config doesn't violate basic assumptions
        assert "data_engine" in config
        assert "quant_engine" in config
        assert "analyst_engine" in config
        assert config["quant_engine"]["vpin"]["toxicity_threshold"] == 0.65 # Conservative enforce
        print("-> Execution successful! Schema is valid mapping to blueprint constraints.")
        
    except Exception as e:
        print(f"-> Execution FAILED: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(run_test())
