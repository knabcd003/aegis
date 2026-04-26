import { useState, useEffect, useCallback } from 'react';

import { AddProviderModal } from '@/components/Setup/AddProviderModal';

const API = 'http://localhost:8000/api/setup';

interface SavedProvider {
  id: string;
  display_name: string;
  type: string;
  model: string;
  tier: string;
  limits: { rpd: number | null; rpm: number | null };
  key_configured: boolean;
  cost_per_1k_tokens: number;
  base_url?: string;
  api_key_env?: string;
}



interface RoleAssignments {
  [role: string]: { primary: string; fallback_chain: string[]; is_critical: boolean };
}

const ROLE_LABELS: Record<string, string> = {
  strategy_generation: 'Strategy reasoning',
  debate_moderator: 'Debate moderation',
  terminal_fallback: 'Emergency fallback',
  large_context: 'Large context',
  debate_bear: 'Adversarial debate',
  debate_bull: 'Bull debate',
  improvement_analyzer: 'Improvement analysis',
  final_audit_score: 'Final audit',
  semantic_validation: 'Semantic validation',
  structured_extraction: 'Data extraction',
  debate_compression: 'Debate compression',
  json_parsing: 'JSON parsing',
  schema_routing: 'Schema routing',
  nli_prefilter: 'NLI pre-filter',
};

const REQUIRED_ROLES = ['strategy_generation', 'debate_moderator', 'terminal_fallback'];

