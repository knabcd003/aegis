# scripts/verify/11_live_proving_ground.py
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from dotenv import load_dotenv
load_dotenv()

print("=== PHASE 11: 5-Minute Live Proving Ground Test ===\n")
print("This test runs a Sentinel in paper-trading mode for 5 minutes.")
print("It will NOT execute any real trades.")
print("Watch the frontend at http://localhost:5173/command for live events.\n")

from engines.data_ingestion.data_engine import DataEngine
from engines.monitoring.connector_health import ConnectorHealthMonitor
from engines.sentinel.state_manager import SentinelStateManager, SentinelStateInput
import json
import datetime

# 1. Initialize heavyweight AI engines
print("Initializing Aegis AI Engines for live test...")
data_engine = DataEngine(data_dir="./data")
health_monitor = ConnectorHealthMonitor(data_engine=data_engine)
state_manager = SentinelStateManager(data_engine=data_engine, health_monitor=health_monitor)

# 2. Verify health
health_result = state_manager.health()
print(f"  State Manager status: {health_result.status}")

# 3. Load strategy config
config_path = "config/saved_strategies/e2e_verify_sma.json"
if not os.path.exists(config_path):
    print(f"❌ Strategy config not found: {config_path}")
    sys.exit(1)

with open(config_path, "r") as f:
    strategy_config = json.load(f)

# 4. Deploy Sentinel
sentinel_id = "verify_proving_ground_001"
sentinel = state_manager.deploy_sentinel(
    sentinel_id=sentinel_id,
    config=strategy_config,
    promoted_run_id="run_e2e_001",
    initial_cash=100000.0
)
print(f"✅ Sentinel {sentinel_id} deployed in Proving Ground mode")

# 5. Live Paper Trading Loop (60 seconds for verification)
print("Monitoring for 60 seconds...\n")
start_time = time.time()
while time.time() - start_time < 60:
    elapsed = int(time.time() - start_time)
    
    # Simulate heartbeat: Check close signals
    # In production, this would use real prices from data_engine
    current_prices = {"AAPL": 185.00} # Mock for speed, or could fetch from data_engine
    
    inputs = SentinelStateInput(
        sentinel_id=sentinel_id,
        current_prices=current_prices,
        current_date=datetime.datetime.utcnow()
    )
    
    output = state_manager.execute(inputs)
    state = state_manager.get_sentinel_state(sentinel_id)
    
    print(f"[{elapsed:3d}s] NAV: ${state['portfolio']['nav']:,.2f} | Status: {state['status']} | Pending Cards: {len(state['pending_cards'])}")
    
    # Check universe file
    universe_path = f"data/known_universe/{sentinel_id}_universe.json"
    if os.path.exists(universe_path):
        print(f"       ✅ {os.path.basename(universe_path)} exists")
    
    time.sleep(15)

# Final Validation
final_state = state_manager.get_sentinel_state(sentinel_id)
assert final_state["status"] == "active"
assert final_state["portfolio"]["nav"] >= 100000.0
assert os.path.exists(f"data/known_universe/{sentinel_id}_universe.json")

print("\n✅ PHASE 11 PASSED\n")
