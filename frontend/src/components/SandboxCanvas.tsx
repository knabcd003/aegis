import { useState, useEffect, useRef, useCallback } from "react";
import { Play, FastForward, Activity, Terminal, Wifi, WifiOff, Loader2 } from "lucide-react";
import { ImprovementInbox } from "./ImprovementInbox";

const API_BASE = "http://localhost:8000";
const WS_BASE = "ws://localhost:8000";

export function SandboxCanvas() {
    const [logs, setLogs] = useState<string[]>([]);
    const [isRunning, setIsRunning] = useState(false);
    const [wsConnected, setWsConnected] = useState(false);
    const [jobId, setJobId] = useState<string | null>(null);
    const scrollRef = useRef<HTMLDivElement>(null);
    const wsRef = useRef<WebSocket | null>(null);
    
    // Run config state
    const [tickers, setTickers] = useState("AAPL, MSFT, NVDA");
    const [nTrials, setNTrials] = useState(5);
    const [model, setModel] = useState("qwen3:8b");

    // Connect to WebSocket on mount
    const connectWs = useCallback(() => {
        if (wsRef.current?.readyState === WebSocket.OPEN) return;
        
        const ws = new WebSocket(`${WS_BASE}/api/ws/agent_thoughts`);
        
        ws.onopen = () => {
            setWsConnected(true);
            addLog("[WS] Connected to Aegis telemetry stream.");
        };
        
        ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                if (data.type === "system") {
                    addLog(`[SYSTEM] ${data.message}`);
                } else if (data.type === "node_update") {
                    addLog(`[${data.node}] ${data.message} (${data.latency_ms}ms)`);
                } else if (data.type === "improvement_proposal") {
                    addLog(`[IMPROVEMENT] New proposal: ${data.target_param}`);
                } else {
                    addLog(`[STREAM] ${JSON.stringify(data)}`);
                }
            } catch {
                addLog(`[RAW] ${event.data}`);
            }
        };
        
        ws.onclose = () => {
            setWsConnected(false);
            addLog("[WS] Disconnected from telemetry stream.");
        };
        
        ws.onerror = () => {
            setWsConnected(false);
            addLog("[WS] Connection error. Is the FastAPI server running?");
        };
        
        wsRef.current = ws;
    }, []);
    
    useEffect(() => {
        connectWs();
        return () => {
            wsRef.current?.close();
        };
    }, [connectWs]);
    
    const addLog = (line: string) => {
        setLogs(prev => {
            const updated = [...prev, line];
            return updated.slice(-1000);
        });
    };

    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [logs]);

    const launchSweep = async (type: "quick" | "full") => {
        setIsRunning(true);
        const tickerArray = tickers.split(",").map(t => t.trim().toUpperCase()).filter(Boolean);
        const trials = type === "quick" ? Math.min(nTrials, 3) : nTrials;
        
        addLog(`[SYSTEM] Launching ${type} sweep: ${tickerArray.join(", ")} × ${trials} trials using ${model}`);
        
        try {
            const res = await fetch(`${API_BASE}/api/mlops/sweep`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    tickers: tickerArray,
                    n_trials: trials,
                    models_to_test: [model]
                })
            });
            
            if (!res.ok) throw new Error(`API error: ${res.status}`);
            
            const data = await res.json();
            setJobId(data.job_id);
            addLog(`[SYSTEM] Sweep accepted. Job ID: ${data.job_id}`);
            addLog(`[SYSTEM] ${data.message}`);
        } catch (e: any) {
            addLog(`[ERROR] Failed to launch sweep: ${e.message}`);
        } finally {
            setIsRunning(false);
        }
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
                    
                    {/* Run Configuration */}
                    <div className="space-y-3 mb-4">
                        <div>
                            <label className="text-xs text-gray-500 uppercase tracking-wider block mb-1">Tickers</label>
                            <input
                                type="text"
                                value={tickers}
                                onChange={e => setTickers(e.target.value)}
                                className="w-full bg-[#0d0d12] border border-border/80 rounded px-3 py-2 text-sm text-blue-400 font-mono outline-none focus:border-cyan-500/50 uppercase"
                            />
                        </div>
                        <div className="grid grid-cols-2 gap-3">
                            <div>
                                <label className="text-xs text-gray-500 uppercase tracking-wider block mb-1">Trials</label>
                                <input
                                    type="number"
                                    value={nTrials}
                                    onChange={e => setNTrials(parseInt(e.target.value) || 1)}
                                    min={1}
                                    max={50}
                                    className="w-full bg-[#0d0d12] border border-border/80 rounded px-3 py-2 text-sm text-cyan-400 font-mono outline-none focus:border-cyan-500/50"
                                />
                            </div>
                            <div>
                                <label className="text-xs text-gray-500 uppercase tracking-wider block mb-1">Model</label>
                                <select
                                    value={model}
                                    onChange={e => setModel(e.target.value)}
                                    className="w-full bg-[#0d0d12] border border-border/80 rounded px-3 py-2 text-sm text-purple-400 font-mono outline-none focus:border-cyan-500/50"
                                >
                                    <option value="qwen3:8b">qwen3:8b</option>
                                    <option value="qwen2.5:14b">qwen2.5:14b</option>
                                    <option value="llama3.1:8b">llama3.1:8b</option>
                                </select>
                            </div>
                        </div>
                    </div>
                    
                    <div className="flex flex-col gap-3">
                        <button 
                            onClick={() => launchSweep("quick")}
                            disabled={isRunning}
                            className="flex items-center justify-center gap-2 bg-blue-500/10 hover:bg-blue-500/20 text-blue-400 border border-blue-500/30 py-2.5 rounded text-sm font-semibold transition-colors disabled:opacity-50"
                        >
                            {isRunning ? <Loader2 className="w-4 h-4 animate-spin" /> : <FastForward className="w-4 h-4" />}
                            Quick Iteration (3 trials)
                        </button>
                        <button 
                            onClick={() => launchSweep("full")}
                            disabled={isRunning}
                            className="flex items-center justify-center gap-2 bg-purple-500/10 hover:bg-purple-500/20 text-purple-400 border border-purple-500/30 py-2.5 rounded text-sm font-semibold transition-colors disabled:opacity-50"
                        >
                            {isRunning ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
                            Full Sweep ({nTrials} trials)
                        </button>
                    </div>
                    
                    {jobId && (
                        <div className="mt-3 text-xs text-gray-500 font-mono">
                            Last job: <span className="text-cyan-400">{jobId}</span>
                        </div>
                    )}
                </div>

                <div className="flex-1 min-h-0">
                    <h3 className="text-sm font-bold uppercase tracking-wider text-muted-foreground mb-3 pl-1">
                        Agent Proposal Inbox
                    </h3>
                    <ImprovementInbox 
                        proposals={[]}
                        onApprove={(id) => addLog(`[HITL] Approved proposal ${id}`)}
                        onReject={(id) => addLog(`[HITL] Rejected proposal ${id}`)}
                        onModify={(id) => addLog(`[HITL] Opening config editor for proposal ${id}`)}
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
                    <div className="flex items-center gap-2 text-xs">
                        {wsConnected ? (
                            <span className="flex items-center gap-1 text-green-400">
                                <Wifi className="w-3 h-3" />
                                <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
                                Connected
                            </span>
                        ) : (
                            <button 
                                onClick={connectWs} 
                                className="flex items-center gap-1 text-red-400 hover:text-red-300 transition-colors"
                            >
                                <WifiOff className="w-3 h-3" />
                                Disconnected — Click to retry
                            </button>
                        )}
                    </div>
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
                            <div key={i} className={`mb-0.5 whitespace-pre-wrap word-break-all ${
                                log.startsWith("[ERROR]") ? "text-red-400" : 
                                log.startsWith("[SYSTEM]") ? "text-cyan-400" : 
                                log.startsWith("[WS]") ? "text-yellow-400" :
                                log.startsWith("[HITL]") ? "text-purple-400" : ""
                            }`}>
                                {log}
                            </div>
                        ))
                    )}
                </div>
            </div>
        </div>
    );
}
