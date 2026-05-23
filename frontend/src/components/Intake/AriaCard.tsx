import { useState, useEffect, useRef } from 'react';
import { Bot, X, Minimize2, Maximize2, AlertTriangle, Send, ChevronRight } from 'lucide-react';
import type { IntakeSchemaV10 } from '../../types/intake';

const API_URL = 'http://localhost:8000/api/aria';

interface PendingUpdate {
  id: string;
  path: string;
  value: any;
  tier: number;
  plain_label: string;
  plain_value: string;
  auto_apply: boolean;
  countdown: number;
}

interface ConflictEntry {
  description: string;
  severity: 'blocking' | 'warning' | 'advisory';
  fields_involved: string[];
  suggested_resolution: string;
}

interface ChatMessage {
  role: 'aria' | 'user';
  content: string;
}

interface AriaCardProps {
  currentSection: number;
  schemaState: IntakeSchemaV10;
  activeFieldPath: string | null;
  activeFieldLabel?: string | null;
  validationResult?: { errors: string[]; warnings: string[] } | null;
  onFieldUpdate?: (path: string, value: any) => void;
  onConflict?: (conflict: ConflictEntry) => void;
}

// Map field paths to human-readable labels (mirrors backend FIELD_GUIDANCE keys)
const FIELD_LABELS: Record<string, string> = {
  'mandate_identification.investor_sophistication': 'Investor Sophistication',
  'mandate_identification.account_type': 'Account Type',
  'mandate_identification.mandate_role': 'Portfolio Role',
  'capital_structure.investable_capital_usd': 'Investable Capital',
  'capital_structure.leverage_permitted': 'Leverage Permitted',
  'capital_structure.reserved_cash_pct': 'Reserved Cash Buffer',
  'capital_structure.max_deployed_pct': 'Max Capital Deployed',
  'risk_mandate.tier_1_risk_constraints.max_portfolio_drawdown_pct': 'Max Portfolio Drawdown',
  'risk_mandate.tier_1_risk_constraints.max_daily_loss_pct': 'Daily Loss Circuit Breaker',
  'risk_mandate.tier_1_risk_constraints.drawdown_breach_protocol': 'Drawdown Breach Protocol',
  'risk_mandate.tier_1_risk_constraints.max_single_position_pct': 'Max Position Size (%)',
  'risk_mandate.tier_1_risk_constraints.max_single_position_usd': 'Max Position Size ($)',
  'risk_mandate.tier_1_risk_constraints.max_sector_concentration_pct': 'Max Sector Concentration',
  'risk_mandate.tier_1_risk_constraints.max_concurrent_live_strategies': 'Max Concurrent Strategies',
  'return_mandate.primary_objective': 'Primary Objective',
  'return_mandate.target_annual_return_pct': 'Target Annual Return',
  'return_mandate.benchmark': 'Benchmark',
  'universe_mandate.tier_1_hard_filters.asset_classes_permitted': 'Permitted Asset Classes',
  'universe_mandate.tier_1_hard_filters.min_avg_daily_volume_usd': 'Minimum Liquidity Floor',
  'universe_mandate.tier_1_hard_filters.geographies_permitted': 'Geographies Permitted',
  'strategy_mandate.catalyst_types': 'Catalyst Event Types',
  'operational_mandate.tier_1_operational_constraints.automation_level': 'Automation Level',
  'operational_mandate.tier_1_operational_constraints.max_execution_latency_minutes': 'Max Execution Latency',
  'behavioral_profile.loss_aversion_coefficient': 'Loss Aversion Level',
  'tax_and_legal.account_tax_status': 'Account Tax Status',
  'tax_and_legal.marginal_tax_rate_pct': 'Marginal Tax Rate',
  'portfolio_scope_and_macro.regime_adaptivity_intent': 'Regime Adaptivity',
  'governance_and_review.mandate_review_frequency': 'Mandate Review Frequency',
};

