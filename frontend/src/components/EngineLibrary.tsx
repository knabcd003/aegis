import { useEffect, useState } from "react";
import { Library, CheckCircle2, Settings2, Loader2 } from "lucide-react";

const API_BASE = "http://localhost:8000";

interface EngineInfo {
    name: string;
    status: string;
    model: string;
    description: string;
}

export function EngineLibrary() {
    const [engines, setEngines] = useState<EngineInfo[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        (async () => {
            try {
                const res = await fetch(`${API_BASE}/api/system-health/quant`);
                if (res.ok) {
                    const data = await res.json();
                    setEngines(data.engines || []);
                }
            } catch {} finally {
                setLoading(false);
            }
        })();
    }, []);

    if (loading) {
        return (
            <div className="flex items-center justify-center h-full">
                <Loader2 className="w-5 h-5 animate-spin text-muted-foreground" />
            </div>
        );
    }

    return (
        <div className="max-w-4xl mx-auto p-8">
            <div className="mb-8">
                <h1 className="text-2xl font-semibold tracking-tight flex items-center gap-2.5">
                    <Library className="w-6 h-6 text-accent" />
                    Engine Library
                </h1>
                <p className="text-sm text-muted-foreground mt-1">
                    Registered quant engines and plugins
                </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {engines.map((engine, i) => (
                    <div key={i} className="rounded-lg border border-border bg-card p-5 hover:bg-muted/30 transition-colors">
                        <div className="flex items-start justify-between mb-3">
                            <div className="flex items-center gap-2">
                                <CheckCircle2 className={`w-4 h-4 ${engine.status === "AVAILABLE" ? "text-emerald-500" : "text-red-400"}`} />
                                <h3 className="text-sm font-semibold">{engine.name}</h3>
                            </div>
                            <span className={`text-[11px] font-medium px-2 py-0.5 rounded-full ${
                                engine.status === "AVAILABLE" ? "bg-emerald-500/10 text-emerald-500" : "bg-red-500/10 text-red-400"
                            }`}>
                                {engine.status}
                            </span>
                        </div>
                        <p className="text-xs text-muted-foreground mb-3">{engine.description}</p>
                        <div className="flex items-center justify-between pt-3 border-t border-border">
                            <span className="text-[11px] font-mono text-muted-foreground">{engine.model}</span>
                            <button className="text-xs text-accent hover:text-accent/80 flex items-center gap-1 transition-colors">
                                <Settings2 className="w-3 h-3" />
                                Configure
                            </button>
                        </div>
                    </div>
                ))}
            </div>

            {engines.length === 0 && (
                <div className="text-center py-16 text-muted-foreground text-sm">
                    No engines registered. Install the quant engine plugins to get started.
                </div>
            )}
        </div>
    );
}
