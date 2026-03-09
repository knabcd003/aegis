from typing import Dict, Any, Literal
from langgraph.graph import StateGraph, START, END
from langchain_ollama import ChatOllama

from engines.analyst.state import AgentState
from engines.analyst.analyst import AnalystNode
from engines.analyst.risk_manager import RiskManagerNode

class AgenticSupervisor:
    """
    The LangGraph routing mechanism for Aegis Phase 2.
    """
    def __init__(self, provider: str = "ollama", model: str = "qwen2.5:3b"):
        if provider == "ollama":
            self.llm = ChatOllama(model=model, temperature=0.1)
        else:
            raise ValueError(f"Unsupported provider: {provider}")
            
        self.analyst_node = AnalystNode(self.llm)
        self.risk_node = RiskManagerNode(self.llm)
        self.graph = self._build_graph()
        
    def _build_graph(self):
        builder = StateGraph(AgentState)
        
        # Add Nodes
        builder.add_node("analyst", self.analyst_node)
        builder.add_node("risk_manager", self.risk_node)
        
        # Edges
        builder.add_edge(START, "analyst")
        builder.add_edge("analyst", "risk_manager")
        builder.add_edge("risk_manager", END)
        
        return builder.compile()

    def run(self, ticker: str, date: str, fundamental_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes the LangGraph for a given ticker and point-in-time date.
        """
        initial_state = {
            "ticker": ticker,
            "date": str(date),
            "fundamental_context": fundamental_context,
            "reasoning_trace": [],
            "analyst_proposal": {},
            "risk_veto": False,
            "compliance_veto": False,
            "final_decision": {}
        }
        
        # Run graph
        final_state = self.graph.invoke(initial_state)
        
        return {
            "action": final_state["final_decision"].get("action", "HOLD"),
            "conviction": final_state["final_decision"].get("conviction", 0.0),
            "reasoning_trace": final_state.get("reasoning_trace", [])
        }
