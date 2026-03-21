import pytest
from unittest.mock import patch, MagicMock
import requests
import datetime
from engines.sentinel.state_manager import SignalCard
from engines.sentinel.price_feed import FinnhubPriceFeed, ConfigurationError
from engines.sentinel.freshness_validator import FreshnessValidator, SignalFreshnessState

@pytest.fixture
def mock_signal() -> SignalCard:
    # A standard signal card generated with dummy data
    return SignalCard(
        sentinel_id="test_sentinel_1",
        ticker="AAPL",
        decision="BUY",
        shares=100,
        price=150.0,
        portfolio_pct=0.1,
        target_price=165.0,
        stop_loss_price=140.0,
        hold_duration_days=20,
        thesis="Strong earnings",
        confidence=0.9,
        session_quality="nominal",
        volatility_bucket="medium_volatility",
        freshness_threshold=0.010,  # 1% threshold
        polling_interval=30
    )

def test_price_feed_requires_api_key(monkeypatch):
    """Verify ConfigurationError if FINNHUB_API_KEY is missing."""
    monkeypatch.delenv("FINNHUB_API_KEY", raising=False)
    with pytest.raises(ConfigurationError):
        FinnhubPriceFeed()

@patch.dict('os.environ', {'FINNHUB_API_KEY': 'test_key'})
@patch('requests.get')
def test_price_feed_timeout(mock_get):
    """Verify FinnhubPriceFeed handles timeouts safely by failing closed."""
    mock_get.side_effect = requests.exceptions.Timeout("Timeout")
    feed = FinnhubPriceFeed()
    price = feed.get_mid_price("AAPL")
    assert price is None

@patch.dict('os.environ', {'FINNHUB_API_KEY': 'test_key'})
@patch('engines.sentinel.price_feed.FinnhubPriceFeed.get_mid_price')
def test_Scenario_1_fresh_card(mock_get_price, mock_signal):
    """Test 1: Fresh card: price within threshold -> accept_enabled: True"""
    # 0.5% deviation, well within 1.0%
    mock_get_price.return_value = 150.75 
    feed = FinnhubPriceFeed()
    validator = FreshnessValidator(price_feed=feed)
    
    state = validator.validate_signal_freshness(mock_signal)
    assert state.is_fresh is True
    assert state.accept_enabled is True
    assert state.failure_reason is None
    assert state.reeval_triggered is False

@patch.dict('os.environ', {'FINNHUB_API_KEY': 'test_key'})
@patch('engines.sentinel.price_feed.FinnhubPriceFeed.get_mid_price')
def test_Scenario_2_stale_card(mock_get_price, mock_signal):
    """Test 2: Stale card: price beyond threshold -> accept_enabled: False, is_fresh: False"""
    # 1.5% deviation, breached 1.0% threshold
    mock_get_price.return_value = 152.25 
    feed = FinnhubPriceFeed()
    validator = FreshnessValidator(price_feed=feed)
    
    state = validator.validate_signal_freshness(mock_signal)
    assert state.is_fresh is False
    assert state.accept_enabled is False
    assert state.failure_reason == "price_stale"
    assert state.reeval_triggered is False # Not quite 2x threshold yet

@patch.dict('os.environ', {'FINNHUB_API_KEY': 'test_key'})
@patch('engines.sentinel.price_feed.FinnhubPriceFeed.get_mid_price')
def test_Scenario_3_reevaluation_trigger(mock_get_price, mock_signal):
    """Test 3: Re-evaluation trigger: price beyond 2x threshold -> reeval_triggered: True"""
    # 2.5% deviation, breached 2.0% (2x threshold)
    mock_get_price.return_value = 153.75 
    feed = FinnhubPriceFeed()
    validator = FreshnessValidator(price_feed=feed)
    
    state = validator.validate_signal_freshness(mock_signal)
    assert state.is_fresh is False
    assert state.accept_enabled is False
    assert state.reeval_triggered is True
    assert state.failure_reason == "price_stale"

@patch.dict('os.environ', {'FINNHUB_API_KEY': 'test_key'})
@patch('engines.sentinel.price_feed.FinnhubPriceFeed.get_mid_price')
def test_Scenario_4_price_feed_timeout(mock_get_price, mock_signal):
    """Test 4: Price feed timeout: feed unreachable -> accept_enabled: False, is_fresh: False"""
    mock_get_price.return_value = None 
    feed = FinnhubPriceFeed()
    validator = FreshnessValidator(price_feed=feed)
    
    state = validator.validate_signal_freshness(mock_signal)
    assert state.is_fresh is False
    assert state.current_price is None
    assert state.accept_enabled is False
    assert state.failure_reason == "price_feed_timeout"

@patch.dict('os.environ', {'FINNHUB_API_KEY': 'test_key'})
@patch('engines.sentinel.price_feed.FinnhubPriceFeed.get_mid_price')
def test_Scenario_5_degraded_session(mock_get_price, mock_signal):
    """Test 5: Degraded session card -> accept_enabled: False regardless of price freshness"""
    # Price is perfect
    mock_get_price.return_value = 150.0 
    mock_signal.session_quality = "degraded"
    
    feed = FinnhubPriceFeed()
    validator = FreshnessValidator(price_feed=feed)
    
    state = validator.validate_signal_freshness(mock_signal)
    assert state.is_fresh is True
    assert state.accept_enabled is False
    assert state.failure_reason == "degraded_session"

@patch.dict('os.environ', {'FINNHUB_API_KEY': 'test_key'})
@patch('engines.sentinel.price_feed.FinnhubPriceFeed.get_mid_price')
def test_Scenario_6_combined_stale_and_degraded(mock_get_price, mock_signal):
    """Test 6: Combined: stale AND degraded -> accept_enabled: False, both failure reasons recorded"""
    # Bad price
    mock_get_price.return_value = 155.0 
    # Bad session
    mock_signal.session_quality = "degraded"
    
    feed = FinnhubPriceFeed()
    validator = FreshnessValidator(price_feed=feed)
    
    state = validator.validate_signal_freshness(mock_signal)
    assert state.is_fresh is False
    assert state.accept_enabled is False
    assert state.failure_reason == "stale_and_degraded"
