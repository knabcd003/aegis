# Aegis AI — Comprehensive System Blueprint v4.2

**One-Line Thesis:** The Databricks for retail investing — a transparent, auditable belief-testing machine that lets retail investors build real market judgment by stress-testing their ideas against reality before committing a single dollar.

---

## A Note on This Version

v3 was an excellent engineering document for a quant hedge fund that had been retrofitted for retail investors. v4 is a retail conviction platform that happens to have serious quant infrastructure underneath. The difference is not cosmetic — it changes what gets built first, what gets surfaced in the UI, and what the platform promises to deliver.

The platform does not promise alpha. It promises something more defensible and more valuable: **auditable conviction.** Users who want to go deeper get the full quant engine. Users who want a thesis-tracking tool get that. Both use the same infrastructure. Neither gets a black box.

---

## Part I: Product Vision

### 1.1 What Aegis AI Is

Aegis AI is a quantitative strategy research and conviction-building platform for retail investors who have been failed by two kinds of tools: black-box signal generators that tell you what to do without explaining why, and raw quant platforms that require a PhD to operate.

The platform is built around a single insight: **retail investors don't lose money because they lack access to good signals. They lose money because they lack conviction in their own reasoning — and without conviction, fear wins.** A person who genuinely understands why they own a position holds through volatility. A person following a signal they don't understand panic-sells the moment it stops working.

Aegis AI is the infrastructure for building that understanding. It is a laboratory where investment theses are constructed, stress-tested against historical reality, refined through agent analysis, and then monitored against the live market. Every step of the reasoning is transparent, logged, and auditable. Nothing is hidden. Nothing is taken on faith.

The platform is explicitly not a signal generator. It does not tell users what to buy. It tells users whether their reasoning holds up — and that is a fundamentally different product.

### 1.2 The Two Modes

**The Laboratory (The Sandbox)** — where AI agents build, break, and improve investment theses and strategy configurations through rigorous simulation. No human in the loop during testing. Every decision is automatic, every result is logged, every piece of reasoning is preserved. This is the primary engine. Everything else exists to translate what the Sandbox produces.

**Mission Control (The Sentinel Dashboard)** — where validated theses watch the live market and surface alerts when something material has changed. The Sentinel is not a signal generator. It is a thesis monitor. It remains silent until reality challenges your reasoning — then it tells you exactly what changed and why it matters.

### 1.3 The Core Loop

```
Thesis → Build → Stress-Test → Iterate → Trust → Monitor → Alert → Decide → Learn
```

| Stage | What Happens | Who Does It |
|---|---|---|
| Thesis | Articulate why you own this asset and what would change your mind | User + Claude 4.6 |
| Build | Compose a pipeline from the engine library to test the thesis | User (template or scratch) |
| Stress-Test | Run historical and scenario simulations against the thesis | Agents (fully autonomous) |
| Iterate | Analyze failures, propose specific improvements with expected deltas | Agents propose, User approves |
| Trust | Configuration passes promotion criteria, thesis is validated | MLflow verdict |
| Monitor | Live Sentinel watches for thesis-relevant events in the market | Agents |
| Alert | Sentinel fires only when a deterministic thesis event occurs | Agents |
| Decide | User reads the full audit trail, decides to hold, exit, or re-evaluate | Human always |
| Learn | Mirror Portfolio tracks counterfactual — what happened when you overruled the Sentinel | Platform |

### 1.4 The Belief-Testing Machine Framing

This is the core mental model and it should be understood before anything else in this document.

Every other retail platform treats a bad outcome as noise — the position lost money, move on. Aegis AI treats every outcome, good or bad, as **structured data about the quality of the reasoning that produced it.** The Sandbox doesn't just run backtests. It answers the question: "Given everything I believed about this asset, does the historical evidence support that belief — and if not, exactly where does the belief break down?"

That reframe changes everything:

- A failed backtest is not a dead end. It is a diagnostic. The Improvement Analyzer Agent tells you precisely which assumption was wrong and what the data actually shows.
- A passed backtest is not a guarantee. It is evidence that your reasoning survived a specific historical test. The live paper trading phase tests whether it survives the present.
- A declined Sentinel alert is not a neutral event. The Mirror Portfolio tracks what happened after you overruled the system, building a personal record of when your judgment adds alpha versus when it detracts.

Over time, a user who engages seriously with the platform doesn't just get better signals. They develop genuine market judgment — the kind that compounds across years and isn't dependent on any single tool.

---

## Part II: The Layered User Model

This is the section that most clearly distinguishes v4 from v3. v3 implicitly assumed a single user type: a technically sophisticated quant who wanted an institutional-grade research environment. That user exists but is small in number and already served.

v4 explicitly serves three user types on the same infrastructure with different entry points. This is the Databricks model.

### 2.1 The Three User Tiers

**Tier 1 — The Conviction Investor**

Who they are: Retail investors who hold positions but panic-sell during volatility, chase performance, or lack the framework to distinguish "price went down" from "my thesis is broken." They may have $10k–$200k invested and a general sense of what they own. They do not read 10-Qs and have no interest in configuring VPIN thresholds.

What they need: A thesis-construction tool that helps them articulate why they own something, and a monitoring system that remains silent until something materially relevant to that thesis changes. They need the platform to build conviction for them, then protect that conviction from their own behavioral biases.

What they see: The New Sentinel Wizard, default templates, the Thesis Breach Alert, the Mirror Portfolio counterfactual. The Sandbox exists for them as a one-click stress test, not a configuration environment.

What they don't see: Raw VPIN scores, HMM state probabilities, Optuna sweep results, agent architecture. These live under the Glass Box if they want to look — but they are never surfaced by default.

**Tier 2 — The Curious Tinkerer**

Who they are: The WallStreetBets adjacent retail investor. They have a theory — insider buying predicts 6-month returns, congressional trading disclosures have alpha, earnings revisions lead price — and they want to know if it actually holds up. They are comfortable with data, comfortable with uncertainty, and skeptical of black boxes. They will open the Sandbox.

What they need: A rigorous, transparent testing environment where they can take their theory, build a pipeline around it, run it against real history with real slippage simulation, and see an honest answer. They need the MLflow Arena to compare their results. They need the Improvement Analyzer to tell them where their theory breaks down.

What they see: Everything in Tier 1, plus full Sandbox access, the MLflow Arena leaderboard, the Config Diff Viewer, the Improvement Analyzer proposals. They can access the Plugin Library to add VPIN or HMM context if they understand what those signals mean.

What they don't see: Raw model internals, LangGraph architecture. The Glass Box is available but presented in plain language first.

**Tier 3 — The Serious Retail Quant**

Who they are: A small but extremely high-engagement user. Probably has a finance background or serious self-teaching history. Has used QuantConnect or Alpaca before. Wants full engine access, custom connectors, custom agents, VPIN and HMM in the core pipeline if they choose. Will write their own LangGraph nodes.

What they need: The full platform with no guardrails removed. Custom Engine registration, the complete Plugin Library, the ability to override promotion criteria, access to raw MLflow artifacts, custom agent YAML specs.

What they see: Everything. The full Engine Library, all plugins enabled, raw metric outputs, full agent trace replay, configuration JSON editor.

### 2.2 Why All Three Users Share the Same Infrastructure

The temptation when designing for multiple user types is to build separate products that share a brand. That is the wrong architecture for two reasons:

First, users graduate upward. A Conviction Investor who uses the platform seriously for six months becomes a Curious Tinkerer. A Tinkerer who goes deep becomes a Retail Quant. If the platform is architected in tiers, graduating users encounter friction — they have to switch tools. If it is architected as a single system with progressive disclosure, graduation is natural and the platform becomes more valuable as users develop.

Second, the credibility of the simpler tiers depends on the sophistication of the deeper ones. A Conviction Investor who knows they could open the Glass Box and see the full LangGraph trace trusts the thesis summary more — even if they never actually look. Transparency at depth creates trust at the surface. This is the Databricks principle applied to retail investing.

---

## Part III: System Architecture

### 3.1 Architecture Overview (7 Layers)

```
┌──────────────────────────────────────────────────────────────┐
│  Layer 7: Frontend (React + Vite)                            │
│  Dashboard | Engine Library | Sandbox | Arena | Alerts       │
├──────────────────────────────────────────────────────────────┤
│  Layer 6: API Layer (FastAPI)                                │
│  REST endpoints + WebSocket streaming                        │
├──────────────────────────────────────────────────────────────┤
│  Layer 5: Orchestration (LangGraph)                          │
│  Supervisor + Sub-agents + Improvement Analyzer              │
├──────────────────────────────────────────────────────────────┤
│  Layer 4: Engine Layer                                       │
│  Data Engine | Fundamental Engine | Analyst Engine | Research│
│  + Plugin Layer (VPIN, HMM, Intraday — optional, off by default)│
├──────────────────────────────────────────────────────────────┤
│  Layer 3: Model Routing Layer (NEW)                          │
│  Claude 4.6 API (thesis, breach alerts) |                    │
│  Qwen Local VM (agent loop, MLflow analysis, proposals)      │
├──────────────────────────────────────────────────────────────┤
│  Layer 2: Storage Layer                                      │
│  MLflow (SQLite) | ChromaDB | Episodic Memory | JSON         │
├──────────────────────────────────────────────────────────────┤
│  Layer 1: Data Sources                                       │
│  YFinance | FRED | SEC EDGAR | Finnhub | Congressional |     │
│  Alpaca (plugin) | FinBERT                                   │
└──────────────────────────────────────────────────────────────┘
```

### 3.2 Complete Data Flow

```
External Sources (YFinance, FRED, SEC EDGAR, Finnhub, Congressional Disclosures)
        │
        ▼
DataEngine — ingestion, cleaning, normalization
        │  (attached: point-in-time timestamps on ALL records)
        ├──► FinBERT → Sentiment Scores
        ├──► SEC Parser → Chunked Filing Text → ChromaDB
        ├──► Congressional Disclosure Parser → Insider Signal Layer
        └──► Raw OHLCV + Macro Data + Fundamental Data
        │
        ▼
Fundamental Engine — primary signal generation (value/conviction-oriented)
        ├──► Earnings Revision Tracker → Forward estimate momentum
        ├──► Insider Activity Monitor → Form 4 accumulation patterns
        ├──► Thesis Parameter Extractor → Tracks specific thesis KPIs
        └──► Macro Overlay → FRED-driven regime context
        │
        ├── [OPTIONAL] Plugin Layer — loaded only if enabled in config
        │       ├──► HMM → Market Regime (Bull/Bear/Volatile)
        │       ├──► VPIN → Order Flow Toxicity
        │       └──► Chronos → Probabilistic Price Forecast
        │
        ▼ (if thesis breach gate crossed OR signal gate crossed)
AnalystEngine (LangGraph) — routed through Model Router
        ├──► Research Agent [Qwen local] — queries ChromaDB for filing evidence
        ├──► Sentiment Agent [Qwen local] — synthesizes FinBERT + news
        ├──► Risk Agent [Qwen local] — validates against configured constraints
        └──► Supervisor [Claude 4.6] — final thesis synthesis + breach determination
        │
        ▼
Output:
  [Sandbox Mode] → Scenario results → Plain-language verdict → MLflow logging
  [Live Mode] → Thesis Breach Alert → User Hold/Re-evaluate → Mirror Portfolio
```

