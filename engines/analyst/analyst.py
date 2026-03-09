import json
from typing import Dict, Any
from langchain_core.messages import SystemMessage, HumanMessage
from engines.analyst.state import AgentState

class AnalystNode:
    """
    Research Agent. Translates the fundamental Phase 1 context into a 
    trading thesis and conviction score.
    """
    def __init__(self, llm):
        self.llm = llm
        
    def __call__(self, state: AgentState) -> Dict[str, Any]:
        ticker = state["ticker"]
        date = state["date"]
        context_str = json.dumps(state["fundamental_context"], indent=2, default=str)
        
        system_prompt = f"""You are the Aegis Fundamental Analyst.
Analyze the provided fundamental data for {ticker} as of {date}.
You MUST output your decision as a JSON object matching this schema EXACTLY:
{{
  "action": "BUY" | "SELL" | "HOLD",
  "conviction": float (0.0 to 1.0),
  "rationale": "Clear, data-backed 2-sentence explanation."
}}
Return ONLY valid JSON and nothing else. No markdown blocks."""

        user_prompt = f"Fundamental Context:\n{context_str}\n\nWhat is your proposal?"
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        
        response = self.llm.invoke(messages)
        content = response.content.strip()
        
        # Clean up potential markdown formatting from Qwen
        if content.startswith("```json"):
            content = content[7:-3]
        elif content.startswith("```"):
            content = content[3:-3]
            
        try:
            proposal = json.loads(content)
            # Ensure types
            if "action" not in proposal: proposal["action"] = "HOLD"
            if "conviction" not in proposal: proposal["conviction"] = 0.0
            if "rationale" not in proposal: proposal["rationale"] = "Failed to parse rationale."
            
            trace_entry = f"[Analyst]: Proposed {proposal['action']} (Conviction: {proposal['conviction']}). Rationale: {proposal['rationale']}"
        except Exception as e:
            proposal = {
                "action": "HOLD",
                "conviction": 0.0,
                "rationale": f"JSON Parse Error: {e}. Raw output: {content}"
            }
            trace_entry = f"[Analyst ERROR]: {proposal['rationale']}"
            
        return {
            "analyst_proposal": proposal,
            "reasoning_trace": [trace_entry]
        }
