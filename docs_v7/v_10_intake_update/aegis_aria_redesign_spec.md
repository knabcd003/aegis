# ARIA — INTEGRATED FORM AGENT REDESIGN
## Version 10.0 — Implementation Specification

**What changed:** Aria is no longer a sidebar chat panel. She is a 
floating card that anchors to the active field, watches the entire 
form in real time, speaks proactively and reactively, can write 
directly to form fields, and replaces the detail box with a 
conversational interface. She works alongside validation — she 
doesn't replace it, but she knows exactly what failed and why.

---

## PART 1: CONCEPTUAL MODEL

Aria is a form agent. Not a chatbot. Not a help tooltip. She is an 
expert sitting with the user who:

- Opens each section with a brief orientation before the user 
  touches anything
- Watches every field change and reacts when something matters
- Asks the questions a form cannot ask — context, reasoning, history
- Writes to Tier 2 fields automatically from what the user tells her
- Suggests Tier 1 values and waits for the user to confirm
- Knows exactly what's wrong when validation fails and explains it 
  in plain language
- Can "feel out" a field from conversation and fill it automatically 
  when the user's intent is clear enough

The user experience: you're filling out a complex institutional form 
with a senior analyst sitting next to you. She knows the form better 
than you do. She speaks when something matters. She's quiet when you 
don't need her. She never wastes your time.

---

## PART 2: VISUAL ARCHITECTURE

### The Floating Card

Aria's UI is a single floating card. It is not fixed to the sidebar. 
It is not inline between fields. It floats and anchors.

```
Anchor behavior:
  Default position: bottom-right of the active section form area
  When a field is focused: card slides to anchor beside that field
    — right side of the field if space permits
    — below the field if right side is too narrow
  When no field is focused: returns to section default position
  Transition: 200ms ease-out position change, no layout shift

Card dimensions:
  Width: 320px fixed
  Height: auto, min 120px, max 480px
  Overflow: ScrollArea (Radix) when content exceeds max height
```

### Card Anatomy

```
┌──────────────────────────────────────┐
│ ● ARIA                    [_] [×]    │  ← header
│ Section 2 — Risk Mandate             │
├──────────────────────────────────────┤
│                                      │
│  Aria's current message              │  ← message area
│  (Newsreader serif, conversational)  │
│                                      │
│  [field suggestion card if present]  │  ← optional
│                                      │
├──────────────────────────────────────┤
│  [textarea placeholder]    [Send →]  │  ← input
└──────────────────────────────────────┘
```

Header:
  Left: status dot (green = ready, amber = thinking, red = conflict)
        "ARIA" label in Inter xs uppercase tracking-widest Sage color
  Right: minimize button [_] collapses card to header-only strip
         close button [×] hides card entirely (restore via floating 
         Aria button that appears bottom-right of page)
  Below name: current section label in Inter xs muted

Message area:
  Aria's text in Newsreader serif sm, not monospace, not clinical
  Sage left border accent (2px) on the message block
  Messages replace each other — this is NOT a chat history thread
  Only the current message is shown
  Exception: if Aria asked a question and user responded, show the 
    exchange as a 2-message mini thread before the next message
  Fade transition between messages: 150ms opacity

Field suggestion card (optional, appears when Aria proposes a value):
  Rendered inside the message area when field_updates are present
  Per suggested field:
    Field label + proposed value
    "Apply" button (Sage) + "Skip" button (muted)
    Tier 1 fields: always require Apply confirmation
    Tier 2 fields: auto-applied after 3 seconds unless user clicks Skip
      Show a countdown: "Applying in 3..." that can be cancelled

Input area:
  Textarea: 2 rows, expands to 4 max
  Placeholder text is context-aware — changes per section and 
    per what Aria just asked
  Send button: arrow icon, Sage, disabled when empty or thinking
  Enter sends, Shift+Enter newlines

Minimize state:
  Card collapses to a 48px strip showing only the header
  Status dot pulses amber if Aria has something to say 
    (new message waiting behind minimize)
  Click to expand

Hidden state:
  Card disappears entirely
  Floating restore button: circular, 48px, Sage background, 
    Aria icon, bottom-right of page, z-index above everything
  Badge on restore button shows unread message count if Aria 
    has spoken while hidden

### Styling

