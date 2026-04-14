import React from 'react';
import { 
    Activity, ShieldAlert, Zap, Terminal, ChevronRight, Share2, 
    Download, Bell, User, Search as SearchIcon, HeartPulse, 
    MessageSquare, Info, Target, TrendingUp, AlertTriangle, 
    Cpu, Globe
} from 'lucide-react';
import { VisualPipelineMap } from './VisualPipelineMap/VisualPipelineMap';
import { useAegisStore } from '@/lib/store';
import { cn } from "@/lib/utils";

export function CommandCenter() {
    const activeRun = useAegisStore(state => state.active_run_id);
    const sessionQuality = useAegisStore(state => state.session_quality);

    const signals = [
        {
            pair: "BTC/USDT",
            direction: "Strong Buy",
            reason: "V-Shape Recovery detected on 15m timeframe",
            confidence: "94.2%",
            entry: "$64,210 - $64,350",
            target: "$67,800.00",
            stop: "$63,100.00",
            type: "buy"
        },
        {
            pair: "SOL/USDT",
            direction: "Strong Sell",
            reason: "Resistance break failure at psychological barrier",
            confidence: "88.7%",
            entry: "$142.10 - $143.00",
            target: "$128.50.00",
            stop: "$148.00.00",
            type: "sell"
        }
    ];

    const sentinels = [
        { name: "Sentinel Alpha", strategy: "Scalping Strategy", performance: "+4.2%", status: "Active", icon: Zap, color: "text-secondary" },
        { name: "Sentinel Beta", strategy: "Trend Following", performance: "+1.8%", status: "Active", icon: ShieldCheck, color: "text-primary" },
    ];

    return (
        <div className="p-8 space-y-8 max-w-screen-2xl mx-auto">
            {/* Hero Summary (Editorial Style) */}
            <section className="grid grid-cols-1 md:grid-cols-12 gap-8">
                <div className="md:col-span-8">
                    <p className="text-xs tracking-[0.3em] uppercase text-on-surface-variant font-medium mb-3">System Integrity Status</p>
                    <h3 className="font-headline text-5xl font-light leading-tight text-on-surface max-w-2xl">
                        Aegis AI has identified <span className="italic text-primary underline decoration-primary/30 underline-offset-8">three high-probability</span> vector shifts in the last 14 minutes.
                    </h3>
                </div>
                <div className="md:col-span-4 flex flex-col justify-end">
                    <div className="bg-surface-container-low p-6 rounded-lg border border-white/5 space-y-4">
                        <div className="flex justify-between items-center">
                            <span className="text-[0.6875rem] text-on-surface-variant uppercase tracking-widest font-bold">Active Sentinels</span>
                            <span className="text-secondary text-[10px] uppercase font-bold flex items-center gap-1.5">
                                <span className="w-1.5 h-1.5 rounded-full bg-secondary animate-pulse"></span> Nominal
                            </span>
                        </div>
                        <div className="flex items-baseline gap-2">
                            <span className="text-3xl font-headline text-on-surface">12 / 12</span>
                            <span className="text-[10px] text-muted-foreground uppercase font-bold tracking-widest">Nodes Online</span>
                        </div>
                        <div className="w-full bg-surface-container-highest h-1 rounded-full overflow-hidden">
                            <div className="bg-primary w-full h-full"></div>
                        </div>
                    </div>
                </div>
            </section>

            {/* Bento Grid Layout */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
                {/* Main Feed: Live Signal Feed */}
                <div className="lg:col-span-8 space-y-6">
                    <div className="flex justify-between items-end border-b border-white/5 pb-4">
                        <h4 className="font-headline text-xl text-on-surface">Live Signal Feed</h4>
                        <span className="text-[0.6875rem] text-muted-foreground uppercase tracking-widest font-bold">Auto-Refresh: 2s</span>
                    </div>

                    <div className="space-y-4">
                        {signals.map((sig, idx) => (
                            <div key={idx} className={cn(
                                "bg-surface-container p-6 rounded-lg border-l-4 transition-all hover:bg-surface-container-high",
                                sig.type === 'buy' ? "border-primary" : "border-tertiary"
                            )}>
                                <div className="flex items-start justify-between">
                                    <div className="flex gap-4">
                                        <div className={cn(
                                            "w-12 h-12 rounded-lg bg-surface-container-highest flex items-center justify-center font-bold border border-white/5",
                                            sig.type === 'buy' ? "text-primary" : "text-tertiary"
                                        )}>
                                            {sig.pair.split('/')[0]}
                                        </div>
                                        <div>
                                            <div className="flex items-center gap-2">
                                                <span className="font-bold text-on-surface">{sig.pair}</span>
                                                <span className={cn(
                                                    "px-1.5 py-0.5 rounded-sm text-[0.625rem] font-bold uppercase",
                                                    sig.type === 'buy' ? "bg-secondary-container text-on-secondary-container" : "bg-tertiary-container text-on-tertiary-container"
                                                )}>
                                                    {sig.direction}
                                                </span>
                                            </div>
                                            <p className="text-xs text-muted-foreground mt-1 italic">{sig.reason}</p>
                                        </div>
                                    </div>
                                    <div className="text-right">
                                        <div className="text-[0.6875rem] text-on-surface-variant uppercase tracking-widest font-bold">Confidence</div>
                                        <div className={cn(
                                            "text-xl font-headline",
                                            sig.type === 'buy' ? "text-secondary" : "text-tertiary"
                                        )}>{sig.confidence}</div>
                                    </div>
                                </div>

                                <div className="grid grid-cols-3 gap-6 mt-6 py-4 border-y border-white/5">
                                    <div>
                                        <p className="text-[0.625rem] uppercase text-on-surface-variant tracking-widest mb-1 font-bold">Entry Range</p>
                                        <p className="text-sm font-medium font-mono">{sig.entry}</p>
                                    </div>
                                    <div>
                                        <p className="text-[0.625rem] uppercase text-on-surface-variant tracking-widest mb-1 font-bold">Target Price</p>
                                        <p className="text-sm font-medium text-secondary font-mono">{sig.target}</p>
                                    </div>
                                    <div>
                                        <p className="text-[0.625rem] uppercase text-on-surface-variant tracking-widest mb-1 font-bold">Stop Loss</p>
                                        <p className="text-sm font-medium text-tertiary font-mono">{sig.stop}</p>
                                    </div>
                                </div>

                                <div className="flex justify-end gap-3 mt-4">
                                    <button className="px-6 py-2 text-[10px] font-bold text-on-surface-variant hover:text-on-surface border border-white/10 hover:border-white/20 transition-all rounded-lg uppercase tracking-widest">Decline</button>
                                    <button className="px-8 py-2 text-[10px] font-bold bg-primary-container text-on-primary-container rounded-lg uppercase tracking-widest shadow-lg hover:scale-[1.02] active:scale-95 transition-all">Accept Signal</button>
                                </div>
                            </div>
                        ))}
                    </div>

                    {/* Integrated Topology View */}
                    <div className="pt-8 space-y-4">
                         <div className="flex justify-between items-end">
                            <h4 className="font-headline text-xl text-on-surface">Topology Engine</h4>
                            <span className="text-[0.6875rem] text-muted-foreground uppercase tracking-widest font-bold">Mesh Ref: V7.02B</span>
                        </div>
                        <div className="h-[400px] w-full bg-surface-container rounded-lg border border-white/5 overflow-hidden isolate relative">
                            <VisualPipelineMap />
                        </div>
                    </div>
                </div>

                {/* Side Panels */}
                <div className="lg:col-span-4 space-y-8">
                    {/* Deployed Sentinels */}
                    <section className="space-y-4">
                        <h4 className="font-headline text-lg text-on-surface">Active Sentinels</h4>
                        <div className="bg-surface-container-low rounded-lg overflow-hidden border border-white/5 divide-y divide-white/5">
                            {sentinels.map((s, idx) => (
                                <div key={idx} className="p-4 flex items-center justify-between hover:bg-white/[0.02] transition-colors">
                                    <div className="flex items-center gap-3">
                                        <div className="w-8 h-8 rounded bg-surface-container-highest flex items-center justify-center">
                                            <s.icon className={cn("w-4 h-4", s.color)} />
                                        </div>
                                        <div>
                                            <p className="text-[0.8125rem] font-medium text-on-surface">{s.name}</p>
                                            <p className="text-[0.625rem] text-muted-foreground uppercase font-bold">{s.strategy}</p>
                                        </div>
                                    </div>
                                    <div className="text-right">
                                        <p className="text-xs text-secondary font-bold font-mono">{s.performance}</p>
                                        <p className="text-[0.625rem] text-muted-foreground uppercase font-bold tracking-tighter">{s.status}</p>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </section>

                    {/* Execution Logs */}
                    <section className="space-y-4">
                        <div className="flex justify-between items-center">
                            <h4 className="font-headline text-lg text-on-surface">Execution Logs</h4>
                            <span className="text-[0.625rem] text-primary uppercase tracking-widest font-bold flex items-center gap-1.5 animate-pulse">
                                <span className="w-1.5 h-1.5 rounded-full bg-primary" />
                                Live
                            </span>
                        </div>
                        <div className="bg-surface-container-low font-mono text-[0.6875rem] p-4 rounded-lg border border-white/5 h-64 overflow-y-auto space-y-2 scrollbar-thin">
                            <div className="text-muted-foreground"><span className="text-secondary">[12:44:02]</span> SYSTEM: Initiating node handshake protocol...</div>
                            <div className="text-muted-foreground"><span className="text-secondary">[12:44:15]</span> ALPHA: Market anomaly detected (BTC/USDT)</div>
                            <div className="text-muted-foreground"><span className="text-secondary">[12:44:18]</span> AI: Confidence threshold passed (0.94)</div>
                            <div className="text-primary font-bold">[12:44:21] CORE: Signal broadcasted to control center</div>
                            <div className="text-muted-foreground"><span className="text-secondary">[12:45:00]</span> BETA: Awaiting user confirmation for node entry</div>
                            <div className="text-muted-foreground animate-pulse"><span className="text-primary">[12:45:12]</span> MONITOR: Processing ticker SOL/USDT...</div>
                            <div className="text-red-500/80 uppercase font-bold text-[9px]">[12:45:30] ERR: Connection timeout on node AP-SOUTH-1 (Retrying)</div>
                        </div>
                    </section>
                </div>
            </div>
        </div>
    );
}

const ShieldCheck = (props: any) => (
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}>
        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10" />
        <path d="m9 12 2 2 4-4" />
    </svg>
);
