from engines.vcl.component import VCLComponent, ComponentRole, HealthResult, HealthStatus
from pydantic import BaseModel, Field
from datetime import date
from typing import Optional, Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class FinBERTSentimentGate(VCLComponent):
    """
    VCL Component that gates signals based on FinBERT sentiment scores.
    Aggregates point-in-time news headlines for the given date.
    """
    component_id = "finbert_sentiment_gate"
    version = "1.0.0"
    role = ComponentRole.GATE_CONDITION

    class Input(BaseModel):
        ticker: str
        date: date
        upstream_signal: bool
        min_sentiment_score: float = 0.0

    class Output(BaseModel):
        signal: bool
        sentiment_score: float
        gate_applied: bool
        reason: str

    input_schema = Input
    output_schema = Output

    def execute(self, input_data: Input) -> Output:
        # If upstream signal is already False, pass through — don't waste a FinBERT call
        if not input_data.upstream_signal:
            return self.Output(
                signal=False,
                sentiment_score=0.0,
                gate_applied=False,
                reason="upstream_signal_false — gate not evaluated"
            )

        # Get FinBERT sentiment score for this ticker on this date
        score = self._get_finbert_score(input_data.ticker, input_data.date)
        passed = score >= input_data.min_sentiment_score

        return self.Output(
            signal=passed,
            sentiment_score=score,
            gate_applied=True,
            reason=(
                f"sentiment_score={score:.3f} "
                f"{'≥' if passed else '<'} "
                f"threshold={input_data.min_sentiment_score:.3f}"
            )
        )

    def _get_finbert_score(self, ticker: str, target_date: date) -> float:
        """
        Aggregates news for the specific date (PiT) and scores them.
        """
        from engines.data_ingestion.connectors.yfinance_connector import YFinanceConnector
        from engines.data_ingestion.connectors.finbert_connector import FinBERTConnector

        yf = YFinanceConnector()
        finbert = FinBERTConnector()

        # 1. Fetch news knowable on this date (Point-in-Time)
        # We fetch last 7 days leading up to target_date to get enough volume
        news_items = yf.get_news(ticker, days=7, as_of_date=target_date)
        
        if not news_items:
            # Default to neutral/0.0 if no news found
            return 0.0

        # 2. Score news items
        scored_news = finbert.score_news_items(news_items)
        
        # 3. Simple average of scores for the headlines
        scores = [item.get("sentiment_score", 0.0) for item in scored_news]
        
        # Adjust scores: positive = 1, negative = -1, neutral = 0 is one way.
        # But FinBERT returns a probability. Let's use the net (pos - neg).
        net_scores = []
        for item in scored_news:
            pos = item.get("sentiment_positive", 0.0)
            neg = item.get("sentiment_negative", 0.0)
            net_scores.append(pos - neg)
            
        return sum(net_scores) / len(net_scores) if net_scores else 0.0

    def health(self) -> HealthResult:
        """
        Industrial Requirement: Distinguish between model availability and connectivity.
        - HEALTHY: Model weights present and loadable.
        - DEGRADED: Model weights missing, corrupt, or wrong version.
        - News connectivity is relaxed (handled via fallback to neutral in execute).
        """
        try:
            from engines.data_ingestion.connectors.finbert_connector import FinBERTConnector
            connector = FinBERTConnector()
            
            # 1. Model Availability Check (Non-negotiable)
            # We check if the model name is defined and try a minimal load check
            if not connector.MODEL_NAME:
                return HealthResult(status=HealthStatus.DEGRADED, reason="MODEL_NAME undefined")
            
            # Check if transformer model is loadable. 
            # Note: connector.health_check() currently tries to score text, which confirms the model is ready.
            if connector.health_check():
                return HealthResult(status=HealthStatus.HEALTHY)
            else:
                return HealthResult(
                    status=HealthStatus.DEGRADED, 
                    reason="FinBERT model initialization failed (weights may be missing or corrupt)"
                )
        except Exception as e:
            return HealthResult(
                status=HealthStatus.DEGRADED,
                reason=f"System Dependency Error: {str(e)}"
            )
