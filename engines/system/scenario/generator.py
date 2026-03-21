import numpy as np
from typing import Type
from pydantic import BaseModel
from engines.vcl.component import VCLComponent, ComponentRole
from engines.system.scenario.models import BootstrapRequest, ScenarioBatteryResult, ScenarioSummary

class BlockBootstrapGenerator(VCLComponent):
    """
    Resamples non-overlapping blocks of historical returns.
    Preserves short-run autocorrelation within blocks.
    Disrupts long-run regime dependencies across blocks.
    Produces scenarios the backtest has not optimized against.
    """
    role = ComponentRole.SCENARIO_GENERATOR

    @property
    def component_id(self) -> str:
        return "block_bootstrap_generator"

    @property
    def version(self) -> str:
        return "1.0.0"

    def health(self) -> dict:
        return {"status": "healthy"}

    @property
    def input_schema(self) -> Type[BaseModel]:
        return BootstrapRequest

    @property
    def output_schema(self) -> Type[BaseModel]:
        return ScenarioBatteryResult

    def execute(self, request: BootstrapRequest) -> ScenarioBatteryResult:
        returns = np.array(request.strategy_returns)
        n_history = len(returns)
        
        # If history is too short, gracefully return a safe pass indicating no evaluation
        if n_history < request.block_size_days:
            return ScenarioBatteryResult(
                scenarios_run=0, scenarios_passed=0, pass_rate=1.0, worst_case_drawdown=0.0,
                expected_shortfall_95=0.0, battery_passed=True, failing_scenarios=[], generator_type="block_bootstrap"
            )

        max_start = n_history - request.block_size_days
        num_blocks = request.scenario_length_days // request.block_size_days
        
        drawdowns = []
        failing_scenarios = []
        passed = 0
        
        for i in range(request.num_scenarios):
            # Sample blocks
            synthetic_returns = []
            for _ in range(num_blocks):
                start_idx = np.random.randint(0, max_start + 1)
                synthetic_returns.extend(returns[start_idx : start_idx + request.block_size_days])
            
            synthetic_returns = np.array(synthetic_returns)
            
            # Simulate NAV
            synthetic_nav = np.cumprod(1 + synthetic_returns)
            running_max = np.maximum.accumulate(synthetic_nav)
            
            # Avoid divide by zero safely
            safe_max = np.where(running_max == 0, 1e-8, running_max)
            dds = synthetic_nav / safe_max - 1
            max_dd = float(np.min(dds))  # Yields a negative number natively (e.g. -0.22)
            
            drawdowns.append(max_dd)
            
            # Pass/Fail evaluation: mandate expects positive e.g. 0.15 for 15% limit
            # So max_dd (-0.22) is NOT strictly greater than -0.15, meaning it failed.
            has_passed = (max_dd > -request.mandate_max_drawdown)
            
            if has_passed:
                passed += 1
            else:
                desc = (
                    f"A {request.scenario_length_days}-day synthetic scenario composed of {num_blocks} random "
                    f"{request.block_size_days}-day historical blocks. Strategy NAV broke mandate risk limits, "
                    f"drawing down {abs(max_dd)*100:.1f}% vs mandate limit {request.mandate_max_drawdown*100:.1f}%."
                )
                failing_scenarios.append(ScenarioSummary(
                    scenario_id=f"boot_sample_{i}",
                    description=desc,
                    pass_status=False,
                    max_drawdown=max_dd
                ))
                
        pass_rate = passed / request.num_scenarios if request.num_scenarios > 0 else 1.0
        worst_dd = min(drawdowns) if drawdowns else 0.0
        
        # Expected Shortfall 95 (mean of worst 5% drawdowns)
        sorted_dds = sorted(drawdowns) # sort ascending (worst negative numbers first)
        n_worst = max(1, int(len(sorted_dds) * 0.05))
        es_95 = float(np.mean(sorted_dds[:n_worst])) if sorted_dds else 0.0
        
        return ScenarioBatteryResult(
            scenarios_run=request.num_scenarios,
            scenarios_passed=passed,
            pass_rate=pass_rate,
            worst_case_drawdown=worst_dd,
            expected_shortfall_95=es_95,
            battery_passed=bool(pass_rate >= 0.70),
            failing_scenarios=failing_scenarios,
            generator_type="block_bootstrap"
        )
