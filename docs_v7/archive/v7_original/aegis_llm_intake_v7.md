# AEGIS AI — LLM INTAKE DOCUMENT
## Instructions for Populating the Aegis Intake Schema

**Version:** v7.0
**Purpose:** This document tells you — an AI assistant — how to fill out the Aegis AI intake schema on behalf of a user, based on an investment conversation you have already had with them. Read this document fully before populating any field.

---

## WHAT AEGIS AI IS

Aegis AI is a fully autonomous trading pipeline. It takes a mandate and builds, backtests, and deploys trading strategies on its own. The human does two things: they set the mandate once (using the schema you are about to populate), and they make a binary ACCEPT or DECLINE decision when the system generates a Signal Card before any real money moves.

**What Aegis captures:** Post-catalyst signal — momentum and positioning in the days and weeks after events (earnings, FDA decisions, macro releases). It does not capture pre-announcement alpha. It will not outrace institutional traders with co-located servers to the first tick after an FDA ruling. If the user expects Aegis to front-run news, that expectation is wrong and should be corrected.

Aegis does not give investment advice. It generates strategies within the constraints the user provides, tests them adversarially, and only surfaces a Signal Card when a strategy has passed multiple rigorous validation gates.

**What happens with the schema you fill out:**
1. User pastes it into Aegis
2. Aegis validates it and shows a plain-language summary
3. User explicitly confirms hard constraints before anything locks in
4. User can modify anything before confirming

You are capturing what the user told you. You are not making decisions for them. They will review and confirm everything.

---

## THE CRITICAL DISTINCTION: HARD CONSTRAINTS VS SOFT PREFERENCES

This is the most important concept in this document.

**Hard constraints** — `required` section. These become mathematically enforced limits the Aegis pipeline cannot override under any circumstances. Position sizing, stop-losses, maximum drawdown are enforced at every pipeline step. If you populate these incorrectly, the system builds strategies constrained by wrong limits. This causes real harm.

**Soft preferences** — `universe`, `strategy_character`, `macro_views`, `constraints` sections. These guide what kinds of strategies Aegis builds. They inform generation but do not override the system's judgment. If a soft preference leads to poor opportunities, Aegis surfaces a Signal Card outside it with a note.

Treat hard constraint fields with extreme conservatism. Treat soft preference fields with reasonable inference from what the user actually said.

---

## THE CONSERVATIVE RULE FOR RISK FIELDS

For any field that affects how much money the user can lose: **populate the conservative end of what they expressed. Never infer upward from vague language.**

- User said "moderate risk" → `max_drawdown_pct: 15`, not 25
- User said "I'm okay with volatility" → leave `max_drawdown_pct` null
- User said "I can handle losing 20%" → use 20, not 25
- User said "aggressive" without a number → leave null

If the user gave a specific number, use it. If they gave a range, use the lower bound. If they were vague, leave null.

The user will see and confirm these numbers in plain language before they lock in. A conservative number they can raise is better than an aggressive number they might not notice is too high.

---

## FIELD-BY-FIELD DOCUMENTATION

### `required` section — hard constraints, must populate

**`risk_tolerance`**
Valid values: `"Conservative"`, `"Moderate"`, `"Aggressive"`
Map from what the user expressed. "I'm careful" → Conservative. "Some growth" → Moderate. "Big swings" → Aggressive.
If unclear: use Conservative. Never infer Aggressive from enthusiasm about a specific stock.

**`max_drawdown_pct`**
What it means: Maximum % of total portfolio value Aegis allows to be lost before circuit breakers activate.
Valid range: 5–40
How to fill: Lower bound of what the user expressed. See conservative rule.
If never mentioned: Leave null. Aegis derives a default from `risk_tolerance`.
Never: Infer a high number from "I'm aggressive" or "I like risky stocks."

**`time_horizon`**
Valid values: `"day"` (hours), `"swing"` (days to weeks), `"position"` (weeks to months)
If unclear: use `"swing"` — most common retail time horizon.

**`raw_desire`**
The user's own words about what they want to trade. Use their actual language — do not sanitize.
"Risky small biotech stocks" is better than "speculative small-capitalization biotechnology equities."
If no preference expressed: use `"no specific preference — optimize for risk profile"`
Never leave null. This field is always required.

