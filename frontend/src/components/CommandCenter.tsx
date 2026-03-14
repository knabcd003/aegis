import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Activity, Play, Square, Settings2, RefreshCw, Loader2, Wifi, AlertTriangle } from "lucide-react";

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
    const navigate = useNavigate();
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

            setQuantLoading(true);
            const tickers = new Set<string>();
            systemsData.forEach(sys => {
                if (sys.active_position?.ticker) tickers.add(sys.active_position.ticker);
            });

            const snapshots: Record<string, QuantSnapshot> = {};
            await Promise.all(
                Array.from(tickers).map(async (ticker) => {
                    const [regime, vpin] = await Promise.all([fetchRegime(ticker), fetchVpin(ticker)]);
                    snapshots[ticker] = { regime: regime?.regime, vpin_score: vpin?.vpin_score, is_toxic: vpin?.is_toxic };
                })
            );
            setQuantData(snapshots);
            setQuantLoading(false);
        } catch {
            setError("Could not connect to Aegis API. Is the FastAPI server running?");
        } finally {
            setLoading(false);
            setRefreshing(false);
        }
    };

    useEffect(() => {
        load();
        const interval = setInterval(load, 30_000);
        return () => clearInterval(interval);
    }, []);

    if (loading) {
        return (
            <div className="flex h-full items-center justify-center">
                <Loader2 className="w-5 h-5 animate-spin text-muted-foreground" />
            </div>
        );
    }

    if (error) {
        return (
            <div className="flex h-full items-center justify-center">
                <div className="rounded-lg border border-red-500/20 bg-red-500/5 text-red-400 p-6 max-w-md text-sm">
                    {error}
                </div>
            </div>
        );
    }

    return (
        <div className="max-w-5xl mx-auto p-8">
            <div className="flex items-center justify-between mb-8">
                <div>
                    <h1 className="text-2xl font-semibold tracking-tight flex items-center gap-2.5">
                        <Activity className="w-6 h-6 text-accent" />
                        Command Center
                    </h1>
                    <p className="text-sm text-muted-foreground mt-1">
                        {systems.length} system(s) deployed · Auto-refreshes every 30s
                    </p>
                </div>
                <button onClick={load} disabled={refreshing}
                    className="flex items-center gap-2 px-3 py-1.5 rounded-lg border border-border text-sm text-muted-foreground hover:text-foreground hover:bg-muted/60 transition-colors">
                    <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? "animate-spin" : ""}`} />
                    Refresh
                </button>
            </div>

            {/* Connector Banner */}
            {connectors.length > 0 && (
                <div className="flex items-center gap-3 mb-6 rounded-lg border border-border bg-card p-3">
                    <Wifi className="w-4 h-4 text-muted-foreground" />
                    <span className="text-[11px] font-semibold uppercase tracking-widest text-muted-foreground">Connectors</span>
                    {connectors.map((c, i) => (
                        <div key={i} className="flex items-center gap-1.5 ml-2">
                            <span className={`w-1.5 h-1.5 rounded-full ${
                                c.status === "MONITORING" ? "bg-emerald-500" : c.status === "DEGRADED" ? "bg-amber-500" : "bg-red-500"
                            }`} />
                            <span className={`text-xs font-mono ${
                                c.status === "MONITORING" ? "text-emerald-500" : c.status === "DEGRADED" ? "text-amber-500" : "text-red-400"
                            }`}>{c.name}</span>
                        </div>
                    ))}
                </div>
            )}

            {/* System Cards */}
            <div className="space-y-4">
                {systems.map((sys) => {
                    const ticker = sys.active_position?.ticker;
                    const quant = ticker ? quantData[ticker] : undefined;

                    return (
                        <div key={sys.id} className="rounded-lg border border-border bg-card p-5 hover:bg-muted/30 transition-colors">
                            <div className="flex items-start justify-between mb-4">
                                <div>
                                    <div className="flex items-center gap-2.5 mb-1.5">
                                        <h3 className="text-base font-semibold">{sys.name}</h3>
                                        <span className={`text-[11px] font-medium px-2 py-0.5 rounded-full ${
                                            sys.status === "ACTIVE" ? "bg-emerald-500/10 text-emerald-500" :
                                            sys.status === "PAUSED" ? "bg-muted text-muted-foreground" :
                                            "bg-amber-500/10 text-amber-500"
                                        }`}>{sys.status}</span>
                                    </div>
                                    <div className="flex items-center gap-1.5">
                                        {Object.values(sys.components).map((comp, idx) => (
                                            <span key={idx} className="text-[11px] font-mono text-muted-foreground bg-muted px-2 py-0.5 rounded">{comp}</span>
                                        ))}
                                    </div>
                                </div>
                                <div className="flex gap-2">
                                    <button onClick={() => navigate(`/sentinel/${sys.id}`)}
                                        className="text-xs px-3 py-1.5 rounded-lg border border-border text-muted-foreground hover:text-foreground hover:bg-muted/60 transition-colors flex items-center gap-1.5">
                                        <Settings2 className="w-3.5 h-3.5" />
                                        Inspect
                                    </button>
                                    {sys.status === "ACTIVE" ? (
                                        <button onClick={() => haltSystem(sys.id).then(load)}
                                            className="text-xs px-3 py-1.5 rounded-lg bg-red-500/10 text-red-400 hover:bg-red-500/20 transition-colors flex items-center gap-1.5">
                                            <Square className="w-3.5 h-3.5" />
                                            Halt
                                        </button>
                                    ) : (
                                        <button onClick={() => deploySystem(sys.id).then(load)}
                                            className="text-xs px-3 py-1.5 rounded-lg bg-emerald-500/10 text-emerald-500 hover:bg-emerald-500/20 transition-colors flex items-center gap-1.5">
                                            <Play className="w-3.5 h-3.5" />
                                            Deploy
                                        </button>
                                    )}
                                </div>
                            </div>

                            <div className="grid grid-cols-5 gap-6 pt-4 border-t border-border">
                                <div>
                                    <span className="text-[11px] text-muted-foreground uppercase tracking-wider block mb-1">PnL</span>
                                    <span className={`text-sm font-mono font-semibold ${sys.pnl_usd >= 0 ? "text-emerald-500" : "text-red-400"}`}>
                                        {sys.pnl_usd >= 0 ? "+" : ""}${Math.abs(sys.pnl_usd).toLocaleString()} ({sys.pnl_usd >= 0 ? "+" : ""}{sys.pnl_pct.toFixed(1)}%)
                                    </span>
                                </div>
                                <div>
                                    <span className="text-[11px] text-muted-foreground uppercase tracking-wider block mb-1">Position</span>
                                    <span className="text-sm">
                                        {sys.active_position
                                            ? `${sys.active_position.direction} ${sys.active_position.ticker} (${sys.active_position.shares})`
                                            : "Flat"}
                                    </span>
                                </div>
                                <div>
                                    <span className="text-[11px] text-muted-foreground uppercase tracking-wider block mb-1">HMM Regime</span>
                                    {quantLoading ? <Loader2 className="w-3 h-3 animate-spin text-muted-foreground" /> : (
                                        <span className={`text-xs font-mono font-medium px-2 py-0.5 rounded ${
                                            quant?.regime === "Bullish" ? "bg-emerald-500/10 text-emerald-500" :
                                            quant?.regime === "Bearish" ? "bg-red-500/10 text-red-400" :
                                            quant?.regime ? "bg-amber-500/10 text-amber-500" : "text-muted-foreground"
                                        }`}>{quant?.regime || (ticker ? "…" : "—")}</span>
                                    )}
                                </div>
                                <div>
                                    <span className="text-[11px] text-muted-foreground uppercase tracking-wider block mb-1">VPIN</span>
                                    {quantLoading ? <Loader2 className="w-3 h-3 animate-spin text-muted-foreground" /> : (
                                        quant?.vpin_score != null ? (
                                            <span className={`text-sm font-mono font-semibold ${quant.is_toxic ? "text-red-400" : "text-emerald-500"}`}>
                                                {quant.vpin_score.toFixed(3)} {quant.is_toxic && <AlertTriangle className="w-3 h-3 inline" />}
                                            </span>
                                        ) : <span className="text-muted-foreground text-xs">{ticker ? "…" : "—"}</span>
                                    )}
                                </div>
                                <div>
                                    <span className="text-[11px] text-muted-foreground uppercase tracking-wider block mb-1">Last Action</span>
                                    <span className="text-xs text-muted-foreground">{sys.activity[0]?.event || "None"}</span>
                                </div>
                            </div>
                        </div>
                    );
                })}

                {systems.length === 0 && (
                    <div className="text-center py-16 text-muted-foreground text-sm rounded-lg border border-border bg-card">
                        No systems deployed. Use the Strategy Wizard to create one.
                    </div>
                )}
            </div>
        </div>
    );
}
