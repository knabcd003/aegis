import { useState, useEffect, useRef } from "react";
import { Play, FastForward, Activity, Terminal } from "lucide-react";
import { ImprovementInbox, type Proposal } from "./ImprovementInbox";

export function SandboxCanvas() {
    const [logs, setLogs] = useState<string[]>([]);
    const [isRunning, setIsRunning] = useState(false);
    const scrollRef = useRef<HTMLDivElement>(null);

    // Mock proposals
    const mockProposals: Proposal[] = [
        {
            proposal_id: "prop-42",
            target_param: "quant_engine.vpin.toxicity_threshold",
            current_value: 0.85,
            proposed_value: 0.75,
            rationale: "VPIN threshold of 0.85 caused 18 missed entries in confirmed Bull regime. Lowering to 0.75 would have captured 11 of them with avg +2.1% forward return.",
            expected_delta: { sharpe: "+0.23", alpha_pct: "+1.8%", additional_trades: 8 },
            risk_of_change: "May increase false signals in volatile periods. Risk Agent veto rate expected to rise from 12% to 18%."
        }
    ];

    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [logs]);

    const runSimulation = (type: "quick" | "full") => {
        setIsRunning(true);
        setLogs(prev => [...prev, `[SYSTEM] Launching ${type} simulation...`, `[SYSTEM] Connecting to WebSocket telemetry stream...`]);
        
        // Mock WebSocket rapid burst stream to test performance
        let count = 0;
        const interval = setInterval(() => {
            if (count > 50) {
                clearInterval(interval);
                setIsRunning(false);
                setLogs(prev => [...prev, `[SYSTEM] Simulation complete. Analyzing MLflow traces...`, `[IMPROVEMENT AGENT] Proposal prop-42 generated.`]);
                return;
            }
            // Add batch of logs to test rendering dense text
            const newLogs = Array.from({ length: 5 }).map((_, i) => 
                `[AGENT TRACE] Node analyst evaluated data_snapshot at T=${count}-${i}: VPIN OK, HMM Bullish. Proposal: BUY.`
            );
            setLogs(prev => {
                // Keep max 1000 lines to prevent browser crash
                const updated = [...prev, ...newLogs];
                return updated.slice(-1000);
            });
            count++;
        }, 100);
    };

    return (
        <div className="h-full w-full flex gap-4 overflow-hidden">
            {/* Left Panel: Controls & Inbox */}
            <div className="w-1/3 flex flex-col gap-4 overflow-y-auto pr-2 scrollbar-thin scrollbar-thumb-gray-700">
                <div className="bg-card/50 border border-border p-5 rounded-lg">
                    <h2 className="text-lg font-bold flex items-center gap-2 mb-4">
                        <Activity className="text-cyan-400 w-5 h-5" />
                        Sandbox Orchestrator
                    </h2>
                    
                    <div className="flex flex-col gap-3">
                        <button 
                            onClick={() => runSimulation("quick")}
                            disabled={isRunning}
                            className="flex items-center justify-center gap-2 bg-blue-500/10 hover:bg-blue-500/20 text-blue-400 border border-blue-500/30 py-2.5 rounded text-sm font-semibold transition-colors disabled:opacity-50"
                        >
                            <FastForward className="w-4 h-4" />
                            Quick Iteration Run (90 Day)
                        </button>
                        <button 
                            onClick={() => runSimulation("full")}
                            disabled={isRunning}
                            className="flex items-center justify-center gap-2 bg-purple-500/10 hover:bg-purple-500/20 text-purple-400 border border-purple-500/30 py-2.5 rounded text-sm font-semibold transition-colors disabled:opacity-50"
                        >
                            <Play className="w-4 h-4" />
                            Full Production Backtest
                        </button>
                    </div>
                </div>

                <div className="flex-1 min-h-0">
                    <h3 className="text-sm font-bold uppercase tracking-wider text-muted-foreground mb-3 pl-1">
                        Agent Proposal Inbox
                    </h3>
                    <ImprovementInbox 
                        proposals={!isRunning && logs.length > 0 ? mockProposals : []}
                        onApprove={(id) => console.log('Approved', id)}
                        onReject={(id) => console.log('Rejected', id)}
                        onModify={(id) => console.log('Opening ConfigEditor for', id)}
                    />
                </div>
            </div>

            {/* Right Panel: Telemetry Stream */}
            <div className="flex-1 bg-[#0a0a0f] border border-border/80 rounded-lg flex flex-col overflow-hidden relative">
                <div className="bg-[#14141b] px-4 py-2 border-b border-border/80 flex items-center justify-between z-10">
                    <div className="flex items-center gap-2">
                        <Terminal className="w-4 h-4 text-cyan-400" />
                        <span className="text-xs uppercase tracking-wider font-bold text-gray-300">Live Telemetry Stream</span>
                    </div>
                    {isRunning && (
                        <div className="flex items-center gap-2 text-xs text-green-400">
                            <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
                            Streaming
                        </div>
                    )}
                </div>
                
                <div 
                    ref={scrollRef}
                    className="flex-1 overflow-y-auto p-4 font-mono text-xs text-green-500/80 leading-relaxed scrollbar-thin scrollbar-thumb-gray-700"
                >
                    {logs.length === 0 ? (
                        <div className="flex h-full items-center justify-center opacity-30 text-sm">
                            Awaiting simulation launch...
                        </div>
                    ) : (
                        logs.map((log, i) => (
                            <div key={i} className="mb-0.5 whitespace-pre-wrap word-break-all">
                                {log}
                            </div>
                        ))
                    )}
                </div>
            </div>
        </div>
    );
}
