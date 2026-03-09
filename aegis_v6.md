# AEGIS AI — Comprehensive System Blueprint v6.1

**The one-line thesis:** A personal portfolio management system where retail investors build, battle-test, and deploy their own AI-powered trading strategies as paper portfolio managers — then choose, trade by trade, whether to mirror those positions into real money.

---

## PREFACE: Why This Document Exists and How to Read It

This is the sixth iteration of a blueprint that has progressively corrected its own misunderstandings of what it was building.

**v3** described a quant hedge fund toolkit — signal generators, VPIN, HMM, institutional microstructure tools applied to a retail context. It was technically sophisticated and practically wrong for the user it was supposed to serve.

**v4** overcorrected into a thesis-monitoring platform. It spent enormous design energy on a thesis wizard and Sentinel breach alerts, implicitly assuming users already owned positions they wanted to monitor. It forgot to clearly specify how positions got opened in the first place.

**v5** corrected the mental model — the Sentinel as paper portfolio manager, buy and close signals as first-class outputs — and upgraded the local model to Qwen 2.5 14B. But it left the Custom Engine SDK as a vague mention and the Claude cost problem as an afterthought.

**v6** completes all three corrected ideas:

1. **The right mental model, fully specified.** The Sentinel is a paper portfolio manager. You build the system. You test it. You trust it. It generates complete position recommendations — entry, size, expected hold, exit conditions. You accept or decline each one. Paper always executes. Real money only moves if you choose to mirror it.

2. **A Custom Engine SDK with a formal wrapper contract.** Bring any model, pipeline, or signal logic into the system. The wrapper enforces the boundary — defined inputs, defined outputs, health reporting, Glass Box integration — so the rest of Aegis treats your custom engine as a first-class participant.

3. **An intelligent validation budget system.** You have $30 of Claude API credit. A naive architecture burns through it in 6 backtests. An intelligent one allocates Claude to the signals where its reasoning actually changes the output, routes everything else to Qwen 2.5 14B locally, and gives you 20+ full validation runs before you've spent $20.

Everything that was right in v3 and preserved through v5 remains unchanged here. The engineering foundations — point-in-time discipline, slippage simulation, two-phase backtests, MLflow logging, LangGraph topology, the Glass Box principle — are not touched. Version history is documented in Part XVII.

---

## PART I: PRODUCT VISION

### 1.1 The Correct Mental Model

You are building a system. Not receiving someone else's signals. Not following an AI's recommendations about what the market is doing. Building your own pipeline — your own data sources, your own quant models, your own AI agents, your own signal logic — that watches the market on your behalf and tells you specifically what to do: buy this ticker, this many shares, at this price, hold for this long, exit when this condition is met.

You build it yourself. You understand what it does and why. You test it exhaustively — against two years of history, against specific adverse market conditions, against the live market in paper trading — until you either trust it or you've learned enough to fix it. When you trust it, you deploy it as a live paper portfolio manager. It manages a paper account initialized at whatever capital you declare — say $5,000. Every position recommendation it generates executes automatically in that paper account. You see the paper account grow or shrink in real time.

Every time it generates a signal — BUY 20 shares of NVDA, or CLOSE your AAPL position now — you receive a Signal Card. You review the full reasoning chain. You decide whether to mirror that trade in your real brokerage account. Paper always executes whether you mirror or not. Your real account only moves if you explicitly choose it.

This is the complete mental model. Everything in the architecture serves it.

### 1.2 What Makes This Different

**Quantopian and QuantConnect** gave you a backtesting environment and a research community. They did not give you a system you could deploy as a live portfolio manager for your personal accounts. They were research platforms that ended at "here are your backtest results."

**Signal services** (newsletters, Discord groups, paid alerts) give you someone else's recommendations delivered as signals you cannot audit, cannot understand, and cannot improve. When they're wrong, you have no path to diagnosis.

**Brokerage paper trading** gives you a single fake account with no AI, no systematic signal generation, no improvement loop, no Glass Box, no MLflow history.

**Aegis gives you all three combined**: a rigorous build-and-test environment, a deployed system that acts as your portfolio manager, and complete auditability of every decision the system has ever made. The trust comes from the build process, not from the platform's authority.

### 1.3 The Full Lifecycle

```
BUILD → BACKTEST → ITERATE → PROVE → PROMOTE → DEPLOY → SIGNAL → ACCEPT/DECLINE → MIRROR
```

| Stage | What Happens | Who Acts | Cost |
|---|---|---|---|
| Build | Configure pipeline from Engine Library | User | $0 |
| Backtest | Historical simulation — vectorized + event-gated LLM | Agents | $0–$1 per run |
| Iterate | Improvement Analyzer proposes changes; user approves/rejects | Agents propose / User decides | $0 |
| Prove | Live paper trading in Proving Ground before promotion | Agents (autonomous) | $0–$0.05/month |
| Promote | User reviews MLflow history, initiates promotion | User | $0 |
| Deploy | System becomes live Sentinel managing declared paper portfolio | System | — |
| Signal | Sentinel generates BUY or CLOSE with full reasoning | Agents | ~$0.013/signal |
| Accept/Decline | User decides whether to mirror paper trade in real account | Human always | — |
| Mirror | Accepted: paper + real execute. Declined: paper executes, real unchanged. | User + Platform | — |

### 1.4 The Multi-Account Model

A user may run multiple Sentinels simultaneously, each managing its own independent paper portfolio, each optionally mirroring a different real brokerage account.

Five different strategies. Five different $1,000 paper accounts. Five different pipelines running in parallel. Each independently built, tested, and deployed. Each generating its own Signal Cards. Each tracked independently in MLflow. Each with its own Mirror Portfolio counterfactual.

No retail tool currently provides this. Brokerage paper trading gives you one account. No transparency. No agents. No improvement loop. No history of why any signal was generated. Aegis gives you five independently managed research environments, each deployed as a live paper portfolio manager, each fully auditable.

---

## PART II: LAYERED USER MODEL

### 2.1 Three Tiers, One Infrastructure

The platform serves three types of users on identical infrastructure. Users graduate upward as their understanding deepens. Every capability available to Tier 3 is available to Tier 1 — it is simply not surfaced by default. Transparency at depth creates trust at the surface even for users who never look.

**Tier 1 — The Guided Builder**

Starts with default templates and the five-step Sentinel Wizard. Runs the Sandbox with one-click defaults. Reviews Improvement Analyzer proposals in plain language. Deploys a Sentinel and uses Signal Cards without needing to understand what's underneath.

What they need: complexity hidden by default, outputs explained in plain language, the build process guided step-by-step.

What they should never need to see: VPIN math, HMM state probabilities, Optuna parameter surfaces, LangGraph node graphs. These exist and are accessible but never required.

**Tier 2 — The Curious Tinkerer**

Has a theory they want to test. Maybe insider buying predicts 6-month returns. Maybe congressional trades have alpha. Maybe earnings revision momentum is underpriced. Wants to test it rigorously. Opens the Sandbox, modifies configurations, reads MLflow comparisons, enables plugins, reads agent reasoning traces. The Engine Library is a playground.

What they need: a transparent, rigorous testing environment where their theories meet reality with full auditability.

**Tier 3 — The Serious Retail Quant**

Full engine access. Custom data connectors, custom LangGraph agents, custom quant models, raw MLflow artifact access. Will write their own signal gates, position sizing logic, and custom engine wrappers. VPIN and HMM in the core pipeline if they choose. Will use the Custom Engine SDK.

### 2.2 The Graduation Principle

Users graduate upward naturally. The platform gets more valuable as they do. No capability is locked behind a tier gate — only surfaced progressively. A Tier 1 user who opens the Glass Box sees the exact same LangGraph trace a Tier 3 user sees.

---

## PART III: SYSTEM ARCHITECTURE

### 3.1 Eight-Layer Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│  Layer 8: Frontend (React + Vite)                                    │
│  Dashboard | Engine Library | Sandbox | Arena | Sentinels | Wizard  │
├──────────────────────────────────────────────────────────────────────┤
│  Layer 7: API Layer (FastAPI)                                        │
│  REST endpoints + WebSocket streaming for live agent traces          │
├──────────────────────────────────────────────────────────────────────┤
│  Layer 6: Orchestration (LangGraph)                                  │
│  Supervisor + Sub-agents + Improvement Analyzer + Custom Agents      │
├──────────────────────────────────────────────────────────────────────┤
│  Layer 5: Engine Layer                                               │
│  Data Engine (+ Health Monitor) | Fundamental Engine                 │
│  Analyst Engine | Research Engine                                    │
│  Custom Engine Registry — user-defined engines via SDK wrapper       │
│  Plugin Layer: HMM | VPIN | Chronos | Alpaca  [OFF by default]       │
├──────────────────────────────────────────────────────────────────────┤
│  Layer 4: Model Routing + Validation Budget Layer  [NEW in v6]       │
│  Uncertainty Router | Budget Allocator | Cost Tracker                │
│  Claude Sonnet 4.6 (API)  ←→  Qwen 2.5 14B (Ollama, local)         │
├──────────────────────────────────────────────────────────────────────┤
│  Layer 3: Storage Layer                                              │
│  MLflow (SQLite) | ChromaDB | Episodic Memory | JSON configs         │
│  Cost Attribution Log | Proposal Decision Log                        │
├──────────────────────────────────────────────────────────────────────┤
│  Layer 2: Custom Engine Runtime                                      │
│  Wrapper contract enforcement | Health reporting | I/O isolation     │
├──────────────────────────────────────────────────────────────────────┤
│  Layer 1: Data Sources                                               │
│  YFinance | FRED | SEC EDGAR | Finnhub | Congressional | FinBERT     │
│  Alpaca (plugin) | User-defined connectors (via SDK)                 │
└──────────────────────────────────────────────────────────────────────┘
```

### 3.2 Complete Data Flow

```
External Sources
(YFinance, FRED, SEC EDGAR, Finnhub, Congressional, Alpaca, Custom)
        │
        ▼
Data Engine
  ├── Point-in-time enforcement  [public_disclosure_ts on ALL records]
  ├── Connector Health Monitor   [last_successful_fetch_ts per connector]
  ├── FinBERT → Sentiment scores
  ├── SEC Parser → 512-token chunks → ChromaDB
  └── Custom Connector outputs → normalized into snapshot
        │
        ▼
Engine Layer (parallel execution per tick)
  ├── Fundamental Engine
  │     ├── Earnings Revision Tracker
  │     ├── Insider Activity Monitor (Form 4 + Congressional)
  │     ├── Macro Overlay (FRED-driven)
  │     └── Signal Gate Evaluator
  ├── Custom Engines (registered via SDK)
  │     ├── [User Engine A: custom momentum model]
  │     ├── [User Engine B: satellite imagery classifier]
  │     └── [User Engine N: any wrapped pipeline]
  └── Plugin Layer [if enabled by user]
        ├── HMM → Market Regime
        ├── VPIN → Order Flow Toxicity
        └── Chronos → Probabilistic Price Range
        │
        ▼  [if signal gate crossed]
Uncertainty Scorer [pure math, no LLM]
  └── uncertainty_score (0.0–1.0) → routes to Claude or Qwen
        │
        ├── High uncertainty + budget remaining → Claude Sonnet 4.6 (Supervisor)
        └── Low uncertainty OR budget exhausted → Qwen 2.5 14B (Supervisor)
        │
        ▼
Analyst Engine (LangGraph)
  ├── Research Agent    [Qwen 2.5 14B local — always]
  ├── Sentiment Agent   [Qwen 2.5 14B local — always]
  ├── Risk Agent        [Qwen 2.5 14B local — always]
  └── Supervisor        [Claude or Qwen per routing decision]
        └── Final Signal: BUY/CLOSE + position spec + reasoning
        │
        ▼
Output routing:
  [Backtest / Scenario]  → Portfolio simulation → MLflow + cost log
  [Proving Ground]       → Live paper execution → MLflow + cost log
  [Deployed Sentinel]    → Signal Card → Accept/Decline → Mirror Portfolio
```

### 3.3 Configuration Schema

The configuration is the atomic unit of the platform. Every test, comparison, promotion, and Signal Card is anchored to a specific versioned config.

```json
{
  "config_id": "tech-breakout-v3.2",
  "version": "3.2",
  "created_at": "2026-03-08T01:30:00",
  "trading_style": "swing",
  "asset_universe": {
    "tickers": ["AAPL", "NVDA", "MSFT", "GOOGL", "META"],
    "benchmark": "QQQ"
  },
  "data_engine": {
    "connectors": ["yfinance", "finnhub", "sec_edgar", "congressional"],
    "custom_connectors": [],
    "finbert": { "enabled": true, "score_threshold": 0.6 },
    "lookback_days": 504
  },
  "fundamental_engine": {
    "earnings_revision": { "enabled": true, "warn_threshold": 0.03 },
    "insider_monitor": { "enabled": true, "cluster_window_days": 30 },
    "macro_overlay": { "enabled": true, "fred_series": ["FEDFUNDS", "T10Y2Y"] }
  },
  "custom_engines": [
    { "engine_id": "my_momentum_v2", "role": "SIGNAL_GENERATOR", "weight": 0.3 }
  ],
  "plugins": {
    "hmm": { "enabled": false },
    "vpin": { "enabled": false },
    "chronos": { "enabled": false }
  },
  "signal_gate": {
    "require_earnings_revision_direction": "up",
    "require_insider_activity": "neutral_or_positive",
    "finbert_above": 0.4,
    "custom_engine_conditions": []
  },
  "analyst_engine": {
    "agents": ["research_agent", "sentiment_agent", "risk_agent"]
  },
  "position_sizing": {
    "method": "equal_weight",
    "max_position_pct": 0.15,
    "capital": 5000
  },
  "validation": {
    "claude_budget_usd": 1.00,
    "allocation_strategy": "uncertainty_first",
    "min_uncertainty_threshold": 0.65,
    "budget_exhausted_behavior": "fallback"
  },
  "routing": {
    "mode": "validate",
    "supervisor": "auto"
  },
  "sandbox": {
    "slippage_bps": 15,
    "market_impact_bps_per_10k": 5,
    "min_hold_days": 2,
    "promotion_criteria": {
      "sharpe_min": 1.0,
      "alpha_min_pct": 3.0,
      "max_drawdown_pct": 15.0,
      "win_rate_min": 0.52,
      "backtest_months_min": 6,
      "min_trades": 20,
      "held_out_sharpe_min": 0.85,
      "held_out_degradation_max": 0.35
    }
  }
}
```

---

## PART IV: ENGINE LIBRARY

### 4.1 Organizing Principle

Every engine in the default pipeline must answer a question statable in plain language. Before any engine is added — by the platform or by the user — the question it answers must be statable. "This helps optimize a parameter" means it belongs in the Plugin Library. "This tells me whether a trade is worth taking right now" means it belongs in the default pipeline.

This principle extends to custom engines. When a user registers a custom engine, the wizard asks: what question does this engine answer? That answer becomes the plain-language description shown in the Glass Box when the engine's output appears in a signal trace.

### 4.2 Data Engine

**Purpose:** Ingest, clean, normalize, and annotate all market and alternative data. Enforce point-in-time discipline without exception.

**The Point-in-Time Rule:** Every data record carries two timestamps:
- `event_ts`: when the underlying event occurred
- `public_disclosure_ts`: when the data became publicly available to the market

The simulation loop uses **only** `public_disclosure_ts`. This applies to every connector, every ChromaDB retrieval, every custom data source. There are no exceptions. Congressional trading data uses `disclosure_filing_ts` — the date the filing was submitted — never `trade_date`. The 45-day STOCK Act delay is a feature: the signal arrives 45 days after the trade, which is still a useful slow-moving signal for a swing strategy. Using `trade_date` manufactures alpha that does not exist in live trading.

**The Point-in-Time Data Problem — What APIs Actually Deliver**

Enforcing `public_disclosure_ts` at the query level is necessary but not sufficient. Most standard market data APIs do not maintain true point-in-time data. YFinance and similar services silently overwrite historical financial statements when a company issues a restatement. A backtest querying Q1 2022 revenue data in 2025 may receive the 2023-restated figure — data that was not publicly visible at the simulation date. The timestamps are correct. The *values* are wrong. This is silent lookahead bias that survives `public_disclosure_ts` enforcement because the enforcement mechanism trusts the API to return what was visible at the specified date.

**Required Fix: An Immutable Append-Only Filing Ledger**

The Data Engine must maintain a local immutable ledger for any financial data it cannot trust APIs to deliver correctly at historical dates:

```
data/ledger/
├── sec_filings/
│   └── AAPL/
│       ├── 0000320193-22-000010.json   ← 10-Q filed 2022-01-27; NEVER overwritten
│       └── 0000320193-22-000059.json   ← 10-Q filed 2022-07-29; NEVER overwritten
├── prices/
│   └── AAPL_2022-01-01_2022-12-31.parquet  ← cached at download time
└── macro/
    └── FRED_FEDFUNDS_downloaded_2024-01-15.parquet  ← snapshot, not live query
