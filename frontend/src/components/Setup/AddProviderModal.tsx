import { useState } from 'react';

const API = 'http://localhost:8000/api/setup';

const SUGGESTED_MODELS: Record<string, string[]> = {
  groq: [
    'qwen/qwen3-32b',
    'moonshotai/kimi-k2-instruct',
    'openai/gpt-oss-120b',
    'meta-llama/llama-4-scout-17b-16e-instruct',
    'llama-3.3-70b-versatile',
    'llama-3.1-8b-instant',
  ],
  anthropic: ['claude-sonnet-4-6', 'claude-haiku-4-5-20251001'],
  gemini: ['gemini-2.5-flash', 'gemini-2.0-flash'],
  openrouter: ['qwen/qwen3-235b-a22b:free', 'meta-llama/llama-4-maverick:free'],
  mistral: ['mistral-large-latest', 'mistral-small-latest'],
  together: ['meta-llama/Llama-3.3-70B-Instruct-Turbo'],
};

const CLOUD_PROVIDERS = ['groq', 'anthropic', 'gemini', 'openrouter', 'mistral', 'together'];

interface Props {
  onClose: () => void;
  onSaved: () => void;
}

type Tab = 'cloud' | 'openai_compatible' | 'ollama';

export function AddProviderModal({ onClose, onSaved }: Props) {
  const [tab, setTab] = useState<Tab>('cloud');

  // Cloud state
  const [cloudProvider, setCloudProvider] = useState('groq');
  const [cloudModel, setCloudModel] = useState('');
  const [cloudKey, setCloudKey] = useState('');
  const [cloudQuota, setCloudQuota] = useState('1000');

  // OpenAI-compatible state
  const [oaiUrl, setOaiUrl] = useState('');
  const [oaiModel, setOaiModel] = useState('');
  const [oaiKey, setOaiKey] = useState('');
  const [oaiQuota, setOaiQuota] = useState('0');

  // Ollama state
  const [ollamaModel, setOllamaModel] = useState('qwen3:8b');

  // Shared
  const [testing, setTesting] = useState(false);
  const [saving, setSaving] = useState(false);
  const [testResult, setTestResult] = useState<{ valid?: boolean; latency_ms?: number; error?: string } | null>(null);

  const handleTest = async () => {
    setTesting(true);
    setTestResult(null);
    let body: any;

    if (tab === 'cloud') {
      body = { provider_type: 'cloud', provider_name: cloudProvider, model: cloudModel, api_key: cloudKey };
    } else if (tab === 'openai_compatible') {
      body = { provider_type: 'openai_compatible', provider_name: 'custom', model: oaiModel, api_key: oaiKey || undefined, base_url: oaiUrl };
    } else {
      body = { provider_type: 'ollama', provider_name: 'ollama', model: ollamaModel };
    }

    try {
      const res = await fetch(`${API}/validate-provider`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body),
      });
      setTestResult(await res.json());
    } catch (e: any) {
      setTestResult({ valid: false, error: e.message });
    }
    setTesting(false);
  };

  const handleSave = async () => {
    setSaving(true);
    let body: any;

    if (tab === 'cloud') {
      const id = `${cloudProvider}/${cloudModel}`;
      body = {
        provider_id: id,
        display_name: `${cloudModel} (${cloudProvider})`,
        provider_type: 'openai_compatible',
        provider_name: cloudProvider,
        model: cloudModel,
        api_key: cloudKey || undefined,
        daily_quota: cloudQuota === '0' || !cloudQuota ? null : parseInt(cloudQuota),
        cost_per_1k: 0.0,
      };
      if (cloudProvider === 'groq') body.base_url = 'https://api.groq.com/openai/v1';
    } else if (tab === 'openai_compatible') {
      body = {
        provider_id: `custom/${oaiModel}`,
        display_name: `${oaiModel} (Custom)`,
        provider_type: 'openai_compatible',
        provider_name: 'custom',
        model: oaiModel,
        api_key: oaiKey || undefined,
        base_url: oaiUrl,
        daily_quota: oaiQuota === '0' || !oaiQuota ? null : parseInt(oaiQuota),
        cost_per_1k: 0.0,
      };
    } else {
      body = {
        provider_id: `local/${ollamaModel}`,
        display_name: `${ollamaModel} (Local)`,
        provider_type: 'ollama',
        provider_name: 'ollama',
        model: ollamaModel,
        daily_quota: null,
        cost_per_1k: 0.0,
      };
    }

    try {
      await fetch(`${API}/save-provider`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body),
      });
      onSaved();
    } catch (e) {
      console.error('Save failed:', e);
    }
    setSaving(false);
  };

  const tabClass = (t: Tab) =>
    `px-4 py-2 text-[0.8125rem] font-bold uppercase tracking-widest rounded-md transition-all ${tab === t ? 'bg-primary-container text-on-primary-container shadow-sm' : 'text-muted-foreground hover:text-on-surface hover:bg-white/5'}`;

  const inputClass = 'w-full bg-surface-container border border-white/5 rounded-lg px-3 py-2.5 text-[0.8125rem] text-on-surface placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary/50 transition-shadow';
  const labelClass = 'block text-[0.6875rem] font-bold uppercase tracking-widest text-on-surface-variant mb-1.5';

  const suggestions = SUGGESTED_MODELS[cloudProvider] || [];

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4 font-body" onClick={onClose}>
      <div className="bg-surface border border-white/10 rounded-2xl w-full max-w-lg p-7 space-y-6 shadow-2xl" onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between border-b border-white/5 pb-4">
          <h2 className="text-xl font-headline text-on-surface">Add Provider</h2>
          <button onClick={onClose} className="text-muted-foreground hover:text-on-surface transition-colors">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>
          </button>
        </div>

        {/* Tabs */}
        <div className="flex gap-1 bg-surface-container-low rounded-lg p-1 border border-white/5">
          <button className={tabClass('cloud')} onClick={() => { setTab('cloud'); setTestResult(null); }}>Cloud Provider</button>
          <button className={tabClass('openai_compatible')} onClick={() => { setTab('openai_compatible'); setTestResult(null); }}>OpenAI-Compatible</button>
          <button className={tabClass('ollama')} onClick={() => { setTab('ollama'); setTestResult(null); }}>Local Ollama</button>
        </div>

        {/* Tab Content */}
        <div className="space-y-4">
          {tab === 'cloud' && (
            <>
              <div>
                <label className={labelClass}>Provider</label>
                <select value={cloudProvider} onChange={e => { setCloudProvider(e.target.value); setCloudModel(''); }}
                  className={inputClass + ' cursor-pointer'}>
                  {CLOUD_PROVIDERS.map(p => <option key={p} value={p}>{p.charAt(0).toUpperCase() + p.slice(1)}</option>)}
                </select>
              </div>
              <div>
                <label className={labelClass}>Model</label>
                <input type="text" value={cloudModel} onChange={e => setCloudModel(e.target.value)}
                  placeholder="Select or type model name" className={inputClass} list="model-suggestions" />
                <datalist id="model-suggestions">
                  {suggestions.map(m => <option key={m} value={m} />)}
                </datalist>
              </div>
              <div>
                <label className={labelClass}>API Key</label>
                <input type="password" value={cloudKey} onChange={e => setCloudKey(e.target.value)}
                  placeholder="sk-..." className={inputClass} />
              </div>
              <div>
                <label className={labelClass}>Daily quota (requests, 0 = unlimited)</label>
                <input type="number" value={cloudQuota} onChange={e => setCloudQuota(e.target.value)} className={inputClass} />
              </div>
            </>
          )}

          {tab === 'openai_compatible' && (
            <>
              <div>
                <label className={labelClass}>Base URL</label>
                <input type="text" value={oaiUrl} onChange={e => setOaiUrl(e.target.value)}
                  placeholder="https://api.example.com/v1" className={inputClass} />
              </div>
              <div>
                <label className={labelClass}>Model</label>
                <input type="text" value={oaiModel} onChange={e => setOaiModel(e.target.value)} className={inputClass} />
              </div>
              <div>
                <label className={labelClass}>API Key (optional)</label>
                <input type="password" value={oaiKey} onChange={e => setOaiKey(e.target.value)} className={inputClass} />
              </div>
              <div>
                <label className={labelClass}>Daily quota (0 = unlimited)</label>
                <input type="number" value={oaiQuota} onChange={e => setOaiQuota(e.target.value)} className={inputClass} />
              </div>
            </>
          )}

          {tab === 'ollama' && (
            <div>
              <label className={labelClass}>Model name</label>
              <input type="text" value={ollamaModel} onChange={e => setOllamaModel(e.target.value)}
                placeholder="qwen3:8b" className={inputClass} />
              <p className="text-[0.6875rem] text-muted-foreground mt-2 font-mono">Assumes Ollama running at localhost:11434</p>
            </div>
          )}
        </div>

        {/* Test Result */}
        {testResult && (
          <div className={`text-[0.8125rem] font-medium rounded-lg px-4 py-3 ${testResult.valid ? 'bg-secondary/10 text-secondary border border-secondary/20' : 'bg-destructive/10 text-destructive border border-destructive/20'}`}>
            {testResult.valid
              ? `✅ Connected — ${testResult.latency_ms}ms`
              : `❌ ${testResult.error}`}
          </div>
        )}

        {/* Actions */}
        <div className="flex gap-3 pt-4 border-t border-white/5">
          <button onClick={handleTest} disabled={testing}
            className="flex-1 py-2.5 rounded-lg border border-white/10 text-on-surface-variant text-[0.8125rem] font-bold uppercase tracking-widest hover:text-on-surface hover:bg-white/5 transition-all disabled:opacity-50">
            {testing ? 'Testing...' : 'Test Connection'}
          </button>
          <button onClick={handleSave} disabled={saving || !testResult?.valid}
            className="flex-1 py-2.5 rounded-lg bg-primary-container text-on-primary-container text-[0.8125rem] font-bold uppercase tracking-widest hover:opacity-90 active:scale-[0.98] transition-all shadow-sm disabled:bg-surface-container disabled:text-muted-foreground disabled:shadow-none disabled:cursor-not-allowed">
            {saving ? 'Saving...' : 'Save Provider'}
          </button>
        </div>
      </div>
    </div>
  );
}
