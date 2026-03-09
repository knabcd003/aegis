import pytest
from uuid import UUID

from config.manager import ConfigManager, ConfigValidationError

# Mock template path for testing
TEST_TEMPLATE_PATH = "config/templates/tech_breakout_v1.json"


def test_valid_config_loads():
    """T2.1 — Valid template loads and fingerprints"""
    config = ConfigManager.load(TEST_TEMPLATE_PATH)
    assert config.fingerprint is not None
    assert len(config.fingerprint) == 64   # SHA256 hex
    assert config.config_id == "tech_breakout_v1"
    assert config.asset_universe.tickers == ["AAPL", "MSFT", "NVDA", "GOOGL", "META", "TSLA", "AMZN"]


def test_fingerprint_deterministic():
    """T2.2 — Fingerprint is deterministic"""
    c1 = ConfigManager.load(TEST_TEMPLATE_PATH)
    c2 = ConfigManager.load(TEST_TEMPLATE_PATH)
    assert c1.fingerprint == c2.fingerprint


def test_run_id_unique():
    """T2.4 — run_id is unique per load instance"""
    c1 = ConfigManager.load(TEST_TEMPLATE_PATH)
    c2 = ConfigManager.load(TEST_TEMPLATE_PATH)
    assert c1.run_id != c2.run_id
    
    # Verify it's a valid UUID
    try:
        UUID(c1.run_id)
        UUID(c2.run_id)
    except ValueError:
        pytest.fail("run_id is not a valid UUID string")


def test_missing_field_raises():
    """T2.3 — Missing required field raises with field name in message"""
    invalid_dict = {
        "config_id": "test",
        "version": "1.0",
        "asset_universe": {"tickers": ["AAPL"]}
    }
    
    with pytest.raises(ConfigValidationError) as exc:
        ConfigManager.load_dict(invalid_dict)
        
    error_msg = str(exc.value)
    assert "position_sizing" in error_msg
    assert "fundamental_engine" in error_msg
    assert "sandbox" in error_msg
    assert "routing" in error_msg