```

**Four rules that make this work:**

1. **SEC EDGAR filings are stored by accession number and never overwritten.** Restated filings arrive as new accession numbers with new `edgar_accession_ts` values — correctly treated as later-disclosure data invisible before their own filing date. A simulation at any historical date retrieves only filings with `edgar_accession_ts <= simulation_date`.

2. **Price and fundamental data is cached at download time with a `downloaded_at` field.** Simulation queries hit the local cache, not live APIs. The cache represents what the API returned when you fetched it — not what the API returns today after silent revisions.

3. **Live Sentinel operation fetches from APIs normally.** The immutability requirement applies to backtesting and Proving Ground simulation, where data must represent what was visible at a specific historical date. Live mode needs current data.

4. **FRED is the exception.** The Federal Reserve publishes vintage data through the ALFRED API and does not silently overwrite historical releases. FRED data can be queried live during simulation with high confidence. All other financial statement sources should be treated with suspicion until proven otherwise.

This adds build complexity but is non-negotiable. A backtest silently incorporating restated financial data is not a backtest — it is a lookahead-biased simulation that will overstate performance in a way that is invisible until you go live and the numbers stop working.

| Connector | Data Type | Update Cadence | Point-in-Time Field | Tier |
|---|---|---|---|---|
| YFinance | OHLCV, fundamentals, options chain | Daily / realtime | `market_close_ts` | Core |
| FRED | CPI, Fed rate, M2, yield curve, credit spreads | Monthly / weekly | `release_ts` | Core |
| SEC EDGAR | 10-K, 10-Q, 8-K, Form 4 insider filings | Event-driven | `edgar_accession_ts` | Core |
| Finnhub | News, earnings calendar, analyst revisions | Realtime | `published_ts` | Core |
| Congressional | STOCK Act disclosures — 45-day delay enforced | 45-day delay | `disclosure_filing_ts` | Core |
| FinBERT | Sentiment scoring applied at ingest | At ingest | Inherits from source | Core |
| Alpaca | Intraday tick/bar data | Sub-minute | `bar_ts` | Plugin |
| Custom | User-defined — must implement BaseConnector | User-defined | Required field | SDK |

#### 4.2.1 Connector Health Monitor

A silent data feed failure is worse than an obvious one. If YFinance returns stale OHLCV, if EDGAR has a maintenance window, if Finnhub rate-limits during a busy period — the Fundamental Engine continues running against an increasingly outdated snapshot. The Sentinel appears healthy. It is monitoring nothing current.

Every connector exposes `last_successful_fetch_ts`. A background health-check coroutine evaluates health against staleness thresholds calibrated to each connector's expected cadence:

```python
HEALTH_THRESHOLDS = {
    "yfinance":      {"warn": timedelta(hours=25),  "offline": timedelta(hours=48)},
    "fred":          {"warn": timedelta(days=8),    "offline": timedelta(days=14)},
    "sec_edgar":     {"warn": timedelta(hours=72),  "offline": timedelta(days=7)},
    "finnhub":       {"warn": timedelta(hours=25),  "offline": timedelta(hours=48)},
    "congressional": {"warn": timedelta(days=8),    "offline": timedelta(days=14)},
    # Custom connectors set their own thresholds in BaseConnector
}
```

**Sentinel Health States:**

| State | Meaning | Dashboard | Signal Generation |
|---|---|---|---|
| `MONITORING` | All connectors within warn threshold | Green | Normal |
| `DEGRADED` | One or more connectors stale, not offline | Amber — affected connectors named | Continues with warning |
| `OFFLINE` | Critical connector offline | Red — user notified | Suspended immediately |

The `OFFLINE` state suspends Signal Card generation entirely. A close signal generated from stale data could cause a user to exit a position based on information that no longer reflects reality.

**The Asymmetry Rule:** When connector status is ambiguous, downgrade the health state. A false `DEGRADED` warning is an annoying notification. A Sentinel silently running on week-old data while the user believes it is watching the market is a product integrity failure.

Health checks run every 4 hours for daily connectors and every 30 minutes for real-time connectors. This is a lightweight scheduled coroutine — no model involvement, negligible compute.

### 4.3 Fundamental Engine

**Purpose:** The primary signal generation layer for the default pipeline. Transforms ingested data into thesis-relevant signals and gate conditions. Replaces VPIN/HMM as the default because it answers questions a retail swing trader actually cares about rather than microstructure questions designed for high-frequency market makers.

**Earnings Revision Tracker**
- Monitors sell-side EPS and revenue estimate revisions for configured tickers via Finnhub
- Detects direction, magnitude, analyst count, and revision momentum (accelerating vs. decelerating)
- Output: `{direction: "up", magnitude: 0.04, analyst_count: 12, momentum: "accelerating"}`
- Why it matters: Earnings revision momentum is one of the most durable, academically documented return predictors. A stock where analysts are raising estimates is being re-rated upward by people with better information access than the market has fully priced in. It is a signal with genuine forward predictive power at the swing/position holding period.

**Insider Activity Monitor**
- Tracks SEC Form 4 and Congressional trade disclosures using `edgar_accession_ts` / `disclosure_filing_ts` only — never `trade_date`
- Detects cluster buying: multiple insiders buying within a configurable time window
- Distinguishes executive-level insiders from board members (different signal strength)
- Output: `{insider_type: "CEO", transaction: "BUY", shares: 50000, cluster_buy: true, cluster_size: 3, cluster_window_days: 30}`
- Why it matters: Cluster insider buying — multiple officers buying simultaneously — historically precedes meaningful outperformance. It is slow-moving (45-day disclosure delay for Congressional, immediate for Form 4) and non-noisy. Insiders don't buy for reasons unrelated to their company's prospects.

**Macro Overlay**
- FRED-driven contextual layer: yield curve shape (T10Y2Y), credit spread trajectory, Fed rate direction, M2 money supply momentum
- Output: `{macro_regime: "tightening", credit_spread_trend: "stable", yield_curve: "inverted"}`
- Not a signal. A context qualifier. The Supervisor receives this alongside fundamental signals and uses it to modulate confidence in the final recommendation. A strong earnings revision in a tightening macro environment deserves different treatment than the same revision in a risk-on environment.

**Signal Gate Evaluator**
- Combines Fundamental Engine outputs, FinBERT scores, and optional Plugin/Custom Engine outputs into a binary gate condition
- The gate determines whether the Analyst Engine (LangGraph) is invoked for a given ticker on a given day
- In a typical swing configuration, the gate passes on 10–20% of trading days
- This is the primary cost control mechanism: LLM agents fire only on genuinely signal-relevant events

### 4.4 Plugin Library

Plugins are powerful tools available to Tier 2 and Tier 3 users. They are off by default. They require explicit opt-in. They contribute context to the Analyst Engine. They cannot generate standalone signals independently — they are context modifiers only.

The reason for this architecture: VPIN was designed for high-frequency market makers to detect order flow toxicity before microsecond flash crashes. Displaying it to a retail investor holding a 2-week swing position generates anxiety, not insight. For a Tier 3 user who understands what they're measuring, it is a legitimate additional lens. The Plugin Library makes it available without imposing it.

| Plugin | What It Measures | Best For | Default |
|---|---|---|---|
| HMM (Hidden Markov) | Market regime classification: Bull / Bear / Volatile | Swing strategies wanting macro context | OFF |
| VPIN | Order flow toxicity — smart money vs. retail flow | Quants wanting microstructure context | OFF |
| Chronos | Amazon time-series model — probabilistic price range forecast | Any tier as optional entry/exit context | OFF |
| Alpaca Intraday | Sub-minute tick and bar data | Day Trader template only | OFF |

**Plugin UI Rule:** Raw plugin scores never appear as headline metrics in Signal Cards or the Dashboard. They appear in the Glass Box audit trail and as plain-language context lines in the Signal Card's expanded reasoning section. Never "VPIN: 0.84" — always "Institutional flow: Elevated — note before acting."

### 4.5 Analyst Engine (LangGraph)

The reasoning layer. Takes signals from the Fundamental Engine, optional Plugin context, and optional Custom Engine outputs, retrieves evidence from ChromaDB, synthesizes a complete position recommendation, and produces a fully auditable reasoning trace.

```
Supervisor Agent [Claude Sonnet 4.6 API or Qwen 2.5 8B — per routing decision]
│
├──► Research Agent [Qwen 2.5 8B — local, always]
│     "What does the most recent 10-Q say about margin trends?"
│     "Has management guidance changed in the last two quarters?"
│     └── ChromaDB query → top-3 chunks max, point-in-time filtered
│         Returns structured JSON conclusion to Supervisor context
│
├──► Sentiment Agent [Qwen 2.5 8B — local, always]
│     "Synthesize current news narrative for this ticker"
│     └── FinBERT scores per source + news headline narrative
│         Returns structured JSON conclusion to Supervisor context
│
├──► Risk Agent [Qwen 2.5 8B — local, always]
│     "Is this position within portfolio constraints?"
│     └── Position sizing validation, drawdown budget check, macro regime check
│         Risk Agent veto: if vetoed, NO SIGNAL regardless of other agents
│         Returns structured JSON conclusion to Supervisor context
│
├──► Context Ceiling Node [runs before Supervisor — no LLM]
│     Counts tokens in accumulated LangGraph state.
│     If > 3,500 tokens: truncate by dropping oldest sub-agent outputs first.
│     Supervisor always receives most recent conclusions, never partial outputs.
│
└──► Supervisor [Claude or Qwen per uncertainty routing]
      Final output:
        - Signal type: BUY or CLOSE
        - Ticker and entry/exit price range
        - Position size (shares, dollar value, % of declared capital)
        - Expected hold duration with rationale
        - Exit conditions: price target, stop, thesis shift trigger
        - Plain-language thesis for this specific trade
        - Confidence level with explicit uncertainty acknowledgment
        - Sub-agent vote summary
        - model_used: "claude-sonnet-4-6" or "qwen2.5:8b" — always logged
```

**Context Window Management:** Three enforced constraints prevent KV cache overflow on 16GB hardware:

1. **Retrieval cap** — Research Agent ChromaDB queries return maximum 3 chunks (not 5). The 4th and 5th chunks rarely change the Supervisor's conclusion; they inflate context for free. This is a one-line config change with meaningful memory impact.

2. **3,500-token context ceiling** — A state management node runs before every Supervisor invocation and counts accumulated tokens. If the count exceeds 3,500 tokens, the oldest sub-agent outputs are dropped first. Implementation: `LangChain.trim_messages(strategy="last", max_tokens=3500)`. The Supervisor always sees the most recent sub-agent conclusions, never truncated partial outputs.

3. **Structured JSON sub-agent outputs** — Sub-agents return structured JSON conclusions to the Supervisor context, not prose. The full prose reasoning is logged to MLflow verbatim. The Supervisor context gets the summary only. A Risk Agent returning `{"approved": true, "drawdown_budget_remaining_pct": 0.67}` adds ~50 tokens. A Risk Agent returning a reasoning paragraph adds ~300 tokens. At three agents plus instructions, the difference between structured and prose is ~750 tokens of KV cache pressure per gated event.

**Why this matters:** Qwen 2.5 8B's KV cache grows at roughly 0.5MB per context token at inference time. Five 512-token chunks plus an EntryStateSnapshot plus prompt instructions plus prior agent outputs can hit 6,000 tokens of active context — 3GB of KV cache on top of the 5GB model weights. On a 16GB Mac with 7GB of headroom, that triggers swap. The retrieval cap and context ceiling together bound KV cache at ~1.5GB, fitting comfortably within headroom.

**Episodic Memory:** The Supervisor maintains a rolling record of its past signals and their outcomes. "I recommended AAPL on Feb 12 under similar conditions. It reached exit target in 8 days at +3.4%." This creates lightweight self-calibration without model fine-tuning. Episodic memory is particularly valuable for the Supervisor to distinguish familiar setups (low uncertainty — route to Qwen) from genuinely novel ones (high uncertainty — route to Claude).

### 4.6 Research Engine

| Component | Description |
|---|---|
| SEC Filing Loader | Downloads and parses 10-K / 10-Q / 8-K / Form 4 into 512-token chunks with filing metadata |
| Earnings Call Parser | Extracts forward guidance, risk factor statements, management tone changes |
| ChromaDB Vector Store | Embeds and indexes all chunks. **Retrieval cap: 3 chunks maximum per query.** Chunk size: 512 tokens. Queryable by ticker / filing type / period. All queries in simulation enforce `public_disclosure_ts <= simulation_date` |
| Episodic Memory Store | Supervisor's rolling history of past signals, outcomes, and self-calibration notes |

The ChromaDB point-in-time filter is enforced at the query level, not the application level. The query itself cannot return documents with `public_disclosure_ts > simulation_date` regardless of what the calling code does.

**Chunk size rationale:** 512 tokens × 3 chunks = 1,536 tokens of Research Agent evidence in Supervisor context. This is the correct operating point. Larger chunks or more chunks push the context ceiling without meaningfully improving signal quality for swing strategy time horizons.

---

## PART V: CUSTOM ENGINE SDK

### 5.1 Why This Exists

The platform's core promise is "you built it." If that promise is real, it must extend beyond the templates and plugins the platform pre-built. A user who has a proprietary momentum classifier trained on their own features, a custom alternative data source, a novel macro indicator, or a rule-based system they've refined over years — they should be able to integrate it into Aegis and have it participate as a first-class engine.

Without a formal wrapper framework, custom logic can be added but it becomes a black box inside the Glass Box. The audit trail reads "custom engine said X" with no provenance, no health reporting, and no way to trace the signal back through that engine's reasoning. The wrapper framework solves this by enforcing a contract at the boundary — it doesn't care what's inside the engine, only that the boundary is correct.

### 5.2 The Wrapper Contract

The wrapper is a Python class that inherits from `BaseEngine` and implements four methods. The engine's internals are completely unconstrained — the wrapper enforces only the boundary.

```python
from aegis.sdk import BaseEngine, EngineInput, EngineOutput, EngineHealth

