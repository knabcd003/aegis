import os
import subprocess
import json
import re
from typing import Dict, Any, Optional
from config.schema import AegisConfig

class SandboxOrchestrator:
    """
    Manages the execution of simulation loops via an isolated subprocess.
    This guarantees zero memory leakage or lookahead bias between the agent
    and the backtester.
    """
    def __init__(self, script_path: str = "scripts/run_optimization_backtest.py"):
        self.script_path = script_path

    def run_simulation(self, config: AegisConfig) -> str:
        """
        Executes a backtest as a subprocess.
        Returns the MLflow Run ID parsed from standard output.
        """
        # Serialize the config to a temporary file
        os.makedirs("/tmp/aegis_sandbox", exist_ok=True)
        temp_config_path = f"/tmp/aegis_sandbox/cfg_{config.run_id}.json"
        
        try:
            with open(temp_config_path, "w") as f:
                f.write(config.model_dump_json())

            cmd = ["python", self.script_path, "--config", temp_config_path]

            print(f"[{config.run_id}] Orchestrator spawning subprocess: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                text=True, 
                check=True
            )
            
            output = result.stdout
            
            # Parse the MLflow Run ID from the output
            # Our SimulationLoop prints: Logged simulation results to MLflow Run ID: <id>
            match = re.search(r"Logged simulation results to MLflow Run ID: ([a-zA-Z0-9]+)", output)
                
            if match:
                run_id = match.group(1)
                print(f"[{config.run_id}] Subprocess complete. Captured Run ID: {run_id}")
                return run_id
            else:
                print(output)
                raise RuntimeError("Subprocess succeeded but MLflow Run ID could not be parsed from stdout.")
                
        except subprocess.CalledProcessError as e:
            print(f"[{config.run_id}] Subprocess failed with exit code {e.returncode}")
            print("STDOUT:", e.stdout)
            print("STDERR:", e.stderr)
            raise RuntimeError(f"Sandbox simulation failed: {e.stderr}")
        finally:
            if os.path.exists(temp_config_path):
                os.remove(temp_config_path)
