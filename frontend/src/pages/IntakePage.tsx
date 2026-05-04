import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

const API = 'http://localhost:8000/api/intake';

type Step = 'input' | 'review' | 'launched';
type Path = 'A' | 'B';

interface ValidationResult {
  mandate_summary: Record<string, string>;
  contradictions: string[];
  is_valid: boolean;
}

interface ConfirmResult {
  workflow_id: string;
  status: string;
}

const RISK_OPTIONS = [
  { value: 'conservative', label: 'Conservative', desc: 'Capital preservation first. Lower volatility, smaller positions.' },
  { value: 'moderate', label: 'Moderate', desc: 'Balanced risk/reward. Standard position sizing.' },
  { value: 'aggressive', label: 'Aggressive', desc: 'Growth-oriented. Higher volatility tolerance, larger bets.' },
];

const HORIZON_OPTIONS = [
  { value: 'short', label: 'Short', desc: '1–30 days' },
  { value: 'medium', label: 'Medium', desc: '1–6 months' },
  { value: 'long', label: 'Long', desc: '6+ months' },
];

const DRAWDOWN_PRESETS = [
  { value: 0.05, label: '5%', severity: 'Strict' },
  { value: 0.10, label: '10%', severity: 'Moderate' },
  { value: 0.15, label: '15%', severity: 'Standard' },
  { value: 0.20, label: '20%', severity: 'Relaxed' },
  { value: 0.30, label: '30%', severity: 'Aggressive' },
];

const SAMPLE_SCHEMA = JSON.stringify({
  _schema_version: 'v7.0',
  _path: 'B',
  required: {
    risk_tolerance: 'moderate',
    max_drawdown_pct: 0.15,
    time_horizon: 'medium',
    raw_desire: 'Find momentum plays in tech and biotech after earnings catalysts',
  },
  portfolio: { investable_capital: 50000, existing_holdings: [], account_type: 'margin' },
  universe: { asset_classes: ['equity'], sectors_of_interest: ['technology', 'biotech'], market_cap_range: 'mid-large' },
  strategy_character: { catalyst_types: ['earnings', 'fda'], holding_period_days: 14 },
  constraints: { leverage: false, max_single_position_pct: 5 },
}, null, 2);

