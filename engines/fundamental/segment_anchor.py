"""
Segment Anchor (Phase 4)
Handles business segment tracking, obfuscation detection, and re-anchoring across SEC filings.
Uses a DeBERTa-v3-large Cross-Encoder for NLI classification + Qwen 8B fallback.
"""
import json
import logging
from typing import Dict, Any, Optional

try:
    from sentence_transformers import CrossEncoder
except ImportError:
    CrossEncoder = None

from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage

logger = logging.getLogger(__name__)

class SegmentAnchor:
    """
    Singleton evaluator for business segment reporting consistency.
    """
    _instance = None
    _nli_model: Optional[Any] = None
    _llm: Optional[ChatOllama] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SegmentAnchor, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """Preflight initialization. Loads the DeBERTa model so failures are loud at startup."""
        logger.info("Initializing SegmentAnchor NLI Cross-Encoder...")
        if CrossEncoder is None:
            raise ImportError(
                "sentence-transformers is required for Segment Anchor. "
                "Run `pip install sentence-transformers`"
            )

        try:
            # We use the generic cross-encoder for NLI
            self._nli_model = CrossEncoder("cross-encoder/nli-deberta-v3-large")
        except Exception as e:
            logger.error(f"Failed to load NLI model: {e}")
            raise RuntimeError(f"Critical failure loading NLI cross-encoder: {e}")

        # Initialize Qwen fallback
        self._llm = ChatOllama(model="qwen3:8b", temperature=0.1)
        self.reanchoring_alerts: Dict[str, Dict[str, Any]] = {}

    def classify_segment_change(self, historical_label: str, candidate_text: str) -> str:
        """
        Stage 1: DeBERTa NLI check between the historical segment description
        and the new 10-Q text snippet.
        Returns: 'CONTRADICTION', 'ENTAILMENT', or 'NEUTRAL'
        """
        if not self._nli_model:
            raise RuntimeError("NLI model not loaded.")

        # CrossEncoder predicts [CONTRADICTION, ENTAILMENT, NEUTRAL] probabilities
        scores = self._nli_model.predict([(historical_label, candidate_text)])[0]
        
        # Mapping index to label according to cross-encoder/nli-deberta-v3-large generic output
        # Common layout: 0: Contradiction, 1: Entailment, 2: Neutral
        label_mapping = ["CONTRADICTION", "ENTAILMENT", "NEUTRAL"]
        
        max_idx = int(scores.argmax())
        return label_mapping[max_idx]

    def _query_qwen_for_struct_change(self, historical_label: str, candidate_text: str) -> Dict[str, Any]:
        """
        Stage 2: Use Qwen 8B to interpret a Neutral or Contradictory text chunk
        and return a constrained JSON mapping for the structural change.
        """
        sys_msg = SystemMessage(content="""You are an expert financial analyst. A company may have changed its business reporting segment structure in its recent SEC filing. 
Given the Historical Segment Name and the Candidate Text from the new filing, determine if the segment has been renamed, merged, or spun off.
Your output must be strict JSON matching this schema:
{
  "equivalent_metric_found": boolean,
  "proposed_replacement": "string (the new segment name, or null)",
  "change_type": "cosmetic" | "structural",
  "confidence": float (0.0 to 1.0)
}
Return ONLY valid JSON.
""")
        user_msg = HumanMessage(content=f"Historical Segment Name: {historical_label}\nCandidate Text: {candidate_text}")
        
        try:
            response = self._llm.invoke([sys_msg, user_msg])
            # Parse the JSON
            raw_content = response.content.replace("```json", "").replace("```", "").strip()
            return json.loads(raw_content)
        except Exception as e:
            logger.error(f"Qwen fallback failed: {e}")
            return {
                "equivalent_metric_found": False,
                "proposed_replacement": None,
                "change_type": "structural",
                "confidence": 0.0,
                "error": str(e)
            }

    def evaluate_filing_segment(self, ticker: str, historical_label: str, candidate_text: str) -> bool:
        """
        Full 3-stage process for evaluating an ingested Segment.
        Returns True if processing can continue, False if a Re-Anchoring Alert was triggered.
        """
        # Stage 1
        nli_result = self.classify_segment_change(historical_label, candidate_text)
        
        if nli_result == "ENTAILMENT":
            logger.info(f"[{ticker}] Segment '{historical_label}' entailed. Proceeding.")
            return True

        logger.warning(f"[{ticker}] NLI returned {nli_result} for '{historical_label}'. Hooking Qwen...")

        # Stage 2
        qwen_analysis = self._query_qwen_for_struct_change(historical_label, candidate_text)
        
        # Stage 3 - Re-Anchoring Alert logic
        is_structural_neutral = (nli_result == "NEUTRAL" and qwen_analysis.get("change_type") == "structural")
        
        if nli_result == "CONTRADICTION" or is_structural_neutral:
            alert_id = f"{ticker}_{len(self.reanchoring_alerts)}"
            self.reanchoring_alerts[alert_id] = {
                "ticker": ticker,
                "historical_label": historical_label,
                "candidate_text": candidate_text,
                "nli_result": nli_result,
                "qwen_analysis": qwen_analysis,
                "acknowledged": False
            }
            logger.critical(f"[{ticker}] RE-ANCHORING ALERT TRIGGERED. Monitoring suspended for this segment.")
            return False

        # If it was a cosmetic rename (e.g. "Services" -> "Services & Subscriptions")
        if qwen_analysis.get("change_type") == "cosmetic" and qwen_analysis.get("equivalent_metric_found"):
            logger.info(f"[{ticker}] Qwen identified cosmetic change. Proceeding with '{qwen_analysis.get('proposed_replacement')}'.")
            return True

        # Edge case fallback: treat as alert
        return False

    def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge a re-anchoring alert to resume monitoring (Stage 3)."""
        if alert_id in self.reanchoring_alerts:
            self.reanchoring_alerts[alert_id]["acknowledged"] = True
            logger.info(f"Alert {alert_id} structurally acknowledged. Monitoring resumed.")
            return True
        return False
