"""
Post-Mortem Reflexion Graph (The Autopsy Engine)

When a historical trade results in an unacceptable drawdown, the Sandbox Orchestrator 
triggers this graph. It reads the original thesis, the bad market outcome, and forces 
Claude to criticize its own logic to generate a permanent "Lesson." 
This lesson is injected into the ChromaDB Episodic Memory Bank to prevent future mistakes.
"""

import os
import logging
from typing import Dict, Any, TypedDict
import yaml

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, END

from engines.analyst.episodic_memory import EpisodicMemory

logger = logging.getLogger(__name__)

# Define the LangGraph State
class ReflexionState(TypedDict):
    ticker: str
    original_thesis: str
    quant_context: Dict[str, Any]
    actual_outcome: str
    criticism: str
    final_lesson: str

class ReflexionEngine:
    def __init__(self, config_path: str = "config/experiment_config.yaml", memory: EpisodicMemory = None):
        self.logger = logging.getLogger(self.__class__.__name__)
        
        with open(config_path, "r") as f:
            self.config = yaml.safe_load(f)
            
        # We reuse the supervisor model (Claude) for high-reasoning tasks
        self.model_name = self.config.get("analyst_engine", {}).get("supervisor_llm", "claude-sonnet-4-6")
        
        if not os.environ.get("ANTHROPIC_API_KEY"):
            raise ValueError("ANTHROPIC_API_KEY environment variable not set.")
            
        self.llm = ChatAnthropic(model_name=self.model_name, temperature=0.2)
        self.memory = memory or EpisodicMemory()
        
        # Build Graph
        self.graph = self._build_graph()

    def _build_graph(self):
        workflow = StateGraph(ReflexionState)
        
        workflow.add_node("critic", self._critic_node)
        workflow.add_node("formulator", self._formulator_node)
        workflow.add_node("injector", self._injector_node)
        
        workflow.set_entry_point("critic")
        workflow.add_edge("critic", "formulator")
        workflow.add_edge("formulator", "injector")
        workflow.add_edge("injector", END)
        
        return workflow.compile()

    def _critic_node(self, state: ReflexionState) -> Dict:
        self.logger.info("[Reflexion] Critic Node: Analyzing the failure...")
        
        prompt = f"""You are a ruthless Senior Portfolio Manager auditing a failed trade.
A junior AI analyst recommended a trade that resulted in a massive loss.

CONTEXT OF THE TRADE:
Ticker: {state['ticker']}
Regime: {state['quant_context'].get('regime', 'Unknown')}
Sector: {state['quant_context'].get('sector', 'Unknown')}
VPIN Toxicity: {state['quant_context'].get('vpin_toxicity', 'Unknown')}

THE JUNIOR'S FAILED THESIS:
{state['original_thesis']}

THE ACTUAL OUTCOME:
{state['actual_outcome']}

INSTRUCTIONS:
Read the thesis and the context. Identify exactly what the junior analyst missed or misweighted. 
Did they ignore a high VPIN? Did they buy into a bear market regime? Be harsh, concise, and analytical.
"""
        response = self.llm.invoke([HumanMessage(content=prompt)])
        return {"criticism": response.content}

    def _formulator_node(self, state: ReflexionState) -> Dict:
        self.logger.info("[Reflexion] Formulator Node: Condensing criticism into a strict rule...")
        
        prompt = f"""You are an AI Architect. Read the following criticism of a failed trading thesis 
and distill it into a SINGLE, actionable, generalizing rule (maximum 2 sentences). 
This rule will be injected into our permanent memory bank so we never make this mistake again.

CRITICISM:
{state['criticism']}

OUTPUT ONLY THE FINAL RULE:"""
        
        response = self.llm.invoke([HumanMessage(content=prompt)])
        return {"final_lesson": response.content}

    def _injector_node(self, state: ReflexionState) -> Dict:
        self.logger.info("[Reflexion] Injector Node: Saving final lesson to ChromaDB Episodic Memory...")
        
        sector = state['quant_context'].get('sector', 'Unknown')
        regime = state['quant_context'].get('regime', 'Unknown')
        
        doc_id = self.memory.store_memory(
            ticker=state['ticker'],
            content=state['final_lesson'],
            sector=sector,
            regime=regime,
            outcome="Loss",
            memory_type="Correction_Rule"
        )
        self.logger.info(f"Saved lesson to Memory Bank ID: {doc_id}")
        return {}

    def run_autopsy(self, ticker: str, original_thesis: str, quant_context: Dict[str, Any], actual_outcome: str) -> str:
        """
        Main entrypoint. Runs the reflection suite and saves to memory.
        Returns the generated rule.
        """
        initial_state: ReflexionState = {
            "ticker": ticker,
            "original_thesis": original_thesis,
            "quant_context": quant_context,
            "actual_outcome": actual_outcome,
            "criticism": "",
            "final_lesson": ""
        }
        
        result = self.graph.invoke(initial_state)
        return result["final_lesson"]
