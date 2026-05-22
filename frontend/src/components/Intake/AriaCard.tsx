import { useState, useEffect, useRef } from 'react';
import { Bot, X, Minimize2, Maximize2, AlertTriangle, Play } from 'lucide-react';
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
  countdown: number; // in seconds
}

interface ConflictEntry {
  description: string;
  severity: 'blocking' | 'warning' | 'advisory';
  fields_involved: string[];
  suggested_resolution: string;
}

interface AriaCardProps {
  currentSection: number;
  schemaState: IntakeSchemaV10;
  activeFieldPath: string | null;
  validationResult?: { errors: string[]; warnings: string[] } | null;
  onFieldUpdate?: (path: string, value: any) => void;
  onConflict?: (conflict: ConflictEntry) => void;
}

export function AriaCard({
  currentSection,
  schemaState,
  activeFieldPath,
  validationResult,
  onFieldUpdate,
  onConflict
}: AriaCardProps) {
  const [isMinimized, setIsMinimized] = useState(false);
  const [isHidden, setIsHidden] = useState(false);
  const [coords, setCoords] = useState<{ x: number; y: number } | null>(null);
  const [positionMode, setPositionMode] = useState<'docked' | 'anchored'>('docked');

  const [message, setMessage] = useState<string>(
    "Hello! I am Aria, your mandate assistant. I will guide you section-by-section to compile your Aegis portfolio configuration."
  );
  const [messageHistory, setMessageHistory] = useState<{ role: 'aria' | 'user'; content: string }[]>([
    { role: 'aria', content: "Hello! I am Aria, your mandate assistant. I will guide you section-by-section to compile your Aegis portfolio configuration." }
  ]);
  const [inputText, setInputText] = useState('');
  const [isThinking, setIsThinking] = useState(false);
  
  // Pending field updates (Tier 1 confirmation queue & Tier 2 countdowns)
  const [pendingUpdates, setPendingUpdates] = useState<PendingUpdate[]>([]);
  // Suggestion chips
  const [questions, setQuestions] = useState<string[]>([]);
  // Active conflicts
  const [conflicts, setConflicts] = useState<ConflictEntry[]>([]);
  // Context completeness signal
  const [contextComplete, setContextComplete] = useState(false);

  // Keep track of previous schema state to detect changes
  const prevSchemaRef = useRef<IntakeSchemaV10>(schemaState);

  // Deep diffing function to find which path changed
  const findDiffPath = (obj1: any, obj2: any, currentPath = ''): { path: string; value: any } | null => {
    if (obj1 === obj2) return null;
    if (!obj1 || !obj2 || typeof obj1 !== 'object' || typeof obj2 !== 'object') {
      return { path: currentPath, value: obj2 };
    }
    for (const key in obj2) {
      const p = currentPath ? `${currentPath}.${key}` : key;
      const diff = findDiffPath(obj1[key], obj2[key], p);
      if (diff) return diff;
    }
    return null;
  };

  // Main function to query Aria API
  const triggerAria = async (
    triggerType: 'section_enter' | 'field_focus' | 'field_change' | 'user_message' | 'validation_result',
    extra?: { fieldPath?: string; fieldValue?: any; userMessage?: string }
  ) => {
    setIsThinking(true);
    try {
      // Map history down to last 4 exchanges
      const trimmedHistory = messageHistory.slice(-8).map(m => ({
        role: m.role,
        content: m.content
      }));

      const payload = {
        trigger: triggerType,
        section: currentSection,
        active_field_path: extra?.fieldPath || activeFieldPath || undefined,
        active_field_value: extra?.fieldValue !== undefined ? extra.fieldValue : undefined,
        user_message: extra?.userMessage || undefined,
        validation_errors: validationResult?.errors || undefined,
        validation_warnings: validationResult?.warnings || undefined,
        schema_state: schemaState,
        message_history: trimmedHistory
      };

      const res = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (!res.ok) {
        throw new Error('Aria API request failed');
      }

      const data = await res.json();

      // Update state based on response
      if (data.message) {
        setMessage(data.message);
        setMessageHistory(prev => [...prev, { role: 'aria', content: data.message }]);
      }

      if (data.section_context_complete !== undefined) {
        setContextComplete(!!data.section_context_complete);
      }

      if (data.questions) {
        setQuestions(data.questions);
      } else {
        setQuestions([]);
      }

      if (data.conflicts) {
        setConflicts(data.conflicts);
        if (onConflict) {
          data.conflicts.forEach((c: ConflictEntry) => onConflict(c));
        }
      } else {
        setConflicts([]);
      }

      if (data.field_updates) {
        const newUpdates: PendingUpdate[] = data.field_updates.map((update: any) => ({
          id: Math.random().toString(36).substr(2, 9),
          path: update.path,
          value: update.value,
          tier: update.tier,
          plain_label: update.plain_label,
          plain_value: update.plain_value,
          auto_apply: !!update.auto_apply,
          countdown: update.auto_apply ? 3 : -1
        }));

        setPendingUpdates(prev => {
          // Merge updates, avoiding duplicate paths
          const filteredPrev = prev.filter(p => !newUpdates.some(n => n.path === p.path));
          return [...filteredPrev, ...newUpdates];
        });

        // For Tier 2 prose fields that auto_apply and have no countdown, apply immediately
        newUpdates.forEach(update => {
          if (update.tier === 2 && update.auto_apply && update.countdown <= 0) {
            if (onFieldUpdate) {
              onFieldUpdate(update.path, update.value);
            }
          }
        });
      }

    } catch (error) {
      console.error('Aria connection error:', error);
    } finally {
      setIsThinking(false);
    }
  };

  // Effect for Trigger: section_enter
  useEffect(() => {
    triggerAria('section_enter');
  }, [currentSection]);

  // Effect for Trigger: field_focus
  useEffect(() => {
    if (!activeFieldPath) return;
    const timer = setTimeout(() => {
      triggerAria('field_focus', { fieldPath: activeFieldPath });
    }, 100); // 100ms debounce
    return () => clearTimeout(timer);
  }, [activeFieldPath]);

  // Effect for Trigger: field_change
  useEffect(() => {
    const prevSchema = prevSchemaRef.current;
    if (prevSchema === schemaState) return;

    const diff = findDiffPath(prevSchema, schemaState);
    prevSchemaRef.current = schemaState;

    if (diff) {
      const timer = setTimeout(() => {
        triggerAria('field_change', { fieldPath: diff.path, fieldValue: diff.value });
      }, 800); // 800ms debounce
      return () => clearTimeout(timer);
    }
  }, [schemaState]);

  // Effect for Trigger: validation_result
  useEffect(() => {
    if (validationResult && (validationResult.errors.length > 0 || validationResult.warnings.length > 0)) {
      triggerAria('validation_result');
    }
  }, [validationResult]);

  // Countdown timer for auto-applying updates
  useEffect(() => {
    const interval = setInterval(() => {
      setPendingUpdates(prev => {
        const updated = prev.map(p => {
          if (p.auto_apply && p.countdown > 0) {
            return { ...p, countdown: p.countdown - 1 };
          }
          return p;
        });

        // Trigger updates that reached 0
        updated.forEach(p => {
          if (p.auto_apply && p.countdown === 0) {
            if (onFieldUpdate) {
              onFieldUpdate(p.path, p.value);
            }
          }
        });

        // Remove applied updates
        return updated.filter(p => !(p.auto_apply && p.countdown === 0));
      });
    }, 1000);

    return () => clearInterval(interval);
  }, [onFieldUpdate]);

  // Positioning calculations
  useEffect(() => {
    if (isMinimized || isHidden) return;

    if (activeFieldPath) {
      const el = document.querySelector(`[data-field-path="${activeFieldPath}"]`);
      if (el) {
        const rect = el.getBoundingClientRect();
        const cardWidth = 320;
        const spaceRight = window.innerWidth - rect.right;
        
        let x = rect.right + 20;
        let y = rect.top + window.scrollY;
        
        if (spaceRight < cardWidth + 40) {
          x = Math.max(20, rect.left + window.scrollX);
          y = rect.bottom + window.scrollY + 12;
          
          if (rect.bottom + 250 > window.innerHeight) {
            y = Math.max(20, rect.top + window.scrollY - 220);
          }
        } else {
          y = rect.top + window.scrollY - 10;
        }

        setCoords({ x, y });
        setPositionMode('anchored');
        return;
      }
    }

    setPositionMode('docked');
    setCoords(null);
  }, [activeFieldPath, isMinimized, isHidden, currentSection]);

  const handleSendMessage = (e?: React.FormEvent, customText?: string) => {
    if (e) e.preventDefault();
    const textToSend = customText || inputText;
    if (!textToSend.trim()) return;

    const userMsg = textToSend.trim();
    setMessageHistory(prev => [...prev, { role: 'user', content: userMsg }]);
    if (!customText) setInputText('');

    triggerAria('user_message', { userMessage: userMsg });
  };

  const handleApplyUpdate = (id: string, path: string, value: any) => {
    if (onFieldUpdate) {
      onFieldUpdate(path, value);
    }
    setPendingUpdates(prev => prev.filter(p => p.id !== id));
  };

  const handleSkipUpdate = (id: string) => {
    setPendingUpdates(prev => prev.filter(p => p.id !== id));
  };

  if (isHidden) {
    return (
      <button
        onClick={() => setIsHidden(false)}
        className="fixed bottom-6 right-6 w-12 h-12 rounded-full bg-[#ACCEC5] text-surface flex items-center justify-center shadow-xl hover:scale-105 transition-all z-50 border border-white/10"
        title="Open Aria Guidance"
      >
        <Bot size={22} className="text-[#151512]" />
      </button>
    );
  }

  const cardStyle = positionMode === 'anchored' && coords
    ? {
        position: 'absolute' as const,
        left: `${coords.x}px`,
        top: `${coords.y}px`,
        transition: 'left 200ms ease-out, top 200ms ease-out',
      }
    : {
        position: 'fixed' as const,
        right: '24px',
        bottom: '24px',
      };

  return (
    <div
      style={cardStyle}
      className="w-[320px] z-50 rounded-[16px] bg-[#151512]/90 border-2 border-[#8e8e88]/20 backdrop-blur-xl shadow-[0_8px_32px_rgba(0,0,0,0.4)] overflow-hidden flex flex-col transition-all duration-300 max-h-[480px]"
    >
      {/* HEADER */}
      <div className="px-4 py-3 bg-[#1c1c18]/80 border-b border-[#8e8e88]/10 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className={`w-2.5 h-2.5 rounded-full ${isThinking ? 'bg-[#ffb03a] animate-pulse' : conflicts.some(c => c.severity === 'blocking') ? 'bg-[#ff5555]' : 'bg-[#ACCEC5]'}`} />
          <span className="text-[10px] font-bold uppercase tracking-[0.2em] text-[#ACCEC5]">
            ARIA
          </span>
          <span className="text-[10px] text-[#8e8e88] tracking-tighter truncate max-w-[120px]">
            Section {currentSection}
          </span>
        </div>
        <div className="flex items-center gap-1.5">
          <button
            onClick={() => setIsMinimized(!isMinimized)}
            className="p-1 hover:bg-white/5 rounded text-[#8e8e88] transition-colors"
          >
            {isMinimized ? <Maximize2 size={13} /> : <Minimize2 size={13} />}
          </button>
          <button
            onClick={() => setIsHidden(true)}
            className="p-1 hover:bg-white/5 rounded text-[#8e8e88] transition-colors"
          >
            <X size={13} />
          </button>
        </div>
      </div>

      {!isMinimized && (
        <>
          {/* SCROLLABLE MESSAGE & SETTINGS PANEL */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4 max-h-[300px] text-xs leading-relaxed custom-scrollbar">
            {/* Aria Serif Message */}
            <div className="pl-2 border-l-2 border-[#ACCEC5] italic font-serif text-[13px] text-on-surface/90">
              {isThinking && messageHistory[messageHistory.length - 1]?.role === 'user' ? (
                <span className="text-[#8e8e88]/60">Thinking...</span>
              ) : (
                message
              )}
            </div>

            {/* Field Suggestions (Tier 1 or Tier 2 counting down) */}
            {pendingUpdates.length > 0 && (
              <div className="space-y-2">
                {pendingUpdates.map((update) => (
                  <div key={update.id} className="p-3 bg-[#ACCEC5]/5 border border-[#ACCEC5]/10 rounded-xl space-y-2">
                    <div className="flex items-center justify-between text-[11px]">
                      <span className="font-semibold text-secondary">{update.plain_label}</span>
                      <span className="text-[#8e8e88] font-mono text-[9px] uppercase">
                        {update.tier === 1 ? 'Tier 1' : 'Tier 2'}
                      </span>
                    </div>
                    <p className="text-[11px] text-on-surface/80">{update.plain_value}</p>
                    
                    {update.tier === 1 ? (
                      <div className="flex gap-2 justify-end">
                        <button
                          onClick={() => handleSkipUpdate(update.id)}
                          className="px-2.5 py-1 text-[10px] text-[#8e8e88] hover:bg-white/5 rounded"
                        >
                          Skip
                        </button>
                        <button
                          onClick={() => handleApplyUpdate(update.id, update.path, update.value)}
                          className="px-2.5 py-1 text-[10px] bg-[#ACCEC5] text-[#151512] font-semibold rounded hover:opacity-90 transition-all"
                        >
                          Apply
                        </button>
                      </div>
                    ) : (
                      <div className="flex items-center justify-between text-[10px]">
                        <span className="text-[#8e8e88] italic">
                          Applying in {update.countdown}s...
                        </span>
                        <button
                          onClick={() => handleSkipUpdate(update.id)}
                          className="px-2 py-0.5 text-terracotta hover:underline"
                        >
                          Cancel
                        </button>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}

            {/* Conflicts banner display */}
            {conflicts.length > 0 && (
              <div className="space-y-2">
                {conflicts.map((conflict, idx) => (
                  <div
                    key={idx}
                    className={`p-3 rounded-xl border text-[11px] space-y-1 ${
                      conflict.severity === 'blocking'
                        ? 'bg-terracotta/10 border-terracotta/20 text-terracotta'
                        : conflict.severity === 'warning'
                        ? 'bg-amber-500/10 border-amber-500/20 text-amber-400'
                        : 'bg-white/5 border-white/10 text-[#8e8e88]'
                    }`}
                  >
                    <div className="flex items-center gap-1.5 font-bold uppercase tracking-wider text-[9px]">
                      <AlertTriangle size={12} />
                      <span>{conflict.severity} Conflict</span>
                    </div>
                    <p className="font-semibold text-on-surface">{conflict.description}</p>
                    <p className="text-[10px] opacity-80"><span className="font-semibold">Resolution:</span> {conflict.suggested_resolution}</p>
                  </div>
                ))}
              </div>
            )}

            {/* Context completed notification */}
            {contextComplete && (
              <div className="p-2 bg-[#ACCEC5]/10 border border-[#ACCEC5]/20 rounded-lg text-center text-[10px] font-semibold text-[#ACCEC5]">
                Ready to validate section →
              </div>
            )}
          </div>

          {/* Suggestion Chips */}
          {questions.length > 0 && (
            <div className="px-3 pt-2 flex flex-wrap gap-1.5 border-t border-[#8e8e88]/5 bg-[#1c1c18]/40">
              {questions.slice(0, 3).map((q, idx) => (
                <button
                  key={idx}
                  onClick={() => handleSendMessage(undefined, q)}
                  className="px-2.5 py-1 text-[10px] bg-white/5 border border-white/10 rounded-full hover:bg-white/10 transition-colors text-[#8e8e88] hover:text-on-surface text-left"
                >
                  {q}
                </button>
              ))}
            </div>
          )}

          {/* CHAT INPUT AREA */}
          <form
            onSubmit={handleSendMessage}
            className="p-3 bg-[#1c1c18] border-t border-[#8e8e88]/10 flex gap-2 items-center"
          >
            <textarea
              rows={2}
              value={inputText}
              onChange={e => setInputText(e.target.value)}
              onKeyDown={e => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSendMessage();
                }
              }}
              placeholder={
                activeFieldPath 
                  ? "Ask about this field..." 
                  : "Ask Aria anything..."
              }
              disabled={isThinking}
              className="flex-1 bg-white/5 border border-white/5 rounded-lg px-3 py-1.5 text-xs text-on-surface placeholder-[#8e8e88]/30 outline-none focus:border-secondary/20 resize-none h-[42px] custom-scrollbar"
            />
            <button
              type="submit"
              disabled={isThinking || !inputText.trim()}
              className="p-2 bg-[#ACCEC5] hover:opacity-90 disabled:opacity-40 disabled:hover:opacity-40 rounded-lg text-[#151512] transition-all flex items-center justify-center"
            >
              <Play size={14} fill="currentColor" />
            </button>
          </form>
        </>
      )}
    </div>
  );
}