class MyMomentumEngine(BaseEngine):

    # Required metadata
    engine_id   = "my_momentum_v2"
    engine_name = "Custom Momentum Signal"
    version     = "2.1.0"
    role        = "SIGNAL_GENERATOR"  # see §5.3

    def describe(self) -> str:
        """Plain-language description shown in Glass Box."""
        return (
            "Computes 12-1 momentum score for each ticker using risk-adjusted "
            "returns over the past 252 days excluding the most recent 21 days. "
            "Returns a conviction score between 0 and 1."
        )

    def run(self, input: EngineInput) -> EngineOutput:
        """
        Core execution method.
        input.data_snapshot is the point-in-time enforced data snapshot
        for input.as_of_date — the simulation date.
        The engine must not access any data beyond what is in the snapshot.
        """
        scores = {}
        reasoning = {}

        for ticker in input.tickers:
            df = input.data_snapshot[ticker]
            # ... your logic here ...
            scores[ticker]    = self._compute_momentum(df)
            reasoning[ticker] = {
                "lookback_return":    float(df['close'].pct_change(252).iloc[-1]),
                "skip_return":        float(df['close'].pct_change(21).iloc[-1]),
                "momentum_score":     scores[ticker],
                "model_version":      self.version,
                "features_used":      ["close", "volume"],
            }

        return EngineOutput(
            signals      = scores,        # {ticker: float} conviction scores
            signal_type  = "conviction",
            reasoning    = reasoning,     # logged verbatim to Glass Box
            metadata     = {
                "engine_id":        self.engine_id,
                "engine_version":   self.version,
                "run_duration_ms":  self._elapsed_ms,
                "model_hash":       self._model_hash(),  # for ML models
                "inputs_used":      ["close", "volume"],
            }
        )

    def health(self) -> EngineHealth:
        """Called by the health monitor on each check cycle."""
        return EngineHealth(
            last_successful_run_ts = self._last_run_ts,
            last_error             = self._last_error,
            avg_run_duration_ms    = self._avg_duration,
        )
```

### 5.3 Signal Roles

The role declaration is the most important field in the wrapper. It tells the pipeline how to use the engine's output. A custom engine must declare one role.

| Role | What It Does | Signal Gate Behavior | Risk Level |
|---|---|---|---|
| `DATA_SOURCE` | Provides additional data to the snapshot | Cannot gate signals directly | Low |
| `SIGNAL_GENERATOR` | Produces conviction scores 0–1 | Score can be added as a gate condition | Medium |
| `GATE_CONDITION` | Returns a boolean gate pass/fail | Directly participates in signal gate logic | Medium |
| `CONTEXT_MODIFIER` | Provides context to the Analyst Engine | Cannot gate signals — advisory only | Low |
| `RISK_OVERRIDE` | Can veto a signal regardless of other agents | Enforced at Supervisor level — hard veto | High — requires confirmation |

**`RISK_OVERRIDE` note:** This role gives a custom engine the same authority as the built-in Risk Agent. A custom engine with portfolio-level constraints — sector exposure limits, correlation caps, custom drawdown rules — needs this authority to enforce them. But it is dangerous if misconfigured. The Sentinel Wizard requires explicit confirmation when a `RISK_OVERRIDE` engine is added: "This engine can block any signal regardless of other agent votes. Confirm you understand this."

### 5.4 Input and Output Contracts

**EngineInput — what every custom engine receives:**
```python
@dataclass
class EngineInput:
    tickers:        List[str]        # tickers in scope this cycle
    as_of_date:     datetime         # simulation date — ONLY date visible
    data_snapshot:  Dict[str, DataFrame]  # point-in-time enforced externally
    config:         Dict[str, Any]   # engine's own config block from config.json
    prior_outputs:  Dict[str, Any]   # other engines' outputs this cycle, if needed
```

The `as_of_date` is critical. In simulation, it is the current simulation date. In live mode, it is the current real date. The engine must not make any network calls, read any external files, or access any data not contained in `data_snapshot` — the wrapper sandbox enforces this in simulation mode to prevent lookahead.

**EngineOutput — what every custom engine must return:**
```python
@dataclass
class EngineOutput:
    signals:     Dict[str, Any]   # {ticker: value} — format depends on role
    signal_type: str              # "conviction" | "boolean" | "context" | "veto"
    reasoning:   Dict[str, Any]   # logged verbatim to Glass Box — be descriptive
    metadata:    Dict[str, Any]   # engine_id, version, duration, model_hash
```

**EngineHealth — what the health monitor reads:**
```python
@dataclass
class EngineHealth:
    last_successful_run_ts: datetime
    last_error:             Optional[str]
    avg_run_duration_ms:    float
    custom_status:          Optional[str]  # engine-specific status message
```

### 5.5 Glass Box Integration

Every `EngineOutput.reasoning` dict is logged verbatim to MLflow as part of the signal trace. In the Glass Box view, each custom engine appears as a collapsible section alongside the built-in agent traces:

```
▼ Research Agent (Qwen 2.5 14B)
  └── [retrieved 10-Q chunks, evidence synthesis]

▼ Custom: My Momentum Engine v2.1
  └── lookback_return:  +0.287 (252-day)
      skip_return:      +0.031 (21-day)
      momentum_score:   0.74
      features_used:    [close, volume]

▼ Risk Agent (Qwen 2.5 14B)
  └── [constraint validation, approval]

▼ Supervisor (Claude Sonnet 4.6)
  └── [final synthesis, position spec]
```

The `describe()` method output is shown as the section header tooltip. Users always know what a custom engine claims to measure and where its output came from.

### 5.6 Health Monitor Integration

Custom engines participate in the Sentinel health system automatically via the `health()` method. A custom engine that fails silently — throwing exceptions, returning stale outputs — degrades the Sentinel's health state identically to a broken data connector. The health check coroutine calls `engine.health()` on the same schedule as connector health checks.

If a custom engine's `last_successful_run_ts` exceeds its configured staleness threshold, the Sentinel transitions to `DEGRADED`. If the engine is crashing consistently, `OFFLINE`. Signal generation is suspended on `OFFLINE` — same as a broken connector.

### 5.7 Registration and Validation

A custom engine is registered by placing the wrapper file in the configured engine directory and registering it via the CLI or UI:

```bash
aegis engine register ./my_momentum_engine.py --validate
```

Registration runs a validation sequence:
1. Import and instantiate the wrapper — catch any dependency errors
2. Run `engine.describe()` — confirm it returns a non-empty string
3. Run `engine.health()` — confirm it returns a valid `EngineHealth` object
4. Run a single Quick Iteration backtest (90-day, single ticker) — confirm the engine produces valid `EngineOutput` objects without exceptions
5. If all pass: engine appears in the Engine Library under `/engines/custom`

Custom engines must pass validation before they are available in production runs. This catches integration errors before they silently break 15-hour Full Production Backtests.

### 5.8 Execution Sandbox (Security)

**The problem without this:** Without isolation, a custom `.py` file registered from an external source runs inside the same Python process as the rest of the application. That process owns all the user's API keys via environment variables. A malicious engine — or a well-intentioned engine with a compromised dependency — can read `.env`, make outbound network calls, and write to disk. The user believes they're running a backtest. The engine may be exfiltrating Anthropic and Finnhub credentials. This is the standard supply chain threat model for any plugin architecture.

**Phase 3 — Subprocess enforcement (immediate):**

Every `run()` call executes in a restricted subprocess with:
- Explicit import allowlist: `numpy`, `pandas`, `scikit-learn`, `torch` (CPU-only), `scipy`
- No network access (outbound blocked at the subprocess level)
- `sys.path` restricted to the venv — no access to application modules or `.env`
- Any import outside the allowlist raises `ImportRestrictionError` — run aborts

This catches honest mistakes and enforces the documented intent. It is buildable immediately with no additional infrastructure.

**Phase 3b — Docker isolation (production target):**

Every `run()` call executes inside a Docker container:

```bash
docker run \
  --network none \
  --read-only \
  --memory 512m \
  --cpus 1.0 \
  --env-file /dev/null \
  aegis-engine-runner \
  # EngineInput serialized via stdin → EngineOutput returned via stdout
```

- `--network none` — no outbound or inbound connections
- Read-only filesystem — engine receives `EngineInput` via stdin, cannot write to host
- No host environment variables — the container sees no `.env`, no API keys
- Resource caps — prevents runaway engine consuming host

The ~200ms Docker startup overhead is acceptable for daily-bar backtests. For the Day Trader template (intraday bars), pre-warm the container and keep it alive across ticks to eliminate per-call startup cost.

**Wasmtime (future):** Wasmtime with a pre-approved package manifest removes the Docker dependency and tightens isolation further. This is the correct long-term target when the engineering investment is available.

---

## PART VI: THE SANDBOX

### 6.1 Philosophy

The Sandbox is not a feature. The Sandbox is the platform. The Engine Library exists to configure what the Sandbox runs. The Sentinel exists to deploy what the Sandbox validated. The Glass Box exists to audit what the Sandbox produced. The Custom Engine SDK exists to extend what the Sandbox can run. Everything serves the Sandbox.

The Sandbox is where you find out whether your system actually works before it costs you anything. The agents and the historical data are the adversary, not the ally. They do not tell you what you want to hear. They run your system against reality and report what they find.

### 6.2 Three Run Types

**Quick Iteration Run**

Duration: 2–10 minutes on Mac 16GB with Qwen 2.5 14B. Claude not invoked.

Scope: 90-day window, up to 3 tickers, Phase 1 only (Fundamental Engine + Custom Engines in data/context roles, no LangGraph, no Supervisor).

Purpose: rapid directional feedback during the Improvement Loop. The Improvement Analyzer proposes "lower earnings revision threshold from 5% to 3%." You approve. A Quick Run confirms whether the direction is right in minutes before you commit to a full run. It is the iteration accelerator — not the validation tool.

Cost: $0.00. Claude is never invoked.

MLflow tag: `run_type=quick_iteration`

**Full Production Backtest**

Duration: 4–15 hours on Mac 16GB with Qwen 2.5 14B. This is expected and acceptable. Launch before sleep.

Scope: Full configured history (default 2+ years), all configured tickers, both phases. Phase 1 is vectorized — the Fundamental Engine and all non-LLM engines run day by day in NumPy/pandas. Phase 2 invokes the Analyst Engine (LangGraph) on signal-gated events only, routing each Supervisor call through the Uncertainty Router.

Held-out partition: at run initiation, 20% of the date range is randomly partitioned and sealed. The optimization process — including the Improvement Analyzer and all MLflow visibility — uses only the 80% window. The held-out window is revealed for the first time at promotion.

Cost: $0.00–$5.00 depending on routing mode and budget setting. See Part X for full cost analysis.

MLflow tag: `run_type=production`

**Scenario Stress Test**

Duration: 30 minutes–4 hours depending on scenario count and pipeline complexity.

Scope: Deterministic historical date ranges from the Scenario Library — real FRED, YFinance, and EDGAR data. Not LLM simulation. The LLM cannot simulate historical scenarios — it produces hallucinations with financial formatting. The Scenario Library maps scenario types to specific calendar periods and runs the full pipeline over those exact dates.

Purpose: "Does my system survive specific adverse conditions?" Rising rate cycles. Market crashes. High-volatility regimes. Sector rotation periods. Each scenario runs your complete pipeline against the real data from that period.

Cost: Modest — same Uncertainty Router applies, fewer gated events than a 2-year production run.

MLflow tag: `run_type=scenario`

Scenario Library (deterministic — never LLM-generated):
```json
{
  "rising_rate_environment": {
    "description": "Fed tightening cycles with >200bps cumulative increase",
    "instances": [
      {"label": "1994 Tightening",      "start": "1994-02-04", "end": "1995-02-01"},
      {"label": "1999-2000 Tightening", "start": "1999-06-30", "end": "2000-05-16"},
      {"label": "2004-2006 Tightening", "start": "2004-06-30", "end": "2006-06-29"},
      {"label": "2018 Tightening",      "start": "2018-03-21", "end": "2018-12-19"},
      {"label": "2022-2023 Tightening", "start": "2022-03-17", "end": "2023-07-26"}
    ]
  },
  "market_crash": {
    "instances": [
      {"label": "Dot-com crash",    "start": "2000-03-10", "end": "2002-10-09"},
      {"label": "2008 Financial",   "start": "2007-10-09", "end": "2009-03-09"},
      {"label": "COVID Crash",      "start": "2020-02-19", "end": "2020-03-23"},
      {"label": "2022 Bear",        "start": "2022-01-03", "end": "2022-10-12"}
    ]
  },
  "high_volatility": {
    "instances": [
      {"label": "2011 Debt Crisis", "start": "2011-07-22", "end": "2011-10-04"},
      {"label": "2015-2016 China",  "start": "2015-08-18", "end": "2016-02-11"}
    ]
  }
}
```

Show survival rates across all instances of a scenario type — not just the most recent. "Your system survived 3 of 5 rate hike cycles" is more informative than "your system survived 2022." Post-scenario decomposition: Qwen 2.5 14B analyzes structured per-scenario results with a constrained JSON prompt to attribute which factors differentiated survival from failure.

### 6.3 The Simulation Loop

```python
def run_production_backtest(config, run_type="production"):

    # 1. Partition held-out window at initiation (production runs only)
    #    Random partition — not always the most recent 20%
    optimization_dates, holdout_dates = partition_dates(
        trading_calendar[config.start_date:config.end_date],
        holdout_fraction = 0.20,
        method           = "random",
        seed             = run_id  # reproducible
    )
    mlflow.log_param("holdout_dates", holdout_dates)  # logged and sealed

    portfolio = Portfolio(config.position_sizing)

    for date in optimization_dates:

        # 2. Point-in-time data snapshot
        #    No record with public_disclosure_ts > date is visible
        snapshot = data_engine.get_snapshot(config.tickers, as_of=date)

        # 3. Run all engines (parallel where possible)
        fundamental = fundamental_engine.compute(snapshot, config, date)
        plugins      = plugin_layer.compute(snapshot, config.plugins, date)
        custom_outs  = custom_engine_registry.run_all(
            EngineInput(config.tickers, date, snapshot, config.custom_engines)
        )

        # 4. Signal gate evaluation per ticker
        for ticker in config.tickers:
            signals = {
                **fundamental[ticker],
                **plugins.get(ticker, {}),
                **custom_outs.get(ticker, {})
            }

            if not signal_gate.evaluate(signals, config.signal_gate):
                continue  # gate did not pass — no LLM call

            # 5. Uncertainty scoring (production runs only)
            if run_type == "production":
                u_score = uncertainty_scorer.score(
                    ticker, signals, config, episodic_memory
                )
                supervisor_model = routing_budget.route(u_score, config.validation)
            else:
                supervisor_model = config.routing.fallback_model

            # 6. Analyst Engine (LangGraph)
            recommendation = analyst_engine.evaluate(
                ticker, snapshot, signals, supervisor_model
            )

            # 7. Portfolio execution with slippage
            portfolio.execute(recommendation, date, config.sandbox)

        nav_history.append((date, portfolio.nav))

    # 8. Metrics calculation
    metrics = compute_metrics(nav_history, config.asset_universe.benchmark, holdout_dates)

    # 9. Plain-language verdict (Qwen 2.5 14B, constrained prompt)
    verdict = improvement_analyzer.generate_verdict(metrics, config)

    # 10. MLflow logging
    mlflow.log_run(config, metrics, verdict, traces, cost_log)
