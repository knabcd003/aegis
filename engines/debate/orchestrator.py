import json
from typing import Callable, Any, List
from engines.system.llm_router.router import ProviderRouter
from engines.debate.models import DebateRound, DebateVerdict
from engines.debate.compressor import DebateCompressor
from engines.debate.agents import BullAgent, BearAgent, ModeratorAgent
from engines.system.token_messenger.messenger import TokenMessenger
from engines.system.token_messenger.models import WorkflowStage

class FinDebateOrchestrator:
    """
    Executes the 4-round adversarial FinDebate protocol.
    Integrates directly with TokenMessenger pipeline (BACKTEST -> AUDIT -> PROMOTION).
    """
    def __init__(
        self, 
        router: ProviderRouter, 
        llm_invoker: Callable[[str, str, str], str],
        token_messenger: TokenMessenger,
        mlflow_client: Any = None
    ):
        self.router = router
        self.llm_invoker = llm_invoker
        self.messenger = token_messenger
        self.mlflow_client = mlflow_client
        
        self.bull = BullAgent(router, llm_invoker)
        self.bear = BearAgent(router, llm_invoker)
        self.moderator = ModeratorAgent(router, llm_invoker)
        self.compressor = DebateCompressor(router, llm_invoker)

    def run_debate(
        self,
        token_value: str,
        workflow_id: str,
        config_hash: str,
        strategy_manifest: str,
        num_rounds: int = 4
    ) -> DebateVerdict:
        """
        Consumes BACKTEST token, runs the debate loop (with compression),
        invokes Moderator, logs to MLflow, and issues AUDIT token.
        """
        # 1. Consume BACKTEST token early to validate sequence integrity
        audit_token_value = self.messenger.consume_and_issue(
            token_value=token_value,
            workflow_id=workflow_id,
            expected_stage=WorkflowStage.BACKTEST,
            config_hash=config_hash,
            next_stage=WorkflowStage.AUDIT
        )
        
        rounds: List[DebateRound] = []
        transcript = ""
        
        # 2. 4-Round Debate Loop
        for i in range(1, num_rounds + 1):
            # Bull Turn
            raw_bull = self.bull.generate_argument(strategy_manifest, transcript)
            compressed_bull = self.compressor.compress_to_schema(raw_bull, "bull")
            
            # Bear Turn
            raw_bear = self.bear.generate_argument(strategy_manifest, transcript)
            compressed_bear = self.compressor.compress_to_schema(raw_bear, "bear")
            
            # Record Round
            round_data = DebateRound(
                round_number=i,
                bull_arguments=compressed_bull,
                bear_arguments=compressed_bear
            )
            rounds.append(round_data)
            
            # Append strictly the compressed schema representations to the transcript
            # so the context Window stays under ~3K tokens for the next round.
            transcript += f"\nRound {i} Summary:\n{round_data.model_dump_json(indent=2)}\n"

        # 3. Moderator Judgment
        raw_judgment = self.moderator.evaluate_debate(strategy_manifest, transcript)
        
        # Parse JSON Verdict
        try:
            judgment_json = raw_judgment.replace("```json", "").replace("```", "").strip()
            data = json.loads(judgment_json)
            verdict = DebateVerdict(**data)
        except Exception as e:
            # Fallback to REJECT if Moderator fundamentally fails
            verdict = DebateVerdict(
                confidence_score=0,
                verdict="REJECT",
                bull_evidentiary_score=0.0,
                bear_evidentiary_score=0.0,
                bull_strongest_point="N/A",
                bear_strongest_point="N/A",
                deciding_factor=f"Moderator Parse Failure: {e}",
                debate_integrity="COMPROMISED",
                required_revisions=["Fix Moderator output format"]
            )

        # 4. Bear Win Rate Telemetry (Glass Box)
        # Note: A Bear win is defined as the strategy being REJECTED.
        bear_won = (verdict.verdict == "REJECT")
        if self.mlflow_client:
            try:
                # Log to the active run. We abstract active run handling inside the MLflow client.
                self.mlflow_client.log_metric("bear_won", float(bear_won))
            except Exception:
                pass

        # 5. Token Messenger: Return the issued AUDIT token alongside verdict.
        # The Promotion Gate will now be waiting to consume this AUDIT token.
        return verdict, audit_token_value
