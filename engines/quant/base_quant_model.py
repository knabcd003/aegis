"""
Base Quant Model Interface — Abstract contract for all mathematical models in the Quant Engine.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any
import pandas as pd


class BaseQuantModel(ABC):
    """Abstract base class for quantitative models (e.g., HMM, Riskfolio)."""

    def __init__(self, model_dir: str = "models"):
        self.model_dir = model_dir

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable model name."""
        pass

    @abstractmethod
    def train(self, df: pd.DataFrame) -> None:
        """
        Train/fit the model on historical data.
        """
        pass

    @abstractmethod
    def predict(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Run inference on recent data.
        Returns a dictionary containing the mathematical outputs.
        """
        pass

    @abstractmethod
    def save(self, filepath: str) -> None:
        """Serialize and save the model to disk."""
        pass

    @abstractmethod
    def load(self, filepath: str) -> None:
        """Load a serialized model from disk."""
        pass
