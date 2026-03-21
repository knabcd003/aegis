"""
DeBERTa NLI Segment Classifier — Standalone Module (Phase 4)

Two-stage classification for segment obfuscation detection:
  Stage 1: DeBERTa-v3-large cross-encoder (NLI) — ~1ms per pair, CPU
  Stage 2: Qwen 8B (only woken for NEUTRAL/CONTRADICTION from Stage 1)

Singleton model loading: model is loaded once at module import or first call,
then reused for all subsequent classifications.

This module replaces the inline NLI code that was embedded in sec_edgar_connector.py.
"""
import logging
from typing import Optional, Dict, Any, List, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


class NLIResult(str, Enum):
    ENTAILMENT = "ENTAILMENT"
    NEUTRAL = "NEUTRAL"
    CONTRADICTION = "CONTRADICTION"


class SegmentClassifier:
    """
    Singleton DeBERTa-v3-large NLI classifier for segment change detection.

    Usage:
        classifier = SegmentClassifier.get_instance()
        result = classifier.classify("Software Services", "Cloud Computing Platform")
    """
    _instance: Optional["SegmentClassifier"] = None
    _model = None
    _model_loaded = False

    def __init__(self):
        """Use get_instance() instead of direct construction."""
        self._load_model()

    @classmethod
    def get_instance(cls) -> "SegmentClassifier":
        """Get or create the singleton classifier instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset(cls):
        """Reset the singleton (for testing only)."""
        cls._instance = None
        cls._model = None
        cls._model_loaded = False

    def _load_model(self):
        """Load DeBERTa-v3-large cross-encoder. ~183MB, loaded once."""
        if self.__class__._model_loaded:
            return

        try:
            from sentence_transformers import CrossEncoder
            logger.info("Loading cross-encoder/nli-deberta-v3-large (~183MB, once)...")
            self.__class__._model = CrossEncoder("cross-encoder/nli-deberta-v3-large")
            self.__class__._model_loaded = True
            logger.info("NLI model ready.")
        except Exception as e:
            logger.warning(f"Could not load NLI model: {e}. Classification will use fallback.")
            self.__class__._model = None
            self.__class__._model_loaded = True  # Don't retry on failure

    @property
    def is_available(self) -> bool:
        """Check if the NLI model loaded successfully."""
        return self._model is not None

    def classify(
        self,
        historical_label: str,
        candidate_text: str,
    ) -> NLIResult:
        """
        Stage 1 — DeBERTa NLI classification.

        Compares a historical segment label against new candidate text.
        Returns:
          ENTAILMENT    → segment unchanged. Do NOT wake Qwen.
          NEUTRAL       → borderline. Wake Qwen for confirmation.
          CONTRADICTION → confirmed restructuring. Wake Qwen, queue re-anchoring.

        Falls back to NEUTRAL if model unavailable (conservative: triggers Qwen).
        """
        if self._model is None:
            return NLIResult.NEUTRAL  # Conservative fallback

        try:
            scores = self._model.predict([(historical_label, candidate_text)])
            # DeBERTa-v3 NLI label order: [CONTRADICTION, ENTAILMENT, NEUTRAL]
            labels = [NLIResult.CONTRADICTION, NLIResult.ENTAILMENT, NLIResult.NEUTRAL]
            return labels[int(scores[0].argmax())]
        except Exception as e:
            logger.error(f"NLI classification error: {e}")
            return NLIResult.NEUTRAL  # Conservative fallback

    def classify_batch(
        self,
        pairs: List[Tuple[str, str]],
    ) -> List[NLIResult]:
        """
        Batch classification for multiple label-text pairs.
        More efficient than calling classify() in a loop.
        """
        if self._model is None:
            return [NLIResult.NEUTRAL] * len(pairs)

        try:
            scores = self._model.predict(pairs)
            labels = [NLIResult.CONTRADICTION, NLIResult.ENTAILMENT, NLIResult.NEUTRAL]
            results = []
            for score in scores:
                results.append(labels[int(score.argmax())])
            return results
        except Exception as e:
            logger.error(f"NLI batch classification error: {e}")
            return [NLIResult.NEUTRAL] * len(pairs)

    def should_wake_qwen(self, result: NLIResult) -> bool:
        """
        Stage 2 routing decision.
        Qwen is only called for NEUTRAL or CONTRADICTION — never for ENTAILMENT.
        """
        return result in (NLIResult.NEUTRAL, NLIResult.CONTRADICTION)


# Module-level convenience functions (backward compatible with sec_edgar_connector)

def classify_segment_change(historical_label: str, candidate_text: str) -> str:
    """
    Module-level wrapper for backward compatibility.
    Returns string result: 'ENTAILMENT' | 'NEUTRAL' | 'CONTRADICTION'
    """
    classifier = SegmentClassifier.get_instance()
    return classifier.classify(historical_label, candidate_text).value


def get_nli_model():
    """Module-level accessor for the NLI model (backward compatibility)."""
    classifier = SegmentClassifier.get_instance()
    return classifier._model
