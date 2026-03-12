import pytest
import numpy as np
from unittest.mock import patch, MagicMock
from engines.fundamental.segment_anchor import SegmentAnchor

@pytest.fixture
def mock_nli():
    with patch('engines.fundamental.segment_anchor.CrossEncoder') as mock:
        yield mock

@pytest.fixture
def mock_qwen():
    with patch('engines.fundamental.segment_anchor.ChatOllama') as mock:
        yield mock

@pytest.fixture
def anchor(mock_nli, mock_qwen):
    SegmentAnchor._instance = None
    return SegmentAnchor()

def test_singleton(anchor):
    second_instance = SegmentAnchor()
    assert anchor is second_instance

def test_nli_entailment(anchor):
    # Mocking CrossEncoder behavior: index 1 is ENTAILMENT
    anchor._nli_model.predict.return_value = np.array([[0.1, 0.8, 0.1]])
    
    result = anchor.classify_segment_change(
        "iPhone Revenue", 
        "Our iPhone segment revenue reported strong growth."
    )
    assert result == "ENTAILMENT"

    # Should pass without hooking Qwen
    assert anchor.evaluate_filing_segment("AAPL", "iPhone Revenue", "Our iPhone segment revenue reported strong growth.") is True

def test_nli_contradiction_triggers_alert(anchor):
    # Index 0 is CONTRADICTION
    anchor._nli_model.predict.return_value = np.array([[0.9, 0.05, 0.05]])
    
    # Mock Qwen response
    mock_response = MagicMock()
    mock_response.content = '{"equivalent_metric_found": false, "change_type": "structural"}'
    anchor._llm.invoke.return_value = mock_response

    result = anchor.classify_segment_change(
        "Services", 
        "We have completely disbanded our Services unit and folded it into Hardware."
    )
    assert result == "CONTRADICTION"

    # Should trigger alert and suspend
    assert anchor.evaluate_filing_segment("AAPL", "Services", "We have completely disbanded our Services unit.") is False
    assert len(anchor.reanchoring_alerts) == 1
    
    alert_id = "AAPL_0"
    assert anchor.reanchoring_alerts[alert_id]["acknowledged"] is False
    
    # After acknowledgement
    assert anchor.acknowledge_alert(alert_id) is True
    assert anchor.reanchoring_alerts[alert_id]["acknowledged"] is True

def test_nli_neutral_cosmetic_change(anchor, mock_qwen):
    # Index 2 is NEUTRAL
    anchor._nli_model.predict.return_value = np.array([[0.1, 0.1, 0.8]])
    
    # Mock Qwen response for cosmetic change
    mock_response = MagicMock()
    mock_response.content = '{"equivalent_metric_found": true, "proposed_replacement": "Services & Subscriptions", "change_type": "cosmetic"}'
    anchor._llm.invoke.return_value = mock_response

    result = anchor.classify_segment_change(
        "Services", 
        "Our Services & Subscriptions segment has been introduced to replace the former nomenclature."
    )
    assert result == "NEUTRAL"

    # Should NOT trigger alert because Qwen found an equivalent metric and it's cosmetic
    assert anchor.evaluate_filing_segment("AAPL", "Services", "Our Services & Subscriptions segment...") is True
    assert len(anchor.reanchoring_alerts) == 0