function fieldLabel(path: string | null): string | null {
  if (!path) return null;
  return FIELD_LABELS[path] ?? path.split('.').pop()?.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()) ?? null;
}

function deepDiff(a: any, b: any, path = ''): { path: string; value: any } | null {
  if (a === b) return null;
  if (!a || !b || typeof a !== 'object' || typeof b !== 'object') return { path, value: b };
  for (const key of Object.keys(b)) {
    const p = path ? `${path}.${key}` : key;
    const diff = deepDiff(a[key], b[key], p);
    if (diff) return diff;
  }
  return null;
}

export function AriaCard({
  currentSection,
  schemaState,
  activeFieldPath,
  validationResult,
  onFieldUpdate,
  onConflict,
}: AriaCardProps) {
  const [isMinimized, setIsMinimized] = useState(false);
  const [isHidden, setIsHidden] = useState(false);
  const [isThinking, setIsThinking] = useState(false);
  const [inputText, setInputText] = useState('');

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [pendingUpdates, setPendingUpdates] = useState<PendingUpdate[]>([]);
  const [chips, setChips] = useState<string[]>([]);
  const [conflicts, setConflicts] = useState<ConflictEntry[]>([]);

  // Track schema changes but suppress when Aria itself applied a change
  const prevSchemaRef = useRef<IntakeSchemaV10>(schemaState);
  const suppressNextChangeRef = useRef(false);

  // Track which section we've already greeted
  const lastGreetedSection = useRef<number>(0);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => { scrollToBottom(); }, [messages, isThinking]);

  // ── Core: call the Aria API ────────────────────────────────────────────────
  const callAria = async (
    trigger: string,
    extra?: { fieldPath?: string; fieldValue?: any; userMessage?: string }
  ) => {
    setIsThinking(true);
    try {
      const history = messages.slice(-6).map(m => ({ role: m.role, content: m.content }));

      const payload = {
        trigger,
        section: currentSection,
        active_field_path: extra?.fieldPath ?? activeFieldPath ?? undefined,
        active_field_value: extra?.fieldValue !== undefined ? extra.fieldValue : undefined,
        user_message: extra?.userMessage,
        validation_errors: validationResult?.errors,
        validation_warnings: validationResult?.warnings,
        schema_state: schemaState,
        message_history: history,
      };

      const res = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!res.ok) throw new Error(`Aria API ${res.status}`);
      const data = await res.json();

      if (data.message) {
        setMessages(prev => [...prev, { role: 'aria', content: data.message }]);
      }

      if (data.questions?.length) setChips(data.questions.slice(0, 3));
      else setChips([]);

      if (data.conflicts?.length) {
        setConflicts(data.conflicts);
        data.conflicts.forEach((c: ConflictEntry) => onConflict?.(c));
      } else {
        setConflicts([]);
      }

      if (data.field_updates?.length) {
        const newUpdates: PendingUpdate[] = data.field_updates.map((u: any) => ({
          id: Math.random().toString(36).slice(2),
          path: u.path,
          value: u.value,
          tier: u.tier,
          plain_label: u.plain_label,
          plain_value: u.plain_value,
          auto_apply: !!u.auto_apply,
          countdown: u.auto_apply && u.tier === 2 ? 4 : -1,
        }));
        setPendingUpdates(prev => {
          const filtered = prev.filter(p => !newUpdates.some(n => n.path === p.path));
          return [...filtered, ...newUpdates];
        });
      }
    } catch (err) {
      console.error('Aria error:', err);
    } finally {
      setIsThinking(false);
    }
  };

  // ── Trigger: section_enter (only fire once per section) ───────────────────
  useEffect(() => {
    if (currentSection === lastGreetedSection.current) return;
    lastGreetedSection.current = currentSection;
    callAria('section_enter');
  }, [currentSection]);

  // ── Trigger: field_focus (debounced 150ms) ────────────────────────────────
  const fieldFocusTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  useEffect(() => {
    if (!activeFieldPath) return;
    if (fieldFocusTimer.current) clearTimeout(fieldFocusTimer.current);
    fieldFocusTimer.current = setTimeout(() => {
      callAria('field_focus', { fieldPath: activeFieldPath });
    }, 150);
    return () => { if (fieldFocusTimer.current) clearTimeout(fieldFocusTimer.current); };
  }, [activeFieldPath]);

  // ── Trigger: field_change (debounced 1s, suppressed after Aria applies) ──
  const fieldChangeTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  useEffect(() => {
    const prev = prevSchemaRef.current;
    if (prev === schemaState) return;

    if (suppressNextChangeRef.current) {
      suppressNextChangeRef.current = false;
      prevSchemaRef.current = schemaState;
      return;
    }

    const diff = deepDiff(prev, schemaState);
    prevSchemaRef.current = schemaState;

    if (!diff) return;

    if (fieldChangeTimer.current) clearTimeout(fieldChangeTimer.current);
    fieldChangeTimer.current = setTimeout(() => {
      callAria('field_change', { fieldPath: diff.path, fieldValue: diff.value });
    }, 1000);
    return () => { if (fieldChangeTimer.current) clearTimeout(fieldChangeTimer.current); };
  }, [schemaState]);

  // ── Trigger: validation_result ────────────────────────────────────────────
  const lastValidationRef = useRef<string>('');
  useEffect(() => {
    if (!validationResult) return;
    const key = JSON.stringify(validationResult);
    if (key === lastValidationRef.current) return;
    lastValidationRef.current = key;
    if (validationResult.errors.length > 0 || validationResult.warnings.length > 0) {
      callAria('validation_result');
    }
  }, [validationResult]);

  // ── Countdown timer for Tier 2 auto-apply ────────────────────────────────
  useEffect(() => {
    const interval = setInterval(() => {
      setPendingUpdates(prev => {
        const next = prev.map(p =>
          p.auto_apply && p.countdown > 0 ? { ...p, countdown: p.countdown - 1 } : p
        );
        next.forEach(p => {
          if (p.auto_apply && p.countdown === 0 && onFieldUpdate) {
            suppressNextChangeRef.current = true;
            onFieldUpdate(p.path, p.value);
          }
        });
        return next.filter(p => !(p.auto_apply && p.countdown === 0));
      });
    }, 1000);
    return () => clearInterval(interval);
  }, [onFieldUpdate]);

  const applyUpdate = (id: string, path: string, value: any) => {
    suppressNextChangeRef.current = true;
    onFieldUpdate?.(path, value);
    setPendingUpdates(prev => prev.filter(p => p.id !== id));
  };

  const dismissUpdate = (id: string) => {
    setPendingUpdates(prev => prev.filter(p => p.id !== id));
  };

  const handleSend = (e?: React.FormEvent, chip?: string) => {
    e?.preventDefault();
    const text = chip ?? inputText.trim();
    if (!text) return;
    setMessages(prev => [...prev, { role: 'user', content: text }]);
    if (!chip) setInputText('');
    setChips([]);
    callAria('user_message', { userMessage: text });
  };

  const activeLabel = fieldLabel(activeFieldPath);

  if (isHidden) {
    return (
      <button
        onClick={() => setIsHidden(false)}
        className="fixed bottom-6 right-6 w-12 h-12 rounded-full bg-[#ACCEC5] flex items-center justify-center shadow-xl hover:scale-105 transition-all z-50"
        title="Open Aria"
      >
        <Bot size={20} className="text-[#151512]" />
      </button>
    );
  }

  const conflictColor = (s: string) =>
    s === 'blocking' ? 'bg-red-500/10 border-red-500/20 text-red-400' :
    s === 'warning' ? 'bg-amber-500/10 border-amber-500/20 text-amber-400' :
    'bg-white/5 border-white/10 text-[#8e8e88]';

  return (
    <div className="fixed right-0 top-0 h-screen w-[340px] z-40 flex flex-col bg-[#111110] border-l border-[#8e8e88]/10">
      {/* ── Header ── */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-[#8e8e88]/10 flex-shrink-0">
        <div className="flex items-center gap-2.5">
          <div className={`w-2 h-2 rounded-full flex-shrink-0 ${isThinking ? 'bg-amber-400 animate-pulse' : 'bg-[#ACCEC5]'}`} />
          <div>
            <span className="text-[11px] font-bold uppercase tracking-[0.18em] text-[#ACCEC5]">Aria</span>
            {activeLabel && !isThinking && (
              <p className="text-[10px] text-[#8e8e88] leading-none mt-0.5 truncate max-w-[180px]">
                {activeLabel}
              </p>
            )}
            {isThinking && (
              <p className="text-[10px] text-amber-400/70 leading-none mt-0.5">thinking…</p>
            )}
          </div>
        </div>
        <div className="flex items-center gap-1">
          <button onClick={() => setIsMinimized(v => !v)} className="p-1.5 hover:bg-white/5 rounded text-[#8e8e88] transition-colors">
            {isMinimized ? <Maximize2 size={13} /> : <Minimize2 size={13} />}
          </button>
          <button onClick={() => setIsHidden(true)} className="p-1.5 hover:bg-white/5 rounded text-[#8e8e88] transition-colors">
            <X size={13} />
          </button>
        </div>
      </div>

      {!isMinimized && (
        <>
          {/* ── Conflict banners ── */}
          {conflicts.length > 0 && (
            <div className="px-3 pt-3 space-y-2 flex-shrink-0">
              {conflicts.map((c, i) => (
                <div key={i} className={`px-3 py-2 rounded-lg border text-[11px] ${conflictColor(c.severity)}`}>
                  <div className="flex items-center gap-1.5 font-bold uppercase tracking-wider text-[9px] mb-1">
                    <AlertTriangle size={11} />
                    <span>{c.severity}</span>
                  </div>
                  <p className="font-medium leading-snug">{c.description}</p>
                  <p className="text-[10px] opacity-70 mt-0.5">{c.suggested_resolution}</p>
                </div>
              ))}
            </div>
          )}

          {/* ── Chat messages ── */}
          <div className="flex-1 overflow-y-auto px-4 py-3 space-y-4 min-h-0">
            {messages.length === 0 && !isThinking && (
              <div className="text-center pt-12 space-y-2">
                <div className="w-10 h-10 rounded-full bg-[#ACCEC5]/10 flex items-center justify-center mx-auto">
                  <Bot size={20} className="text-[#ACCEC5]" />
                </div>
                <p className="text-[12px] text-[#8e8e88] leading-relaxed">
                  I'm Aria — I'll guide you through each section.<br />
                  Start filling in the form and I'll jump in.
                </p>
              </div>
            )}

            {messages.map((msg, i) => (
              <div key={i} className={`flex gap-2.5 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
                {msg.role === 'aria' && (
                  <div className="w-6 h-6 rounded-full bg-[#ACCEC5]/15 flex items-center justify-center flex-shrink-0 mt-0.5">
                    <Bot size={13} className="text-[#ACCEC5]" />
                  </div>
                )}
                <div className={`max-w-[82%] px-3 py-2 rounded-xl text-[12px] leading-relaxed ${
                  msg.role === 'aria'
                    ? 'bg-[#1c1c18] text-on-surface/90 rounded-tl-sm'
                    : 'bg-[#ACCEC5]/10 text-[#ACCEC5] rounded-tr-sm'
                }`}>
                  {msg.content}
                </div>
              </div>
            ))}

            {/* Thinking indicator */}
            {isThinking && (
              <div className="flex gap-2.5">
                <div className="w-6 h-6 rounded-full bg-[#ACCEC5]/15 flex items-center justify-center flex-shrink-0 mt-0.5">
                  <Bot size={13} className="text-[#ACCEC5]" />
                </div>
                <div className="px-3 py-2.5 bg-[#1c1c18] rounded-xl rounded-tl-sm flex items-center gap-1">
                  <span className="w-1.5 h-1.5 bg-[#ACCEC5]/40 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                  <span className="w-1.5 h-1.5 bg-[#ACCEC5]/40 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                  <span className="w-1.5 h-1.5 bg-[#ACCEC5]/40 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                </div>
              </div>
            )}

            {/* Pending field updates */}
            {pendingUpdates.length > 0 && (
              <div className="space-y-2 pt-1">
                {pendingUpdates.map(u => (
                  <div key={u.id} className="p-3 bg-[#1c1c18] border border-[#ACCEC5]/10 rounded-xl space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-[11px] font-semibold text-[#ACCEC5]">{u.plain_label}</span>
                      <span className="text-[9px] font-bold uppercase tracking-wider text-[#8e8e88]">
                        {u.tier === 1 ? 'needs approval' : `auto in ${u.countdown}s`}
                      </span>
                    </div>
                    <p className="text-[11px] text-on-surface/70">{u.plain_value}</p>
                    {u.tier === 1 ? (
                      <div className="flex justify-end gap-2">
                        <button onClick={() => dismissUpdate(u.id)} className="px-2.5 py-1 text-[10px] text-[#8e8e88] hover:bg-white/5 rounded transition-colors">Skip</button>
                        <button onClick={() => applyUpdate(u.id, u.path, u.value)} className="px-2.5 py-1 text-[10px] bg-[#ACCEC5] text-[#151512] font-semibold rounded hover:opacity-90 transition-all flex items-center gap-1">
                          <ChevronRight size={11} /> Apply
                        </button>
                      </div>
                    ) : (
                      <div className="flex items-center justify-between">
                        <div className="flex-1 h-1 bg-white/5 rounded-full overflow-hidden mr-3">
                          <div
                            className="h-full bg-[#ACCEC5]/40 rounded-full transition-all duration-1000"
                            style={{ width: `${((4 - u.countdown) / 4) * 100}%` }}
                          />
                        </div>
                        <button onClick={() => dismissUpdate(u.id)} className="text-[10px] text-[#8e8e88] hover:text-red-400 transition-colors">Cancel</button>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* ── Suggestion chips ── */}
          {chips.length > 0 && (
            <div className="px-3 pb-2 flex flex-wrap gap-1.5 flex-shrink-0">
              {chips.map((chip, i) => (
                <button
                  key={i}
                  onClick={() => handleSend(undefined, chip)}
                  className="px-2.5 py-1 text-[10px] bg-[#1c1c18] border border-[#8e8e88]/15 rounded-full hover:border-[#ACCEC5]/30 hover:text-on-surface text-[#8e8e88] transition-all"
                >
                  {chip}
                </button>
              ))}
            </div>
          )}

          {/* ── Input ── */}
          <form onSubmit={handleSend} className="px-3 pb-4 flex gap-2 items-end flex-shrink-0 border-t border-[#8e8e88]/10 pt-3">
            <textarea
              rows={1}
              value={inputText}
              onChange={e => {
                setInputText(e.target.value);
                e.target.style.height = 'auto';
                e.target.style.height = Math.min(e.target.scrollHeight, 100) + 'px';
              }}
              onKeyDown={e => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSend();
                }
              }}
              placeholder={activeLabel ? `Ask about ${activeLabel}…` : 'Ask Aria anything…'}
              disabled={isThinking}
              className="flex-1 bg-[#1c1c18] border border-[#8e8e88]/10 rounded-xl px-3 py-2.5 text-[12px] text-on-surface placeholder-[#8e8e88]/30 outline-none focus:border-[#ACCEC5]/20 resize-none overflow-hidden min-h-[40px] transition-colors"
            />
            <button
              type="submit"
              disabled={isThinking || !inputText.trim()}
              className="w-9 h-9 rounded-xl bg-[#ACCEC5] hover:opacity-90 disabled:opacity-30 flex items-center justify-center text-[#151512] transition-all flex-shrink-0"
            >
              <Send size={15} />
            </button>
          </form>
        </>
      )}
    </div>
  );
}
