# Aegis AI — Documentation Index

> **Primary Blueprint:** [`/aegis_v6.md`](../aegis_v6.md) — Read this first. It is the source of truth for every design decision.

---

## Phase Mini-Blueprints

Each file is a self-contained, actionable spec for one build phase. Read the primary blueprint for *why*. Read the phase blueprint for *what to build, in what order, and how to know when it's done*.

| Phase | File | Status | Description |
|---|---|---|---|
| Phase 1 | [PHASE_1_MATHEMATICAL_FOUNDATION.md](./PHASE_1_MATHEMATICAL_FOUNDATION.md) | 🔨 **Current** | Point-in-time connectors, config schema, Fundamental Engine, simulation loop, metrics, MLflow |
| Phase 2 | [PHASE_2_INTELLIGENCE_LAYER.md](./PHASE_2_INTELLIGENCE_LAYER.md) | ⬜ Not started | Signal gate, Model Routing, Uncertainty Scorer, LangGraph, Improvement Analyzer, Scenario Library |
| Phase 3 | [PHASE_3_CUSTOM_ENGINE_SDK.md](./PHASE_3_CUSTOM_ENGINE_SDK.md) | ⬜ Not started | BaseEngine contract, registry, wrapper sandbox, Glass Box integration, health monitor wiring |
| Phase 4 | [PHASE_4_SENTINEL_LAYER.md](./PHASE_4_SENTINEL_LAYER.md) | ⬜ Not started | Connector health monitor, Sentinel state manager, Mirror Portfolio, Signal Cards, Promotion Gate |
| Phase 5 | [PHASE_5_FRONTEND.md](./PHASE_5_FRONTEND.md) | ⬜ Not started | Sandbox view, Signal Cards UI, Mirror Portfolio, MLflow Arena, Engine Library, Wizard |

---

## Other Docs

| File | Description |
|---|---|
| [BUILD_LOG.md](./BUILD_LOG.md) | Running log of what has been built, decisions made, and what was archived |
| [ARCHITECTURE_DECISIONS.md](./ARCHITECTURE_DECISIONS.md) | Key design choices and their rationale |

---

## Quick Reference Rules (from the blueprint)

These never change. If any code violates them, fix the code.

1. **`public_disclosure_ts` everywhere** — simulation loop uses only this field. `trade_date` is never used.
2. **Slippage is always real** — every run, every tier, no exceptions. Slippage Drag shown alongside gross return.
3. **Signal gate first, LLM second** — LangGraph only fires on gated events. Never on every tick.
4. **Held-out window is sealed** — 20% randomly partitioned at run start. Invisible until promotion.
5. **Build Mode costs $0** — Claude never invoked during development or Quick Runs.
6. **Paper always executes** — real money only moves if user explicitly mirrors.
7. **Close signals are first class** — same design weight as BUY signals.
