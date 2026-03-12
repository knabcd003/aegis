import { useState, useEffect } from "react";
import { BarChart2, DollarSign, ShieldCheck, Zap, GitCompare, RefreshCw, Loader2 } from "lucide-react";
import { AuditChatUI } from "./AuditChatUI";

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

export function MLOpsArena() {
    const [runs, setRuns] = useState<MLflowRun[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [selectedRun, setSelectedRun] = useState<string>("");

    const fetchRuns = async () => {
        try {
            setLoading(true);
            const res = await fetch(`${API_BASE}/api/mlops/runs?limit=50`);
            if (!res.ok) throw new Error(`API error: ${res.status}`);
            const data = await res.json();
            setRuns(data.leaderboard || []);
            if (data.leaderboard?.length > 0 && !selectedRun) {
                setSelectedRun(data.leaderboard[0].run_uuid);
            }
            setError(null);
        } catch (e: any) {
            setError(e.message || "Failed to fetch MLflow runs");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchRuns();
    }, []);

    const formatDate = (ts: number) => {
        if (!ts) return "—";
        return new Date(ts).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
    };

    return (
        <div className="flex flex-col h-full w-full bg-background p-6 overflow-hidden">
            <div className="flex items-center justify-between mb-6 border-b border-border pb-4 shrink-0">
                <div>
                    <h1 className="text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
                        <BarChart2 className="h-6 w-6 text-green-500" />
                        MLflow Arena
                    </h1>
                    <p className="text-muted-foreground mt-1 text-sm">
                        {runs.length} finished runs from local MLflow database
                    </p>
                </div>
                <button
                    onClick={fetchRuns}
                    disabled={loading}
                    className="flex items-center gap-2 px-4 py-2 rounded-md border border-border text-muted-foreground hover:text-foreground hover:bg-secondary/50 text-sm transition-colors"
                >
                    <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
                    Refresh
                </button>
            </div>

            {error && (
                <div className="border border-red-500/30 bg-red-500/10 text-red-400 rounded-lg p-4 mb-4 text-sm font-mono">
                    {error}
                </div>
            )}

            <div className="flex-1 min-h-0 flex gap-6 overflow-hidden">
                {/* Left Column: Leaderboard */}
                <div className="w-1/2 flex flex-col gap-6 overflow-y-auto pr-2 scrollbar-thin scrollbar-thumb-gray-700">
                    {/* Leaderboard Table */}
                    <div className="bg-card/50 border border-border rounded-lg p-5">
                        <h2 className="text-lg font-bold flex items-center gap-2 mb-4 text-purple-400">
                            <Zap className="w-5 h-5" />
                            Configuration Leaderboard
                        </h2>

                        {loading ? (
                            <div className="flex items-center justify-center py-12">
                                <Loader2 className="w-6 h-6 text-muted-foreground animate-spin" />
                            </div>
                        ) : runs.length === 0 ? (
                            <div className="text-center py-12 text-muted-foreground text-sm">
                                No finished MLflow runs found. Run a backtest to populate the leaderboard.
                            </div>
                        ) : (
                            <div className="border border-border/50 rounded-md overflow-hidden bg-[#0d0d12]">
                                <table className="w-full text-sm text-left font-mono">
                                    <thead className="bg-[#14141b] text-gray-400 text-xs uppercase border-b border-border/50">
                                        <tr>
                                            <th className="px-4 py-3">Run ID</th>
                                            <th className="px-4 py-3">Date</th>
                                            <th className="px-4 py-3">Sharpe</th>
                                            <th className="px-4 py-3">Max DD</th>
                                            <th className="px-4 py-3">Model</th>
                                            <th className="px-4 py-3">VPIN θ</th>
                                            <th className="px-4 py-3 text-right">Action</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {runs.map(run => (
                                            <tr
                                                key={run.run_uuid}
                                                onClick={() => setSelectedRun(run.run_uuid)}
                                                className={`border-b border-border/30 hover:bg-white/5 cursor-pointer transition-colors ${selectedRun === run.run_uuid ? 'bg-primary/10' : ''}`}
                                            >
                                                <td className="px-4 py-3 font-semibold text-gray-300 truncate max-w-[120px]">
                                                    {run.run_uuid.slice(0, 8)}…
                                                </td>
                                                <td className="px-4 py-3 text-gray-500 text-xs">
                                                    {formatDate(run.start_time)}
                                                </td>
                                                <td className={`px-4 py-3 font-bold ${(run.sharpe_ratio ?? 0) >= 1.0 ? 'text-green-400' : (run.sharpe_ratio ?? 0) >= 0 ? 'text-cyan-400' : 'text-red-400'}`}>
                                                    {run.sharpe_ratio != null ? run.sharpe_ratio.toFixed(2) : "—"}
                                                </td>
                                                <td className="px-4 py-3 text-red-400">
                                                    {run.max_drawdown != null ? `${(run.max_drawdown * 100).toFixed(1)}%` : "—"}
                                                </td>
                                                <td className="px-4 py-3 text-purple-400 text-xs">
                                                    {run.llm_model || "—"}
                                                </td>
                                                <td className="px-4 py-3 text-blue-400">
                                                    {run.vpin_threshold || "—"}
                                                </td>
                                                <td className="px-4 py-3 text-right">
                                                    <button className="text-xs bg-blue-500/10 hover:bg-blue-500/20 text-blue-400 px-2 py-1 rounded">
                                                        <GitCompare className="w-3 h-3 inline mr-1" />
                                                        Compare
                                                    </button>
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        )}
                    </div>

                    {/* Cost Attribution View — will be wired to real data later */}
                    <div className="bg-card/50 border border-border rounded-lg p-5">
                        <h2 className="text-lg font-bold flex items-center gap-2 mb-4 text-yellow-500">
                            <DollarSign className="w-5 h-5" />
                            Cost Attribution View
                        </h2>
                        <div className="grid grid-cols-2 gap-4">
                            <div className="bg-[#0d0d12] p-4 rounded-md border border-border/50">
                                <h3 className="text-xs uppercase text-gray-500 tracking-wider mb-2">Model Signal Quality</h3>
                                <div className="space-y-2">
                                    <div className="flex justify-between text-sm font-mono">
                                        <span className="text-purple-400">Claude 3.5 Sonnet</span>
                                        <span className="text-gray-500 italic text-xs">No data yet</span>
                                    </div>
                                    <div className="flex justify-between text-sm font-mono">
                                        <span className="text-blue-400">Qwen 2.5 32B</span>
                                        <span className="text-gray-500 italic text-xs">No data yet</span>
                                    </div>
                                </div>
                            </div>
                            <div className="bg-[#0d0d12] p-4 rounded-md border border-border/50">
                                <h3 className="text-xs uppercase text-gray-500 tracking-wider mb-2">Cumulative Spend</h3>
                                <div className="flex items-center gap-2">
                                    <span className="text-2xl font-bold font-mono text-gray-500">—</span>
                                    <span className="text-xs text-gray-500">(Tracking not yet active)</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Right Column: Audit Chat & Actions */}
                <div className="w-1/2 flex flex-col gap-4">
                    {/* Action Bar */}
                    <div className="bg-[#14141b] border border-border/80 rounded-lg p-4 flex items-center justify-between shadow-lg">
                        <div className="font-mono text-sm">
                            <span className="text-gray-500 mr-2">Selected Run:</span>
                            <span className="font-bold text-cyan-400">{selectedRun ? `${selectedRun.slice(0, 12)}…` : "None"}</span>
                        </div>
                        <div className="flex gap-2">
                            <button className="flex items-center gap-2 bg-blue-500/10 hover:bg-blue-500/20 text-blue-400 border border-blue-500/30 px-3 py-1.5 rounded text-sm transition-colors">
                                <GitCompare className="w-4 h-4" />
                                Diff Config
                            </button>
                            <button
                                className="flex items-center gap-2 bg-green-500/10 hover:bg-green-500/20 text-green-400 border border-green-500/30 px-3 py-1.5 rounded text-sm font-bold transition-colors"
                            >
                                <ShieldCheck className="w-4 h-4" />
                                Promote to Sentinel
                            </button>
                        </div>
                    </div>

                    {/* Audit Chat */}
                    <div className="flex-1 min-h-0">
                        <AuditChatUI runId={selectedRun} />
                    </div>
                </div>
            </div>
        </div>
    );
}
