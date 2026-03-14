import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
    ArrowLeft, Activity, Square, Play, RefreshCw, Loader2, AlertTriangle,
    Settings2, Wallet, BarChart2, Bell, Clock, CheckCircle2, XCircle,
    TrendingUp, TrendingDown, Wifi
} from "lucide-react";

const API_BASE = "http://localhost:8000";

interface TradingSystem {
    id: string;
    name: string;
    status: string;
    components: Record<string, string>;
    pnl_usd: number;
    pnl_pct: number;
    active_position: { ticker: string; direction: string; shares: number; entry_price: number } | null;
    activity: { ts: string; event: string; ticker: string; rationale: string }[];
    config?: Record<string, any>;
    pending_cards?: number;
}

interface SignalCard {
    card_id: string;
    ticker: string;
    decision: string;
    thesis: string;
    quant_anchors: Record<string, any>;
    sub_agent_votes: Record<string, string>;
    confidence: number;
    generated_at: string;
    status: string;
}

interface QuantSnapshot {
    ticker: string;
    regime?: string;
    vpin_score?: number;
    is_toxic?: boolean;
}

export function SentinelDetail() {
    const { id } = useParams<{ id: string }>();
    const navigate = useNavigate();
    const [system, setSystem] = useState<TradingSystem | null>(null);
    const [signals, setSignals] = useState<SignalCard[]>([]);
    const [quantData, setQuantData] = useState<QuantSnapshot[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const load = async () => {
        if (!id) return;
        try {
            setLoading(true);
            // Fetch system details
            const sysRes = await fetch(`${API_BASE}/api/systems/${id}`);
            if (!sysRes.ok) throw new Error(`System not found: ${sysRes.status}`);
            const sysData = await sysRes.json();
            setSystem(sysData);

            // Fetch signal cards
            try {
                const sigRes = await fetch(`${API_BASE}/api/systems/${id}/signals`);
                if (sigRes.ok) {
                    const sigData = await sigRes.json();
                    setSignals(sigData.cards || []);
                }
            } catch { /* signals endpoint may not exist for seed systems */ }

            // Fetch quant data for each ticker in universe
            const tickers: string[] = sysData.config?.asset_universe?.tickers ||
                (sysData.active_position ? [sysData.active_position.ticker] : []);

            const snapshots: QuantSnapshot[] = [];
            await Promise.all(tickers.map(async (ticker: string) => {
                const snap: QuantSnapshot = { ticker };
                try {
                    const regRes = await fetch(`${API_BASE}/api/quant/regime?ticker=${ticker}`);
                    if (regRes.ok) { const d = await regRes.json(); snap.regime = d.regime; }
                } catch {}
                try {
                    const vpRes = await fetch(`${API_BASE}/api/quant/vpin?ticker=${ticker}`);
                    if (vpRes.ok) { const d = await vpRes.json(); snap.vpin_score = d.vpin_score; snap.is_toxic = d.is_toxic; }
                } catch {}
                snapshots.push(snap);
            }));
            setQuantData(snapshots);
            setError(null);
        } catch (e: any) {
            setError(e.message);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => { load(); }, [id]);

    const handleHaltDeploy = async () => {
        if (!system) return;
        const endpoint = system.status === "ACTIVE" ? "halt" : "deploy";
        await fetch(`${API_BASE}/api/systems/${id}/${endpoint}`, { method: "POST" });
        load();
    };

    const handleSignalReview = async (cardId: string, action: "ACCEPTED" | "DECLINED") => {
        await fetch(`${API_BASE}/api/systems/${id}/signals/${cardId}/review?action=${action}`, { method: "POST" });
        load();
    };

    const fmt = (val: number) => new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(val);

    if (loading) {
        return (
            <div className="flex h-full items-center justify-center">
                <Loader2 className="w-5 h-5 animate-spin text-muted-foreground" />
            </div>
        );
    }

    if (error || !system) {
        return (
            <div className="flex h-full items-center justify-center">
                <div className="rounded-lg border border-red-500/20 bg-red-500/5 text-red-400 p-6 max-w-md text-sm text-center">
                    <p className="font-semibold mb-1">Sentinel not found</p>
                    <p className="text-xs text-muted-foreground">{error}</p>
                    <button onClick={() => navigate("/command")} className="mt-4 text-xs text-accent hover:underline">
                        ← Back to Command Center
                    </button>
                </div>
            </div>
        );
    }

    const config = system.config || {};
    const tickers = config.asset_universe?.tickers || (system.active_position ? [system.active_position.ticker] : []);
    const capital = config.sandbox?.capital || 100000;

    return (
        <div className="max-w-6xl mx-auto p-8 space-y-6">
            {/* Header */}
            <div className="flex items-start justify-between">
                <div>
                    <button onClick={() => navigate("/command")}
                        className="flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground mb-3 transition-colors">
                        <ArrowLeft className="w-3.5 h-3.5" /> Back to Command Center
                    </button>
                    <div className="flex items-center gap-3">
                        <h1 className="text-2xl font-semibold tracking-tight">{system.name}</h1>
                        <span className={`text-[11px] font-medium px-2.5 py-1 rounded-full ${
                            system.status === "ACTIVE" ? "bg-emerald-500/10 text-emerald-500" :
                            system.status === "PAUSED" ? "bg-muted text-muted-foreground" :
                            "bg-amber-500/10 text-amber-500"
                        }`}>{system.status}</span>
                    </div>
                    <p className="text-sm text-muted-foreground mt-1">
                        {system.id} · {tickers.length} ticker{tickers.length !== 1 ? "s" : ""} · {fmt(capital)} capital
                    </p>
                </div>
                <div className="flex gap-2">
                    <button onClick={load}
                        className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-border text-xs text-muted-foreground hover:text-foreground hover:bg-muted/60 transition-colors">
                        <RefreshCw className="w-3.5 h-3.5" /> Refresh
                    </button>
                    <button onClick={handleHaltDeploy}
                        className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                            system.status === "ACTIVE"
                                ? "bg-red-500/10 text-red-400 hover:bg-red-500/20"
                                : "bg-emerald-500/10 text-emerald-500 hover:bg-emerald-500/20"
                        }`}>
                        {system.status === "ACTIVE" ? <><Square className="w-3.5 h-3.5" /> Halt</> : <><Play className="w-3.5 h-3.5" /> Deploy</>}
                    </button>
                </div>
            </div>

            {/* Config Summary */}
            <section className="rounded-lg border border-border bg-card p-5">
                <h2 className="text-xs font-semibold uppercase tracking-widest text-muted-foreground mb-4 flex items-center gap-2">
                    <Settings2 className="w-3.5 h-3.5" /> Configuration
                </h2>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div>
                        <span className="text-[10px] text-muted-foreground uppercase tracking-wider block mb-0.5">Capital</span>
                        <span className="text-sm font-mono font-semibold">{fmt(capital)}</span>
                    </div>
                    <div>
                        <span className="text-[10px] text-muted-foreground uppercase tracking-wider block mb-0.5">Trading Style</span>
                        <span className="text-sm capitalize">{config.trading_style || "—"}</span>
                    </div>
                    <div>
                        <span className="text-[10px] text-muted-foreground uppercase tracking-wider block mb-0.5">Max Position</span>
                        <span className="text-sm font-mono">{((config.quant_engine?.position_sizing?.max_position_pct || 0.1) * 100).toFixed(0)}%</span>
                    </div>
                    <div>
                        <span className="text-[10px] text-muted-foreground uppercase tracking-wider block mb-0.5">VPIN Threshold</span>
                        <span className="text-sm font-mono">{config.quant_engine?.vpin?.toxicity_threshold || "—"}</span>
                    </div>
                </div>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-3 pt-3 border-t border-border">
                    <div>
                        <span className="text-[10px] text-muted-foreground uppercase tracking-wider block mb-0.5">Data Connectors</span>
                        <div className="flex flex-wrap gap-1">
                            {(config.data_engine?.connectors || Object.values(system.components).slice(0, 1)).map((c: string, i: number) => (
                                <span key={i} className="text-[11px] font-mono bg-muted px-1.5 py-0.5 rounded">{c}</span>
                            ))}
                        </div>
                    </div>
                    <div>
                        <span className="text-[10px] text-muted-foreground uppercase tracking-wider block mb-0.5">Quant Engine</span>
                        <span className="text-[11px] font-mono bg-muted px-1.5 py-0.5 rounded">
                            {system.components?.quant_engine || "—"}
                        </span>
                    </div>
                    <div>
                        <span className="text-[10px] text-muted-foreground uppercase tracking-wider block mb-0.5">Analyst Model</span>
                        <span className="text-[11px] font-mono bg-muted px-1.5 py-0.5 rounded">
                            {config.analyst_engine?.model || system.components?.analyst_engine || "—"}
                        </span>
                    </div>
                    <div>
                        <span className="text-[10px] text-muted-foreground uppercase tracking-wider block mb-0.5">Lookback</span>
                        <span className="text-sm font-mono">{config.data_engine?.lookback_days || "252"}d</span>
                    </div>
                </div>
                <div className="mt-3 pt-3 border-t border-border">
                    <span className="text-[10px] text-muted-foreground uppercase tracking-wider block mb-1.5">Asset Universe</span>
                    <div className="flex flex-wrap gap-1.5">
                        {tickers.map((t: string) => (
                            <span key={t} className="text-xs font-mono font-semibold bg-accent/10 text-accent px-2 py-0.5 rounded">{t}</span>
                        ))}
                        {tickers.length === 0 && <span className="text-xs text-muted-foreground">No tickers configured</span>}
                    </div>
                </div>
            </section>

            {/* Portfolio & PnL */}
            <section className="rounded-lg border border-border bg-card p-5">
                <h2 className="text-xs font-semibold uppercase tracking-widest text-muted-foreground mb-4 flex items-center gap-2">
                    <Wallet className="w-3.5 h-3.5" /> Portfolio
                </h2>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div>
                        <span className="text-[10px] text-muted-foreground uppercase tracking-wider block mb-0.5">PnL</span>
                        <span className={`text-lg font-mono font-semibold ${system.pnl_usd >= 0 ? "text-emerald-500" : "text-red-400"}`}>
                            {system.pnl_usd >= 0 ? "+" : ""}{fmt(system.pnl_usd)}
                        </span>
                    </div>
                    <div>
                        <span className="text-[10px] text-muted-foreground uppercase tracking-wider block mb-0.5">Return</span>
                        <span className={`text-lg font-mono font-semibold flex items-center gap-1 ${system.pnl_pct >= 0 ? "text-emerald-500" : "text-red-400"}`}>
                            {system.pnl_pct >= 0 ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
                            {system.pnl_pct >= 0 ? "+" : ""}{system.pnl_pct.toFixed(2)}%
                        </span>
                    </div>
                    <div>
                        <span className="text-[10px] text-muted-foreground uppercase tracking-wider block mb-0.5">NAV</span>
                        <span className="text-lg font-mono font-semibold">{fmt(capital + system.pnl_usd)}</span>
                    </div>
                    <div>
                        <span className="text-[10px] text-muted-foreground uppercase tracking-wider block mb-0.5">Active Position</span>
                        {system.active_position ? (
                            <span className="text-sm font-mono">
                                {system.active_position.direction} {system.active_position.ticker} ({system.active_position.shares}) @ {fmt(system.active_position.entry_price)}
                            </span>
                        ) : (
                            <span className="text-sm text-muted-foreground">Flat — no position</span>
                        )}
                    </div>
                </div>
            </section>

            {/* Quant Dashboard — per-ticker */}
            <section className="rounded-lg border border-border bg-card p-5">
                <h2 className="text-xs font-semibold uppercase tracking-widest text-muted-foreground mb-4 flex items-center gap-2">
                    <BarChart2 className="w-3.5 h-3.5" /> Quant Data — Per Ticker
                </h2>
                {quantData.length > 0 ? (
                    <div className="rounded-lg border border-border overflow-hidden">
                        <table className="w-full text-sm text-left">
                            <thead className="text-[10px] uppercase tracking-wider text-muted-foreground border-b border-border">
                                <tr>
                                    <th className="px-4 py-2.5 font-semibold">Ticker</th>
                                    <th className="px-4 py-2.5 font-semibold">HMM Regime</th>
                                    <th className="px-4 py-2.5 font-semibold">VPIN Score</th>
                                    <th className="px-4 py-2.5 font-semibold">Toxicity</th>
                                </tr>
                            </thead>
                            <tbody>
                                {quantData.map((q) => (
                                    <tr key={q.ticker} className="border-b border-border last:border-0 hover:bg-muted/30 transition-colors">
                                        <td className="px-4 py-2.5 font-mono font-semibold text-accent">{q.ticker}</td>
                                        <td className="px-4 py-2.5">
                                            <span className={`text-xs font-mono font-medium px-2 py-0.5 rounded ${
                                                q.regime === "Bullish" ? "bg-emerald-500/10 text-emerald-500" :
                                                q.regime === "Bearish" ? "bg-red-500/10 text-red-400" :
                                                q.regime ? "bg-amber-500/10 text-amber-500" : "text-muted-foreground"
                                            }`}>{q.regime || "Loading..."}</span>
                                        </td>
                                        <td className="px-4 py-2.5 font-mono">
                                            {q.vpin_score != null ? (
                                                <span className={q.is_toxic ? "text-red-400" : "text-emerald-500"}>
                                                    {q.vpin_score.toFixed(4)}
                                                </span>
                                            ) : <span className="text-muted-foreground">—</span>}
                                        </td>
                                        <td className="px-4 py-2.5">
                                            {q.is_toxic != null ? (
                                                q.is_toxic ? (
                                                    <span className="flex items-center gap-1 text-xs text-red-400">
                                                        <AlertTriangle className="w-3 h-3" /> TOXIC
                                                    </span>
                                                ) : (
                                                    <span className="text-xs text-emerald-500">Clean</span>
                                                )
                                            ) : <span className="text-muted-foreground text-xs">—</span>}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                ) : (
                    <p className="text-sm text-muted-foreground">No tickers in universe to analyze.</p>
                )}
            </section>

            {/* Signal Cards */}
            <section className="rounded-lg border border-border bg-card p-5">
                <h2 className="text-xs font-semibold uppercase tracking-widest text-muted-foreground mb-4 flex items-center gap-2">
                    <Bell className="w-3.5 h-3.5" /> Pending Signal Cards
                </h2>
                {signals.length > 0 ? (
                    <div className="space-y-3">
                        {signals.map((card) => (
                            <div key={card.card_id} className="rounded-lg border border-border bg-muted/20 p-4">
                                <div className="flex items-center justify-between mb-2">
                                    <div className="flex items-center gap-2">
                                        <span className={`text-xs font-semibold px-2 py-0.5 rounded ${
                                            card.decision === "BUY" ? "bg-emerald-500/10 text-emerald-500" : "bg-red-500/10 text-red-400"
                                        }`}>{card.decision}</span>
                                        <span className="text-sm font-mono font-semibold">{card.ticker}</span>
                                        <span className="text-[10px] text-muted-foreground">
                                            Confidence: {(card.confidence * 100).toFixed(0)}%
                                        </span>
                                    </div>
                                    <span className="text-[10px] text-muted-foreground font-mono">{card.card_id.slice(0, 8)}</span>
                                </div>
                                <p className="text-xs text-muted-foreground mb-3 leading-relaxed">{card.thesis}</p>
                                <div className="flex gap-2">
                                    <button onClick={() => handleSignalReview(card.card_id, "ACCEPTED")}
                                        className="flex-1 flex items-center justify-center gap-1.5 py-1.5 rounded-lg bg-emerald-500/10 text-emerald-500 text-xs font-medium hover:bg-emerald-500/20 transition-colors border border-emerald-500/20">
                                        <CheckCircle2 className="w-3.5 h-3.5" /> Accept
                                    </button>
                                    <button onClick={() => handleSignalReview(card.card_id, "DECLINED")}
                                        className="flex-1 flex items-center justify-center gap-1.5 py-1.5 rounded-lg bg-red-500/10 text-red-400 text-xs font-medium hover:bg-red-500/20 transition-colors border border-red-500/20">
                                        <XCircle className="w-3.5 h-3.5" /> Decline
                                    </button>
                                </div>
                            </div>
                        ))}
                    </div>
                ) : (
                    <div className="text-center py-6 text-muted-foreground">
                        <Bell className="w-6 h-6 mx-auto mb-2 opacity-40" />
                        <p className="text-sm">No pending signals.</p>
                        <p className="text-[11px] mt-1">Signal cards appear here when the Sentinel generates BUY/SELL recommendations.</p>
                    </div>
                )}
            </section>

            {/* Activity Log */}
            <section className="rounded-lg border border-border bg-card p-5">
                <h2 className="text-xs font-semibold uppercase tracking-widest text-muted-foreground mb-4 flex items-center gap-2">
                    <Clock className="w-3.5 h-3.5" /> Activity Log
                </h2>
                {system.activity && system.activity.length > 0 ? (
                    <div className="space-y-2">
                        {system.activity.map((evt, i) => (
                            <div key={i} className="flex items-start gap-3 py-2 border-b border-border last:border-0">
                                <span className={`text-[10px] font-mono font-semibold px-2 py-0.5 rounded mt-0.5 shrink-0 ${
                                    evt.event === "BUY" ? "bg-emerald-500/10 text-emerald-500" :
                                    evt.event === "SELL" ? "bg-red-500/10 text-red-400" :
                                    evt.event === "HALT" ? "bg-amber-500/10 text-amber-500" :
                                    evt.event === "DEPLOY" ? "bg-accent/10 text-accent" :
                                    "bg-muted text-muted-foreground"
                                }`}>{evt.event}</span>
                                <div className="flex-1 min-w-0">
                                    <p className="text-xs text-foreground leading-relaxed">{evt.rationale}</p>
                                    <p className="text-[10px] text-muted-foreground font-mono mt-0.5">
                                        {evt.ticker && evt.ticker !== "N/A" ? `${evt.ticker} · ` : ""}{evt.ts}
                                    </p>
                                </div>
                            </div>
                        ))}
                    </div>
                ) : (
                    <p className="text-sm text-muted-foreground text-center py-4">No activity recorded yet.</p>
                )}
            </section>
        </div>
    );
}
