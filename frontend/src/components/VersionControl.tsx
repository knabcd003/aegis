import { useEffect, useState } from "react";
import { GitBranch, Loader2, Clock, CheckCircle2 } from "lucide-react";

const API_BASE = "http://localhost:8000";

interface LineageEntry {
    version: string;
    timestamp: string;
    changes: string[];
    promoted_from?: string;
}

export function VersionControl() {
    const [lineage, setLineage] = useState<LineageEntry[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        (async () => {
            try {
                // Try to load the lineage config file via a simple proxy
                const res = await fetch(`${API_BASE}/api/systems`);
                if (res.ok) {
                    // For now we show the system configs as versions
                    setLineage([]);
                }
            } catch {} finally {
                setLoading(false);
            }
        })();
    }, []);

    return (
        <div className="max-w-3xl mx-auto p-8">
            <div className="mb-8">
                <h1 className="text-2xl font-semibold tracking-tight flex items-center gap-2.5">
                    <GitBranch className="w-6 h-6 text-accent" />
                    Version Control
                </h1>
                <p className="text-sm text-muted-foreground mt-1">
                    Config lineage and rollback history
                </p>
            </div>

            {loading ? (
                <div className="flex items-center justify-center py-12">
                    <Loader2 className="w-5 h-5 animate-spin text-muted-foreground" />
                </div>
            ) : lineage.length === 0 ? (
                <div className="rounded-lg border border-border bg-card p-8 text-center">
                    <GitBranch className="w-8 h-8 text-muted-foreground mx-auto mb-3" />
                    <p className="text-sm text-muted-foreground">
                        No config lineage recorded yet. Generate and deploy a strategy to start tracking versions.
                    </p>
                    <p className="text-[11px] text-muted-foreground mt-2">
                        Lineage data is stored in <span className="font-mono">config/lineage.json</span>
                    </p>
                </div>
            ) : (
                <div className="space-y-3">
                    {lineage.map((entry, i) => (
                        <div key={i} className="rounded-lg border border-border bg-card p-4 flex items-start gap-3">
                            <CheckCircle2 className="w-4 h-4 text-emerald-500 mt-0.5 shrink-0" />
                            <div className="flex-1">
                                <div className="flex items-center gap-2 mb-1">
                                    <span className="text-sm font-semibold font-mono">{entry.version}</span>
                                    <span className="text-[11px] text-muted-foreground flex items-center gap-1">
                                        <Clock className="w-3 h-3" />
                                        {entry.timestamp}
                                    </span>
                                </div>
                                <ul className="space-y-0.5">
                                    {entry.changes.map((change, j) => (
                                        <li key={j} className="text-xs text-muted-foreground">• {change}</li>
                                    ))}
                                </ul>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