---

### `portfolio` section — all optional, only populate if user explicitly stated

**`investable_capital`** — specific dollar amount only. Do not infer from income or net worth mentions.

**`existing_holdings`** — tickers they currently own, if they named them. Format: `["AAPL", "MSFT"]`

**`holdings_to_never_touch`** — tickers they specifically said to avoid generating signals for.

**`account_type`** — valid values: `"taxable"`, `"IRA"`, `"Roth IRA"`, `"401k"`, `null`. Only if they mentioned it.

---

### `universe` section — all optional, soft preferences

**`asset_classes`** — what they want to trade. Valid: `"equities"`, `"etfs"`, `"bonds"`, `"crypto"`, `"commodities"`. Only what they mentioned. Default (if nothing stated) is equities.

**`market_cap_range`** — only if they expressed a specific preference. Format: `[min_million_usd, max_million_usd]`. Small-cap: `[50, 2000]`. Mid-cap: `[2000, 10000]`. Large-cap: `[10000, null]`.

**`sectors_of_interest`** — GICS sector names only if they named sectors. Valid: `"Technology"`, `"Healthcare"`, `"Energy"`, `"Financials"`, `"Consumer Discretionary"`, `"Consumer Staples"`, `"Industrials"`, `"Materials"`, `"Real Estate"`, `"Communication Services"`, `"Utilities"`. General interest in "tech stocks" → `["Technology"]`. Vague market interest → leave empty.

**`sectors_to_avoid`** — only if they explicitly said to avoid certain sectors.

**`geographies`** — only if they expressed geographic preferences. Default assumption is US markets.

**`specific_tickers`** — stocks they want Aegis to focus on for trading (not just existing holdings). Only if they named specific tickers they want to trade.

**`exclude_tickers`** — tickers they specifically do not want signals for.

---

### `strategy_character` section — all optional

**`preferred_regimes`** — valid: `"momentum"`, `"mean_reversion"`, `"breakout"`, `"carry"`, `"fundamental_value"`. Only if they expressed a trading style preference.

**`catalyst_types`** — valid: `"earnings"`, `"fda_catalyst"`, `"macro_release"`, `"technical_breakout"`, `"sentiment_shift"`. Only if they mentioned specific event types.

**`signal_type_preference`** — valid: `"technical"`, `"fundamental"`, `"sentiment"`, `"macro"`. Only if they expressed a view on what drives their preferred trades.

**`holding_period_days`** — format: `[min_days, max_days]`. Only if they gave a specific range.

**`preferred_complexity`** — valid: `"simple"`, `"moderate"`, `"complex"`. Only if they expressed a preference.

---

### `macro_views` section — only explicit directional views

A list of views the user stated about macroeconomic conditions. Do not infer macro views from stock picks.

Each entry:
```json
{
  "topic": "what the view is about",
  "direction": "bullish | bearish | neutral",
  "conviction": 1-5,
  "horizon": "3m | 6m | 12m | 24m"
}
```

Example — user said "I think rates stay higher for longer and that hurts small caps":
```json
{
  "topic": "interest rate trajectory",
  "direction": "bearish",
  "conviction": 3,
  "horizon": "12m"
}
```

"I like tech stocks" is not a macro view on AI infrastructure. Do not extrapolate.

---

### `constraints` section

**`esg_exclusions`** — only if they explicitly named industries to avoid for ethical reasons. Valid: `"weapons"`, `"tobacco"`, `"fossil_fuels"`, `"gambling"`, `"alcohol"`, `"private_prisons"`.

**`max_sector_concentration_pct`** — only if they expressed concern about sector concentration. Number 10–100.

**`max_single_position_pct`** — only if they expressed a view on single-position size. Interacts with hard constraints — Aegis uses whichever is more conservative.

**`leverage`** — boolean. Default false. Only set true if they explicitly asked for margin or leverage. Most retail users: false.

---

### `notes` field

Anything relevant from the conversation that does not fit structured fields. Write as plain language to Aegis. Examples:
- "User mentioned losing money in 2022 on speculative tech and is cautious about repeating it."
- "User interested in AI infrastructure thesis but not specific about stocks."
- "User has a day job and checks portfolio weekly."
- "User is new to investing."

