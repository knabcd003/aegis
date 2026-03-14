import { useState, useEffect, useRef, useCallback } from "react";
import { Play, FastForward, Activity, Terminal, Wifi, WifiOff, Loader2, ChevronDown } from "lucide-react";
import { ImprovementInbox } from "./ImprovementInbox";
import type { Proposal } from "./ImprovementInbox";

const API_BASE = "http://localhost:8000";
const WS_BASE = "ws://localhost:8000";

interface DeployedSystem {
    id: string;
    name: string;
    status: string;
    config?: Record<string, any>;
}

export function SandboxCanvas() {
    const [logs, setLogs] = useState<string[]>([]);
    const [isRunning, setIsRunning] = useState(false);
    const [wsConnected, setWsConnected] = useState(false);
    const [jobId, setJobId] = useState<string | null>(null);
    const scrollRef = useRef<HTMLDivElement>(null);
    const wsRef = useRef<WebSocket | null>(null);

    // System-aware state
    const [systems, setSystems] = useState<DeployedSystem[]>([]);
    const [selectedSystemId, setSelectedSystemId] = useState<string>("");
    const [tickers, setTickers] = useState("");
    const [nTrials, setNTrials] = useState(5);
    const [model, setModel] = useState("qwen3:8b");

    // Real improvement proposals
    const [proposals, setProposals] = useState<Proposal[]>([]);

    // Fetch deployed systems on mount
    useEffect(() => {
        (async () => {
            try {
                const res = await fetch(`${API_BASE}/api/systems`);
                if (res.ok) {
                    const data: DeployedSystem[] = await res.json();
                    setSystems(data);
                    if (data.length > 0) {
                        const first = data[0];
                        setSelectedSystemId(first.id);
                        const sysTickers = first.config?.asset_universe?.tickers || [];
                        setTickers(sysTickers.join(", "));
                        if (first.config?.analyst_engine?.model) {
                            setModel(first.config.analyst_engine.model);
                        }
                    }
                }
            } catch (e) {
                addLog("[SYSTEM] Could not fetch deployed systems.");
            }
        })();
    }, []);

    // When selected system changes, update tickers
    useEffect(() => {
        if (!selectedSystemId) return;
        const sys = systems.find(s => s.id === selectedSystemId);
        if (sys?.config?.asset_universe?.tickers) {
            setTickers(sys.config.asset_universe.tickers.join(", "));
        }
        if (sys?.config?.analyst_engine?.model) {
            setModel(sys.config.analyst_engine.model);
        }
    }, [selectedSystemId, systems]);

    // Fetch real improvement proposals
    useEffect(() => {
        (async () => {
            try {
                const res = await fetch(`${API_BASE}/api/improvements/pending`);
                if (res.ok) {
                    const data = await res.json();
                    setProposals(data.proposals || []);
                }
            } catch {}
        })();
    }, []);

    const connectWs = useCallback(() => {
        if (wsRef.current?.readyState === WebSocket.OPEN) return;
        const ws = new WebSocket(`${WS_BASE}/api/ws/agent_thoughts`);
        ws.onopen = () => { setWsConnected(true); addLog("[WS] Connected to telemetry stream."); };
        ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                if (data.type === "system") addLog(`[SYSTEM] ${data.message}`);
                else if (data.type === "node_update") addLog(`[${data.node}] ${data.message} (${data.latency_ms}ms)`);
                else addLog(`[STREAM] ${JSON.stringify(data)}`);
            } catch { addLog(`[RAW] ${event.data}`); }
        };
        ws.onclose = () => { setWsConnected(false); addLog("[WS] Disconnected."); };
        ws.onerror = () => { setWsConnected(false); addLog("[WS] Connection error."); };
        wsRef.current = ws;
    }, []);

    useEffect(() => { connectWs(); return () => { wsRef.current?.close(); }; }, [connectWs]);

    const addLog = (line: string) => {
        setLogs(prev => [...prev, line].slice(-1000));
    };

    useEffect(() => {
        if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }, [logs]);

    const handleApprove = async (id: string) => {
        try {
            await fetch(`${API_BASE}/api/improvements/action`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ proposal_id: id, action: "approve" })
            });
            addLog(`[HITL] Approved ${id}`);
            setProposals(prev => prev.filter(p => p.proposal_id !== id));
        } catch { addLog(`[ERROR] Failed to approve ${id}`); }
    };

    const handleReject = async (id: string) => {
        try {
            await fetch(`${API_BASE}/api/improvements/action`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ proposal_id: id, action: "reject" })
            });
            addLog(`[HITL] Rejected ${id}`);
            setProposals(prev => prev.filter(p => p.proposal_id !== id));
        } catch { addLog(`[ERROR] Failed to reject ${id}`); }
    };

    const launchSweep = async (type: "quick" | "full") => {
        setIsRunning(true);
        const tickerArray = tickers.split(",").map(t => t.trim().toUpperCase()).filter(Boolean);
        const trials = type === "quick" ? Math.min(nTrials, 3) : nTrials;
        addLog(`[SYSTEM] Launching ${type} sweep: ${tickerArray.join(", ")} × ${trials} trials`);
        try {
            const res = await fetch(`${API_BASE}/api/mlops/sweep`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ tickers: tickerArray, n_trials: trials, models_to_test: [model] })
            });
            if (!res.ok) throw new Error(`API error: ${res.status}`);
            const data = await res.json();
            setJobId(data.job_id);
            addLog(`[SYSTEM] Job accepted: ${data.job_id}`);
        } catch (e: any) {
            addLog(`[ERROR] ${e.message}`);
        } finally {
            setIsRunning(false);
        }
    };

    return (
        <div className="flex h-full">
            {/* Left: Controls */}
            <div className="w-80 border-r border-border bg-card/50 flex flex-col overflow-y-auto scrollbar-thin">
                <div className="p-5 border-b border-border">
                    <h2 className="text-base font-semibold flex items-center gap-2 mb-4">
                        <Activity className="w-5 h-5 text-accent" />
                        Sandbox
                    </h2>

                    <div className="space-y-3">
                        {/* System selector */}
                        {systems.length > 0 && (
                            <div>
                                <label className="text-[11px] text-muted-foreground uppercase tracking-wider block mb-1.5">System</label>
                                <div className="relative">
                                    <select value={selectedSystemId} onChange={e => setSelectedSystemId(e.target.value)}
                                        className="w-full bg-background border border-border rounded-lg px-3 py-2 text-sm outline-none focus:ring-1 focus:ring-accent/50 appearance-none">
                                        {systems.map(s => (
                                            <option key={s.id} value={s.id}>{s.name} ({s.status})</option>
                                        ))}
                                    </select>
                                    <ChevronDown className="w-3.5 h-3.5 text-muted-foreground absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none" />
                                </div>
                            </div>
                        )}

                        <div>
                            <label className="text-[11px] text-muted-foreground uppercase tracking-wider block mb-1.5">Tickers</label>
                            <input type="text" value={tickers} onChange={e => setTickers(e.target.value)}
                                className="w-full bg-background border border-border rounded-lg px-3 py-2 text-sm font-mono outline-none focus:ring-1 focus:ring-accent/50 uppercase" />
                        </div>
                        <div className="grid grid-cols-2 gap-3">
                            <div>
                                <label className="text-[11px] text-muted-foreground uppercase tracking-wider block mb-1.5">Trials</label>
                                <input type="number" value={nTrials} onChange={e => setNTrials(parseInt(e.target.value) || 1)} min={1} max={50}
                                    className="w-full bg-background border border-border rounded-lg px-3 py-2 text-sm font-mono outline-none focus:ring-1 focus:ring-accent/50" />
                            </div>
                            <div>
                                <label className="text-[11px] text-muted-foreground uppercase tracking-wider block mb-1.5">Model</label>
                                <select value={model} onChange={e => setModel(e.target.value)}
                                    className="w-full bg-background border border-border rounded-lg px-3 py-2 text-sm font-mono outline-none focus:ring-1 focus:ring-accent/50">
                                    <option value="qwen3:8b">qwen3:8b</option>
                                    <option value="qwen2.5:14b">qwen2.5:14b</option>
                                    <option value="llama3.1:8b">llama3.1:8b</option>
                                </select>
                            </div>
                        </div>
                    </div>

                    <div className="flex flex-col gap-2 mt-4">
                        <button onClick={() => launchSweep("quick")} disabled={isRunning}
                            className="flex items-center justify-center gap-2 py-2 rounded-lg border border-border text-sm font-medium hover:bg-muted/60 transition-colors disabled:opacity-50">
                            {isRunning ? <Loader2 className="w-4 h-4 animate-spin" /> : <FastForward className="w-4 h-4" />}
                            Quick (3 trials)
                        </button>
                        <button onClick={() => launchSweep("full")} disabled={isRunning}
                            className="flex items-center justify-center gap-2 py-2 rounded-lg bg-accent text-accent-foreground text-sm font-medium hover:bg-accent/90 transition-colors disabled:opacity-50">
                            {isRunning ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
                            Full Sweep ({nTrials} trials)
                        </button>
                    </div>

                    {jobId && (
                        <p className="mt-3 text-[11px] text-muted-foreground font-mono">
                            Last job: <span className="text-accent">{jobId}</span>
                        </p>
                    )}
                </div>

                <div className="p-5 flex-1">
                    <h3 className="text-[11px] font-semibold uppercase tracking-widest text-muted-foreground mb-3">
                        Improvement Inbox
                    </h3>
                    <ImprovementInbox
                        proposals={proposals}
                        onApprove={handleApprove}
                        onReject={handleReject}
                        onModify={(id) => addLog(`[HITL] Modify ${id}`)}
                    />
                </div>
            </div>

            {/* Right: Telemetry */}
            <div className="flex-1 bg-background flex flex-col overflow-hidden">
                <div className="px-4 py-2.5 border-b border-border flex items-center justify-between bg-card/50">
                    <div className="flex items-center gap-2">
                        <Terminal className="w-4 h-4 text-muted-foreground" />
                        <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Telemetry</span>
                    </div>
                    {wsConnected ? (
                        <span className="flex items-center gap-1.5 text-xs text-emerald-500">
                            <Wifi className="w-3 h-3" />
                            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                            Connected
                        </span>
                    ) : (
                        <button onClick={connectWs} className="flex items-center gap-1.5 text-xs text-red-400 hover:text-red-300 transition-colors">
                            <WifiOff className="w-3 h-3" />
                            Disconnected — Retry
                        </button>
                    )}
                </div>

                <div ref={scrollRef} className="flex-1 overflow-y-auto p-4 font-mono text-xs leading-relaxed scrollbar-thin">
                    {logs.length === 0 ? (
                        <div className="flex h-full items-center justify-center text-sm text-muted-foreground">
                            Awaiting simulation launch…
                        </div>
                    ) : (
                        logs.map((log, i) => (
                            <div key={i} className={`mb-0.5 whitespace-pre-wrap ${
                                log.startsWith("[ERROR]") ? "text-red-400" :
                                log.startsWith("[SYSTEM]") ? "text-accent" :
                                log.startsWith("[WS]") ? "text-amber-500" :
                                log.startsWith("[HITL]") ? "text-violet-400" :
                                "text-muted-foreground"
                            }`}>{log}</div>
                        ))
                    )}
                </div>
            </div>
        </div>
    );
}
