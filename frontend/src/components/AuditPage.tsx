import { useState, useEffect } from "react";
import { MessageSquare, Loader2 } from "lucide-react";
import { AuditChatUI } from "./AuditChatUI";

const API_BASE = "http://localhost:8000";

interface RunInfo {
    run_id: string;
    status: string;
    start_time: number;
}

export function AuditPage() {
    const [runs, setRuns] = useState<RunInfo[]>([]);
    const [selectedRun, setSelectedRun] = useState("");
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        (async () => {
            try {
                const res = await fetch(`${API_BASE}/api/audit/runs`);
                if (res.ok) {
                    const data = await res.json();
                    setRuns(data.runs || []);
                    if (data.runs?.length > 0) {
                        setSelectedRun(data.runs[0].run_id);
                    }
                }
            } catch {} finally {
                setLoading(false);
            }
        })();
    }, []);

    return (
        <div className="flex h-full">
            {/* Run Selector */}
            <div className="w-64 border-r border-border bg-card/50 flex flex-col">
                <div className="px-4 py-3 border-b border-border">
                    <h2 className="text-sm font-semibold flex items-center gap-2">
                        <MessageSquare className="w-4 h-4 text-accent" />
                        Audit Chat
                    </h2>
                    <p className="text-[11px] text-muted-foreground mt-0.5">
                        Interrogate any backtest run
                    </p>
                </div>
                <div className="flex-1 overflow-y-auto p-2 scrollbar-thin">
                    {loading ? (
                        <div className="flex items-center justify-center py-8">
                            <Loader2 className="w-4 h-4 animate-spin text-muted-foreground" />
                        </div>
                    ) : runs.length === 0 ? (
                        <p className="text-xs text-muted-foreground p-3">
                            No finished runs found. Run a backtest to generate auditable data.
                        </p>
                    ) : (
                        runs.map((run) => (
                            <button
                                key={run.run_id}
                                onClick={() => setSelectedRun(run.run_id)}
                                className={`w-full text-left px-3 py-2 rounded-lg text-xs font-mono transition-colors mb-1 ${
                                    selectedRun === run.run_id
                                        ? "bg-accent/12 text-accent"
                                        : "text-muted-foreground hover:bg-muted/60 hover:text-foreground"
                                }`}
                            >
                                <div className="truncate">{run.run_id.slice(0, 16)}…</div>
                                <div className="text-[10px] text-muted-foreground mt-0.5">
                                    {new Date(run.start_time).toLocaleDateString()}
                                </div>
                            </button>
                        ))
                    )}
                </div>
            </div>

            {/* Chat Panel */}
            <div className="flex-1 h-full">
                <AuditChatUI runId={selectedRun} />
            </div>
        </div>
    );
}
