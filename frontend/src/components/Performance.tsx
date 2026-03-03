import React from 'react';

export const Performance: React.FC = () => {
    return (
        <div style={{ padding: '48px', color: 'var(--text-muted)' }}>
            <h2 style={{ color: 'var(--text-main)', marginBottom: '16px', fontFamily: 'var(--font-mono)' }}>HISTORICAL PERFORMANCE</h2>
            <p>Review system trade history, localized sharpe ratios, and win-rate statistics.</p>
            <div style={{ marginTop: '32px', height: '300px', border: '1px dashed var(--border-light)', display: 'flex', alignItems: 'center', justifyContent: 'center', borderRadius: '4px' }}>
                <span className="mono" style={{ fontSize: '14px' }}>Awaiting sufficient trade history to generate localized performance metrics.</span>
            </div>
        </div>
    );
};
