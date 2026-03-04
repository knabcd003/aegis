import React, { useState, useEffect } from 'react';
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid, Legend } from 'recharts';

interface BacktestRun {
    run_id: number;
    tickers: string[];
    start_date: string;
    end_date: string;
    total_return: number;
    sharpe_ratio: number;
    max_drawdown: number;
    win_rate: number;
    total_trades: number;
    status: string;
}

interface Trade {
    id: number;
    ticker: string;
    side: string;
    qty: number;
    fill_price: number;
    date: string;
    thesis: string;
    pnl: number;
    exit_reason: string;
    failure_tag: string;
}

interface RunDetail {
    run_id: number;
    equity_curve: { date: string; equity: number }[];
    trades: Trade[];
    total_return: number;
    sharpe_ratio: number;
    max_drawdown: number;
    win_rate: number;
    total_trades: number;
    config: any;
    tickers: string[];
    start_date: string;
    end_date: string;
}

export const Sandbox: React.FC = () => {
    // Config state
    const [tickers, setTickers] = useState('AAPL, NVDA, MSFT');
    const [startDate, setStartDate] = useState('2024-06-01');
    const [endDate, setEndDate] = useState('2024-12-31');
    const [useLlm, setUseLlm] = useState(false);
    const [evalFreq, setEvalFreq] = useState(5);

    // Execution state
    const [running, setRunning] = useState(false);
    const [downloading, setDownloading] = useState(false);
    const [status, setStatus] = useState<string | null>(null);

    // Results state
    const [runs, setRuns] = useState<BacktestRun[]>([]);
    const [selectedRun, setSelectedRun] = useState<RunDetail | null>(null);
    const [compareIds, setCompareIds] = useState<string>('');
    const [compareData, setCompareData] = useState<any>(null);

    useEffect(() => {
        fetchRuns();
    }, []);

    const fetchRuns = () => {
        fetch('http://localhost:8000/api/backtest/results')
            .then(res => res.json())
            .then(data => setRuns(data))
            .catch(() => { });
    };

    const handleDownloadData = async () => {
        setDownloading(true);
        setStatus('Downloading historical data...');
        try {
            const tickerList = tickers.split(',').map(t => t.trim());
            const res = await fetch('http://localhost:8000/api/backtest/download-data', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ tickers: tickerList, start_date: startDate, end_date: endDate })
            });
            if (res.ok) {
                setStatus('Data downloaded successfully.');
            } else {
                setStatus('Download failed.');
            }
        } catch { setStatus('Network error.'); }
        setDownloading(false);
    };

    const handleRunBacktest = async () => {
        setRunning(true);
        setStatus('Running backtest...');
        try {
            const tickerList = tickers.split(',').map(t => t.trim());
            const res = await fetch('http://localhost:8000/api/backtest/run', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    tickers: tickerList,
                    start_date: startDate,
                    end_date: endDate,
                    use_llm: useLlm,
                    eval_frequency_days: evalFreq
                })
            });
            if (res.ok) {
                const data = await res.json();
                setStatus(`Backtest #${data.run_id} complete!`);
                fetchRuns();
                loadRun(data.run_id);
            } else {
                setStatus('Backtest failed.');
            }
        } catch { setStatus('Network error.'); }
        setRunning(false);
    };

    const loadRun = async (runId: number) => {
        try {
            const res = await fetch(`http://localhost:8000/api/backtest/results/${runId}`);
            const data = await res.json();
            setSelectedRun(data);
            setCompareData(null);
        } catch { }
    };

    const handleCompare = async () => {
        try {
            const res = await fetch(`http://localhost:8000/api/backtest/compare?ids=${compareIds}`);
            const data = await res.json();
            setCompareData(data);
            setSelectedRun(null);
        } catch { }
    };

    const inputStyle = { padding: '8px', backgroundColor: 'var(--bg-base)', color: 'var(--text-main)', border: '1px solid var(--border-light)', borderRadius: '4px', fontSize: '12px' };

    return (
        <div style={{ padding: '48px', color: 'var(--text-muted)', overflowY: 'auto', flex: 1 }}>
            <h2 style={{ color: 'var(--text-main)', marginBottom: '8px', fontFamily: 'var(--font-mono)' }}>BACKTESTING SANDBOX</h2>
            <p style={{ marginBottom: '32px' }}>Replay the agent pipeline against historical data. Measure before you deploy.</p>

            {/* ── Config Panel ────────────────────────────────────── */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '32px', maxWidth: '900px' }}>
                <div style={{ border: '1px solid var(--border-light)', borderRadius: '4px', padding: '24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
                    <h3 style={{ fontSize: '12px', fontWeight: 700, letterSpacing: '1px', margin: 0 }}>CONFIGURATION</h3>

                    <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                        <label style={{ fontSize: '11px', fontWeight: 600 }}>Tickers (comma-separated)</label>
                        <input value={tickers} onChange={e => setTickers(e.target.value)} style={inputStyle} />
                    </div>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                            <label style={{ fontSize: '11px', fontWeight: 600 }}>Start Date</label>
                            <input type="date" value={startDate} onChange={e => setStartDate(e.target.value)} style={inputStyle} />
                        </div>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                            <label style={{ fontSize: '11px', fontWeight: 600 }}>End Date</label>
                            <input type="date" value={endDate} onChange={e => setEndDate(e.target.value)} style={inputStyle} />
                        </div>
                    </div>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                            <label style={{ fontSize: '11px', fontWeight: 600 }}>Eval Frequency (days)</label>
                            <input type="number" value={evalFreq} onChange={e => setEvalFreq(Number(e.target.value))} style={inputStyle} />
                        </div>
                        <div style={{ display: 'flex', alignItems: 'flex-end', gap: '8px' }}>
                            <label style={{ fontSize: '11px', display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer' }}>
                                <input type="checkbox" checked={useLlm} onChange={e => setUseLlm(e.target.checked)} />
                                <span style={{ fontWeight: 600 }}>Use LLM (Ollama)</span>
                            </label>
                        </div>
                    </div>

                    <div style={{ display: 'flex', gap: '12px', marginTop: '8px' }}>
                        <button className="btn-primary" onClick={handleDownloadData} disabled={downloading}
                            style={{ flex: 1, fontSize: '11px', opacity: downloading ? 0.5 : 1 }}>
                            {downloading ? 'DOWNLOADING...' : 'DOWNLOAD DATA'}
                        </button>
                        <button className="btn-primary btn-accent" onClick={handleRunBacktest} disabled={running}
                            style={{ flex: 1, fontSize: '11px', opacity: running ? 0.5 : 1 }}>
                            {running ? 'RUNNING...' : 'RUN BACKTEST'}
                        </button>
                    </div>
                    {status && <span className="mono" style={{ fontSize: '11px', color: status.includes('fail') || status.includes('error') ? 'var(--neon-red)' : 'var(--neon-green)' }}>{status}</span>}
                </div>

                {/* ── Past runs ────────────────────────────────────── */}
                <div style={{ border: '1px solid var(--border-light)', borderRadius: '4px', padding: '24px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
                    <h3 style={{ fontSize: '12px', fontWeight: 700, letterSpacing: '1px', margin: 0 }}>PREVIOUS RUNS</h3>
                    {runs.length === 0 ? (
                        <p style={{ fontSize: '12px', fontStyle: 'italic' }}>No backtests yet. Run one above.</p>
                    ) : (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', maxHeight: '300px', overflowY: 'auto' }}>
                            {runs.map(run => (
                                <div key={run.run_id} onClick={() => loadRun(run.run_id)}
                                    style={{ cursor: 'pointer', padding: '12px', backgroundColor: 'var(--bg-card)', borderRadius: '4px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', border: selectedRun?.run_id === run.run_id ? '1px solid var(--neon-orange)' : '1px solid transparent' }}>
                                    <div>
                                        <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-main)' }}>#{run.run_id} — {(run.tickers || []).join(', ')}</div>
                                        <div style={{ fontSize: '10px' }}>{run.start_date} → {run.end_date}</div>
                                    </div>
                                    <div style={{ textAlign: 'right' }}>
                                        <div style={{ fontSize: '14px', fontWeight: 700, color: (run.total_return || 0) >= 0 ? 'var(--neon-green)' : 'var(--neon-red)' }}>
                                            {(run.total_return || 0) >= 0 ? '+' : ''}{(run.total_return || 0).toFixed(2)}%
                                        </div>
                                        <div style={{ fontSize: '10px' }}>{run.total_trades} trades</div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                    <div style={{ display: 'flex', gap: '8px', marginTop: '8px' }}>
                        <input placeholder="e.g. 1,2" value={compareIds} onChange={e => setCompareIds(e.target.value)} style={{ ...inputStyle, flex: 1 }} />
                        <button className="btn-primary" onClick={handleCompare} style={{ fontSize: '11px' }}>COMPARE</button>
                    </div>
                </div>
            </div>

            {/* ── Results Display ──────────────────────────────────── */}
            {selectedRun && (
                <div style={{ marginTop: '48px', maxWidth: '900px' }}>
                    <h3 style={{ fontSize: '14px', fontWeight: 700, letterSpacing: '1px', color: 'var(--text-main)', marginBottom: '24px' }}>
                        RUN #{selectedRun.run_id} RESULTS
                    </h3>

                    {/* Stats cards */}
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '16px', marginBottom: '32px' }}>
                        {[
                            { label: 'RETURN', value: `${(selectedRun.total_return || 0) >= 0 ? '+' : ''}${(selectedRun.total_return || 0).toFixed(2)}%`, color: (selectedRun.total_return || 0) >= 0 ? 'var(--neon-green)' : 'var(--neon-red)' },
                            { label: 'SHARPE', value: (selectedRun.sharpe_ratio || 0).toFixed(2), color: 'var(--neon-orange)' },
                            { label: 'MAX DD', value: `${(selectedRun.max_drawdown || 0).toFixed(2)}%`, color: 'var(--neon-red)' },
                            { label: 'WIN RATE', value: `${(selectedRun.win_rate || 0).toFixed(1)}%`, color: 'var(--neon-green)' },
                            { label: 'TRADES', value: String(selectedRun.total_trades || 0), color: 'var(--text-main)' },
                        ].map(stat => (
                            <div key={stat.label} style={{ backgroundColor: 'var(--bg-card)', padding: '16px', borderRadius: '4px', textAlign: 'center' }}>
                                <div style={{ fontSize: '10px', letterSpacing: '1px', marginBottom: '8px' }}>{stat.label}</div>
                                <div style={{ fontSize: '20px', fontWeight: 700, color: stat.color }}>{stat.value}</div>
                            </div>
                        ))}
                    </div>

                    {/* Equity curve */}
                    {selectedRun.equity_curve && selectedRun.equity_curve.length > 0 && (
                        <div style={{ backgroundColor: 'var(--bg-card)', borderRadius: '4px', padding: '24px', marginBottom: '32px' }}>
                            <h4 style={{ fontSize: '12px', letterSpacing: '1px', marginBottom: '16px', color: 'var(--text-main)' }}>EQUITY CURVE</h4>
                            <ResponsiveContainer width="100%" height={300}>
                                <LineChart data={selectedRun.equity_curve}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                                    <XAxis dataKey="date" tick={{ fill: 'var(--text-muted)', fontSize: 10 }} tickFormatter={d => d?.slice(5) || ''} />
                                    <YAxis tick={{ fill: 'var(--text-muted)', fontSize: 10 }} domain={['auto', 'auto']} />
                                    <Tooltip contentStyle={{ backgroundColor: 'var(--bg-surface)', border: '1px solid var(--border-light)', fontSize: '12px' }} />
                                    <Line type="monotone" dataKey="equity" stroke="var(--neon-orange)" strokeWidth={2} dot={false} />
                                </LineChart>
                            </ResponsiveContainer>
                        </div>
                    )}

                    {/* Trade log */}
                    {selectedRun.trades && selectedRun.trades.length > 0 && (
                        <div style={{ backgroundColor: 'var(--bg-card)', borderRadius: '4px', padding: '24px' }}>
                            <h4 style={{ fontSize: '12px', letterSpacing: '1px', marginBottom: '16px', color: 'var(--text-main)' }}>TRADE LOG</h4>
                            <div style={{ overflowX: 'auto' }}>
                                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px' }}>
                                    <thead>
                                        <tr style={{ borderBottom: '1px solid var(--border-light)' }}>
                                            {['Date', 'Ticker', 'Side', 'Qty', 'Price', 'P&L', 'Exit Reason', 'Tag'].map(h => (
                                                <th key={h} style={{ textAlign: 'left', padding: '8px', fontSize: '10px', letterSpacing: '1px', fontWeight: 600 }}>{h}</th>
                                            ))}
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {selectedRun.trades.map((t, i) => (
                                            <tr key={i} style={{ borderBottom: '1px solid rgba(255,255,255,0.03)' }}>
                                                <td style={{ padding: '8px' }}>{t.date}</td>
                                                <td style={{ padding: '8px', fontWeight: 600, color: 'var(--text-main)' }}>{t.ticker}</td>
                                                <td style={{ padding: '8px', color: t.side === 'buy' ? 'var(--neon-green)' : 'var(--neon-red)' }}>{t.side?.toUpperCase()}</td>
                                                <td style={{ padding: '8px' }}>{t.qty}</td>
                                                <td style={{ padding: '8px' }}>${t.fill_price?.toFixed(2)}</td>
                                                <td style={{ padding: '8px', color: (t.pnl || 0) >= 0 ? 'var(--neon-green)' : 'var(--neon-red)', fontWeight: 600 }}>
                                                    {t.pnl != null ? `$${t.pnl >= 0 ? '+' : ''}${t.pnl.toFixed(2)}` : '—'}
                                                </td>
                                                <td style={{ padding: '8px' }}>{t.exit_reason || '—'}</td>
                                                <td style={{ padding: '8px' }}>
                                                    {t.failure_tag && <span style={{ padding: '2px 6px', borderRadius: '2px', fontSize: '10px', backgroundColor: t.failure_tag === 'WIN' ? 'rgba(0,255,0,0.1)' : 'rgba(255,0,0,0.1)', color: t.failure_tag === 'WIN' ? 'var(--neon-green)' : 'var(--neon-red)' }}>{t.failure_tag}</span>}
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    )}
                </div>
            )}

            {/* ── Compare View ────────────────────────────────────── */}
            {compareData && (
                <div style={{ marginTop: '48px', maxWidth: '900px' }}>
                    <h3 style={{ fontSize: '14px', fontWeight: 700, letterSpacing: '1px', color: 'var(--text-main)', marginBottom: '24px' }}>
                        COMPARE: RUN #{compareData.run_a?.run_id} vs #{compareData.run_b?.run_id}
                    </h3>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
                        {[compareData.run_a, compareData.run_b].map((run: any, idx: number) => (
                            <div key={idx} style={{ backgroundColor: 'var(--bg-card)', borderRadius: '4px', padding: '24px' }}>
                                <h4 style={{ fontSize: '12px', marginBottom: '16px', color: 'var(--neon-orange)' }}>RUN #{run?.run_id}</h4>
                                {[
                                    { l: 'Return', v: `${(run?.total_return || 0).toFixed(2)}%` },
                                    { l: 'Sharpe', v: (run?.sharpe_ratio || 0).toFixed(2) },
                                    { l: 'Max DD', v: `${(run?.max_drawdown || 0).toFixed(2)}%` },
                                    { l: 'Win Rate', v: `${(run?.win_rate || 0).toFixed(1)}%` },
                                    { l: 'Trades', v: run?.total_trades || 0 },
                                ].map(s => (
                                    <div key={s.l} style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid rgba(255,255,255,0.05)', fontSize: '12px' }}>
                                        <span>{s.l}</span>
                                        <span style={{ fontWeight: 600, color: 'var(--text-main)' }}>{s.v}</span>
                                    </div>
                                ))}
                            </div>
                        ))}
                    </div>

                    {/* Overlaid equity curves */}
                    {(compareData.run_a?.equity_curve?.length > 0 || compareData.run_b?.equity_curve?.length > 0) && (
                        <div style={{ backgroundColor: 'var(--bg-card)', borderRadius: '4px', padding: '24px', marginTop: '24px' }}>
                            <h4 style={{ fontSize: '12px', letterSpacing: '1px', marginBottom: '16px', color: 'var(--text-main)' }}>EQUITY CURVES OVERLAY</h4>
                            <ResponsiveContainer width="100%" height={300}>
                                <LineChart>
                                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                                    <XAxis dataKey="date" tick={{ fill: 'var(--text-muted)', fontSize: 10 }} data={compareData.run_a?.equity_curve || []} />
                                    <YAxis tick={{ fill: 'var(--text-muted)', fontSize: 10 }} />
                                    <Tooltip contentStyle={{ backgroundColor: 'var(--bg-surface)', border: '1px solid var(--border-light)', fontSize: '12px' }} />
                                    <Legend />
                                    <Line data={compareData.run_a?.equity_curve || []} type="monotone" dataKey="equity" name={`Run #${compareData.run_a?.run_id}`} stroke="var(--neon-orange)" strokeWidth={2} dot={false} />
                                    <Line data={compareData.run_b?.equity_curve || []} type="monotone" dataKey="equity" name={`Run #${compareData.run_b?.run_id}`} stroke="var(--neon-green)" strokeWidth={2} dot={false} />
                                </LineChart>
                            </ResponsiveContainer>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};
