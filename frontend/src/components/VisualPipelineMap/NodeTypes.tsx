import React from 'react';
import { Handle, Position } from '@xyflow/react';

export interface PipelineNodeData {
    label: string;
    node_id: string;
    status: "IDLE" | "RUNNING" | "DONE" | "ERROR";
    provider?: string;
    session_quality?: string;
    last_latency_ms?: number;
}

export const PipelineNode = ({ data }: { data: PipelineNodeData }) => {
    let bg = "bg-[#1a1a24]";
    let border = "border-border";
    let textStatus = "text-gray-500";

    if (data.status === "RUNNING") {
        bg = "bg-blue-500/10";
        border = "border-blue-500/50 shadow-[0_0_15px_rgba(59,130,246,0.5)] animate-pulse";
        textStatus = "text-blue-400";
    }
    if (data.status === "DONE") {
        bg = "bg-green-500/10";
        border = "border-green-500/50";
        textStatus = "text-green-400";
    }
    if (data.status === "ERROR") {
        bg = "bg-red-500/10";
        border = "border-red-500/50";
        textStatus = "text-red-400";
    }

    return (
        <div className={`px-4 py-3 rounded-md border-2 w-48 ${bg} ${border} flex flex-col font-mono`}>
            <div className="font-bold text-sm text-white">{data.label}</div>
            <div className={`text-xs font-semibold ${textStatus}`}>{data.status}</div>
            {data.provider && <div className="text-[10px] text-gray-400 mt-1 uppercase tracking-wider">{data.provider}</div>}

            <Handle type="target" position={Position.Top} className="w-2 h-2 !bg-gray-500 border-none" />
            <Handle type="source" position={Position.Bottom} className="w-2 h-2 !bg-gray-500 border-none" />
        </div>
    );
};

export const TokenNode = ({ data }: any) => {
    return (
        <div className="px-3 py-1 bg-yellow-500/10 border-2 border-yellow-600/50 text-yellow-400 text-xs rounded-full shadow-lg font-mono flex gap-2 items-center w-max">
            <span className="uppercase font-bold tracking-wider">{data.token_type}</span>
            <span className="text-[10px] opacity-70">[{data.stage}]</span>
            <Handle type="target" position={Position.Top} className="!opacity-0" />
            <Handle type="source" position={Position.Bottom} className="!opacity-0" />
        </div>
    );
};

export const ModelNode = ({ data }: any) => (
    <div className="px-2 py-1 bg-purple-500/10 border border-purple-500/50 text-purple-400 text-[10px] rounded" />
);

export const DataNode = ({ data }: any) => (
    <div className="px-2 py-1 bg-cyan-500/10 border border-cyan-500/50 text-cyan-400 text-[10px] rounded" />
);

export const nodeTypes = {
    pipeline: PipelineNode,
    token: TokenNode,
    model: ModelNode,
    data: DataNode
};
