# Aegis AI V7 Architecture & Memory Summary

The pivot from v6 to v7 transforms Aegis from a human-in-the-loop strategy builder into a **fully autonomous AI pipeline** where the human only sets the mandate and makes the final binary executing decision.

## 1. The Core Intake Models
The human guides the system via two data structures resulting from the intake process:

* **`MandateProfile`**: Frozen, hard mathematical constraints. (e.g., `max_drawdown_target`, `max_position_pct`, `risk_tolerance`). The system **never** violates these.
* **`UserIntent`**: Soft preferences used to guide the `Builder` on what to explore (e.g., sectors of interest, catalyst types, macro views).

## 2. Seven-Tier Capability Architecture
Aegis relies on an explicit hierarchy of free-tier/local foundation models to route specific agent roles:

| Tier | Provider/Model | Primary Roles | Quotas / Context |
|---|---|---|---|
| **0 - Local** | `local/qwen3:8b` (Ollama) | Terminal fallback, JSON parsing, basic routing | Unlimited / 0 latency |
| **1 - Fast** | `groq/llama-4-scout` | Semantic validation, structured extraction | 1K RPD @ 30 RPM |
| **2 - Strong** | `groq/qwen3-32b` | Strategy Generation, Improvement Analyzer, Bear | 1K RPD @ 60 RPM |
| **3 - Adversarial**| `groq/kimi-k2` | Bear alternative, Auditor | 1K RPD @ 60 RPM |
| **4 - Frontier** | `groq/gpt-oss-120b` | Debate Moderator, Final Audit Score | 1K RPD @ 30 RPM |
| **5 - Massive** | `gemini-2.5-flash` | Large context tasks (10-K ingestion, world events)| 500 RPD / 1M token |
| **6 - Overflow** | `openrouter/:free` | Quick fallback exhaustion pool | 200 RPD |
| **7 - Emergency** | `claude-sonnet-4-6`| Irreversible split-decisions / tie-breaking | $20 fixed budget |

### Critical Degradation Handling
If primary models exhaust their daily limits on **critical** reasoning roles (Strategy Gen, Moderator, Final Audit, Improvement Analyzer), pipeline executes but the run gets flagged as `degraded` or `severely_degraded`. The Promotion Gate will **hold/reject** these runs, waiting for quotas to reset instead of surfing off weak strategies.

## 3. The Execution Pipeline (Token Messenger)
LangGraph boundaries are not enough to enforce structure. Aegis uses **cryptographic token chaining** across steps:

1. `Builder` generates `StrategyConfig` → **`Schema Validator`**
2. **`Quick Iteration Backtest`** evaluates using purely mathematical simulation logic (loop).
3. **`Full Production Backtest`** computes real walk-forward metrics across all splits. If passing mathematical gates → `[backtest_token]`.
4. **`FinDebate Orchestrator`** triggers adversarial debate context via the tokens.
5. **`Bootstrap Scenario Battery`** runs robust ML scenario models.
6. **`Promotion Gate`** consumes all output + `session_quality` rating. Passes gate → `[promotion_token]`.
7. **`Sentinel Deployment`** utilizes `promotion_token` to monitor live variables.

## 4. Design Tenets to Memorize
* **Point-in-Time Non-Negotiable**: Filter all lookup data via `public_disclosure_ts`.
* **State over Memory**: Agents have no context history other than `AegisState` passing structure.
* **Compress Context**: Agent text must be filtered to `pydantic` schemas before handoffs to respect strict token allocations.
* **Component SDK Strictness**: (VCL) verified tools only; agents *cannot* write inline logic.
