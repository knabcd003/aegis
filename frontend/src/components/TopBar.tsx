import React, { useEffect, useState } from 'react';

interface Metrics {
    total_value: number;
    daily_pnl: number;
    pnl_percentage: number;
    available_cash: number;
}

export const TopBar: React.FC = () => {
    const [metrics, setMetrics] = useState<Metrics | null>(null);

    useEffect(() => {
        fetch('http://localhost:8000/api/portfolio/metrics')
            .then(res => res.json())
            .then(data => setMetrics(data))
            .catch(err => console.error("Error fetching metrics", err));
    }, []);

    const formatCurrency = (val: number) => {
        return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(val);
    };

    const handleRunScan = async () => {
        try {
            await fetch('http://localhost:8000/api/run-analysis', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ ticker: "AAPL" }) // Hardcoded for this demo step per usual prototype patterns
            });
        } catch (err) {
            console.error("Failed to trigger scan", err);
        }
    };

    return (
        <header className="topbar">
            <div style={{ display: 'flex', gap: '64px' }}>
                <div className="topbar-metric">
                    <div className="topbar-label">TOTAL PORTFOLIO VALUE</div>
                    <div className="topbar-value">{metrics ? formatCurrency(metrics.total_value) : '---'}</div>
                </div>

                <div className="topbar-metric">
                    <div className="topbar-label">DAILY P&L</div>
                    <div className="topbar-value text-green">
                        {metrics ? `+${formatCurrency(metrics.daily_pnl)}` : '---'}
                    </div>
                    {metrics && <div className="text-green" style={{ fontSize: '12px', fontWeight: 600, marginTop: '-4px' }}>(+{metrics.pnl_percentage}%)</div>}
                </div>

                <div className="topbar-metric">
                    <div className="topbar-label">AVAILABLE CASH</div>
                    <div className="topbar-value">{metrics ? formatCurrency(metrics.available_cash) : '---'}</div>
                </div>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                <div style={{ background: 'var(--bg-card)', padding: '8px 16px', borderRadius: '4px', fontSize: '11px', fontFamily: 'var(--font-mono)' }}>
                    EST: <br /> 14:02:44
                </div>
                <button className="btn-primary" onClick={handleRunScan} style={{ padding: '8px 16px', fontSize: '12px', height: '100%' }}>
                    RUN<br />MARKET SCAN
                </button>
                <button className="btn-emergency">EMERGENCY<br />HALT</button>
            </div>
        </header>
    );
};
