import pytest
from unittest.mock import patch, MagicMock
import subprocess
from engines.sandbox.orchestrator import SandboxOrchestrator
from config.schema import AegisConfig

@pytest.fixture
def mock_config():
    return AegisConfig(
        config_id="test-config-1",
        name="Test",
        version="1.0",
        template_base="test",
        trading_style="swing",
        asset_universe={"type": "custom", "tickers": ["AAPL"]},
        data_engine={"connectors": ["yfinance"], "lookback_days": 10},
        quant_engine={"hmm": {"enabled": False}, "vpin": {"enabled": False}, "chronos": {"enabled": False}},
        fundamental_engine={"earnings_revision": {"enabled": False}, "insider_monitor": {"enabled": False}, "macro_overlay": {"enabled": False}},
        signal_gate={"vpin_below": 1.0, "finbert_above": 0.0},
        position_sizing={"method": "equal_weight", "max_position_pct": 0.1, "capital": 100000},
        routing={"default_provider": "ollama", "default_model": "qwen3:4b", "complexity_threshold": 0.8, "logging": {"enabled": True}},
        agent={"enabled": False, "provider": "ollama", "model": "qwen3:4b"},
        sandbox={"slippage_bps": 10, "min_hold_days": 1, "promotion_criteria": {"sharpe_min": 1.0, "alpha_min_pct": 0.0, "max_drawdown_pct": 20.0, "backtest_months": 3}}
    )

def test_orchestrator_success(mock_config):
    orchestrator = SandboxOrchestrator(script_path="dummy.py")
    
    mock_stdout = "Some random logs\nLogged simulation results to MLflow Run ID: 12345abcde\nMore logs"
    
    with patch("subprocess.run") as mock_run:
        mock_result = MagicMock()
        mock_result.stdout = mock_stdout
        mock_result.returncode = 0
        mock_run.return_value = mock_result
        
        run_id = orchestrator.run_simulation(mock_config)
        assert run_id == "12345abcde"
        mock_run.assert_called_once()

def test_orchestrator_parse_failure(mock_config):
    orchestrator = SandboxOrchestrator(script_path="dummy.py")
    
    mock_stdout = "Some random logs\nNo run ID here\nMore logs"
    
    with patch("subprocess.run") as mock_run:
        mock_result = MagicMock()
        mock_result.stdout = mock_stdout
        mock_result.returncode = 0
        mock_run.return_value = mock_result
        
        with pytest.raises(RuntimeError, match="could not be parsed from stdout"):
            orchestrator.run_simulation(mock_config)

def test_orchestrator_subprocess_failure(mock_config):
    orchestrator = SandboxOrchestrator(script_path="dummy.py")
    
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = subprocess.CalledProcessError(
            returncode=1, cmd="dummy.py", stderr="Traceback: Crash"
        )
        
        with pytest.raises(RuntimeError, match="Sandbox simulation failed: Traceback: Crash"):
            orchestrator.run_simulation(mock_config)