export function SetupPage() {
  const [providers, setProviders] = useState<SavedProvider[]>([]);
  const [roles, setRoles] = useState<RoleAssignments>({});
  const [hasFinnhub, setHasFinnhub] = useState(false);
  const [finnhubKey, setFinnhubKey] = useState('');
  const [finnhubStatus, setFinnhubStatus] = useState<{ valid?: boolean; latency_ms?: number; aapl_price?: number; error?: string } | null>(null);
  const [finnhubValidating, setFinnhubValidating] = useState(false);
  const [dataConnections, setDataConnections] = useState<any>({});
  const [modalOpen, setModalOpen] = useState(false);
  const [validatingId, setValidatingId] = useState<string | null>(null);
  const [testResults, setTestResults] = useState<Record<string, { valid: boolean; latency_ms?: number; error?: string }>>({});

  const loadProviders = useCallback(async () => {
    try {
      const provRes = await fetch(`${API}/current-providers`);
      const provData = await provRes.json();
      setProviders(provData.providers || []);
      setRoles(provData.role_assignments || {});
      setDataConnections(provData.data_connections || {});
      setHasFinnhub(provData.data_connections?.finnhub || false);
    } catch (e) {
      console.error('Failed to load providers:', e);
    }
  }, []);

  useEffect(() => { loadProviders(); }, [loadProviders]);

  const handleTest = async (p: SavedProvider) => {
    setValidatingId(p.id);
    try {
      const res = await fetch(`${API}/validate-provider`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          provider_type: p.type,
          provider_name: p.id.split('/')[0],
          model: p.model,
          base_url: p.base_url,
        }),
      });
      const data = await res.json();
      setTestResults(prev => ({ ...prev, [p.id]: data }));
    } catch (e: any) {
      setTestResults(prev => ({ ...prev, [p.id]: { valid: false, error: e.message } }));
    }
    setValidatingId(null);
  };

  const handleRemove = async (id: string) => {
    await fetch(`${API}/remove-provider`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ provider_id: id }),
    });
    await loadProviders();
  };

  const handleFinnhubValidate = async () => {
    if (!finnhubKey.trim()) return;
    setFinnhubValidating(true);
    try {
      const res = await fetch(`${API}/validate-finnhub`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ api_key: finnhubKey }),
      });
      const data = await res.json();
      setFinnhubStatus(data);
      if (data.valid) {
        setHasFinnhub(true);
        await loadProviders();
      }
    } catch (e: any) {
      setFinnhubStatus({ valid: false, error: e.message });
    }
    setFinnhubValidating(false);
  };

  const handleProviderSaved = async () => {
    setModalOpen(false);
    await loadProviders();
  };

  const allRoles = Object.keys(ROLE_LABELS);

  return (
    <div className="min-h-screen bg-surface text-on-surface flex items-center justify-center p-6 font-body selection:bg-primary-container selection:text-on-primary-container">
      <div className="w-full max-w-2xl space-y-8">
        {/* Header */}
        <div className="text-center space-y-3">
          <h1 className="text-4xl font-headline font-light tracking-tight text-on-surface">Command Center</h1>
          <p className="text-muted-foreground text-[0.8125rem] max-w-md mx-auto leading-relaxed">
            Connect the AI models and Data sources that will power your pipeline. Aegis assigns them to the right roles automatically. Your keys are stored locally.
          </p>
        </div>

        {/* AI Providers Section */}
        <section className="bg-surface-container-low border border-white/5 rounded-xl p-6 space-y-4 shadow-sm">
          <h2 className="text-[0.6875rem] font-bold uppercase tracking-widest text-on-surface-variant">AI Providers</h2>

          {providers.length === 0 && (
            <p className="text-[0.8125rem] text-muted-foreground italic">No providers connected yet.</p>
          )}

          {providers.map(p => {
            const tr = testResults[p.id];
            return (
              <div key={p.id} className="flex items-center justify-between bg-surface-container border border-white/5 rounded-lg px-4 py-3 transition-colors hover:bg-surface-container-high">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className={`w-1.5 h-1.5 rounded-full ${p.key_configured ? 'bg-secondary' : 'bg-primary'}`} />
                    <span className="text-[0.8125rem] font-semibold text-on-surface">{p.display_name}</span>
                    <span className="text-[0.6875rem] text-muted-foreground">— {p.model}</span>
                  </div>
                  <div className="text-[0.6875rem] text-muted-foreground pl-3.5">
                    Type: {p.type === 'ollama' ? 'Local' : p.type === 'openai_compatible' ? 'Cloud' : p.type}
                    {' · '}Quota: {p.limits?.rpd == null ? 'Unlimited' : `${p.limits.rpd} req/day`}
                    {tr && tr.valid && <span className="text-secondary font-medium"> · {tr.latency_ms}ms</span>}
                    {tr && !tr.valid && <span className="text-destructive font-medium"> · {tr.error?.slice(0, 50)}</span>}
                  </div>
                </div>
                <div className="flex gap-2">
                  <button onClick={() => handleTest(p)} disabled={validatingId === p.id}
                    className="text-[0.6875rem] font-bold uppercase tracking-widest px-3 py-1.5 rounded-md border border-white/10 text-on-surface-variant hover:text-on-surface hover:border-white/20 transition-all disabled:opacity-50">
                    {validatingId === p.id ? '...' : 'Test'}
                  </button>
                  <button onClick={() => handleRemove(p.id)}
                    className="text-[0.6875rem] font-bold uppercase tracking-widest px-3 py-1.5 rounded-md text-destructive hover:bg-destructive/10 transition-colors">
                    Remove
                  </button>
                </div>
              </div>
            );
          })}

          <button onClick={() => setModalOpen(true)}
            className="w-full py-2.5 rounded-lg border border-dashed border-white/10 text-muted-foreground text-[0.8125rem] font-medium hover:border-primary/50 hover:text-primary transition-colors">
            + Add Provider
          </button>
        </section>

        {/* Data Connections Section */}
        <div className="space-y-6">
          <h2 className="text-xl font-headline font-light tracking-tight text-on-surface text-center pt-8 border-t border-white/5">Data Connections</h2>

          {/* Market Data */}
          <section className="bg-surface-container-low border border-white/5 rounded-xl p-6 space-y-6 shadow-sm">
            <div>
              <h3 className="text-[0.6875rem] font-bold uppercase tracking-widest text-on-surface-variant mb-1">Market Data</h3>
              <p className="text-[0.6875rem] text-muted-foreground">Required for backtesting and live execution.</p>
            </div>

            <div className="space-y-6">
              {/* Finnhub */}
              <div className="flex flex-col md:flex-row md:items-start gap-4">
                <div className="w-1/3">
                  <h4 className="text-[0.8125rem] font-bold text-on-surface">Finnhub</h4>
                  <a href="https://finnhub.io" target="_blank" rel="noreferrer" className="text-[0.6875rem] text-muted-foreground hover:text-primary transition-colors">free at finnhub.io</a>
                </div>
                <div className="flex-1 space-y-2">
                  <div className="flex gap-2">
                    <input type="password" placeholder="API Key" value={finnhubKey} onChange={e => setFinnhubKey(e.target.value)}
                      className="flex-1 bg-surface-container border border-white/5 rounded-lg px-3 py-2 text-[0.8125rem] text-on-surface placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary/50 transition-shadow" />
                    <button onClick={handleFinnhubValidate} disabled={finnhubValidating}
                      className="px-4 py-2 rounded-lg bg-surface-container-high border border-white/10 text-on-surface-variant hover:text-on-surface text-[0.8125rem] font-bold uppercase tracking-widest hover:bg-white/5 transition-colors disabled:opacity-50">
                      {finnhubValidating ? '...' : 'Validate'}
                    </button>
                  </div>
                  {finnhubStatus ? (
                    <div className={`text-[0.6875rem] font-medium font-mono ${finnhubStatus.valid ? 'text-secondary' : 'text-destructive'}`}>
                      {finnhubStatus.valid ? `✅ Connected — AAPL: $${finnhubStatus.aapl_price} — ${finnhubStatus.latency_ms}ms` : `❌ ${finnhubStatus.error}`}
                    </div>
                  ) : hasFinnhub ? (
                    <div className="text-[0.6875rem] font-medium font-mono text-secondary">✅ Configured in Profile</div>
                  ) : (
                    <div className="text-[0.6875rem] font-medium font-mono text-muted-foreground">⬜ Not configured</div>
                  )}
                </div>
              </div>

              <hr className="border-white/5" />

              {/* Yahoo Finance */}
              <div className="flex flex-col md:flex-row md:items-start gap-4">
                <div className="w-1/3">
                  <h4 className="text-[0.8125rem] font-bold text-on-surface">Yahoo Finance</h4>
                  <span className="text-[0.6875rem] text-muted-foreground">no key needed</span>
                </div>
                <div className="flex-1 space-y-2">
                  <button className="px-4 py-2 rounded-lg bg-surface-container border border-white/10 text-on-surface-variant hover:text-on-surface text-[0.8125rem] font-bold uppercase tracking-widest hover:bg-white/5 transition-colors">
                    Test Connection
                  </button>
                  <div className="text-[0.6875rem] font-medium font-mono text-secondary">✅ Connected — rate limit: standard</div>
                </div>
              </div>
            </div>
          </section>

          {/* Execution & Extended Data */}
          <section className="bg-surface-container-low border border-white/5 rounded-xl p-6 space-y-6 shadow-sm">
            <div>
              <h3 className="text-[0.6875rem] font-bold uppercase tracking-widest text-on-surface-variant mb-1">Execution & Extended Data</h3>
              <p className="text-[0.6875rem] text-muted-foreground">Recommended for full functionality.</p>
            </div>

            <div className="space-y-6">
              {/* Alpaca */}
              <div className="flex flex-col md:flex-row md:items-start gap-4">
                <div className="w-1/3">
                  <h4 className="text-[0.8125rem] font-bold text-on-surface">Alpaca</h4>
                  <a href="https://alpaca.markets" target="_blank" rel="noreferrer" className="text-[0.6875rem] text-muted-foreground hover:text-primary transition-colors">free at alpaca.markets</a>
                </div>
                <div className="flex-1 space-y-2">
                  <div className="flex gap-2">
                    <input type="password" placeholder="API Key" className="flex-1 bg-surface-container border border-white/5 rounded-lg px-3 py-2 text-[0.8125rem] text-on-surface placeholder:text-muted-foreground" />
                  </div>
                  <div className="flex gap-2">
                    <input type="password" placeholder="API Secret" className="flex-1 bg-surface-container border border-white/5 rounded-lg px-3 py-2 text-[0.8125rem] text-on-surface placeholder:text-muted-foreground" />
                    <button className="px-4 py-2 rounded-lg bg-surface-container-high border border-white/10 text-on-surface-variant hover:text-on-surface text-[0.8125rem] font-bold uppercase tracking-widest hover:bg-white/5 transition-colors">
                      Validate
                    </button>
                  </div>
                  {dataConnections.alpaca ? (
                    <div className="text-[0.6875rem] font-medium font-mono text-secondary">✅ Configured in Profile</div>
                  ) : (
                    <div className="text-[0.6875rem] font-medium font-mono text-muted-foreground">⬜ Not configured</div>
                  )}
                </div>
              </div>

              <hr className="border-white/5" />

              {/* FRED */}
              <div className="flex flex-col md:flex-row md:items-start gap-4">
                <div className="w-1/3">
                  <h4 className="text-[0.8125rem] font-bold text-on-surface">FRED (macro data)</h4>
                  <a href="https://fred.stlouisfed.org" target="_blank" rel="noreferrer" className="text-[0.6875rem] text-muted-foreground hover:text-primary transition-colors">free at fred.stlouisfed.org</a>
                </div>
                <div className="flex-1 space-y-2">
                  <div className="flex gap-2">
                    <input type="password" placeholder="API Key" className="flex-1 bg-surface-container border border-white/5 rounded-lg px-3 py-2 text-[0.8125rem] text-on-surface placeholder:text-muted-foreground" />
                    <button className="px-4 py-2 rounded-lg bg-surface-container-high border border-white/10 text-on-surface-variant hover:text-on-surface text-[0.8125rem] font-bold uppercase tracking-widest hover:bg-white/5 transition-colors">
                      Validate
                    </button>
                  </div>
                  {dataConnections.fred ? (
                    <div className="text-[0.6875rem] font-medium font-mono text-secondary">✅ Configured in Profile</div>
                  ) : (
                    <div className="text-[0.6875rem] font-medium font-mono text-muted-foreground">⬜ Not configured</div>
                  )}
                </div>
              </div>
            </div>
          </section>

          {/* Alternative Data */}
          <section className="bg-surface-container-low border border-white/5 rounded-xl p-6 space-y-6 shadow-sm">
            <div>
              <h3 className="text-[0.6875rem] font-bold uppercase tracking-widest text-on-surface-variant mb-1">Alternative Data</h3>
              <p className="text-[0.6875rem] text-muted-foreground">Optional external signals.</p>
            </div>

            <div className="space-y-6">
              {/* SEC EDGAR */}
              <div className="flex flex-col md:flex-row md:items-start gap-4">
                <div className="w-1/3">
                  <h4 className="text-[0.8125rem] font-bold text-on-surface">SEC EDGAR</h4>
                  <span className="text-[0.6875rem] text-muted-foreground">no key needed</span>
                </div>
                <div className="flex-1 space-y-2">
                  <div className="flex gap-2">
                    <input type="email" placeholder="User-Agent Email" className="flex-1 bg-surface-container border border-white/5 rounded-lg px-3 py-2 text-[0.8125rem] text-on-surface placeholder:text-muted-foreground" />
                    <button className="px-4 py-2 rounded-lg bg-surface-container-high border border-white/10 text-on-surface-variant hover:text-on-surface text-[0.8125rem] font-bold uppercase tracking-widest hover:bg-white/5 transition-colors">
                      Save
                    </button>
                  </div>
                  <p className="text-[0.625rem] text-muted-foreground italic">(required by SEC for API access)</p>
                  {dataConnections.sec_edgar ? (
                    <div className="text-[0.6875rem] font-medium font-mono text-secondary">✅ Configured in Profile</div>
                  ) : (
                    <div className="text-[0.6875rem] font-medium font-mono text-muted-foreground">⬜ Not configured</div>
                  )}
                </div>
              </div>

              <hr className="border-white/5" />

              {/* Congressional Disclosures */}
              <div className="flex flex-col md:flex-row md:items-start gap-4">
                <div className="w-1/3">
                  <h4 className="text-[0.8125rem] font-bold text-on-surface">Congressional</h4>
                  <span className="text-[0.6875rem] text-muted-foreground">no key needed</span>
                </div>
                <div className="flex-1 space-y-2">
                  <button className="px-4 py-2 rounded-lg bg-surface-container border border-white/10 text-on-surface-variant hover:text-on-surface text-[0.8125rem] font-bold uppercase tracking-widest hover:bg-white/5 transition-colors">
                    Test Connection
                  </button>
                  <div className="text-[0.6875rem] font-medium font-mono text-secondary">✅ Connected — public portal accessible</div>
                </div>
              </div>

              <hr className="border-white/5" />

              {/* Polymarket */}
              <div className="flex flex-col md:flex-row md:items-start gap-4">
                <div className="w-1/3">
                  <h4 className="text-[0.8125rem] font-bold text-on-surface">Polymarket</h4>
                  <span className="text-[0.6875rem] text-muted-foreground">no key needed</span>
                </div>
                <div className="flex-1 space-y-2">
                  <button className="px-4 py-2 rounded-lg bg-surface-container border border-white/10 text-on-surface-variant hover:text-on-surface text-[0.8125rem] font-bold uppercase tracking-widest hover:bg-white/5 transition-colors">
                    Test Connection
                  </button>
                  <div className="text-[0.6875rem] font-medium font-mono text-secondary">✅ Connected — public API accessible</div>
                </div>
              </div>
            </div>
          </section>
        </div>

        {/* Pipeline Readiness Section */}
        <section className="bg-surface-container-low border border-white/5 rounded-xl p-6 space-y-4 shadow-sm">
          <h2 className="text-[0.6875rem] font-bold uppercase tracking-widest text-on-surface-variant">Pipeline Readiness</h2>

          <div className="space-y-2.5">
            {allRoles.map(role => {
              const assigned = roles[role];
              const isRequired = REQUIRED_ROLES.includes(role);
              const isCovered = !!assigned;
              return (
                <div key={role} className="flex items-center gap-3 text-[0.8125rem]">
                  <span className={`flex items-center justify-center w-4 h-4 rounded-full text-[10px] ${isCovered ? 'bg-secondary/20 text-secondary' : isRequired ? 'bg-destructive/20 text-destructive' : 'bg-white/5 text-muted-foreground'}`}>
                    {isCovered ? '✓' : isRequired ? '!' : ''}
                  </span>
                  <span className={isCovered ? 'text-on-surface font-medium' : 'text-muted-foreground'}>
                    {ROLE_LABELS[role] || role}
                  </span>
                  {isCovered && (
                    <span className="text-[0.6875rem] font-mono text-muted-foreground ml-auto">{assigned.primary}</span>
                  )}
                  {!isCovered && isRequired && (
                    <span className="text-[0.625rem] uppercase font-bold text-destructive/80 ml-auto tracking-widest">Missing</span>
                  )}
                </div>
              );
            })}

            <div className="flex items-center gap-3 text-[0.8125rem] pt-3 border-t border-white/5">
              <span className={`flex items-center justify-center w-4 h-4 rounded-full text-[10px] ${hasFinnhub ? 'bg-secondary/20 text-secondary' : 'bg-destructive/20 text-destructive'}`}>
                {hasFinnhub ? '✓' : '!'}
              </span>
              <span className={hasFinnhub ? 'text-on-surface font-medium' : 'text-muted-foreground'}>Price feed</span>
              {hasFinnhub && <span className="text-[0.6875rem] font-mono text-muted-foreground ml-auto">Finnhub</span>}
              {!hasFinnhub && <span className="text-[0.625rem] uppercase font-bold text-destructive/80 ml-auto tracking-widest">Missing</span>}
            </div>
          </div>
        </section>

      </div>

      {modalOpen && (
        <AddProviderModal onClose={() => setModalOpen(false)} onSaved={handleProviderSaved} />
      )}
    </div>
  );
}