glass-panel background
Sage/20 border (stronger than standard glass-panel to make 
  Aria visually distinct from the form fields she floats over)
backdrop-blur-xl
border-radius: 16px (more rounded than SectionShell — 
  Aria feels like a different layer)
box-shadow: 0 8px 32px rgba(0,0,0,0.4)
z-index: 50 (above form content, below modals)

---

## PART 3: TRIGGER SYSTEM

Five trigger types. Each fires a different prompt and uses a 
different model.

```typescript
type AriaTrigger =
  | 'section_enter'       // user navigates to a new section
  | 'field_focus'         // user focuses a specific field
  | 'field_change'        // a field value settles (800ms debounce)
  | 'user_message'        // user sends a message to Aria
  | 'validation_result'   // validation ran and returned results

type AriaContext = {
  trigger: AriaTrigger
  section: number
  active_field_path?: string    // for field_focus and field_change
  active_field_value?: any      // for field_change
  user_message?: string         // for user_message
  validation_errors?: string[]  // for validation_result
  validation_warnings?: string[]
  schema_state: IntakeSchemaV10 // always included — full current state
  message_history: {            // last 4 exchanges only
    role: 'aria' | 'user'
    content: string
  }[]
}
```

### Trigger Rules

SECTION_ENTER:
  Fires when currentSection changes.
  Aria introduces the section. 2-3 sentences max:
    - What this section captures
    - What the most important field is
    - One question to get the user started
  Never a generic "Welcome to Section N" — always specific.
  
  Example for Section 2:
  "Let's set your risk limits. The drawdown cap is the single 
  most important number in your mandate — everything else derives 
  from it. What's the maximum total loss you could sustain before 
  losing confidence in the system?"

FIELD_FOCUS:
  Fires when a field receives focus.
  Aria explains the field in plain language IF it is a field 
    that a regular user might not understand.
  Silent for self-explanatory fields (e.g. "Brokerage" text input).
  Active for fields like max_position_as_pct_of_adv, 
    regret_asymmetry, loss_aversion_coefficient, 
    horizon_allocation, catalyst acknowledgments.
  Max 2 sentences. No input required from user.

FIELD_CHANGE:
  800ms debounce after value settles.
  Aria only speaks if the change is notable:
    - Value creates or resolves a cross-section conflict
    - Value is at an extreme that deserves acknowledgment
      (e.g. max_portfolio_drawdown_pct = 5 with biotech enabled)
    - Value contradicts something else already set
    - Value unlocks or blocks a downstream field
  Silent for routine changes (moving a slider from 15 to 18).
  When Aria speaks: 1-2 sentences, specific to what changed.

