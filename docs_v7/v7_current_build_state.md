# Aegis AI V7: Current Build State & Component Map

*This document serves as the active memory for the state of the codebase. It tracks what has been built, where it lives, and its current status, enabling rapid context resumption.*

*Last updated: 2026-05-02 after v6 cleanup.*

## 1. Directory Structure Map

The backend is structurally mature and follows the segmented engine pattern. The v6 analyst engine and its dependent scripts/tests have been archived to `_v6_archive/`.

```text
Aegis_AI/
├── _v6_archive/            # Archived v6 code (analyst, reflexion, episodic memory, etc.)
├── api/                    # FastAPI backend (14 routers)
│   ├── routers/            # Endpoint handlers
│   ├── schemas/            # Pydantic request/response models
│   └── services/           # Business logic (user profiles, crypto)
├── config/                 # Static configuration files
│   ├── llm_providers.yaml  # 11-provider static routing table with 21 role assignments
│   └── templates/          # Baseline strategy templates
├── engines/                # Core V7 Pipeline Engines (15 subdirectories)
│   ├── data_ingestion/     # Point-in-time data gathering (7 connectors)
│   ├── debate/             # FinDebate adversarial audit (Bull, Bear, Moderator)
│   ├── fundamental/        # Signal engines (SegmentAnchor, SignalGate, Earnings, Insider, Macro)
│   ├── intake/             # V7 Intake System (MandateProfile, UserIntent, ArchetypePool)
│   ├── models/             # Pydantic data models
│   ├── monitoring/         # Connector Health Monitor
│   ├── nli/                # DeBERTa NLI segment classifier
│   ├── plugins/            # Plugin layer
│   ├── quant/              # Quant models (HMM, Chronos, VPIN, Portfolio) — v7 integration pending
│   ├── sandbox/            # Subprocess isolation orchestrator
│   ├── sentinel/           # Live execution (PromotionGate, StateMgr, CloseSignal, Freshness, Mirror)
│   ├── simulation/         # Math foundation (Loop, Metrics, WalkForward, MLflow Logger)
│   ├── system/             # Runtime (LLM Router, Token Messenger, Scenario Generator, Telemetry)
│   └── vcl/                # Verified Component Library (Registry, 7 wrappers)
├── frontend/               # React + Vite + TailwindCSS
│   └── src/                # SetupPage (Command Center) — only page built so far
├── scripts/                # Independent runner scripts & verification suite
│   └── verify/             # 16 step-by-step verification scripts
├── tests/                  # Unit & integration tests
│   ├── unit/               # 19 test files (simulation, sentinel, intake, debate, etc.)
│   └── integration/        # 2 test files
└── docs_v7/                # Documentation & design references
    └── design_references/  # Archived stitch HTML prototypes
```

## 2. Completed Backend Mechanics (Phase 1-5)

Verified via `scripts/verify_phase5_e2e.py` and `scripts/verify/` suite:

*   ✅ **LLM Routing & Fallback:** `config/llm_providers.yaml` — 11 providers, 21 roles, Cerebras integrated.
*   ✅ **Simulation & Walk-Forward (WFE):** Vectorized backtest + anchored K-fold WFE.
*   ✅ **Promotion Gate:** 3-stage deterministic gate (Backtest → Proving Ground → Live).
*   ✅ **FinDebate Protocol:** Evidentiary rubric, Bear win rate monitoring, anti-rubber-stamp.
*   ✅ **Data Pipeline:** 7 connectors with strict `public_disclosure_ts` enforcement.
*   ✅ **VCL SDK:** 5-gate import verification, 7 wrappers registered.
*   ✅ **Token Messenger:** Cryptographic chaining across pipeline stages.
*   ✅ **Scenario Battery:** Block bootstrap generator with pass rate gating.
*   ✅ **Intake System:** MandateProfile, UserIntent, Contradiction detection, ArchetypePool.
*   ✅ **Signal Freshness:** Live price validator with volatility-bucketed thresholds.

## 3. Archived v6 Code (`_v6_archive/`)

The following v6 components have been archived — they conflict with v7's autonomous pipeline design:

*   `analyst/` — AgenticSupervisor, AnalystNode, RiskManager, Reflexion, EpisodicMemory, LocalWorker, ImprovementAgent
*   `scripts/` — 7 v6-specific test/demo scripts
*   `tests/` — 8 v6-specific unit/integration tests

**Key risk removed:** `reflexion.py` was importing `ChatAnthropic` directly, which would burn the $20 Claude budget on every autopsy call.

## 4. Pending & Immediate Horizon (Phase 5A)

**Next Up: Phase 5A — Frontend Architecture**
*   Build the *Intake Interface* (Path A & Path B Schema).
*   Construct the *Mission Control* canvas (WebSocket → live pipeline events).
*   Develop the *Glass Box* (audit trail as product).
*   Build the *Signal Card UI* for ACCEPT/DECLINE.
*   Create *Debate Theater*, *Budget Dashboard*, *Arena*, *Pipeline Map*.