### 3.3 The Model Routing Layer (New in v4)

This layer is the practical implementation of a key architectural decision made during platform design: not all reasoning tasks are equal, and routing them to appropriate models is both a cost and quality decision.

**Claude 4.6 (API) handles:**
- Initial thesis generation from user inputs and SEC filing context
- Thesis Breach Alert reasoning — the high-stakes moment when the Sentinel fires
- Final Supervisor synthesis when a Sentinel recommendation is generated
- Any output the user makes a real financial decision against

Rationale: These are the highest-stakes outputs the platform produces. They require genuine reasoning quality, nuanced language, and the ability to synthesize complex financial context into something a retail investor can trust and act on. This is the one place where frontier model quality is directly tied to product quality and user trust.

**Qwen (local, cloud VM) handles:**
- Agent improvement loop analysis — reading MLflow traces, generating proposals
- Quick iteration run evaluation — directional feedback on parameter changes
- Research Agent ChromaDB queries and evidence synthesis
- Sentiment Agent FinBERT aggregation
- Risk Agent constraint validation
- All structured reasoning tasks on well-defined inputs

Rationale: These tasks are largely structured reasoning on constrained inputs. "Here are metrics from run A and run B, what changed and why does it matter?" does not require Claude 4.6. The quality difference is negligible on these tasks; the cost difference is enormous.

**Routing Layer Design Principle:**

The routing layer must be built as explicit logic, not hardcoded assignments. As model quality evolves, as cost structures change, and as task complexity is better understood through real usage, the boundary should be adjustable without architectural surgery. The routing layer should log which model handled which task type, enabling future A/B quality analysis on task-model combinations.

**Critical routing rule: Thesis breach alerts stay on Claude 4.6 regardless of cost pressure.** A thesis breach alert is the moment a user is most emotionally vulnerable and most likely to make a consequential decision. A poorly reasoned breach alert — one that falsely signals thesis failure or misses the nuance of why a metric moved — is worse than no alert. This is not a place to optimize for cost.

**Cloud VM deployment:**

Qwen 14B is the recommended local model. It handles complex multi-step agent reasoning adequately and runs comfortably on A100-class GPU instances. Qwen 7B is acceptable for the simplest structured tasks (Risk Agent constraint checking) but shows quality degradation on Improvement Analyzer proposals, which require genuine causal reasoning about why a backtest failed.

Inference throughput in the Quick Iteration Run is a UX-critical moment — users are in an active iteration loop and waiting 15+ minutes for directional feedback on a parameter change destroys the feel of the product. GPU sizing for the cloud VM should be validated against Quick Iteration Run latency, not just cost per token. Target: Quick Iteration Run completes within 3–5 minutes end-to-end.

---

## Part IV: The Engine Library

### 4.1 Philosophy of the Engine Library in v4

In v3, the Engine Library was a catalog of tools organized by technical function. In v4, it is organized by *what question the tool answers*. This distinction matters because it changes how tools are presented to users across all three tiers, and because it forces architectural clarity about what each engine is actually for.

The fundamental question every engine must answer is: **does this tool help test a thesis, or does it help optimize a parameter?** Thesis-testing tools belong in the default pipeline. Parameter-optimization tools belong in the Plugin Library. This is the organizing principle.

### 4.2 Data Engine

**Purpose:** Ingests, cleans, normalizes, and annotates all raw market and alternative data. Enforces point-in-time discipline across all sources. This engine has not changed in philosophy from v3, but its connector priority has shifted.

**Point-in-Time Discipline Rule:** Every data record carries two timestamps:
- `event_ts`: When the underlying event occurred
- `public_disclosure_ts`: When the data became publicly available

The simulation loop uses **only** `public_disclosure_ts` to determine when data becomes visible to the agent. This prevents lookahead bias across all data types. This is non-negotiable and applies to every connector including third-party integrations.

| Connector | Data Type | Latency | Point-in-Time Field | Priority in v4 |
|---|---|---|---|---|
| YFinance | OHLCV, fundamentals, options chain | Daily/realtime | `market_close_ts` | Core |
| FRED | CPI, Fed rate, M2, unemployment, yield curve | Monthly/weekly | `release_ts` | Core |
| SEC EDGAR | 10-K, 10-Q, 8-K, Form 4 insider filings | Event-driven | `edgar_accession_ts` | Core |
| Finnhub | News articles, earnings calendar, revisions | Realtime | `published_ts` | Core |
| Congressional | Politician trade disclosures (STOCK Act) | 45-day delay | `disclosure_filing_ts` | Core |
| Alpaca | Intraday tick/bar data | Sub-minute | `bar_ts` | Plugin only |
| FinBERT | Sentiment scoring of text | Applied at ingest | Inherits from source | Core |

Note on Congressional data: This is elevated to a core connector in v4. Congressional trading disclosures, enforced to use the 45-day `disclosure_filing_ts` rather than the `trade_date`, represent a slow-moving, high-conviction signal that is directly relevant to a long-horizon thesis. This is exactly the kind of alternative data the platform's value orientation supports.


### 4.2.1 Connector Health Layer (New in v4.1)

**The Silent Failure Problem**

Point-in-time discipline and connector health are not the same problem. The platform already enforces that data is only used after its `public_disclosure_ts`. But there is a second failure mode that discipline does not address: what happens when a connector stops delivering data entirely?

If YFinance returns stale data, EDGAR goes down, or Finnhub rate-limits during a busy period, the Thesis Parameter Monitor continues running against an increasingly outdated data snapshot. The Sentinel appears healthy on the dashboard — no alerts, no errors — while monitoring nothing. A Sentinel that appears operational while its data feed is stale is strictly worse than a broken one, because it produces false confidence.

**The Fix: Connector Health Protocol**

Every connector must expose a `last_successful_fetch_ts` — the timestamp of its most recent successful data retrieval. The Data Engine evaluates health status against configurable staleness thresholds that reflect each connector's expected update cadence:

```python
HEALTH_THRESHOLDS = {
    "yfinance":      {"warn": timedelta(hours=25),  "offline": timedelta(hours=48)},
    "fred":          {"warn": timedelta(days=8),    "offline": timedelta(days=14)},
    "sec_edgar":     {"warn": timedelta(hours=72),  "offline": timedelta(days=7)},
    "finnhub":       {"warn": timedelta(hours=25),  "offline": timedelta(hours=48)},
    "congressional": {"warn": timedelta(days=8),    "offline": timedelta(days=14)},
}
```

**Sentinel Health States**

Each live Sentinel is assigned a health status derived from the worst-case health of its configured connectors:

| Status | Meaning | Dashboard Display |
|---|---|---|
| `MONITORING` | All connectors healthy, last fetch within warn threshold | Green — operating normally |
| `DEGRADED` | One or more connectors stale but not offline | Amber — monitoring may be incomplete, named connectors shown |
| `OFFLINE` | One or more critical connectors offline | Red — Sentinel is not monitoring, user notification sent |

**Dashboard Behavior**

The dashboard must never show a Sentinel as silently healthy when its data feeds are stale. Specific rules:

- `DEGRADED` state shows which connectors are stale and the last successful fetch timestamp for each
- `OFFLINE` state suspends Thesis Breach Alert generation entirely — a thesis breach detected on stale data is worse than no detection
- Sentinel health is shown prominently on the main dashboard card, not buried in a settings panel
- Users receive a notification when any Sentinel transitions to `DEGRADED` or `OFFLINE`

**The Asymmetry Rule**

The system must be biased toward false alarms about connector health rather than silent failures. An amber warning that turns out to be a temporary API hiccup is a minor annoyance. A Sentinel silently running on 3-week-old data while the user believes their thesis is being monitored is a product integrity failure. When in doubt, downgrade the health status.

**Implementation Note for Current Environment**

At 16GB on a Mac, the health check is a lightweight scheduled task — no model involvement. Run a `check_connector_health()` coroutine on a configurable interval (default: every 4 hours for daily connectors, every 30 minutes for real-time connectors). FastAPI exposes a `/health` endpoint per connector. The Sentinel State Manager reads connector health before evaluating whether to surface any Thesis Breach Alert.

### 4.3 Fundamental Engine (Replaces the default Quant Engine role)

**Purpose:** The primary signal generation layer for the default pipeline. Transforms raw data into thesis-relevant fundamental and behavioral signals. This is new in v4 and replaces VPIN/HMM as the default analytical layer.

The Fundamental Engine answers the question: **is the thesis you articulated still supported by the data available today?**

**Earnings Revision Tracker**
- Monitors sell-side EPS and revenue estimate revisions for configured tickers
- Output: `{direction: "up", magnitude: 0.04, analyst_count: 12, revision_momentum: "accelerating"}`
- Thesis relevance: If a thesis was built on "cloud revenue grows 15% annually," an earnings revision showing a consensus cut to 11% is a deterministic thesis event
- MLflow tracks: which revision magnitude thresholds have historically predicted forward returns for different asset classes

**Insider Activity Monitor**
- Tracks SEC Form 4 filings for corporate insider buying/selling patterns using `edgar_accession_ts`
- Output: `{insider_type: "CEO", transaction: "BUY", shares: 50000, value_usd: 2400000, cluster_buy: true}`
- Thesis relevance: Cluster insider buying (multiple insiders buying within a short window) is a slow-moving, high-conviction signal. It doesn't tell you when to buy — it tells you whether the people who know the company best are aligned with your thesis
- Enforces point-in-time strictly — no using trade date, only disclosure date

**Thesis Parameter Monitor**
- Tracks the specific quantitative claims embedded in the thesis
- A thesis is parsed at construction time into a set of monitorable parameters: `"cloud_revenue_growth_rate": {target: 0.15, warn_below: 0.12, breach_below: 0.10}`
- At each 10-Q release, the agent extracts the relevant metric and compares to the threshold
- This is the primary trigger for Thesis Breach Alerts

**Macro Overlay**
- FRED-driven context layer: yield curve shape, credit spreads, Fed rate trajectory
- Output: `{macro_regime: "tightening", recession_probability_3m: 0.18, credit_spread_trend: "widening"}`
- Not a trade signal. A contextual layer that qualifies thesis confidence: "Your thesis holds, but macro conditions have deteriorated since construction. Confidence adjusted from 87% to 71%."

