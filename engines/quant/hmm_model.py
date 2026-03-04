"""
HMM Regime Detection Model — Uses hmmlearn to detect market states.
"""
import os
import joblib
import pandas as pd
import numpy as np
from hmmlearn import hmm
from typing import Dict, Any, List

from engines.quant.base_quant_model import BaseQuantModel


class MarketRegimeHMM(BaseQuantModel):
    """
    Hidden Markov Model for detecting market regimes (Bull, Bear, Volatile).
    Uses SPY log returns and VIX levels as observable inputs.
    """

    # Define standard taxonomy for output
    REGIME_BULL = "Bull"
    REGIME_BEAR = "Bear"
    REGIME_VOLATILE = "Volatile/Chop"

    def __init__(self, n_components: int = 3, model_dir: str = "models"):
        super().__init__(model_dir=model_dir)
        self.n_components = n_components
        
        # we will map the arbitrary hidden state integers (0, 1, 2) to strings
        self.state_labels: Dict[int, str] = {}
        
        # The underlying hmmlearn object
        self.model = hmm.GaussianHMM(
            n_components=self.n_components,
            covariance_type="full",
            n_iter=1000,
            tol=0.01,
            random_state=42
        )
        self.is_trained = False

    @property
    def name(self) -> str:
        return f"GaussianHMM_{self.n_components}State"

    def _prepare_data(self, df: pd.DataFrame) -> np.ndarray:
        """
        Prepares the feature matrix X for the HMM.
        Expects a DataFrame with 'close' (prices) and optionally 'vix'.
        """
        # Ensure data is sorted
        if "date" in df.columns:
            df = df.sort_values("date").copy()
        else:
            df = df.copy()

        # Calculate daily log returns
        df["log_return"] = np.log(df["close"] / df["close"].shift(1))
        
        # If VIX isn't provided, just use Volatility of returns as proxy
        if "vix" not in df.columns:
            df["rolling_vol"] = df["log_return"].rolling(window=10).std()
            features = ["log_return", "rolling_vol"]
        else:
            features = ["log_return", "vix"]
            
        df = df.dropna()
        X = df[features].values
        return X

    def train(self, df: pd.DataFrame) -> None:
        """
        Fit the HMM on historical data and map the hidden states to semantic labels.
        """
        print(f"[{self.name}] Preparing training data...")
        X = self._prepare_data(df)
        
        print(f"[{self.name}] Fitting GaussianHMM on {len(X)} observations...")
        self.model.fit(X)
        
        if self.model.monitor_.converged:
            print(f"[{self.name}] Convergence reached after {self.model.monitor_.iter} iterations.")
        else:
            print(f"[{self.name}] WARNING: Model did not converge.")

        # Map hidden states to semantic meaning
        # We look at the empirical mean return and variance for each state
        hidden_states = self.model.predict(X)
        
        # Re-attach to dataframe to calculate state properties
        features_df = pd.DataFrame(X, columns=["return", "vol"])
        features_df["state"] = hidden_states
        
        state_stats = features_df.groupby("state").agg(
            mean_return=("return", "mean"),
            volatility=("vol", "mean")
        )
        
        print(f"[{self.name}] State Statistics:")
        print(state_stats)

        # Logic to label states:
        # Sort by volatility. The highest volatility is Bear/Volatile.
        # The lowest volatility with positive returns is Bull.
        sorted_by_vol = state_stats.sort_values("volatility")
        
        if self.n_components == 3:
            # Lowest vol = Bull, Mid vol = Chop, High vol = Bear
            state_mapping = sorted_by_vol.index.tolist()
            self.state_labels[state_mapping[0]] = self.REGIME_BULL
            self.state_labels[state_mapping[1]] = self.REGIME_VOLATILE
            self.state_labels[state_mapping[2]] = self.REGIME_BEAR
        elif self.n_components == 2:
            state_mapping = sorted_by_vol.index.tolist()
            self.state_labels[state_mapping[0]] = self.REGIME_BULL
            self.state_labels[state_mapping[1]] = self.REGIME_BEAR
            
        print(f"[{self.name}] State Mapping: {self.state_labels}")
        self.is_trained = True

    def predict(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Infer the current market regime from recent data.
        Returns the regime label, the sequence, and probabilities.
        """
        if not self.is_trained:
            raise ValueError("Model must be trained or loaded before prediction.")
            
        X = self._prepare_data(df)
        if len(X) == 0:
            return {"error": "Insufficient data bounds after dropping NAs"}

        # Decode the most likely sequence
        hidden_states = self.model.predict(X)
        
        # Get probabilities of being in each state for the final day
        probs = self.model.predict_proba(X)
        current_probs = probs[-1]
        
        current_state_idx = hidden_states[-1]
        current_regime = self.state_labels.get(current_state_idx, "Unknown")
        
        # Format the probabilities dictionary
        prob_dict = {
            self.state_labels.get(i, f"State_{i}"): float(prob) 
            for i, prob in enumerate(current_probs)
        }

        return {
            "current_regime": current_regime,
            "current_probabilities": prob_dict,
            "log_likelihood": float(self.model.score(X)),
            "sequence": [self.state_labels.get(s, "Unknown") for s in hidden_states[-10:]] # last 10 days
        }

    def save(self, filename: str = "regime_hmm.joblib") -> None:
        """Save the fitted model and state labels."""
        if not self.is_trained:
            print("Cannot save an untrained model.")
            return
            
        os.makedirs(self.model_dir, exist_ok=True)
        path = os.path.join(self.model_dir, filename)
        
        payload = {
            "model": self.model,
            "state_labels": self.state_labels,
            "n_components": self.n_components
        }
        joblib.dump(payload, path)
        print(f"[{self.name}] Model saved to {path}")

    def load(self, filename: str = "regime_hmm.joblib") -> None:
        """Load a fitted model and state labels."""
        path = os.path.join(self.model_dir, filename)
        if not os.path.exists(path):
            raise FileNotFoundError(f"No model found at {path}")
            
        payload = joblib.load(path)
        self.model = payload["model"]
        self.state_labels = payload["state_labels"]
        self.n_components = payload["n_components"]
        self.is_trained = True
        print(f"[{self.name}] Model loaded from {path}")
