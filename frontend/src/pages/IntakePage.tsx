import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ConversationalChat } from '../components/Intake/ConversationalChat';
import { IntakeWizard } from '../components/Intake/IntakeWizard';

const API = 'http://localhost:8000/api/intake';

type Step = 'input' | 'review' | 'launched';
type Path = 'A' | 'B';

interface ValidationResult {
  mandate_summary: Record<string, string>;
  hard_errors: string[];
  soft_contradictions: string[];
  inferred_flags: string[];
  is_valid: boolean;
}

interface ConfirmResult {
  workflow_id: string;
  status: string;
}

const SAMPLE_SCHEMA = JSON.stringify({
  _schema_version: 'v9.0',
  _path: 'B',
  mandate_hard_constraints: {
    investable_capital: 100000,
    max_portfolio_drawdown_pct: 0.15,
    max_concurrent_live_strategies: 5,
    horizon_allocation: [
      { label: "swing", min_days: 5, max_days: 21, capital_weight: 0.65 },
      { label: "position", min_days: 21, max_days: 60, capital_weight: 0.35 }
    ]
  },
  universe_mandate: {
    raw_desire: "Find momentum plays in tech and biotech after earnings catalysts"
  }
}, null, 2);

export function IntakePage() {
  const navigate = useNavigate();
  const [step, setStep] = useState<Step>('input');
  const [path, setPath] = useState<Path>('A');

  // Path A state
  const [stage, setStage] = useState(0);
  const [schemaWip, setSchemaWip] = useState<any>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  
  // Path B state
  const [schemaJson, setSchemaJson] = useState('');

  // Review & Confirm state
  const [validating, setValidating] = useState(false);
  const [confirming, setConfirming] = useState(false);
  const [validation, setValidation] = useState<ValidationResult | null>(null);
  const [confirmResult, setConfirmResult] = useState<ConfirmResult | null>(null);
  const [error, setError] = useState('');
  
  // Acknowledgment required for soft warnings
  const [acknowledged, setAcknowledged] = useState(false);

  const handleValidate = async (schemaToValidate?: any) => {
    setValidating(true);
    setError('');
    try {
      let body: any;
      if (path === 'A') {
        body = schemaToValidate || schemaWip;
      } else {
        body = JSON.parse(schemaJson);
      }
      
      const res = await fetch(`${API}/validate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      if (!res.ok) throw new Error(`Server error: ${res.status}`);
      const data = await res.json();
      setValidation(data);
      setAcknowledged(false); // Reset ack
      setStep('review');
    } catch (e: any) {
      setError(e.message || 'Validation failed');
    }
    setValidating(false);
  };

  const handleConfirm = async () => {
    setConfirming(true);
    setError('');
    try {
      let body: any;
      if (path === 'A') {
        body = schemaWip;
      } else {
        body = JSON.parse(schemaJson);
      }
      
      const sessionId = sessionStorage.getItem('aegis_intake_session');
      const url = sessionId && path === 'A' ? `${API}/confirm?session_id=${sessionId}` : `${API}/confirm`;
      
      const res = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      if (!res.ok) throw new Error(`Server error: ${res.status}`);
      const data = await res.json();
      setConfirmResult(data);
      setStep('launched');
    } catch (e: any) {
      setError(e.message || 'Confirmation failed');
    }
    setConfirming(false);
  };

  const renderTextWithBadges = (text: string) => {
    if (!text) return null;
    return text.split(/(\[EXPLICIT\]|\[INFERRED\]|\[ASSUMED\])/g).map((part, i) => {
      if (part === '[EXPLICIT]') return <span key={i} className="bg-emerald-500/20 text-emerald-400 px-1.5 py-0.5 rounded text-[10px] font-bold tracking-widest ml-1 align-middle">EXPLICIT</span>;
      if (part === '[INFERRED]') return <span key={i} className="bg-amber-500/20 text-amber-400 px-1.5 py-0.5 rounded text-[10px] font-bold tracking-widest ml-1 align-middle">INFERRED</span>;
      if (part === '[ASSUMED]') return <span key={i} className="bg-orange-500/20 text-orange-400 px-1.5 py-0.5 rounded text-[10px] font-bold tracking-widest ml-1 align-middle">ASSUMED</span>;
      return <span key={i}>{part}</span>;
    });
  };

  // ─── Step: Input ─────────────────────────────────────────
  if (step === 'input') {
    return (
      <div className="max-w-4xl mx-auto space-y-8">
        <div>
          <h1 className="font-headline text-4xl font-light tracking-tight text-on-surface">
            Define Your Mandate
          </h1>
          <p className="text-[#8e8e88] mt-2 max-w-2xl leading-relaxed">
            Aegis needs context to build strategies. Choose a guided conversation or import a predefined v9 schema.
          </p>
        </div>

        <div className="flex gap-2 bg-surface-container-low rounded-lg p-1 border border-white/5 w-fit">
          <button
            onClick={() => setPath('A')}
            className={`px-5 py-2.5 text-[0.8125rem] font-bold uppercase tracking-widest rounded-md transition-all ${
              path === 'A'
                ? 'bg-primary-container text-on-primary-container shadow-sm'
                : 'text-[#8e8e88] hover:text-on-surface hover:bg-white/5'
            }`}
          >
            Guided Conversation
          </button>
          <button
            onClick={() => setPath('B')}
            className={`px-5 py-2.5 text-[0.8125rem] font-bold uppercase tracking-widest rounded-md transition-all ${
              path === 'B'
                ? 'bg-primary-container text-on-primary-container shadow-sm'
                : 'text-[#8e8e88] hover:text-on-surface hover:bg-white/5'
            }`}
          >
            Schema Import
          </button>
        </div>

        {path === 'A' ? (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="md:col-span-2">
              <IntakeWizard 
                stage={stage} 
                schemaWip={schemaWip} 
                onUpdate={(patch) => setSchemaWip((prev: any) => ({ ...prev, ...patch }))}
                onNext={async () => {
                  if (stage === 7) {
                    handleValidate(schemaWip);
                    return;
                  }
                  // Send local edits to backend and advance
                  try {
                    const res = await fetch(`${API}/chat`, {
                      method: 'POST',
                      headers: { 'Content-Type': 'application/json' },
                      body: JSON.stringify({
                        session_id: sessionId,
                        schema_update: schemaWip,
                        advance_stage: true
                      })
                    });
                    const data = await res.json();
                    setStage(data.current_stage);
                    setSchemaWip(data.schema_wip);
                  } catch (e) {
                    console.error("Failed to advance stage manually", e);
                  }
                }}
              />
            </div>
            <div className="md:col-span-1 space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-[0.6875rem] font-bold uppercase tracking-widest text-on-surface-variant">
                  Aegis Advisory Link
                </h3>
                <span className="text-[0.625rem] bg-secondary/20 text-secondary px-2 py-0.5 rounded font-mono uppercase tracking-widest flex items-center gap-1">
                  <span className="w-1.5 h-1.5 bg-secondary rounded-full animate-pulse" />
                  Live
                </span>
              </div>
              <ConversationalChat 
                sessionIdOverride={sessionId}
                onSessionInit={setSessionId}
                onStageChange={setStage} 
                onSchemaUpdate={setSchemaWip} 
                onComplete={() => handleValidate(schemaWip)} 
                schemaWip={schemaWip}
              />
            </div>
          </div>
        ) : (
          <section className="bg-surface-container-low border border-white/5 rounded-xl p-6 space-y-4">
            <div className="flex justify-between items-start">
              <div>
                <h3 className="text-[0.6875rem] font-bold uppercase tracking-widest text-on-surface-variant mb-1">
                  Paste v9 Intake Schema
                </h3>
                <p className="text-[0.6875rem] text-[#8e8e88] max-w-xl">
                  Use an external LLM to populate the schema, then paste it here.
                </p>
              </div>
              <button
                onClick={() => {
                  navigator.clipboard.writeText(SAMPLE_SCHEMA);
                }}
                className="text-[0.6875rem] bg-surface-container hover:bg-white/5 border border-white/10 px-3 py-1.5 rounded transition-colors flex items-center gap-1.5"
              >
                <span className="material-symbols-outlined text-[14px]">content_copy</span>
                Copy Blank Schema
              </button>
            </div>
            <textarea
              value={schemaJson}
              onChange={(e) => setSchemaJson(e.target.value)}
              placeholder="Paste JSON here..."
              rows={16}
              className="w-full bg-surface-container border border-white/5 rounded-lg px-4 py-3 text-[0.8125rem] text-on-surface placeholder:text-[#8e8e88]/30 focus:outline-none focus:ring-1 focus:ring-primary/50 resize-none font-mono"
            />
            {error && <div className="text-destructive text-sm">{error}</div>}
            <div className="flex justify-end pt-2">
              <button
                onClick={() => handleValidate()}
                disabled={validating || !schemaJson.trim()}
                className="px-6 py-2.5 bg-primary-container text-on-primary-container text-[0.8125rem] font-semibold rounded-lg hover:brightness-110 disabled:opacity-50 transition-all"
              >
                {validating ? 'Validating...' : 'Review Mandate'}
              </button>
            </div>
          </section>
        )}
      </div>
    );
  }

  // ─── Step: Review ────────────────────────────────────────
  if (step === 'review' && validation) {
    const hasWarnings = validation.soft_contradictions.length > 0 || validation.inferred_flags.length > 0;
    const canConfirm = validation.is_valid && (!hasWarnings || acknowledged);

    return (
      <div className="max-w-3xl mx-auto space-y-8">
        <div>
          <h1 className="font-headline text-4xl font-light tracking-tight text-on-surface">
            Confirm Your Mandate
          </h1>
          <p className="text-[#8e8e88] mt-2 leading-relaxed">
            Review the final parameters. Once locked, Aegis begins autonomous execution.
          </p>
        </div>

        {/* Hard Constraints Box */}
        <section className="bg-surface-container-low border border-primary-container/30 rounded-xl p-6 space-y-4">
          <div className="flex items-center gap-2">
            <span className="material-symbols-outlined text-primary text-[20px]" style={{ fontVariationSettings: "'FILL' 1" }}>
              lock
            </span>
            <h3 className="text-[0.6875rem] font-bold uppercase tracking-widest text-primary">
              Tier 1: Hard Constraints
            </h3>
          </div>
          <div className="bg-surface-container rounded-lg border border-white/5 p-4 font-mono text-sm space-y-2 text-on-surface">
            {Object.entries(validation.mandate_summary).map(([key, value]) => (
              <div key={key} className="flex justify-between items-start py-1">
                <span className="text-[#8e8e88] whitespace-nowrap">{key}</span>
                <span className="font-semibold text-right break-words max-w-[60%]">
                  {renderTextWithBadges(value)}
                </span>
              </div>
            ))}
          </div>
        </section>

        {/* Hard Errors */}
        {validation.hard_errors.length > 0 && (
          <section className="bg-destructive/10 border border-destructive/30 rounded-xl p-6 space-y-3">
            <div className="flex items-center gap-2">
              <span className="material-symbols-outlined text-destructive text-[20px]">error</span>
              <h3 className="text-[0.6875rem] font-bold uppercase tracking-widest text-destructive">
                Critical Errors (Blocks Confirmation)
              </h3>
            </div>
            <ul className="list-disc pl-5 space-y-1">
              {validation.hard_errors.map((e, i) => (
                <li key={i} className="text-sm text-destructive/90">{e}</li>
              ))}
            </ul>
          </section>
        )}

        {/* Soft Contradictions */}
        {validation.soft_contradictions.length > 0 && (
          <section className="bg-amber-500/10 border border-amber-500/30 rounded-xl p-6 space-y-3">
            <div className="flex items-center gap-2">
              <span className="material-symbols-outlined text-amber-500 text-[20px]">warning</span>
              <h3 className="text-[0.6875rem] font-bold uppercase tracking-widest text-amber-500">
                Priority Conflicts & Contradictions
              </h3>
            </div>
            <ul className="list-disc pl-5 space-y-1">
              {validation.soft_contradictions.map((c, i) => (
                <li key={i} className="text-sm text-amber-500/90">{c}</li>
              ))}
            </ul>
          </section>
        )}

        {/* Inferred Flags */}
        {validation.inferred_flags.length > 0 && (
          <section className="bg-surface-container-high border border-white/10 rounded-xl p-6 space-y-3">
            <div className="flex items-center gap-2">
              <span className="material-symbols-outlined text-on-surface-variant text-[20px]">psychology</span>
              <h3 className="text-[0.6875rem] font-bold uppercase tracking-widest text-on-surface-variant">
                System Inferences
              </h3>
            </div>
            <p className="text-[0.6875rem] text-[#8e8e88]">
              Aegis made the following assumptions based on incomplete information.
            </p>
            <ul className="list-disc pl-5 space-y-1 mt-2">
              {validation.inferred_flags.map((f, i) => (
                <li key={i} className="text-sm text-on-surface/80">{renderTextWithBadges(f)}</li>
              ))}
            </ul>
          </section>
        )}

        {/* Error */}
        {error && <div className="text-destructive text-sm">{error}</div>}

        {/* Actions */}
        <div className="pt-4 border-t border-white/5 space-y-4">
          {hasWarnings && validation.is_valid && (
            <label className="flex items-center gap-3 cursor-pointer group bg-surface-container p-4 rounded-lg border border-white/5 hover:border-white/10 transition-colors">
              <input 
                type="checkbox" 
                checked={acknowledged}
                onChange={(e) => setAcknowledged(e.target.checked)}
                className="w-5 h-5 rounded bg-surface-container-high border-white/20 text-primary focus:ring-primary/50 focus:ring-offset-surface cursor-pointer"
              />
              <span className="text-sm text-on-surface group-hover:text-white transition-colors">
                I acknowledge the warnings and system inferences above.
              </span>
            </label>
          )}

          <div className="flex justify-between items-center">
            <button
              onClick={() => setStep('input')}
              className="flex items-center gap-2 px-4 py-2.5 text-[#8e8e88] hover:text-on-surface text-[0.8125rem] transition-colors"
            >
              <span className="material-symbols-outlined text-[18px]">arrow_back</span>
              Edit Mandate
            </button>
            <button
              onClick={handleConfirm}
              disabled={confirming || !canConfirm}
              className="px-8 py-3 bg-primary-container text-on-primary-container text-[0.8125rem] font-semibold rounded-lg hover:brightness-110 active:scale-[0.98] transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {confirming ? 'Locking...' : 'Lock Mandate'}
            </button>
          </div>
        </div>
      </div>
    );
  }

  // ─── Step: Launched ──────────────────────────────────────
  return (
    <div className="max-w-3xl mx-auto space-y-8">
      <div className="bg-surface-container-low border border-secondary/20 rounded-xl p-10 text-center space-y-6">
        <div className="w-16 h-16 rounded-full bg-secondary/20 mx-auto flex items-center justify-center">
          <span className="material-symbols-outlined text-secondary text-[32px]" style={{ fontVariationSettings: "'FILL' 1" }}>
            rocket_launch
          </span>
        </div>
        <div>
          <h2 className="font-headline text-3xl font-light tracking-tight text-on-surface">
            Sentinel Launched
          </h2>
          <p className="text-[#8e8e88] mt-2">
            Your mandate is locked. The pipeline is now generating and evaluating strategies.
          </p>
        </div>
        {confirmResult && (
          <div className="bg-surface-container rounded-lg border border-white/5 px-4 py-3 inline-flex items-center gap-3 mx-auto">
            <span className="text-[0.6875rem] text-[#8e8e88] uppercase tracking-widest">Workflow</span>
            <code className="text-sm font-mono text-on-surface">{confirmResult.workflow_id}</code>
            <span className="w-1.5 h-1.5 rounded-full bg-secondary animate-pulse" />
            <span className="text-[0.6875rem] uppercase tracking-widest text-secondary font-bold">
              {confirmResult.status}
            </span>
          </div>
        )}
        <div className="flex justify-center gap-3 pt-4">
          <button
            onClick={() => navigate('/pipeline')}
            className="px-6 py-3 bg-primary-container text-on-primary-container text-[0.8125rem] font-semibold rounded-lg hover:brightness-110 transition-all flex items-center gap-2"
          >
            <span className="material-symbols-outlined text-[18px]">hub</span>
            Watch Pipeline
          </button>
          <button
            onClick={() => navigate('/')}
            className="px-6 py-3 border border-white/10 text-on-surface-variant hover:text-on-surface text-[0.8125rem] font-medium rounded-lg hover:bg-white/5 transition-all"
          >
            Mission Control
          </button>
        </div>
      </div>
    </div>
  );
}
