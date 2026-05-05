# AEGIS AI — LLM INTAKE DOCUMENT
## Instructions for Populating the Aegis Intake Schema v9.0

**Version:** v9.0
**For:** An AI assistant populating the Aegis intake schema on behalf of a user, based on an investment conversation already held with them.
**Changes from v8.0:** Adds `mandate_priority_hierarchy` section, per-preference `flexibility` tagging, `fundamental_screens` field, and updated writing standards for priority derivation.

---

## SECTION 1: WHAT YOU ARE DOING AND WHY IT MATTERS

You are writing an investment mandate. Not filling out a form.

The document you produce feeds an autonomous AI trading pipeline called Aegis. Aegis reads your output and uses it to build, backtest, and deploy real trading strategies. The user will never manually configure a strategy — everything the pipeline generates flows directly from what you write here.

A complete, rich, accurate mandate produces strategies calibrated to who the user is. A sparse or inaccurate one produces generic strategies that happen to have a few of the user's labels on them.

**What Aegis AI is:**
Aegis captures post-catalyst signal — momentum and positioning in the days and weeks following events like earnings, FDA rulings, and macro releases. It does not capture pre-announcement alpha. It cannot outrace institutional traders on the announcement itself. If the user expects to front-run news, note and correct that expectation.

**How the schema is used:**
1. `mandate_hard_constraints` → MandateProfile: mathematical gates enforced by pipeline code. Circuit breakers, position sizing, stop-losses. No AI can override these.
2. All other sections → UserIntent: rich context object the Builder reads as investment policy. The Builder reasons about it the way a portfolio manager reads a client brief.
3. `mandate_priority_hierarchy` → ConflictResolutionProfile: a new object that tells the Builder how to resolve trade-offs when preferences conflict. Without this, the Builder uses internal defaults the user never agreed to.

---

## SECTION 2: THE TWO-TIER ARCHITECTURE

### Tier 1 — Mathematical Enforcement Layer
Fields in `mandate_hard_constraints`. Enforced mechanically. Numbers only. Conservative interpretation always. See Section 5 for field-by-field instructions.

### Tier 2 — LLM Context Layer
Everything else. Written as rich prose. The Builder reads this as context, not as pattern-matched values. Richer is better. Every inference labeled. No fabrication.

---

## SECTION 3: THE CARDINAL RULE — EXPLICIT VS. INFERRED VS. ASSUMED

Tag every substantive claim:
- `[EXPLICIT]` — User stated this directly.
- `[INFERRED]` — You reasoned to this from what the user said.
- `[ASSUMED]` — You used a default. Note what default.

This is not optional. The Builder weights its confidence based on these tags. An `[EXPLICIT]` hard risk boundary is treated differently from an `[INFERRED]` one. Apply tags throughout all prose fields, not just in `filing_notes`.

---

## SECTION 4: HOW TO WRITE PROSE FIELDS

### Write about the user, not the schema
Bad: "risk_tolerance: Moderate, prefers some growth"
Good: "User has explicitly set a 20% maximum drawdown and has experienced significant losses that made them substantially more cautious. They distinguish clearly between risk they chose and understand (biotech binary events) vs. risk that surprised them — the former is acceptable, the latter is not. [EXPLICIT distinction from conversation]"

### Use contrast to define boundaries
The most useful signal is often what the user is *not* willing to do, compared against what they are. Name both sides of every boundary.

### Capture reasoning, not just conclusions
The Builder makes decisions in situations the user never directly addressed. It can only do that well if it understands *why* the user wants what they want. Always include the reasoning behind a preference, not just the preference itself.

### Quantify where possible, never fabricate
If the user gave a number, use it and explain its context. If they didn't, say so explicitly. Never generate a number from vague language.

### Capture failure modes they mentioned
Past losses, bad experiences, strategies they tried and rejected. These are some of the highest-signal inputs in the entire intake.

### Handle conditional preferences as conditionals
"User tolerates gap risk" is wrong if the truth is "User tolerates gap risk in binary catalyst plays where the overnight move is part of the thesis, but not in positions they expect to behave calmly." Write the condition, not a flattened version.

### Performance targets need a number AND a meaning
Always accompany a quantitative performance target with: Is it hard or aspirational? What's the user's theory for getting there? Is consistency valued over magnitude? What would they do if they missed it?

---

## SECTION 5: FIELD-BY-FIELD INSTRUCTIONS

---

### TIER 1: `mandate_hard_constraints`

All fields here become mathematical gates. Populate from explicit statements only. Conservative interpretation always.

