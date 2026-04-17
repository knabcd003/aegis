from enum import Enum
from typing import Literal, List, Optional
from pydantic import BaseModel, Field, model_validator

class EvidenceType(str, Enum):
    BACKTEST_DATA      = "backtest_data"      # weight 1.0
    STATISTICAL_TEST   = "statistical_test"   # weight 0.9
    HISTORICAL_ANALOGY = "historical_analogy" # weight 0.8
    HISTORICAL_ANOMALY = "historical_anomaly" # weight 0.8
    CITED_SCENARIO     = "cited_scenario"     # weight 0.7
    GENERAL_PRINCIPLE  = "general_principle"  # weight 0.3
    ASSERTION_ONLY     = "assertion_only"     # weight 0.0

EVIDENCE_WEIGHTS = {
    EvidenceType.BACKTEST_DATA:      1.0,
    EvidenceType.STATISTICAL_TEST:   0.9,
    EvidenceType.HISTORICAL_ANALOGY: 0.8,
    EvidenceType.HISTORICAL_ANOMALY: 0.8,
    EvidenceType.CITED_SCENARIO:     0.7,
    EvidenceType.GENERAL_PRINCIPLE:  0.3,
    EvidenceType.ASSERTION_ONLY:     0.0,
}

class DebateArgumentScore(BaseModel):
    argument_id:        str
    agent:              Literal["bull", "bear"]
    claim:              str
    evidence_type:      EvidenceType
    evidence_specific:  bool    # True if specific numbers/dates cited
    falsifiable:        bool
    evidentiary_weight: float = 0.0

    @model_validator(mode="after")
    def set_evidentiary_weight(self) -> "DebateArgumentScore":
        # Always override — caller cannot set this
        self.evidentiary_weight = EVIDENCE_WEIGHTS[self.evidence_type]
        return self

class DebateRound(BaseModel):
    round_number: int
    bull_arguments: List[DebateArgumentScore]
    bear_arguments: List[DebateArgumentScore]

class DebateVerdict(BaseModel):
    confidence_score:         int = Field(ge=0, le=100)
    verdict:                  Literal["APPROVE", "REJECT", "REVISE"]
    bull_evidentiary_score:   float
    bear_evidentiary_score:   float
    bull_strongest_point:     str
    bear_strongest_point:     str
    deciding_factor:          str
    debate_integrity:         str = "NOMINAL"
    required_revisions:       List[str] = Field(default_factory=list)
