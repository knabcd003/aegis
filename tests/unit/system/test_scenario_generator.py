import pytest
import numpy as np
from engines.system.scenario.models import BootstrapRequest
from engines.system.scenario.generator import BlockBootstrapGenerator

def test_block_bootstrap_generator_passing():
    """Verify Generator successfully builds synthetic NAVs and computes accurate passing metrics."""
    generator = BlockBootstrapGenerator()
    
    # Fake simple historical market returns (100 days of 0.1% daily positive)
    # We use this to verify length calculations and basic cumprod logic works
    historical_returns = [0.001] * 100
    
    # A single day drop that shouldn't impact much
    historical_returns[50] = -0.05
    
    request = BootstrapRequest(
        strategy_returns=historical_returns,
        mandate_max_drawdown=0.10,  # 10% limit
        num_scenarios=10,
        block_size_days=10,
        scenario_length_days=50
    )
    
    result = generator.execute(request)
    
    # All blocks will contain positive returns, or at worst a 5% drop. 
    # That is well within the 10% mandate.
    assert result.scenarios_run == 10
    assert result.scenarios_passed == 10
    assert result.pass_rate == 1.0
    assert result.battery_passed is True
    assert len(result.failing_scenarios) == 0

def test_block_bootstrap_generator_failing():
    """Verify Generator fails scenarios that breach mandate limits and returns human-readable context."""
    generator = BlockBootstrapGenerator()
    
    # Extremely volatile market: drops 5% every day
    historical_returns = [-0.05] * 100
    
    # Tight 2% limit
    request = BootstrapRequest(
        strategy_returns=historical_returns,
        mandate_max_drawdown=0.02,
        num_scenarios=5,
        block_size_days=5,
        scenario_length_days=20
    )
    
    result = generator.execute(request)
    
    assert result.scenarios_passed == 0
    assert result.pass_rate == 0.0
    assert result.battery_passed is False
    assert len(result.failing_scenarios) == 5
    
    # Check the structured string we added via user request
    summary = result.failing_scenarios[0]
    assert "A 20-day synthetic scenario composed of 4 random 5-day historical blocks" in summary.description

def test_expected_shortfall_calculation():
    """Verify ES95 is explicitly calculated across drawdowns."""
    generator = BlockBootstrapGenerator()
    
    historical_returns = [-0.01] * 50
    
    request = BootstrapRequest(
        strategy_returns=historical_returns,
        mandate_max_drawdown=0.20,
        num_scenarios=100,
        block_size_days=5,
        scenario_length_days=10
    )
    
    result = generator.execute(request)
    
    # With a constant 1% drop per day, a 10 day synthetic scenario will always
    # have a cumulative drop of roughly ~9.5%.
    # Therefore the worst drawdown is ~ -0.095, ES95 should be same.
    assert result.worst_case_drawdown < 0
    assert result.expected_shortfall_95 < 0
    assert abs(result.worst_case_drawdown - result.expected_shortfall_95) < 0.01

def test_graceful_short_history_exit():
    """Verify Generator handles returns series shorter than block size cleanly."""
    generator = BlockBootstrapGenerator()
    
    request = BootstrapRequest(
        strategy_returns=[0.01, -0.01, 0.02],
        mandate_max_drawdown=0.10,
        num_scenarios=10,
        block_size_days=20,
        scenario_length_days=50
    )
    
    result = generator.execute(request)
    assert result.scenarios_run == 0
    assert result.battery_passed is True
