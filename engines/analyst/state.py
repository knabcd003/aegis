from typing import TypedDict, Any, Dict, List, Annotated
import operator

class AgentState(TypedDict):
    # Immutable inputs
    ticker: str
    date: str
    fundamental_context: Dict[str, Any]
    
    # Trace log for Glass Box debugging (accumulates strings across nodes)
    reasoning_trace: Annotated[List[str], operator.add]
    
    # Decisions
    analyst_proposal: Dict[str, Any] # {"action": "BUY"|"SELL"|"HOLD", "conviction": float, "rationale": str}
    risk_veto: bool
    compliance_veto: bool
    
    directional_mismatch: bool
    node_latencies: Dict[str, float]
    final_decision: Dict[str, Any] # Same schema as analyst_proposal, updated if vetoed
