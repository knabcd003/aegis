import React, { useEffect, useRef, useState } from 'react';

// Static logs matched to UI mockup for fast prototyping setup
const INITIAL_LOGS = [
    { time: '[14:02:11]', agent: 'RESEARCHER:', text: 'Found high-frequency sentiment shift in $BTC on X (Twitter). Index: 0.82 (Bullish).', sys: false, comment: false, kind: 'res' },
    { time: '[14:02:12]', agent: 'QUANT:', text: 'Recalculating mean reversion targets for BTC/USD 5m timeframe...', sys: false, comment: false, kind: 'quant' },
    { time: '[14:02:14]', agent: 'QUANT:', text: 'Target Alpha identified at µ=64,305. Probability: 68.2%.', sys: false, comment: false, kind: 'quant' },
    { time: '[14:02:15]', agent: 'ANALYST:', text: 'Risk check passed. VaR within 1.5% daily threshold. Liquidity depth confirmed.', sys: false, comment: false, kind: 'analyst' },
    { time: '[14:02:16]', agent: 'SENTINEL:', text: 'Monitoring exchange orderbook for spoofing walls... Clear.', sys: false, comment: false, kind: 'sentinel' },
    { time: '[14:02:18]', agent: 'SYSTEM:', text: 'LIMIT BUY order executed - 0.5 BTC @ $64,281.40.', sys: true, comment: false, kind: 'sys' },
    { time: null, agent: null, text: '# GET /api/v3/ticker/bookTicker?symbol=BTCUSDT HTTP/1.1 200 OK', sys: false, comment: true, kind: 'comment' },
    { time: '[14:02:40]', agent: 'RESEARCHER:', text: 'Monitoring Fed rate speech transcripts... No significant divergence detected.', sys: false, comment: false, kind: 'res' },
    { time: '[14:02:41]', agent: 'QUANT:', text: 'Adjusting dynamic SL for $SOL position to breakeven + 0.5%.', sys: false, comment: false, kind: 'quant' },
    { time: null, agent: null, text: '... awaiting next packet ...', sys: false, comment: true, kind: 'comment' }
];

export const TerminalStream: React.FC = () => {
    const [logs, setLogs] = useState<{ time: string | null; agent: string | null; text: string; sys: boolean; comment: boolean; kind: string }[]>([]);
    const endRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        // Init logs manually for static view to keep the initial dashboard look
        setLogs(INITIAL_LOGS);

        const ws = new WebSocket('ws://localhost:8000/api/stream-logs');

        ws.onmessage = (event) => {
            const now = new Date();
            const timeStr = `[${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}:${now.getSeconds().toString().padStart(2, '0')}]`;

            // Basic parsing to try to colorize the websocket logs roughly matching previous patterns
            const dataStr = event.data;
            let agent = 'SYSTEM:';
            let kind = 'sys';
            let text = dataStr;
            let isComment = false;

            if (dataStr.startsWith('[Researcher]')) { agent = 'RESEARCHER:'; kind = 'res'; text = dataStr.replace('[Researcher]', '').trim(); }
            else if (dataStr.startsWith('[Quant]')) { agent = 'QUANT:'; kind = 'quant'; text = dataStr.replace('[Quant]', '').trim(); }
            else if (dataStr.startsWith('[Analyst]')) { agent = 'ANALYST:'; kind = 'analyst'; text = dataStr.replace('[Analyst]', '').trim(); }
            else if (dataStr.startsWith('[System]')) { agent = 'SYSTEM:'; kind = 'sys'; text = dataStr.replace('[System]', '').trim(); }
            else if (dataStr.startsWith('[Error]')) { agent = 'ERROR:'; kind = 'sys'; text = dataStr.replace('[Error]', '').trim(); }

            const newLog = {
                time: timeStr,
                agent,
                text,
                sys: kind === 'sys',
                comment: isComment,
                kind
            };

            setLogs(prev => [...prev, newLog].slice(-50)); // Keep last 50
        };

        return () => ws.close();
    }, []);

    useEffect(() => {
        endRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [logs]);

    return (
        <div className="terminal-section">
            <div className="terminal-header">
                <span>LIVE EXECUTION STREAM <span style={{ color: 'var(--text-muted)', fontWeight: 400, marginLeft: '8px' }}>Filter: [ALL_AGENTS]</span></span>
                <span className="meta">latency: 14ms  load: 12.4%</span>
            </div>
            <div className="terminal-output">
                {logs.map((log, i) => (
                    <div key={i} className="term-line">
                        {log.comment ? (
                            <span className="term-comment">{log.text}</span>
                        ) : (
                            <>
                                <span className="term-time">{log.time} </span>
                                <span className={`term-agent-${log.kind} ${log.kind === 'sys' ? 'term-sys' : ''}`}>{log.agent}</span>
                                <span> {log.text}</span>
                            </>
                        )}
                    </div>
                ))}
                <div ref={endRef} />
            </div>
        </div>
    );
};