### 4.4 Plugin Library (Formerly the default Quant Engine)

**Philosophy:** The Plugin Library contains powerful tools that are appropriate for users who understand what they are measuring and why. These tools are never surfaced as defaults, never shown as headline metrics, and never generate independent signals. They exist as context modifiers — additional lenses that can inform thesis re-evaluation for users who want them.

This is not a downgrade of these tools. VPIN and HMM are genuinely sophisticated instruments. The issue in v3 was not that they were included — it was that they were shown to users who lacked the context to interpret them, producing anxiety rather than insight. In the Plugin Library, they are available to users who want them, with honest plain-language descriptions.

**Activation rule: Plugins can inform thesis alerts. They cannot generate independent signals.** A VPIN spike can add a context line to a thesis breach alert: "Additionally, unusual institutional selling pressure was detected in the past 48 hours." It cannot fire an alert on its own.

**Available Plugins:**

HMM — Market Regime Detection
- Detects market regime: Bull, Bear, High Volatility
- Config: `n_components` (2-5 states), `training_window_days`, `covariance_type`
- Output: `{regime: "Bull", confidence: 0.82}`
- Appropriate for: Users running swing strategies who want macro regime context
- Not appropriate for: Conviction investors monitoring a 2-year thesis
- Plain-language UI label: "Market Regime Monitor — shows whether the broader market is trending up, down, or choppy. Useful for timing entries. Not relevant if you're holding for 12+ months."

VPIN — Order Flow Toxicity
- Measures the probability that recent trading is informed (institutional/smart money flow)
- Config: `toxicity_threshold` (0.0–1.0), `bucket_size`
- Output: `{vpin_score: 0.14, is_toxic: false}`
- Appropriate for: Tinkerers and Quants who want microstructure context on entries
- Not appropriate for: Long-term conviction investors
- Plain-language UI label: "Institutional Flow Monitor — detects unusual selling pressure from large institutional players. Can provide context before earnings or major events. Advanced tool — enable only if you understand order flow."
- UI rule: Never display raw VPIN score in default view. Display as: "Institutional flow: Normal" / "Institutional flow: Elevated — exercise caution"

Chronos Forecaster
- Probabilistic price forecasting
- Config: `horizon_days`, `model_size`
- Output: `{forecast_low: 185.20, forecast_mid: 191.40, forecast_high: 197.80}`
- Appropriate for: All tiers as an optional range context tool
- Plain-language UI label: "Price Range Forecast — AI model's estimated price range over the next N days. Not a prediction. Use as context, not as a signal."

Alpaca Intraday
- Sub-minute tick data for intraday analysis
- Available only when Day Trader template is active or explicitly enabled
- Plain-language UI label: "Intraday Data — high-frequency market data. Only relevant for day trading strategies. Enable only if you're trading intraday."

**Plugin default states:**

| Plugin | Default | Enabled by template |
|---|---|---|
| HMM | OFF | Tech Breakout, Day Trader, Macro Rotation |
| VPIN | OFF | Tech Breakout (as context), Day Trader |
| Chronos | OFF | Any (user choice) |
| Alpaca Intraday | OFF | Day Trader only |

### 4.5 Analyst Engine (LangGraph)

**Purpose:** The reasoning layer. Takes fundamental signals and data context, synthesizes a human-readable thesis or breach analysis, and produces a recommendation. In v4, the Supervisor is always Claude 4.6. Sub-agents run on Qwen locally.

The key behavioral change from v3: the Analyst Engine's primary output is **thesis construction and thesis breach reasoning**, not trade signal generation. The architecture is the same; the prompting, context, and output format are oriented around conviction building rather than buy/sell decisions.

```
Supervisor Agent [Claude 4.6]
├──► Research Agent [Qwen local]
│      └── Queries ChromaDB for relevant 10-K/10-Q chunks
│          "What does the most recent 10-Q say about cloud revenue trends?"
│          "Has management guidance on margin expansion changed in the last 2 quarters?"
├──► Sentiment Agent [Qwen local]
│      └── Synthesizes FinBERT scores + news into a thesis-relevant narrative
│          "3 of 5 recent articles cite supply chain improvement — supports thesis"
├──► Risk Agent [Qwen local]
│      └── Validates thesis against hard constraints and portfolio parameters
│          "Position within drawdown budget ✓. Macro regime within thesis assumptions ✓."
└──► Supervisor [Claude 4.6]
       └── Synthesizes into: thesis construction, breach determination, or confidence update
```

**Supervisor Decision Logic:**
- If Risk Agent VETOES → output is HOLD regardless of other agents, with explanation
- Thesis construction mode: Supervisor synthesizes all sub-agent evidence into a structured investment thesis with explicit falsification criteria
- Thesis breach mode: Supervisor determines whether a flagged metric event constitutes a genuine thesis breach or is within-range noise

**Episodic Memory:** The Supervisor tracks its own past thesis constructions and their subsequent outcomes. "I constructed a thesis for AAPL on Feb 12 citing 14% YoY services growth. The next 10-Q showed 16%. Thesis validated." This builds a calibration record that informs future confidence estimates without retraining.

### 4.6 Research Engine

Same as v3. This engine is unchanged and is a core strength of the platform.

| Component | Description |
|---|---|
| SEC Filing Loader | Downloads and parses 10-K/10-Q/8-K/Form 4 into chunks |
| Earnings Call Parser | Extracts forward guidance, risk factor statements, management tone |
| ChromaDB Vector Store | Embeds and indexes all document chunks for semantic search |
| Episodic Memory Store | Stores agent past theses + outcomes for self-reflection |

**Point-in-time RAG:** When the Research Agent queries ChromaDB, it retrieves only chunks with `public_disclosure_ts <= simulation_date`. A 10-Q that was filed on March 15 is invisible to a simulation running on March 14. This applies to the live Sentinel as well — the agent only knows what was publicly available at the moment of analysis.

---

## Part V: The Sandbox

### 5.1 Philosophy

The Sandbox is not a feature attached to the platform. The Sandbox is the platform. Everything else — the Engine Library, the Sentinel Dashboard, the Thesis Breach Alerts — exists to translate Sandbox-validated results into actionable intelligence.

**In v3, the Sandbox was an optimization engine.** It ran parameter sweeps, generated Sharpe ratios, and promoted configurations that cleared performance gates. That framing is not wrong — it is still part of what the Sandbox does. But it is incomplete.

**In v4, the Sandbox is a belief-testing machine.** Its primary output is not "this configuration has Sharpe 1.14." Its primary output is "your belief that insider buying precedes 6-month outperformance held up in 7 of 9 historical analogs, broke down during rising rate environments, and here is exactly why." The metrics are evidence for or against a thesis. The thesis is the unit of analysis, not the configuration.

This reframe has concrete architectural implications:
- Every Sandbox run must produce a plain-language summary alongside raw metrics. Users should never be required to interpret Sharpe ratios to understand what the Sandbox is telling them.
- Scenario stress tests are a first-class run type alongside historical backtests, not an afterthought.
- MLflow logs not just performance metrics but the *thesis* that was being tested, enabling future comparison of thesis quality rather than just parameter quality.

### 5.2 Three Run Types (New in v4 — Scenario Added)

**Quick Iteration Run (minutes)**
- Purpose: Rapid directional feedback during the Agent Improvement Loop
- Scope: 90 days of history, single ticker, Phase 1 (fundamental signals only, no LLM)
- Use: Agent proposes "adjust earnings revision threshold from 3% to 5%" → user approves → Quick Run validates direction in 2–3 minutes
- MLflow tag: `run_type=quick_iteration`

**Full Production Backtest (4–12 hours)**
- Purpose: Canonical validation before Sentinel promotion
- Scope: Full configured history, all tickers, both phases (fundamental + event-gated LLM)
- Phase 1: Vectorized fundamental signal pass with Optuna sweeps → identifies thesis breach events
- Phase 2: LangGraph invoked on gated events only (typically 10–20% of trading days)
- Slippage injection applied to every simulated trade
- MLflow tag: `run_type=production`

**Scenario Stress Test (New in v4)**
- Purpose: Test whether a thesis survives specific adverse conditions
- Scope: Selected historical analog periods or constructed scenario parameters
- Examples: "Run my MSFT thesis through the 2022 rate hike cycle," "Test my cloud revenue thesis if growth drops to 8% for 3 consecutive quarters," "Simulate a 30% drawdown in your entry year"
- Output: Thesis survival rate, which scenarios broke the thesis, what the breaking point was
- This is the most powerful tool for Conviction Investors — it does not require understanding backtesting to be useful. "Your thesis survived 4 of 5 recessions since 2000. It broke during 2008 because [reason]. Does that change your conviction?"
- MLflow tag: `run_type=scenario`

### 5.3 The Simulation Loop

```python
for date in trading_calendar[start_date:end_date]:
    # 1. Fetch point-in-time data snapshot
    data_snapshot = data_engine.get_snapshot(
        tickers=config.asset_universe.tickers,
        as_of=date,  # uses public_disclosure_ts filtering strictly
    )

    # 2. Run Fundamental Engine
    fundamental_signals = fundamental_engine.compute(data_snapshot, config.fundamental_engine)

    # 3. Run enabled plugins (if any)
    plugin_signals = plugin_layer.compute(data_snapshot, config.plugins)  # empty if no plugins

    # 4. Thesis Gate check — did something materially relevant happen?
    for ticker in config.asset_universe.tickers:
        signals = {**fundamental_signals[ticker], **plugin_signals.get(ticker, {})}

        thesis_event = thesis_monitor.check_breach(
            signals,
            config.thesis_parameters[ticker],
            data_snapshot
        )

        if thesis_event.is_material:
            # 5. Only now invoke the LLM (Production run only)
            if run_type == "production":
                analysis = analyst_engine.evaluate(
                    ticker, data_snapshot, signals, thesis_event,
                    model_router=model_router  # routes sub-agents to Qwen, Supervisor to Claude
                )
            else:
                # Quick run: use fundamental signal as proxy, no LLM
                analysis = derive_from_fundamentals(signals)

        # 6. Execute in simulated portfolio
        portfolio.execute(analysis, date, config.sandbox.slippage_bps)

    # 7. Track portfolio state
    nav_history.append(portfolio.nav)

# 8. Compute performance metrics
metrics = compute_metrics(nav_history, config.asset_universe.benchmark)

# 9. Generate plain-language verdict (Qwen local)
plain_verdict = improvement_analyzer.generate_verdict(metrics, config.thesis)

# 10. Log everything to MLflow
mlflow.log_run(config, metrics, plain_verdict, thesis_traces)
```

