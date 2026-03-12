import { useState, useEffect } from "react";
import { BarChart3, DollarSign, Zap, GitCompare, RefreshCw, Loader2 } from "lucide-react";
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

    useEffect(() => { fetchRuns(); }, []);

    const formatDate = (ts: number) => {
        if (!ts) return "—";
        return new Date(ts).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
    };

    return (
        <div className="flex h-full">
            {/* Main Content */}
            <div className="flex-1 flex flex-col overflow-hidden">
                <div className="px-8 pt-8 pb-4">
                    <div className="flex items-center justify-between mb-1">
                        <h1 className="text-2xl font-semibold tracking-tight flex items-center gap-2.5">
                            <BarChart3 className="w-6 h-6 text-accent" />
                            MLOps Arena
                        </h1>
                        <button onClick={fetchRuns} disabled={loading}
                            className="flex items-center gap-2 px-3 py-1.5 rounded-lg border border-border text-sm text-muted-foreground hover:text-foreground hover:bg-muted/60 transition-colors">
                            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
                            Refresh
                        </button>
                    </div>
                    <p className="text-sm text-muted-foreground">
                        {runs.length} finished run{runs.length !== 1 ? "s" : ""} from MLflow
                    </p>
                </div>

                {error && (
                    <div className="mx-8 mb-4 rounded-lg border border-red-500/20 bg-red-500/5 text-red-400 p-3 text-sm">
                        {error}
                    </div>
                )}

                <div className="flex-1 overflow-auto px-8 pb-8">
                    {/* Leaderboard */}
                    <section className="mb-8">
                        <h2 className="text-xs font-semibold uppercase tracking-widest text-muted-foreground mb-3 flex items-center gap-2">
                            <Zap className="w-3.5 h-3.5" />
                            Leaderboard
                        </h2>

                        {loading ? (
                            <div className="flex items-center justify-center py-12">
                                <Loader2 className="w-5 h-5 animate-spin text-muted-foreground" />
                            </div>
                        ) : runs.length === 0 ? (
                            <div className="rounded-lg border border-border bg-card p-8 text-center text-sm text-muted-foreground">
                                No finished runs found. Run a backtest to populate the leaderboard.
                            </div>
                        ) : (
                            <div className="rounded-lg border border-border bg-card overflow-hidden">
                                <table className="w-full text-sm text-left">
                                    <thead className="text-[11px] uppercase tracking-wider text-muted-foreground border-b border-border">
                                        <tr>
                                            <th className="px-4 py-3 font-semibold">Run ID</th>
                                            <th className="px-4 py-3 font-semibold">Date</th>
                                            <th className="px-4 py-3 font-semibold">Sharpe</th>
                                            <th className="px-4 py-3 font-semibold">Max DD</th>
                                            <th className="px-4 py-3 font-semibold">Model</th>
                                            <th className="px-4 py-3 font-semibold">VPIN θ</th>
                                            <th className="px-4 py-3 text-right font-semibold">Action</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {runs.map(run => (
                                            <tr key={run.run_uuid}
                                                onClick={() => setSelectedRun(run.run_uuid)}
                                                className={`border-b border-border last:border-0 cursor-pointer transition-colors ${
                                                    selectedRun === run.run_uuid ? "bg-accent/5" : "hover:bg-muted/40"
                                                }`}>
                                                <td className="px-4 py-3 font-mono text-xs truncate max-w-[120px]">
                                                    {run.run_uuid.slice(0, 8)}…
                                                </td>
                                                <td className="px-4 py-3 text-muted-foreground text-xs">{formatDate(run.start_time)}</td>
                                                <td className={`px-4 py-3 font-mono font-semibold ${
                                                    (run.sharpe_ratio ?? 0) >= 1.0 ? 'text-emerald-500' :
                                                    (run.sharpe_ratio ?? 0) >= 0 ? 'text-foreground' : 'text-red-400'
                                                }`}>
                                                    {run.sharpe_ratio != null ? run.sharpe_ratio.toFixed(2) : "—"}
                                                </td>
                                                <td className="px-4 py-3 text-red-400 font-mono">
                                                    {run.max_drawdown != null ? `${(run.max_drawdown * 100).toFixed(1)}%` : "—"}
                                                </td>
                                                <td className="px-4 py-3 text-muted-foreground text-xs">{run.llm_model || "—"}</td>
                                                <td className="px-4 py-3 font-mono text-xs">{run.vpin_threshold || "—"}</td>
                                                <td className="px-4 py-3 text-right">
                                                    <button className="text-xs text-accent hover:text-accent/80 flex items-center gap-1 ml-auto transition-colors">
                                                        <GitCompare className="w-3 h-3" />
                                                        Compare
                                                    </button>
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        )}
                    </section>

                    {/* Cost Attribution */}
                    <section>
                        <h2 className="text-xs font-semibold uppercase tracking-widest text-muted-foreground mb-3 flex items-center gap-2">
                            <DollarSign className="w-3.5 h-3.5" />
                            Cost Attribution
                        </h2>
                        <div className="grid grid-cols-2 gap-3">
                            <div className="rounded-lg border border-border bg-card p-4">
                                <h3 className="text-[11px] uppercase tracking-wider text-muted-foreground mb-2">Model Signal Quality</h3>
                                <p className="text-xs text-muted-foreground italic">No data yet</p>
                            </div>
                            <div className="rounded-lg border border-border bg-card p-4">
                                <h3 className="text-[11px] uppercase tracking-wider text-muted-foreground mb-2">Cumulative Spend</h3>
                                <p className="text-xs text-muted-foreground italic">Tracking not yet active</p>
                            </div>
                        </div>
                    </section>
                </div>
            </div>

            {/* Right Sidebar: Audit Chat */}
            <div className="w-[380px] border-l border-border bg-card/50 flex flex-col">
                <div className="px-4 py-3 border-b border-border flex items-center justify-between">
                    <span className="text-sm font-medium">
                        Run: <span className="font-mono text-accent">{selectedRun ? `${selectedRun.slice(0, 12)}…` : "None"}</span>
                    </span>
                    <button className="text-xs text-accent hover:text-accent/80 font-medium transition-colors">
                        Promote
                    </button>
                </div>
                <div className="flex-1 min-h-0">
                    <AuditChatUI runId={selectedRun} />
                </div>
            </div>
        </div>
    );
}
