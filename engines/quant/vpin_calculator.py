"""
VPIN Calculator — Uses FlowRisk to calculate Volume-Synchronized Probability of Informed Trading.
"""
import os
import joblib
import pandas as pd
import numpy as np
from typing import Dict, Any, List

from engines.quant.base_quant_model import BaseQuantModel

import math

# flowrisk relies on np.math, which was removed in numpy 1.25+
if not hasattr(np, "math"):
    np.math = math

try:
    import flowrisk as fr
    HAS_FLOWRISK = True
except ImportError:
    HAS_FLOWRISK = False


class VPINCalculator(BaseQuantModel):
    """
    Computes VPIN (Volume-Synchronized Probability of Informed Trading).
    High VPIN indicates toxic order flow and high probability of institutional dumping.
    Uses Recursive EWMA VPIN from the flowrisk library.
    """

    def __init__(self, model_dir: str = "models", threshold: float = 0.8):
        super().__init__(model_dir=model_dir)
        self.threshold = threshold
        self.last_vpin: float = 0.0

    @property
    def name(self) -> str:
        return "VPIN_EWMA"

    def train(self, df: pd.DataFrame) -> None:
        """
        VPIN calculate is deterministic based on the prices/volume, 
        so 'training' is not strictly required.
        """
        pass

    def predict(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Compute the current VPIN from high-resolution intraday data.
        Expects `df` to have at minimum: 'close', 'volume'.
        """
        if not HAS_FLOWRISK:
            raise ImportError(f"[{self.name}] flowrisk is not installed. Please pip install flowrisk.")

        if df is None or df.empty or len(df) < 50:
            return {"error": "Insufficient intraday data for VPIN (need at least 50 bars)."}

        # Ensure required columns exist
        df_cols = [c.lower() for c in df.columns]
        if "close" not in df_cols or "volume" not in df_cols:
            return {"error": "VPIN requires 'close' and 'volume' columns."}

        # Normalize column names just in case
        working_df = df.copy()
        working_df.columns = [c.lower() for c in working_df.columns]
        
        # flowrisk strongly asserts that volume must be a float or int
        working_df["close"] = working_df["close"].astype(float)
        working_df["volume"] = working_df["volume"].astype(float)
        
        # flowrisk strongly asserts that volume must be a float or int
        working_df["close"] = working_df["close"].astype(float)
        working_df["volume"] = working_df["volume"].astype(float)

        # VPIN requires numpy arrays for calculation
        prices = working_df["close"].values
        volumes = working_df["volume"].values

        try:
            # We use the BulkConfVPIN for a one-shot evaluation over the provided series
            class Config(fr.BulkConfVPINConfig):
                N_TIME_BAR_FOR_INITIALIZATION = min(50, len(working_df) // 4)
                TIME_BAR_PRICE_COL_NAME = "close"
                TIME_BAR_VOLUME_COL_NAME = "volume"
                TIME_BAR_TIME_STAMP_COL_NAME = "date"
                
            config = Config()
            
            # Create the estimator
            estimator = fr.BulkConfVPIN(config)
            
            # flowrisk estimate() takes the DataFrame directly
            if "date" not in working_df.columns:
                working_df = working_df.reset_index()
                if "index" in working_df.columns:
                    working_df = working_df.rename(columns={"index": "date"})
                # If still no date, make a dummy one
                if "date" not in working_df.columns:
                    working_df["date"] = pd.date_range(start="2025-01-01", periods=len(working_df), freq="1min")
            
            result_df = estimator.estimate(working_df)
            
            # Extract the raw list of VPINs from the returned dataframe
            if isinstance(result_df, pd.DataFrame) and 'vpin' in result_df.columns:
                vpins = result_df['vpin'].tolist()
            else:
                return {"error": "Unexpected return format from flowrisk."}

            # Filter out NaNs resulting from the initialization period
            valid_vpins = [v for v in vpins if not pd.isna(v)]
            
            if not valid_vpins:
                return {"error": "Failed to calculate a valid VPIN score."}

            current_vpin = float(valid_vpins[-1])
            self.last_vpin = current_vpin

            is_toxic = current_vpin >= self.threshold

            return {
                "vpin": current_vpin,
                "is_toxic": is_toxic,
                "threshold_used": self.threshold
            }

        except Exception as e:
            return {"error": f"VPIN calculation failed: {str(e)}"}

    def save(self, filename: str = "vpin_state.joblib") -> None:
        """Save the last known state."""
        os.makedirs(self.model_dir, exist_ok=True)
        path = os.path.join(self.model_dir, filename)
        joblib.dump({"threshold": self.threshold, "last_vpin": self.last_vpin}, path)

    def load(self, filename: str = "vpin_state.joblib") -> None:
        """Load state."""
        path = os.path.join(self.model_dir, filename)
        if os.path.exists(path):
            state = joblib.load(path)
            self.threshold = state.get("threshold", 0.8)
            self.last_vpin = state.get("last_vpin", 0.0)