### 5.4 Slippage and Market Impact Model

Unchanged from v3 in mechanics. Emphasized here because it is a foundational integrity rule.

| Cost Component | Default | Description |
|---|---|---|
| Bid-ask spread | 10 bps (0.10%) | Half-spread applied per side |
| Market impact | Linear, 5 bps/$10k | Larger positions move price against you |
| Execution latency | 1 bar (1 day) | Orders fill at next bar open, not same-bar close |

The platform always displays gross return vs. net return after costs side by side. A strategy that looks compelling on gross return and mediocre on net return is a strategy that depends on impossible execution. Users should understand this before promoting anything to a Sentinel.

### 5.5 Sandbox Outputs: The Plain Language Rule

Every Sandbox run produces two parallel output layers:

**Layer 1 — Raw Metrics (for Tier 2/3 users and Glass Box)**
Standard quantitative performance metrics: Sharpe, Sortino, CAGR, Max Drawdown, Win Rate, Alpha, Beta, Signal Gate Rate, LLM Alpha Contribution, Slippage Drag. These are logged to MLflow in full detail.

**Layer 2 — Plain Language Verdict (for all users, required)**
Produced by the Improvement Analyzer using Qwen locally. Not a marketing summary. An honest, specific interpretation of what the metrics mean for the thesis being tested.

Example of what this should look like:

> "Your thesis that insider buying predicts 6-month outperformance held up historically, but with important qualifiers. In bull market conditions, the strategy generated meaningful alpha over SPY. In rising rate environments (2022, 2018), the same signals preceded underperformance, suggesting that macro regime matters as much as insider activity for this type of signal. Transaction costs consumed a significant portion of gross returns — the strategy works best when you are patient and let positions run rather than trading frequently. The Improvement Analyzer has flagged three specific changes that historical data suggests would improve performance."

What this should never look like:

> "Sharpe ratio: 1.14. Alpha: +5.8%. Drawdown: -12.3%. Configuration outperformed benchmark."

The second version is not wrong. It is useless to the Conviction Investor and only marginally useful to the Tinkerer. The plain language verdict is what transforms a good quant backend into a platform that actually builds investor judgment.

### 5.6 The Agent Improvement Loop

This is a core differentiator and is preserved from v3. The change in v4 is that proposals are framed around **thesis quality**, not just parameter optimization.

```
Production Backtest or Scenario Stress Test Completes
           │
           ▼
Improvement Analyzer [Qwen local] reads:
  - Trade-by-trade P&L log against thesis event triggers
  - Which thesis parameters generated the most accurate breach signals?
  - Which scenarios broke the thesis and why?
  - Did the LLM add alpha over the fundamental-only baseline?
  - Per-parameter Optuna surface (which ranges produced better thesis survival?)
           │
           ▼
Generates structured proposals (two types):

  Type 1 — Parameter proposals:
  {
    "proposal_id": "prop-42",
    "target_param": "fundamental_engine.earnings_revision.threshold",
    "current_value": 0.03,
    "proposed_value": 0.05,
    "rationale": "3% revision threshold generated 12 false thesis alerts in stable
                  periods. Raising to 5% reduces false alerts by ~8 while retaining
                  all genuinely material revision events.",
    "expected_delta": {"thesis_precision": "+0.18", "false_alert_reduction": "67%"},
    "risk_of_change": "May delay detection of early-stage deterioration."
  }

  Type 2 — Thesis insight proposals:
  {
    "proposal_id": "prop-43",
    "insight_type": "thesis_vulnerability",
    "finding": "This thesis has a hidden macro dependency that is not stated
                 in the original thesis construction. Performance degrades
                 significantly when the 10-year yield rises more than 75bps
                 over any 6-month window. Consider adding this as an explicit
                 thesis falsification criterion.",
    "supporting_evidence": "Backtest performance in 2018 and 2022 rate cycles."
  }
           │
           ▼
User Inbox: APPROVE ✓ | REJECT ✗ | MODIFY and APPROVE →
           │
           ▼
Quick Iteration Run validates direction (2–3 minutes)
           │
           ▼
If directionally correct → Full Production Backtest confirms delta
           │
           ▼
Config version incremented (v3.1 → v3.2), new MLflow run logged
```

---

## Part VI: MLflow Arena

### 6.1 MLflow as Reasoning History

In v3, MLflow was "the court of truth" — a performance ledger. That framing is correct but incomplete. In v4, MLflow serves a second equally important function: **the institutional memory of a user's evolving judgment.**

Every run logs not just performance metrics but the thesis being tested, the agent's plain-language verdict, the specific proposals that were approved or rejected, and the expected vs. actual delta of each change. Over months of use, this becomes something no retail investor has ever had: a structured record of how their thinking about markets has evolved, which intuitions have held up, and which have been falsified by evidence.

This is the compounding asset the platform creates. Portfolio returns compound with capital. Reasoning quality compounds with time. MLflow is the ledger for both.

### 6.2 What Gets Logged

Every Sandbox run (quick, production, or scenario) logs to MLflow:

**Parameters (the configuration fingerprint):**
- Complete `config.json` including all engine settings and plugin states
- Thesis text as constructed at run time
- Thesis parameter thresholds (the monitorable claims)

**Metrics (the performance verdict):**
- All quantitative metrics from §5.4
- Per-ticker breakdown (which positions drove alpha?)
- Thesis breach accuracy (what % of alerts were followed by genuine thesis events?)
- LLM Alpha Contribution (Sharpe full vs. Sharpe fundamental-only baseline)

**Artifacts (the audit trail):**
- `thesis_trace.jsonl` — every thesis event with full agent reasoning
- `plain_verdict.md` — the Improvement Analyzer's plain-language summary
- `portfolio_nav.csv` — daily NAV history
- `config.json` — the exact configuration
- `scenario_results.json` (if scenario run) — survival rates per scenario
- `optuna_study.pkl` — parameter sweep surface

### 6.3 MLflow Arena Views

**Leaderboard**
All production runs ranked by any metric. Filterable by `config_id`, `template_base`, `trading_style`, `asset_universe`. "Promote" button appears next to runs passing all promotion criteria.

**Config Diff Viewer**
Select any two runs → git-style diff of configurations + performance delta. Example: `earnings_revision_threshold: 0.03 → 0.05 | Thesis Precision: 0.61 → 0.79 (+0.18)`

**Thesis Evolution View (New in v4)**
Shows a user's thesis for a specific ticker across all runs. How has the thesis changed? Which falsification criteria were added or removed? What did the agent learn about this position over time? This is the "judgment ledger" view — the most important long-term value driver of the platform.

**Parallel Coordinate Plot**
Each line = one MLflow run. Axes = key parameters + Sharpe. Reveals which parameter regions produce high-performance configurations.

**Scenario Survival Matrix (New in v4)**
For scenario-run results: a matrix showing each tested scenario against each configuration, color-coded by thesis survival rate. Makes it immediately visual which configurations are fragile vs. robust.

**LLM vs. Fundamental-Only Comparison**
Compares Phase 1 Sharpe (fundamental-only baseline) vs. Phase 2 Sharpe (with LLM). If LLM Alpha Contribution < 0, suggests disabling Analyst Engine for this configuration.

### 6.4 Promotion Gate

User-configurable criteria that a Production Backtest must meet before a configuration can be promoted to a live Sentinel:

```json
"promotion_criteria": {
  "sharpe_min": 1.0,
  "alpha_min_pct": 3.0,
  "max_drawdown_pct": 15.0,
  "win_rate_min": 0.52,
  "backtest_months_min": 6,
  "min_thesis_events": 10,
  "thesis_breach_precision_min": 0.65,
  "scenario_survival_rate_min": 0.70
}
```

Note: `thesis_breach_precision_min` and `scenario_survival_rate_min` are new in v4. A configuration can have excellent Sharpe but generate thesis breach alerts that are mostly noise. Those configurations should not be promoted — they will generate frequent false alarms that erode user trust and drive behavioral overtrading.

---

## Part VII: The Sentinel

### 7.1 The Silent Sentinel Principle

This is the most significant behavioral change from v3 to v4 and it must be understood as a product philosophy, not just a feature change.

v3's Sentinel generated Signal Cards whenever the signal gate was crossed. A well-performing swing strategy might generate 3–5 Signal Cards per week. Each card presented a BUY or HOLD recommendation with a full quant anchor panel and two large buttons: ACCEPT or DECLINE.

The problem is not that this is technically wrong. The problem is that it recreates the exact behavioral dynamic the platform is meant to solve. A user receiving frequent, beautifully designed Signal Cards with authoritative quant metrics will develop one of two unhealthy patterns: they either follow every signal mechanically (replacing judgment with dependence) or they start second-guessing and overriding signals emotionally (the same fear-driven behavior they had before). Neither builds conviction.

**The Silent Sentinel fires only when something has materially changed in the thesis.** Between thesis events, it is silent. Complete silence. No weekly check-ins, no "here's the latest quant read," no low-confidence alerts. The user's position is running. The thesis is being monitored. If nothing changes, nothing is communicated.

This is a harder product to build emotionally — users will feel anxious about the silence. This anxiety should be addressed in onboarding: the silence means the thesis is intact. You set your conviction level during Sandbox validation. Trust it unless the Sentinel tells you otherwise.

### 7.2 What Triggers a Thesis Breach Alert

A Thesis Breach Alert fires when a deterministic thesis parameter crosses a configured threshold. These thresholds are set during thesis construction and must be explicit — vague theses ("this company will grow") cannot be monitored.

**Example thesis parameter triggers:**
- `cloud_revenue_growth_rate` drops below 12% (warn) or 10% (breach)
- `gross_margin` contracts more than 3 percentage points in a single quarter
- `insider_buying_cluster` reverses — CEO sells >10% of holdings within 90 days of a cluster buy signal
- `earnings_revision_direction` turns negative for 2 consecutive quarters
- Macro overlay: yield curve inverts AND credit spreads widen >50bps within 30 days (if configured as thesis dependency)
- Plugin trigger (if enabled): VPIN crosses toxicity threshold for 5 consecutive sessions AND HMM shifts to Volatile regime

### 7.3 The Thesis Breach Alert (Replaces the Signal Card)

