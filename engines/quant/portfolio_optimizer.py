"""
Portfolio Optimizer — Uses Riskfolio-Lib to dynamically allocate weights based on Hierarchical Risk Parity (HRP).
"""
import os
import joblib
import pandas as pd
import numpy as np
from typing import Dict, Any, List

from engines.quant.base_quant_model import BaseQuantModel

try:
    import riskfolio as rf
    HAS_RISKFOLIO = True
except ImportError:
    HAS_RISKFOLIO = False


class HierarchicalRiskParityOptimizer(BaseQuantModel):
    """
    Allocates portfolio weights using Hierarchical Risk Parity (HRP).
    HRP clusters correlated assets and allocates risk equally to the clusters, 
    making it far more robust to shocks than Markowitz Mean-Variance.
    """

    def __init__(self, model_dir: str = "models", linkage_method: str = "single"):
        super().__init__(model_dir=model_dir)
        self.linkage_method = linkage_method
        self.last_weights: pd.DataFrame = None

    @property
    def name(self) -> str:
        return "HierarchicalRiskParity"

    def train(self, df: pd.DataFrame) -> None:
        """
        HRP is a non-parametric clustering algorithm that solves analytically 
        on the covariance matrix. Thus, 'training' in the ML sense is not required,
        but we can compute weights over the provided historical dataframe and store them.
        """
        # We assume the dataframe contains prices with dates as index or a 'date' column
        # and tickers as columns.
        pass

    def predict(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Infer the optimal portfolio weights for the given price matrix.
        Expects `df` to be a price matrix: Rows = Dates, Cols = Tickers.
        Returns a dictionary mapping ticker to target weight percentage (0.0 to 1.0).
        """
        if not HAS_RISKFOLIO:
            raise ImportError(
                f"[{self.name}] riskfolio-lib is not installed. Please pip install riskfolio-lib."
            )

        if df.empty:
            return {"error": "Empty dataframe provided"}

        # If date is a column, set it as index
        if "date" in df.columns:
            df = df.set_index("date")

        # Convert prices to returns
        returns = df.pct_change().dropna()
        if returns.empty:
            return {"error": "Not enough data to calculate returns"}
            
        # Avoid perfectly flat assets causing covariance division by zero
        # Add tiny noise if std is 0
        stds = returns.std()
        for col in stds[stds == 0].index:
            returns[col] += np.random.normal(0, 1e-6, len(returns))

        print(f"[{self.name}] Running HRP optimization on {returns.shape[1]} assets...")
        
        # Build the Riskfolio Object
        port = rf.HCPortfolio(returns=returns)

        # Estimate covariance matrix and expected returns using defaults
        # model='HRP' indicates Hierarchical Risk Parity
        try:
            # We must specify the parameters for the clustering
            # linkage options: 'single', 'complete', 'average', 'ward'
            weights_df = port.optimization(
                model="HRP", 
                codependence="pearson", 
                rm="MV", # Risk Measure: Variance (Standard Dev)
                rf=0,     # Risk free rate
                linkage=self.linkage_method, 
                max_k=10, 
                leaf_order=True
            )
        except Exception as e:
            return {"error": f"HRP optimization failed: {e}"}

        self.last_weights = weights_df

        # Format output as a flat dictionary
        weight_dict = weights_df.squeeze().to_dict()
        
        # Ensure values are native python floats
        return {k: float(v) for k, v in weight_dict.items()}

    def save(self, filename: str = "hrp_weights.joblib") -> None:
        """Save the last computed weights."""
        if self.last_weights is None:
            print("No weights to save.")
            return

        os.makedirs(self.model_dir, exist_ok=True)
        path = os.path.join(self.model_dir, filename)

        payload = {
            "last_weights": self.last_weights,
            "linkage_method": self.linkage_method
        }
        joblib.dump(payload, path)
        print(f"[{self.name}] Model parameters saved to {path}")

    def load(self, filename: str = "hrp_weights.joblib") -> None:
        """Load saved weights."""
        path = os.path.join(self.model_dir, filename)
        if not os.path.exists(path):
            raise FileNotFoundError(f"No model found at {path}")

        payload = joblib.load(path)
        self.last_weights = payload["last_weights"]
        self.linkage_method = payload["linkage_method"]
        print(f"[{self.name}] Model loaded from {path}")
