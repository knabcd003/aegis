import React, { useState } from 'react';

export const StrategyConfig: React.FC = () => {
    const [mode, setMode] = useState<'manual' | 'ai'>('manual');
    const [nlPrompt, setNlPrompt] = useState('');

    // Core parameters
    const [deploymentAmount, setDeploymentAmount] = useState<number>(50000);
    const [philosophy, setPhilosophy] = useState('value');
    const [maxPeRatio, setMaxPeRatio] = useState<number>(15);
    const [sectors, setSectors] = useState('tech, healthcare');
    const [riskTolerance, setRiskTolerance] = useState('moderate');
    const [maxPositionPct, setMaxPositionPct] = useState<number>(0.10);

    const [status, setStatus] = useState<string | null>(null);

    const handleSaveAndDeploy = async () => {
        setStatus('Deploying configuration...');
        let url = 'http://localhost:8000/api/update-philosophy';
        let payload: any = {
            philosophy,
            max_pe_ratio: maxPeRatio,
            sectors: sectors.split(',').map(s => s.trim()),
            risk_tolerance: riskTolerance,
            max_position_size_pct: maxPositionPct,
            deployment_amount: deploymentAmount
        };

        if (mode === 'ai') {
            url = 'http://localhost:8000/api/update-philosophy-nl';
            payload = { prompt: nlPrompt };
        }

        try {
            const res = await fetch(url, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            if (res.ok) {
                const data = await res.json();
                if (mode === 'ai' && data.config) {
                    // Update state to match AI's parsing
                    setPhilosophy(data.config.philosophy || philosophy);
                    setMaxPeRatio(data.config.max_pe_ratio || maxPeRatio);
                    setSectors((data.config.sectors || []).join(', '));
                    setRiskTolerance(data.config.risk_tolerance || riskTolerance);
                    setMaxPositionPct(data.config.max_position_size_pct || maxPositionPct);
                    setDeploymentAmount(data.config.deployment_amount || deploymentAmount);
                    setMode('manual'); // Flip back to show what it parsed
                }
                setStatus('SUCCESS: Strategy Deployed. Agents synced.');
                setTimeout(() => setStatus(null), 3000);
            } else {
                setStatus('ERROR: Failed to parse configuration.');
            }
        } catch (err) {
            console.error(err);
            setStatus('ERROR: Failed to reach backend.');
        }
    };

    return (
        <div style={{ padding: '48px', color: 'var(--text-muted)' }}>
            <h2 style={{ color: 'var(--text-main)', marginBottom: '16px', fontFamily: 'var(--font-mono)' }}>STRATEGY CONFIGURATION</h2>
            <p>Define the strict "laws" the multi-agent system uses to evaluate execution vectors.</p>

            <div style={{ display: 'flex', gap: '16px', marginTop: '32px' }}>
                <button
                    className={`timeframe-btn ${mode === 'manual' ? 'active' : ''}`}
                    onClick={() => setMode('manual')}
                >
                    Manual Entry
                </button>
                <button
                    className={`timeframe-btn ${mode === 'ai' ? 'active' : ''}`}
                    onClick={() => setMode('ai')}
                    style={{ color: mode === 'ai' ? 'var(--neon-green)' : 'inherit', borderColor: mode === 'ai' ? 'var(--neon-green)' : 'inherit' }}
                >
                    AI Assistant
                </button>
            </div>

            <div style={{ marginTop: '24px', border: '1px solid var(--border-light)', padding: '24px', borderRadius: '4px', maxWidth: '600px', display: 'flex', flexDirection: 'column', gap: '24px' }}>

                {mode === 'ai' ? (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                        <label style={{ fontSize: '12px', fontWeight: 600, color: 'var(--neon-green)' }}>Natural Language Instructions</label>
                        <p style={{ fontSize: '12px', marginBottom: '8px' }}>Describe your strategy and total capital. The AI will parse your constraints into strict systemic laws.</p>
                        <textarea
                            value={nlPrompt} onChange={(e) => setNlPrompt(e.target.value)}
                            placeholder="e.g. I want to value invest in tech and healthcare with a moderate risk tolerance. I have $50000 to deploy and I don't want any single position to be more than 10% of my portfolio."
                            style={{ padding: '12px', backgroundColor: 'var(--bg-base)', color: 'var(--text-main)', border: '1px solid var(--neon-green)', borderRadius: '4px', minHeight: '120px', fontFamily: 'var(--font-mono)', fontSize: '12px', resize: 'vertical' }}
                        />
                    </div>
                ) : (
                    <>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                            <label style={{ fontSize: '12px', fontWeight: 600 }}>Target Deployment Amount ($)</label>
                            <input
                                type="number" step="1000" value={deploymentAmount} onChange={(e) => setDeploymentAmount(Number(e.target.value))}
                                style={{ padding: '8px', backgroundColor: 'var(--bg-base)', color: 'var(--text-main)', border: '1px solid var(--border-light)', borderRadius: '4px' }}
                            />
                        </div>

                        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                            <label style={{ fontSize: '12px', fontWeight: 600 }}>Philosophical Alignment</label>
                            <select
                                value={philosophy} onChange={(e) => setPhilosophy(e.target.value)}
                                style={{ padding: '8px', backgroundColor: 'var(--bg-base)', color: 'var(--text-main)', border: '1px solid var(--border-light)', borderRadius: '4px' }}
                            >
                                <option value="value">Value Investing</option>
                                <option value="growth">Growth Focus</option>
                                <option value="momentum">Momentum / Trend</option>
                                <option value="contrarian">Contrarian</option>
                            </select>
                        </div>

                        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                            <label style={{ fontSize: '12px', fontWeight: 600 }}>Hard P/E Ratio Cap</label>
                            <input
                                type="number" value={maxPeRatio} onChange={(e) => setMaxPeRatio(Number(e.target.value))}
                                style={{ padding: '8px', backgroundColor: 'var(--bg-base)', color: 'var(--text-main)', border: '1px solid var(--border-light)', borderRadius: '4px' }}
                            />
                        </div>

                        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                            <label style={{ fontSize: '12px', fontWeight: 600 }}>Approved Sectors (Comma separated)</label>
                            <input
                                type="text" value={sectors} onChange={(e) => setSectors(e.target.value)}
                                style={{ padding: '8px', backgroundColor: 'var(--bg-base)', color: 'var(--text-main)', border: '1px solid var(--border-light)', borderRadius: '4px' }}
                            />
                        </div>

                        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                            <label style={{ fontSize: '12px', fontWeight: 600 }}>Risk Tolerance / Stop Range</label>
                            <select
                                value={riskTolerance} onChange={(e) => setRiskTolerance(e.target.value)}
                                style={{ padding: '8px', backgroundColor: 'var(--bg-base)', color: 'var(--text-main)', border: '1px solid var(--border-light)', borderRadius: '4px' }}
                            >
                                <option value="conservative">Conservative (Tight Stops)</option>
                                <option value="moderate">Moderate</option>
                                <option value="aggressive">Aggressive (Wide Variance)</option>
                            </select>
                        </div>

                        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                            <label style={{ fontSize: '12px', fontWeight: 600 }}>Max Position Size % (Decimal)</label>
                            <input
                                type="number" step="0.01" value={maxPositionPct} onChange={(e) => setMaxPositionPct(Number(e.target.value))}
                                style={{ padding: '8px', backgroundColor: 'var(--bg-base)', color: 'var(--text-main)', border: '1px solid var(--border-light)', borderRadius: '4px' }}
                            />
                        </div>
                    </>
                )}

                <button className="btn-primary" onClick={handleSaveAndDeploy} style={{ marginTop: '16px' }}>
                    SAVE & DEPLOY
                </button>
                {status && <span className="mono" style={{ fontSize: '12px', color: status.includes('ERROR') ? 'var(--neon-red)' : 'var(--neon-green)' }}>{status}</span>}
            </div>

            <div style={{ marginTop: '48px', border: '1px solid var(--border-light)', padding: '24px', borderRadius: '4px', maxWidth: '600px' }}>
                <h3 style={{ color: 'var(--text-main)', marginBottom: '16px', fontSize: '14px', fontFamily: 'var(--font-mono)' }}>SENTINEL AGENT DEPLOYMENT</h3>
                <p style={{ fontSize: '12px', lineHeight: 1.6 }}>
                    The passive <strong>Sentinel Agent</strong> should not be triggered manually. It evaluates existing Theses against current price action and fundamentals (e.g. Earnings Transcripts) on a schedule.
                    <br /><br />
                    To deploy Sentinel to your local Unix environment, add the following to your crontab (`crontab -e`):
                </p>
                <div style={{ background: 'var(--bg-base)', padding: '12px', borderRadius: '4px', marginTop: '16px', fontFamily: 'var(--font-mono)', fontSize: '12px', color: 'var(--neon-green)' }}>
                    0 15 * * 1-5 cd /path/to/Aegis_AI && /path/to/venv/bin/python main.py --monitor
                </div>
                <p style={{ marginTop: '16px', fontSize: '10px', fontStyle: 'italic' }}>* This schedule sets Sentinel to sweep the portfolio at 3:00 PM EST daily.</p>
            </div>
        </div>
    );
};