```

### 6.4 Slippage and Market Impact

Every simulated trade injects realistic transaction costs. This is non-negotiable. A strategy that looks good on gross returns but not on net returns is a strategy that requires impossible execution. Slippage Drag — the difference between gross and net returns — is always displayed alongside headline performance metrics.

| Component | Default | Description |
|---|---|---|
| Bid-ask spread | 10 bps | Half-spread applied per side |
| Market impact | 5 bps per $10k notional | Larger positions move price against you |
| Execution latency | 1 bar | Orders fill at next bar open, not same-bar close |
| Partial fills | Applied above 2% of daily volume | Large positions in illiquid names |

### 6.5 Performance Metrics

| Metric | Formula / Description |
|---|---|
| Total Return | `(final_nav - initial_nav) / initial_nav` |
| CAGR | Annualized compound growth rate over the backtest period |
| Sharpe Ratio | `(mean_daily_return - risk_free_daily) / std_daily_return × √252` |
| Sortino Ratio | Sharpe computed using only downside deviation |
| Max Drawdown | Largest peak-to-trough NAV decline |
| Win Rate | Percentage of closed trades that were profitable |
| Avg Win / Avg Loss | Mean profitable trade return / mean losing trade return |
| Alpha vs. Benchmark | Excess annualized return over configured benchmark |
| Beta | Portfolio sensitivity to benchmark moves |
| Avg Hold Duration | Mean days between position open and close |
| Signal Gate Rate | Percentage of trading days that triggered LLM invocation |
| LLM Alpha Contribution | `Sharpe(full)` minus `Sharpe(Phase 1 only baseline)` |
| Slippage Drag | Gross return minus net return after all transaction costs |
| Claude Call Rate | Percentage of gated events routed to Claude vs. Qwen |
| Estimated API Cost | Actual Claude spend for this run |
| Optimization Sharpe | Sharpe on the 80% training window |
| Held-Out Sharpe | Sharpe on the sealed 20% — revealed at promotion only |

### 6.6 The Plain Language Rule

Every Sandbox run produces two parallel output layers:

**Layer 1 — Raw metrics** for MLflow Arena, Glass Box, and technical review. Every number, every trace, every artifact.

**Layer 2 — Plain-language verdict** generated by the Improvement Analyzer (Qwen 2.5 14B) and shown as the primary output in the Sandbox view. Not a marketing summary. An honest interpretation: what worked, what didn't, where the system is fragile, what the Improvement Analyzer recommends changing and why.

Users should never be required to interpret a Sharpe ratio to understand what the Sandbox is telling them. The plain-language verdict is the primary output. The raw metrics are there when you want them.

### 6.7 The Agent Improvement Loop

The Improvement Loop is the core differentiator. After every Full Production Backtest, the Improvement Analyzer (Qwen 2.5 14B) reviews the complete MLflow trace and generates structured proposals. It only sees the optimization window. It never sees the held-out window. This is the overfitting protection.

```
Full Production Backtest Completes
        │
        ▼
Improvement Analyzer [Qwen 2.5 14B] receives:
  - Trade-by-trade P&L log
  - Signal gate events and invocation rate
  - Sub-agent vote log (Risk Agent veto frequency, disagreements)
  - Optuna parameter sweep surface (if Phase 1 sweep was run)
  - Per-agent LLM alpha contribution breakdown
  - Custom engine output correlation with trade outcomes
        │
        ▼
Generates two proposal types:

TYPE 1 — Parameter Proposal (specific and testable):
{
  "proposal_id":    "prop-47",
  "target_param":   "signal_gate.earnings_revision_threshold",
  "current_value":  0.05,
  "proposed_value": 0.03,
  "rationale":      "Threshold of 5% filtered 14 valid entries that had
                     positive forward returns over the next 21 trading days.
                     Lowering to 3% captures them. False signal rate increases
                     from 12% to 15% — modest cost for +1.6% alpha estimate.",
  "expected_delta": {"sharpe": "+0.19", "alpha_pct": "+1.6%", "gate_rate": "+3%"},
  "risk":           "More LLM invocations. API cost increases ~8% per run."
}

TYPE 2 — System Insight (structural, non-parameterizable):
{
  "proposal_id":    "prop-48",
  "insight_type":   "hidden_dependency",
  "finding":        "This system underperforms consistently when the 10-year
                     yield rises >75bps over any 6-month window. This pattern
                     appears across 2018, 2022, and partially in 2013 taper
                     tantrum data. Your signal gate has no macro condition
                     that would suppress entries in this environment.",
  "evidence":       "Win rate: 71% in stable/falling rate periods vs. 39%
                     in rising rate periods (>75bps in 6 months).",
  "options":        ["Add FRED macro condition to signal gate",
                     "Add this to Scenario Stress Test library as a known risk",
                     "Accept as a known limitation and size positions smaller"]
}
        │
        ▼
User Proposal Inbox: APPROVE / REJECT / MODIFY AND APPROVE
  All outcomes logged: proposal_id, outcome, time_to_decision_seconds,
  user_modified_value (if MODIFIED), user_notes (optional)
        │
        ▼
Quick Iteration Run validates direction (2–10 minutes, $0)
        │
        ▼
Full Production Backtest confirms delta (4–15 hours, $0–$1)
        │
        ▼
Config version incremented → new MLflow run
```

---

## PART VII: MLFLOW ARENA

### 7.1 Two Roles: Scoreboard and Judgment Ledger

MLflow serves two equally important functions.

**As a scoreboard:** it is the court of truth for configuration performance. No configuration is trusted without a logged production backtest run. Results are reproducible from the logged configuration. Numbers cannot be argued with.

**As a judgment ledger:** it is the institutional memory of the user's evolving thinking about their system. Every proposal generated and whether it was approved, rejected, or modified. Every parameter change and what it produced. Every version of the configuration and its full performance history. The record of how the user's system-building judgment has developed.

Over months of iteration, the MLflow Arena becomes a record of which intuitions held up under testing and which were falsified. This is the learning artifact the platform produces beyond financial returns.

### 7.2 What Gets Logged

**Parameters:**
- Complete `config.json` at the time of the run — every engine setting, every plugin state, every signal gate condition, every custom engine registration
- Optimization window date range and the sealed holdout date range

**Metrics:** All metrics from §6.5, plus per-ticker breakdown, per-phase breakdown (Phase 1 vs Phase 2), per-agent LLM alpha contribution

**Cost attribution:**
- Total estimated Claude spend for this run
- Number of Claude-routed calls vs. Qwen-routed calls
- Average uncertainty score distribution
- Breakdown by uncertainty bucket

#### 7.2.1 Tiered Trace Depth

MLflow trace verbosity is controlled by `logging.depth` in the routing config. The default for every run type is `production`. The `debug` mode is an explicit opt-in — never the default.

| Run Type | Trace Depth | What Is Logged |
|---|---|---|
| `quick_iteration` | minimal | Config + metrics only. No agent traces. |
| `production` | production | Config + metrics + top-level Supervisor output per gated event (signal type, confidence, model used, cost). No sub-agent spans. |
| `scenario` | production | Same as production. |
| `debug` | full | Full autolog — every nested LangGraph span. Explicit opt-in only. **Disk space guard: debug mode cannot be enabled if available disk < 5GB.** |

**Why this matters:** `mlflow.langchain.autolog()` captures every nested LangGraph span. For a 500-day production backtest at 15% gate rate across 5 tickers, this generates ~375 gated events × thousands of spans each. SQLite degrades under this write load progressively and is hard to diagnose once it starts. Selective logging eliminates this without losing the information you actually need across runs.

Routing config:
```json
{
  "logging": {
    "depth": "production"
  }
}
```

#### 7.2.2 Tiered Artifact Storage

Regular production run artifacts are lightweight. Full reasoning traces are written once — at promotion.

**Every production run logs:**
- `config.json` — exact configuration
- `metrics.json` — all metrics from §6.5
- `portfolio_nav.csv` — daily NAV history  
- `plain_verdict.md` — Improvement Analyzer plain-language summary
- `proposal_log.jsonl` — proposals generated, outcomes, time-to-decision
- `cost_log.jsonl` — per-call cost attribution
- `recommendation_trace.jsonl` — **top-level only**: `{event_id, ticker, date, signal_type, confidence, supervisor_model, supervisor_cost, uncertainty_score}` per gated event. No sub-agent reasoning.

**At promotion — written once, never regenerated:**

A `write_full_promotion_artifact()` call generates the complete Glass Box artifact for the promoted run:
- `full_reasoning_trace.jsonl` — complete sub-agent reasoning, custom engine outputs, every signal factor for every gated event in the promoted configuration's run

This file is permanently associated with the specific MLflow run ID that passed the promotion gate. If that run is re-run with a different config version, the promotion artifact is not regenerated — it belongs to the run that was promoted, not a subsequent re-run. The Glass Box audit view reads from this file.

**Storage math:** A 500-day backtest at 15% gate rate = ~375 gated events. Regular production artifact: ~375 events × ~1KB summary = ~375KB. Promotion artifact: ~375 events × 75KB full trace = ~28MB. Written once. After 50 production runs, artifact store is ~20MB (run summaries) + ~28MB (promoted config trace) = ~50MB total. Manageable.
- `cost_log.jsonl` — per-call cost attribution

### 7.3 Arena Views

**Leaderboard** — All production runs ranked by any metric. One-click config diff. Promote button for runs meeting all criteria.

**Config Diff Viewer** — Git-style diff between any two configurations, with performance delta side by side.
Example: `signal_gate.earnings_revision_threshold: 0.05 → 0.03 | Sharpe: 0.87 → 1.06 (+0.19)`

**System Evolution View** — All runs for a config lineage in chronological order. The engineering history of your strategy. Which changes moved the needle and which didn't.

**Parallel Coordinate Plot** — Each line is one run. Axes are key parameters plus Sharpe. Reveals parameter regions that produce high-Sharpe configurations.

**Scenario Survival Matrix** — Scenario runs: each scenario type vs. each configuration, color-coded by survival rate. Robustness visible at a glance.

**LLM vs. Quant-Only Comparison** — Phase 1 Sharpe (Fundamental Engine only, no LLM) vs. Phase 2 Sharpe (with LangGraph). If LLM Alpha Contribution is negative or near zero, the Analyst Engine is adding noise for this configuration. A finding worth knowing before you optimize around it.

**Cost Attribution View** — Per-run Claude cost, cumulative spend across all runs, Claude vs. Qwen signal quality comparison (win rate and P&L contribution per model), uncertainty score distribution. Answers the question: is the Uncertainty Router allocating Claude to the right calls?

**Proposal Decision Log** — Every Improvement Analyzer proposal across all runs. APPROVED / REJECTED / MODIFIED. Time-to-decision in seconds. User-modified values. This is both a personal learning tool (which proposals have you consistently acted on vs. ignored?) and the empirical basis for the regulatory user-directed defense.

### 7.4 The Promotion Gate

User-configurable thresholds. A production run must meet all criteria before a "Ready to Promote" button appears.

```json
{
  "sharpe_min":               1.0,
  "alpha_min_pct":            3.0,
  "max_drawdown_pct":         15.0,
  "win_rate_min":             0.52,
  "backtest_months_min":      6,
  "min_trades":               20,
  "held_out_sharpe_min":      0.85,
  "held_out_degradation_max": 0.35
}
```

`held_out_sharpe_min` and `held_out_degradation_max` are non-negotiable defaults. They are grayed out in the UI with a tooltip explaining why. A configuration with Sharpe 1.4 on the optimization window and Sharpe 0.3 on the held-out window is a curve-fitted configuration. The Improvement Loop produced an iteratively overfit result that looks excellent on the training data. It must not be promoted.

At promotion time, the user sees both windows side by side for the first time:

```
Optimization window (80%):  Sharpe 1.41  |  Alpha +6.2%  |  Drawdown -11.4%
Held-out validation (20%):  Sharpe 1.12  |  Alpha +4.8%  |  Drawdown -13.1%
Degradation:                -0.29 Sharpe |  -1.4% Alpha

✓  Held-out Sharpe 1.12 meets minimum threshold (0.85)
✓  Degradation -0.29 within maximum (0.35)
✓  All other criteria met

