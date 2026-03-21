from typing import Dict
from engines.system.token_messenger.models import WorkflowToken

# Store — ephemeral in-memory dict, not persisted.
# Tokens are intentionally ephemeral. If the process restarts,
# all in-flight workflows must restart from backtest.
# This prevents stale backtests from being deployed hours later.
_store: Dict[str, WorkflowToken] = {}
