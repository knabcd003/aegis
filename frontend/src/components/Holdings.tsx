import React, { useEffect, useState } from 'react';

interface Holding {
    ticker: string;
    alloc: number;
    entry: number;
    price: number;
}

export const Holdings: React.FC<{ onSelectAsset?: (ticker: string) => void }> = ({ onSelectAsset }) => {
    const [holdings, setHoldings] = useState<Holding[]>([]);

    useEffect(() => {
        fetch('http://localhost:8000/api/portfolio/holdings')
            .then(res => res.json())
            .then(data => setHoldings(data))
            .catch(err => console.error("Error fetching holdings:", err));
    }, []);

    return (
        <div className="holdings-section">
            <div className="section-header">CURRENT HOLDINGS</div>
            <table className="holdings-table">
                <thead>
                    <tr>
                        <th>Ticker</th>
                        <th>Alloc%</th>
                        <th>Entry</th>
                        <th>Price</th>
                    </tr>
                </thead>
                <tbody>
                    {holdings.map((h, i) => {
                        const isUp = h.price > h.entry;
                        const diffClass = isUp ? 'text-green' : 'text-red';
                        return (
                            <tr key={i} onClick={() => onSelectAsset && onSelectAsset(h.ticker)} style={{ cursor: onSelectAsset ? 'pointer' : 'default' }}>
                                <td>{h.ticker}</td>
                                <td>{h.alloc.toFixed(1)}</td>
                                <td>{h.entry.toLocaleString(undefined, { minimumFractionDigits: 1, maximumFractionDigits: 2 })}</td>
                                <td className={diffClass}>{h.price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
                            </tr>
                        );
                    })}
                </tbody>
            </table>
        </div>
    );
};
