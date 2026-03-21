import json
from typing import List, Callable, Any
from pydantic import ValidationError
from engines.debate.models import DebateArgumentScore
from engines.system.llm_router.router import ProviderRouter

class DebateCompressor:
    """
    Compresses verbose LangGraph/LLM string outputs into terse, structured DebateRound
    Pydantic schemas to strictly cap context windows.
    """
    def __init__(self, router: ProviderRouter, llm_invoker: Callable[[str, str, str], str]):
        self.router = router
        self.llm_invoker = llm_invoker

    def compress_to_schema(self, raw_text: str, agent_role: str) -> List[DebateArgumentScore]:
        if not raw_text.strip():
            return []

        # Get the fast model for structured extraction (groq/llama-4-scout)
        decision = self.router.get_provider_for_role("debate_compression")
        
        prompt = (
            f"Extract the core claims from the following {agent_role} argument. "
            "Output strictly as a JSON array of objects. Do not include markdown formatting.\n"
            "Each object must have:\n"
            "- argument_id: a unique string like 'arg_1'\n"
            f"- agent: '{agent_role}'\n"
            "- claim: concise summary of the point\n"
            "- evidence_type: one of [backtest_data, historical_analogy, cited_scenario, general_principle, assertion_only]\n"
            "- evidence_specific: true if exact numbers/dates are cited, else false\n"
            "- falsifiable: true if the claim could mechanically be proven false\n\n"
            f"Raw text:\n{raw_text}"
        )

        try:
            # Mockable LLM invocation boundary (real HTTP wired in Phase 5.8)
            response_text = self.llm_invoker(decision.provider_id, decision.model_id, prompt)
            
            # Clean possible markdown block
            response_text = response_text.replace("```json", "").replace("```", "").strip()
            data = json.loads(response_text)
            
            if not isinstance(data, list):
                return []
                
            return [DebateArgumentScore(**item) for item in data]
            
        except (json.JSONDecodeError, ValidationError) as e:
            # Fallback or alert if compression fails
            raise RuntimeError(f"Failed to compress debate round: {e}")
