import pytest
import sys
import os

# Add the project root to the python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.calculators import TradingCalculators

def test_kelly_criterion_basic():
    # 50% win rate, 2:1 reward/risk ratio
    # K = 0.5 - ((1-0.5)/2) = 0.5 - 0.25 = 0.25
    # Half Kelly (default fraction=0.5) = 0.125
    kelly = TradingCalculators.calculate_kelly_criterion(win_rate=0.5, win_loss_ratio=2.0)
    assert pytest.approx(kelly, 0.001) == 0.125
    
def test_kelly_criterion_negative_edge():
    # 30% win rate, 1:1 reward/risk ratio
    # K = 0.3 - (0.7/1) = -0.4
    # Should clamp to 0.0
    kelly = TradingCalculators.calculate_kelly_criterion(win_rate=0.3, win_loss_ratio=1.0)
    assert kelly == 0.0

def test_kelly_criterion_full_fraction():
    # K = 0.25, full Kelly (fraction = 1.0)
    kelly = TradingCalculators.calculate_kelly_criterion(win_rate=0.5, win_loss_ratio=2.0, fraction=1.0)
    assert pytest.approx(kelly, 0.001) == 0.25
    
def test_calculate_position_size():
    # Standard allocation
    size = TradingCalculators.calculate_position_size_usd(total_capital=10000.0, risk_percentage=0.1)
    assert size == 1000.0
    
def test_calculate_position_size_capped():
    # Should cap at 20% (max_allocation default = 0.2)
    size = TradingCalculators.calculate_position_size_usd(total_capital=10000.0, risk_percentage=0.5)
    assert size == 2000.0

def test_calculate_sma():
    prices = [10, 20, 30, 40, 50]
    # SMA over 3 periods: (30+40+50)/3 = 40
    sma = TradingCalculators.calculate_sma(prices, periods=3)
    assert sma == 40.0
    
def test_calculate_sma_insufficient_data():
    prices = [10, 20]
    sma = TradingCalculators.calculate_sma(prices, periods=3)
    assert sma is None
    
def test_stop_loss():
    # Entry: 100, ATR: 5. 2x multiplier -> Stop at 90.
    stop = TradingCalculators.calculate_stop_loss_price(100.0, 5.0, multiplier=2.0)
    assert stop == 90.0

def test_take_profit():
    # Entry: 100, ATR: 5. 3x multiplier -> Target at 115.
    target = TradingCalculators.calculate_take_profit_price(100.0, 5.0, multiplier=3.0)
    assert target == 115.0
