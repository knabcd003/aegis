import { useEffect, useState } from "react";
import { Activity, Play, Square, Settings2, RefreshCw, Layers } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { SignalCard, type SignalCardData } from "./SignalCard";

const API_BASE = "http://localhost:8000";

interface ActivePosition {
    ticker: string;
    direction: string;
    shares: number;
    entry_price: number;
}

interface ActivityEvent {
    ts: string;
    event: string;
    ticker: string;
    rationale: string;
}

interface GapAnalysis {
    actual_nav: number;
    mirror_nav: number;
    absolute_gap: number;
    actual_return_pct: number;
    mirror_return_pct: number;
    human_outperformance: boolean;
}

interface TradingSystem {
    id: string;
    name: string;
    status: "ACTIVE" | "PAUSED" | "BACKTESTING" | "DEGRADED" | "OFFLINE";
    components: {
        data_engine: string;
        quant_engine: string;
        analyst_engine: string;
    };
    pnl_usd: number;
    pnl_pct: number;
    active_position: ActivePosition | null;
    activity: ActivityEvent[];
    pending_signals: SignalCardData[];
    gap_analysis: GapAnalysis;
}

async function fetchSystems(): Promise<TradingSystem[]> {
    const res = await fetch(`${API_BASE}/api/systems`);
    if (!res.ok) throw new Error(`API error: ${res.status}`);
    return res.json();
}

async function haltSystem(id: string): Promise<void> {
    await fetch(`${API_BASE}/api/systems/${id}/halt`, { method: "POST" });
}

async function deploySystem(id: string): Promise<void> {
    await fetch(`${API_BASE}/api/systems/${id}/deploy`, { method: "POST" });
}

