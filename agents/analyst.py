import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Dict, Any
from langchain_core.prompts import PromptTemplate
from langchain_anthropic import ChatAnthropic
from tools.market_api import AlpacaClient
from memory.db_helpers import MemoryManager
from config.manager import ConfigManager

class AnalystAgent:
    """
    Analyzes Research & Quant data.
    If 'Buy', generates an investment thesis and executes the trade.
    """
    def __init__(self):
        self.alpaca = AlpacaClient()
        self.db = MemoryManager()
        
        provider = os.getenv("ANTHROPIC_API_KEY")
        if not provider:
            raise ValueError("ANTHROPIC_API_KEY is not set.")
            
        self.llm = ChatAnthropic(
            model="claude-3-5-sonnet-20240620",
            temperature=0.2
        )
        
        self.thesis_prompt = PromptTemplate.from_template(
            "You are an expert algorithmic trading analyst. You are a strict {philosophy} investor. "
            "Reject any stock with a P/E over {max_pe_ratio}.\n\n"
            "Given the following data on {ticker}, write a structured 2-paragraph investment thesis "
            "detailing strictly why this asset is a BUY at this particular juncture based purely on these "
            "fundamentals and technicals. If the stock violates your philosophy or P/E constraints, state 'REJECTED' "
            "as the first word of your response followed by a brief 1-sentence explanation.\n\n"
            "Data Summary:\n"
            "Metrics: {metrics}\n"
            "Technicals: {technicals}\n"
            "Transcript Segment: {transcript}\n\n"
            "Output only the generated response, nothing else."
        )

    def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        ticker = state.get("ticker")
        quant_data = state.get("quant_data", {})
        research_data = state.get("research_data", {})
        
        if quant_data.get("decision") != "PROCEED":
            print(f"[Analyst] Quant signaled SKIP for {ticker}. Aborting.")
            state["analyst_decision"] = "SKIP"
            # Optional: Short generation if allowed, but long-only prototype here.
            return state
            
        shares = quant_data.get("recommended_shares", 0)
        if shares <= 0:
            print(f"[Analyst] Zero shares recommended for {ticker}. Aborting.")
            state["analyst_decision"] = "SKIP"
            return state
            
        print(f"[Analyst] Generating investment thesis for {ticker} (Quantity: {shares})...")
        
        try:
            # Load dynamic configuration constraints
            config = ConfigManager.load_config()
            
            # Generate Thesis
            prompt_val = self.thesis_prompt.format(
                philosophy=config.get("philosophy", "algorithmic"),
                max_pe_ratio=config.get("max_pe_ratio", 100),
                ticker=ticker,
                metrics=research_data.get("metrics"),
                technicals=research_data.get("technicals"),
                transcript=research_data.get("transcript_summary")
            )
            
            response = self.llm.invoke(prompt_val)
            thesis_text = response.content
            
            if thesis_text.startswith("REJECTED"):
                print(f"[Analyst] {ticker} rejected based on philosophy constraints: {thesis_text}")
                state["analyst_decision"] = "SKIP"
                state["thesis"] = thesis_text
                return state
                
            # Execute Trade
            print(f"[Analyst] Thesis generated. Submitting Market BUY for {shares} shares of {ticker}...")
            order = self.alpaca.execute_trade(symbol=ticker, qty=float(shares), side="buy")
            
            if order:
                # Log execution to SQLite
                self.db.log_trade(trade_data=order, exit_reason="INITIAL_ENTRY")
                
                # Store Vector Thesis to ChromaDB
                metadata = {
                    "shares": shares,
                    "order_id": order.get("id"),
                    "execution_price": order.get("filled_avg_price") or quant_data.get("latest_price")
                }
                self.db.store_thesis(symbol=ticker, thesis_text=thesis_text, metadata=metadata)
                
                print(f"[Analyst] Trade executed and thesis stored successfully.")
                state["analyst_decision"] = "BUY_EXECUTED"
                state["thesis"] = thesis_text
                state["order"] = order
            else:
                print(f"[Analyst] Trade execution failed for {ticker}.")
                state["analyst_decision"] = "EXECUTION_FAILED"
                
            return state
            
        except Exception as e:
            print(f"[Analyst] Error during execution: {e}")
            state["error"] = str(e)
            return state
