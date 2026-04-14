import { useState, useEffect } from "react";
import { 
    BarChart3, DollarSign, Zap, GitCompare, RefreshCw, 
    Loader2, TrendingUp, TrendingDown, Target, ShieldCheck,
    Cpu, Activity, Globe, Download, Share2, Layers,
    AlertTriangle, Info, TrendingUp as TrendingUpIcon,
    ArrowUpRight, ArrowDownRight, MoreHorizontal
} from "lucide-react";
import { 
    LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, 
    ResponsiveContainer, AreaChart, Area 
} from 'recharts';
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

const mockChartData = [
    { name: '00:00', live: 150, ideal: 150, counter: 150 },
    { name: '04:00', live: 140, ideal: 130, counter: 160 },
    { name: '08:00', live: 160, ideal: 140, counter: 175 },
    { name: '12:00', live: 120, ideal: 90, counter: 180 },
    { name: '16:00', live: 80, ideal: 50, counter: 190 },
    { name: '20:00', live: 20, ideal: 10, counter: 160 },
];

export function MLOpsArena() {
    const [runs, setRuns] = useState<MLflowRun[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [budget, setBudget] = useState<any>(null);
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
        } catch (e: any) {
            setError(e.message);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => { 
        fetchRuns(); 
    }, []);

    return (
        <div className="p-8 max-w-screen-2xl mx-auto space-y-8">
            {/* Hero Grid: Performance & Bear Bias */}
            <div className="grid grid-cols-12 gap-6">
                {/* Main Chart Card */}
                <div className="col-span-12 lg:col-span-8 bg-surface-container rounded-xl p-6 border border-white/5 relative overflow-hidden group">
                    <div className="flex justify-between items-start mb-8">
                        <div>
                            <h3 className="font-headline text-xl font-medium text-on-surface">Cumulative Performance</h3>
                            <p className="text-on-surface-variant text-xs mt-1 italic">Relative alpha comparison across simulation regimes.</p>
                        </div>
                        <div className="flex gap-4">
                            <div className="flex items-center gap-2">
                                <span className="w-2 h-2 rounded-full bg-primary"></span>
                                <span className="text-[0.6875rem] text-on-surface-variant font-bold uppercase tracking-widest">Live</span>
                            </div>
                            <div className="flex items-center gap-2">
                                <span className="w-2 h-2 rounded-full bg-secondary"></span>
                                <span className="text-[0.6875rem] text-on-surface-variant font-bold uppercase tracking-widest">Ideal</span>
                            </div>
                            <div className="flex items-center gap-2">
                                <span className="w-2 h-2 rounded-full border border-outline"></span>
                                <span className="text-[0.6875rem] text-on-surface-variant font-bold uppercase tracking-widest">Counterfactual</span>
                            </div>
                        </div>
                    </div>
                    
                    <div className="h-64 w-full">
                        <ResponsiveContainer width="100%" height="100%">
                            <LineChart data={mockChartData}>
                                <Line type="monotone" dataKey="live" stroke="#FFB59E" strokeWidth={3} dot={false} />
                                <Line type="monotone" dataKey="ideal" stroke="#ACCEC5" strokeWidth={2} strokeDasharray="8 4" dot={false} />
                                <Line type="monotone" dataKey="counter" stroke="#a38c85" strokeWidth={1.5} dot={false} />
                                <Tooltip 
                                    contentStyle={{ background: '#1C1C1A', border: '1px solid #2D333B', borderRadius: '8px' }}
                                    itemStyle={{ fontSize: '12px', fontWeight: 'bold' }}
                                />
                            </LineChart>
                        </ResponsiveContainer>
                    </div>

                    <div className="mt-6 flex gap-12 border-t border-white/5 pt-6">
                        <div>
                            <p className="text-[0.6875rem] text-on-surface-variant uppercase tracking-widest font-bold">Live Alpha</p>
                            <p className="font-headline text-2xl text-on-surface font-medium">+14.2%</p>
                        </div>
                        <div>
                            <p className="text-[0.6875rem] text-on-surface-variant uppercase tracking-widest font-bold">Slippage Loss</p>
                            <p className="font-headline text-2xl text-tertiary font-medium">-0.82%</p>
                        </div>
                        <div>
                            <p className="text-[0.6875rem] text-on-surface-variant uppercase tracking-widest font-bold">Execution Edge</p>
                            <p className="font-headline text-2xl text-secondary font-medium">+2.1%</p>
                        </div>
                    </div>
                </div>

                {/* Bear Bias Report Card */}
                <div className="col-span-12 lg:col-span-4 bg-surface-container rounded-xl p-6 border border-white/5">
                    <div className="flex justify-between items-center mb-6">
                        <h3 className="font-headline text-xl font-medium text-on-surface">Bear Bias Report</h3>
                        <AlertTriangle className="text-tertiary w-5 h-5" />
                    </div>
                    <div className="space-y-6">
                        <div className="p-4 bg-surface-container-low rounded-lg border-l-4 border-tertiary-container">
                            <p className="text-[0.6875rem] text-on-surface-variant uppercase tracking-widest mb-1 font-bold">Adversarial Win Rate</p>
                            <div className="flex justify-between items-end">
                                <p className="font-headline text-3xl font-semibold text-on-surface">62.1%</p>
                                <span className="text-tertiary text-xs font-bold uppercase">+4.2% (24h)</span>
                            </div>
                        </div>
                        <div className="space-y-4">
                            <div>
                                <div className="flex justify-between text-[0.75rem] mb-1.5 font-bold uppercase tracking-tight">
                                    <span className="text-on-surface-variant">Regime Sensitivity</span>
                                    <span className="text-on-surface">High</span>
                                </div>
                                <div className="w-full bg-surface-container-highest h-1.5 rounded-full overflow-hidden">
                                    <div className="bg-tertiary h-full rounded-full w-[85%]"></div>
                                </div>
                            </div>
                            <div>
                                <div className="flex justify-between text-[0.75rem] mb-1.5 font-bold uppercase tracking-tight">
                                    <span className="text-on-surface-variant">Agent Decay Rate</span>
                                    <span className="text-on-surface">Moderate</span>
                                </div>
                                <div className="w-full bg-surface-container-highest h-1.5 rounded-full overflow-hidden">
                                    <div className="bg-primary h-full rounded-full w-[42%]"></div>
                                </div>
                            </div>
                        </div>
                        <div className="pt-4 border-t border-white/5">
                            <p className="text-[0.75rem] text-on-surface-variant italic leading-relaxed">
                                "Current adversarial nodes are exploiting high-volatility liquidity gaps. Recommend increasing hedging delta for Delta-Neutral clusters."
                            </p>
                        </div>
                    </div>
                </div>
            </div>

            {/* Strategy Leaderboard & Stress Matrix */}
            <div className="grid grid-cols-12 gap-6">
                {/* Leaderboard */}
                <div className="col-span-12 xl:col-span-8 bg-surface-container rounded-xl overflow-hidden border border-white/5">
                    <div className="px-6 py-5 border-b border-white/5 flex justify-between items-center">
                        <h3 className="font-headline text-xl font-medium">Strategy Leaderboard</h3>
                        <button className="text-primary text-[0.8125rem] font-bold uppercase tracking-widest flex items-center gap-2 hover:underline">
                            Export CSV <Download className="w-4 h-4" />
                        </button>
                    </div>
                    <div className="overflow-x-auto">
                        <table className="w-full text-left">
                            <thead>
                                <tr className="text-[0.6875rem] uppercase tracking-widest text-on-surface-variant border-b border-white/5 font-bold">
                                    <th className="px-6 py-4">Strategy Node</th>
                                    <th className="px-6 py-4">Sharpe</th>
                                    <th className="px-6 py-4">Drawdown</th>
                                    <th className="px-6 py-4">Status</th>
                                    <th className="px-6 py-4 text-right">Performance</th>
                                </tr>
                            </thead>
                            <tbody className="text-[0.8125rem] divide-y divide-white/5">
                                {runs.map((run, i) => (
                                    <tr key={run.run_uuid} className="hover:bg-white/[0.02] transition-colors group">
                                        <td className="px-6 py-4">
                                            <div className="flex items-center gap-3">
                                                <div className="w-2 h-2 rounded-full bg-secondary"></div>
                                                <span className="font-bold font-mono text-[11px]">{run.run_uuid.slice(0, 12)}</span>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4 font-bold text-secondary font-mono">{run.sharpe_ratio?.toFixed(2) || "0.00"}</td>
                                        <td className="px-6 py-4 text-on-surface-variant font-mono">{(run.max_drawdown! * 100).toFixed(1)}%</td>
                                        <td className="px-6 py-4">
                                            <span className="px-2 py-1 rounded bg-secondary/10 text-secondary text-[0.625rem] font-bold uppercase tracking-widest border border-secondary/20">Active</span>
                                        </td>
                                        <td className="px-6 py-4 text-right font-headline font-medium text-lg">
                                            +{(Math.random() * 10).toFixed(1)}%
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>

                {/* Scenario Stress Matrix */}
                <div className="col-span-12 xl:col-span-4 bg-surface-container rounded-xl p-6 border border-white/5">
                    <div className="mb-6">
                        <h3 className="font-headline text-xl font-medium">Scenario Stress Matrix</h3>
                        <p className="text-[0.6875rem] text-on-surface-variant uppercase tracking-widest mt-1 font-bold">Impact probability heatmap</p>
                    </div>
                    <div className="grid grid-cols-4 gap-2">
                        {[...Array(16)].map((_, i) => (
                            <div key={i} className={cn(
                                "aspect-square rounded flex items-center justify-center font-bold text-[10px] transition-all hover:scale-105 cursor-help",
                                i % 5 === 0 ? "bg-tertiary/60 border border-tertiary" : 
                                i % 3 === 0 ? "bg-primary/40 border border-primary/50" : 
                                "bg-secondary/20 border border-secondary/30"
                            )}>
                                {i % 5 === 0 ? "CRIT" : i % 3 === 0 ? "HIGH" : "SAFE"}
                            </div>
                        ))}
                    </div>
                    <div className="mt-6 flex flex-col gap-3">
                        <div className="flex items-center justify-between text-[0.75rem] font-bold">
                            <span className="text-on-surface-variant uppercase tracking-tight">Top Risk Factor</span>
                            <span className="text-tertiary uppercase">Liquidity Crisis</span>
                        </div>
                        <div className="flex items-center justify-between text-[0.75rem] font-bold">
                            <span className="text-on-surface-variant uppercase tracking-tight">Current VIX Level</span>
                            <span className="text-on-surface font-mono">18.42</span>
                        </div>
                    </div>
                    <button className="w-full mt-6 py-3 border border-outline/20 text-on-surface-variant text-[0.75rem] font-bold uppercase tracking-widest rounded hover:bg-white/5 transition-all active:scale-95">
                        Run New Monte Carlo
                    </button>
                </div>
            </div>
        </div>
    );
}

