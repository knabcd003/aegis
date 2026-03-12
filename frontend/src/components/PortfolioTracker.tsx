import { useEffect, useState } from "react";
import { TrendingUp, TrendingDown, DollarSign, BarChart2, RefreshCw, Loader2, ArrowUpRight, ArrowDownRight } from "lucide-react";

const API_BASE = "http://localhost:8000";

interface SentinelSnapshot {
    sentinel_id: string;
    actual_nav: number;
    mirror_nav: number;
    absolute_gap: number;
    actual_return_pct: number;
    mirror_return_pct: number;
    human_outperformance: boolean;
}

interface BacktestNav {
    run_id: string;
    start_nav: number;
    end_nav: number;
    return_pct: number;
    data_points: number;
}

interface PortfolioData {
    sentinels: SentinelSnapshot[];
    total_actual_nav: number;
    total_mirror_nav: number;
    total_gap: number;
    backtest_navs: BacktestNav[];
}

export function PortfolioTracker() {
    const [data, setData] = useState<PortfolioData | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const load = async () => {
        try {
            setLoading(true);
            const res = await fetch(`${API_BASE}/api/portfolio/overview`);
            if (!res.ok) throw new Error(`API error: ${res.status}`);
            setData(await res.json());
            setError(null);
        } catch (e: any) {
            setError(e.message);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => { load(); }, []);

    const formatCurrency = (val: number) => {
        return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(val);
    };

    const formatPct = (val: number) => {
        const sign = val >= 0 ? "+" : "";
        return `${sign}${(val * 100).toFixed(2)}%`;
    };

    if (loading) {
        return (
            <div className="flex h-full items-center justify-center">
                <Loader2 className="w-5 h-5 animate-spin text-muted-foreground" />
            </div>
        );
    }

    return (
        <div className="max-w-5xl mx-auto p-8">
            <div className="flex items-center justify-between mb-8">
                <div>
                    <h1 className="text-2xl font-semibold tracking-tight flex items-center gap-2.5">
                        <DollarSign className="w-6 h-6 text-accent" />
                        Portfolio Tracker
                    </h1>
                    <p className="text-sm text-muted-foreground mt-1">
                        Live NAV, counterfactual mirror, and human override gap analysis
                    </p>
                </div>
                <button onClick={load}
                    className="flex items-center gap-2 px-3 py-1.5 rounded-lg border border-border text-sm text-muted-foreground hover:text-foreground hover:bg-muted/60 transition-colors">
                    <RefreshCw className="w-3.5 h-3.5" />
                    Refresh
                </button>
            </div>

            {error && (
                <div className="rounded-lg border border-red-500/20 bg-red-500/5 text-red-400 p-4 text-sm mb-6">
                    {error}
                </div>
            )}

            {/* Summary Cards */}
            {data && (data.sentinels.length > 0 || data.backtest_navs.length > 0) ? (
                <>
                    {data.sentinels.length > 0 && (
                        <div className="grid grid-cols-3 gap-4 mb-8">
                            <div className="rounded-lg border border-border bg-card p-5">
                                <span className="text-[11px] text-muted-foreground uppercase tracking-wider block mb-1">Actual NAV</span>
                                <span className="text-xl font-semibold font-mono">{formatCurrency(data.total_actual_nav)}</span>
                            </div>
                            <div className="rounded-lg border border-border bg-card p-5">
                                <span className="text-[11px] text-muted-foreground uppercase tracking-wider block mb-1">Mirror NAV (AI-only)</span>
                                <span className="text-xl font-semibold font-mono">{formatCurrency(data.total_mirror_nav)}</span>
                            </div>
                            <div className="rounded-lg border border-border bg-card p-5">
                                <span className="text-[11px] text-muted-foreground uppercase tracking-wider block mb-1">Human Override Gap</span>
                                <span className={`text-xl font-semibold font-mono flex items-center gap-1 ${
                                    data.total_gap >= 0 ? "text-emerald-500" : "text-red-400"
                                }`}>
                                    {data.total_gap >= 0 ? <ArrowUpRight className="w-4 h-4" /> : <ArrowDownRight className="w-4 h-4" />}
                                    {formatCurrency(Math.abs(data.total_gap))}
                                </span>
                            </div>
                        </div>
                    )}

                    {/* Sentinel Details */}
                    {data.sentinels.length > 0 && (
                        <section className="mb-8">
                            <h2 className="text-xs font-semibold uppercase tracking-widest text-muted-foreground mb-3 flex items-center gap-2">
                                <TrendingUp className="w-3.5 h-3.5" />
                                Live Sentinels
                            </h2>
                            <div className="space-y-3">
                                {data.sentinels.map((s, i) => (
                                    <div key={i} className="rounded-lg border border-border bg-card p-5 hover:bg-muted/30 transition-colors">
                                        <div className="flex items-center justify-between mb-3">
                                            <h3 className="text-sm font-semibold font-mono">{s.sentinel_id}</h3>
                                            <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${
                                                s.human_outperformance ? "bg-emerald-500/10 text-emerald-500" : "bg-red-500/10 text-red-400"
                                            }`}>
                                                {s.human_outperformance ? "Human Outperforming" : "AI Outperforming"}
                                            </span>
                                        </div>
                                        <div className="grid grid-cols-4 gap-4 text-sm">
                                            <div>
                                                <span className="text-[11px] text-muted-foreground uppercase block mb-0.5">Actual NAV</span>
                                                <span className="font-mono">{formatCurrency(s.actual_nav)}</span>
                                            </div>
                                            <div>
                                                <span className="text-[11px] text-muted-foreground uppercase block mb-0.5">Mirror NAV</span>
                                                <span className="font-mono">{formatCurrency(s.mirror_nav)}</span>
                                            </div>
                                            <div>
                                                <span className="text-[11px] text-muted-foreground uppercase block mb-0.5">Actual Return</span>
                                                <span className={`font-mono ${s.actual_return_pct >= 0 ? "text-emerald-500" : "text-red-400"}`}>
                                                    {formatPct(s.actual_return_pct)}
                                                </span>
                                            </div>
                                            <div>
                                                <span className="text-[11px] text-muted-foreground uppercase block mb-0.5">Mirror Return</span>
                                                <span className={`font-mono ${s.mirror_return_pct >= 0 ? "text-emerald-500" : "text-red-400"}`}>
                                                    {formatPct(s.mirror_return_pct)}
                                                </span>
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </section>
                    )}

                    {/* Backtest Equity Curves */}
                    {data.backtest_navs.length > 0 && (
                        <section>
                            <h2 className="text-xs font-semibold uppercase tracking-widest text-muted-foreground mb-3 flex items-center gap-2">
                                <BarChart2 className="w-3.5 h-3.5" />
                                Backtest Results
                            </h2>
                            <div className="rounded-lg border border-border bg-card overflow-hidden">
                                <table className="w-full text-sm text-left">
                                    <thead className="text-[11px] uppercase tracking-wider text-muted-foreground border-b border-border">
                                        <tr>
                                            <th className="px-4 py-3 font-semibold">Run ID</th>
                                            <th className="px-4 py-3 font-semibold">Start NAV</th>
                                            <th className="px-4 py-3 font-semibold">End NAV</th>
                                            <th className="px-4 py-3 font-semibold">Return</th>
                                            <th className="px-4 py-3 font-semibold">Data Points</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {data.backtest_navs.map((nav, i) => (
                                            <tr key={i} className="border-b border-border last:border-0 hover:bg-muted/40 transition-colors">
                                                <td className="px-4 py-3 font-mono text-xs">{nav.run_id}</td>
                                                <td className="px-4 py-3 font-mono">{formatCurrency(nav.start_nav)}</td>
                                                <td className="px-4 py-3 font-mono">{formatCurrency(nav.end_nav)}</td>
                                                <td className={`px-4 py-3 font-mono font-semibold ${nav.return_pct >= 0 ? "text-emerald-500" : "text-red-400"}`}>
                                                    {nav.return_pct >= 0 ? "+" : ""}{nav.return_pct.toFixed(2)}%
                                                </td>
                                                <td className="px-4 py-3 text-muted-foreground">{nav.data_points}</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </section>
                    )}
                </>
            ) : (
                <div className="rounded-lg border border-border bg-card p-8 text-center">
                    <DollarSign className="w-8 h-8 text-muted-foreground mx-auto mb-3" />
                    <p className="text-sm text-muted-foreground">
                        No portfolio data yet. Deploy a sentinel and run backtests to populate this view.
                    </p>
                    <p className="text-[11px] text-muted-foreground mt-2">
                        Backtest results with <span className="font-mono">portfolio_nav.csv</span> will appear here automatically.
                    </p>
                </div>
            )}
        </div>
    );
}
