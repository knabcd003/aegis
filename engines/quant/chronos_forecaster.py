"""
Chronos-Bolt Forecaster — Uses Amazon's chronos-bolt-base time series foundation model.
"""
import os
import joblib
import pandas as pd
import numpy as np
from typing import Dict, Any

from engines.quant.base_quant_model import BaseQuantModel

try:
    import torch
    from chronos import ChronosBoltPipeline
    HAS_CHRONOS = True
except ImportError:
    HAS_CHRONOS = False

class ChronosForecaster(BaseQuantModel):
    """
    Forecasting model utilizing Amazon's zero-shot chronos-bolt-base foundation model.
    Treats time-series forecasting as a language modeling problem to predict median,
    upper bound, and lower bound future trajectories.
    """

    def __init__(self, model_dir: str = "models", model_name: str = "amazon/chronos-bolt-base"):
        super().__init__(model_dir=model_dir)
        self.model_name = model_name
        self._pipeline = None

    @property
    def name(self) -> str:
        return "ChronosBolt"
        
    def _init_pipeline(self):
        if self._pipeline is None:
            print(f"[{self.name}] Initializing {self.model_name} pipeline (may take a moment to download weights)...")
            device_map = "cpu"
            if torch.backends.mps.is_available():
                device_map = "mps"
            elif torch.cuda.is_available():
                device_map = "cuda"
                
            self._pipeline = ChronosBoltPipeline.from_pretrained(
                self.model_name,
                device_map=device_map,
                torch_dtype=torch.bfloat16 if device_map != "mps" else torch.float32, 
            )

    def train(self, df: pd.DataFrame) -> None:
        """
        Chronos is a zero-shot foundation model pre-trained on 100B params.
        No custom training is supported or necessary.
        """
        pass

    def predict(self, df: pd.DataFrame, prediction_length: int = 7) -> Dict[str, Any]:
        """
        Predict the next `prediction_length` prices.
        Expects `df` to have a 'close' column containing history (e.g., 90 days array).
        Returns median, lower (10th percentile), and upper (90th percentile) bounds.
        """
        if not HAS_CHRONOS:
            return {"error": "Chronos/torch is not installed."}

        if df is None or df.empty:
            return {"error": "Empty dataframe provided."}
            
        working_df = df.copy()
        working_df.columns = [c.lower() for c in working_df.columns]
        
        if "close" not in working_df.columns:
            return {"error": "Dataframe must contain 'close' column."}

        prices = torch.tensor(working_df["close"].values, dtype=torch.float32)
        
        # Chronos expects size > 0
        if len(prices) < 2:
            return {"error": "Need at least 2 historical data points."}

        try:
            self._init_pipeline()
            
            # Predict
            # For chronos-bolt, the first argument is `inputs`
            forecast = self._pipeline.predict(inputs=prices, prediction_length=prediction_length)
            
            # ChronosBoltPipeline returns a single torch.Tensor of shape [batch_size, num_samples, prediction_length]
            if len(forecast.shape) == 3: # (batch=1, samples, length)
                forecast_samples = forecast[0].numpy() # (samples, length)
            else:
                forecast_samples = forecast.numpy()
            
            # Calculate quantiles over the sample distribution
            low, median, high = np.quantile(forecast_samples, [0.1, 0.5, 0.9], axis=0)

            return {
                "median": median.tolist(),
                "lower_bound": low.tolist(),
                "upper_bound": high.tolist(),
                "prediction_length": prediction_length
            }

        except Exception as e:
            return {"error": f"Chronos prediction failed: {str(e)}"}

    def save(self, filename: str = "chronos_config.joblib") -> None:
        pass # Zero shot model, nothing to save

    def load(self, filename: str = "chronos_config.joblib") -> None:
        pass