export function CommandCenter() {
    const [systems, setSystems] = useState<TradingSystem[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [refreshing, setRefreshing] = useState(false);

    const load = async () => {
        try {
            setRefreshing(true);
            const data = await fetchSystems();
            setSystems(data);
            setError(null);
        } catch (e) {
            setError("Could not connect to Aegis API. Is the FastAPI server running?");
        } finally {
            setLoading(false);
            setRefreshing(false);
        }
    };

    useEffect(() => {
        load();
        // Poll every 10 seconds for live updates
        const interval = setInterval(load, 10_000);
        return () => clearInterval(interval);
    }, []);

    const handleHalt = async (id: string) => {
        await haltSystem(id);
        await load();
    };

    const handleDeploy = async (id: string) => {
        await deploySystem(id);
        await load();
    };

    const handleAcceptSignal = async (systemId: string, cardId: string) => {
        await fetch(`${API_BASE}/api/systems/${systemId}/signals/${cardId}/accept`, { method: "POST" });
        await load();
    };

    const handleDeclineSignal = async (systemId: string, cardId: string) => {
        await fetch(`${API_BASE}/api/systems/${systemId}/signals/${cardId}/decline`, { method: "POST" });
        await load();
    };

    const formatPosition = (pos: ActivePosition | null) => {
        if (!pos) return "FLAT";
        return `${pos.direction} ${pos.ticker} (${pos.shares} shares @ $${pos.entry_price})`;
    };

    const formatPnl = (usd: number, pct: number) => {
        const sign = usd >= 0 ? "+" : "";
        return `${sign}$${Math.abs(usd).toLocaleString()} (${sign}${pct.toFixed(1)}%)`;
    };

    if (loading) {
        return (
            <div className="flex h-full items-center justify-center">
                <div className="text-muted-foreground text-sm animate-pulse">Connecting to Aegis backend…</div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="flex h-full items-center justify-center">
                <div className="border border-red-500/30 bg-red-500/10 text-red-400 rounded-lg p-6 max-w-md text-sm font-mono">
                    {error}
                </div>
            </div>
        );
    }

    return (
        <div className="flex flex-col h-full w-full bg-background p-6 overflow-auto">
            <div className="flex items-center justify-between mb-8 border-b border-border pb-4">
                <div>
                    <h1 className="text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
                        <Activity className="h-6 w-6 text-blue-500" />
                        Command Center
                    </h1>
                    <p className="text-muted-foreground mt-1 text-sm">
                        Monitor live autonomous trading systems • Auto-refreshes every 10s
                    </p>
                </div>
                <button
                    onClick={load}
                    disabled={refreshing}
                    className="flex items-center gap-2 px-4 py-2 rounded-md border border-border text-muted-foreground hover:text-foreground hover:bg-secondary/50 text-sm transition-colors"
                >
                    <RefreshCw className={`w-4 h-4 ${refreshing ? "animate-spin" : ""}`} />
                    Refresh
                </button>
            </div>

            <div className="grid grid-cols-1 gap-4">
                {systems.map((sys) => (
                    <div
                        key={sys.id}
                        className="border border-border rounded-lg bg-card/50 p-5 flex flex-col md:flex-row items-start md:items-center justify-between gap-4 hover:bg-card transition-colors"
                    >
                        <div className="flex-1">
                            <div className="flex items-center gap-3 mb-2">
                                <h3 className="font-semibold text-lg text-primary">{sys.name}</h3>
                                <Badge
                                    variant={sys.status === "ACTIVE" ? "default" : "secondary"}
                                    className={sys.status === "ACTIVE" ? "bg-green-500/10 text-green-400 border-green-500/20" : ""}
                                >
                                    {sys.status}
                                </Badge>
                            </div>

                            {/* Component Stack */}
                            <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground font-mono mb-3">
                                {Object.values(sys.components).map((comp, idx) => (
                                    <span key={idx} className="bg-secondary px-2 py-1 rounded-md">{comp}</span>
                                ))}
                            </div>

                            {/* Live Stats */}
                            <div className="grid grid-cols-4 gap-4 text-sm mt-4">
                                <div>
                                    <span className="text-muted-foreground block text-xs uppercase tracking-wider mb-1">Live PnL</span>
                                    <span className={`font-mono font-semibold ${sys.pnl_usd >= 0 ? "text-green-400" : "text-red-400"}`}>
                                        {formatPnl(sys.pnl_usd, sys.pnl_pct)}
                                    </span>
                                </div>
                                <div className="border border-border/50 rounded-md p-2 bg-[#0d0d12]">
                                    <span className="text-muted-foreground block text-[10px] uppercase tracking-wider mb-1">Human Gap</span>
                                    <span className={`font-mono font-semibold text-xs ${sys.gap_analysis?.absolute_gap >= 0 ? "text-green-400" : "text-red-400"}`}>
                                        {sys.gap_analysis ? formatPnl(sys.gap_analysis.absolute_gap, sys.gap_analysis.actual_return_pct - sys.gap_analysis.mirror_return_pct) : '$0 (0%)'}
                                    </span>
                                </div>
                                <div>
                                    <span className="text-muted-foreground block text-xs uppercase tracking-wider mb-1">Active Position</span>
                                    <span className="font-semibold text-sm">{formatPosition(sys.active_position)}</span>
                                </div>
                                <div>
                                    <span className="text-muted-foreground block text-xs uppercase tracking-wider mb-1">Last Action</span>
                                    <span className="italic text-gray-400 truncate">
                                        {sys.activity[0]
                                            ? `[${sys.activity[0].event}]`
                                            : "No activity yet"}
                                    </span>
                                </div>
                            </div>
                        </div>

                        {/* Action Buttons */}
                        <div className="flex flex-col gap-2 min-w-[150px]">
                            <button className="flex items-center justify-center gap-2 w-full bg-blue-500/10 hover:bg-blue-500/20 text-blue-400 border border-blue-500/20 px-4 py-2 rounded-md text-sm font-medium transition-colors">
                                <Settings2 className="w-4 h-4" />
                                Inspect Glass Box
                            </button>
                            {sys.status === "ACTIVE" ? (
                                <button
                                    onClick={() => handleHalt(sys.id)}
                                    className="flex items-center justify-center gap-2 w-full bg-red-500/10 hover:bg-red-500/20 text-red-400 border border-red-500/20 px-4 py-2 rounded-md text-sm font-medium transition-colors"
                                >
                                    <Square className="w-4 h-4" />
                                    Halt System
                                </button>
                            ) : (
                                <button
                                    onClick={() => handleDeploy(sys.id)}
                                    className="flex items-center justify-center gap-2 w-full bg-green-500/10 hover:bg-green-500/20 text-green-400 border border-green-500/20 px-4 py-2 rounded-md text-sm font-medium transition-colors"
                                >
                                    <Play className="w-4 h-4" />
                                    Deploy System
                                </button>
                            )}
                        </div>
                    </div>
                ))}
            </div>

            {/* Pending Signal Cards */}
            {systems.some(s => s.pending_signals?.length > 0) && (
                <div className="mt-8 border-t border-border pt-6">
                    <h2 className="text-xl font-bold tracking-tight text-foreground flex items-center gap-2 mb-4">
                        <Layers className="h-5 w-5 text-purple-400" />
                        Pending Signals Queue
                    </h2>
                    <div className="grid grid-cols-1 xl:grid-cols-2 gap-6 overflow-y-auto max-h-[500px] pr-2 scrollbar-thin scrollbar-thumb-gray-700">
                        {systems.flatMap(sys => 
                            (sys.pending_signals || []).map(sig => (
                                <SignalCard 
                                    key={sig.card_id} 
                                    signal={sig} 
                                    onAccept={(id) => handleAcceptSignal(sys.id, id)} 
                                    onDecline={(id) => handleDeclineSignal(sys.id, id)} 
                                />
                            ))
                        )}
                    </div>
                </div>
            )}
        </div>
    );
}
