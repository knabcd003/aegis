"""
Declarative LangGraph Supervisor for the Analyst Engine.
Uses Claude to orchestrate local worker agents based on a YAML configuration.
"""

import os
import yaml
import json
import logging
from typing import Dict, Any, List, TypedDict, Annotated
from operator import add

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, END

from engines.analyst.local_worker import LocalWorker
from engines.analyst.episodic_memory import EpisodicMemory

logger = logging.getLogger(__name__)

# Define the LangGraph State
class AnalystState(TypedDict):
    ticker: str
    quant_data: Dict[str, Any]
    worker_outputs: Dict[str, str]
    messages: Annotated[List[BaseMessage], add]
    config: Dict[str, Any]

class AnalystSupervisor:
    def __init__(self, config_path: str = "config/experiment_config.yaml", memory: EpisodicMemory = None):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.config = self._load_config(config_path)
        
        # Load APIs and Models
        self.supervisor_model = self.config.get("analyst_engine", {}).get("supervisor_llm", "claude-sonnet-4-6")
        self.worker_model = self.config.get("analyst_engine", {}).get("worker_llm", "qwen2.5")
        self.active_nodes = self.config.get("analyst_engine", {}).get("active_nodes", [])
        
        if not os.environ.get("ANTHROPIC_API_KEY"):
            raise ValueError("ANTHROPIC_API_KEY environment variable not set. Please add it to your .env file.")
            
        self.llm = ChatAnthropic(model_name=self.supervisor_model, temperature=0.1)
        self.worker = LocalWorker(model_name=self.worker_model, use_cache=True)
        self.memory = memory or EpisodicMemory()
        
        # Build Graph
        self.graph = self._build_graph()

    def _load_config(self, path: str) -> Dict[str, Any]:
        with open(path, "r") as f:
            return yaml.safe_load(f)

    def _build_graph(self):
        workflow = StateGraph(AnalystState)
        
        # Add Supervisor Node
        workflow.add_node("supervisor", self._supervisor_node)
        
        # Add Conditional Worker Nodes
        if "fundamentals_reader" in self.active_nodes:
            workflow.add_node("fundamentals_reader", self._fundamentals_node)
        if "sentiment_analyzer" in self.active_nodes:
            workflow.add_node("sentiment_analyzer", self._sentiment_node)
            
        # Define Edges
        workflow.set_entry_point("supervisor")
        workflow.add_conditional_edges("supervisor", self._route_from_supervisor)
        
        # Connect workers back to supervisor
        for node in self.active_nodes:
            if node in ["fundamentals_reader", "sentiment_analyzer"]:
                workflow.add_edge(node, "supervisor")
                
        return workflow.compile()

    def _get_system_prompt(self, state: AnalystState) -> str:
        regime = state["quant_data"].get("regime", "Unknown")
        sector = state["quant_data"].get("sector", "Unknown")
        
        # Check Memory for past mistakes
        lessons = self.memory.retrieve_lessons(sector=sector, regime=regime, outcome="Loss", n_results=3)
        memory_str = "None found." if not lessons else "\n".join([f"- {l['content']}" for l in lessons])
        
        # List of available tools
        workers_list = ", ".join(self.active_nodes) if self.active_nodes else "None configured"

        # Prevent massive raw strings from bloating Claude's prompt (save $$$).
        # We only pass these to the local Ollama agents.
        clean_quant = {k: v for k, v in state['quant_data'].items() if not k.startswith("raw_")}

        prompt = f"""You are the Aegis AI Principal Analyst.
Your job is to read Quantitative Engine data and sub-agent reports to make a final BUY/SELL/HOLD decision.

CURRENT CONTEXT:
Ticker: {state['ticker']}
Regime: {regime}
Sector: {sector}

QUANTITATIVE DATA:
{json.dumps(clean_quant, indent=2)}

SUB-AGENT REPORTS:
{json.dumps(state['worker_outputs'], indent=2)}

AVAILABLE LOCAL WORKERS IN THIS CONFIG:
{workers_list}

PAST MISTAKES IN THIS REGIME / SECTOR:
{memory_str}

INSTRUCTIONS:
1. If you need more fundamental analysis and 'fundamentals_reader' is active but hasn't reported yet, output EXACTLY: `CALL_WORKER: fundamentals_reader`
2. If you need news context and 'sentiment_analyzer' is active but hasn't reported yet, output EXACTLY: `CALL_WORKER: sentiment_analyzer`
3. DO NOT CALL A WORKER THAT HAS ALREADY PROVIDED A REPORT.
4. If you have enough information, output a final JSON decision wrapped in ```json ... ``` with keys: 
   "decision": ("BUY"/"SELL"/"HOLD"), "confidence": (0-1.0), "reasoning": (string)

Do NOT hallucinate math. Rely strictly on the Quant Data. Learn from past mistakes.
"""
        return prompt

    def _supervisor_node(self, state: AnalystState) -> Dict:
        self.logger.info("[Supervisor] Claude is evaluating the state...")
        sys_prompt = self._get_system_prompt(state)
        
        # Construct the call to Claude
        prompt_msgs = [SystemMessage(content=sys_prompt)] + state.get("messages", [])
        
        response = self.llm.invoke(prompt_msgs)
        return {"messages": [AIMessage(content=response.content)]}

    def _route_from_supervisor(self, state: AnalystState) -> str:
        last_msg = state["messages"][-1].content
        worker_outputs = state.get("worker_outputs", {})
        
        if "CALL_WORKER: fundamentals_reader" in last_msg and "fundamentals_reader" in self.active_nodes:
            if "fundamentals_reader" not in worker_outputs:
                self.logger.info("[Router] Routing to Fundamentals Worker (Qwen 2.5)")
                return "fundamentals_reader"
            else:
                self.logger.warning("[Router] Claude tried to call fundamentals_reader twice. Forcing END.")
                return END
                
        elif "CALL_WORKER: sentiment_analyzer" in last_msg and "sentiment_analyzer" in self.active_nodes:
            if "sentiment_analyzer" not in worker_outputs:
                self.logger.info("[Router] Routing to Sentiment Worker (Qwen 2.5)")
                return "sentiment_analyzer"
            else:
                self.logger.warning("[Router] Claude tried to call sentiment_analyzer twice. Forcing END.")
                return END
            
        if "```json" in last_msg or "decision" in last_msg.lower():
            self.logger.info("[Router] Decision reached. Ending evaluation.")
            return END
            
        self.logger.warning("[Router] Unrecognized instruction or hallucination. Ending to prevent loop.")
        return END

    def _fundamentals_node(self, state: AnalystState) -> Dict:
        self.logger.info("[Worker] Fundamentals Reader analyzing raw string...")
        raw_text = state["quant_data"].get("raw_fundamentals_text", "No raw fundamentals provided.")
        query = "Summarize the key growth drivers and risk factors from this fundamental data."
        output = self.worker.extract_information(raw_text, query)
            
        new_outputs = state.get("worker_outputs", {}).copy()
        new_outputs["fundamentals_reader"] = output
        return {"worker_outputs": new_outputs, "messages": [HumanMessage(content=f"Fundamentals Worker Output:\n{output}")]}

    def _sentiment_node(self, state: AnalystState) -> Dict:
        self.logger.info("[Worker] Sentiment Analyzer evaluating raw string...")
        raw_text = state["quant_data"].get("raw_news_text", "No raw news provided.")
        query = "Summarize the prevailing sentiment and identify any immediate catalysts or red flags."
        output = self.worker.extract_information(raw_text, query)
            
        new_outputs = state.get("worker_outputs", {}).copy()
        new_outputs["sentiment_analyzer"] = output
        return {"worker_outputs": new_outputs, "messages": [HumanMessage(content=f"Sentiment Worker Output:\n{output}")]}

    def evaluate_trade(self, ticker: str, quant_data: Dict[str, Any]) -> str:
        """
        Main entrypoint. Injects initial state and runs the LangGraph to completion.
        """
        initial_state: AnalystState = {
            "ticker": ticker,
            "quant_data": quant_data,
            "worker_outputs": {},
            "messages": [HumanMessage(content="Evaluate this ticker and make a final trading decision.")],
            "config": self.config
        }
        
        result = self.graph.invoke(initial_state)
        return result["messages"][-1].content
