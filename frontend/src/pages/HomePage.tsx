import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { User, ShieldCheck, Database, Settings } from 'lucide-react';

const API = 'http://localhost:8000/api/setup';

export function HomePage() {
  const [providers, setProviders] = useState<any[]>([]);
  const [readiness, setReadiness] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const [provRes, readyRes] = await Promise.all([
          fetch(`${API}/current-providers`),
          fetch(`${API}/readiness`),
        ]);
        const provData = await provRes.json();
        const readyData = await readyRes.json();
        setProviders(provData.providers || []);
        setReadiness(readyData);
      } catch (e) {
        console.error('Failed to load profile data', e);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-surface flex items-center justify-center font-body">
        <div className="w-6 h-6 border-2 border-primary border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-surface text-on-surface p-8 font-body selection:bg-primary-container selection:text-on-primary-container">
      <div className="max-w-4xl mx-auto space-y-8">
        
        {/* Header */}
        <header className="flex items-center justify-between pb-6 border-b border-white/5">
          <div>
            <h1 className="text-3xl font-headline font-light text-on-surface tracking-tight">Command Center</h1>
            <p className="text-[0.8125rem] text-muted-foreground mt-1">Aegis AI Profile Dashboard</p>
          </div>
          <div className="flex items-center gap-3 bg-surface-container border border-white/5 px-4 py-2 rounded-full">
            <div className="w-8 h-8 rounded-full bg-primary-container text-on-primary-container flex items-center justify-center">
              <User className="w-4 h-4" />
            </div>
            <span className="text-[0.8125rem] font-bold tracking-widest uppercase">Default User</span>
          </div>
        </header>

        {/* Dashboard Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          
          {/* AI Providers Summary */}
          <section className="bg-surface-container-low border border-white/5 rounded-xl p-6 shadow-sm flex flex-col">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 rounded-lg bg-surface-container flex items-center justify-center border border-white/5">
                <ShieldCheck className="w-5 h-5 text-primary" />
              </div>
              <div>
                <h2 className="text-[0.8125rem] font-bold uppercase tracking-widest text-on-surface">AI Providers</h2>
                <p className="text-[0.6875rem] text-muted-foreground">{providers.length} models connected</p>
              </div>
            </div>
            
            <div className="flex-1 space-y-3">
              {providers.length === 0 ? (
                <p className="text-[0.8125rem] text-muted-foreground italic">No AI providers configured.</p>
              ) : (
                providers.map((p: any) => (
                  <div key={p.id} className="flex justify-between items-center text-[0.8125rem]">
                    <span className="text-on-surface">{p.display_name}</span>
                    <span className="text-muted-foreground font-mono text-[0.6875rem]">{p.model}</span>
                  </div>
                ))
              )}
            </div>

            <Link to="/setup" className="mt-6 flex items-center justify-center gap-2 w-full py-2.5 rounded-lg border border-white/10 text-on-surface-variant hover:text-on-surface hover:bg-white/5 transition-colors text-[0.8125rem] font-bold uppercase tracking-widest">
              <Settings className="w-4 h-4" />
              Manage Providers
            </Link>
          </section>

          {/* Data Connections Summary */}
          <section className="bg-surface-container-low border border-white/5 rounded-xl p-6 shadow-sm flex flex-col">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 rounded-lg bg-surface-container flex items-center justify-center border border-white/5">
                <Database className="w-5 h-5 text-secondary" />
              </div>
              <div>
                <h2 className="text-[0.8125rem] font-bold uppercase tracking-widest text-on-surface">Data Sources</h2>
                <p className="text-[0.6875rem] text-muted-foreground">Market & Extended Data</p>
              </div>
            </div>
            
            <div className="flex-1 space-y-3">
              <div className="flex justify-between items-center text-[0.8125rem]">
                <span className="text-on-surface">Finnhub (Market Data)</span>
                <span className={readiness?.has_price_feed ? "text-secondary font-medium" : "text-destructive font-medium"}>
                  {readiness?.has_price_feed ? 'Active' : 'Missing'}
                </span>
              </div>
              <div className="flex justify-between items-center text-[0.8125rem]">
                <span className="text-on-surface">Alpaca (Execution)</span>
                <span className="text-muted-foreground italic">Unverified</span>
              </div>
              <div className="flex justify-between items-center text-[0.8125rem]">
                <span className="text-on-surface">Yahoo Finance</span>
                <span className="text-secondary font-medium">Ready</span>
              </div>
            </div>

            <Link to="/setup" className="mt-6 flex items-center justify-center gap-2 w-full py-2.5 rounded-lg border border-white/10 text-on-surface-variant hover:text-on-surface hover:bg-white/5 transition-colors text-[0.8125rem] font-bold uppercase tracking-widest">
              <Settings className="w-4 h-4" />
              Manage Connections
            </Link>
          </section>

        </div>

        {/* Readiness Alert */}
        {readiness && !readiness.ready && (
          <div className="bg-destructive/10 border border-destructive/20 rounded-xl p-4 flex items-start gap-4">
            <div className="text-destructive">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
            </div>
            <div>
              <h4 className="text-[0.8125rem] font-bold text-destructive uppercase tracking-widest mb-1">Pipeline Not Ready</h4>
              <p className="text-[0.8125rem] text-destructive/80 mb-2">You must complete the provider and data setup before pipelines can be deployed.</p>
              <ul className="list-disc list-inside text-[0.8125rem] text-destructive/80 font-mono">
                {readiness.missing_roles.map((r: string) => <li key={r}>Missing role: {r}</li>)}
                {!readiness.has_price_feed && <li>Missing price feed (Finnhub)</li>}
              </ul>
            </div>
          </div>
        )}

        {readiness && readiness.ready && (
          <div className="bg-secondary/10 border border-secondary/20 rounded-xl p-4 flex items-start gap-4">
             <div className="text-secondary">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <div>
              <h4 className="text-[0.8125rem] font-bold text-secondary uppercase tracking-widest mb-1">System Armed</h4>
              <p className="text-[0.8125rem] text-secondary/80">All required AI roles and data connections are configured. Aegis is ready for deployment.</p>
            </div>
          </div>
        )}

      </div>
    </div>
  );
}