```
┌──────────────────────────────────────────────────────────────────┐
│ SENTINEL: MSFT — Cloud Growth Thesis        March 8, 2026 5:15 PM│
│ ────────────────────────────────────────────────────────────────  │
│  ⚠️  THESIS EVENT DETECTED                                        │
│                                                                   │
│  ── What Your Thesis Said ──────────────────────────────────     │
│  "Microsoft's cloud (Azure) revenue will sustain 15%+ annual     │
│   growth, driven by enterprise AI adoption and multi-cloud        │
│   tailwinds. Thesis breaks if growth falls below 12% for         │
│   2 consecutive quarters."                                        │
│                                                                   │
│  ── What Just Changed ─────────────────────────────────────     │
│  Q2 2026 10-Q (filed March 8): Azure growth = 11.4% YoY          │
│  This is the FIRST quarter below your 12% warning threshold.     │
│  Not yet a breach. One more quarter below 12% triggers breach.   │
│                                                                   │
│  ── Agent Analysis ────────────────────────────────────────     │
│  Research Agent: Management attributed slowdown to elongated      │
│  enterprise sales cycles, not structural demand loss. Guidance    │
│  for next quarter: 13–14% growth. Language in earnings call was   │
│  cautious but not alarming.                                       │
│                                                                   │
│  Sentiment Agent: 4 of 6 analyst notes post-earnings maintained  │
│  BUY ratings. 2 downgraded. Consensus EPS estimate cut by 2.1%.  │
│                                                                   │
│  Risk Agent: Position within drawdown tolerance. Macro regime     │
│  remains neutral — yield curve not inverted, credit stable.       │
│                                                                   │
│  ── Supervisor Verdict [Claude 4.6] ───────────────────────     │
│  "This is a warning event, not a thesis breach. The slowdown      │
│  appears cyclical rather than structural based on management      │
│  guidance and analyst consensus. Your thesis requires a second    │
│  consecutive sub-12% quarter before the falsification criterion   │
│  is met. Recommend holding and monitoring next quarter closely."  │
│                                                                   │
│  ── Your Options ───────────────────────────────────────────    │
│  [ 📌 HOLD — I still have conviction in my thesis ]              │
│  [ 🔍 RE-EVALUATE — Open thesis editor to update my criteria ]   │
│  [ 🚪 EXIT — This changes my conviction, I want to close ]       │
│                                                                   │
│  [ 🔎 Open Full Glass Box Audit ]                                │
└──────────────────────────────────────────────────────────────────┘
```

Key differences from v3 Signal Card:
- No BUY/SELL framing. HOLD / RE-EVALUATE / EXIT framing — the question is about conviction, not direction.
- The thesis is quoted explicitly. The user is reminded of what they committed to believing.
- The event is contextualized against the thesis. "First quarter below warning threshold" is more meaningful than "cloud growth = 11.4%."
- RE-EVALUATE opens the thesis editor — the platform explicitly supports evolving your thesis rather than forcing binary decisions.
- No Chronos price range forecast unless the Chronos plugin is enabled. A 14-day price range is irrelevant to a conviction decision on an 18-month thesis.

### 7.4 Behavioral Friction in the EXIT Path

When a user selects EXIT, the platform introduces deliberate friction:

1. "Your thesis falsification criterion is: two consecutive quarters below 12% growth. This is the first. Are you acting on the thesis falsification criterion or on price movement / anxiety?"
2. "Your Mirror Portfolio will continue tracking this position hypothetically if you exit. You'll see whether you exited at the right time."
3. A 24-hour cooling-off option: "Set a reminder to decide tomorrow." Research consistently shows that sleeping on exit decisions during volatility reduces regret.

This friction is not paternalistic — the user can override it instantly. It is a behavioral intervention that the user opted into when they built their thesis. The thesis itself becomes a commitment device.

### 7.5 The Mirror Portfolio

Setup: User declares capital when deploying a Sentinel. Paper portfolio initializes at that amount.

**HOLD behavior:** Paper portfolio holds the position. Mirror Portfolio P&L continues tracking.

**EXIT behavior:** Paper portfolio still holds hypothetically (counterfactual). User's real position is closed. The system tracks: "You exited. Here is what happened afterward."

**Counterfactual Report (the learning engine):**

> "Over 14 months with your MSFT thesis:
> - You received 3 Thesis Breach Alerts
> - You held through 2 (correct — both were warning events that resolved)
> - You exited on the 3rd (position would have recovered 8.2% in the following 60 days)
> - Your thesis-based conviction outperformed your emotional overrides by 6.1% over the period"

This is the platform's long-term value proposition made concrete. Not "our signals are right." But: "Here is the documented history of when your judgment added value and when it didn't. Now you know something real about yourself as an investor."

---

## Part VIII: The Glass Box

### 8.1 Principle (Unchanged from v3, Reinforced in v4)

Every recommendation produced by Aegis AI — historical or live — must be fully reproducible and auditable. The Glass Box is not a UI view. It is a principle applied to every layer of the platform.

The credibility of the simpler tiers depends on the sophistication of the deeper ones. A Conviction Investor who knows they could open the Glass Box and see the LangGraph trace trusts the thesis summary more — even if they never look. Transparency at depth creates trust at the surface.

### 8.2 Glass Box Audit Contents

Accessible from any Thesis Breach Alert or historical trade.

- The exact data snapshot the agent had access to at decision time, with `public_disclosure_ts` for every record
- Thesis parameter values at decision time versus configured thresholds
- Fundamental Engine signal state at decision time
- Plugin signal states (if any were enabled) at decision time
- Research Agent ChromaDB query + retrieved document chunks with citations
- Sentiment Agent FinBERT score breakdown per source
- Risk Agent constraint evaluation, line by line
- LangGraph node-by-node reasoning trace, replayed in chronological order
- Supervisor thesis or breach reasoning (Claude 4.6 output, untruncated)
- MLflow Run ID linking to the configuration that produced this Sentinel

### 8.3 The Anchored Reasoning Principle

In the Thesis Breach Alert and in the Glass Box, every factual claim in the agent's analysis is anchored to its source. Hovering "Azure growth = 11.4%" highlights the specific 10-Q passage that was retrieved from ChromaDB. Hovering the VPIN context line (if a plugin was active) highlights the VPIN chart. Citations are structural, not decorative — they are the difference between a summary you trust and a summary you have to take on faith.

---

## Part IX: Frontend Architecture

### 9.1 Navigation Structure

```
AEGIS AI
│
├── /dashboard              Sentinel Command Center
│   ├── Active Sentinels + live thesis status (INTACT / WARNING / BREACHED)
│   ├── Pending Thesis Breach Alerts (hold / re-evaluate / exit queue)
│   └── Mirror Portfolio performance vs. real account + counterfactual
│
├── /engines                Engine Library
│   ├── /engines/data       Data connectors + point-in-time health status
│   ├── /engines/fundamental Fundamental engine config + current signal state
│   ├── /engines/analyst    Agent configurations + trace history
│   ├── /engines/research   Vector store status + document pipeline
│   ├── /engines/plugins    Plugin Library (VPIN, HMM, Chronos, Alpaca — all OFF by default)
│   └── /engines/custom     User-defined connector + agent registration
│
├── /sandbox                The Sandbox (primary view)
│   ├── Configuration Editor (visual builder with JSON toggle)
│   ├── Quick Iteration Run panel
│   ├── Full Production Backtest launcher
│   ├── Scenario Stress Test builder
│   ├── Live Paper Trading monitor
│   ├── Agent Improvement Proposal Inbox
│   └── Active run progress + live metrics streaming (WebSocket)
│
├── /arena                  MLflow Arena
│   ├── Leaderboard (sortable, filterable)
│   ├── Config Diff Viewer
│   ├── Thesis Evolution View
│   ├── Parallel Coordinate Plot
│   ├── Scenario Survival Matrix
│   ├── LLM vs. Fundamental-Only Comparison
│   └── Promote → Sentinel flow
│
├── /create                 New Sentinel Wizard
│   ├── Step 1: What do you believe? (thesis construction with Claude 4.6)
│   ├── Step 2: What would change your mind? (falsification criteria)
│   ├── Step 3: Template or Build From Scratch
│   ├── Step 4: Review configuration + stress test quick preview
│   └── Step 5: Launch in Sandbox
│
└── /settings
    ├── Paper Portfolios (capital per Sentinel)
    ├── Promotion Criteria defaults
    ├── Thesis breach notification preferences
    └── Model routing configuration (advanced)
```

### 9.2 Key Frontend Design Principles

**Tier-appropriate information density:** The Dashboard and Thesis Breach Alert default to plain-language, low-density views. The Sandbox and MLflow Arena are high-density. Users are never forced into technical views from conviction-oriented flows.

**Progressive disclosure over tabs:** Advanced information (raw metrics, agent traces, plugin signals) lives behind a "Show Details" or "Open Glass Box" control — never as the default view. Users earn access to depth by choosing to look, not by being forced to navigate around it.

**Real-time via WebSocket:** Agent traces stream live during Sandbox runs. The improvement analyzer's plain-language verdict populates in real time as the run completes sections, not as a batch at the end.

**Anchored reasoning:** In the Thesis Breach Alert and Glass Box, every claim links to the underlying data. Hover interactions connect text to charts and source documents.

**Silence as a feature:** The dashboard should be calm when Sentinels are healthy. No "latest market update" noise. No low-confidence alerts disguised as insights. The absence of alerts is meaningful information and the UI should make that feel deliberate rather than empty.

**Dark mode first:** `#0d0d12` background, neon blue/cyan/purple accents, glassmorphism panels. Monospace (JetBrains Mono or Fira Code) for all financial figures.

**New Sentinel Wizard — Step 1 is the highest-risk screen in the product, not just the highest-stakes one:** The thesis construction step, powered by Claude 4.6, must be the most carefully designed screen in the platform. The risk is specific and architectural: if Claude 4.6 does not extract *quantitative, falsifiable* thesis parameters from the user's natural language input, the entire Sentinel monitoring collapses downstream.

The distinction matters precisely:

- "Microsoft will grow" — cannot be monitored. No threshold. No falsification criterion. The Thesis Parameter Monitor has nothing to track.
- "Azure revenue growth must remain above 12% annually" — can be monitored. Specific metric. Specific threshold. Clear breach condition.

A user who completes Step 1 with vague thesis language receives a Sentinel that appears deployed and operational but is monitoring nothing quantitative. The failure is invisible until they wonder why they have never received a Thesis Breach Alert. By that point they may have already made decisions based on false confidence that the system was watching.

**The Step 1 Design Requirement**

Step 1 must not allow thesis construction to complete without at least one quantitative falsification criterion. Claude 4.6's role is not just thesis articulation — it is parameter extraction and quantification. The conversation loop should:

1. Accept the user's natural language thesis statement
2. Extract implied quantitative claims: "Microsoft will grow" → "What growth rate are you expecting? Over what time horizon? What would cause you to change your mind?"
3. Refuse to proceed to Step 2 until at least one monitorable parameter is confirmed: `{metric: "azure_revenue_growth_rate", warn_below: 0.12, breach_below: 0.10, source: "10-Q"}`
4. Show the user their thesis translated into plain-language monitoring criteria before they leave Step 1: "I will monitor Azure revenue growth each quarter. I will alert you if it drops below 12%. I will flag a potential thesis breach if it drops below 10% for two consecutive quarters."

