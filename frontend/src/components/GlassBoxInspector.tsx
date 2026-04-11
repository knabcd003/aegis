import React, { useState, useEffect } from 'react';
import { 
    SquareSquare, ChevronDown, ChevronRight, Activity, Terminal, 
    Key, Database, ShieldCheck, Cpu, Zap, Search, Fingerprint,
    Lock, CheckCircle2, AlertCircle, Info, Clock
} from "lucide-react";
import { useAegisStore } from '@/lib/store';
import { cn } from "@/lib/utils";

export function GlassBoxInspector() {
    const activeRunId = useAegisStore(state => state.active_run_id);
    const sessionQuality = useAegisStore(state => state.session_quality);
    const tokens = useAegisStore(state => state.tokens);
    const pendingSignals = useAegisStore(state => state.pending_signals);

    const [activeLevel, setActiveLevel] = useState<number>(0);
    const [stream, setStream] = useState<string[]>([]);

    // Simulate streaming logs for the demo effect
    useEffect(() => {
        if (!activeRunId) return;
        const messages = [
            "INIT: Pipeline sequence alpha-7 initialized.",
            "AUTH: RSA-4096 signature verified for mandate.",
            "LOAD: Mounting 5-year historical OHLCV mesh...",
            "PROC: Applying SMA(20, 50) vector alignment.",
            "SCAN: 531 crossover events detected in backtest window.",
            "WALK: Forward testing on 2024-Q1 volatility bucket.",
            "PROMO: Risk-parity gate passed (DD < 15%).",
            "DEPLOY: Listening for live pricing socket..."
        ];
        let i = 0;
        const interval = setInterval(() => {
            setStream(prev => [...prev, messages[i % messages.length]].slice(-10));
            i++;
        }, 3000);
        return () => clearInterval(interval);
    }, [activeRunId]);

    const levels = [
        { id: 0, title: "Operations", icon: Activity, color: "text-primary" },
        { id: 1, title: "Orchestration", icon: Terminal, color: "text-cyan-400" },
        { id: 2, title: "Auth Chain", icon: Key, color: "text-amber-500" },
        { id: 3, title: "Dependency", icon: Database, color: "text-violet-400" }
    ];

    return (
        <div className="h-full w-full bg-[#070B14] flex flex-col overflow-hidden border border-[#1F2937] rounded-2xl shadow-2xl isolate">
            {/* Professional Header */}
            <div className="px-6 py-4 border-b border-[#1F2937] bg-[#0B1220]/50 backdrop-blur-md flex items-center justify-between shrink-0">
                <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg bg-primary/20 flex items-center justify-center border border-primary/30">
                        <Fingerprint className="w-5 h-5 text-primary" />
                    </div>
                    <div>
                        <h2 className="text-sm font-bold text-white uppercase tracking-widest">Glass Box Audit Engine</h2>
                        <p className="text-[10px] text-muted-foreground uppercase tracking-tight font-bold mt-0.5">Immutable Decision Provenance</p>
                    </div>
                </div>
                {activeRunId && (
                    <div className="flex items-center gap-2">
                        <div className="flex -space-x-2">
                            <div className="w-6 h-6 rounded-full border border-[#1F2937] bg-primary/10 flex items-center justify-center backdrop-blur-sm">
                                <ShieldCheck className="w-3 h-3 text-primary" />
                            </div>
                            <div className="w-6 h-6 rounded-full border border-[#1F2937] bg-emerald-500/10 flex items-center justify-center backdrop-blur-sm">
                                <CheckCircle2 className="w-3 h-3 text-emerald-500" />
                            </div>
                        </div>
                        <code className="text-[10px] text-primary/60 font-mono ml-2">ID: {activeRunId.split('-')[0]}</code>
                    </div>
                )}
            </div>

            <div className="flex-1 flex overflow-hidden">
                {/* Side Navigation (Step indicator) */}
                <div className="w-16 border-r border-[#1F2937] bg-[#0B1220]/30 flex flex-col items-center py-6 gap-6 shrink-0">
                    {levels.map((level) => (
                        <button
                            key={level.id}
                            onClick={() => setActiveLevel(level.id)}
                            className={cn(
                                "relative w-10 h-10 rounded-xl flex items-center justify-center transition-all duration-300 group",
                                activeLevel === level.id 
                                    ? "bg-primary text-white shadow-lg shadow-primary/20" 
                                    : "text-muted-foreground hover:bg-white/5 hover:text-foreground"
                            )}
                        >
                            <level.icon className="w-5 h-5" />
                            {activeLevel === level.id && (
                                <div className="absolute left-[-2px] inset-y-2 w-1 bg-primary rounded-r-full" />
                            )}
                            {/* Tooltip */}
                            <div className="absolute left-full ml-4 px-3 py-1.5 rounded-lg bg-[#0B1220] border border-[#1F2937] shadow-2xl text-[10px] font-bold text-white uppercase tracking-widest pointer-events-none opacity-0 group-hover:opacity-100 translate-x-[-10px] group-hover:translate-x-0 transition-all z-50 whitespace-nowrap">
                                {level.title}
                            </div>
                        </button>
                    ))}
                </div>

                {/* Content Area */}
                <div className="flex-1 overflow-y-auto p-8 scrollbar-thin">
                    <div className="max-w-3xl mx-auto space-y-10">
                        {/* Status Grid (Always partially visible at top) */}
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                            <div className="p-4 rounded-xl bg-white/[0.02] border border-[#1F2937] space-y-2">
                                <div className="flex items-center justify-between">
                                    <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest">Integrity</span>
                                    <Activity className={cn("w-3.5 h-3.5", sessionQuality === 'nominal' ? 'text-emerald-500' : 'text-amber-500')} />
                                </div>
                                <p className="text-sm font-bold text-white uppercase">{sessionQuality}</p>
                            </div>
                            <div className="p-4 rounded-xl bg-white/[0.02] border border-[#1F2937] space-y-2">
                                <div className="flex items-center justify-between">
                                    <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest">Active Keys</span>
                                    <Key className="w-3.5 h-3.5 text-amber-500" />
                                </div>
                                <p className="text-sm font-bold text-white">{Object.values(tokens).filter(v => v === 'issued').length} AUTHED</p>
                            </div>
                            <div className="p-4 rounded-xl bg-white/[0.02] border border-[#1F2937] space-y-2">
                                <div className="flex items-center justify-between">
                                    <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest">Queue</span>
                                    <Database className="w-3.5 h-3.5 text-blue-500" />
                                </div>
                                <p className="text-sm font-bold text-white">{pendingSignals.length} SIGNALS</p>
                            </div>
                        </div>

                        {/* Active Level Detail */}
                        <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
                            {activeLevel === 0 && (
                                <div className="space-y-6">
                                    <div className="flex items-center gap-3">
                                        <Activity className="w-5 h-5 text-primary" />
                                        <h3 className="text-lg font-bold text-white">Operational Telemetry</h3>
                                    </div>
                                    <div className="p-6 rounded-2xl border border-primary/20 bg-primary/5 flex items-start gap-4 shadow-[inset_0_0_20px_rgba(59,130,246,0.05)]">
                                        <Info className="w-5 h-5 text-primary shrink-0 mt-0.5" />
                                        <p className="text-xs text-muted-foreground leading-relaxed">
                                            Telemetry is being polled at 10ms intervals. All logical gates within the **Backtest Core** are currently 
                                            returning `Status_Nominal`. Execution speed is mapped to historical OHLCV frequency.
                                        </p>
                                    </div>
                                </div>
                            )}

                            {activeLevel === 1 && (
                                <div className="space-y-4">
                                    <div className="flex items-center gap-3 mb-2">
                                        <Terminal className="w-5 h-5 text-cyan-400" />
                                        <h3 className="text-lg font-bold text-white">Decision Narrative Feed</h3>
                                    </div>
                                    <div className="bg-[#0B1220] border border-[#1F2937] rounded-2xl overflow-hidden shadow-inner">
                                        <div className="px-4 py-2 bg-white/5 border-b border-[#1F2937] flex items-center justify-between">
                                            <span className="text-[9px] font-mono text-muted-foreground uppercase">stdout.log</span>
                                            <div className="flex gap-1.5">
                                                <div className="w-1.5 h-1.5 rounded-full bg-red-500/30" />
                                                <div className="w-1.5 h-1.5 rounded-full bg-amber-500/30" />
                                                <div className="w-1.5 h-1.5 rounded-full bg-emerald-500/30" />
                                            </div>
                                        </div>
                                        <div className="p-6 font-mono text-[11px] h-[300px] overflow-hidden relative">
                                            <div className="space-y-1.5">
                                                {stream.map((msg, i) => (
                                                    <div key={i} className="flex gap-4 animate-in fade-in slide-in-from-left-2 duration-300">
                                                        <span className="text-white/20 select-none">{String(i).padStart(3, '0')}</span>
                                                        <span className={cn(
                                                            msg.startsWith('INIT') ? "text-primary" :
                                                            msg.startsWith('AUTH') ? "text-amber-500" :
                                                            msg.startsWith('PROMO') ? "text-emerald-500" : "text-white/60"
                                                        )}>
                                                            {msg}
                                                        </span>
                                                    </div>
                                                ))}
                                                <div className="flex gap-4 text-primary animate-pulse">
                                                    <span className="text-white/20">008</span>
                                                    <span>_</span>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            )}

                            {activeLevel === 2 && (
                                <div className="space-y-6">
                                    <div className="flex items-center gap-3 mb-2">
                                        <Key className="w-5 h-5 text-amber-500" />
                                        <h3 className="text-lg font-bold text-white">Authorization Chain</h3>
                                    </div>
                                    <div className="grid grid-cols-1 gap-3">
                                        {[
                                            { name: "Backtest", state: tokens.backtest, icon: Search },
                                            { name: "Audit", state: tokens.audit, icon: Fingerprint },
                                            { name: "Promotion", state: tokens.promotion, icon: ShieldCheck }
                                        ].map(tok => (
                                            <div key={tok.name} className="p-4 rounded-xl bg-white/[0.02] border border-[#1F2937] flex items-center justify-between group hover:border-white/20 transition-all">
                                                <div className="flex items-center gap-4">
                                                    <div className={cn(
                                                        "w-10 h-10 rounded-xl flex items-center justify-center border",
                                                        tok.state === 'issued' ? "bg-emerald-500/10 border-emerald-500/20 text-emerald-500" :
                                                        tok.state === 'consumed' ? "bg-white/5 border-white/10 text-muted-foreground opacity-50" :
                                                        "bg-white/5 border-white/10 text-muted-foreground opacity-30"
                                                    )}>
                                                        <tok.icon className="w-5 h-5" />
                                                    </div>
                                                    <div>
                                                        <p className="text-xs font-bold text-white uppercase tracking-widest">{tok.name}_TOKEN</p>
                                                        <p className="text-[10px] text-muted-foreground font-mono mt-0.5">RSA-4096-PSS Signature</p>
                                                    </div>
                                                </div>
                                                <div className={cn(
                                                    "px-3 py-1 rounded-full text-[9px] font-bold uppercase tracking-widest border",
                                                    tok.state === 'issued' ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-500" :
                                                    tok.state === 'consumed' ? "bg-white/5 border-white/10 text-muted-foreground" :
                                                    "bg-white/5 border-white/10 text-muted-foreground"
                                                )}>
                                                    {tok.state}
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {activeLevel === 3 && (
                                <div className="space-y-6">
                                    <div className="flex items-center gap-3 mb-2">
                                        <Database className="w-5 h-5 text-violet-400" />
                                        <h3 className="text-lg font-bold text-white">Dependency Object Dump</h3>
                                    </div>
                                    <div className="bg-[#0B1220] border border-[#1F2937] rounded-2xl p-6 overflow-hidden shadow-inner">
                                        <pre className="text-[11px] font-mono text-cyan-400/70 leading-relaxed overflow-x-auto scrollbar-thin">
                                            {JSON.stringify({
                                                workflow_id: activeRunId,
                                                timestamp: new Date().toISOString(),
                                                mandate_v: "7.0.1_ALPHA",
                                                layers: ["L1_SCHEMA", "L2_SEMANTIC", "L3_TRADING"],
                                                session_quality: sessionQuality,
                                                tokens_summary: tokens
                                            }, null, 2)}
                                        </pre>
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </div>
            
            {/* Action Footer */}
            <div className="p-4 border-t border-[#1F2937] bg-[#0B1220]/50 backdrop-blur-md flex items-center justify-between shrink-0">
                <div className="flex items-center gap-4">
                    <div className="flex items-center gap-2">
                        <Clock className="w-3.5 h-3.5 text-muted-foreground" />
                        <span className="text-[10px] font-mono text-muted-foreground uppercase tracking-widest leading-none">Last Audit: 1.2s Ago</span>
                    </div>
                </div>
                <div className="flex items-center gap-2">
                    <button className="px-3 py-1.5 rounded-lg border border-[#1F2937] text-[11px] font-bold text-white hover:bg-white/5 transition-all">
                        Export Report
                    </button>
                    <button className="px-3 py-1.5 rounded-lg bg-primary text-[11px] font-bold text-white hover:bg-primary/90 transition-all shadow-lg shadow-primary/20">
                        Initiate Manual Deep Trace
                    </button>
                </div>
            </div>
        </div>
    );
}

