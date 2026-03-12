import { useEffect, useState } from "react";
import { HeartPulse, Wifi, WifiOff, Cpu, RefreshCw, Loader2, CheckCircle2, AlertTriangle, XCircle } from "lucide-react";

const API_BASE = "http://localhost:8000";

interface ConnectorInfo {
    name: string;
    status: string;
    last_successful_fetch: string | null;
    priority: number;
}

interface EngineInfo {
    name: string;
    status: string;
    model: string;
    description: string;
    error?: string;
}

export function SystemHealth() {
    const [connectors, setConnectors] = useState<ConnectorInfo[]>([]);
    const [engines, setEngines] = useState<EngineInfo[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const load = async () => {
        try {
            setLoading(true);
            const [connRes, engRes] = await Promise.all([
                fetch(`${API_BASE}/api/system-health/connectors`),
                fetch(`${API_BASE}/api/system-health/quant`)
            ]);
            if (connRes.ok) {
                const data = await connRes.json();
                setConnectors(data.connectors || []);
            }
            if (engRes.ok) {
                const data = await engRes.json();
                setEngines(data.engines || []);
            }
            setError(null);
        } catch (e: any) {
            setError(e.message);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => { load(); }, []);

    const statusIcon = (status: string) => {
        switch (status) {
            case "MONITORING":
            case "AVAILABLE":
                return <CheckCircle2 className="w-4 h-4 text-emerald-500" />;
            case "DEGRADED":
                return <AlertTriangle className="w-4 h-4 text-amber-500" />;
            default:
                return <XCircle className="w-4 h-4 text-red-400" />;
        }
    };

    return (
        <div className="max-w-4xl mx-auto p-8">
            <div className="flex items-center justify-between mb-8">
                <div>
                    <h1 className="text-2xl font-semibold tracking-tight flex items-center gap-2.5">
                        <HeartPulse className="w-6 h-6 text-accent" />
                        System Health
                    </h1>
                    <p className="text-sm text-muted-foreground mt-1">
                        Real-time status of data connectors and quant engines
                    </p>
                </div>
                <button onClick={load} disabled={loading}
                    className="flex items-center gap-2 px-3 py-1.5 rounded-lg border border-border text-sm text-muted-foreground hover:text-foreground hover:bg-muted/60 transition-colors">
                    <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
                    Refresh
                </button>
            </div>

            {error && (
                <div className="rounded-lg border border-red-500/20 bg-red-500/5 p-4 text-sm text-red-400 mb-6">
                    {error}
                </div>
            )}

            {/* Connectors */}
            <section className="mb-8">
                <h2 className="text-xs font-semibold uppercase tracking-widest text-muted-foreground mb-3 flex items-center gap-2">
                    <Wifi className="w-3.5 h-3.5" />
                    Data Connectors
                </h2>
                <div className="space-y-2">
                    {connectors.length === 0 && !loading && (
                        <p className="text-sm text-muted-foreground py-4">No connectors registered.</p>
                    )}
                    {connectors.map((c, i) => (
                        <div key={i} className="flex items-center justify-between rounded-lg border border-border bg-card p-4 transition-colors hover:bg-muted/30">
                            <div className="flex items-center gap-3">
                                {statusIcon(c.status)}
                                <div>
                                    <p className="text-sm font-medium">{c.name}</p>
                                    <p className="text-xs text-muted-foreground">Priority {c.priority}</p>
                                </div>
                            </div>
                            <div className="text-right">
                                <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${
                                    c.status === "MONITORING" ? "bg-emerald-500/10 text-emerald-500" :
                                    c.status === "DEGRADED" ? "bg-amber-500/10 text-amber-500" :
                                    "bg-red-500/10 text-red-400"
                                }`}>
                                    {c.status}
                                </span>
                                {c.last_successful_fetch && (
                                    <p className="text-[11px] text-muted-foreground mt-1">
                                        Last fetch: {new Date(c.last_successful_fetch).toLocaleTimeString()}
                                    </p>
                                )}
                            </div>
                        </div>
                    ))}
                </div>
            </section>

            {/* Quant Engines */}
            <section>
                <h2 className="text-xs font-semibold uppercase tracking-widest text-muted-foreground mb-3 flex items-center gap-2">
                    <Cpu className="w-3.5 h-3.5" />
                    Quant Engines
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                    {engines.map((e, i) => (
                        <div key={i} className="rounded-lg border border-border bg-card p-4 transition-colors hover:bg-muted/30">
                            <div className="flex items-center gap-2 mb-2">
                                {statusIcon(e.status)}
                                <h3 className="text-sm font-medium">{e.name}</h3>
                            </div>
                            <p className="text-xs text-muted-foreground mb-2">{e.description}</p>
                            <div className="flex items-center justify-between">
                                <span className="text-[11px] font-mono text-muted-foreground">{e.model}</span>
                                <span className={`text-[11px] font-medium ${
                                    e.status === "AVAILABLE" ? "text-emerald-500" : "text-red-400"
                                }`}>{e.status}</span>
                            </div>
                        </div>
                    ))}
                </div>
            </section>

            {loading && (
                <div className="flex items-center justify-center py-12">
                    <Loader2 className="w-5 h-5 animate-spin text-muted-foreground" />
                </div>
            )}
        </div>
    );
}