export function IntakePage() {
  const navigate = useNavigate();
  const [step, setStep] = useState<Step>('input');
  const [path, setPath] = useState<Path>('A');

  // Path A fields
  const [desire, setDesire] = useState('');
  const [risk, setRisk] = useState('moderate');
  const [horizon, setHorizon] = useState('medium');
  const [drawdown, setDrawdown] = useState(0.15);
  const [tickers, setTickers] = useState('');

  // Path B
  const [schemaJson, setSchemaJson] = useState('');

  // State
  const [validating, setValidating] = useState(false);
  const [confirming, setConfirming] = useState(false);
  const [validation, setValidation] = useState<ValidationResult | null>(null);
  const [confirmResult, setConfirmResult] = useState<ConfirmResult | null>(null);
  const [error, setError] = useState('');

  const handleValidate = async () => {
    setValidating(true);
    setError('');
    try {
      let body: any;
      if (path === 'A') {
        body = {
          risk_tolerance: risk,
          time_horizon: horizon,
          max_drawdown_target: drawdown,
          raw_desire: desire || '',
          is_path_b: false,
          tickers: tickers ? tickers.split(',').map((t) => t.trim().toUpperCase()).filter(Boolean) : null,
        };
      } else {
        const parsed = JSON.parse(schemaJson);
        body = {
          risk_tolerance: parsed.required?.risk_tolerance || 'moderate',
          time_horizon: parsed.required?.time_horizon || 'medium',
          max_drawdown_target: parsed.required?.max_drawdown_pct || 0.15,
          raw_desire: parsed.required?.raw_desire || '',
          is_path_b: true,
          tickers: parsed.universe?.specific_tickers || null,
        };
      }
      const res = await fetch(`${API}/validate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      if (!res.ok) throw new Error(`Server error: ${res.status}`);
      const data = await res.json();
      setValidation(data);
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
      const body = {
        risk_tolerance: risk,
        time_horizon: horizon,
        max_drawdown_target: drawdown,
        raw_desire: desire || '',
        is_path_b: path === 'B',
        tickers: tickers ? tickers.split(',').map((t) => t.trim().toUpperCase()).filter(Boolean) : null,
      };
      const res = await fetch(`${API}/confirm`, {
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

  // ─── Step: Input ─────────────────────────────────────────
  if (step === 'input') {
    return (
      <div className="max-w-3xl mx-auto space-y-8">
        {/* Header */}
        <div>
          <h1 className="font-headline text-4xl font-light tracking-tight text-on-surface">
            Define Your Mandate
          </h1>
          <p className="text-[#8e8e88] mt-2 max-w-xl leading-relaxed">
            Tell Aegis what to trade and how. Your constraints become hard limits — the system will never exceed them.
          </p>
        </div>

        {/* Path Selector */}
        <div className="flex gap-2 bg-surface-container-low rounded-lg p-1 border border-white/5 w-fit">
          <button
            onClick={() => setPath('A')}
            className={`px-5 py-2.5 text-[0.8125rem] font-bold uppercase tracking-widest rounded-md transition-all ${
              path === 'A'
                ? 'bg-primary-container text-on-primary-container shadow-sm'
                : 'text-[#8e8e88] hover:text-on-surface hover:bg-white/5'
            }`}
          >
            Quick Setup
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
          <div className="space-y-8">
            {/* Desire */}
            <section className="bg-surface-container-low border border-white/5 rounded-xl p-6 space-y-4">
              <div>
                <h3 className="text-[0.6875rem] font-bold uppercase tracking-widest text-on-surface-variant mb-1">
                  Investment Desire
                </h3>
                <p className="text-[0.6875rem] text-[#8e8e88]">
                  What do you want the system to find? Leave blank for autonomous discovery.
                </p>
              </div>
              <textarea
                value={desire}
                onChange={(e) => setDesire(e.target.value)}
                placeholder="e.g., Find momentum plays in tech stocks after earnings beats"
                rows={3}
                className="w-full bg-surface-container border border-white/5 rounded-lg px-4 py-3 text-sm text-on-surface placeholder:text-[#8e8e88]/50 focus:outline-none focus:ring-1 focus:ring-primary/50 resize-none transition-shadow"
              />
            </section>

            {/* Risk Tolerance */}
            <section className="bg-surface-container-low border border-white/5 rounded-xl p-6 space-y-4">
              <h3 className="text-[0.6875rem] font-bold uppercase tracking-widest text-on-surface-variant">
                Risk Tolerance
              </h3>
              <div className="grid grid-cols-3 gap-3">
                {RISK_OPTIONS.map((opt) => (
                  <button
                    key={opt.value}
                    onClick={() => setRisk(opt.value)}
                    className={`text-left p-4 rounded-lg border transition-all ${
                      risk === opt.value
                        ? 'border-primary-container bg-primary-container/10 ring-1 ring-primary-container/30'
                        : 'border-white/5 bg-surface-container hover:border-white/10'
                    }`}
                  >
                    <p className={`text-sm font-medium ${risk === opt.value ? 'text-primary' : 'text-on-surface'}`}>
                      {opt.label}
                    </p>
                    <p className="text-[0.6875rem] text-[#8e8e88] mt-1">{opt.desc}</p>
                  </button>
                ))}
              </div>
            </section>

            {/* Time Horizon */}
            <section className="bg-surface-container-low border border-white/5 rounded-xl p-6 space-y-4">
              <h3 className="text-[0.6875rem] font-bold uppercase tracking-widest text-on-surface-variant">
                Time Horizon
              </h3>
              <div className="grid grid-cols-3 gap-3">
                {HORIZON_OPTIONS.map((opt) => (
                  <button
                    key={opt.value}
                    onClick={() => setHorizon(opt.value)}
                    className={`text-left p-4 rounded-lg border transition-all ${
                      horizon === opt.value
                        ? 'border-primary-container bg-primary-container/10 ring-1 ring-primary-container/30'
                        : 'border-white/5 bg-surface-container hover:border-white/10'
                    }`}
                  >
                    <p className={`text-sm font-medium ${horizon === opt.value ? 'text-primary' : 'text-on-surface'}`}>
                      {opt.label}
                    </p>
                    <p className="text-[0.6875rem] text-[#8e8e88] mt-1">{opt.desc}</p>
                  </button>
                ))}
              </div>
            </section>

            {/* Max Drawdown */}
            <section className="bg-surface-container-low border border-white/5 rounded-xl p-6 space-y-4">
              <div>
                <h3 className="text-[0.6875rem] font-bold uppercase tracking-widest text-on-surface-variant mb-1">
                  Maximum Drawdown
                </h3>
                <p className="text-[0.6875rem] text-[#8e8e88]">
                  The system will never let your portfolio drop below this threshold.
                </p>
              </div>
              <div className="flex gap-2">
                {DRAWDOWN_PRESETS.map((preset) => (
                  <button
                    key={preset.value}
                    onClick={() => setDrawdown(preset.value)}
                    className={`flex-1 py-3 rounded-lg border text-center transition-all ${
                      drawdown === preset.value
                        ? 'border-primary-container bg-primary-container/10 ring-1 ring-primary-container/30'
                        : 'border-white/5 bg-surface-container hover:border-white/10'
                    }`}
                  >
                    <p className={`text-lg font-headline font-medium ${drawdown === preset.value ? 'text-primary' : 'text-on-surface'}`}>
                      {preset.label}
                    </p>
                    <p className="text-[0.625rem] text-[#8e8e88]">{preset.severity}</p>
                  </button>
                ))}
              </div>
            </section>

            {/* Optional Tickers */}
            <section className="bg-surface-container-low border border-white/5 rounded-xl p-6 space-y-4">
              <div>
                <h3 className="text-[0.6875rem] font-bold uppercase tracking-widest text-on-surface-variant mb-1">
                  Focus Tickers <span className="text-[#8e8e88] font-normal">(optional)</span>
                </h3>
                <p className="text-[0.6875rem] text-[#8e8e88]">
                  Comma-separated symbols to prioritize. Leave blank for broad discovery.
                </p>
              </div>
              <input
                type="text"
                value={tickers}
                onChange={(e) => setTickers(e.target.value)}
                placeholder="AAPL, NVDA, TSLA"
                className="w-full bg-surface-container border border-white/5 rounded-lg px-4 py-3 text-sm text-on-surface placeholder:text-[#8e8e88]/50 focus:outline-none focus:ring-1 focus:ring-primary/50 transition-shadow font-mono"
              />
            </section>
          </div>
        ) : (
          /* Path B — Schema Import */
          <section className="bg-surface-container-low border border-white/5 rounded-xl p-6 space-y-4">
            <div>
              <h3 className="text-[0.6875rem] font-bold uppercase tracking-widest text-on-surface-variant mb-1">
                Paste Intake Schema
              </h3>
              <p className="text-[0.6875rem] text-[#8e8e88]">
                Use{' '}
                <code className="px-1.5 py-0.5 bg-surface-container rounded text-primary text-[0.625rem]">
                  aegis_intake_schema.json
                </code>{' '}
                +{' '}
                <code className="px-1.5 py-0.5 bg-surface-container rounded text-primary text-[0.625rem]">
                  aegis_llm_intake.md
                </code>{' '}
                with your preferred LLM, then paste the result.
              </p>
            </div>
            <textarea
              value={schemaJson}
              onChange={(e) => setSchemaJson(e.target.value)}
              placeholder={SAMPLE_SCHEMA}
              rows={16}
              className="w-full bg-surface-container border border-white/5 rounded-lg px-4 py-3 text-[0.8125rem] text-on-surface placeholder:text-[#8e8e88]/30 focus:outline-none focus:ring-1 focus:ring-primary/50 resize-none transition-shadow font-mono leading-relaxed"
            />
            <button
              onClick={() => setSchemaJson(SAMPLE_SCHEMA)}
              className="text-[0.6875rem] text-primary hover:text-primary/80 transition-colors underline underline-offset-4"
            >
              Load sample schema
            </button>
          </section>
        )}

        {/* Error */}
        {error && (
          <div className="bg-destructive/10 border border-destructive/20 rounded-lg px-4 py-3 text-sm text-destructive">
            {error}
          </div>
        )}

        {/* Submit */}
        <div className="flex justify-end gap-3 pt-4 border-t border-white/5">
          <button
            onClick={handleValidate}
            disabled={validating}
            className="px-8 py-3 bg-primary-container text-on-primary-container text-[0.8125rem] font-semibold rounded-lg hover:brightness-110 active:scale-[0.98] transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            {validating ? (
              <>
                <span className="w-4 h-4 border-2 border-on-primary-container/30 border-t-on-primary-container rounded-full animate-spin" />
                Validating…
              </>
            ) : (
              <>
                <span className="material-symbols-outlined text-[18px]" style={{ fontVariationSettings: "'wght' 500" }}>
                  check_circle
                </span>
                Review Mandate
              </>
            )}
          </button>
        </div>
      </div>
    );
  }

  // ─── Step: Review ────────────────────────────────────────
  if (step === 'review' && validation) {
    return (
      <div className="max-w-3xl mx-auto space-y-8">
        <div>
          <h1 className="font-headline text-4xl font-light tracking-tight text-on-surface">
            Confirm Your Mandate
          </h1>
          <p className="text-[#8e8e88] mt-2 max-w-xl leading-relaxed">
            Review your constraints before the system begins. Hard limits below can never be exceeded.
          </p>
        </div>

        {/* Summary Cards */}
        <section className="bg-surface-container-low border border-white/5 rounded-xl p-6 space-y-5">
          <h3 className="text-[0.6875rem] font-bold uppercase tracking-widest text-on-surface-variant">
            Mandate Summary
          </h3>
          <div className="space-y-0">
            {Object.entries(validation.mandate_summary).map(([key, value]) => (
              <div key={key} className="flex justify-between items-center py-3 border-b border-white/5 last:border-0">
                <span className="text-sm text-[#8e8e88]">{key}</span>
                <span className="text-sm font-medium text-on-surface font-mono">{value}</span>
              </div>
            ))}
          </div>
        </section>

        {/* Hard Constraints Box */}
        <section className="bg-surface-container-low border border-primary-container/30 rounded-xl p-6 space-y-4">
          <div className="flex items-center gap-2">
            <span className="material-symbols-outlined text-primary text-[20px]" style={{ fontVariationSettings: "'FILL' 1" }}>
              lock
            </span>
            <h3 className="text-[0.6875rem] font-bold uppercase tracking-widest text-primary">
              Hard Constraints — The System Will Never Exceed These
            </h3>
          </div>
          <div className="bg-surface-container rounded-lg border border-white/5 p-4 font-mono text-sm space-y-2 text-on-surface">
            <div className="flex justify-between">
              <span className="text-[#8e8e88]">Max portfolio drawdown</span>
              <span className="font-semibold">{(drawdown * 100).toFixed(0)}%</span>
            </div>
            <div className="flex justify-between">
              <span className="text-[#8e8e88]">Risk profile</span>
              <span className="font-semibold capitalize">{risk}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-[#8e8e88]">Holding period</span>
              <span className="font-semibold capitalize">{horizon}</span>
            </div>
          </div>
        </section>

        {/* Contradictions */}
        {validation.contradictions.length > 0 && (
          <section className="bg-destructive/10 border border-destructive/20 rounded-xl p-6 space-y-3">
            <div className="flex items-center gap-2">
              <span className="material-symbols-outlined text-destructive text-[20px]">warning</span>
              <h3 className="text-[0.6875rem] font-bold uppercase tracking-widest text-destructive">
                Contradictions Detected
              </h3>
            </div>
            {validation.contradictions.map((c, i) => (
              <p key={i} className="text-sm text-destructive/90">{c}</p>
            ))}
          </section>
        )}

        {/* Error */}
        {error && (
          <div className="bg-destructive/10 border border-destructive/20 rounded-lg px-4 py-3 text-sm text-destructive">
            {error}
          </div>
        )}

        {/* Actions */}
        <div className="flex justify-between items-center pt-4 border-t border-white/5">
          <button
            onClick={() => { setStep('input'); setValidation(null); }}
            className="flex items-center gap-2 px-5 py-3 text-[#8e8e88] hover:text-on-surface text-[0.8125rem] transition-colors"
          >
            <span className="material-symbols-outlined text-[18px]">arrow_back</span>
            Let me adjust
          </button>
          <button
            onClick={handleConfirm}
            disabled={confirming || !validation.is_valid}
            className="px-8 py-3 bg-primary-container text-on-primary-container text-[0.8125rem] font-semibold rounded-lg hover:brightness-110 active:scale-[0.98] transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            {confirming ? (
              <>
                <span className="w-4 h-4 border-2 border-on-primary-container/30 border-t-on-primary-container rounded-full animate-spin" />
                Launching…
              </>
            ) : (
              <>
                <span className="material-symbols-outlined text-[18px]" style={{ fontVariationSettings: "'FILL' 1, 'wght' 500" }}>
                  rocket_launch
                </span>
                These look right — build it
              </>
            )}
          </button>
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
            Your mandate is active. The pipeline is now generating and evaluating strategies.
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
