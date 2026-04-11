import React, { useState, useEffect } from "react";
import { DollarSign, Activity, Settings, Zap, AlertTriangle, ShieldCheck } from "lucide-react";

interface BudgetStatus {
    claude_spent_usd: number;
    claude_budget_usd: number;
    claude_pct_consumed: number;
    groq_daily_usage: Record<string, number>;
    groq_daily_limits: Record<string, number>;
    gemini_daily_usage: number;
    gemini_daily_limit: number;
    openrouter_daily_usage: number;
    openrouter_daily_limit: number;
    session_quality_today: {
        nominal: number;
        degraded: number;
    };
}

export function BudgetDashboard() {
    const [status, setStatus] = useState<BudgetStatus | null>(null);
    const [loading, setLoading] = useState(true);

    const fetchBudget = async () => {
        try {
            const res = await fetch('http://localhost:8000/api/budget/status');
            if (res.ok) {
                const data = await res.json();
                setStatus(data);
            }
        } catch (e) {
            console.error("Failed to fetch budget status", e);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchBudget();
        const interval = setInterval(fetchBudget, 60000); // 60 seconds
        return () => clearInterval(interval);
    }, []);

    if (loading && !status) {
        return <div className="p-8 text-slate-500 font-mono">Loading Budget Data...</div>;
    }

    if (!status) {
        return <div className="p-8 text-red-500 font-mono">Failed to load budget data.</div>;
    }

    const totalRuns = status.session_quality_today.nominal + status.session_quality_today.degraded;
    const nominalPct = totalRuns > 0 ? (status.session_quality_today.nominal / totalRuns) * 100 : 0;
    
    // Sum Groq traffic
    const totalGroqUsage = Object.values(status.groq_daily_usage).reduce((a, b) => a + b, 0);
    const totalTraffic = totalGroqUsage + status.gemini_daily_usage + status.openrouter_daily_usage;

    return (
        <div className="h-full bg-[#050508] p-6 overflow-y-auto">
            <h1 className="text-2xl font-bold text-white tracking-widest uppercase flex items-center gap-2 mb-6 font-mono">
                <DollarSign className="w-6 h-6 text-emerald-400" />
                V7 Budget & Quota Core
            </h1>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-2 gap-6 font-mono">
                
                {/* Panel 1: Claude Budget Gauge */}
                <div className="bg-[#111118] border border-slate-800 rounded-lg p-5">
                    <h2 className="text-sm text-slate-400 tracking-widest font-bold uppercase mb-4 flex items-center gap-2">
                        <Activity className="w-4 h-4 text-purple-400" />
                        Claude Absolute Budget Constraints
                    </h2>
                    
                    <div className="flex flex-col items-center justify-center py-6">
                        <div className="text-4xl font-bold mb-2 flex items-baseline gap-1">
                            <span className={status.claude_pct_consumed > 0.9 ? "text-red-500" : "text-emerald-400"}>
                                ${status.claude_spent_usd.toFixed(2)}
                            </span>
                            <span className="text-lg text-slate-500">/ ${status.claude_budget_usd.toFixed(2)}</span>
                        </div>
                        
                        <div className="w-full max-w-sm bg-slate-900 rounded-full h-3 mt-4 overflow-hidden border border-slate-800">
                            <div 
                                className={`h-full ${status.claude_pct_consumed > 0.9 ? 'bg-red-500' : 'bg-emerald-500'}`} 
                                style={{ width: `${Math.min(100, status.claude_pct_consumed * 100)}%` }}
                            ></div>
                        </div>
                        <div className="mt-2 text-[10px] text-slate-500 tracking-widest uppercase">
                            Cumulative Billing Cap: 99% Hard Cutoff
                        </div>
                    </div>
                </div>

                {/* Panel 2: Daily Quota Utilization */}
                <div className="bg-[#111118] border border-slate-800 rounded-lg p-5">
                    <h2 className="text-sm text-slate-400 tracking-widest font-bold uppercase mb-4 flex items-center gap-2">
                        <Settings className="w-4 h-4 text-blue-400" />
                        Daily Quota Utilization (Resets Midnight UTC)
                    </h2>
                    
                    <div className="space-y-4">
                        {Object.entries(status.groq_daily_usage).map(([model, usage]) => {
                            const limit = status.groq_daily_limits[model] || 14400;
                            const pct = Math.min(100, (usage / limit) * 100);
                            return (
                                <div key={model}>
                                    <div className="flex justify-between text-xs mb-1">
                                        <span className="text-blue-300 font-bold tracking-wide">{model.replace('groq/', '')}</span>
                                        <span className="text-slate-400">{usage} / {limit} RPD</span>
                                    </div>
                                    <div className="w-full bg-slate-900 rounded-full h-1.5 overflow-hidden">
                                        <div className="bg-blue-500 h-full" style={{ width: `${pct}%` }}></div>
                                    </div>
                                </div>
                            );
                        })}
                        
                        {/* Gemini & OpenRouter */}
                        <div className="pt-2 border-t border-slate-800">
                            <div className="flex justify-between text-xs mb-1">
                                <span className="text-purple-300 font-bold tracking-wide">gemini-2.5-flash (Google)</span>
                                <span className="text-slate-400">{status.gemini_daily_usage} / {status.gemini_daily_limit} RPD</span>
                            </div>
                            <div className="w-full bg-slate-900 rounded-full h-1.5 overflow-hidden">
                                <div className="bg-purple-500 h-full" style={{ width: `${Math.min(100, (status.gemini_daily_usage / status.gemini_daily_limit) * 100)}%` }}></div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Panel 3: Routing Distribution */}
                <div className="bg-[#111118] border border-slate-800 rounded-lg p-5">
                    <h2 className="text-sm text-slate-400 tracking-widest font-bold uppercase mb-4 flex items-center gap-2">
                        <Zap className="w-4 h-4 text-yellow-400" />
                        Provider Routing Distribution
                    </h2>
                    
                    <div className="flex flex-col justify-center gap-3">
                        <div className="flex items-center justify-between p-3 bg-slate-900/50 rounded border border-slate-800">
                            <span className="text-sm text-blue-300 font-bold uppercase tracking-wider">Fast Inference (Groq)</span>
                            <span className="text-sm font-bold text-slate-300">
                                {totalTraffic > 0 ? Math.round((totalGroqUsage / totalTraffic) * 100) : 0}%
                            </span>
                        </div>
                        <div className="flex items-center justify-between p-3 bg-slate-900/50 rounded border border-slate-800">
                            <span className="text-sm text-purple-300 font-bold uppercase tracking-wider">Mid-Tier Context (Gemini)</span>
                            <span className="text-sm font-bold text-slate-300">
                                {totalTraffic > 0 ? Math.round((status.gemini_daily_usage / totalTraffic) * 100) : 0}%
                            </span>
                        </div>
                        <div className="flex items-center justify-between p-3 bg-slate-900/50 rounded border border-slate-800">
                            <span className="text-sm text-amber-300 font-bold uppercase tracking-wider">Fallback (OpenRouter)</span>
                            <span className="text-sm font-bold text-slate-300">
                                {totalTraffic > 0 ? Math.round((status.openrouter_daily_usage / totalTraffic) * 100) : 0}%
                            </span>
                        </div>
                    </div>
                </div>

                {/* Panel 4: Session Quality Distribution */}
                <div className="bg-[#111118] border border-slate-800 rounded-lg p-5">
                    <h2 className="text-sm text-slate-400 tracking-widest font-bold uppercase mb-4 flex items-center gap-2">
                        <ShieldCheck className="w-4 h-4 text-cyan-400" />
                        Execution Integrity Index
                    </h2>
                    
                    <div className="flex flex-col items-center justify-center py-4">
                        <div className="relative w-32 h-32 mb-4">
                            <svg className="w-full h-full transform -rotate-90" viewBox="0 0 36 36">
                                <path
                                    className="text-slate-800"
                                    strokeWidth="3"
                                    stroke="currentColor"
                                    fill="none"
                                    d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                                />
                                <path
                                    className="text-emerald-400"
                                    strokeWidth="3"
                                    strokeDasharray={`${nominalPct}, 100`}
                                    stroke="currentColor"
                                    fill="none"
                                    d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                                />
                            </svg>
                            <div className="absolute inset-0 flex items-center justify-center flex-col">
                                <span className="text-2xl font-bold text-white">{Math.round(nominalPct)}%</span>
                            </div>
                        </div>
                        
                        <div className="flex items-center gap-6 text-xs uppercase tracking-widest font-bold mt-2">
                            <div className="flex items-center gap-1.5 text-emerald-400">
                                <div className="w-2 h-2 rounded-full bg-emerald-400"></div>
                                Nominal ({status.session_quality_today.nominal})
                            </div>
                            <div className="flex items-center gap-1.5 text-amber-500">
                                <div className="w-2 h-2 rounded-full bg-amber-500 shadow-[0_0_8px_rgba(245,158,11,0.5)]"></div>
                                Degraded ({status.session_quality_today.degraded})
                            </div>
                        </div>
                    </div>
                </div>

            </div>
        </div>
    );
}