[ Promote to Sentinel ]
```

No surprises. The held-out results are shown, always, before the user confirms promotion.

---

## PART VIII: THE SENTINEL LIFECYCLE

### 8.1 What Promotion Creates

Promotion does three things simultaneously:

1. **Locks the configuration.** Any modification creates a new version and requires a new Full Production Backtest before the new version can be promoted. The currently deployed version runs unchanged until explicitly replaced.

2. **Initializes a paper portfolio.** The user declares capital at promotion time (e.g., $5,000). This is the notional size of the paper account. All position sizes in future signals are calculated against this figure. The paper portfolio tracks its own NAV in real time.

3. **Starts live monitoring.** The Sentinel runs the complete pipeline — data ingestion, health monitoring, Fundamental Engine, Custom Engines, signal gate evaluation, Analyst Engine on gated events — against real market data, continuously.

### 8.2 The Proving Ground Phase

Before promotion, any configuration can be run in the Proving Ground — live paper trading against the real market, no real money, full signal generation. This phase is distinct from post-promotion live mode in one critical way: it is still a testing phase, and MLflow logs it as `run_type=live_paper`. The configuration can still be modified, and modified versions can be compared in the Arena.

The Proving Ground reveals things backtests cannot:
- Regime shifts that occur after the backtest period that break a historically-validated system
- Data latency issues in live market conditions vs. historical simulation
- Edge cases in the signal gate that 2 years of historical data happened not to contain
- Whether the system's signal frequency is emotionally tolerable in practice — a system that generates 3 signals per day when you expected 2 per month is useful to discover in paper before live

The Proving Ground is optional but strongly recommended. Unlike the Sandbox, it has no automatic pass/fail gate — promotion from the Proving Ground is always a user decision. But "optional but recommended with no criteria" becomes a checkbox that users skip. To give it teeth, the platform supports a `proving_ground_criteria` block that makes the user explicitly acknowledge whether the live behavior met their expectations.

```json
{
  "proving_ground_criteria": {
    "min_observation_days":        30,
    "min_signals_generated":       5,
    "max_win_rate_degradation":    0.15,
    "max_drawdown_vs_backtest":    0.05,
    "max_signal_frequency_ratio":  3.0,
    "require_explicit_sign_off":   true
  }
}
```

**`min_observation_days`** — the minimum live paper trading period before promotion is permitted. 30 days minimum catches at least one full earnings cycle and at least one macro event. Shorter is not meaningful.

**`min_signals_generated`** — the system must have generated at least this many signals during the Proving Ground. A configuration that generated zero signals in 30 days didn't fail — it was never tested. Something in the signal gate is too restrictive and needs investigation.

**`max_win_rate_degradation`** — allowed drop in win rate vs. the held-out backtest window. A system with 65% win rate in the held-out window and 45% in 30 days of live paper trading has degraded beyond acceptable variance. The comparison anchors to the held-out window — not the optimization window.

**`max_drawdown_vs_backtest`** — allowed max drawdown in live paper trading beyond the backtest max drawdown. If the backtest showed -12% max drawdown and the Proving Ground shows -18%, that's a 6-point overage. Investigate before promoting.

**`max_signal_frequency_ratio`** — if the system generates 3x more signals in live than it did in backtest, the signal gate is behaving differently in live conditions than in simulation. Investigate data latency differences, regime shifts, or edge cases in the gate logic.

**`require_explicit_sign_off`** — when enabled (default), the promotion button is not available until the user explicitly reviews a Proving Ground summary card and confirms: "I have reviewed the live paper trading behavior and am satisfied." This is a forcing function, not a checkbox. The summary card shows each criterion and whether the system met it.

When a criterion is not met, the summary card shows the specific shortfall and suggests a diagnosis path — it does not block promotion, but requires the user to acknowledge the shortfall before proceeding. The acknowledgment is logged to MLflow.

#### 8.2.1 Why Thesis-First in the Wizard Matters Here Too

The Proving Ground is where the user watches their live system generate signals and decides whether to trust it enough to promote. The quality of that decision depends heavily on whether the user's system was built around a genuine belief or reverse-engineered to match a template.

This connects to the Sentinel Wizard design: Step 1 of the wizard is thesis articulation — what do you actually believe about the market opportunity you're targeting? Step 2 is template matching based on that articulation. Template-first (the v6.0 design) encouraged users to pick a template that looked rigorous, then construct a belief that justified it. That produces systems the user doesn't fully trust in the Proving Ground because they were never fully theirs. Thesis-first forces the honest question before any template anchoring occurs.

### 8.3 Buy Signal Card

Every BUY recommendation generated by the Deployed Sentinel is surfaced as a Signal Card in the user's dashboard.

```
┌─────────────────────────────────────────────────────────────────────┐
│  SENTINEL: Tech Breakout v3.2                March 8, 2026  4:02 PM │
├─────────────────────────────────────────────────────────────────────┤
│  📈  BUY SIGNAL  —  AAPL                                            │
│                                                                     │
│  Position:  15 shares  @  ~$187.40  =  $2,811 (9.7% of portfolio)  │
│  Expected hold:  8–14 trading days                                  │
│  Price target:  $197.00  |  Stop-loss:  $181.00                     │
│                                                                     │
│  ─── Agent Reasoning ─────────────────────────────────────────── │
│  "Services revenue grew 14% YoY per latest 10-Q [EDGAR 3/1/26].   │
│  Two officers filed Form 4 cluster buys totalling $4.2M in past    │
│  18 days [Form 4 filed 2/19/26, 2/28/26]. Analyst consensus EPS   │
│  revised up 3.1% over past 30 days [Finnhub 3/7/26]. Risk agent   │
│  confirms position is within drawdown and concentration limits."   │
│                                                                     │
│  ─── Signal Anchors ──────────────────────────────────────────── │
│  Earnings Revision   +3.1%  ↑  (above 3.0% gate threshold)   ✓   │
│  Insider Activity    Cluster Buy  (CEO + CFO, 18 days)        ✓   │
│  FinBERT Sentiment   +0.71  (Strong Positive, 4 sources)      ✓   │
│  Risk Agent          APPROVED  —  all constraints met         ✓   │
│  Supervisor Model    Claude Sonnet 4.6  (uncertainty: 0.79)        │
│                                                                     │
│  ─── System Track Record ─────────────────────────────────────── │
│  This Sentinel:  9 / 12 signals profitable  (75.0% win rate)       │
│  Held-out window (backtest):  68% win rate  |  avg +3.1% per trade │
│  Paper portfolio:  +$1,847  (+6.4%)  since deployment              │
│                                                                     │
│  ⚠  This signal was generated by an AI system. It is not           │
│     financial advice. Verify all claims before acting.              │
│                                                                     │
│  [ ✅  ACCEPT — Mirror in Robinhood ]    [ ❌  DECLINE ]           │
│  [ 🔍  Open Full Glass Box Audit ]                                 │
└─────────────────────────────────────────────────────────────────────┘
```

**ACCEPT:** Paper portfolio executes the position. User manually replicates in real brokerage account. Paper and real accounts are now synchronized on this position.

**DECLINE:** Paper portfolio executes the position hypothetically. Real account is unchanged. The system records: "User declined this signal on March 8, 2026." The position runs in the paper account and the outcome is tracked permanently.

The decline counterfactual is one of the most valuable feedback mechanisms in the platform. Over time the user builds a personal track record of when their discretion adds value and when it costs them.

**Supervisor model attribution** is always shown on the Signal Card. Users know whether this signal was generated by Claude or by Qwen 14B.

**Track Record anchoring — held-out window only:** The "Similar setups (backtest)" line on the Signal Card anchors to the held-out validation window win rate and average return — not the optimization window. The optimization window was the one the Improvement Loop ran on for multiple iterations. Its win rate is biased upward by the tuning process. The held-out window is the honest comparison: data the system never saw during optimization. If the configuration has not yet been promoted (Signal Card appears during Proving Ground), this line shows "N/A — promote to unlock backtest comparison" rather than silently defaulting to optimization window numbers.

### 8.4 Close Signal Card

When an exit condition is met — price target reached, stop triggered, hold duration exceeded, fundamental shift detected, or risk budget exceeded — a Close Signal Card is surfaced.

```
┌─────────────────────────────────────────────────────────────────────┐
│  SENTINEL: Tech Breakout v3.2               March 16, 2026  3:47 PM │
├─────────────────────────────────────────────────────────────────────┤
│  📉  CLOSE SIGNAL  —  AAPL                                          │
│                                                                     │
│  Opened:   March 8   @  $187.40  (15 shares)                       │
│  Close at: March 16  @  ~$196.20                                    │
│  Paper P&L:   +$132   (+4.7%)   |   Hold duration:  8 trading days  │
│                                                                     │
│  ─── Exit Rationale ──────────────────────────────────────────── │
│  "Price target of $197 approached. FinBERT sentiment shifted from  │
│  +0.71 to +0.12 following supply chain commentary in analyst note  │
│  published this morning [Finnhub 3/16/26]. Risk agent recommends   │
│  taking profit at current level rather than holding into weakening │
│  original signal conditions."                                       │
│                                                                     │
│  ─── Exit Type ────────────────────────────────────────────────  │
│  ● Target Approached    ○ Stop Triggered    ○ Fundamental Shift    │
│  ○ Hold Duration        ○ Risk Budget                              │
│                                                                     │
│  [ ✅  ACCEPT — Close in Robinhood ]    [ ❌  HOLD — Keep it ]     │
│  [ 🔍  Open Full Glass Box Audit ]                                 │
└─────────────────────────────────────────────────────────────────────┘
```

Close signals are first-class outputs with equal design priority to buy signals. A system that generates good entries but ambiguous exits is not a complete portfolio manager.

**Five exit condition types:**
- **Target approached:** price reached configured target
- **Stop triggered:** price hit configured stop-loss
- **Hold duration:** position exceeded maximum configured hold
- **Fundamental shift:** Fundamental Engine or Custom Engine detects material change in the original signal conditions (see §8.4.1 for implementation)
- **Risk budget:** maintaining the position would exceed configured drawdown budget

#### 8.4.1 Fundamental Shift — Entry State Snapshot (Implementation Required)

The "Fundamental Shift" exit type is non-trivial to implement correctly. It requires the system to continuously compare current signal conditions against the conditions that originally justified the entry. Without a precise spec, developers will implement something reasonable that either triggers false closes on normal signal noise or never triggers at all.

**What must be stored at position open:**

```python
@dataclass
class EntryStateSnapshot:
    position_id:         str
    ticker:              str
    opened_at:           datetime

    # Fundamental Engine state at entry
    earnings_revision:   float     # the revision magnitude that crossed the gate
    insider_activity:    str       # "cluster_buy" | "single_buy" | "neutral"
    finbert_score:       float     # FinBERT composite score at entry

    # Signal gate state at entry — the exact conditions that passed
    gate_conditions_met: Dict[str, Any]  # {condition_name: value_at_entry}

    # Custom engine states at entry (if any)
    custom_engine_states: Dict[str, Any]  # {engine_id: output_at_entry}

    # Divergence thresholds (from config at entry time)
    thresholds: Dict[str, float]  # {condition_name: max_allowed_divergence}
```

This snapshot is stored alongside the trade record in the portfolio state and in MLflow as a trade artifact.

**Continuous comparison during hold period:**

On each simulation tick (or live market day), the Close Signal Generator compares current signal values against the entry snapshot:

```python
def evaluate_fundamental_shift(position, current_signals, snapshot) -> bool:
    divergences = []

    # Check each gate condition that was true at entry
    for condition, entry_value in snapshot.gate_conditions_met.items():
        current_value = current_signals.get(condition)
        threshold = snapshot.thresholds.get(condition)

        if current_value is not None and threshold is not None:
            divergence = abs(current_value - entry_value)
            if divergence > threshold:
                divergences.append({
                    "condition": condition,
                    "entry_value": entry_value,
                    "current_value": current_value,
                    "divergence": divergence,
                    "threshold": threshold,
                })

    # Fire close signal if ANY gate condition has diverged beyond threshold
    return len(divergences) > 0, divergences
```

**Default divergence thresholds (configurable):**

```json
{
  "fundamental_shift_thresholds": {
    "earnings_revision":   0.05,
    "finbert_score":       0.30,
    "insider_activity":    "any_deterioration"
  }
}
```

If `earnings_revision` at entry was `+0.031` and the current quarter shows `-0.019` — a divergence of `0.05` — that crosses the default threshold and triggers a Fundamental Shift close signal. The Close Signal Card displays the specific divergence: "Earnings revision has moved from +3.1% at entry to -1.9% today — a 5.0 point shift exceeding the 5.0 point threshold."

**Why this matters:** without the entry state snapshot, the Close Signal Generator has no anchor. It can detect that current conditions are weak in absolute terms, but it cannot detect that conditions have changed materially from the specific conditions that justified *this particular entry* at *this particular time*. The snapshot is what makes the Fundamental Shift exit type meaningful rather than just a second signal gate pass running in reverse.

**If you DECLINE a close signal** (choose to hold past the system's exit): paper portfolio closes the position and records it as closed. Your real account continues holding. The counterfactual tracks what would have happened if you had exited when the system said to. This is often the most instructive data point in the Mirror Portfolio.

### 8.5 The Mirror Portfolio

The complete paper account for a given Sentinel. Every position ever opened. Every close generated. Every accept/decline decision. The counterfactual performance of every declined signal.

**Initialization:** user declares capital at promotion. Paper portfolio starts at that NAV.

**ACCEPT on BUY:** paper opens position. User opens same in real account. Synchronized.
**DECLINE on BUY:** paper opens hypothetically. Real unchanged. Counterfactual tracked.
**ACCEPT on CLOSE:** paper closes. User closes in real account. Synchronized.
**DECLINE on CLOSE:** paper closes. User holds past system exit. Real account diverges. Cost tracked.

```
Mirror Portfolio: Tech Breakout v3.2 — 90 Days

Paper Portfolio NAV:    $5,847   (+16.9%)
Your Real Account:      $4,991   (+12.3% estimated)
Gap:                    -$856    (-4.6 percentage points)

Where the gap came from:
─────────────────────────────────────────────────────────
  BUY signals you declined to enter:      3
    Combined counterfactual impact:        +$412 you left on table
    Note: 2 of 3 would have been profitable (67% win rate)

  CLOSE signals you declined (held longer): 2
    Combined cost of holding past exit:    -$1,268
    Note: Both positions declined after system exit signal

  Net judgment impact:                     -$856

─────────────────────────────────────────────────────────
  Your best judgment call: Declined TSLA buy signal on Feb 3.
  Paper took -8.2% before hitting stop. You avoided it.

  Your worst judgment call: Held NVDA past close signal on Feb 28.
  Cost $847 additional loss before you eventually closed.
```

This is not a judgment. It is data. Over time it reveals whether the user's discretionary overrides add value or cost them money — something no other retail platform provides.

---

## PART IX: THE GLASS BOX

### 9.1 Principle

Every signal the platform has ever generated — historical or live — must be fully reproducible and auditable from raw data to final output. The Glass Box is not a UI view. It is a principle applied to every layer.

Given any Signal Card in the system's history, the user can open the Glass Box and reconstruct exactly: what data each agent saw (with `public_disclosure_ts` for every record), what each sub-agent reasoned, what each custom engine contributed, which model handled the Supervisor, what parameters were active, and what the Supervisor concluded and why.

Three reasons this matters:

**Trust.** A user who knows they can open the Glass Box and see the complete reasoning chain trusts the surface-level summary more — even if they never look. Transparency at depth creates trust at the surface.

**Improvement.** When a signal is wrong, the Glass Box is how you diagnose it. Not "the system was wrong" but "the Research Agent retrieved an outdated filing" or "the custom momentum engine produced a spurious high score on anomalously low volume." The Glass Box turns failures into actionable diagnostics.

**Auditability.** Any signal, any time, fully reproducible. No post-hoc rationalization is possible because the data snapshot is preserved.

### 9.2 Glass Box Contents

| Layer | What Is Preserved |
|---|---|
| Data snapshot | Exact OHLCV, fundamental, and alternative data visible at signal time, with `public_disclosure_ts` for every record |
| Fundamental Engine | Earnings revision values, insider activity events, macro overlay state — all at signal time |
| Custom Engines | `EngineOutput.reasoning` dict for every registered custom engine, logged verbatim |
| Plugin state | HMM regime, VPIN score, Chronos range — if plugins were active |
| Signal gate | Exact condition evaluation showing which factors passed, failed, and by what margin |
| Research Agent | ChromaDB query issued, documents retrieved with filing metadata, evidence synthesis |
| Sentiment Agent | FinBERT scores per source, narrative synthesis |
| Risk Agent | Constraint evaluation line by line, position size calculation, veto or approval |
| Supervisor | Full output untruncated, `model_used` field, `uncertainty_score` that triggered routing |
| MLflow Run ID | Direct link to the configuration version and run that produced this Sentinel |

### 9.3 Anchored Reasoning

In Signal Cards and the Glass Box, every factual claim in the agent's reasoning links to its underlying data source. Hovering "Services revenue grew 14% YoY" highlights the specific 10-Q chunk retrieved from ChromaDB. Hovering the earnings revision figure highlights the Finnhub data record. Hovering the insider buy event highlights the Form 4 filing with its `edgar_accession_ts`.

Citations are structural. They are the difference between a summary the user trusts and one they must accept on faith.

---

## PART X: MODEL ROUTING AND THE VALIDATION BUDGET SYSTEM

### 10.1 The Problem

At $30 total Claude budget, the platform must treat each API call as a finite and valuable resource — not a free commodity. A naive architecture that routes every Supervisor call to Claude burns through the $30 in 6 Full Production Backtests. At that point you have validated 6 configurations and have no budget remaining for live Sentinel operation, which is where Claude actually matters most — because now you're generating signals you might act on with real money.

The solution is not to avoid Claude. The solution is to allocate Claude intelligently:
- Use it for signals where its reasoning quality changes the output
- Route everything else to Qwen 2.5 14B locally
- Track exactly what you spend and what you get for it
- Give yourself explicit budget control before every run

### 10.2 The Three Routing Modes

The routing mode is a single field in the configuration. Changing it changes everything about how Claude is used in that configuration.

**Build Mode** — developing the platform, testing plumbing, integration work

```json
{ "mode": "build" }
```

Claude: not invoked at all. Qwen 2.5 14B handles every Supervisor call.
Use when: writing the pipeline, testing MLflow logging, debugging the simulation loop, running Quick Iteration Runs.
Claude weekly spend: $0.00

**Validate Mode** — running real backtests, iterating on configurations

```json
{
  "mode": "validate",
  "claude_budget_usd": 1.00,
  "allocation_strategy": "uncertainty_first",
  "min_uncertainty_threshold": 0.65,
  "budget_exhausted_behavior": "fallback"
}
```

Claude: invoked on high-uncertainty signals up to the declared budget. Everything else uses Qwen 14B.
Use when: running Full Production Backtests on configurations you're seriously evaluating.
Claude weekly spend: $0.50–$2.00 depending on budget setting.

**Production Mode** — Deployed Sentinel generating live signals you might act on with real money

```json
{ "mode": "production" }
```

Claude: invoked on every Supervisor call unconditionally.
Use when: the Sentinel is live and generating Signal Cards you're considering mirroring.
Claude monthly spend: ~$0.25–$0.35 per active Sentinel (swing strategy, 3–5 signals/month).

### 10.3 The Uncertainty Router

In Validate Mode, before any Supervisor call, the Uncertainty Scorer evaluates whether Claude's reasoning quality is likely to change the output of this specific gated event. This is pure mathematics — no LLM involved.

**Critical acknowledgment: the weights below are starting priors, not calibrated values.** They are reasonable guesses about which factors make a signal harder to synthesize. They have not been empirically validated. The MLflow Cost Attribution View exists specifically to calibrate them: if Claude-routed signals (high uncertainty score) do not outperform Qwen-routed signals (low uncertainty score) on win rate and P&L contribution, the router is miscalibrated and the weights need adjustment. If the performance gap is minimal at a given threshold, lower the threshold and save Claude budget. If the gap is large, raise it. Treat the weights as version 1.0 of a system you will tune with evidence.

```python
def compute_uncertainty_score(ticker, signals, config, episodic_memory) -> float:
    """
    Returns a score from 0.0 (confident, route to Qwen) to
    1.0 (uncertain, route to Claude if budget permits).

    IMPORTANT: These weights are starting priors. Calibrate them using
    the MLflow Cost Attribution View after accumulating 50+ production runs.
    Compare Claude-routed vs. Qwen-routed signal outcomes per factor.
    """
    score = 0.0

    # 1. Signal gate margin — how far above threshold did signals land?
    #    Prior: barely-crossed gate = harder synthesis needed
    #    Calibrate: do low-margin gated events actually produce worse Qwen signals?
    margin = signal_gate.compute_margin(signals, config.signal_gate)
    score += (1.0 - normalize(margin, 0, 2)) * 0.25  # weight: 0.25 (prior)

    # 2. Sub-agent agreement
    #    Prior: disagreements between Research, Sentiment, Risk = harder synthesis
    #    Calibrate: does sub-agent disagreement actually predict Claude outperformance?
    disagreements = count_sub_agent_disagreements(signals)
    score += normalize(disagreements, 0, 3) * 0.25   # weight: 0.25 (prior)

    # 3. Episodic memory precedent
    #    Prior: strong precedent = Supervisor has seen this → low uncertainty
    #    Calibrate: does low episodic similarity actually predict Qwen failure?
    precedent_strength = episodic_memory.query_similarity(ticker, signals)
    score += (1.0 - precedent_strength) * 0.20       # weight: 0.20 (prior)

    # 4. Position size materiality
    #    Prior: larger positions warrant more rigorous reasoning
    #    Calibrate: does position size actually correlate with Claude uplift?
    position_usd = estimate_position_size(ticker, config.position_sizing)
    score += normalize(position_usd, 0, config.position_sizing.capital) * 0.15  # weight: 0.15 (prior)

    # 5. Macro regime novelty
    #    Prior: novel FRED context vs. training period = higher uncertainty
    #    Calibrate: does regime novelty actually predict Qwen failure?
    regime_novelty = macro_overlay.compute_regime_novelty(signals['macro'])
    score += regime_novelty * 0.15                   # weight: 0.15 (prior)

    return min(score, 1.0)
