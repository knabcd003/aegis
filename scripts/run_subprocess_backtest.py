import argparse
from datetime import date
from config.manager import ConfigManager
from engines.simulation.loop import SimulationLoop
from config.schema import AegisConfig

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True, help="Path to JSON config")
    args = parser.parse_args()
    
    # Load config directly from dict representation
    manager = ConfigManager()
    config = manager.load(args.config)
    
    # Run the simulation loop
    # We will just run a small backtest window for speed during the loop
    start_date = date(2023, 1, 1)
    end_date = date(2023, 1, 31)
    
    loop = SimulationLoop(config)
    results = loop.run(start_date, end_date)
    
if __name__ == "__main__":
    main()