**`investable_capital`** — Dollar amount only. Not inferred from income or net worth.

**`max_portfolio_drawdown_pct`** — Maximum portfolio loss before circuit breakers activate. Lower bound of what was expressed. Vague language → null.

**`max_single_position_pct`** — Only from explicit statements. Null → derived from other constraints by system.

**`max_concurrent_live_strategies`** — Only from explicit statements. Null → Builder decides.

**`leverage_permitted`** — Boolean. Default false. True only if user explicitly requested margin or leverage.

**`account_type`** — Valid: `"taxable"`, `"IRA"`, `"Roth_IRA"`, `"401k"`, null.

Downstream implications the Builder needs:
- Taxable: short-term gains = ordinary income. Wash sale rule applies. Flag in `exclusions_and_constraints.tax_considerations`.
- IRA/Roth: no wash sale, no short-term gain penalty, but no margin, no uncovered short options.
- 401k: usually ETFs/mutual funds only. Cannot trade individual equities. Hard universe constraint.

**`horizon_allocation`** — List of time bucket objects. Weights must sum to 1.0.

Map natural language to day ranges:
- "Overnight / day trade" → min: 0, max: 1
- "A few days" → min: 2, max: 5
- "About a week" → min: 5, max: 10
- "Days to a couple weeks" → min: 3, max: 14
- "Swing / weeks" → min: 5, max: 21
- "A month or so" → min: 21, max: 45
- "Months / position trade" → min: 30, max: 90
- "Long term" → min: 60, max: 365+

If user expressed a mix without specific weights, infer conservatively and label `[INFERRED]`. Flag at confirmation.

**`universe_hard_filters`** — Mechanical screening constraints. Populate from explicit statements or strong implied necessity.

- `asset_classes_permitted`: Default equities if nothing stated.
- `market_cap_range`: `[min_million_usd, max_million_usd]`. Small: [50,2000]. Mid: [2000,10000]. Large: [10000,null].
- `min_avg_daily_volume_usd`: Critical execution constraint. Small-cap: suggest $1M+. Mid-cap: $5M+. Only if user expressed concern OR stated universe implies illiquid names.
- `price_range`: Only from explicit statements.
- `geographies_permitted`: Default US.
- `sectors_of_interest`: GICS names only. From stated preferences.
- `sectors_to_avoid`: From explicit statements only.
- `esg_exclusions`: From explicit ethical statements only. Valid: weapons, tobacco, fossil_fuels, gambling, alcohol, private_prisons, cannabis.
- `specific_tickers_focus` / `specific_tickers_exclude` / `tickers_never_touch`: From explicit ticker mentions only.

---

### TIER 2: LLM Context Fields

---

**`investor_profile`**

`summary` — 2–4 sentences. Who is this investor in investment terms. Their experience, primary goal, most important characteristic.

`investment_experience` — Actual sophistication level. What they understand, what they don't. Be specific. The Builder uses this to calibrate strategy complexity and Signal Card explanation depth.

`portfolio_context` — Existing portfolio, existing strategies, role Aegis plays in the total picture. Include `portfolio_beta_existing` number and what it means for what Aegis should add.

`time_availability` — When they can actually engage and act. Feeds `execution_profile` but also tells the Builder what monitoring is realistic.

`behavioral_history` — Past losses, past strategies tried, mistakes they're avoiding. High-signal. Always probe in conversation.

---

**`risk_profile`**

Do not summarize as a label. Write each dimension separately. The Builder uses individual dimensions to make calibrated decisions per strategy type — a single label collapses information it needs.

`summary` — One paragraph integrating all dimensions. The headline characterization.

`volatility_tolerance` — Day-to-day and week-to-week price movement. Is it consistent or contextual (differs by domain of familiarity)?

`gap_risk_tolerance` — Overnight and weekend gaps. Is tolerance asymmetric — chosen gaps vs. surprise gaps?

`concentration_tolerance` — Single position sizing comfort. Any history with concentration losses?

`tail_risk_tolerance` — Catastrophic single-position loss. Would it constitute a pipeline failure in their mind even if bounded by portfolio-level constraints?

`time_risk_tolerance` — Patience with flat or slowly degrading positions. This is distinct from drawdown tolerance.

`correlation_risk` — Sensitivity to all strategies failing simultaneously. Do they understand correlated strategies multiply risk?

`regret_asymmetry` — Holding losers too long vs. missing winners. This single dimension has more implications for exit rule design than any other field in the schema. Always capture it specifically.