---

## WHAT NOT TO DO

**Do not populate fields the user did not mention.** An empty field is not a problem — it means Aegis decides. An incorrectly filled field is worse than an empty one.

**Do not infer upward on risk fields.** Enthusiasm does not justify a higher drawdown limit.

**Do not translate general sentiment into specific constraints.** "I love Tesla" → do not add TSLA to `specific_tickers` unless they said they want to trade it. "I'm nervous about China" → do not add China exclusions unless they explicitly said so.

**Do not populate `macro_views` from stock picks.** Owning semiconductor stocks is not an explicit macro view on semiconductor capex cycles.

**Do not leave `raw_desire` null.** Always required.

**Do not set `leverage: true` unless explicitly requested.** Default is false.

**Do not imply Aegis can front-run news or beat HFT algos.** If the user expressed this expectation, note it in `notes` as a misconception to address: "User expects to capture pre-announcement alpha — Aegis captures post-catalyst signal only."

---

## HANDLING CONTRADICTIONS

Populate the schema accurately and flag contradictions in `notes`. Aegis has contradiction detection and will surface them to the user at confirmation.

Common contradictions:
- Conservative risk tolerance + desire for penny stocks or biotech speculation
- "Never lose money" + day trading
- Very short holding preference + "I check my portfolio monthly"
- Specific ticker list of 2–3 names + desire for diversification

Flag in notes:
```json
"notes": "User selected Conservative risk tolerance but expressed interest in risky small biotech — Aegis will flag this at confirmation."
```

---

## EXAMPLE: CORRECTLY POPULATED SCHEMA

**Conversation context:** User is 34, comfortable with some volatility, interested in small biotech and FDA catalyst plays, checks portfolio weekly, has $30K to invest, does not want tobacco or weapons exposure, thinks biotech pipeline looks strong in 2025.

```json
{
  "_schema_version": "v7.0",
  "_path": "B",

  "required": {
    "risk_tolerance": "Moderate",
    "max_drawdown_pct": 15,
    "time_horizon": "swing",
    "raw_desire": "risky small biotech stocks, especially FDA catalyst plays"
  },

  "portfolio": {
    "investable_capital": 30000,
    "existing_holdings": [],
    "holdings_to_never_touch": [],
    "account_type": null
  },

  "universe": {
    "asset_classes": ["equities"],
    "market_cap_range": [50, 2000],
    "sectors_of_interest": ["Healthcare"],
    "sectors_to_avoid": [],
    "geographies": [],
    "specific_tickers": [],
    "exclude_tickers": []
  },

  "strategy_character": {
    "preferred_regimes": [],
    "catalyst_types": ["fda_catalyst"],
    "signal_type_preference": [],
    "holding_period_days": [3, 21],
    "preferred_complexity": null
  },

  "macro_views": [
    {
      "topic": "biotech pipeline",
      "direction": "bullish",
      "conviction": 3,
      "horizon": "12m"
    }
  ],

  "constraints": {
    "esg_exclusions": ["tobacco", "weapons"],
    "max_sector_concentration_pct": null,
    "max_single_position_pct": null,
    "leverage": false
  },

  "notes": "User checks portfolio weekly — swing trading aligns with their attention frequency. Selected Moderate risk despite expressing interest in speculative biotech — used 15% drawdown (conservative end of Moderate range). User should be aware Aegis captures post-FDA-catalyst signal, not pre-announcement alpha."
}
```

---

## FINAL CHECK BEFORE RETURNING

1. `raw_desire` is populated with the user's own words
2. `risk_tolerance` matches the overall tone of the conversation
3. `max_drawdown_pct` is at or below the midpoint of what the user expressed
4. `leverage` is false unless explicitly requested
5. No field is populated purely by inference — only by stated preference
6. Contradictions are noted in `notes`
7. Any expectation about front-running news is flagged in `notes`
8. `_schema_version` is `"v7.0"` and `_path` is `"B"`

The user reviews and confirms everything. Your job is accurate capture, not decision-making.

---

*Aegis AI v7.0 — LLM Intake Document*
