"""
Semantic Invalidation Trigger for the Sentinel Engine.
Uses a fast, local HuggingFace Cross-Encoder to perform Natural Language Inference (NLI).
Compares the Analyst's invalidation trigger (premise) against a live news headline (hypothesis)
to instantly determine if the thesis is invalidated (entailment).
"""

import warnings
warnings.filterwarnings("ignore", category=FutureWarning)

import torch
import numpy as np
import logging
from typing import List, Dict, Any, Tuple

# Optional import to prevent crashing if not installed
try:
    from sentence_transformers import CrossEncoder
    HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    HAS_SENTENCE_TRANSFORMERS = False

logger = logging.getLogger(__name__)

class SemanticTrigger:
    def __init__(self, model_name: str = "cross-encoder/nli-deberta-v3-base"):
        """
        Initializes the Cross-Encoder. 
        Downloads the model to local HuggingFace cache on first run.
        """
        if not HAS_SENTENCE_TRANSFORMERS:
            raise ImportError("Please install `sentence-transformers` to use the SemanticTrigger.")
            
        # Determine optimal device
        if torch.cuda.is_available():
            self.device = "cuda"
        elif torch.backends.mps.is_available():
            self.device = "mps"
        else:
            self.device = "cpu"
            
        logger.info(f"Initializing Semantic Trigger Cross-Encoder on {self.device}...")
        
        # DeBERTa-v3 optimized for NLI
        self.encoder = CrossEncoder(model_name, device=self.device)
        
        # Determine index of entailment. Usually:
        # 0: contradiction, 1: entailment, 2: neutral
        # But we can check config to be safe
        self.entailment_idx = 1
        if hasattr(self.encoder.model.config, "label2id"):
            labels = self.encoder.model.config.label2id
            if "entailment" in labels:
                 self.entailment_idx = labels["entailment"]

    def evaluate(self, trigger_condition: str, headlines: List[str]) -> List[Dict[str, Any]]:
        """
        Evaluates a list of live news headlines against the Analyst's trigger condition.
        Returns a list of dicts with scores and whether the trigger was tripped.
        
        Args:
            trigger_condition: The Analyst's semantic invalidation limit (e.g. "SEC files lawsuit")
            headlines: A list of recent news strings.
            
        Returns:
            List of evaluations predicting entailment.
        """
        if not headlines:
            return []
            
        # Cross encoder format: [[Premise, Hypothesis], [Premise, Hypothesis]]
        # Premise = the trigger condition we are looking for
        # Hypothesis = the actual news headline
        pairs = [[trigger_condition, headline] for headline in headlines]
        
        # Predict probabilities directly 
        probs = self.encoder.predict(pairs, apply_softmax=True)
        
        # In case of single pair, expand dims to keep array 2D
        if len(headlines) == 1 and len(probs.shape) == 1:
            probs = np.expand_dims(probs, axis=0)
            
        results = []
        for i, headline in enumerate(headlines):
            entailment_prob = float(probs[i][self.entailment_idx])
            
            # Identify dominant class
            pred_idx = int(np.argmax(probs[i]))
            
            # Tripped if entailment is dominant class and prob > 0.5
            is_tripped = bool(pred_idx == self.entailment_idx and entailment_prob > 0.5)
            
            results.append({
                "trigger_condition": trigger_condition,
                "headline": headline,
                "entailment_probability": entailment_prob,
                "is_invalidated": is_tripped
            })
            
        return results
