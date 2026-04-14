from datetime import date
from config.config_manager import load_config
from engines.simulation.loop import SimulationLoop

config = load_config("config/saved_strategies/sma_crossover.json")
# Overwrite dates to a short burst
loop = SimulationLoop(config)
res = loop.run(date(2022, 1, 1), date(2023, 1, 1))
trades = res["trade_log"]
print(f"Number of trades: {len(trades)}")
if trades:
    print("First 3 trades:", trades[:3])
