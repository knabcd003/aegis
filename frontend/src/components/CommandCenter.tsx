import { useEffect, useState } from "react";
import { Activity, Play, Square, Settings2, RefreshCw, Loader2, Wifi, AlertTriangle } from "lucide-react";
import { Badge } from "@/components/ui/badge";


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
}

interface QuantSnapshot {
    regime?: string;
    vpin_score?: number;
    is_toxic?: boolean;
}

interface ConnectorStatus {
    name: string;
    status: string;
    last_successful_fetch: string | null;
}

async function fetchSystems(): Promise<TradingSystem[]> {
    const res = await fetch(`${API_BASE}/api/systems`);
    if (!res.ok) throw new Error(`API error: ${res.status}`);
    return res.json();
}

async function fetchRegime(ticker: string): Promise<{ regime: string } | null> {
    try {
        const res = await fetch(`${API_BASE}/api/quant/regime?ticker=${ticker}`);
        if (!res.ok) return null;
        return res.json();
    } catch { return null; }
}

async function fetchVpin(ticker: string): Promise<{ vpin_score: number; is_toxic: boolean } | null> {
    try {
        const res = await fetch(`${API_BASE}/api/quant/vpin?ticker=${ticker}`);
        if (!res.ok) return null;
        return res.json();
    } catch { return null; }
}

async function fetchConnectorHealth(): Promise<ConnectorStatus[]> {
    try {
        const res = await fetch(`${API_BASE}/api/system-health/connectors`);
        if (!res.ok) return [];
        const data = await res.json();
        return data.connectors || [];
    } catch { return []; }
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
    const [quantData, setQuantData] = useState<Record<string, QuantSnapshot>>({});
    const [connectors, setConnectors] = useState<ConnectorStatus[]>([]);
    const [quantLoading, setQuantLoading] = useState(false);

    const load = async () => {
        try {
            setRefreshing(true);
            const [systemsData, connectorData] = await Promise.all([
                fetchSystems(),
                fetchConnectorHealth()
            ]);
            setSystems(systemsData);
            setConnectors(connectorData);
            setError(null);
            
            // Fetch quant data for each active system's ticker
            setQuantLoading(true);
            const tickers = new Set<string>();
            systemsData.forEach(sys => {
                if (sys.active_position?.ticker) {
                    tickers.add(sys.active_position.ticker);
                }
            });
            
            const snapshots: Record<string, QuantSnapshot> = {};
            await Promise.all(
                Array.from(tickers).map(async (ticker) => {
                    const [regime, vpin] = await Promise.all([
                        fetchRegime(ticker),
                        fetchVpin(ticker)
                    ]);
                    snapshots[ticker] = {
                        regime: regime?.regime,
                        vpin_score: vpin?.vpin_score,
                        is_toxic: vpin?.is_toxic
                    };
                })
            );
            setQuantData(snapshots);
            setQuantLoading(false);
        } catch (e) {
            setError("Could not connect to Aegis API. Is the FastAPI server running?");
        } finally {
            setLoading(false);
            setRefreshing(false);
        }
    };

    useEffect(() => {
        load();
        const interval = setInterval(load, 30_000); // Poll every 30s
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
                <div className="flex items-center gap-2 text-muted-foreground text-sm">
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Connecting to Aegis backend…
                </div>
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
            <div className="flex items-center justify-between mb-6 border-b border-border pb-4">
                <div>
                    <h1 className="text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
                        <Activity className="h-6 w-6 text-blue-500" />
                        Command Center
                    </h1>
                    <p className="text-muted-foreground mt-1 text-sm">
                        {systems.length} system(s) deployed • Auto-refreshes every 30s
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

            {/* Connector Health Bar */}
            {connectors.length > 0 && (
                <div className="flex items-center gap-3 mb-6 bg-card/50 border border-border rounded-lg p-3">
                    <Wifi className="w-4 h-4 text-gray-500" />
                    <span className="text-xs text-gray-500 uppercase tracking-wider font-bold">Connectors:</span>
                    {connectors.map((c, i) => (
                        <div key={i} className="flex items-center gap-1.5">
                            <span className={`w-2 h-2 rounded-full ${
                                c.status === "MONITORING" ? "bg-green-500" : 
                                c.status === "DEGRADED" ? "bg-yellow-500" : "bg-red-500"
                            }`} />
                            <span className={`text-xs font-mono ${
                                c.status === "MONITORING" ? "text-green-400" : 
                                c.status === "DEGRADED" ? "text-yellow-400" : "text-red-400"
                            }`}>{c.name}</span>
                        </div>
                    ))}
                </div>
            )}

            <div className="grid grid-cols-1 gap-4">
                {systems.map((sys) => {
                    const ticker = sys.active_position?.ticker;
                    const quant = ticker ? quantData[ticker] : undefined;
                    
                    return (
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
                                <div className="grid grid-cols-5 gap-4 text-sm mt-4">
                                    <div>
                                        <span className="text-muted-foreground block text-xs uppercase tracking-wider mb-1">Live PnL</span>
                                        <span className={`font-mono font-semibold ${sys.pnl_usd >= 0 ? "text-green-400" : "text-red-400"}`}>
                                            {formatPnl(sys.pnl_usd, sys.pnl_pct)}
                                        </span>
                                    </div>
                                    <div>
                                        <span className="text-muted-foreground block text-xs uppercase tracking-wider mb-1">Active Position</span>
                                        <span className="font-semibold text-sm">{formatPosition(sys.active_position)}</span>
                                    </div>
                                    {/* Real Quant Data */}
                                    <div>
                                        <span className="text-muted-foreground block text-xs uppercase tracking-wider mb-1">HMM Regime</span>
                                        {quantLoading ? (
                                            <Loader2 className="w-3 h-3 animate-spin text-gray-500" />
                                        ) : (
                                            <span className={`font-mono font-bold text-xs px-2 py-0.5 rounded ${
                                                quant?.regime === "Bullish" ? "bg-green-500/20 text-green-400" :
                                                quant?.regime === "Bearish" ? "bg-red-500/20 text-red-400" :
                                                quant?.regime ? "bg-yellow-500/20 text-yellow-400" : "text-gray-500"
                                            }`}>
                                                {quant?.regime || (ticker ? "Loading…" : "—")}
                                            </span>
                                        )}
                                    </div>
                                    <div>
                                        <span className="text-muted-foreground block text-xs uppercase tracking-wider mb-1">VPIN Toxicity</span>
                                        {quantLoading ? (
                                            <Loader2 className="w-3 h-3 animate-spin text-gray-500" />
                                        ) : quant?.vpin_score != null ? (
                                            <span className={`font-mono font-bold text-sm ${quant.is_toxic ? "text-red-400" : "text-green-400"}`}>
                                                {quant.vpin_score.toFixed(3)} {quant.is_toxic && <AlertTriangle className="w-3 h-3 inline text-red-400" />}
                                            </span>
                                        ) : (
                                            <span className="text-gray-500 text-xs">{ticker ? "No data" : "—"}</span>
                                        )}
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
                    );
                })}

                {systems.length === 0 && (
                    <div className="text-center py-16 text-muted-foreground text-sm">
                        No systems deployed. Use the Strategy Wizard to create one.
                    </div>
                )}
            </div>
        </div>
    );
}