This is both a UX design problem and a prompt engineering problem. The Claude 4.6 system prompt for thesis construction must be written to extract falsifiable parameters, not to produce eloquent thesis summaries. Eloquent summaries are the failure mode — they satisfy the user emotionally while producing nothing the Thesis Parameter Monitor can act on.

This component will require significant iteration. Budget for it accordingly. The quality of every downstream Thesis Breach Alert the platform ever generates depends on getting this right.

---

## Part X: Default Templates

### 10.1 Template Library

Templates are reoriented in v4. Each template describes not just a strategy but a **thesis archetype** — a category of investment belief and the engine configuration best suited to stress-test that belief.

| Template | Investment Thesis Type | Hold Duration | Key Engines | Plugins Available |
|---|---|---|---|---|
| Conviction Value | "This company is structurally undervalued based on fundamentals" | 12–24 months | SEC EDGAR heavy, Form 4 insider monitor, FRED macro overlay, earnings revision tracker | Chronos (optional) |
| Tech Catalyst | "A specific catalyst (product launch, regulation, AI adoption) is not yet priced in" | 2–6 months | FinBERT + SEC 10-Q, earnings call parser, analyst revision tracker | HMM, VPIN (optional) |
| Conservative ETF | "Broad market exposure with macro-informed regime sensitivity" | 3–12 months | FRED macro heavy, earnings revision for index components, tight threshold gates | HMM (optional) |
| Insider Signal | "Management buying their own stock is a high-conviction signal" | 3–9 months | Form 4 Congressional disclosure tracker, cluster buy detector | Chronos (optional) |
| Macro Rotation | "Sector rotation based on macro regime shifts" | 1–3 months | FRED yield curve + credit spreads, sector ETF fundamentals | HMM, VPIN (optional) |
| Day Trader | "Technical and flow-based intraday signals" | Intraday only | Alpaca tick data, VPIN core (not plugin), HMM on 15-min bars | All plugins available |
| Dividend Income | "Sustainable yield from quality companies with balance sheet discipline" | 24+ months | FRED rates, payout ratio tracker, earnings stability monitor, long-horizon Chronos | None recommended |

Note on Day Trader: This template is explicitly marked as Tier 3 in the onboarding wizard. Users selecting it see a notice: "Day trading strategies require understanding of technical and flow signals. The VPIN and HMM tools are active by default in this template. If you're new to these tools, we recommend starting with a different template." The template still exists — the platform serves the full spectrum of users — but it is not the default entry point and it is not presented as equivalent to longer-term templates.

### 10.2 Template Selection — New Sentinel Wizard

The wizard starts with thesis construction before template selection. This is intentional. Users who articulate their thesis first select templates that match their actual belief rather than selecting a template that looks impressive and reverse-engineering a belief to match it.

Step 1: "What do you believe about this investment? Why do you own it, or why are you considering it?" (Free text + Claude 4.6 synthesis into structured thesis)

Step 2: "What would change your mind? What would have to be true for you to exit this position?" (Falsification criteria builder)

Step 3: Based on the thesis type detected in Step 1, the wizard recommends 2–3 templates with plain-language descriptions. The user can also choose "Build From Scratch."

Step 4: Configuration review — the user sees exactly what engines are active, what plugins are available, and what the promotion criteria are. No surprises.

Step 5: Quick Scenario Preview — before launching a full sandbox run, the wizard runs a 30-second simplified stress test on the thesis with 2–3 analog scenarios. Not a backtest. A preview. "Your thesis is most similar to positions that performed well when X and poorly when Y. Here are two historical periods worth examining in detail."

---

## Part XI: Build Order

### Phase 1 — The Mathematical Foundation (Build First)
1. Add `public_disclosure_ts` to all DataEngine connectors including Congressional disclosure
2. Build Configuration Schema loader and validator
3. Build Fundamental Engine (earnings revision tracker, insider activity monitor, thesis parameter monitor, macro overlay)
4. Build the Simulation Loop (vectorized, fundamental signals only, with slippage injection)
5. Build Performance Metrics Calculator
6. Extend MLflow logging to full spec including thesis text and plain-language verdict field

### Phase 2 — The Intelligence Layer
7. Build Thesis Parameter Monitor and breach gate logic
8. Wire LangGraph into the simulation loop as Phase 2 (event-gated on thesis events)
9. Build Model Routing Layer (Claude 4.6 for Supervisor/thesis/breach, Qwen local for sub-agents)
10. Build Improvement Analyzer Agent (both parameter proposals and thesis insight proposals)
11. Build Scenario Stress Test run type
12. Build Quick Iteration Run mode

### Phase 3 — The Sentinel Layer
13. Build Sentinel State Manager (tracks live Sentinels, queues Thesis Breach Alerts)
14. Build Mirror Portfolio Tracker (accepted/declined/held tracking + counterfactual P&L)
15. Build Promotion Gate Evaluator including thesis breach precision criterion
16. Build Plugin Layer (VPIN, HMM, Chronos, Alpaca — off by default, activation logic)

### Phase 4 — The Frontend
17. New Sentinel Wizard — Step 1 thesis construction with Claude 4.6 (most critical screen)
18. Sandbox primary view (run controls, live metrics streaming, proposal inbox)
19. Thesis Breach Alert UI with anchored reasoning
20. Mirror Portfolio counterfactual panel
21. MLflow Arena (leaderboard, config diff, thesis evolution view, scenario survival matrix)
22. Engine Library hubs with plugin catalog
23. Glass Box audit view
24. Dashboard (silent sentinel status, pending alert queue)

---

## Part XII: Guiding Principles

**The Sandbox is the product.** Everything else is how you consume what it produces.

**The thesis is the unit of analysis, not the configuration.** Configurations are instruments for testing theses. A configuration with a high Sharpe ratio that tests a meaningless thesis is less valuable than a configuration with a modest Sharpe that tests a belief the user genuinely holds about a company they own.

**Silence is a feature, not a bug.** The Sentinel's silence means the thesis is intact. Train users to interpret silence as confidence, not absence. Every platform that fills silence with noise is training users to need noise.

**Plain language is not a simplification — it is the output.** A platform that requires users to interpret Sharpe ratios to understand what the Sandbox is telling them has failed its primary design goal. Raw metrics live in the Glass Box and MLflow Arena. The primary interface communicates in the language of investing, not statistics.

**Slippage is always real.** Returns without realistic transaction costs are fiction. Every run, every user tier, no exceptions.

**Point-in-time is non-negotiable.** Lookahead bias invalidates every MLflow result it touches. This applies to all connectors including third-party integrations and RAG retrieval.

**Plugins inform thesis alerts. They never generate them.** VPIN and HMM are context modifiers, not signal generators, in the conviction platform configuration. A user who enables them is adding a lens. They are not getting a new signal source.

**The mirror portfolio's counterfactual is the long-term value.** A user who has 12 months of documented evidence about when their judgment adds value and when it doesn't is a qualitatively different investor than when they started. That record is irreplaceable and cannot be built anywhere else. It is the platform's deepest moat.

**Judgment compounds. Build for that.** The most valuable thing this platform creates is not a good backtest. It is a retail investor who, after a year of serious engagement, genuinely understands why they own what they own and what it would take to change their mind. That investor is better at every subsequent decision they make — with or without this platform. Build for that user.

---

## Part XIII: What Changed from v3 — Changelog

### Thesis and Framing

| v3 | v4 | Rationale |
|---|---|---|
| "A quant strategy research platform that builds and battle-tests portfolio configurations" | "The Databricks for retail investing — a transparent, auditable belief-testing machine" | The v3 framing described a quant tool. The v4 framing describes what the platform actually does: test beliefs. The Databricks analogy captures the progressive-depth architecture for multiple user tiers. |
| Single implicit user type: technical quant | Three-tier user model: Conviction Investor / Curious Tinkerer / Serious Retail Quant | The v3 user had to understand VPIN, HMM, Optuna, MLflow, and LangGraph to use the platform. That user is rare and already served. The three-tier model opens a much larger addressable market without removing anything for the technical user. |
| No explicit behavioral thesis | Behavioral loss framing made explicit: retail investors lose to fear, not signal deficiency | This is the actual product-market fit justification. v3 didn't state it. v4 opens with it and every architectural decision flows from it. |

### Architecture

| v3 | v4 | Rationale |
|---|---|---|
| No model routing layer | Model Routing Layer: Claude 4.6 for thesis/breach, Qwen local for agents | Cost discipline and quality allocation. Not all tasks need frontier model quality. The routing layer is explicit and adjustable, not hardcoded. |
| No explicit plugin system | Plugin Library: VPIN, HMM, Chronos, Alpaca — all off by default | VPIN and HMM are genuinely powerful tools that are inappropriate as defaults for a conviction platform. The plugin architecture keeps them available without imposing them on users who will misinterpret them. This resolves the core product-market mismatch identified in v3. |
| 6 architecture layers | 7 layers — Model Routing Layer added | Explicit separation of model assignment from orchestration logic. |

### The Engine Library

| v3 | v4 | Rationale |
|---|---|---|
| Quant Engine (HMM, VPIN, Chronos) as primary signal layer | Fundamental Engine as primary signal layer | HMM and VPIN are microstructure tools designed for high-frequency market making. They are noise for an 18-month thesis. The Fundamental Engine (earnings revisions, insider activity, thesis parameter monitoring, macro overlay) is the correct primary signal layer for a conviction platform. |
| Congressional trading data as an example data source | Congressional trading data elevated to Core connector | Slow-moving, high-conviction alternative signal that is directly aligned with a long-horizon thesis orientation. Deserves first-class status. |
| VPIN and HMM in default pipeline | VPIN and HMM in Plugin Library, off by default | See above. Plain-language UI labels replace metric names in the default user-facing interface. |
| No thesis parameter monitoring | Thesis Parameter Monitor in Fundamental Engine | This is the technical foundation for the Silent Sentinel. Without monitorable thesis parameters, the Sentinel cannot know when to fire. |

### The Sandbox

| v3 | v4 | Rationale |
|---|---|---|
| Two run types: Quick Iteration, Full Production | Three run types: Quick Iteration, Full Production, Scenario Stress Test | Scenario stress testing is the most accessible and most meaningful Sandbox feature for Conviction Investors. "Does my thesis survive a recession?" is a question every retail investor can engage with. Parameter sweeps are not. |
| Plain language outputs not specified | Plain Language Verdict required for every run, produced by Improvement Analyzer | Raw metrics are insufficient for the platform's stated goal. The improvement analyzer must produce a human-readable interpretation of what the metrics mean for the thesis being tested. This is non-negotiable. |
| Improvement Analyzer proposals: parameter-only | Improvement Analyzer proposals: parameter AND thesis insight | Agents should be able to identify hidden thesis vulnerabilities (e.g., "this thesis has an undeclared macro dependency") not just optimize parameters. |
| Sandbox framed as optimization engine | Sandbox framed as belief-testing machine | The most important reframe in the document. Not cosmetic — changes what the platform promises to deliver and what success looks like. |

