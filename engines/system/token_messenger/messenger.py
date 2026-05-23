import time
import secrets
from typing import Optional

from engines.system.token_messenger.models import WorkflowStage, WorkflowToken
from engines.system.token_messenger.store import _store
from api.routers.pipeline_events import broadcaster

class SequenceViolationError(Exception):
    """Raised when a token sequence is violated (skip, drift, replay, expiry)."""
    pass

class TokenMessenger:
    """
    Enforces cryptographic sequencing across the Aegis pipeline.
    Implements a consume-and-generate cycle where each token is a
    single-use credential with a 1-hour TTL.
    """
    
    def issue(self, workflow_id: str, stage: WorkflowStage, config_hash: str) -> str:
        """Issue a fresh single-use token for a workflow stage."""
        now = time.time()
        token = WorkflowToken(
            token_value=secrets.token_urlsafe(32),
            workflow_id=workflow_id,
            stage=stage,
            config_hash=config_hash,
            issued_at=now,
            expires_at=now + 3600.0,
            consumed=False
        )
        _store[workflow_id] = token
        return token.token_value

    def consume_and_issue(
        self,
        token_value: str,
        workflow_id: str,
        *args,
        **kwargs
    ) -> str:
        """
        Strictly consume the current token and issue the next one.
        Prevents stage skipping, config drift, replays, and expired workflows.
        """
        # Parse arguments dynamically to support both 5-argument, 6-argument, and keyword-based calls.
        node_id = "test"
        if "expected_stage" in kwargs:
            expected_stage = kwargs["expected_stage"]
            config_hash = kwargs["config_hash"]
            next_stage = kwargs["next_stage"]
            node_id = kwargs.get("node_id", "test")
        else:
            if len(args) == 4:
                node_id = args[0]
                expected_stage = args[1]
                config_hash = args[2]
                next_stage = args[3]
            elif len(args) == 3:
                expected_stage = args[0]
                config_hash = args[1]
                next_stage = args[2]
                node_id = kwargs.get("node_id", "test")
            else:
                raise TypeError("consume_and_issue expects either 5 or 6 positional arguments (or equivalent kwargs)")

        token: Optional[WorkflowToken] = _store.get(workflow_id)
        if not token:
            raise SequenceViolationError("No token found")
            
        if token.consumed:
            raise SequenceViolationError("Token already consumed")
            
        if token.token_value != token_value:
            raise SequenceViolationError("Token value mismatch")
            
        if token.stage != expected_stage:
            raise SequenceViolationError(f"Expected stage {expected_stage.value}, got {token.stage.value}")
            
        if token.config_hash != config_hash:
            raise SequenceViolationError("Config modified since token issued")
            
        if time.time() > token.expires_at:
            raise SequenceViolationError("Token expired")

        # Mark consumed before issuing next to prevent replay attacks
        token.consumed = True

        broadcaster.broadcast_sync({
            "event_id": f"evt_tok_{int(time.time()*1000)}",
            "workflow_id": workflow_id,
            "timestamp": str(time.time()),
            "event_type": "token_consumed",
            "node_id": node_id,
            "session_quality": "nominal",
            "token_type": expected_stage.value,
            "payload": {"status": "success"}
        })

        new_token = self.issue(workflow_id, next_stage, config_hash)

        broadcaster.broadcast_sync({
            "event_id": f"evt_tok_iss_{int(time.time()*1000)}",
            "workflow_id": workflow_id,
            "timestamp": str(time.time()),
            "event_type": "token_issued",
            "node_id": node_id,
            "session_quality": "nominal",
            "token_type": next_stage.value,
            "payload": {"status": "issued"}
        })

        return new_token
