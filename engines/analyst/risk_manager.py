import json
from typing import Dict, Any
from langchain_core.messages import SystemMessage, HumanMessage
from engines.analyst.state import AgentState

class RiskManagerNode:
    """
    Risk Agent. Vetoes overly aggressive Analyst proposals if the macro
    environment or recent drawdowns look dangerous.
    """
    def __init__(self, llm):
        self.llm = llm
        
    def __call__(self, state: AgentState) -> Dict[str, Any]:
        ticker = state["ticker"]
        proposal = state.get("analyst_proposal", {})
        
        # If Analyst said HOLD, no need for Risk to veto a non-trade
        if proposal.get("action", "HOLD") == "HOLD":
            return {
                "risk_veto": False,
                "reasoning_trace": ["[Risk]: Analyst proposed HOLD. Auto-approving."]
            }
            
        # Extract subset of macro data for risk
        macro = state["fundamental_context"].get("macro", {})
        macro_str = json.dumps(macro, indent=2, default=str)
        
        system_prompt = f"""You are the Aegis Risk Manager.
The Analyst wants to {proposal.get('action')} {ticker} with conviction {proposal.get('conviction')}.
Analyst Rationale: {proposal.get('rationale')}

Look at the Macro conditions. If the environment is highly inverted or tightening fast, you must VETO the trade by returning TRUE.
Otherwise, return FALSE.

You MUST format your output as exactly valid JSON matching this schema:
{{
  "veto": true | false,
  "rationale": "1 sentence explanation."
}}
Return ONLY valid JSON."""

        user_prompt = f"Macro Context:\n{macro_str}\n\nDo you veto?"
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        
        response = self.llm.invoke(messages)
        content = response.content.strip()
        
        # Parse JSON output
        if content.startswith("```json"):
            content = content[7:-3]
        elif content.startswith("```"):
            content = content[3:-3]
            
        try:
            risk_decision = json.loads(content)
            veto = bool(risk_decision.get("veto", False))
            rationale = risk_decision.get("rationale", "No rationale provided.")
            
            verb = "VETOED" if veto else "APPROVED"
            trace_entry = f"[Risk]: {verb}. Rationale: {rationale}"
        except Exception as e:
            # Fall fail-safe open for sandbox so bugs don't freeze all trading
            veto = False
            trace_entry = f"[Risk ERROR]: Failed to parse JSON, defaulting to approved. Error: {e}. Raw: {content}"
            
        # Update final decision if vetoed
        final_decision = dict(proposal)
        if veto:
            final_decision["action"] = "HOLD"
            final_decision["conviction"] = 0.0
            
        return {
            "risk_veto": veto,
            "final_decision": final_decision,
            "reasoning_trace": [trace_entry]
        }
