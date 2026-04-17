import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime
from engines.sentinel.promotion_gate import PromotionGate, GateStage

class TestPromotionWFE(unittest.TestCase):
    def setUp(self):
        # Mock the health monitor
        self.mock_health = MagicMock()
        self.mock_health.is_any_connector_offline.return_value = False
        self.mock_health.is_any_connector_degraded.return_value = False
        
        self.gate = PromotionGate(health_monitor=self.mock_health)

    @patch('mlflow.get_run')
    def test_wfe_fails_on_negative_is_sharpe(self, mock_get_run):
        """
        Verify that WFE gate auto-fails if Optimization (IS) Sharpe is <= 0,
        even if WFE is theoretically high.
        """
        # Mock MLflow run data
        mock_run = MagicMock()
        mock_run.data.metrics = {
            "optimization_sharpe": -0.1,      # Negative IS Sharpe
            "walk_forward_efficiency": 1.5,   # High WFE (meaningless)
            "optimization_max_drawdown": -0.05,
            "trade_count": 100,
            "profit_factor": 1.5,
            "correlation_with_existing": 0.2,
            "bootstrap_pvalue": 0.01
        }
        # Explicitly mock tags so evaluate() routes correctly
        mock_run.data.tags = {"aegis_workflow_stage": "backtest"}
        
        mock_get_run.return_value = mock_run
        
        # Run evaluation (evaluate_backtest calls the logic we modified)
        result = self.gate.evaluate(
            run_id="test_run_neg_sharpe",
            workflow_id="test_wf",
            session_quality="nominal"
        )
        
        print(f"DEBUG NEG: failures={result.failures}")
        self.assertFalse(result.passed)

        # Check for the specific failure message we added
        wfe_failures = [f for f in result.failures if "WFE_INVALID" in f]
        self.assertTrue(len(wfe_failures) > 0, "Should have a WFE_INVALID failure")
        self.assertIn("IS Sharpe is -0.1000 (non-positive)", wfe_failures[0])

    @patch('mlflow.get_run')
    def test_wfe_passes_on_positive_is_sharpe(self, mock_get_run):
        """
        Verify that WFE gate passes if IS Sharpe is positive and WFE >= 0.50.
        """
        # Mock MLflow run data
        mock_run = MagicMock()
        mock_run.data.metrics = {
            "optimization_sharpe": 1.2,       # Positive IS Sharpe
            "walk_forward_efficiency": 0.6,   # WFE > 0.50
            "optimization_max_drawdown": -0.05,
            "trade_count": 100,
            "profit_factor": 1.5,
            "correlation_with_existing": 0.2,
            "bootstrap_pvalue": 0.01
        }
        mock_run.data.tags = {"aegis_workflow_stage": "backtest"}
        mock_get_run.return_value = mock_run
        
        result = self.gate.evaluate(
            run_id="test_run_pos_sharpe",
            workflow_id="test_wf",
            session_quality="nominal",
            scenario_pass_rate=0.8, # Satisfy other possible gates
            debate_confidence=80
        )
        
        print(f"DEBUG POS: failures={result.failures}")
        
        # If any other gates fail, it won't pass, but we care that WFE didn't fail
        wfe_failures = [f for f in result.failures if "WFE" in f or "WALK_FORWARD" in f]
        self.assertEqual(len(wfe_failures), 0, f"WFE should have passed, but got: {wfe_failures}")

if __name__ == '__main__':
    unittest.main()