```

#### 10.3.1 Calibrating the Router with MLflow Evidence

After accumulating 50+ Full Production Backtest runs in Validate Mode, the Cost Attribution View will have enough data to answer these questions empirically:

- Do Claude-routed signals have a meaningfully higher win rate than Qwen-routed signals?
- Which of the five factors most strongly predicts the quality gap?
- Is the default threshold (0.65) correctly positioned, or are there high-value Claude calls being blocked and low-value ones being approved?

If the win rate gap is less than 5 percentage points, the router is marginally calibrated — the threshold may be too permissive. If the gap is greater than 15 points, Claude is being under-used — lower the threshold to route more events to it.

Adjust one weight at a time and re-run. Document the adjustment and rationale in MLflow. This is empirical engineering, not guesswork with better numbers.

#### 10.3.2 Phase Two: ML-Based Uncertainty Scoring

The heuristic scorer is Phase 1. Phase 2, once sufficient MLflow traces have accumulated, is a trained classifier that replaces the hardcoded weights entirely.

```python
# Phase 2: Train a lightweight local model on accumulated MLflow traces
# No API calls. No new infrastructure. Built from data you already have.

from sklearn.ensemble import RandomForestClassifier
import mlflow

def train_uncertainty_classifier():
    # Pull all production run traces from MLflow
    runs = mlflow.search_runs(filter_string="tags.run_type='production'")

    # Features: the five uncertainty factors computed at signal time
    # Label: 1 if Claude-routed signal outperformed Qwen baseline by >X%, else 0
    X = extract_uncertainty_features(runs)  # signal margin, disagreements, etc.
    y = extract_claude_uplift_labels(runs)  # did Claude actually improve outcome?

    clf = RandomForestClassifier(n_estimators=100, max_depth=4)
    clf.fit(X, y)

    # Replace heuristic scorer with trained classifier
    # Re-train every 100 new production runs or quarterly
    return clf
```

The RandomForest is deliberately small — `max_depth=4` prevents overfitting on limited traces. The model runs locally, adds no API cost, and directly answers "does Claude improve this specific type of signal?" rather than relying on structural priors.

This upgrade is a Phase 2 milestone: build it after you have 100+ production runs with model attribution in MLflow. The infrastructure already captures everything you need.

**Routing decision:**
```python
def route_supervisor(u_score, config, budget_tracker):
    if config.routing.mode == "build":
        return "qwen2.5:14b"

    if config.routing.mode == "production":
        return "claude-sonnet-4-6"

    # Validate mode: budget-aware routing
    if (u_score >= config.validation.min_uncertainty_threshold and
        budget_tracker.remaining > 0):
        budget_tracker.reserve(ESTIMATED_CLAUDE_COST_PER_CALL)
        return "claude-sonnet-4-6"
    else:
        return "qwen2.5:14b"
```

### 10.4 Budget Configuration Options

```json
{
  "validation": {
    "claude_budget_usd":          1.00,
    "allocation_strategy":        "uncertainty_first",
    "min_uncertainty_threshold":  0.65,
    "budget_exhausted_behavior":  "fallback"
  }
}
```

**`claude_budget_usd`** — your declared ceiling for this run. Hard limit. Set it before you launch.

**`allocation_strategy`:**

| Strategy | Description | Best For |
|---|---|---|
| `uncertainty_first` | Spend Claude on highest-uncertainty events until budget runs out. Best signal quality per dollar. | Standard — use this. |
| `uniform_sample` | Spend Claude on every Nth gated event regardless of uncertainty score. | Baseline comparison: want to compare uncertainty-first vs. random allocation |
| `high_stakes_only` | Spend Claude only when recommended position size exceeds a threshold. | If you care most about large-position signal quality |
| `disabled` | Qwen 14B handles everything. Identical to Build Mode but explicitly declared. | Zero-cost validation runs when testing plumbing only |

**`min_uncertainty_threshold`** — even with budget remaining, don't invoke Claude unless the event clears this floor. Prevents spending budget on marginally uncertain events when the budget is small and you want to preserve it for genuinely ambiguous calls. Default: 0.65.

**`budget_exhausted_behavior`:**

| Behavior | What Happens | When to Use |
|---|---|---|
| `fallback` | Continue with Qwen 14B for remaining events. Run completes. | Default — always want a complete run. |
| `pause` | Run pauses. Notification: "Claude budget exhausted. 127 events remaining. Add budget or resume with Qwen 14B." | When you want explicit control over partial runs. |
| `stop` | Run stops at budget exhaustion. Review partial results. | When you're evaluating early-period performance only. |

### 10.5 Pre-Run Cost Estimator

The Sandbox shows a cost estimate before every Full Production Backtest or Scenario Stress Test. The estimate uses historical signal gate rates from prior runs of similar configurations. On the first run for a new configuration, it uses the template's default gate rate.

```
┌──────────────────────────────────────────────────────────────────┐
│  Run Cost Estimate — Tech Breakout v3.2                          │
│                                                                  │
│  Run type:              Full Production Backtest                 │
│  Date range:            Jan 2023 → Jan 2025  (2 years)          │
│  Tickers:               5                                        │
│  Routing mode:          Validate (uncertainty_first)             │
│                                                                  │
│  Est. trading days:             504                              │
│  Est. signal gate rate:         ~15%  (from prior runs)         │
│  Est. gated events:             ~378                             │
│  Est. high-uncertainty events:  ~79   (21% of gated)            │
│  Claude budget:                 $1.00                            │
│  Est. Claude calls:             ~77   (budget covers ~77)        │
│  Remaining events → Qwen 14B:   ~301                            │
│                                                                  │
│  Estimated Claude spend:        $0.97  ✓  within budget         │
│  Estimated run duration:        8–12 hours                       │
│                                                                  │
│  [ Launch ]  [ Adjust Budget ]  [ Build Mode — $0.00 ]          │
└──────────────────────────────────────────────────────────────────┘
```

### 10.6 MLflow Cost Attribution

Every logged recommendation trace includes model attribution and cost:

```json
{
  "event_id":          "gated-2024-03-15-AAPL",
  "uncertainty_score": 0.81,
  "supervisor_model":  "claude-sonnet-4-6",
  "supervisor_cost":   0.013,
  "signal":            "BUY",
  "confidence":        0.74
}
```

```json
{
  "event_id":          "gated-2024-04-02-AAPL",
  "uncertainty_score": 0.31,
  "supervisor_model":  "qwen2.5:14b",
  "supervisor_cost":   0.000,
  "signal":            "NO_SIGNAL",
  "confidence":        0.38
}
```

The MLflow Arena's Cost Attribution View shows:
- Cumulative Claude spend across all your runs
- Claude-handled signals vs. Qwen-handled signals: win rate comparison, average P&L contribution, average confidence
- Uncertainty score distribution histogram: are high-uncertainty signals actually harder? Is the router calibrated?
- Cost per validated configuration

Over multiple runs, you'll know empirically whether the Uncertainty Router is allocating Claude to the right calls. If Claude-handled and Qwen-handled signals have statistically similar outcomes, you can lower your budget confidently. If there's a meaningful quality gap, the router is earning its keep.

### 10.7 Real Cost Numbers at Your Budget

At $30 total Claude credit with the `uncertainty_first` strategy at $1.00/run:

| Activity | Cost Per Unit | Units at $30 | Notes |
|---|---|---|---|
| Build Mode (development, plumbing, Quick Runs) | $0.00 | Unlimited | Use for all development |
| Full Production Backtest (validate mode, $1 budget) | ~$0.97 | ~30 runs | Enough to validate 5–6 strategies deeply with multiple iterations each |
| Scenario Stress Test (validate mode, $0.50 budget) | ~$0.45 | ~60 scenarios | Thorough stress testing |
| Live Sentinel (production mode, swing strategy) | ~$0.30/month | ~8 months | Per active Sentinel at 3–5 signals/month |
| Emergency reserve | — | ~$3 | Buffer for edge cases and re-runs |

$30 gets you through the complete build and validation phase and into 8+ months of live Sentinel operation per deployed strategy.

### 10.8 Hardware Configuration — Honest Assessment

Previous versions described running Qwen 2.5 14B on a 16GB Mac as "tight but workable." This was optimistic. Here is the actual math.

| Process | Memory | Notes |
|---|---|---|
| macOS + WindowServer | 4–6 GB | Cannot be reduced |
| Qwen 2.5 14B Q4_K_M (Ollama) | 8.5–9.5 GB | Widens as context window fills during 10-K retrieval |
| ChromaDB (under load) | 1–2.5 GB | Spikes when loading large embedding collections |
| MLflow SQLite + FastAPI | ~0.8 GB | Relatively lightweight |
| React dev server | ~0.5–1 GB | Close during Full Production Backtests |
| **Total at peak** | **~15.8–20 GB** | **Exceeds 16GB at the upper end** |

When total memory pressure exceeds physical RAM, macOS begins swapping to SSD. The consequences are not minor: a Quick Iteration Run intended to complete in 2–10 minutes can take 45+ minutes under swap. Full Production Backtests degrade to unpredictable runtimes. Swap also causes latency spikes mid-simulation that can corrupt timing-sensitive results.

**The Honest Recommendation for 16GB Macs: Use Qwen 2.5 8B**

Qwen 2.5 8B Q4_K_M (~5.0 GB) leaves approximately 7 GB of headroom for the rest of the stack — comfortable for all run types without swap risk.

| Model | VRAM | Remaining Headroom | Quality: Constrained JSON | Quality: Open Reasoning |
|---|---|---|---|---|
| Qwen 2.5 7B Q4_K_M | ~4.5 GB | ~7.5 GB | Good | Degrades on multi-step |
| **Qwen 2.5 8B Q4_K_M** | **~5.0 GB** | **~7.0 GB** | **Good** | **Acceptable** |
| Qwen 2.5 14B Q4_K_M | ~8.5 GB | ~2.5 GB | Better | Better — but swap risk real |

The quality gap between 8B and 14B is smallest on the constrained JSON tasks that sub-agents actually perform (Research, Sentiment, Risk Agent) and largest on open-ended causal reasoning (Improvement Analyzer). But if the Improvement Analyzer is running while the system is swapping to disk, the 14B model produces worse *actual* results than a stable 8B. Stable beats theoretically-better-but-thrashing every time.

**Practical configuration for 16GB Mac:**
```
Primary local model: qwen2.5:8b
OLLAMA_MAX_LOADED_MODELS=1
Close React dev server before Full Production Backtests
Watch Activity Monitor memory pressure during first full run
If pressure gauge is yellow or red: cancel, switch to qwen2.5:7b, restart
```

**Upgrade path to 14B:** 32GB unified memory. At 32GB, Qwen 2.5 14B has ~18 GB of headroom — comfortable for any run type including full 10-K corpus retrieval during concurrent agent calls. If Aegis becomes a regular tool, 32GB is the correct hardware target. Changing the routing config from `qwen2.5:8b` to `qwen2.5:14b` is a one-line change when you upgrade.

**Quick Iteration Runs are safe on 16GB regardless of model.** They are Phase 1 only — computation-bound NumPy/pandas with no LLM calls. Memory pressure during a Quick Run comes only from the Python backend and ChromaDB, well within headroom.

### 10.9 The Routing Config

The routing configuration is a top-level field in the run configuration. It is explicit, version-controlled alongside the config, and readable at a glance.

**Default config — 16GB Mac (Qwen 2.5 8B, swap-safe):**

```json
{
  "routing": {
    "mode": "validate",
    "models": {
      "supervisor":           "auto",
      "research_agent":       "qwen2.5:8b",
      "sentiment_agent":      "qwen2.5:8b",
      "risk_agent":           "qwen2.5:8b",
      "improvement_analyzer": "qwen2.5:8b",
      "plain_verdict":        "qwen2.5:8b",
      "nli_check":            "qwen2.5:8b"
    }
  }
}
```

**32GB Mac upgrade — Qwen 2.5 14B (recommended quality ceiling):**

```json
{
  "routing": {
    "mode": "validate",
    "models": {
      "supervisor":           "auto",
      "research_agent":       "qwen2.5:14b",
      "sentiment_agent":      "qwen2.5:14b",
      "risk_agent":           "qwen2.5:14b",
      "improvement_analyzer": "qwen2.5:14b",
      "plain_verdict":        "qwen2.5:14b",
      "nli_check":            "qwen2.5:14b"
    }
  }
}
```

`"auto"` for the Supervisor means the Uncertainty Router decides based on the uncertainty score and remaining budget — routing to Claude or the local model per §10.3. All sub-agent models are always local — this is not configurable in the UI for Tier 1/2 users. Tier 3 users can modify the `models` block directly.

The default config ships with `qwen2.5:8b`. This is the 16GB-safe configuration. Upgrading to `qwen2.5:14b` is a single block change when you move to 32GB hardware — no agent code changes required. Do not use the 14B block on a 16GB Mac: §10.8 documents why this causes swap and what it does to run times.

---

## PART XI: FRONTEND ARCHITECTURE

### 11.1 Navigation

```
AEGIS AI
│
├── /dashboard                     Command Center
│   ├── All active Sentinels: name, version, health state, live paper P&L
│   ├── Pending Signal Cards (BUY queue + CLOSE queue — sorted by uncertainty)
│   ├── Mirror Portfolio summary per Sentinel (paper vs. real, counterfactual gap)
│   ├── Monthly Claude spend tracker (current vs. estimated remaining)
│   └── Recent agent activity (last 5 signal events across all Sentinels)
│
├── /engines                       Engine Library
│   ├── /engines/data              Core connectors, health monitor, connector config
│   ├── /engines/fundamental       Fundamental engine params, current signal state
│   ├── /engines/analyst           Agent configs, model routing, trace history
│   ├── /engines/research          ChromaDB status, document pipeline, filing coverage
│   ├── /engines/plugins           Plugin catalog (all OFF by default), activation flow
│   └── /engines/custom            Custom Engine SDK, registered engines, validation status
│
├── /sandbox                       The Sandbox (primary view — most time spent here)
│   ├── Configuration Editor       Visual builder + raw JSON toggle
│   ├── Run Launcher               Run type selector + pre-run cost estimator
│   ├── Routing Mode Selector      Build / Validate (with budget control) / Production
│   ├── Active Run View            Live metrics stream + agent trace stream (WebSocket)
│   ├── Proving Ground             Live paper trading monitor (pre-promotion)
│   └── Improvement Inbox          APPROVE / REJECT / MODIFY on agent proposals
│
├── /arena                         MLflow Arena
│   ├── Leaderboard                All production runs, sortable, one-click diff
│   ├── Config Diff Viewer         Git-style parameter diff + performance delta
│   ├── System Evolution View      Config lineage history — the engineering record
│   ├── Parallel Coordinate Plot   Parameter regions vs. Sharpe
│   ├── Scenario Survival Matrix   Scenario types vs. configurations
│   ├── LLM vs. Quant-Only View    Phase 1 vs. Phase 2 Sharpe per configuration
│   ├── Cost Attribution View      Claude spend, model comparison, router calibration
│   ├── Proposal Decision Log      All proposals, outcomes, time-to-decision
│   └── Promotion Flow             Held-out validation reveal + promotion confirm
│
├── /sentinels                     Sentinel Manager
│   ├── Deployed Sentinels         Config version, capital, health, live P&L
│   ├── Signal Card Queue          Pending BUY and CLOSE decisions
│   ├── Open Positions             Current positions per Sentinel with real-time P&L
│   └── Mirror Portfolio View      Paper vs. real, counterfactual breakdown, gap analysis
│
├── /create                        New Sentinel Wizard (6 steps)
│   ├── Step 1: What do you believe? (thesis articulation — before any template shown)
│   ├── Step 2: Template matching (system suggests templates that match articulated thesis)
│   ├── Step 3: Asset universe and capital
│   ├── Step 4: Data sources and signal gate
│   ├── Step 5: Position sizing and exit conditions
│   └── Step 6: Routing mode and validation budget → launch into Sandbox
│
└── /settings
    ├── Paper portfolio capital per Sentinel
    ├── Promotion criteria defaults
    ├── Model routing defaults
    ├── Notification preferences
    └── API keys (Anthropic, Finnhub, Alpaca)
