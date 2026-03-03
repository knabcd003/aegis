import React from 'react';

export const ApiManagement: React.FC = () => {
    return (
        <div style={{ padding: '48px', color: 'var(--text-muted)' }}>
            <h2 style={{ color: 'var(--text-main)', marginBottom: '16px', fontFamily: 'var(--font-mono)' }}>API MANAGEMENT</h2>
            <p>Manage connections to market data providers and LLM execution services.</p>

            <div style={{ marginTop: '32px', display: 'flex', flexDirection: 'column', gap: '16px', maxWidth: '600px' }}>
                <div style={{ border: '1px solid var(--border-light)', padding: '16px', borderRadius: '4px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                        <div style={{ color: 'var(--text-main)', fontWeight: 600 }}>Alpaca Paper Trading API</div>
                        <div style={{ fontSize: '12px', marginTop: '4px' }}>Market Data & Order Routing</div>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <div className="status-dot active"></div>
                        <span style={{ fontSize: '12px', color: 'var(--neon-green)' }}>CONNECTED</span>
                    </div>
                </div>

                <div style={{ border: '1px solid var(--border-light)', padding: '16px', borderRadius: '4px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                        <div style={{ color: 'var(--text-main)', fontWeight: 600 }}>Financial Modeling Prep (FMP)</div>
                        <div style={{ fontSize: '12px', marginTop: '4px' }}>Fundamental Metrics & Earnings Transcripts</div>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <div className="status-dot active"></div>
                        <span style={{ fontSize: '12px', color: 'var(--neon-green)' }}>CONNECTED</span>
                    </div>
                </div>

                <div style={{ border: '1px solid var(--border-light)', padding: '16px', borderRadius: '4px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                        <div style={{ color: 'var(--text-main)', fontWeight: 600 }}>Anthropic Claude 3.5 Sonnet</div>
                        <div style={{ fontSize: '12px', marginTop: '4px' }}>LLM Analytical Engine</div>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <div className="status-dot active"></div>
                        <span style={{ fontSize: '12px', color: 'var(--neon-green)' }}>CONNECTED</span>
                    </div>
                </div>
            </div>
        </div>
    );
};
