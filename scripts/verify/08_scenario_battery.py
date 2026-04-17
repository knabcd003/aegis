# scripts/verify/08_scenario_battery.py
import sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from engines.intake.mandate_profile import MandateProfile
from engines.system.scenario.generator import BlockBootstrapGenerator
from engines.system.scenario.models import BootstrapRequest

print("=== PHASE 8: Scenario Battery Verification ===\n")

# Create a realistic return series (approximating equity returns)
np.random.seed(42)
n_days = 1260  # 5 years of trading days
daily_returns = np.random.normal(0.0005, 0.012, n_days).tolist()  # ~12.5% annual vol

# Add a stress period (simulating 2022-style drawdown)
# (In the list)
for i in range(500, 600):
    daily_returns[i] = float(np.random.normal(-0.003, 0.025))

mandate = MandateProfile.from_path_a(
    risk_tolerance="moderate",
    time_horizon="swing",
    capital=50000
)

generator = BlockBootstrapGenerator()
health = generator.health()
print(f"Generator health: {health['status']}")

request = BootstrapRequest(
    strategy_returns=daily_returns,
    num_scenarios=50,
    block_size_days=20,
    scenario_length_days=252,
    mandate_max_drawdown=0.15
)

print(f"\nRunning {request.num_scenarios} scenarios...")
print(f"Block size: {request.block_size_days} days")
print(f"Scenario length: {request.scenario_length_days} days\n")

result = generator.execute(request)

print(f"=== SCENARIO BATTERY RESULTS ===")
print(f"Scenarios run: {result.scenarios_run}")
print(f"Scenarios passed: {result.scenarios_passed}")
print(f"Pass rate: {result.pass_rate:.1%}")
print(f"Worst case drawdown: {result.worst_case_drawdown:.1%}")
print(f"Expected shortfall (95%): {result.expected_shortfall_95:.1%}")
print(f"Battery passed (>=70%): {'✅' if result.battery_passed else '❌'} {result.battery_passed}")
print(f"Generator type: {result.generator_type}")

assert result.scenarios_run == 50, f"Expected 50 scenarios, got {result.scenarios_run}"
assert result.worst_case_drawdown < 0, "Worst case drawdown should be negative"
assert result.expected_shortfall_95 < 0, "Expected shortfall should be negative"
assert result.expected_shortfall_95 >= result.worst_case_drawdown, \
    "ES95 (mean of worst 5%) must be >= absolute worst case"

print(f"\nFailing scenarios (for Builder context):")
for i, scenario in enumerate(result.failing_scenarios[:3]):
    print(f"  {i+1}. {scenario.description}")

print(f"\nTotal failing scenarios: {len(result.failing_scenarios)}")
assert all(hasattr(s, 'description') and len(s.description) > 20
           for s in result.failing_scenarios), \
    "Failing scenario descriptions too short for Builder context"
print("✅ Failing scenarios have meaningful descriptions for Builder injection")

print("\n✅ PHASE 8 PASSED\n")