```

### 11.2 Design Principles

**Routing mode is always visible.** Current routing mode (BUILD / VALIDATE / PRODUCTION) is shown in the header of the Sandbox and on each Sentinel card. It should never be ambiguous which mode is active. Validate mode shows the remaining Claude budget alongside the mode label.

**Signal Cards include model attribution.** Users always know whether a Signal Card was generated by Claude or Qwen 14B. "Supervisor: Claude Sonnet 4.6 (uncertainty: 0.79)" or "Supervisor: Qwen 2.5 14B (uncertainty: 0.31)". This is not a quality warning — it is transparency.

**Connector health is always visible.** MONITORING / DEGRADED / OFFLINE shown prominently on the Dashboard and Sentinel Manager. Never buried in settings. OFFLINE suspends Signal Card generation, which must be immediately apparent to the user.

**Both Signal Card types are first class.** BUY and CLOSE cards have identical design weight and information density. The platform is a portfolio manager. Exits are as important as entries.

**Progressive disclosure, not hidden complexity.** Advanced views (Glass Box, raw MLflow artifacts, parallel coordinate plots) are always accessible but never the default view. Dashboard and Signal Cards are plain-language first.

**Cost tracker on every Sandbox view.** The remaining Claude budget for the current run and the estimated total session spend are visible at all times in the Sandbox header. No surprises.

**Dark mode first.** `#0D0D12` background. `#1E90FF` accent (blue). `#C5A028` gold for callouts. `#50FA7B` green for ACCEPT / BUY. `#FF5555` red for DECLINE / CLOSE. Monospace (JetBrains Mono) for all financial figures, code, and Glass Box content.

---

## PART XII: DEFAULT TEMPLATES

Templates are pre-configured starting points that define a strategy archetype, the data sources best suited to detect the opportunity it targets, and the signal logic that operationalizes it. Users start with a template, modify it in the Sandbox, or build from scratch via the Engine Library.

| Template | Signal Logic | Hold Duration | Active Engines | Plugins Available | Tier |
|---|---|---|---|---|---|
| Tech Catalyst | Upcoming product/regulatory catalyst not yet priced. FinBERT heavy, 10-Q forward guidance monitoring. | 2–6 weeks | FinBERT + 10-Q, earnings revision, insider monitor | HMM, VPIN, Chronos | 1+ |
| Insider Conviction | Cluster insider buying (Form 4 + Congressional) as forward-return signal | 1–4 months | Form 4 cluster detector, Congressional, FRED overlay | Chronos | 1+ |
| Earnings Revision Momentum | Accelerating positive sell-side estimate revisions | 2–8 weeks | Finnhub revision tracker, FinBERT, SEC EDGAR | HMM | 1+ |
| Conservative ETF Rotation | Macro-regime-driven sector ETF allocation | 1–3 months | FRED heavy, HMM enabled by default, earnings revision | VPIN | 1+ |
| Macro Rotation | Sector rotation on yield curve and credit spread signals | 2–6 weeks | FRED yield curve, credit spreads, sector fundamentals | HMM, VPIN | 2+ |
| Dividend Income | Quality yield with sustainable payout and balance sheet discipline | 3–12 months | FRED rates, earnings stability, payout ratio tracker | Chronos | 1+ |
| Day Trader | Technical and order flow signals, intraday | Intraday | Alpaca tick data, VPIN (core), HMM 15-min | All | 3 only |
| Custom | Blank slate — build from Engine Library | User-defined | All available | All | 2+ |

**Day Trader template note:** Tier 3 only in the wizard. Requires Alpaca API key. Full production backtest on 2 years of 15-minute bar data on Mac 16GB: expect 10–15 hours. In validate mode, Claude invocations are rare for intraday signals (fast-moving, low uncertainty scores typically) — budget can be set lower ($0.25–$0.50 per run).

---

## PART XIII: KNOWN EXECUTION TRAPS

These are specific, concrete engineering failures that will occur if not addressed before the affected feature ships. Five traps. Five known fixes. None of them are theoretical.

---

### Trap 1 — Segment Obfuscation (10-Q Monitoring)

**The Problem**

The Fundamental Engine monitors quantitative metrics by extracting them from sequential 10-Q filings. This works as long as the same metric appears in the same place across quarters. It breaks when a company restructures how it reports segments.

This happens regularly and not by accident. When a division's growth begins to slow, companies restructure reporting segments so the underperforming metric disappears into a blended category. "Azure Revenue" becomes "Intelligent Cloud Services" combined with a hardware division. The agent monitoring Azure revenue finds no matching segment in the new filing.

Two failure modes: the agent generates a false signal (treats absence as deterioration) or silently stops monitoring while appearing to continue. The second is worse.

**The Fix**

Two-stage process. A discriminative cross-encoder (183MB, CPU-native) handles classification. Qwen 8B (generative) is only invoked when classification is genuinely ambiguous or confirms a structural change.

**Stage 1 — Cross-Encoder NLI Classification:**

At each new 10-Q ingest, before any extraction, run `DeBERTa-v3-large` (cross-encoder) against the candidate segment text:

```python
from sentence_transformers import CrossEncoder

# Loaded ONCE at startup as a singleton — do not reload per filing
_nli_model = CrossEncoder("cross-encoder/nli-deberta-v3-large")

def classify_segment_change(historical_label: str, candidate_text: str) -> str:
    """
    Returns: 'ENTAILMENT' | 'NEUTRAL' | 'CONTRADICTION'
    ~1ms per pair on CPU. Model: ~183MB. Requires no GPU.
    """
    scores = _nli_model.predict([(historical_label, candidate_text)])
    labels = ["CONTRADICTION", "ENTAILMENT", "NEUTRAL"]
    return labels[scores[0].argmax()]
```

**Routing logic:**

| Result | Action |
|---|---|
| `ENTAILMENT` | Segment is unchanged. Extract normally. No alert. Qwen not invoked. |
| `NEUTRAL` | Borderline case. Wake Qwen 8B to confirm with constrained JSON schema. |
| `CONTRADICTION` | Confirmed restructuring. Wake Qwen 8B for full extraction. Queue re-anchoring alert. Suspend monitoring. |

**Stage 2 — Qwen 8B (only on NEUTRAL or CONTRADICTION):**

Constrained JSON output schema — no free-form reasoning:
```json
{
  "equivalent_metric_found": true,
  "proposed_replacement": "Intelligent Cloud Services — Azure component",
  "change_type": "cosmetic",
  "confidence": 0.84
}
```

**Stage 3 — Human re-anchoring (mandatory, not skippable):**

On `CONTRADICTION` (or `NEUTRAL` with `change_type: "structural"`): suspend monitoring for the affected metric. Surface a Re-Anchoring Alert: original metric + tracking method, the structural change in plain language, Qwen's proposed replacement with rationale, and "Confirm New Anchor" or "Review Position" action. Monitoring does not resume until the user explicitly confirms the new anchor.

**Why DeBERTa instead of embedding similarity:** The previous spec used cosine similarity between segment label embeddings as Stage 1. This works for surface-level similarity but fails on semantic equivalence — "Intelligent Cloud" and "Azure Revenue" have low cosine similarity despite being the same business. DeBERTa-v3-large as a cross-encoder is specifically trained for NLI (natural language inference) and correctly handles entailment relationships between financial segment descriptions. It runs at ~1ms per pair on CPU versus Qwen's ~2-10 seconds, and the model is 183MB versus Qwen's 5GB. The vast majority of quarters have no segment changes — Stage 1 handles them in milliseconds for free.

This is both the correct engineering behavior and the correct regulatory behavior — the human is explicitly in the loop when the monitoring methodology changes.

---

### Trap 2 — Scenario Library Must Be Deterministic

**The Problem**

Asking an LLM to "simulate a rising rate environment" produces plausible-sounding analysis with no relationship to what actually happened to specific tickers during those periods. The output looks like analysis. It is not. It is a hallucination with financial formatting.

This is not a quality problem — it is a categorical problem. Language models don't have access to the actual price data, earnings reports, and macro readings from specific historical periods. They have statistical patterns from training text. Those patterns produce outputs that sound like historical analysis but are not grounded in it.

**The Fix**

Every scenario in the Scenario Library is a named set of deterministic date ranges. The backtest runs the user's complete pipeline over those exact calendar dates using real FRED, YFinance, and EDGAR data. The LLM is not involved in the simulation itself — only in post-scenario decomposition on structured results.

Show survival rates across all instances of a scenario type, not just the most recent. Surface a recency bias nudge: "You selected 2022. The 1994 and 2018 tightening cycles are useful analogs with different starting valuations — consider running them for comparison."

Post-scenario decomposition: Qwen 2.5 14B receives the structured per-scenario performance table (real numbers from real backtests) and uses a constrained prompt to attribute which factors correlated with survival vs. failure. Never open-ended macroeconomic reasoning from memory.

---

### Trap 3 — Iterative Overfitting in the Improvement Loop

**The Problem**

This is the most dangerous trap and the least visible one. It is dangerous specifically because it is generated by the platform's most valuable feature.

Failure scenario: backtest runs, performance is mediocre, Improvement Analyzer proposes a parameter change, user approves, performance improves. Six rounds later, the MLflow history shows a clean improvement trajectory. Sharpe went from 0.72 to 1.41 through six iterations of agent-guided, user-approved improvements. The user promotes with high confidence.

What they have is a configuration that has been iteratively fitted to a specific historical period through six rounds of human-approved optimization. The MLflow history documents the overfitting process and makes it look like disciplined engineering. Human approval at each step created false confidence that the result was validated — when it was the product of a legitimate-looking process that happened to produce curve-fitting.

**The Fix**

At production backtest initiation, randomly partition 20% of the configured date range as the held-out validation window. This window is:
- Logged to MLflow immediately at run initiation and sealed
- Invisible to the Improvement Analyzer throughout the iteration process
- Not shown in any MLflow view during active iteration
- Never accessible to the user during the optimization phase

The partition is random — not always the most recent 20%. Most-recent-only partitioning is itself a form of bias: the Improvement Analyzer can infer the approximate boundary and the optimization process can implicitly learn to avoid it.

At promotion time, the current configuration is run against the held-out window for the first time. Both windows are shown side by side. The user sees the result before confirming. If held-out degradation exceeds 0.35 Sharpe, promotion is blocked. This is not configurable.

---

### Trap 4 — Connector Health Silent Failure

**The Problem**

Point-in-time discipline prevents lookahead bias. Connector health is a different problem: what happens when the data pipeline delivers no data at all?

A Sentinel running on data that is 3 days stale because YFinance returned a cached response appears healthy on the dashboard. No alerts. No errors. The Fundamental Engine runs. Signals are generated. Signal Cards are surfaced to the user. The user acts on them. All of this happens on information that no longer reflects the current market.

A Sentinel that fails visibly is recoverable. A Sentinel that appears operational while running on stale data is a product integrity failure.

**The Fix**

Covered in §4.2.1. The critical implementation details:
- `last_successful_fetch_ts` on every connector including custom connectors via the SDK
- Health check coroutine running on connector-appropriate intervals (not one-size-fits-all)
- Signal generation suspended on `OFFLINE` — not just flagged
- The asymmetry rule enforced: when status is ambiguous, downgrade
- Custom engines participate in health monitoring via the `health()` SDK method

---

### Trap 5 — Regulatory Framing Drift

**The Problem**

The platform's regulatory position — "user-directed software tool" rather than "autonomous trading system" — is valid but fragile. It depends on implementation details that can drift as the product evolves.

Three specific risks:

**The nudge problem:** If the Improvement Analyzer consistently proposes more aggressive configurations and users consistently approve them, a regulator can characterize the agent as exercising de facto discretion regardless of who clicks the button. The defense is empirical — but only if the data exists from the beginning.

**Signal Card liability:** Any factual error in the agent's reasoning that a user acts on touches liability territory. The Glass Box is the primary defense. But it requires prominent, unavoidable disclosure at signal generation time.

**Marketing language:** Any language implying accuracy guarantees, reliability claims, or systematic correctness creates warranty-like expectations no probabilistic system can meet.

**The Fix**

