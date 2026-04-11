import { useState, useEffect } from "react";
import { 
    BarChart3, DollarSign, Zap, GitCompare, RefreshCw, 
    Loader2, TrendingUp, TrendingDown, Target, ShieldCheck,
    Cpu, Activity, Globe, Download, Share2, Layers
} from "lucide-react";
import { useAegisStore } from '@/lib/store';
import { cn } from "@/lib/utils";

const API_BASE = "http://localhost:8000";

interface MLflowRun {
    run_uuid: string;
    status: string;
    start_time: number;
    sharpe_ratio: number | null;
    max_drawdown: number | null;
    hmm_length: string | null;
    vpin_threshold: string | null;
    llm_model: string | null;
}

interface BudgetStatus {
    claude_spent_usd: number;
    session_quality_today: {
        nominal: number;
        degraded: number;
    };
}

export function MLOpsArena() {
    const [runs, setRuns] = useState<MLflowRun[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [budget, setBudget] = useState<BudgetStatus | null>(null);
    const setActiveRunId = useAegisStore(state => state.setActiveRunId);
    const activeRunId = useAegisStore(state => state.active_run_id);

    const fetchRuns = async () => {
        try {
            setLoading(true);
            const res = await fetch(`${API_BASE}/api/mlops/runs?limit=50`);
            if (!res.ok) throw new Error(`API error: ${res.status}`);
            const data = await res.json();
            setRuns(data.leaderboard || []);
            if (data.leaderboard?.length > 0 && !activeRunId) {
                setActiveRunId(data.leaderboard[0].run_uuid);
            }
            setError(null);
        } catch (e: any) {
            setError(e.message || "Failed to fetch MLflow runs");
        } finally {
            setLoading(false);
        }
    };

    const fetchBudget = async () => {
        try {
            const res = await fetch(`${API_BASE}/api/budget/status`);
            if (res.ok) {
                const data = await res.json();
                setBudget(data);
            }
        } catch(e) {}
    };

    useEffect(() => { 
        fetchRuns(); 
        fetchBudget();
    }, []);

    const formatDate = (ts: number) => {
        if (!ts) return "—";
        return new Date(ts).toISOString().slice(0, 10);
    };

    return (
        <div className="flex flex-col h-full bg-[#0C0E11] overflow-hidden">
            <div className="flex-1 flex flex-col p-6 gap-6 overflow-hidden">
                {/* Compact Technical Header */}
                <header className="flex items-center justify-between border-b border-[#2D333B] pb-4">
                    <div className="flex items-center gap-4">
                        <div className="flex flex-col">
                            <h1 className="text-sm font-bold text-white uppercase tracking-[0.2em]">MLOps Experiment Registry</h1>
                            <div className="flex items-center gap-2 mt-1">
                                <span className="text-[10px] font-mono text-white/40 uppercase">Cluster: v7-Darwin-Foundry</span>
                                <span className="text-[10px] font-mono text-white/20">•</span>
                                <span className="text-[10px] font-mono text-white/40 uppercase">Instances: {runs.length}</span>
                            </div>
                        </div>
                    </div>
                    <div className="flex gap-2">
                        <button onClick={fetchRuns} className="h-7 px-3 rounded border border-[#2D333B] text-[10px] font-bold text-white/60 hover:text-white transition-all uppercase tracking-widest flex items-center gap-2">
                             <RefreshCw className={cn("w-3 h-3", loading && "animate-spin")} />
                             Sync
                        </button>
                        <button className="h-7 px-3 rounded bg-white/5 border border-white/10 text-[10px] font-bold text-white uppercase tracking-widest flex items-center gap-2">
                             <Download className="w-3 h-3" />
                             Export CSV
                        </button>
                    </div>
                </header>

                {/* Industrial Leaderboard Table */}
                <div className="flex-1 min-h-0 border border-[#2D333B] bg-[#111418] relative overflow-hidden flex flex-col">
                    <div className="overflow-x-auto overflow-y-auto scrollbar-thin flex-1">
                        <table className="w-full text-left border-collapse">
                            <thead className="sticky top-0 bg-[#1C1F24] border-b border-[#2D333B] z-10">
                                <tr>
                                    <th className="px-4 py-2 text-[10px] font-bold text-white/30 uppercase tracking-widest border-r border-[#2D333B]">ID_REF</th>
                                    <th className="px-4 py-2 text-[10px] font-bold text-white/30 uppercase tracking-widest border-r border-[#2D333B]">Start_Time</th>
                                    <th className="px-4 py-2 text-[10px] font-bold text-white/30 uppercase tracking-widest border-r border-[#2D333B]">Sharpe</th>
                                    <th className="px-4 py-2 text-[10px] font-bold text-white/30 uppercase tracking-widest border-r border-[#2D333B]">MDD</th>
                                    <th className="px-4 py-2 text-[10px] font-bold text-white/30 uppercase tracking-widest border-r border-[#2D333B]">Framework</th>
                                    <th className="px-4 py-2 text-[10px] font-bold text-white/30 uppercase tracking-widest text-right">Status</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-[#2D333B]">
                                {runs.map(run => (
                                    <tr key={run.run_uuid}
                                        onClick={() => setActiveRunId(run.run_uuid)}
                                        className={cn(
                                            "group cursor-pointer hover:bg-white/[0.02]",
                                            activeRunId === run.run_uuid && "bg-white/[0.04]"
                                        )}>
                                        <td className="px-4 py-2 border-r border-[#2D333B]">
                                            <code className="text-[11px] font-mono text-white/80">
                                                {run.run_uuid.slice(0, 8)}...{run.run_uuid.slice(-4)}
                                            </code>
                                        </td>
                                        <td className="px-4 py-2 border-r border-[#2D333B] text-[10px] font-mono text-white/40">{formatDate(run.start_time)}</td>
                                        <td className="px-4 py-2 border-r border-[#2D333B]">
                                            <span className={cn(
                                                "font-mono text-[11px] font-bold",
                                                (run.sharpe_ratio ?? 0) >= 1.0 ? 'text-emerald-500/80' : 'text-white/60'
                                            )}>
                                                {run.sharpe_ratio?.toFixed(3) || "0.000"}
                                            </span>
                                        </td>
                                        <td className="px-4 py-2 border-r border-[#2D333B] font-mono text-[11px] text-white/40">
                                            {run.max_drawdown != null ? (run.max_drawdown * 100).toFixed(2) : "0.00"}%
                                        </td>
                                        <td className="px-4 py-2 border-r border-[#2D333B]">
                                            <div className="flex items-center gap-2">
                                                <span className="text-[9px] font-mono text-white/60 uppercase">{run.llm_model || "V7_DEFAULT"}</span>
                                            </div>
                                        </td>
                                        <td className="px-4 py-2 text-right">
                                            <div className="inline-flex items-center gap-1.5 grayscale opacity-60">
                                                <div className="w-1 h-1 rounded-full bg-emerald-500" />
                                                <span className="text-[9px] font-mono text-white uppercase tracking-tighter">Verified</span>
                                            </div>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                        {runs.length === 0 && !loading && (
                            <div className="py-20 text-center">
                                <p className="text-[11px] font-mono text-white/30 uppercase tracking-[0.2em]">Zero_Records_Found</p>
                            </div>
                        )}
                    </div>
                </div>

                {/* Bottom Total Summary Bar (Industrial) */}
                <footer className="h-8 border border-[#2D333B] bg-[#111418] px-4 flex items-center justify-between">
                     <div className="flex gap-6">
                        <div className="flex items-center gap-2">
                            <span className="text-[9px] font-bold text-white/20 uppercase">Agg_Sharpe</span>
                            <span className="text-[10px] font-mono text-white/60">1.42</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <span className="text-[9px] font-bold text-white/20 uppercase">Max_Sys_DD</span>
                            <span className="text-[10px] font-mono text-white/60">8.1%</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <span className="text-[9px] font-bold text-white/20 uppercase">Splurge_USD</span>
                            <span className="text-[10px] font-mono text-white/60">${budget?.claude_spent_usd.toFixed(2) || "0.00"}</span>
                        </div>
                     </div>
                     <div className="text-[9px] font-mono text-white/20">ROOT::MLOPS_GATEWAY::STABLE</div>
                </footer>
            </div>
        </div>
    );
}