USER_MESSAGE:
  User sent text to Aria.
  Aria processes the message in context of:
    - Current section and its field spec
    - Current schema state (what's already filled)
    - Message history (last 4 exchanges)
  Aria may:
    - Answer a question about a field
    - Extract field values from what the user said and propose them
    - Update Tier 2 prose fields directly
    - Ask a follow-up question
    - Confirm what she understood
  This is the primary mechanism for populating Tier 2 fields.

VALIDATION_RESULT:
  Fires after the validate button is pressed and results return.
  Aria receives the errors and warnings array.
  She explains each issue in plain language — not the raw 
    field path, not the schema error message.
  For blocking errors: specific, direct, tells user exactly 
    what to fix and where.
  For warnings: acknowledges them, explains the trade-off, 
    asks if the user wants to address them.
  Never says "validation failed" — explains what and why.
  
  Example:
  Not: "max_portfolio_drawdown_pct: required field missing"
  Yes: "You haven't set a drawdown limit yet — it's the first 
  slider in this section. This is required before you can lock."

---

## PART 4: FIELD INTELLIGENCE

This is what makes Aria a form agent rather than a chatbot. She 
understands what every field means, what good values look like, 
what bad values look like, and can suggest or populate values 
from conversational input.

### Field Knowledge Map

Aria's system prompt includes a field knowledge map — a structured 
description of every field that tells her:
- What it is in plain English
- What a typical range looks like
- What extreme values imply
- What fields it interacts with
- Whether she can auto-fill it from conversation

```
FIELD: max_portfolio_drawdown_pct
plain_language: "The maximum total loss from the portfolio's peak 
  value before the system stops trading completely"
typical_range: "10-25% for most retail investors"
extreme_low: "Below 8% is very restrictive and may conflict with 
  binary catalyst types that carry overnight gap risk"
extreme_high: "Above 35% suggests high risk tolerance — verify 
  this is intentional"
interacts_with: [max_daily_loss_pct, drawdown_breach_protocol, 
  catalyst_types, target_annual_return_pct]
aria_can_extract: true
extraction_cue: "user mentions a specific percentage loss they 
  could tolerate, or references a past loss experience with a number"

FIELD: regret_asymmetry.type
plain_language: "Whether missing a winner or holding a loser 
  bothers the user more — directly controls how exits are designed"
aria_can_extract: true
extraction_cue: "user describes emotional response to winning 
  or losing trades, or mentions specific experiences"
builder_impact: "loss_regret_dominant → time-based exits enforced. 
  miss_regret_dominant → trailing stops, maximum continuation"

FIELD: horizon_allocation
plain_language: "How capital is split across different holding 
  period windows — 5-21 days, 21-63 days, etc."
aria_can_extract: false  — requires structured input, too complex
  to reliably extract from conversation
aria_can_suggest: true   — can suggest a preset based on 
  catalyst types selected

FIELD: loss_aversion_coefficient
plain_language: "How much worse losing feels compared to winning 
  the same amount"
aria_can_extract: true
extraction_cue: "user describes emotional asymmetry between 
  gains and losses"

FIELD: volatility_tolerance (Tier 2 prose)
aria_auto_fills: true    — from any description of risk comfort
no_confirmation_needed: true  — Tier 2, auto-apply

FIELD: sector_reasoning (Tier 2 prose)
aria_auto_fills: true    — from why user selected sectors
no_confirmation_needed: true
```

The full field knowledge map covers all fields in all 10 sections 
and is embedded in Aria's system prompt.

### Auto-Fill Behavior

Tier 2 prose fields:
  Aria fills these automatically from conversation.
  No confirmation card shown.
  Fields update silently in the store.
  Aria may mention what she captured: "I've noted your preference 
  for healthcare based on your background — I'll use that context 
  when the Builder selects strategies."

Tier 2 structured fields (enums, numbers):
  Aria proposes via a suggestion card.
  Auto-applies after 3-second countdown unless user clicks Skip.
  Example: user says "losses hit me really hard, way more than 
    gains" → Aria suggests loss_aversion_coefficient: severe_4plus_to_1
    with a 3-second auto-apply.

Tier 1 fields:
  Aria ALWAYS shows a confirmation card.
  Never auto-applies.
  Never times out.
  User must click Apply explicitly.
  Aria may suggest a specific number: "Based on what you described, 
    a 15% drawdown limit sounds right. Want me to set that?"
  The suggestion card shows the field label, proposed value, 
    and a plain-language explanation of what it means.

### The "Feel Out" Mechanism

When a user cannot express a value numerically but describes their 
situation clearly, Aria derives a value:

User: "I'd be pretty upset if I lost more than like... a month's 
  salary. I make about $8,000 a month and this is $150K."

Aria processes:
  $8,000 / $150,000 = 5.3% of investable capital
  Suggests: max_portfolio_drawdown_pct = 5
  With explanation: "A month's salary on $150K is about 5%. 
    That's on the tighter end — it means the system stops if 
    it loses $7,500. Does that feel right?"

User: "I tend to panic when I see red. Like, I check my phone 
  constantly and start second-guessing everything."

Aria processes:
  → regret_asymmetry.type = loss_regret_dominant
  → loss_aversion_coefficient = elevated_3to1 or severe_4plus_to_1
  → overtrading_tendency = frequent (checking constantly)
  → behavioral_constraints_during_drawdown (Tier 2, auto-fill)
  Proposes Tier 2 structured fields, auto-fills prose.

---

## PART 5: DETAIL BOX REPLACEMENT

The static detail box textarea is removed from all sections. 
Aria replaces it.

Instead of a fixed prompt at the bottom of each section, Aria 
asks the context questions conversationally after the user has 
filled the structured fields.

### Flow per section:

1. User enters section → Aria gives orientation (SECTION_ENTER)
2. User fills structured fields → Aria reacts to notable changes
3. When all required Tier 1 fields in the section are filled:
   Aria transitions to context questions:
   "Good — the hard numbers are set. Now I want to understand 
   the reasoning behind them. [first context question]"
4. User responds in conversation → Aria extracts Tier 2 prose 
   fields and proposes structured field updates
5. When Aria is satisfied with context coverage, she signals:
   "I have everything I need for this section. You can validate 
   and lock when ready."
6. User clicks Validate → validation runs → Aria explains results

### Context questions per section (Aria asks these, not a textarea):

Section 1:
  "Tell me about your existing portfolio — what else are you 
  holding and what role do you want Aegis to play?"

Section 2:
  "Walk me through a time a trade went badly for you — how did 
  you react and what did you wish you'd done differently?"

Section 3:
  "What would make you shut this system down? Not a number — 
  what would actually make you pull the plug?"

Section 4:
  "Why these sectors? What do you know about them that the 
  market might be missing?"

Section 5:
  "How do you think about getting into and out of trades? 
  What have you tried before and what did you learn?"

Section 6:
  "Walk me through a typical trading day — when are you actually 
  free to act, and how quickly can you move when you need to?"

Section 7:
  "What patterns have you noticed in yourself when trading gets 
  stressful? Be honest — what do you actually do versus what 
  you know you should do?"

Section 8:
  "Any legal constraints I should know about — blackout periods, 
  employer restrictions, anything like that?"

Section 9:
  "What's your read on the market right now? What do you think 
  is happening and how should Aegis position in response?"

Section 10:
  "When the system has to give something up to get something 
  else — what should it always protect, no matter what?"

---

## PART 6: SYSTEM PROMPT ARCHITECTURE

The system prompt is assembled per API call. Five parts.

### Part 1 — Identity and Rules (static)

```
You are Aria, an expert intake agent for the Aegis autonomous 
trading system. You are helping a user configure their investment 
mandate. You speak like a senior analyst who has done thousands 
of these sessions — precise, efficient, direct, human.

RULES:
1. You never set a Tier 1 field without explicit user confirmation. 
   You may suggest a value but always wait for Apply.
2. You set Tier 2 prose fields automatically from conversation. 
   You set Tier 2 structured fields with a 3-second auto-apply.
3. You never say "Great question", "I'd be happy to help", or 
   any variant. You just answer.
4. You never mention schema field names or JSON paths to the user.
   Translate everything to plain language.
5. You keep messages short. 2-4 sentences max unless explaining 
   a conflict. The user is filling a form, not reading an essay.
6. When you detect a conflict, say so immediately and specifically.
   "You've excluded healthcare from your universe but enabled FDA 
   catalyst types — these are mutually exclusive." Not "there may 
   be a potential conflict to consider."
7. When validation fails, explain each issue in plain language 
   with the specific fix. Never say "validation failed."
8. You respond in JSON. See output format below.
```

### Part 2 — Field Knowledge Map (static)

Full field knowledge map as described in Part 4. Every field, 
every section, with plain_language, typical_range, extreme notes, 
interaction dependencies, aria_can_extract, aria_auto_fills.

### Part 3 — Current Schema State (dynamic)

```json
CURRENT MANDATE STATE:
{schema_state_json}

Fields that are set: {list of non-null field paths}
Fields still needed (Tier 1, current section): {list}
```

### Part 4 — Current Trigger Context (dynamic)

```
TRIGGER: {trigger_type}
ACTIVE SECTION: {section_number} — {section_name}
{if field_focus or field_change}
  ACTIVE FIELD: {field_path}
  FIELD VALUE: {value}
  FIELD PLAIN NAME: {plain_language name}
{if user_message}
  USER SAID: "{user_message}"
{if validation_result}
  VALIDATION ERRORS (blocking): {errors}
  VALIDATION WARNINGS: {warnings}
```

### Part 5 — Message History (dynamic)

```
RECENT EXCHANGE (last 4 messages):
Aria: "..."
User: "..."
Aria: "..."
User: "..."
```

### Output Format

Every Aria API response is structured JSON:

```typescript
interface AriaResponse {
  message: string           // what Aria says — plain language, 
                            // no field paths, no JSON
  
  field_updates?: {
    path: string            // dot-notation schema path
    value: any
    tier: 1 | 2
    plain_label: string     // human-readable field name
    plain_value: string     // human-readable value description
    auto_apply: boolean     // true for Tier 2, false for Tier 1
    auto_apply_delay_ms?: number  // default 3000 for Tier 2 structured
  }[]

  questions?: string[]      // follow-up questions Aria is asking
                            // (rendered as suggestion chips below 
                            // the input, user can tap or type)

  conflicts?: {
    description: string     // plain language conflict description
    severity: 'blocking' | 'warning' | 'advisory'
    fields_involved: string[] // plain names, not schema paths
    suggested_resolution: string
  }[]

  section_context_complete?: boolean  // Aria signals she has 
                                      // enough context for this 
                                      // section — shifts UI to 
                                      // show validate button 
                                      // more prominently

  aria_thinking?: string    // shown during streaming if supported
                            // "Looking at your risk settings..."
}
```

---

## PART 7: MODEL ROUTING

```
SECTION_ENTER      → Llama 4 Scout (Groq)
  Low complexity. Static orientation. Fast response critical —
  user just navigated and expects immediate presence.

FIELD_FOCUS        → Llama 4 Scout (Groq)
  Simple field explanation. 2 sentences. Fast.

FIELD_CHANGE       → Llama 4 Scout (Groq)
  Reactive comment. Often silent. Fast.
  Exception: if conflict detected → Qwen3 32B (Groq)
  Conflicts require more reasoning.

USER_MESSAGE       → Qwen3 32B (Groq)
  Conversational response + field extraction.
  Needs capability for nuanced interpretation.
  If message contains behavioral description or emotional 
    content → Cerebras Qwen3 235B for more accurate extraction.

VALIDATION_RESULT  → Qwen3 32B (Groq)
  Explain validation errors. Needs context and reasoning.
  If multiple blocking errors → Cerebras Qwen3 235B
  Complex multi-error explanations need more capability.
```

---

## PART 8: ARIA COMPONENT SPEC

```
Build AriaCard.tsx — the floating Aria agent card.

Props:
  currentSection: number
  schemaState: IntakeSchemaV10
  activeFieldPath: string | null    — currently focused field
  onFieldUpdate: (update: AriaFieldUpdate) => void
  onConflict: (conflict: AriaConflict) => void
  validationResult: ValidationResult | null  — populated after 
    validate button is pressed, null otherwise

Types:
  AriaFieldUpdate {
    path: string
    value: any
    tier: 1 | 2
    auto_apply: boolean
    auto_apply_delay_ms?: number
  }

  AriaConflict {
    description: string
    severity: 'blocking' | 'warning' | 'advisory'
    fields_involved: string[]
    suggested_resolution: string
  }

  ValidationResult {
    errors: string[]    — blocking, plain language
    warnings: string[]  — non-blocking, plain language
  }

Internal state (the only local state permitted):
  position: {x: number, y: number}  — current card position
  isMinimized: boolean
  isHidden: boolean
  currentMessage: AriaResponse | null
  messageHistory: {role: 'aria'|'user', content: string}[]
  inputText: string
  isThinking: boolean
  pendingAutoApplies: PendingAutoApply[]  — Tier 2 field updates 
    with countdown timers

  PendingAutoApply {
    update: AriaFieldUpdate
    applyAt: number  — timestamp
    cancelled: boolean
  }

Position logic:
  On mount: position at bottom-right of form area
  On activeFieldPath change: 
    Find the DOM element for that field path
    Calculate position: right side of element if viewport 
      width allows (element.right + 340 < window.width)
      Otherwise below the element
    Animate to new position: 200ms ease-out
    If field is in the bottom 30% of viewport: 
      position card above the field instead of below
  On minimize: stay in current x, collapse to 48px height
  On hide: fade out, show restore FAB

Trigger logic (internal):
  On mount: fire SECTION_ENTER for currentSection
  On currentSection prop change: fire SECTION_ENTER
  On activeFieldPath prop change (non-null): 
    fire FIELD_FOCUS with debounce 100ms
  On schemaState prop change:
    Diff against previous schemaState
    If a field changed: fire FIELD_CHANGE after 800ms debounce
    Cancel pending FIELD_CHANGE if another change arrives 
      within 800ms
  On validationResult prop change (non-null):
    fire VALIDATION_RESULT immediately
    Cancel any pending FIELD_CHANGE debounce

API call logic:
  Every trigger fires POST /api/aria with AriaContext
  Set isThinking = true before call
  Set isThinking = false on response
  Update currentMessage with response
  Process field_updates from response:
    Tier 1: add to confirmation queue (shown in card)
    Tier 2 prose: call onFieldUpdate immediately
    Tier 2 structured: start PendingAutoApply countdown
  Process conflicts: call onConflict for each
  Append to messageHistory (Aria side)

Auto-apply countdown UI:
  For each PendingAutoApply in state:
    Show in message area below main message:
    "[Field label]: [plain value]"
    Countdown: "Applying in 3..." animated
    "Cancel" link that sets cancelled = true
    On timer expiry if not cancelled: call onFieldUpdate

Tier 1 confirmation card UI:
  Shown in message area, persists until user acts:
  "[Field label]"
  "[Plain value description]"
  [Apply] button — Sage background
  [Skip] button — muted ghost
  Apply: call onFieldUpdate, remove card
  Skip: remove card, Aria does not re-propose 
    the same value in this session unless 
    schema context changes

Input area behavior:
  Textarea placeholder changes based on context:
    After SECTION_ENTER: "Tell Aria about your situation..."
    After field focus on complex field: 
      "Ask Aria what this means..."
    After Aria asks a question: "Your answer..."
    Default: "Ask Aria anything..."
  On send:
    Append to messageHistory (user side)
    Fire USER_MESSAGE trigger with inputText
    Clear inputText

Question chips:
  If AriaResponse includes questions array:
    Render as tappable chips above the input
    Max 3 chips shown
    Tapping a chip fills the input with that text 
      and immediately sends
    Chips disappear after user sends any message

Conflicts display:
  Conflicts from AriaResponse are displayed as 
    inline banners in the message area BELOW the 
    main message text:
    blocking: Terracotta/20 background, 
      Lucide AlertOctagon, Terracotta text
    warning: amber/15 background, 
      Lucide AlertTriangle, amber text
    advisory: white/10 background, 
      Lucide Info, muted text
  Each banner shows: description + suggested_resolution
  Conflicts persist in the card across messages 
    until the underlying field is corrected
  When conflict is resolved (schema state changes 
    to eliminate it): banner fades out

Restore FAB (shown when isHidden = true):
  Position: fixed, bottom-24px, right-24px
  Size: 48px circular
  Background: Sage/90
  Icon: custom Aria icon or Lucide Bot
  z-index: 60
  Badge: shows count of messages received while hidden
  Click: set isHidden = false, animate card back in

Section context complete indicator:
  When AriaResponse.section_context_complete = true:
    Show a subtle banner at bottom of card:
    "Ready to validate →" in Sage
    This doesn't trigger validation — just signals 
      Aria is satisfied
    The validate button in SectionShell becomes 
      more prominent (remove muted styling, 
      full Sage background)

Streaming support (optional, implement if backend supports):
  If backend streams the response:
    Show aria_thinking text while streaming
    Update currentMessage.message as tokens arrive
    Process field_updates only when stream completes
```

---

## PART 9: INTEGRATION INTO INTAKEPAGEV10

```
IntakePageV10.tsx changes:

1. Remove AgentPanel (the old sidebar) entirely

2. Add AriaCard as a single instance at the page level:
   <AriaCard
     currentSection={currentSection}
     schemaState={schema}
     activeFieldPath={activeFieldPath}
     onFieldUpdate={handleAriaFieldUpdate}
     onConflict={handleAriaConflict}
     validationResult={lastValidationResult}
   />

3. Add activeFieldPath state:
   Track which field is currently focused across 
   all section components.
   Each field component calls a shared 
   onFieldFocus(path: string) callback on focus 
   and onFieldBlur() on blur.
   Store in IntakePageV10 state: 
   const [activeFieldPath, setActiveFieldPath] = useState<string|null>(null)

4. Pass onFieldFocus and onFieldBlur down to all 
   section components as props.
   Each field that should trigger Aria must call 
   onFieldFocus with its schema path on focus.

5. Add lastValidationResult state:
   const [lastValidationResult, setLastValidationResult] = 
     useState<ValidationResult | null>(null)
   Populate this when section validation runs and returns.
   Pass to AriaCard.

6. handleAriaFieldUpdate:
   Receives AriaFieldUpdate from AriaCard.
   Calls store.updateField(update.path, update.value).
   This is the same updateField used by the form — 
   Aria writes to the same store the form writes to.
   The form fields re-render automatically since 
   they read from the store.

7. handleAriaConflict:
   Receives AriaConflict from AriaCard.
   Stores in local conflict state for display if needed 
   at page level (e.g. blocking section lock).
   Passes blocking conflicts to canLockSection validators.

8. Remove detail box components from all section 
   components. Aria replaces them.
   Remove the static "Detail Box" prompt textareas.
   Remove the static Validate-triggers-LLM flow that 
   was specced for the detail box.
```

---

## PART 10: API ENDPOINT

```
POST /api/aria

Request:
{
  trigger: AriaTrigger
  section: number
  active_field_path?: string
  active_field_value?: any
  user_message?: string
  validation_errors?: string[]
  validation_warnings?: string[]
  schema_state: IntakeSchemaV10
  message_history: {role: 'aria'|'user', content: string}[]
}

Response: AriaResponse (see Part 6 output format)

Model selection: server-side based on trigger type 
  (see Part 7 model routing)

System prompt assembly: server-side, Parts 1-5 of 
  system prompt structure

Timeout: 8 seconds. If exceeded:
  Return a safe fallback response:
  { message: "Take your time — I'm here when you're ready." }
  No field_updates in fallback.

Rate limiting per session:
  FIELD_CHANGE: max 1 call per 800ms (enforced client-side 
    by debounce — server enforces as backup)
  USER_MESSAGE: max 10 per minute per session
  SECTION_ENTER, FIELD_FOCUS: no limit
  VALIDATION_RESULT: max 5 per minute per section
```

---

## PART 11: FIELDS THAT SHOULD TRIGGER ARIA ON FOCUS

Not every field needs a FIELD_FOCUS explanation. Only fields 
a regular user cannot be expected to understand intuitively.

```
Section 1:
  investor_sophistication  — explain what each level means 
                             for the system's behavior
  aegis_capital_as_pct    — explain why this matters

Section 2:
  max_portfolio_drawdown_pct    — most important field, always explain
  max_daily_loss_pct            — explain reference point (starting NAV)
  drawdown_breach_protocol      — explain each option's implications
  max_position_as_pct_of_adv   — explain market impact concept
  regret_asymmetry              — explain builder impact
  target_portfolio_beta         — explain what beta means in this context

Section 3:
  return_character.smoothness_preference — explain the trade-off
  min_acceptable_sharpe          — explain what Sharpe ratio means

Section 4:
  restrict_to_sectors_of_interest — explain hard filter vs preference
  min_avg_daily_volume_usd        — explain liquidity and why it matters
  fundamental_screens             — explain applies_to_catalyst_types

Section 5:
  All catalyst type cards          — explain each when expanded
  horizon_allocation               — explain drift windows concept
  HorizonAllocationBuilder presets — explain what each preset implies

Section 6:
  max_execution_latency_minutes — explain how it affects strategy design
  automation_level              — explain what each mode means operationally

Section 7:
  loss_aversion_coefficient     — explain builder impact
  disposition_effect_tendency   — explain builder impact
  overtrading_tendency          — explain signal friction mechanism
  cooling_off_requirements      — explain what the system does

Section 8:
  account_tax_status            — explain strategy implications
  short_term_gains_tolerance    — explain STCG rate implications
  specific_tax_lot_method       — explain each method

Section 9:
  market_beta_intent            — explain what beta means for the mandate
  regime_adaptivity_intent      — explain adaptive vs consistent

Section 10:
  DragToRankList immovable      — explain Tier 2-Hard concept in plain terms
  drawdown review threshold     — explain the computed trigger value
```

Fields NOT on this list: brokerage text input, ticker inputs,
toggle fields with self-explanatory labels, percentage sliders 
with clear labels and helpers already shown.

---

*Aria Integrated Form Agent — v10.0 Redesign Specification*
*Replaces: AgentPanel.tsx (sidebar), all static detail box textareas*
*New component: AriaCard.tsx*
*Modified: IntakePageV10.tsx, all section components (remove detail boxes, add onFieldFocus)*