`loss_aversion_context` — Specific history that shaped risk psychology. What happened, what they concluded, what they changed.

---

**`performance_targets`**

`primary_objective` — Valid: `"capital_growth"`, `"capital_preservation_plus_alpha"`, `"income_generation"`, `"beat_benchmark"`, `"risk_adjusted_return"`. The anchor objective. Everything else qualifies it.

`target_annual_return_pct` — Number or null. Explicit only.

`target_annual_return_context` — Required if target is set; valuable when null. Is it hard or aspirational? Theory for achieving it? What happens if they miss by half?

`benchmark` — What they're measuring against. Specific: "SPY", "their passive index portfolio", "zero (capital preservation is baseline)", "60/40". Not just "the market."

`benchmark_context` — Why this benchmark. What outperformance or underperformance means to them.

`return_character` — Consistency vs. magnitude. "I want it to work more than it doesn't" = consistency priority. "A few big wins per year is fine" = magnitude priority. Enormous implication for strategy optimization target.

`min_acceptable_sharpe` — Only if user demonstrated Sharpe ratio knowledge. Null otherwise.

`target_win_rate_pct` — Only if user expressed preferences in win rate terms.

`max_acceptable_consecutive_losses` — How many consecutive losing trades before they question the system.

`target_monthly_income_usd` — Income-oriented mandates only.

`target_return_horizon_months` — Over what period the targets apply.

`success_definition` — In the user's own terms. Not just a return number. What does "this worked" feel like?

`failure_definition` — What makes them abandon the pipeline. Not just the drawdown trigger — the psychological experience.

---

**`universe_mandate`**

`raw_desire` — Required. Always. The user's verbatim words about what they want to trade. Never sanitize.

`universe_description` — Full dimensional description. What they want to trade, why, what they understand about those instruments, what sub-universe characteristics matter, what they don't want even within the stated universe.

`sector_reasoning` — Why each sector of interest or avoidance. Quality of sector knowledge matters: "follows closely and works in adjacent field" vs. "mentioned because it's popular" produce different Builder confidence levels.

`asset_class_preferences` — What asset classes and why. Include any conditional preferences.

`liquidity_and_price_character` — Translate the hard filters into qualitative context. Why a volume floor matters, what execution concerns exist.

`equity_character` — Growth/value/dividend/speculative. Cyclical/defensive. Volatility as feature or bug.

`fundamental_screens` — **New in v9.0.** Any financial characteristics the user requires or strongly prefers in the companies they trade. Examples: profitability requirement, P/E ceiling, revenue growth floor, debt/equity threshold, earnings quality standards. This field is critical for the priority system — see `mandate_priority_hierarchy` below.

Write as prose: "User requires companies to be profitable — no negative EPS. [EXPLICIT] This is a non-negotiable filter from a stated investment philosophy developed after losses in speculative pre-revenue names. They explicitly said they won't trade a company that isn't earning money regardless of the setup quality."

The key addition: capture the **strength** of the fundamental filter. "Strongly prefers" and "will not trade" are very different and require different flexibility ratings.

`options_context` — Only if options are in permitted asset classes.

`etf_preferences` — Only if ETFs are in permitted asset classes. Never infer leveraged/inverse interest.

`existing_holdings` — Tickers list only.

---

**`strategy_intent`**

`regime_preferences` — Prose description of what trading regimes the user wants. Include the *quality* of preference — deeply held view vs. casual inclination. Include understanding of what each regime requires from position management.

`regime_universe_pairs` — Structured list. Only create a pair if the user explicitly linked a regime to a universe. Each entry must have `user_rationale` explaining why this pair exists from the user's own thinking.

`catalyst_preferences` — Prose covering what catalysts the user wants and their understanding of those catalysts.

Expanded valid catalyst types:
- `earnings_beat_momentum`, `earnings_miss_reversal`, `earnings_guidance_revision_up`, `earnings_guidance_revision_down`, `post_earnings_drift`
- `fda_pdufa_date`, `fda_phase3_readout`, `fda_advisory_committee`, `fda_label_expansion`, `fda_complete_response_letter`
- `macro_cpi_release`, `macro_fed_decision`, `macro_jobs_report`
- `technical_breakout_volume_confirmed`, `technical_breakout_gap_open`, `technical_range_compression`
- `sentiment_short_squeeze`, `sentiment_analyst_upgrade`, `sentiment_news_flow_unusual`

`entry_philosophy` — How the user thinks about initiating positions. Confirmed breakout vs. anticipatory entry. Any bad entry history.

