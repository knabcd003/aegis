import React, { useMemo, useState, useEffect } from 'react';
import { ResponsiveContainer, ComposedChart, Bar, Line, Cell, YAxis } from 'recharts';
import { Holdings } from './Holdings';
import { TerminalStream } from './TerminalStream';

// Mock price action generator to emulate the chart from the mockup
const generateData = () => {
    let prevPrice = 64200;
    return Array.from({ length: 45 }).map((_, i) => {
        const isUp = Math.random() > 0.45;
        const delta = Math.random() * 100;
        const open = prevPrice;
        const close = isUp ? open + delta : open - delta;
        prevPrice = close;

        // Smooth Sine wave for the moving average overlay
        const ma = 64250 + (Math.sin(i / 5) * 150);

        return {
            name: `T${i}`,
            up: isUp,
            range: [Math.min(open, close), Math.max(open, close)],
            ma
        };
    });
};

export const Dashboard: React.FC<{ onSelectAsset?: (ticker: string) => void }> = ({ onSelectAsset }) => {
    const data = useMemo(() => generateData(), []);

    return (
        <div className="dashboard-grid">
            <div className="chart-section">
                <div className="chart-header">
                    <div className="chart-title">BTC / USD <span className="text-green" style={{ marginLeft: '16px' }}>$64,281.40</span></div>
                    <div className="timeframes">
                        <button className="timeframe-btn">1m</button>
                        <button className="timeframe-btn active">5m</button>
                        <button className="timeframe-btn">15m</button>
                        <button className="timeframe-btn">1h</button>
                    </div>
                </div>

                <div className="chart-view">
                    <ResponsiveContainer width="100%" height="100%">
                        <ComposedChart data={data} margin={{ top: 20, right: 0, left: 0, bottom: 0 }}>
                            {/* Scale adjustment so bars render mid-screen */}
                            <YAxis domain={['dataMin - 100', 'dataMax + 100']} hide />
                            <Line type="monotone" dataKey="ma" stroke="rgba(255,255,255,0.15)" strokeWidth={2} dot={false} isAnimationActive={false} />

                            {/* Use range to draw candlestick body */}
                            <Bar dataKey="range" barSize={8} isAnimationActive={false}>
                                {data.map((entry, index) => (
                                    <Cell key={`cell-${index}`} fill={entry.up ? 'var(--neon-green)' : 'var(--neon-red)'} />
                                ))}
                            </Bar>
                        </ComposedChart>
                    </ResponsiveContainer>
                </div>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
                {/* Alerts Feed Section */}
                <AlertsFeed />

                <Holdings onSelectAsset={onSelectAsset} />
            </div>
            <TerminalStream />
        </div>
    );
};

const AlertsFeed: React.FC = () => {
    const [alerts, setAlerts] = useState<any[]>([]);

    useEffect(() => {
        fetch('http://localhost:8000/api/alerts')
            .then(res => res.json())
            .then(data => setAlerts(data))
            .catch(err => console.error("Error fetching alerts", err));
    }, []);

    if (alerts.length === 0) return null;

    return (
        <div className="holdings-section" style={{ border: '1px solid var(--neon-red)', backgroundColor: 'rgba(255, 0, 0, 0.02)' }}>
            <div className="terminal-header" style={{ borderBottom: '1px solid var(--neon-red)' }}>
                <span className="text-red" style={{ fontWeight: 600 }}>ACTIONABLE AI ALERTS</span>
            </div>
            <div style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
                {alerts.map(alert => (
                    <div key={alert.id} style={{ display: 'flex', alignItems: 'flex-start', gap: '16px', backgroundColor: 'var(--bg-card)', padding: '16px', borderRadius: '4px' }}>
                        <div style={{
                            padding: '4px 8px',
                            backgroundColor: alert.type === 'OPEN' ? 'rgba(0, 255, 0, 0.1)' : 'rgba(255, 0, 0, 0.1)',
                            color: alert.type === 'OPEN' ? 'var(--neon-green)' : 'var(--neon-red)',
                            fontSize: '12px',
                            fontWeight: 700,
                            borderRadius: '2px',
                            minWidth: '60px',
                            textAlign: 'center'
                        }}>
                            {alert.type}
                        </div>
                        <div style={{ flex: 1 }}>
                            <div style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-main)', marginBottom: '4px' }}>${alert.ticker}</div>
                            <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{alert.message}</div>
                        </div>
                        <div style={{ textAlign: 'right' }}>
                            <div style={{ fontSize: '10px', color: 'var(--text-muted)', marginBottom: '4px' }}>CONFIDENCE</div>
                            <div className={alert.type === 'OPEN' ? 'text-green' : 'text-red'} style={{ fontSize: '14px', fontWeight: 700 }}>{alert.confidence}%</div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
};
