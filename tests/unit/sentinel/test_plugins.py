import pytest
import pandas as pd
from engines.plugins import PluginRegistry, VPINPlugin, HMMPlugin

def test_plugin_registry():
    registry = PluginRegistry()
    registry.register("VPIN", VPINPlugin())
    registry.register("HMM", HMMPlugin())

    # Create dummy dataframe
    df = pd.DataFrame()
    
    anchors = registry.generate_quant_anchors("AAPL", df)
    
    assert "vpin_score" in anchors
    assert "vpin_signal" in anchors
    assert "hmm_regime" in anchors
    assert anchors["vpin_score"] == 0.72
    assert anchors["hmm_regime"] == "HIGH_VOLATILITY"

def test_plugin_failure_isolation():
    class FailingPlugin:
        def evaluate(self, ticker, data):
            raise ValueError("Model crash")
            
    registry = PluginRegistry()
    registry.register("Fail", FailingPlugin())
    registry.register("VPIN", VPINPlugin())
    
    df = pd.DataFrame()
    anchors = registry.generate_quant_anchors("AAPL", df)
    
    # Should isolate failure and still supply VPIN
    assert "vpin_score" in anchors
    assert "Fail_error" in anchors
    assert anchors["Fail_error"] == "Model crash"