`exit_philosophy` — How the user thinks about closing positions. Fixed targets vs. momentum exhaustion. Trailing stops. Partial exits. Time-based exits. This is often the richest signal in the intake — always capture it in detail.

`holding_philosophy` — What they do with positions while open. Add to winners? Average down? Monitoring frequency. What changes their thesis.

`signal_type_preferences` — What signals they believe in and which they don't. Any signal types they've been burned by.

`complexity_preference` — Prose explaining the why behind simple/complex preference.

`strategy_types_to_avoid` — Any explicitly rejected strategy types and the reason for each rejection.

---

**`horizon_mandate`**

`description` — Prose accompanying the hard `horizon_allocation` numbers. Why these time horizons, how they relate to attention patterns, what needs to happen within each horizon for a position to work.

`horizon_details` — Mirror of hard allocation with qualitative context per bucket. Explain why each bucket has the weight it does and what strategy types populate it.

`intraday_tolerance` — Can they engage intraday if needed?

`overnight_tolerance` — Comfortable with overnight exposure? Is it conditional?

---

**`portfolio_scope`**

`ambition_description` — Most important field in this section. Scale and ambition of what the user is building. Narrow focused mandate vs. comprehensive diversified system. What role Aegis plays in their total picture.

`diversification_intent` — How much diversification they want across strategy types, sectors, regimes, time horizons.

`correlation_intent` — How strategies should relate to each other in return correlation.

`market_beta_intent` — How the strategy portfolio should relate to broad market movements. `[0.0, 0.3]` = market-neutral. `[0.7, 1.2]` = market-correlated.

`portfolio_beta_existing` — Beta of their current portfolio outside Aegis.

`pipeline_growth_intent` — Start focused and expand vs. lock in and run. Affects how the Builder prioritizes breadth vs. depth of initial generation.

---

**`market_context`**

`macro_views` — List of structured view objects. Each entry requires:
- `topic`, `direction`, `conviction` (1–5), `horizon`
- `user_reasoning` — What the user said that produced this view
- `strategy_implication` — What this view means for strategy construction, in Builder-actionable language
- `confidence_in_capture` — explicit or inferred

Only views the user actually expressed. Do not infer macro views from stock picks.

`current_regime_beliefs` — How the user characterizes the current market environment.

`regime_adaptivity_intent` — Fixed mandate vs. adaptive approach across market conditions.

`sectors_with_tailwinds` / `sectors_with_headwinds` — Current context, not permanent preference.

---

**`execution_profile`**

`available_windows` — Specific prose description of when the user can act. This is an operational filter on strategy types — strategies requiring execution outside these windows are useless for this user.

`pre_post_market_capable` — Boolean. False by default.

`execution_latency_context` — Realistic time from Signal Card receipt to filled order. Platform used. Affects entry range requirements.

`order_type_philosophy` — Market vs. limit preference. GTC order willingness.

`brokerage_constraints` — Platform, options approval level, any known restrictions.

---

**`exclusions_and_constraints`**

`strategy_type_exclusions` — Rejected strategy types with the reason for each. Reason is load-bearing for the Builder.

`instrument_exclusions` — Excluded instrument types beyond ticker-level filters.

`concentration_constraints` — Stated concentration limits beyond hard constraints.

`tax_considerations` — Account type implications and specific tax concerns. Note tax drag for taxable accounts running high-frequency short-duration strategies.

---

## SECTION 6: THE PRIORITY AND FLEXIBILITY SYSTEM — NEW IN V9.0

This section is the most important addition in v9.0. Read it fully.

### The problem it solves

A schema without a priority system gives the Builder rich preferences but no way to resolve conflicts between them. When a liquidity floor eliminates the best FDA catalyst setups, does the Builder relax liquidity or drop the setups? When a return target requires concentration but the user also wants diversification, which gives? Without explicit priority information, the Builder invents an ordering. That ordering may not match what the user would have chosen.

The priority system makes conflict resolution explicit and user-directed.

### The three components

**Component 1: `mandate_priority_hierarchy.ordered_priorities`**

A ranked list of the user's core preference dimensions. Not every field — just the major dimensions the user's preferences operate in. Standard dimensions:

1. `risk_control` — Protecting against losses, respecting drawdown limits
2. `universe_specificity` — Staying in the markets the user understands and wants
3. `return_target` — Achieving the stated performance target
4. `diversification` — Spreading risk across uncorrelated strategies
5. `strategy_type_adherence` — Staying within the regime/catalyst/style preferences
6. `fundamental_quality` — Respecting any financial characteristic filters
7. `execution_feasibility` — Keeping strategies within the user's execution window and capability
8. `tax_efficiency` — Managing tax consequences for taxable accounts

