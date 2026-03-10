from typing import Dict, Any, List, Optional, Type
from langgraph.graph import StateGraph, START, END
from langchain_ollama import ChatOllama

from engines.analyst.state import AgentState
from engines.analyst.analyst import AnalystNode
from engines.analyst.risk_manager import RiskManagerNode

# Node Registry: Mapping strings in config to Class Implementations
NODE_MAP: Dict[str, Type] = {
    "analyst": AnalystNode,
    "risk_manager": RiskManagerNode,
}

class AgenticSupervisor:
    """
    Manifest-Based Orchestrator for Aegis Agents.
    Dynamically builds a LangGraph DAG based on configuration.
    """
    def __init__(self, 
                 model: str, 
                 pipeline: List[str], 
                 edges: Optional[Dict[str, Dict[str, str]]] = None,
                 provider: str = "ollama"):
        
        if provider == "ollama":
            self.llm = ChatOllama(model=model, temperature=0.1)
        else:
            raise ValueError(f"Unsupported provider: {provider}")
            
        self.pipeline = pipeline
        self.edge_config = edges or {}
        
        # Verify agents exist in registry
        for agent_name in self.pipeline:
            if agent_name not in NODE_MAP:
                available = list(NODE_MAP.keys())
                raise ValueError(f"Unknown agent '{agent_name}' in pipeline. Available: {available}")
        
        self.graph = self._build_graph()
        self._verify_connectivity()
        
    def _verify_connectivity(self):
        """
        Ensures that every node in the pipeline has a valid path to the END state.
        This prevents runtime hangs from 'dangling' nodes.
        """
        graph = self.graph.get_graph()
        nodes = [n.id for n in graph.nodes.values()]
        # Skip internal nodes like __start__ and __end__ for our core check
        core_nodes = [n for n in nodes if n not in ("__start__", "__end__", "START", "END")]
        
        # Build adjacency list
        adj = {n: [] for n in nodes}
        for edge in graph.edges:
            adj[edge.source].append(edge.target)
            
        def can_reach_end(start_node):
            visited = set()
            stack = [start_node]
            while stack:
                curr = stack.pop()
                if curr == "__end__":
                    return True
                if curr not in visited:
                    visited.add(curr)
                    stack.extend(adj.get(curr, []))
            return False

        for node in core_nodes:
            if not can_reach_end(node):
                raise ValueError(f"Dangling node detected: '{node}' has no path to END.")

    def _build_graph(self):
        builder = StateGraph(AgentState)
        
        # 1. Add Nodes
        nodes = {}
        for name in self.pipeline:
             node_class = NODE_MAP[name]
             node_instance = node_class(self.llm)
             builder.add_node(name, node_instance)
             nodes[name] = node_instance
             
        # 2. Add Edges
        if not self.pipeline:
            raise ValueError("Pipeline cannot be empty.")
            
        # Start at the first node
        builder.add_edge(START, self.pipeline[0])
        
        # Build connections
        for i, name in enumerate(self.pipeline):
            # Check for explicit edge overrides
            if name in self.edge_config:
                overrides = self.edge_config[name]
                
                # If the node supports conditional routing (like RiskManager)
                # We expect it to return specific keys in the state or we use a router function
                # For Phase 1-2, we'll implement explicit mapping for known conditional nodes
                if name == "risk_manager":
                    def risk_router(state: AgentState):
                        if state.get("risk_veto", False):
                            return "veto"
                        return "approve"
                    
                    routing_map = {
                        "veto": END if overrides.get("veto") == "END" else overrides.get("veto"),
                        "approve": END if overrides.get("approve") == "END" else overrides.get("approve")
                    }
                    builder.add_conditional_edges(name, risk_router, routing_map)
                else:
                    # Default linear behavior if override is present but not conditional logic implemented yet
                    next_node = overrides.get("next")
                    if next_node:
                        builder.add_edge(name, END if next_node == "END" else next_node)
            else:
                # Default linear connection
                if i < len(self.pipeline) - 1:
                    builder.add_edge(name, self.pipeline[i+1])
                else:
                    builder.add_edge(name, END)
        
        return builder.compile()

    def run(self, ticker: str, date: str, fundamental_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes the dynamic LangGraph for a given ticker and point-in-time date.
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
