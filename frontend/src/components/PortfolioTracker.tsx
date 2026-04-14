import { useEffect, useState } from "react";
import { 
    TrendingUp, TrendingDown, DollarSign, BarChart2, RefreshCw, 
    Loader2, ArrowUpRight, ArrowDownRight, ShieldCheck, 
    Zap, Target, Activity, Search, LayoutGrid, Globe,
    ChevronDown, MoreHorizontal, Download, Share2
} from "lucide-react";
import { cn } from "@/lib/utils";

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
            const data = await res.json();
            setData(data);
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
            <div className="flex h-full items-center justify-center bg-surface">
                <div className="flex flex-col items-center gap-4 py-20 px-40 glass-panel border border-white/5">
                    <Loader2 className="w-5 h-5 animate-spin text-primary" />
                    <span className="text-[10px] font-bold text-on-surface-variant uppercase tracking-[0.2em]">Hydrating Portfolio State...</span>
                </div>
            </div>
        );
    }

    return (
        <div className="p-8 max-w-screen-2xl mx-auto space-y-8">
            {/* Editorial Header */}
            <header className="flex items-center justify-between border-b border-white/5 pb-6">
                <div className="flex flex-col">
                    <h1 className="font-headline text-3xl font-medium text-on-surface">Portfolio Attribution Matrix</h1>
                    <div className="flex items-center gap-2 mt-1">
                        <span className="text-[10px] font-bold text-on-surface-variant uppercase tracking-widest">Gateway: PROT-V7-ALPHA</span>
                        <span className="h-3 w-[1px] bg-white/10 mx-1"></span>
                        <span className="text-[10px] font-bold text-on-surface-variant uppercase tracking-widest italic text-secondary">Oracles: LIVE_FEED</span>
                    </div>
                </div>
                <div className="flex gap-3">
                    <button onClick={load} className="h-10 px-4 rounded-lg border border-white/10 text-[0.8125rem] font-bold text-on-surface-variant hover:text-on-surface hover:bg-[#1a1a19] transition-all uppercase tracking-widest flex items-center gap-2">
                        <RefreshCw className={cn("w-4 h-4", loading && "animate-spin")} />
                        Refresh
                    </button>
                    <button className="h-10 px-4 rounded-lg bg-primary-container text-on-primary-container text-[0.8125rem] font-bold uppercase tracking-widest flex items-center gap-2 shadow-lg transition-transform active:scale-95">
                        <Download className="w-4 h-4" />
                        Export
                    </button>
                </div>
            </header>

            {error && (
                <div className="bg-tertiary-container/10 border border-tertiary/20 text-tertiary p-4 rounded-lg text-xs font-bold uppercase tracking-widest flex items-center gap-3">
                    <Zap className="w-4 h-4" />
                    System Attribution Error: {error}
                </div>
            )}

            {data && (
                <div className="space-y-8">
                    {/* Summary Cards */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                        <div className="bg-surface-container rounded-xl p-6 border border-white/5 group hover:bg-surface-container-high transition-colors">
                            <span className="text-[0.625rem] font-bold text-on-surface-variant uppercase tracking-[0.2em] block mb-2">Total Actual NAV</span>
                            <div className="flex items-baseline gap-2">
                                <span className="font-headline text-3xl font-medium text-on-surface">{formatCurrency(data.total_actual_nav)}</span>
                                <span className="text-secondary text-[10px] font-bold uppercase">+1.2%</span>
                            </div>
                            <div className="mt-4 w-full bg-surface-container-highest h-1 rounded-full overflow-hidden">
                                <div className="bg-secondary h-full w-[65%]" />
                            </div>
                        </div>
                        <div className="bg-surface-container rounded-xl p-6 border border-white/5 opacity-80 hover:opacity-100 transition-opacity">
                            <span className="text-[0.625rem] font-bold text-on-surface-variant uppercase tracking-[0.2em] block mb-2">Mirror Shadow NAV</span>
                            <span className="font-headline text-3xl font-light text-on-surface-variant italic">{formatCurrency(data.total_mirror_nav)}</span>
                            <div className="mt-4 flex items-center gap-2">
                                <Activity className="w-3 h-3 text-on-surface-variant/30" />
                                <span className="text-[10px] uppercase font-bold text-on-surface-variant/50">Simulated Baseline</span>
                            </div>
                        </div>
                        <div className="bg-surface-container rounded-xl p-6 border border-white/5 border-l-4 border-l-primary">
                            <span className="text-[0.625rem] font-bold text-on-surface-variant uppercase tracking-[0.2em] block mb-2">Override Alpha Gap</span>
                            <div className="flex items-baseline gap-2">
                                <span className={cn(
                                    "font-headline text-3xl font-semibold",
                                    data.total_gap >= 0 ? "text-primary" : "text-tertiary"
                                )}>
                                    {formatCurrency(data.total_gap)}
                                </span>
                                <TrendingUp className="w-4 h-4 text-primary" />
                            </div>
                            <p className="text-[10px] text-muted-foreground mt-2 font-medium uppercase tracking-tighter italic">Net outperformance vs agent baseline</p>
                        </div>
                    </div>

                    {/* Registry Table */}
                    <div className="bg-surface-container rounded-xl overflow-hidden border border-white/5">
                        <div className="px-6 py-5 border-b border-white/5 flex items-center justify-between">
                            <h3 className="font-headline text-xl font-medium">Active Sentinel Nodes</h3>
                            <div className="flex items-center gap-4">
                                <div className="relative">
                                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground w-4 h-4" />
                                    <input className="bg-surface-container-low border-none rounded-lg pl-9 pr-4 py-1.5 text-[0.75rem] text-on-surface placeholder:text-muted-foreground w-48 focus:ring-1 focus:ring-primary-container" placeholder="Filter nodes..." type="text" />
                                </div>
                                <MoreHorizontal className="w-5 h-5 text-muted-foreground cursor-pointer" />
                            </div>
                        </div>
                        <div className="overflow-x-auto">
                            <table className="w-full text-left">
                                <thead>
                                    <tr className="text-[0.6875rem] uppercase tracking-widest text-on-surface-variant border-b border-white/5 font-bold">
                                        <th className="px-6 py-4">Node Identity</th>
                                        <th className="px-6 py-4">Actual Perf</th>
                                        <th className="px-6 py-4 text-on-surface-variant/50">Mirror Alpha</th>
                                        <th className="px-6 py-4 text-right">Attribution</th>
                                    </tr>
                                </thead>
                                <tbody className="text-[0.8125rem] divide-y divide-white/5">
                                    {data.sentinels.map((s, i) => (
                                        <tr key={i} className="hover:bg-white/[0.02] transition-colors group">
                                            <td className="px-6 py-4">
                                                <div className="flex items-center gap-3">
                                                    <div className="w-8 h-8 rounded bg-surface-container-highest flex items-center justify-center">
                                                        <Activity className="w-4 h-4 text-secondary" />
                                                    </div>
                                                    <div>
                                                        <p className="font-bold text-on-surface font-mono">{s.sentinel_id}</p>
                                                        <p className="text-[0.625rem] text-muted-foreground uppercase font-bold tracking-tighter italic">Primary Execution Node</p>
                                                    </div>
                                                </div>
                                            </td>
                                            <td className="px-6 py-4">
                                                <div className="flex flex-col">
                                                    <span className="font-headline text-lg font-medium text-on-surface">{formatCurrency(s.actual_nav)}</span>
                                                    <span className={cn("text-[0.6875rem] font-bold", s.actual_return_pct >= 0 ? "text-secondary" : "text-tertiary")}>
                                                        {formatPct(s.actual_return_pct)}
                                                    </span>
                                                </div>
                                            </td>
                                            <td className="px-6 py-4">
                                                <div className="flex flex-col opacity-40 group-hover:opacity-60 transition-opacity">
                                                    <span className="font-headline text-base font-light italic">{formatCurrency(s.mirror_nav)}</span>
                                                    <span className={cn("text-[0.6875rem] font-bold", s.mirror_return_pct >= 0 ? "text-secondary" : "text-tertiary")}>
                                                        {formatPct(s.mirror_return_pct)}
                                                    </span>
                                                </div>
                                            </td>
                                            <td className="px-6 py-4 text-right">
                                                <div className={cn(
                                                    "inline-flex items-center gap-2 px-3 py-1 rounded-lg border text-[10px] font-bold uppercase tracking-widest",
                                                    s.human_outperformance 
                                                        ? "bg-secondary-container/10 border-secondary/20 text-secondary" 
                                                        : "bg-surface-container-highest border-white/5 text-on-surface-variant"
                                                )}>
                                                    <div className={cn("w-1.5 h-1.5 rounded-full", s.human_outperformance ? "bg-secondary" : "bg-outline")} />
                                                    {s.human_outperformance ? "Alpha Positive" : "Baseline"}
                                                </div>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>

                    {/* Simulation Archive footer */}
                    <section className="bg-surface-container-low rounded-xl border border-white/5 overflow-hidden">
                        <div className="px-6 py-3 bg-surface-container border-b border-white/5 flex items-center justify-between">
                            <h4 className="font-headline text-sm font-medium italic text-on-surface-variant">Simulation Archive (Historical Path)</h4>
                            <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest">{data.backtest_navs.length} Segments Logged</span>
                        </div>
                        <div className="max-h-48 overflow-auto scrollbar-thin">
                            <table className="w-full text-left">
                                <tbody className="divide-y divide-white/5">
                                    {data.backtest_navs.map((nav, i) => (
                                        <tr key={i} className="hover:bg-white/[0.01] transition-colors">
                                            <td className="px-6 py-2 font-mono text-[10px] text-on-surface-variant">{nav.run_id}</td>
                                            <td className="px-6 py-2 font-headline text-sm text-on-surface">{formatCurrency(nav.end_nav)}</td>
                                            <td className={cn("px-6 py-2 font-bold text-[11px]", nav.return_pct >= 0 ? "text-secondary/60" : "text-tertiary/60")}>
                                                {formatPct(nav.return_pct)}
                                            </td>
                                            <td className="px-6 py-2 text-right text-[9px] text-muted-foreground uppercase font-bold tracking-tighter">{nav.data_points} Data Points</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </section>
                </div>
            )}
        </div>
    );
}