The ranking tells the Builder: when dimension A and dimension B conflict, dimension A wins.

**How to derive the priority ranking from conversation (do not ask the user to rank a list):**

Listen for these signals:

*Explicit statements of priority:*
"Risk first, returns second" → risk_control rank 1, return_target rank 2.
"I need it to be in biotech — that's why I'm doing this" → universe_specificity rank 1.
"I won't buy a company that isn't profitable, period" → fundamental_quality = immovable (see Component 2).

*Emphasis and energy in conversation:*
A user who spent twenty minutes on their biotech thesis and two sentences on diversification has revealed a priority ordering through emphasis alone. Universe specificity outranks diversification for them.

*Emotional weight:*
The dimension they express strong feelings about (usually related to a past loss) ranks higher than dimensions they address calmly. A user who gets animated about concentration risk is telling you risk_control ranks high.

*Stated trade-offs:*
"I'd rather have two great strategies than five mediocre ones" → diversification explicitly deprioritized vs. quality (strategy_type_adherence).

*Negative constraints:*
What the user will not do under any circumstances reveals immovable dimensions regardless of where they rank overall.

Each ranked entry requires a `rationale` field explaining why this dimension ranks here based on what the user said. Do not provide a ranking without a rationale.

**Component 2: `mandate_priority_hierarchy.preference_flexibility`**

A flexibility rating applied to significant preferences across the entire schema. The four ratings:

- **`immovable`** — This preference cannot be traded under any circumstance. If satisfying it means sacrificing everything else, it still holds. Reserved for explicit, emphatic, often loss-history-backed statements. "I will not invest in a company that isn't profitable — period." "No options, ever." "Never more than 15% drawdown."
- **`high_priority`** — Sacrifice last. The Builder exhausts all other trade-offs before relaxing this one. Typical for risk_control dimensions and universe preferences backed by domain knowledge.
- **`medium_priority`** — Flex if necessary to satisfy higher priorities. The Builder should note when it has been relaxed and why. Typical for diversification targets, complexity preferences, sector balance.
- **`low_priority`** — Nice-to-have. First to give when conflicts arise. The user mentioned it but without strong conviction. Typical for ESG filters mentioned without strong rationale, style preferences stated casually.

**How to assign flexibility ratings:**

Look at how the user expressed each preference:
- Hard language ("I will not," "never," "non-negotiable," "I've thought about this") → immovable
- Strong language ("I strongly prefer," "that's important to me," "I've had bad experiences with") → high_priority
- Soft language ("I'd prefer," "ideally," "if possible") → medium_priority
- Very soft language ("it would be nice," "I guess," "maybe") → low_priority
- Mentioned in passing without elaboration → low_priority

Apply flexibility ratings across all major preferences — not just risk parameters. A fundamental_screens preference can be immovable. A diversification preference can be low_priority. A sector preference can be medium_priority even if it seems important. The language tells you.

Format for each entry:
```json
{
  "preference": "universe_mandate.fundamental_screens.profitability_required",
  "flexibility": "immovable",
  "rationale": "User used the phrase 'I will not' and linked it directly to losses in pre-revenue speculative names. [EXPLICIT]"
}
```

**Component 3: `mandate_priority_hierarchy.trade_off_philosophy`**

A prose field capturing the user's general philosophy for resolving conflicts. This is the field the Builder reads when it faces a conflict that doesn't map cleanly to the ranked dimensions.

Write this from what the user said — not what you think is wise. Common philosophies:

"Don't lose money first, make money second — risk control is the foundation everything else is built on."

"I'd rather do fewer things really well than many things adequately. Depth beats breadth."

"Stay in my lane — I have edge in biotech and I want to exploit it fully before chasing other opportunities."

"The return target is the primary goal. I've thought hard about the risk parameters and they reflect what I can actually tolerate, but the reason I'm here is to make 15-18% per year."

Derive this from how the user talks about their priorities and what they reach for when they describe what success looks like. If they gave a direct statement about their philosophy, use their exact words.

---

## SECTION 7: CONFLICT DETECTION — WHAT TO FLAG

Beyond standard contradictions, v9.0 introduces priority-aware conflict detection. Flag these:

