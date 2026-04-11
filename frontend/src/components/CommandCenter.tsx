import React from 'react';
import { Network, Activity, ShieldAlert, Zap, Terminal, ChevronRight, Share2, Download } from 'lucide-react';
import { VisualPipelineMap } from './VisualPipelineMap/VisualPipelineMap';
import { useAegisStore } from '@/lib/store';
import { cn } from "@/lib/utils";

export function CommandCenter() {
    const activeRun = useAegisStore(state => state.active_run_id);
    const sessionQuality = useAegisStore(state => state.session_quality);

    return (
        <div className="flex flex-col h-full overflow-hidden bg-[#0C0E11]">
            <div className="flex-1 flex flex-col p-4 gap-4 overflow-hidden">
                <header className="flex items-end justify-between shrink-0 border-b border-[#2D333B] pb-4">
                    <div className="space-y-1">
                        <div className="flex items-center gap-2 text-[10px] font-bold text-white/40 uppercase tracking-[0.2em]">
                            <Zap className="w-3.5 h-3.5" />
                            ROOT_TOPOLOGY_V7
                        </div>
                        <h1 className="text-xl font-bold tracking-tight text-white uppercase">Pipeline Command Center</h1>
                    </div>
                    
                    <div className="flex gap-2">
                        <div className="flex items-center gap-2 px-3 py-1.5 rounded bg-[#111418] border border-[#2D333B]">
                             <ShieldAlert className={cn(
                                "w-3 h-3",
                                sessionQuality === "nominal" ? "text-emerald-500" : "text-amber-500"
                            )} />
                            <span className="text-[10px] font-bold text-white/60 uppercase tracking-widest">MESH_QLTY: {sessionQuality}</span>
                        </div>
                        <button className="h-8 px-3 rounded bg-white/5 border border-white/10 text-[10px] font-bold text-white hover:bg-white/10 transition-all uppercase tracking-widest flex items-center gap-2">
                            <Terminal className="w-3 h-3" />
                            TTY_SYSTEM
                        </button>
                    </div>
                </header>

                <div className="flex items-center justify-between px-2 text-[10px] font-bold text-white/30 uppercase tracking-widest">
                    <div className="flex items-center gap-4">
                         <div className="flex items-center gap-1.5">
                            <div className="w-1 h-1 rounded-full bg-emerald-500" />
                            SIGNAL_MESH: ACTIVE
                         </div>
                         <div className="flex items-center gap-1.5">
                            <div className="w-1 h-1 rounded-full bg-blue-500" />
                            ORCHESTRATOR: {activeRun?.slice(0, 8) || "IDLE"}
                         </div>
                    </div>
                    <div className="flex items-center gap-3">
                        <Share2 className="w-3 h-3 cursor-pointer hover:text-white transition-colors" />
                        <Download className="w-3 h-3 cursor-pointer hover:text-white transition-colors" />
                    </div>
                </div>

                {/* The main event — The Glass Box Topology */}
                <div className="flex-1 w-full min-h-0 bg-[#111418] border border-[#2D333B] relative group overflow-hidden isolate">
                    <VisualPipelineMap />
                    
                    {/* Industrial Info Stats (Top Right) */}
                    <div className="absolute top-4 right-4 p-3 border border-[#2D333B] bg-black/60 backdrop-blur-sm z-10 pointer-events-none">
                        <div className="space-y-2">
                            <div className="flex items-center justify-between gap-8">
                                <span className="text-[9px] font-bold text-white/30 uppercase">Latent Bound</span>
                                <span className="text-[9px] font-mono text-emerald-500">8.2ms</span>
                            </div>
                            <div className="flex items-center justify-between gap-8">
                                <span className="text-[9px] font-bold text-white/30 uppercase">Cipher state</span>
                                <span className="text-[9px] font-mono text-white/60 uppercase">AES-GCM-256</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}

