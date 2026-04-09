# Aegis AI V7: Current Build State & Component Map

*This document serves as the active memory for the state of the codebase. It tracks what has been built, where it lives, and its current status, enabling rapid context resumption.*

## 1. Directory Structure Map

The backend is structurally mature and follows the segmented engine pattern.

```text
Aegis_AI/
├── config/                  # Static configuration files
│   ├── llm_providers.yaml   # Contains the 7-tier static routing table (Groq, Google, Local, Anthropic)
│   └── templates/           # Baseline strategy templates
├── engines/                 # Core V7 Pipeline Engines
│   ├── analyst/             # The Intelligence Layer
│   │   ├── findebate/       # Adversarial audit protocol (Bull, Bear, Moderator)
│   │   └── scenario/        # Block bootstrap generator & stress testing
│   ├── data_ingestion/      # Point-in-time data gathering
│   │   ├── connectors/      # Source APIs (YFinance, FRED)
│   │   └── sanitization.py  # `public_disclosure_ts` enforcement logic
│   ├── simulation/          # The Mathematical Foundation
│   │   ├── loop.py          # Deterministic vectorized math looping
│   │   ├── metrics.py       # Sharpe, Sortino, basic metric computation
│   │   └── walk_forward.py  # anchored K-fold Walk-Forward Validator (WFE)
│   ├── system/              # Framework runtime logic
│   │   └── llm_router/      # Token tracking, quota management, and fallback execution
│   └── sentinel/            # Live execution & API
│       ├── health.py        # Connector Health Monitor & resource bounds
│       └── promotion_gate.py# Mathematical logic for rejecting/accepting strategies
├── scripts/                 # Independent runner paths
│   └── verify_phase5_e2e.py # Verification script containing our completed trace
└── ui/                      # (Pending Phase 5A)
```

## 2. Completed Backend Mechanics (Phase 1-5)

We have verified the entire backend pipeline via `scripts/verify_phase5_e2e.py`. The fundamental mechanics are locked:

*   ✅ **LLM Routing & Fallback:** Handled cleanly in `config/llm_providers.yaml`. Tiering is active (Qwen for local/basic, Llama for extraction, Kimi/Qwen32B/GPT-120B for deep reasoning). Degraded sessions are flagged.
*   ✅ **Simulation & Walk-Forward (WFE):** The `simulation/walk_forward.py` operates on K-fold chronological anchoring, explicitly replacing hardcoded stub values with live ML backtests. 
*   ✅ **Promotion Gate:** Evaluates constraints (WFE > 0.5, Target Max Drawdown, etc.) deterministically.
*   ✅ **FinDebate Protocol:** Agents engage adversarially without leaking limits.
*   ✅ **Data Pipeline:** Strict separation isolating future leakage, enforcing `public_disclosure_ts`.

## 3. Pending & Immediate Horizon (Phase 5A)

The backend runs silently and correctly. The user has no way to interact with it under the V7 paradigm. 

**Next Up: Phase 5A — Frontend Architecture (The Glass Box & Visual Pipeline Map)**
*   Build the *Intake Interface* (Path A & Path B Schema).
*   Construct the *Monitoring Canvas* (Connecting WebSockets to view the LangGraph execution flow live).
*   Develop the *Signal Card UI* for final binary ACCEPT/DECLINE.