Proposal decision logging from day one — not retrofitted later. Once the Improvement Analyzer has been running for months without rejection logging, that history is gone. Log every proposal with outcome (APPROVED / REJECTED / MODIFIED_AND_APPROVED), `time_to_decision_seconds`, and user-modified values.

```json
{
  "proposal_id":              "prop-47",
  "proposed_by":              "improvement_analyzer_v2",
  "target_param":             "signal_gate.earnings_revision_threshold",
  "proposed_value":           0.03,
  "outcome":                  "MODIFIED_AND_APPROVED",
  "user_value":               0.04,
  "time_to_decision_seconds": 487,
  "user_notes":               "Agreed with direction, more conservative threshold"
}
```

`time_to_decision_seconds` distinguishes deliberation from rubber-stamping. `MODIFIED_AND_APPROVED` shows the user exercised independent judgment. If approval rates for any proposal type consistently exceed 90%, investigate whether the agent is nudging rather than advising.

Signal Cards must include a non-dismissible disclosure: "This signal was generated by an AI system and is not financial advice. Verify all factual claims independently before acting."

Marketing language to avoid in any public-facing context: accurate, reliable, proven, validated (in reference to future performance), guaranteed. Stay close to: "a research and simulation environment for building personal trading systems."

---

## PART XIV: BUILD ORDER

### Phase 1 — Mathematical Foundation
*(Everything downstream depends on this being correct)*

1. `public_disclosure_ts` on all DataEngine connectors — including Congressional (use `disclosure_filing_ts`, never `trade_date`). Enforced at query level in ChromaDB.
2. Configuration Schema loader, validator, and version manager — JSON spec as in §3.3.
3. Fundamental Engine — earnings revision tracker, insider activity monitor (Form 4 + Congressional), signal gate evaluator, macro overlay.
4. Simulation Loop — vectorized, day-by-day, Phase 1 only (no LLM), with held-out partition logic and slippage injection.
5. Performance Metrics Calculator — all metrics from §6.5 including held-out window metrics.
6. MLflow extended logging — config fingerprint, metrics, artifacts, proposal decision log, cost attribution log from day one.

### Phase 2 — Intelligence Layer

7. Signal gate logic — binary gate condition evaluation before any LLM invocation.
8. Model Routing Layer — routing config, Build/Validate/Production modes, mode visible in UI.
9. Uncertainty Scorer — five-factor scoring, pure math, no LLM.
10. Budget Allocator and Cost Tracker — per-run budget, `budget_exhausted_behavior`, real-time remaining balance.
11. LangGraph integration — Analyst Engine wired into simulation loop as Phase 2, event-gated, uncertainty-routed.
12. Improvement Analyzer — both proposal types (parameter + system insight), constrained JSON output schemas.
13. Scenario Library — deterministic date-range mappings, multi-instance backtest runner, post-scenario decomposition.
14. Quick Iteration Run mode — 90-day, Phase 1 only, no LLM, 2–10 minutes.
15. Pre-run Cost Estimator — estimate gated events, high-uncertainty fraction, Claude spend before launch.

### Phase 3 — Custom Engine SDK

16. `BaseEngine` abstract class — `EngineInput`, `EngineOutput`, `EngineHealth` dataclasses.
17. Custom Engine Registry — registration, validation sequence (§5.7), Engine Library integration.
18. Wrapper sandbox for simulation mode — prevent network calls and external data access in `run()`.
19. Glass Box custom engine rendering — collapsible section per registered engine with `describe()` header.
20. Custom engine health monitor integration — `health()` method on same check schedule as connectors.

### Phase 4 — Sentinel Layer

21. Connector Health Monitor — `last_successful_fetch_ts`, health state evaluation, signal suspension on OFFLINE.
22. Segment Obfuscation NLI Check — embedding similarity stage, constrained Qwen stage, re-anchoring alert flow.
23. Sentinel State Manager — tracks live Sentinels, manages signal pipeline, queues Signal Cards.
24. Mirror Portfolio Tracker — paper account NAV, position tracking, accept/decline recording, counterfactual P&L.
25. Close Signal Generator — all five exit condition types, Close Signal Card generation.
26. Promotion Gate Evaluator — held-out validation run, degradation check, side-by-side display, promotion confirm.
27. Plugin Layer — VPIN, HMM, Chronos, Alpaca, all OFF by default, context-only enforcement.

### Phase 5 — Frontend

28. Sandbox primary view — configuration editor, run launcher with cost estimator, routing mode selector, WebSocket live metrics and agent trace streams.
29. Signal Card UI (BUY and CLOSE) — full spec from §8.3/8.4, anchored reasoning hover interactions, non-dismissible disclosure, model attribution.
30. Mirror Portfolio dashboard — paper vs. real NAV, counterfactual breakdown, per-Sentinel gap analysis.
31. MLflow Arena — all seven views from §7.3, cost attribution view, promotion flow.
32. Engine Library hubs — per-engine catalog, health status, plugin catalog, custom engine registration UI.
33. Glass Box audit view — complete signal audit trail with anchored hover interactions, custom engine sections.
34. New Sentinel Wizard — 6-step thesis-first creation flow, routing mode and budget configuration in Step 6.
35. Dashboard — Sentinel health cards, Signal Card queue, Mirror Portfolio summaries, Claude spend tracker.

---

## PART XV: GUIDING PRINCIPLES

| Principle | What It Means in Practice |
|---|---|
| The Sandbox is the product | Everything else — Engine Library, Sentinel, Signal Cards, Glass Box, Custom Engine SDK — exists to configure what the Sandbox runs or to deploy and audit what it produces. If a feature doesn't serve the Sandbox loop, question whether it should exist. |
| You built it. You tested it. You trust it. | The platform's value is the process by which users build conviction in their own systems through rigorous, auditable testing. A signal from a system you built and watched for 90 days is qualitatively different from a signal received cold from a black box. |
| Paper trading exclusively | Real money only moves when the user manually mirrors a paper trade. This is not a regulatory hedge. It is the right architecture for a retail investor who is still learning whether their system works. |
| Slippage is always real | Returns without realistic transaction costs are fiction. Every run, every template, every tier, no exceptions. Slippage Drag is always shown alongside gross return. |
| Point-in-time is non-negotiable | Applies to all connectors, all RAG retrievals, all simulation loops, all custom engine inputs. Congressional trading data uses `disclosure_filing_ts`, never `trade_date`. No exceptions. |
| The held-out window is non-negotiable | A promoted configuration not evaluated on genuinely unseen data is not validated — it is overfit with extra steps. `held_out_sharpe_min` and `held_out_degradation_max` are non-configurable defaults. |
| Claude is a finite resource with a budget | $30 is not unlimited. Treat each Claude call as a finite resource. Build Mode costs $0. Validate Mode has an explicit budget ceiling you set before each run. The Uncertainty Router ensures those dollars go where they matter. |
| The Uncertainty Router earns its keep | Claude is valuable on signals where its reasoning quality changes the output. Routing it to every call regardless of signal clarity wastes budget on easy calls while degrading coverage. Track whether the router is calibrated and adjust thresholds based on MLflow evidence. |
| Plain language is the primary output | A platform that requires users to interpret Sharpe ratios to understand what the Sandbox is telling them has failed. Every run produces a plain-language verdict alongside raw metrics. The verdict is the primary output for Tier 1 users. |
| Connector health is displayed, not hidden | A Sentinel appearing healthy while running on stale data is worse than a broken one. MONITORING / DEGRADED / OFFLINE states are always visible on the Dashboard. The asymmetry rule: when status is ambiguous, downgrade. |
| Custom engines are first-class participants | A custom engine integrated via the SDK participates in Glass Box logging, health monitoring, and MLflow attribution identically to a built-in engine. The wrapper contract enforces the boundary; it does not constrain the internals. |
| Proposal decisions are logged from day one | The regulatory user-directed defense depends on empirical data about how users interact with agent proposals. That data must exist from the first proposal the system generates. It cannot be retrofitted. |
| The Glass Box is a principle, not a view | Every signal ever generated must be fully reproducible and auditable from raw data to final output. Transparency at depth creates trust at the surface even for users who never look. |
| Close signals are first class | A system that generates good entries but ambiguous exits is not a complete portfolio manager. BUY and CLOSE Signal Cards have equal design weight, equal information density, and equal importance. |

---

## PART XVI: DEFAULT TEMPLATES — DETAILED

*(Expanded from §12 to specify signal gate conditions and default parameters for each template)*

**Tech Catalyst**
```json
{
  "signal_gate": {
    "finbert_above": 0.5,
    "earnings_revision_direction": "up",
    "insider_activity": "neutral_or_positive"
  },
  "fundamental_engine": {
    "earnings_revision": { "warn_threshold": 0.02 },
    "insider_monitor": { "cluster_window_days": 45 }
  },
  "position_sizing": { "max_position_pct": 0.15, "method": "equal_weight" },
  "sandbox": { "slippage_bps": 15, "min_hold_days": 5 }
}
```

**Insider Conviction**
```json
{
  "signal_gate": {
    "require_cluster_buy": true,
    "cluster_min_officers": 2,
    "cluster_min_dollar_value": 500000
  },
  "fundamental_engine": {
    "insider_monitor": { "cluster_window_days": 30, "include_congressional": true },
    "macro_overlay": { "enabled": true }
  },
  "position_sizing": { "max_position_pct": 0.20, "method": "conviction_weighted" },
  "sandbox": { "slippage_bps": 12, "min_hold_days": 14 }
}
```

**Conservative ETF Rotation**
```json
{
  "signal_gate": {
    "hmm_regime": ["bull"],
    "earnings_revision_direction": "neutral_or_up",
    "macro_regime": "not_tightening"
  },
  "plugins": { "hmm": { "enabled": true, "n_states": 3 } },
  "asset_universe": { "tickers": ["XLK", "XLV", "XLF", "XLI", "XLY"] },
  "position_sizing": { "max_position_pct": 0.25, "method": "equal_weight" },
  "sandbox": { "slippage_bps": 8, "min_hold_days": 21 }
}
```

---

## PART XVII: CHANGELOG — V3 THROUGH V6

### The Cumulative Changes

| Area | v3 | v4 | v5 | v6 |
|---|---|---|---|---|
| Core product description | Quant hedge fund toolkit | Thesis monitoring platform | Paper portfolio manager (correct) | Paper portfolio manager (fully specified) |
| Sentinel purpose | Signal generator | Thesis breach monitor | Portfolio manager | Portfolio manager — complete lifecycle |
| Primary signal layer | VPIN + HMM (microstructure) | Thesis Parameter Monitor | Fundamental Engine | Fundamental Engine + Custom Engine SDK |
| Close signals | Underspecified | HOLD/RE-EVALUATE/EXIT on thesis breach | First-class, 5 exit types | First-class, 5 exit types, Card UI spec |
| Mirror Portfolio | Counterfactual tracker | Thesis monitor aid | Full paper account | Full paper account + gap analysis + counterfactual breakdown |
| Claude usage | Unspecified | Supervisor + all reasoning | Supervisor + all reasoning | Uncertainty Router + Budget System + Build/Validate/Production modes |
| Local model | Not specified | Qwen 2.5 7B | Qwen 2.5 14B | Qwen 2.5 14B (with 7B fallback documented) |
| Custom engines | Not present | Not present | Vague mention for Tier 3 | Full Custom Engine SDK with wrapper contract, roles, Glass Box integration, health monitoring |
| Architecture layers | 6 | 7 | 7 | 8 (Model Routing + Validation Budget as dedicated layer) |

### What Changed v5 → v6

**Added: Custom Engine SDK (Part V)**
- `BaseEngine` abstract class with `run()`, `describe()`, `health()` methods
- `EngineInput`, `EngineOutput`, `EngineHealth` dataclasses
- Five signal roles: `DATA_SOURCE`, `SIGNAL_GENERATOR`, `GATE_CONDITION`, `CONTEXT_MODIFIER`, `RISK_OVERRIDE`
- Automatic Glass Box integration via `EngineOutput.reasoning`
- Automatic health monitor integration via `EngineHealth`
- Registration + validation sequence (Quick Iteration Run required before production use)
- Custom connector interface (`BaseConnector`) extended to full engine SDK

**Added: Validation Budget System (Part X)**
- Three routing modes: Build ($0), Validate (budget-controlled), Production (full Claude)
- Uncertainty Scorer — five-factor scoring, pure math
- Budget Allocator with four strategies: `uncertainty_first`, `uniform_sample`, `high_stakes_only`, `disabled`
- `budget_exhausted_behavior`: `fallback`, `pause`, `stop`
- Pre-run Cost Estimator in Sandbox UI
- MLflow Cost Attribution per-call tracking (`supervisor_model`, `uncertainty_score`, `supervisor_cost`)
- Cost Attribution View in MLflow Arena
- Real cost numbers at $30 budget documented
- Hardware configuration documented with realistic memory numbers

**Added: `RISK_OVERRIDE` role confirmation flow**
Custom engines declaring `RISK_OVERRIDE` require explicit user confirmation in the Sentinel Wizard.

**Updated: Architecture diagram**
Layer 4 now shows Custom Engine Registry explicitly. Layer 4 (Model Routing) elevated to dedicated layer (now Layer 4, storage moved to Layer 3).

**Updated: Signal Cards**
- Supervisor model attribution now shown on every Signal Card
- Uncertainty score shown alongside model attribution

**Updated: MLflow Arena**
Cost Attribution View added as a first-class view alongside the other six Arena views.

**Updated: Build Order**
Phase 3 added for Custom Engine SDK (between Intelligence Layer and Sentinel Layer).

### What Changed v4 → v5

- Core mental model rewritten: Sentinel is paper portfolio manager, not thesis monitor
- Buy Signal Card: complete position spec (shares, dollar value, % of portfolio, expected hold, price target, stop)
- Close Signal Card: first-class output with five exit condition types
- Mirror Portfolio: full paper account with NAV tracking, open positions, accept/decline history
- Proving Ground: distinct pre-promotion live paper trading phase
- Qwen 2.5 7B → Qwen 2.5 14B
- Connector Health Monitor added (§4.2.1)
- Segment Obfuscation trap documented with three-stage fix
- Scenario Library specified as deterministic date-range mappings (never LLM simulation)

### What Changed v3 → v4

- VPIN/HMM moved from default pipeline to Plugin Library (OFF by default)
- Fundamental Engine introduced as primary signal layer
- Signal Card framing changed from BUY/HOLD/SELL to HOLD/RE-EVALUATE/EXIT (overcorrection — corrected in v5)
- LangGraph topology introduced
- MLflow extended logging introduced
- Held-out validation partition introduced (Trap 3 fix)
- Congressional data elevated to Core connector
- Two execution traps documented (iterative overfitting, scenario simulation)

### What Has Never Changed

These elements were correct in v3 and have not been modified in any subsequent version:

- Point-in-time data discipline (`public_disclosure_ts` on all connectors, simulation loop enforcement)
- Slippage and market impact simulation — non-negotiable, every run
- Two-phase backtest architecture (vectorized Phase 1 + event-gated LLM Phase 2)
- Signal gate architecture — LLM fires only on gated events (cost control + signal quality)
- Glass Box principle — every decision auditable to raw data
- LangGraph agent topology (Supervisor + Research + Sentiment + Risk)
- ChromaDB RAG with point-in-time retrieval filtering
- Episodic memory for Supervisor self-calibration
- MLflow as the court of truth for all configuration validation
- WebSocket streaming for live agent traces during Sandbox runs
- The Agent Improvement Loop as the core differentiator
- FastAPI + React + Vite technology stack
- Three-phase validation: historical backtest → Proving Ground → Sentinel promotion