**Priority vs. preference conflicts:**
When a stated preference is inconsistent with the priority it was assigned. Example: user ranked diversification as rank 2, but `preference_flexibility` for diversification is `low_priority` based on how softly it was expressed. Flag for Builder to resolve.

**Immovable preferences that are mutually exclusive:**
Two `immovable` preferences that cannot both be satisfied simultaneously. Example: "must have profitable companies" + "small-cap biotech FDA plays" — most small biotech companies are pre-revenue. This is not a user error, it's a real tension the Builder needs explicit guidance on. Flag it with both sides presented fairly and a resolution hint.

**Fundamental screens that contradict the universe:**
P/E filter in a sector where P/E is typically undefined or meaningless (biotech, early-stage tech). Revenue growth floor in a mature dividend-focused universe. Flag with domain context explaining the contradiction.

**Return target vs. risk-control priority:**
When risk_control ranks highest but the return target mathematically requires taking more risk than the stated constraints allow. This is the most common high-stakes conflict. Flag it explicitly with the math: "User's return target of 25% with a 10% portfolio drawdown limit implies a Sharpe ratio of approximately 2.5, which is exceptionally high for a retail strategy portfolio. Either the return target or the risk constraint needs to flex. Given that risk_control ranks rank 1 in their priority hierarchy, the Builder should optimize for risk-adjusted return within the drawdown constraint and be transparent with the user that the 25% target may not be achievable within those bounds."

---

## SECTION 8: WHAT NOT TO DO

All v8.0 prohibitions remain. Additions:

**Do not assign `immovable` flexibility to preferences the user expressed softly.** Immovable is reserved for emphatic, explicit statements — often backed by loss history or a philosophical stance. A casual preference stated once is `low_priority` regardless of how important it might seem to you.

**Do not create a priority ranking without rationale.** Every ranked item must have a sentence explaining why it ranks where it does based on what the user said. A ranking without rationale is a guess.

**Do not resolve conflicts yourself.** Capture both sides of the conflict, flag it, and leave resolution to the Builder (guided by the priority hierarchy) or to the user at confirmation. Your job is accurate capture, not decision-making.

**Do not populate `fundamental_screens` from implied investment philosophy.** "User seems like a value investor" is not grounds for adding a P/E filter. The user must have explicitly stated a financial characteristic they require or strongly prefer.

**Do not assign all preferences the same flexibility.** If everything is `high_priority`, the priority system conveys no information. The ratings only have meaning if they are differentiated based on what the user actually expressed.

---

## SECTION 9: FINAL CHECKLIST — V9.0

**Tier 1:**
- [ ] `max_portfolio_drawdown_pct` is at or below conservative bound of what was expressed
- [ ] `leverage_permitted` is false unless explicitly requested
- [ ] `horizon_allocation` weights sum to exactly 1.0
- [ ] `account_type` populated if mentioned; downstream implications noted
- [ ] `universe_hard_filters` populated only from explicit statements or strong implied necessity

**Tier 2 — Content:**
- [ ] Every prose field reads as a complete thought, not a keyword
- [ ] Every inference labeled `[INFERRED]`; every assumption labeled `[ASSUMED]`
- [ ] `raw_desire` contains user's verbatim words
- [ ] `fundamental_screens` populated only from explicit financial characteristic preferences
- [ ] `performance_targets.success_definition` and `failure_definition` non-null
- [ ] `risk_profile` covers all sub-dimensions in full prose
- [ ] `strategy_intent.regime_universe_pairs` only contains explicitly linked pairs
- [ ] `market_context.macro_views` entries all have `user_reasoning` and `strategy_implication`

**Tier 2 — Priority system:**
- [ ] `mandate_priority_hierarchy.ordered_priorities` is populated with at least 3 ranked dimensions
- [ ] Every ranked item has a `rationale` tracing the ranking to what the user said
- [ ] `mandate_priority_hierarchy.preference_flexibility` tags applied to all significant preferences
- [ ] Flexibility ratings are differentiated — not all the same
- [ ] `mandate_priority_hierarchy.trade_off_philosophy` non-null
- [ ] Immovable ratings are reserved for emphatic, explicit statements only

**Filing notes:**
- [ ] `contradictions` captures all conflicts including priority-aware conflicts
- [ ] `expectation_corrections` captures front-running or unrealistic expectations
- [ ] `conversation_quality_note` accurately describes depth and completeness
- [ ] `explicit_vs_inferred_summary` notes where context was sparse

---

*Aegis AI v9.0 — LLM Intake Document*
*The schema you produce becomes the pipeline the user trades. Write accordingly.*
