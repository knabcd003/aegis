import { useEffect, useState } from "react";
import { 
    TrendingUp, TrendingDown, DollarSign, BarChart2, RefreshCw, 
    Loader2, ArrowUpRight, ArrowDownRight, ShieldCheck, 
    Zap, Target, Activity, Search, LayoutGrid, Globe
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
            <div className="flex h-full items-center justify-center bg-[#0C0E11]">
                <div className="flex flex-col items-center gap-4 py-20 px-40 border border-[#2D333B] bg-[#111418]">
                    <Loader2 className="w-5 h-5 animate-spin text-white/50" />
                    <span className="text-[10px] font-mono font-bold text-white/30 uppercase tracking-[0.2em]">Hydrating_Portfolio_State...</span>
                </div>
            </div>
        );
    }

    return (
        <div className="flex flex-col h-full bg-[#0C0E11] overflow-hidden">
            <div className="flex-1 flex flex-col p-6 gap-6 overflow-hidden">
                {/* Technical Header */}
                <header className="flex items-center justify-between border-b border-[#2D333B] pb-4">
                    <div className="flex flex-col">
                        <h1 className="text-sm font-bold text-white uppercase tracking-[0.2em]">Portfolio Attribution Matrix</h1>
                        <div className="flex items-center gap-2 mt-1">
                            <span className="text-[10px] font-mono text-white/40 uppercase">Gateway: PROT-V7-ALPHA</span>
                            <span className="text-[10px] font-mono text-white/20">•</span>
                            <span className="text-[10px] font-mono text-white/40 uppercase">Oracles: LIVE_FEED</span>
                        </div>
                    </div>
                    <button onClick={load} className="h-7 px-3 rounded border border-[#2D333B] text-[10px] font-bold text-white/60 hover:text-white transition-all uppercase tracking-widest flex items-center gap-2">
                        <RefreshCw className="w-3 h-3" />
                        Refresh
                    </button>
                </header>

                {error && (
                    <div className="border border-red-900 bg-red-950/20 text-red-400 p-2 text-[10px] font-mono uppercase tracking-widest">
                        ERROR_ID::PORTFOLIO_LINK_FAIL -- {error}
                    </div>
                )}

                {data && (data.sentinels.length > 0 || data.backtest_navs.length > 0) ? (
                    <div className="flex-1 flex flex-col gap-6 overflow-hidden min-h-0">
                        {/* Summary Bar */}
                        <div className="grid grid-cols-3 border border-[#2D333B] bg-[#111418]">
                            <div className="p-4 border-r border-[#2D333B]">
                                <span className="text-[9px] font-bold text-white/20 uppercase tracking-widest block mb-1">Total_Actual_NAV</span>
                                <span className="text-lg font-mono font-bold text-white">{formatCurrency(data.total_actual_nav)}</span>
                            </div>
                            <div className="p-4 border-r border-[#2D333B]">
                                <span className="text-[9px] font-bold text-white/20 uppercase tracking-widest block mb-1">Mirror_Shadow_NAV</span>
                                <span className="text-lg font-mono font-bold text-white/40">{formatCurrency(data.total_mirror_nav)}</span>
                            </div>
                            <div className="p-4 flex flex-col justify-center">
                                <span className="text-[9px] font-bold text-white/20 uppercase tracking-widest block mb-1">Override_Gap</span>
                                <span className={cn(
                                    "text-lg font-mono font-bold",
                                    data.total_gap >= 0 ? "text-emerald-500/80" : "text-rose-500/80"
                                )}>
                                    {formatCurrency(data.total_gap)}
                                </span>
                            </div>
                        </div>

                        {/* Registry Table */}
                        <div className="flex-1 border border-[#2D333B] bg-[#111418] relative overflow-hidden flex flex-col min-h-0">
                            <div className="px-4 py-2 bg-[#1C1F24] border-b border-[#2D333B] flex items-center justify-between">
                                <span className="text-[10px] font-bold text-white/40 uppercase tracking-widest">Active_Sentinel_Nodes</span>
                                <LayoutGrid className="w-3 h-3 text-white/20" />
                            </div>
                            <div className="overflow-auto scrollbar-thin flex-1">
                                <table className="w-full text-left border-collapse">
                                    <thead className="sticky top-0 bg-[#111418] border-b border-[#2D333B] z-10">
                                        <tr>
                                            <th className="px-4 py-2 text-[9px] font-bold text-white/30 uppercase tracking-widest border-r border-[#2D333B]">Node_ID</th>
                                            <th className="px-4 py-2 text-[9px] font-bold text-white/30 uppercase tracking-widest border-r border-[#2D333B]">Actual_Perf</th>
                                            <th className="px-4 py-2 text-[9px] font-bold text-white/30 uppercase tracking-widest border-r border-[#2D333B]">Mirror_Perf</th>
                                            <th className="px-4 py-2 text-[9px] font-bold text-white/30 uppercase tracking-widest text-right">Attribution_Status</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-[#2D333B]">
                                        {data.sentinels.map((s, i) => (
                                            <tr key={i} className="hover:bg-white/[0.02]">
                                                <td className="px-4 py-2 border-r border-[#2D333B] font-mono text-[11px] text-white/80">{s.sentinel_id}</td>
                                                <td className="px-4 py-2 border-r border-[#2D333B]">
                                                    <div className="flex flex-col gap-0.5">
                                                        <span className="text-[11px] font-mono text-white">{formatCurrency(s.actual_nav)}</span>
                                                        <span className={cn("text-[9px] font-mono", s.actual_return_pct >= 0 ? "text-emerald-500/60" : "text-rose-500/60")}>
                                                            {formatPct(s.actual_return_pct)}
                                                        </span>
                                                    </div>
                                                </td>
                                                <td className="px-4 py-2 border-r border-[#2D333B]">
                                                    <div className="flex flex-col gap-0.5 opacity-40">
                                                        <span className="text-[11px] font-mono text-white">{formatCurrency(s.mirror_nav)}</span>
                                                        <span className={cn("text-[9px] font-mono", s.mirror_return_pct >= 0 ? "text-emerald-500/60" : "text-rose-500/60")}>
                                                            {formatPct(s.mirror_return_pct)}
                                                        </span>
                                                    </div>
                                                </td>
                                                <td className="px-4 py-2 text-right">
                                                    <div className="inline-flex items-center gap-1.5 grayscale opacity-50">
                                                        <div className={cn("w-1 h-1 rounded-full", s.human_outperformance ? "bg-emerald-500" : "bg-white")} />
                                                        <span className="text-[9px] font-mono text-white uppercase tracking-tighter">
                                                            {s.human_outperformance ? "Positive_Alpha" : "Baseline"}
                                                        </span>
                                                    </div>
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </div>

                        {/* Archive Footer */}
                        <div className="h-40 border border-[#2D333B] bg-[#111418] flex flex-col overflow-hidden shrink-0">
                             <div className="px-4 py-1.5 bg-[#1C1F24] border-b border-[#2D333B] flex items-center justify-between">
                                <span className="text-[9px] font-bold text-white/40 uppercase tracking-widest">Simulation_Archive</span>
                             </div>
                             <div className="overflow-auto scrollbar-thin">
                                <table className="w-full text-left border-collapse">
                                    <tbody className="divide-y divide-[#2D333B]">
                                        {data.backtest_navs.map((nav, i) => (
                                            <tr key={i} className="hover:bg-white/[0.02]">
                                                <td className="px-4 py-1.5 font-mono text-[10px] text-white/40">{nav.run_id}</td>
                                                <td className="px-4 py-1.5 font-mono text-[10px] text-white/60">{formatCurrency(nav.end_nav)}</td>
                                                <td className={cn("px-4 py-1.5 font-mono text-[10px]", nav.return_pct >= 0 ? "text-emerald-500/40" : "text-rose-500/40")}>
                                                    {nav.return_pct >= 0 ? "+" : ""}{nav.return_pct.toFixed(2)}%
                                                </td>
                                                <td className="px-4 py-1.5 text-right font-mono text-[9px] text-white/20 uppercase tracking-tighter">{nav.data_points} POINTS</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                             </div>
                        </div>
                    </div>
                ) : (
                    <div className="py-20 text-center border border-dashed border-[#2D333B]">
                         <p className="text-[11px] font-mono text-white/20 uppercase tracking-[0.3em]">No_Sentinel_Nodes_Active</p>
                    </div>
                )}
            </div>
        </div>
    );
}

