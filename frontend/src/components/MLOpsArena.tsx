import { useState } from "react";
import { BarChart2, DollarSign, ShieldCheck, Zap, GitCompare } from "lucide-react";
import { AuditChatUI } from "./AuditChatUI";

const mockRuns = [
    { id: "run-alpha-09", name: "Alpha-Macro-1 (Baseline)", sharpe: 1.2, return_pct: 14.5, active: true },
    { id: "run-alpha-10", name: "Alpha-Macro-1 (Tune-VPIN)", sharpe: 1.5, return_pct: 18.2, active: false }
];

export function MLOpsArena() {
    const [selectedRun, setSelectedRun] = useState<string>("run-alpha-10");

    return (
        <div className="flex flex-col h-full w-full bg-background p-6 overflow-hidden">
            <div className="flex items-center justify-between mb-6 border-b border-border pb-4 shrink-0">
                <div>
                    <h1 className="text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
                        <BarChart2 className="h-6 w-6 text-green-500" />
                        MLflow Arena
                    </h1>
                    <p className="text-muted-foreground mt-1 text-sm">
                        Leaderboard, Cost Attribution, and Agent Audit Chat
                    </p>
                </div>
            </div>

            <div className="flex-1 min-h-0 flex gap-6 overflow-hidden">
                {/* Left Column: Leaderboard & Cost Attribution */}
                <div className="w-1/2 flex flex-col gap-6 overflow-y-auto pr-2 scrollbar-thin scrollbar-thumb-gray-700">
                    {/* Leaderboard Table */}
                    <div className="bg-card/50 border border-border rounded-lg p-5">
                        <h2 className="text-lg font-bold flex items-center gap-2 mb-4 text-purple-400">
                            <Zap className="w-5 h-5" />
                            Configuration Leaderboard
                        </h2>
                        <div className="border border-border/50 rounded-md overflow-hidden bg-[#0d0d12]">
                            <table className="w-full text-sm text-left font-mono">
                                <thead className="bg-[#14141b] text-gray-400 text-xs uppercase border-b border-border/50">
                                    <tr>
                                        <th className="px-4 py-3">Run ID</th>
                                        <th className="px-4 py-3">Sharpe</th>
                                        <th className="px-4 py-3">Return</th>
                                        <th className="px-4 py-3 text-right">Action</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {mockRuns.map(run => (
                                        <tr 
                                            key={run.id} 
                                            onClick={() => setSelectedRun(run.id)}
                                            className={`border-b border-border/30 hover:bg-white/5 cursor-pointer transition-colors ${selectedRun === run.id ? 'bg-primary/10' : ''}`}
                                        >
                                            <td className="px-4 py-3 font-semibold text-gray-300">
                                                {run.name} 
                                                {run.active && <span className="ml-2 text-[10px] bg-green-500/20 text-green-400 px-1 py-0.5 rounded">SENTINEL</span>}
                                            </td>
                                            <td className="px-4 py-3 text-cyan-400">{run.sharpe.toFixed(2)}</td>
                                            <td className="px-4 py-3 text-green-400">+{run.return_pct.toFixed(1)}%</td>
                                            <td className="px-4 py-3 text-right">
                                                <button className="text-xs bg-blue-500/10 hover:bg-blue-500/20 text-blue-400 px-2 py-1 rounded">Compare</button>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>

                    {/* Cost Attribution View */}
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
                                        <span className="text-green-400">82% Win Rate</span>
                                    </div>
                                    <div className="flex justify-between text-sm font-mono">
                                        <span className="text-blue-400">Qwen 2.5 32B</span>
                                        <span className="text-green-400">68% Win Rate</span>
                                    </div>
                                </div>
                            </div>
                            <div className="bg-[#0d0d12] p-4 rounded-md border border-border/50">
                                <h3 className="text-xs uppercase text-gray-500 tracking-wider mb-2">Cumulative Spend</h3>
                                <div className="flex items-center gap-2">
                                    <span className="text-2xl font-bold font-mono text-red-400">$142.50</span>
                                    <span className="text-xs text-gray-500">(Last 30 Days)</span>
                                </div>
                                <div className="mt-2 text-xs text-gray-400">Router efficiency: <span className="text-cyan-400 font-bold ml-1">High (8.2% override rate)</span></div>
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
                            <span className="font-bold text-cyan-400">{selectedRun}</span>
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
