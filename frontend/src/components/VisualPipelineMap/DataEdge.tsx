import React from 'react';
import { BaseEdge, EdgeLabelRenderer, type EdgeProps, getSmoothStepPath } from '@xyflow/react';
import { cn } from "@/lib/utils";
import { Zap, Clock, DollarSign, Activity } from "lucide-react";

export function DataEdge({
    id,
    sourceX,
    sourceY,
    targetX,
    targetY,
    sourcePosition,
    targetPosition,
    style = {},
    markerEnd,
    data
}: EdgeProps) {
    const [edgePath, labelX, labelY] = getSmoothStepPath({
        sourceX,
        sourceY,
        sourcePosition,
        targetX,
        targetY,
        targetPosition,
    });

    const payload = data?.payload as Record<string, unknown> | undefined;
    const isActive = !!payload && Object.keys(payload).length > 0;
    
    return (
        <>
            <BaseEdge 
                path={edgePath} 
                markerEnd={markerEnd} 
                style={{
                    ...style,
                    stroke: isActive ? '#FFFFFF' : '#2D333B',
                    strokeWidth: 1,
                    transition: 'stroke 0.3s ease',
                    opacity: isActive ? 0.6 : 0.2
                }} 
            />
            
            {isActive && (
                <EdgeLabelRenderer>
                    <div
                        style={{
                            position: 'absolute',
                            transform: `translate(-50%, -50%) translate(${labelX}px,${labelY}px)`,
                            pointerEvents: 'all',
                        }}
                        className="nodrag nopan"
                    >
                        <div className="bg-[#111418] border border-[#2D333B] px-2 py-1 flex items-center gap-2">
                            {payload.provider_id && (
                                <div className="flex items-center gap-1 border-r border-[#2D333B] pr-2">
                                    <span className="text-[8px] font-bold text-white/40 uppercase tracking-tighter">
                                        {String(payload.provider_id).split('/')[0]}
                                    </span>
                                </div>
                            )}
                            
                            <div className="flex items-center gap-2">
                                {payload.cost !== undefined && (
                                    <div className="flex items-center gap-0.5">
                                        <span className="text-[9px] font-mono text-white/60 font-medium">
                                            ${(payload.cost as number).toFixed(4)}
                                        </span>
                                    </div>
                                )}
                                {payload.latency_ms !== undefined && (
                                    <div className="flex items-center gap-0.5">
                                        <span className="text-[9px] font-mono text-white/40">
                                            {Math.round(payload.latency_ms as number)}ms
                                        </span>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                </EdgeLabelRenderer>
            )}
        </>
    );
}

