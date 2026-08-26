from typing import Callable
from engines.system.llm_router.router import ProviderRouter

class BullAgent:
    def __init__(self, router: ProviderRouter, llm_invoker: Callable[[str, str, str], str]):
        self.router = router
        self.llm_invoker = llm_invoker
        
    def generate_argument(self, strategy_manifest: str, previous_rounds: str) -> str:
        decision = self.router.get_provider_for_role("debate_bull")
        prompt = (
            "You are a long-only fund manager. You MUST find at least 3 compelling reasons "
            "this strategy succeeds. Every claim must cite specific data from the backtest results "
            "— round number, date range, or metric. Unanchored assertions will score zero. "
            "You are prohibited from dwelling on risks.\n"
            "NOTE: If any metric is flagged with `low_confidence: true` due to trade_count < 20, "
            "you MUST discount its evidentiary weight and acknowledge sample-size limitations.\n\n"
            f"Strategy Manifest:\n{strategy_manifest}\n\n"
            f"Previous Debate Rounds:\n{previous_rounds}\n\n"
            "State your case:"
        )
        return self.llm_invoker(decision.provider_id, decision.model_id, prompt)

class BearAgent:
    def __init__(self, router: ProviderRouter, llm_invoker: Callable[[str, str, str], str]):
        self.router = router
        self.llm_invoker = llm_invoker
        
    def generate_argument(self, strategy_manifest: str, previous_rounds: str) -> str:
        decision = self.router.get_provider_for_role("debate_bear")
        prompt = (
            "You are a short-seller who survived three market crashes. You are prohibited from saying "
            "anything positive. Find every way this strategy fails. REQUIRED: specific numerical evidence "
            "for every critique — a historical date range, a specific scenario from the battery, a specific "
            "metric from the backtest. 'This could fail' without data scores zero on the evidentiary rubric.\n"
            "NOTE: If any metric is flagged with `low_confidence: true` due to trade_count < 20, "
            "exploit this low sample size as evidence of statistical weakness.\n\n"
            f"Strategy Manifest:\n{strategy_manifest}\n\n"
            f"Previous Debate Rounds:\n{previous_rounds}\n\n"
            "Rip this strategy apart:"
        )
        return self.llm_invoker(decision.provider_id, decision.model_id, prompt)

class ModeratorAgent:
    def __init__(self, router: ProviderRouter, llm_invoker: Callable[[str, str, str], str]):
        self.router = router
        self.llm_invoker = llm_invoker
        
    def evaluate_debate(self, strategy_manifest: str, debate_transcript: str) -> str:
        decision = self.router.get_provider_for_role("debate_moderator")
        prompt = (
            "You are the Moderator. Evaluate the arguments on the evidentiary rubric, not on argumentative quality. "
            "Score arguments by evidentiary weight. A well-written assertion with no data is worth less than a "
            "clumsy citation of a specific backtest metric.\n"
            "CRITICAL: If a metric is flagged `low_confidence: true` (trade_count < 20), discount its evidentiary weight. "
            "Determine a final verdict (APPROVE, REJECT, REVISE).\n\n"
            "CRITICAL INTEGRITY CHECK: If both bull_evidentiary_score and bear_evidentiary_score exceed 0.6 "
            "and both agents argue in the same direction, you MUST flag `debate_integrity: 'COMPROMISED'`.\n\n"
            f"Strategy Manifest:\n{strategy_manifest}\n\n"
            f"Debate Transcript:\n{debate_transcript}\n\n"
            "Output strictly as a JSON object matching the DebateVerdict schema:\n"
            "{'confidence_score': 0-100, 'verdict': 'APPROVE'|'REJECT'|'REVISE', 'bull_evidentiary_score': 0.0-1.0, "
            "'bear_evidentiary_score': 0.0-1.0, 'bull_strongest_point': '...', 'bear_strongest_point': '...', "
            "'deciding_factor': '...', 'debate_integrity': 'NOMINAL'|'COMPROMISED', 'required_revisions': []}"
        )
        return self.llm_invoker(decision.provider_id, decision.model_id, prompt)
