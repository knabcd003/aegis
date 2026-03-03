import React, { useState } from 'react';

interface AssetTerminalProps {
    ticker: string;
    onBack: () => void;
}

export const AssetTerminal: React.FC<AssetTerminalProps> = ({ ticker, onBack }) => {
    const [executing, setExecuting] = useState(false);
    const [status, setStatus] = useState<string | null>(null);

    const handleExecute = async () => {
        setExecuting(true);
        setStatus('Executing...');
        try {
            const res = await fetch('http://localhost:8000/api/execute-approved-trade', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ ticker })
            });
            if (res.ok) {
                setStatus('ORDER FILLED');
            } else {
                setStatus('EXECUTION FAILED');
            }
        } catch (err) {
            console.error(err);
            setStatus('NETWORK ERROR');
        }
        setExecuting(false);
    };
    return (
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', backgroundColor: 'var(--bg-base)' }}>
            {/* Terminal Header */}
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '24px 32px', borderBottom: '1px solid var(--border-light)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                    <div onClick={onBack} style={{ cursor: 'pointer', color: 'var(--neon-orange)' }}>
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m15 18-6-6 6-6" /></svg>
                    </div>
                    <div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                            <h1 style={{ fontSize: '32px', letterSpacing: '2px', margin: 0 }}>${ticker}</h1>
                            <span style={{ backgroundColor: 'rgba(0,255,0,0.1)', color: 'var(--neon-green)', padding: '4px 8px', fontSize: '12px', borderRadius: '2px' }}>+4.28%</span>
                        </div>
                        <div style={{ fontSize: '10px', color: 'var(--text-muted)', letterSpacing: '2px', marginTop: '4px' }}>
                            {ticker} CORP • NASDAQ • AI AGENT OVERLAY ACTIVE
                        </div>
                    </div>
                </div>
                <div style={{ display: 'flex', gap: '12px' }}>
                    <button className="btn-primary" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 2v6h-6" /><path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8" /><path d="M3 8v6h6" /></svg>
                        Re-Analyze
                    </button>
                    <button className="btn-primary btn-accent">Export Logs</button>
                </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 450px', flex: 1, padding: '32px', gap: '48px', overflowY: 'auto' }}>
                {/* Left Column - Thesis */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                        <div style={{ width: '4px', height: '24px', backgroundColor: 'var(--neon-orange)' }}></div>
                        <h2 style={{ fontSize: '18px', fontWeight: 600, letterSpacing: '0.5px' }}>Analyst Agent Thesis</h2>
                        <span style={{ fontSize: '10px', color: 'var(--text-muted)', letterSpacing: '1px' }}>NARRATIVE ENGINE</span>
                    </div>

                    <div style={{ color: '#d1d1d6', fontSize: '14px', lineHeight: 1.8, display: 'flex', flexDirection: 'column', gap: '24px' }}>
                        <p>The underlying growth in data center demand remains robust. AI infrastructure spending is projected to increase by 45% YoY, providing a strong tailwind for current market leaders. Margin expansion is expected to continue as software services (CUDA ecosystem) become a larger portion of the revenue mix.</p>
                        <p>Our agent identifies a significant supply chain optimization in the H200 production cycle, potentially leading to a 12% upside in gross margins for Q3. The competitive moat remains intact as rival silicon solutions struggle with interconnect latency at scale.</p>
                        <p>Risk parameters are centered around geopolitical export restrictions, however, domestic demand from hyperscalers (Azure, AWS, GCP) is currently absorbing 110% of redirected inventory. Technical breakout confirmed above $140.25 level.</p>
                    </div>

                    <div style={{ marginTop: 'auto', border: '1px solid var(--border-light)', borderRadius: '8px', padding: '24px', backgroundColor: 'var(--bg-surface)' }}>
                        <div style={{ fontSize: '10px', color: 'var(--text-muted)', letterSpacing: '1px', marginBottom: '16px' }}>AGENT CONFIDENCE SCORE</div>
                        <div style={{ height: '8px', backgroundColor: 'rgba(255,255,255,0.1)', borderRadius: '4px', overflow: 'hidden', marginBottom: '12px' }}>
                            <div style={{ width: '88%', height: '100%', backgroundColor: 'var(--neon-orange)' }}></div>
                        </div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px' }}>
                            <span className="text-orange" style={{ fontWeight: 600 }}>88% (High Conviction)</span>
                            <span className="mono" style={{ color: 'var(--text-muted)' }}>σ = 0.04</span>
                        </div>
                    </div>
                </div>

                {/* Right Column - Quant & Execution */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
                    <div style={{ border: '1px solid var(--border-light)', borderRadius: '8px', backgroundColor: 'var(--bg-surface)', padding: '24px', flex: 1 }}>
                        <div style={{ fontSize: '12px', fontWeight: 600, letterSpacing: '1px', marginBottom: '32px', display: 'flex', justifyContent: 'space-between' }}>
                            <span>QUANT AGENT OPTIMIZATION</span>
                        </div>

                        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
                            {[
                                { label: 'P/E Ratio (FWD)', value: '48.22', color: '' },
                                { label: 'MA(200) Delta', value: '+18.4%', color: 'var(--neon-green)' },
                                { label: 'Volatility Index (Implied)', value: '34.12', color: 'var(--neon-red)' },
                                { label: 'RSI (14-Day)', value: '62.8', color: '' },
                                { label: 'Beta (Market Correlation)', value: '1.84', color: '' },
                                { label: 'Institutional Inflow', value: '$4.2B', color: 'var(--neon-green)' },
                                { label: 'Sharp Ratio', value: '2.41', color: 'var(--neon-green)' },
                            ].map(stat => (
                                <div key={stat.label} style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid rgba(255,255,255,0.05)', paddingBottom: '16px' }}>
                                    <span className="mono" style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{stat.label}</span>
                                    <span className="mono" style={{ fontSize: '13px', color: stat.color || 'var(--text-main)' }}>{stat.value}</span>
                                </div>
                            ))}
                        </div>
                    </div>

                    <div style={{ display: 'flex', gap: '24px', alignItems: 'flex-end', marginTop: 'auto' }}>
                        <div style={{ flex: 1 }}>
                            <div style={{ fontSize: '10px', color: 'var(--neon-orange)', fontWeight: 700, letterSpacing: '1px', marginBottom: '8px' }}>KELLY CRITERION POSITION SIZE</div>
                            <div style={{ display: 'flex', alignItems: 'baseline', gap: '16px', marginBottom: '12px' }}>
                                <span style={{ fontSize: '36px', fontWeight: 600, letterSpacing: '-1px' }}>12.45%</span>
                                <span style={{ fontSize: '10px', color: 'var(--text-muted)', letterSpacing: '1px' }}>FRACTIONAL KELLY</span>
                            </div>
                            <p style={{ fontSize: '10px', color: 'var(--text-muted)', lineHeight: 1.5 }}>Calculated based on 0.5 edge/odds ratio with current portfolio volatility constraints.</p>
                        </div>
                    </div>

                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '16px', borderTop: '1px solid var(--border-light)', paddingTop: '24px' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                            <div className="status-dot active"></div>
                            <span className="mono" style={{ fontSize: '10px', color: 'var(--text-muted)' }}>Real-time Analysis Pipeline Active</span>
                        </div>
                        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '8px' }}>
                            <button
                                className="btn-primary"
                                onClick={handleExecute}
                                disabled={executing || status === 'ORDER FILLED'}
                                style={{ padding: '16px 32px', fontSize: '12px', letterSpacing: '1px', backgroundColor: 'var(--bg-surface)' }}
                            >
                                {status === 'ORDER FILLED' ? 'EXECUTED' : 'APPROVE & EXECUTE'}
                            </button>
                            {status && <span className="mono" style={{ fontSize: '10px', color: status.includes('FAIL') || status.includes('ERROR') ? 'var(--neon-red)' : 'var(--neon-green)' }}>{status}</span>}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};