### The Sentinel

| v3 | v4 | Rationale |
|---|---|---|
| Signal Card fires whenever signal gate is crossed (3–5x/week possible) | Thesis Breach Alert fires only on deterministic thesis parameter events | Frequent signal cards recreate the behavioral problem the platform is meant to solve. The silent sentinel that fires rarely and meaningfully is a behavioral intervention, not just a feature reduction. |
| BUY / HOLD / SELL framing | HOLD / RE-EVALUATE / EXIT framing | The question for a conviction investor is never "should I buy more?" It is "do I still believe my thesis?" The framing change is substantive. |
| ACCEPT / DECLINE buttons | HOLD / RE-EVALUATE / EXIT with deliberate friction on EXIT | Behavioral intervention design. RE-EVALUATE opens the thesis editor rather than forcing a binary decision. EXIT path includes cooling-off option and counterfactual reminder. |
| Signal Card shows Chronos price range by default | Chronos shown only if plugin is enabled | A 14-day price range forecast is irrelevant to a decision about an 18-month thesis. Showing it by default anchors users to short-term price rather than thesis validity. |
| No explicit behavioral friction | 24-hour cooling-off option on EXIT, thesis reminder before exit | Opt-in behavioral intervention. The user built their thesis as a commitment device. The platform reminds them of that commitment before they override it. |

### MLflow Arena

| v3 | v4 | Rationale |
|---|---|---|
| MLflow as performance ledger | MLflow as performance ledger AND reasoning history | The most important long-term value driver of the platform. A user's MLflow history is a documented record of their evolving investment judgment, not just their configuration performance. |
| No thesis evolution view | Thesis Evolution View (new) | Shows how a user's thesis for a specific ticker has changed across runs. The judgment ledger. |
| No scenario survival matrix | Scenario Survival Matrix (new) | For scenario stress test results — makes thesis robustness immediately visual across multiple adverse conditions. |
| Promotion criteria: Sharpe, alpha, drawdown, win rate | Promotion criteria adds: thesis breach precision min, scenario survival rate min | A configuration that generates high Sharpe but low-precision thesis breach alerts should not be promoted. It will generate noise that erodes user trust and behavioral overtrading. |

### Frontend

| v3 | v4 | Rationale |
|---|---|---|
| Single information density | Tier-appropriate information density + progressive disclosure | Conviction Investors see plain language first. Glass Box is always available but never default. Users choose depth. |
| New Sentinel Wizard starts with style/asset class selection | New Sentinel Wizard starts with thesis construction (Claude 4.6) | Users who articulate their thesis first choose templates that match their actual belief. Template-first selection encourages retrofitting beliefs to templates. |
| Step 1: Trading style | Step 1: "What do you believe? What would change your mind?" | The most important screen in the product. The quality of thesis construction determines the quality of every Thesis Breach Alert. |
| No scenario preview in wizard | 30-second scenario preview before full sandbox launch | Gives Conviction Investors immediate, meaningful feedback before committing to a 4–12 hour production run. |

### What Was NOT Changed

The following v3 elements are preserved entirely and are considered core strengths that the v4 reframe reinforces rather than challenges:

- Point-in-time data discipline (`public_disclosure_ts` on all connectors)
- Slippage and market impact simulation (unchanged, non-negotiable)
- Two-phase backtest architecture (Quick Iteration + Full Production)
- Glass Box principle (every decision auditable to raw data)
- Mirror Portfolio counterfactual tracking
- LangGraph agent topology (Supervisor + Research + Sentiment + Risk)
- ChromaDB RAG with point-in-time retrieval filtering
- Episodic memory for agent self-reflection
- MLflow as the court of truth for configuration validation
- WebSocket streaming for live agent traces
- The six-layer architecture (extended to seven, not replaced)
- Agent Improvement Loop as core differentiator
- The three-step validation pipeline: historical backtest → live paper trading → Sentinel promotion

---

## Part XIV: Known Execution Traps

These are not theoretical risks. They are specific engineering problems that will surface during implementation. Each one has a known fix. None of them should be discovered in production.

---

### Trap 1 — The Segment Obfuscation Problem (Thesis Parameter Monitor)

**The Problem**

The Thesis Parameter Monitor tracks quantitative claims like `cloud_revenue_growth_rate: {target: 0.15}` across quarterly 10-Q filings. The assumption is that the agent can consistently locate and extract this metric across reporting periods. This assumption is wrong.

Public companies regularly restructure how they report business segments — not always for legitimate reasons. A well-known pattern: when a segment's growth begins to slow, companies reorganize reporting structures so the underperforming metric disappears into a blended category. Microsoft has done this. Google does this routinely with how it reports different revenue streams. The agent that was monitoring "Azure Revenue" suddenly cannot find "Azure Revenue" in the new filing — because it has been folded into "Intelligent Cloud Services" combined with a hardware division.

If the system does nothing, one of two failure modes occurs: it generates a false breach alert because the metric appears to have gone to zero, or it silently stops monitoring because the metric is not found, leaving the user with the false confidence that their thesis is being watched.

**The Fix: Two-Stage NLI Check + Human Re-Anchoring Flow**

Stage 1 — Semantic similarity check at each 10-Q ingest: Before attempting metric extraction, compute embedding similarity between the current period's segment label vocabulary and the historical labels used to anchor the thesis parameter. If similarity drops below a configured threshold (start at 0.82 — tune against real EDGAR filings), flag the filing for Stage 2 before any extraction runs.

Stage 2 — LLM structural change analysis: The Qwen agent is asked a constrained question: "The thesis parameter `cloud_revenue_growth_rate` was previously tracked via the 'Azure Revenue' segment disclosure. The latest 10-Q filing does not contain this segment label. Analyze the new reporting structure and determine: (a) whether a semantically equivalent metric can be identified, (b) what the best available proxy is, and (c) whether the change appears cosmetic or structural." Output is a structured JSON response, not free text.

Stage 3 — Human re-anchoring (mandatory, not optional): When a structural change is detected, the Sentinel pauses monitoring for that thesis parameter and surfaces a re-anchoring alert to the user. The alert must show: the original metric and how it was tracked, the detected structural change in plain language, the agent's proposed replacement metric with its rationale, and a "Confirm New Anchor" or "Exit Position" choice. Monitoring does not resume until the user explicitly confirms the new anchor.

This flow is both the correct engineering behavior and a regulatory defensibility argument — the human is explicitly in the loop on material changes to how their thesis is being monitored.

**Implementation Note for Current Environment (Mac, Qwen 2.5 7B)**

The Stage 2 NLI task is within Qwen 2.5 7B's capability when the prompt is tightly constrained. Do not ask it to reason freely about financial reporting structures — give it the old label, the new filing's segment vocabulary, and a structured JSON output schema. Free-form reasoning on financial document analysis degrades significantly at 7B scale. Constrained extraction with a defined output schema is where 7B models are reliable.

---

### Trap 2 — The Scenario Stress Test Is Not a Simulation (Scenario Library)

**The Problem**

The Scenario Stress Test feature is described as "test your thesis against the 2022 rate hike cycle." The implementation trap is treating this as something the LLM can reason about abstractly. Telling an agent to "simulate rising rates" produces a hallucination with financial formatting, not a simulation. The agent will generate plausible-sounding analysis that has no relationship to what actually happened to your specific tickers during that period.

**The Fix: Deterministic Historical Scenario Library**

Scenarios must be implemented as deterministic date-range mappings in the Data Engine, not LLM reasoning tasks. When a user selects a scenario, the system programmatically maps it to specific historical date windows and runs the standard vectorized backtest over those exact dates using real data from FRED, YFinance, and SEC EDGAR.

The scenario library should be curated, versioned, and honest about what it contains:

```json
{
  "rising_rate_environment": {
    "description": "Federal Reserve tightening cycles with >200bps cumulative rate increase",
    "instances": [
      {"label": "1994 Tightening", "start": "1994-02-04", "end": "1995-02-01"},
      {"label": "1999–2000 Tightening", "start": "1999-06-30", "end": "2000-05-16"},
      {"label": "2004–2006 Tightening", "start": "2004-06-30", "end": "2006-06-29"},
      {"label": "2018 Tightening", "start": "2018-03-21", "end": "2018-12-19"},
      {"label": "2022–2023 Tightening", "start": "2022-03-17", "end": "2023-07-26"}
    ],
    "fred_series": ["FEDFUNDS", "DGS10", "T10Y2Y"],
    "thesis_relevant_if": ["interest_rate_sensitivity", "duration_risk", "credit_spread"]
  }
}
```

Three additional requirements:

**Multi-instance survival rates, not single-instance pass/fail.** A thesis that survived four of five rate hike cycles is a different thesis than one that survived the 2022 cycle specifically. The Scenario Survival Matrix should show performance across all historical instances of a scenario type, not just the most recent or most salient. Users gravitate toward recent examples — the system should surface the less-remembered ones.

**Scenario decomposition.** The 2022 rate hike cycle was simultaneously a tech valuation reset, a post-COVID demand normalization, a commodity shock from the Ukraine war, and a tightening cycle. When a thesis underperforms in this scenario, the agent should attempt to attribute which factor was the primary driver: "Your thesis showed stress in the 2018 cycle (pure rate sensitivity) and the 2022 cycle (rate + valuation compression). The 1994 and 2004 cycles — where rates rose but valuations did not compress — showed no meaningful performance degradation. This suggests your thesis is more sensitive to valuation multiple compression than to interest rates directly." That is actionable. "Your thesis failed in rising rate environments" is not.

**Recency bias nudge.** Users will select the scenarios they've heard about on financial media. The system should surface lesser-known analogs: "You selected 2022. The 1994 tightening cycle has a similar rate of change profile but a different starting valuation environment. Running both gives a more complete picture."

**Implementation Note for Current Environment**

