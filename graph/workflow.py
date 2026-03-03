import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Dict, Any, TypedDict, Optional, List
from langgraph.graph import StateGraph, END
from agents.researcher import ResearcherAgent
from agents.quant import QuantAgent
from agents.analyst import AnalystAgent

class TradingState(TypedDict):
    ticker: str
    prices: List[Dict[str, Any]]
    research_data: Dict[str, Any]
    quant_data: Dict[str, Any]
    analyst_decision: Optional[str]
    thesis: Optional[str]
    order: Optional[Dict[str, Any]]
    error: Optional[str]

def build_trading_graph() -> StateGraph:
    """
    Builds the cyclical LangGraph representing the primary trading flow:
    Researcher -> Quant -> Analyst
    """
    
    # Initialize Agents
    researcher = ResearcherAgent()
    quant = QuantAgent()
    analyst = AnalystAgent()
    
    # Initialize Graph
    workflow = StateGraph(TradingState)
    
    # Add Nodes
    workflow.add_node("researcher", researcher)
    workflow.add_node("quant", quant)
    workflow.add_node("analyst", analyst)
    
    # Define routing logic
    def route_after_quant(state: TradingState) -> str:
        if state.get("error"):
            return END
        if state.get("quant_data", {}).get("decision") == "SKIP":
            return END
        return "analyst"
        
    def route_after_research(state: TradingState) -> str:
        if state.get("error"):
            return END
        return "quant"
    
    # Build Edges
    workflow.set_entry_point("researcher")
    
    workflow.add_conditional_edges(
        "researcher",
        route_after_research,
        {
            "quant": "quant",
            END: END
        }
    )
    
    workflow.add_conditional_edges(
        "quant",
        route_after_quant,
        {
            "analyst": "analyst",
            END: END
        }
    )
    
    workflow.add_edge("analyst", END)
    
    return workflow.compile()
