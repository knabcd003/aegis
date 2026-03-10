"""
Portfolio Optimizer — Uses Riskfolio-Lib to dynamically allocate weights based on Hierarchical Risk Parity (HRP).
"""
import os
import joblib
import pandas as pd
import numpy as np
from typing import Dict, Any, List

from engines.quant.base_quant_model import BaseQuantModel

# riskfolio-lib has been removed due to dependency issues.
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
        Infer optimal portfolio weights using Inverse-Variance Weighting (a simplified form of Risk Parity).
        Assets with lower historical volatility receive higher weights.
        Expects `df` to be a price matrix: Rows = Dates, Cols = Tickers.
        Returns a dictionary mapping ticker to target weight percentage (0.0 to 1.0).
        """
        if df.empty or len(df.columns) == 0:
            return {"error": "Empty dataframe provided"}

        # If date is a column, set it as index
        if "date" in df.columns:
            df = df.set_index("date")

        # Convert prices to returns
        returns = df.pct_change().dropna()
        if returns.empty:
            return {"error": "Not enough data to calculate returns"}

        print(f"[{self.name}] Running Inverse-Variance optimization on {returns.shape[1]} assets...")

        # Calculate historical variance for each asset
        variances_s = returns.var()

        # Handle flat assets by adding a tiny variance
        variances_s[variances_s <= 1e-10] = 1e-10

        # Calculate inverse variance
        inv_variances = 1.0 / variances_s

        # Normalize weights so they sum to 1.0
        # Convert to a standard dictionary early to avoid Pyre issues
        inv_var_dict = dict(inv_variances)
        
        total_inv_var = sum(inv_var_dict.values())
        
        weights_dict: Dict[str, Any] = {}
        for k, v in inv_var_dict.items():
            weights_dict[str(k)] = float(v) / float(total_inv_var)
            
        # For saving state, we can keep it as a Series
        self.last_weights = pd.Series(weights_dict)
            
        return weights_dict

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