The vectorized backtest runs entirely on local data — no LLM involvement for the backtest itself. At 16GB RAM with Qwen 2.5 7B, the constraint is not the backtest (that's NumPy/pandas) but the LLM-based scenario decomposition analysis that runs afterward. Keep the decomposition prompt tightly scoped: give the agent the per-scenario performance breakdown as a structured input and ask for a constrained comparison, not an open-ended analysis of macroeconomics. The analysis runs after all scenarios complete, not during them.

---

### Trap 3 — The Iterative Overfitting Trap (Agent Improvement Loop)

**The Problem**

This is the most dangerous trap in the platform and it is entirely self-inflicted. It is dangerous specifically because of a strength: the Agent Improvement Loop works.

Here is the failure scenario: A user runs a production backtest. Performance is mediocre. The Improvement Analyzer proposes a change. User approves. Performance improves. This happens five more times. By iteration six, the user has a configuration that looks excellent on the backtest period. MLflow shows a clear improvement trajectory across six versioned runs. The user promotes it to a Sentinel with high confidence.

What they actually have is a configuration that has been iteratively fitted to a specific historical period through six rounds of agent-guided optimization with human approval at each step. The human approval is not a safeguard here — it is a source of false confidence. The user sees a legitimate-looking deliberation process and concludes the result must be valid. The MLflow history, which should be the court of truth, instead documents the process by which they overfit the data.

This is not a hypothetical. It is what happens in every system where humans can iteratively adjust a model based on its performance on the same data they are evaluating it against.

**The Fix: Held-Out Validation Set, Enforced by the Promotion Gate**

When a production backtest is initiated, the simulation engine silently partitions the configured time window: 80% is the optimization window (visible to the Improvement Analyzer and to the user), 20% is a held-out validation window (never shown during the improvement loop, never accessible to the agent, never visible in the MLflow leaderboard during active iteration).

The held-out window is selected randomly from within the configured date range — not always the most recent 20%, which would introduce its own bias toward recency. The specific held-out dates are logged in MLflow but not displayed in the UI until the user initiates promotion.

When the user clicks "Ready to Promote" in the MLflow Arena, the promotion gate runs the current configuration against the held-out window for the first time. This result is shown alongside the optimization window result:

```
Optimization window (80%):  Sharpe: 1.31 | Alpha: +6.2% | Drawdown: -11.4%
Held-out validation (20%):  Sharpe: 0.94 | Alpha: +2.1% | Drawdown: -17.8%
Performance degradation:    Sharpe: -0.37 | Alpha: -4.1%

⚠️  Significant degradation detected on unseen data.
    This configuration may be overfit to the optimization period.
    The promotion gate requires held-out Sharpe ≥ 0.85. Current: 0.94 — PASSES.
    However: consider whether the improvement loop is overfitting before promoting.
```

If the held-out result fails the promotion gate, the configuration cannot be promoted. If it passes but shows significant degradation, the user is shown the gap prominently and asked to confirm they understand the implication.

The plain-language explanation shown to the user: "Your strategy looked excellent on the historical data it was built against. This test ran it against a different period it has never seen. A large gap between these two results suggests the strategy may be too tuned to specific historical conditions rather than a robust thesis."

**A Note on This Trap Specifically**

The reason this trap is more dangerous than the others is that it is invisible in the normal workflow. The segment obfuscation problem generates an obvious failure — the metric disappears. The simulation problem generates obviously wrong outputs if you know what to look for. But iterative overfitting generates a beautiful, coherent, well-documented MLflow history that looks like exactly what the platform promised. The court of truth becomes the evidence of the crime.

Building the held-out validation set is non-negotiable before the Improvement Analyzer is enabled for any user.

---

### Trap 4 — The Regulatory Framing Trap

**The Problem**

The "user-directed software tool" framing — the argument that because the user clicks HOLD/EXIT, the platform is not exercising discretionary trading power — is a legitimate distinction but it is not an unconditional defense. It depends entirely on implementation details that can drift, and on marketing language that can undermine it.

Three specific risks:

**The nudge problem:** If the Improvement Analyzer consistently generates proposals that move configurations toward more aggressive signals, and users consistently approve them because the proposals look data-backed and authoritative, regulators may characterize the agent as exercising de facto discretion regardless of who clicks the button. The defense is empirical: MLflow must log not just approved proposals but rejected ones, showing the distribution of user decisions. A user who regularly rejects agent proposals is demonstrably making independent decisions. A user who approves 94% of proposals is arguably being directed.

**The thesis construction liability:** When Claude 4.6 constructs an investment thesis from SEC filings and the user acts on it, any factual error in that thesis — even a small one — lands in murky territory. The Glass Box is the primary defense because it shows exactly what data the agent had. But you also need explicit, prominent disclosures at thesis construction time (not buried in terms of service): "This thesis was generated by AI from publicly available information. It is not financial advice. Verify all factual claims independently before making investment decisions." Prominent means on the thesis card itself, not in a modal the user dismissed during onboarding.

**Marketing language:** The phrase "Epistemic Integrity Engine" — or any language that implies reliability, accuracy guarantees, or systematic correctness — is a liability in a regulatory environment that is focused on AI integrity claims. Your marketing language should stay close to what the system actually does: "a research tool for testing investment theses against historical data." Words to avoid in any public-facing context: integrity, accurate, reliable, proven, validated (in reference to future performance). These create warranty-like expectations that no probabilistic system can meet.

**The Fix**

The nudge problem specifically requires a logging architecture decision made from day one, not retrofitted later. Once the Improvement Analyzer has been running and users have been approving proposals for months without rejection logging in place, you cannot reconstruct that history. The regulatory defense depends on empirical data about user decision-making patterns. That data must exist from the first proposal the system ever generates.

**Proposal Decision Logging — Required from Day One**

Every Improvement Analyzer proposal must be logged to MLflow with one of three outcomes: `APPROVED`, `REJECTED`, or `MODIFIED_AND_APPROVED`. The modified approval is important — a user who changes a proposed VPIN threshold from 0.75 to 0.70 before approving is demonstrably exercising independent judgment, not rubber-stamping. That distinction matters.

```json
{
  "proposal_id": "prop-42",
  "generated_at": "2026-03-08T14:22:00",
  "proposed_by": "improvement_analyzer_v2.1",
  "target_param": "quant_engine.vpin.toxicity_threshold",
  "proposed_value": 0.75,
  "outcome": "MODIFIED_AND_APPROVED",
  "user_value": 0.70,
  "decision_at": "2026-03-08T14:31:00",
  "time_to_decision_seconds": 540
}
```

`time_to_decision_seconds` matters: a user who approves every proposal within 3 seconds of generation is not deliberating. That pattern is distinguishable from a user who spends 8 minutes reviewing a proposal before approving a modified version. Both are logged. The distribution tells the regulatory story.

**Platform-Level Decision Audit**

MLflow should expose a platform-level view (internal, not user-facing) showing proposal approval rates across all users over time. If the approval rate for any agent proposal type exceeds 90% consistently, that is a signal that the agent may be nudging rather than advising. The appropriate response is not to add friction arbitrarily — it is to investigate whether that proposal type is genuinely useful or is a de facto instruction.

**The remaining three requirements are unchanged:** prominent thesis-level disclosure language drafted by a fintech-specialized lawyer (not an engineer); a marketing language review before any public launch; and a quarterly review of whether the platform's behavior in practice still matches the user-directed framing as the product evolves.

The Glass Box principle is genuinely strong regulatory defense. Do not undermine it with marketing claims that overpromise what the platform delivers.

---

### Current Development Environment Constraints

**Hardware:** Mac, 16GB unified memory
**Local model:** Qwen 2.5 7B (via Ollama or equivalent)
**API model:** Claude 4.6 (Sonnet) via Anthropic API

At 16GB with Qwen 2.5 7B, the practical constraints are:

**What runs fine:** Vectorized backtest simulation (pure NumPy/pandas, no model involved). FRED and YFinance data ingestion. ChromaDB embedding and retrieval. FinBERT sentiment scoring (small model, CPU-friendly). Risk Agent constraint validation (constrained structured reasoning, 7B handles this well). Quick Iteration Run — should complete in 2–5 minutes at this scale.

**What degrades at 7B:** Improvement Analyzer proposals that require multi-step causal reasoning ("why did this backtest fail and what specific change would improve it"). Free-form financial document analysis. Scenario decomposition across multiple historical periods simultaneously. For these tasks, keep prompts tightly constrained with structured output schemas — 7B models are substantially more reliable on extraction tasks with defined schemas than on open-ended analytical tasks.

**What should stay on Claude API regardless:** Thesis construction (too important to quality-compromise). Thesis Breach Alert reasoning (highest-stakes output in the platform). Supervisor synthesis of sub-agent votes.

**Memory ceiling:** At 16GB, running Qwen 2.5 7B alongside ChromaDB, MLflow, FastAPI, and a React dev server simultaneously will be tight. If memory pressure causes model swap-outs, Quick Iteration Run latency will spike dramatically. Prioritize: close unnecessary applications during Sandbox runs. If Ollama is used, set `OLLAMA_MAX_LOADED_MODELS=1` to prevent model thrashing.

**The VM question:** When cloud deployment becomes relevant, the architecture is ready for it. The Model Routing Layer was designed to make this transition clean — the local Qwen endpoint swaps to a cloud VM endpoint with no agent-level code changes. That decision doesn't need to be made now.

---

## Part XV: Changelog — What Changed from v4 to v4.1

### Added: Part XIV — Known Execution Traps

Four traps added based on implementation analysis:

| Trap | Impact | Fix Complexity |
|---|---|---|
| Segment Obfuscation (Thesis Parameter Monitor) | High — can generate false breach alerts or silent monitoring failures | Medium — NLI similarity check + human re-anchoring flow |
| Scenario Library Implementation | High — LLM cannot simulate scenarios; must use deterministic date-range backtests | Medium — curated scenario library with multi-instance survival rates |
| Iterative Overfitting (Improvement Analyzer Loop) | Critical — the platform's strongest feature is also its most dangerous without this fix | High — held-out validation partition enforced at promotion gate |
| Regulatory Framing Drift | Medium — user-directed framing is valid but requires active maintenance | Low — logging, disclosure language, marketing review |

### Updated: Model Routing Section

Updated from abstract VM deployment guidance to reflect actual current development environment: Mac 16GB RAM, Qwen 2.5 7B local. Added specific guidance on what degrades at 7B scale and mitigation strategies (constrained prompts, structured output schemas). VM deployment guidance preserved as a future-state note — the routing layer is designed to make that transition seamless when the time comes.

### Updated: Promotion Gate

Added held-out validation set requirement to the promotion gate. Configurations can no longer be promoted based solely on optimization-window performance. Held-out window is randomly partitioned at backtest initiation, never shown during improvement loop, evaluated only at promotion time. Significant degradation (>0.30 Sharpe drop) must be acknowledged by user before promotion proceeds.

### What Did Not Change

All architectural decisions from v4 remain intact. The execution traps section does not change what gets built — it changes how specific components are implemented to avoid known failure modes. The build order from Part XI is unchanged. The guiding principles from Part XII are unchanged.
