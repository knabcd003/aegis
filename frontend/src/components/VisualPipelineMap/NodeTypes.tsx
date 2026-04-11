import React from 'react';
import { Handle, Position } from '@xyflow/react';
import { 
    Zap, Star, Cpu, ShieldCheck, AlertTriangle, 
    Link as LinkIcon, Lock, Activity, Server,
    Layers, Database, FileText, BarChart2
} from "lucide-react";
import { cn } from "@/lib/utils";

export interface PipelineNodeData {
    label: string;
    node_id: string;
    status: "IDLE" | "RUNNING" | "DONE" | "ERROR";
    provider?: "Groq" | "Gemini" | "Local" | "Kimi" | "Claude" | string;
    session_quality?: "nominal" | "degraded" | "severely_degraded";
    last_latency_ms?: number;
    role?: string;
}

const ProviderIcon = ({ provider }: { provider?: string }) => {
    switch (provider?.toLowerCase()) {
        case 'groq': return <Zap className="w-3 h-3 text-orange-400 fill-orange-400" />;
        case 'gemini': return <Star className="w-3 h-3 text-blue-400 fill-blue-400" />;
        case 'local': return <Cpu className="w-3 h-3 text-emerald-400" />;
        case 'claude': return <ShieldCheck className="w-3 h-3 text-purple-400" />;
        default: return <Server className="w-3 h-3 text-gray-500" />;
    }
};

export const PipelineNode = ({ data }: { data: PipelineNodeData }) => {
    const isRunning = data.status === "RUNNING";
    const isDone = data.status === "DONE";
    const isError = data.status === "ERROR";

    return (
        <div className={cn(
            "group relative px-3 py-2 border bg-[#111418] min-w-[160px] transition-colors",
            isRunning ? "border-white/40" : "border-[#2D333B]",
            isDone && "border-emerald-900 bg-emerald-950/20",
            isError && "border-red-900 bg-red-950/20"
        )}>
            <div className="relative flex flex-col gap-1.5">
                <div className="flex items-center justify-between gap-3 border-b border-[#2D333B] pb-1.5">
                    <div className="flex items-center gap-2">
                        <Activity className={cn("w-3 h-3", isRunning ? "text-white" : "text-white/20")} />
                        <span className="text-[11px] font-bold text-white uppercase tracking-tighter">{data.label}</span>
                    </div>
                </div>

                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-1.5">
                        <div className={cn(
                            "w-1 h-1 rounded-full",
                            isRunning ? "bg-white" :
                            isDone ? "bg-emerald-500" :
                            isError ? "bg-red-500" : "bg-[#2D333B]"
                        )} />
                        <span className={cn(
                            "text-[9px] uppercase font-mono font-bold tracking-widest",
                            isRunning ? "text-white" :
                            isDone ? "text-emerald-500/80" :
                            isError ? "text-red-500/80" : "text-white/20"
                        )}>
                            {data.status}
                        </span>
                    </div>
                    {data.last_latency_ms && (
                        <span className="text-[9px] font-mono text-white/30">{data.last_latency_ms}ms</span>
                    )}
                </div>
            </div>

            <Handle type="target" position={Position.Left} className="w-1.5 h-1.5 !bg-[#2D333B] !border-none !rounded-none" />
            <Handle type="source" position={Position.Right} className="w-1.5 h-1.5 !bg-[#2D333B] !border-none !rounded-none" />
        </div>
    );
};

export const TokenNode = ({ data }: any) => {
    const isIssued = data.stage === "issued";
    const isConsumed = data.stage === "consumed";

    return (
        <div className={cn(
            "px-3 py-1.5 border flex items-center gap-2.5 transition-colors",
            isIssued ? "bg-[#1C1F24] border-white/20" :
            isConsumed ? "bg-black/20 border-[#2D333B] opacity-50" :
            "bg-black/10 border-[#2D333B] opacity-30"
        )}>
            <Lock className={cn("w-3 h-3", isIssued ? "text-white" : "text-white/20")} />
            <div className="flex flex-col">
                <span className={cn(
                    "text-[10px] font-bold uppercase tracking-[0.2em] font-mono",
                    isIssued ? "text-white" : "text-white/20"
                )}>
                    {data.token_type}
                </span>
                <span className="text-[8px] text-white/20 uppercase font-bold tracking-tighter">STATE::{data.stage}</span>
            </div>
            <Handle type="target" position={Position.Left} className="!opacity-0" />
            <Handle type="source" position={Position.Right} className="!opacity-0" />
        </div>
    );
};

export const nodeTypes = {
    pipeline: PipelineNode,
    token: TokenNode,
    group: ({ node }: any) => (
        <div className="w-full h-full border border-dashed border-[#2D333B] bg-white/[0.01] pointer-events-none" />
    )
};

