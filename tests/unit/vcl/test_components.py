import pytest
from unittest.mock import MagicMock
from engines.vcl.registry import VCLRegistry

from engines.monitoring.connector_health import ConnectorHealthMonitor
from engines.nli.segment_classifier import SegmentClassifier
from engines.sentinel.close_signal_generator import CloseSignalGenerator
from engines.sentinel.promotion_gate import PromotionGate
from engines.sentinel.mirror_portfolio import CounterfactualTracker
from engines.sentinel.state_manager import SentinelStateManager

@pytest.fixture
def registry():
    return VCLRegistry()

def test_connector_health_monitor_registration(registry):
    mock_engine = MagicMock()
    comp = ConnectorHealthMonitor(data_engine=mock_engine)
    res = registry.register(comp)
    assert res.success is True, f"Failed at {res.failed_gate}: {res.reason}"

def test_segment_classifier_registration(registry):
    comp = SegmentClassifier()
    res = registry.register(comp)
    assert res.success is True, f"Failed at {res.failed_gate}: {res.reason}"

def test_close_signal_generator_registration(registry):
    comp = CloseSignalGenerator()
    res = registry.register(comp)
    assert res.success is True, f"Failed at {res.failed_gate}: {res.reason}"

def test_promotion_gate_registration(registry):
    mock_health = MagicMock()
    comp = PromotionGate(health_monitor=mock_health)
    res = registry.register(comp)
    assert res.success is True, f"Failed at {res.failed_gate}: {res.reason}"

def test_mirror_portfolio_registration(registry):
    comp = CounterfactualTracker(sentinel_id="test_sentinel_123")
    res = registry.register(comp)
    assert res.success is True, f"Failed at {res.failed_gate}: {res.reason}"

def test_state_manager_registration(registry):
    mock_data = MagicMock()
    mock_health = MagicMock()
    comp = SentinelStateManager(data_engine=mock_data, health_monitor=mock_health)
    comp.deploy_sentinel(sentinel_id="a", config={}, promoted_run_id="test")
    res = registry.register(comp)
    assert res.success is True, f"Failed at {res.failed_gate}: {res.reason}"

def test_fingerprint_stability():
    """Verify that equivalent components have identical fingerprints and survive serialization roundtrips."""
    import json
    
    comp1 = CloseSignalGenerator()
    comp2 = CloseSignalGenerator()
    
    # 1. Two separate instances of same class must have identical fingerprints
    fp1 = comp1.compatibility_fingerprint
    fp2 = comp2.compatibility_fingerprint
    assert fp1 == fp2, "Fingerprints differ between identical instances"
    
    # 2. Serialize and Deserialize via JSON to ensure deterministic ordering holds
    # dump input and output schema model json_schemas
    in_schema_json = json.dumps(comp1.input_schema.model_json_schema())
    out_schema_json = json.dumps(comp1.output_schema.model_json_schema())
    
    # deserialize back to python dicts
    in_dict = json.loads(in_schema_json)
    out_dict = json.loads(out_schema_json)
    
    # Recreate fingerprint logic based on the dicts (which lose python internal ordering)
    import hashlib
    roundtrip = (
        json.dumps(in_dict, sort_keys=True) +
        json.dumps(out_dict, sort_keys=True)
    )
    fp_roundtrip = hashlib.sha256(roundtrip.encode()).hexdigest()[:16]
    
    assert fp1 == fp_roundtrip, "Fingerprint changed after JSON roundtrip serialization (ordering bug)"
