import React, { useMemo } from 'react';
import { ReactFlow, Background, Controls, type Node, type Edge } from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { nodeTypes, type PipelineNodeData } from './NodeTypes';
import { DataEdge } from './DataEdge';
import { useAegisStore } from '@/lib/store';

const edgeTypes = {
    data: DataEdge
};

// We do NOT wire useAegisStore here yet per Step 6 constraint. All nodes are static IDLE.

const initialNodes: Node[] = [
    { id: "intake",          type: "pipeline", position: {x: 50,   y: 200}, data: {label: "Intake",          status: "IDLE"} as PipelineNodeData },
    { id: "supervisor",      type: "pipeline", position: {x: 270,  y: 200}, data: {label: "Supervisor",      status: "IDLE"} as PipelineNodeData },
    { id: "builder",         type: "pipeline", position: {x: 490,  y: 200}, data: {label: "Builder",         status: "IDLE"} as PipelineNodeData },
    { id: "schema_validator",type: "pipeline", position: {x: 710,  y: 200}, data: {label: "Schema Validator",status: "IDLE"} as PipelineNodeData },
    
    // Backtesting branches
    { id: "backtest_quick",  type: "pipeline", position: {x: 930,  y: 100}, data: {label: "Quick Backtest",  status: "IDLE"} as PipelineNodeData },
    { id: "backtest_full",   type: "pipeline", position: {x: 930,  y: 300}, data: {label: "Full Backtest",   status: "IDLE"} as PipelineNodeData },
    
    // Tokens
    { id: "token_backtest",  type: "token",    position: {x: 1100, y: 390}, data: {token_type: "backtest", stage: "unissued"} },
    
    // FinDebate group container (React Flow parent)
    { 
        id: "findebate_group", 
        type: "group", 
        position: {x: 1180, y: 80}, 
        style: { width: 500, height: 350, backgroundColor: 'rgba(255, 255, 255, 0.02)', border: '1px dashed #333', borderRadius: '10px' },
        data: { label: null }
    },
    
    // Debate Children (Relative to parent position x:1180, y:80)
    { id: "findebate",       type: "pipeline", position: {x: 20, y: 20}, data: {label: "FinDebate Orch",  status: "IDLE"}, parentId: "findebate_group", extent: 'parent' },
    { id: "debate_bull",     type: "pipeline", position: {x: 20, y: 120}, data: {label: "Bull Agent",      status: "IDLE"}, parentId: "findebate_group", extent: 'parent' },
    { id: "debate_bear",     type: "pipeline", position: {x: 270, y: 120}, data: {label: "Bear Agent",      status: "IDLE"}, parentId: "findebate_group", extent: 'parent' },
    { id: "debate_moderator",type: "pipeline", position: {x: 145, y: 240}, data: {label: "Moderator",       status: "IDLE"}, parentId: "findebate_group", extent: 'parent' },
    
    { id: "token_audit",     type: "token",    position: {x: 1530, y: 470}, data: {token_type: "audit",    stage: "unissued"} },
    
    { id: "scenario_battery",type: "pipeline", position: {x: 1730, y: 320}, data: {label: "Scenario Battery",status: "IDLE"} },
    { id: "promotion_gate",  type: "pipeline", position: {x: 1950, y: 320}, data: {label: "Promotion Gate",  status: "IDLE"} },
    
    { id: "token_promotion", type: "token",    position: {x: 2160, y: 290}, data: {token_type: "promotion",stage: "unissued"} },
    
    { id: "sentinel_deploy", type: "pipeline", position: {x: 2170, y: 200}, data: {label: "Sentinel Deploy", status: "IDLE"} },
    { id: "signal_card",     type: "pipeline", position: {x: 2390, y: 200}, data: {label: "Signal Card",     status: "IDLE"} }
];

const initialEdges: Edge[] = [
    { id: 'e-intake-sup', source: 'intake', target: 'supervisor', type: 'smoothstep' },
    { id: 'e-sup-build', source: 'supervisor', target: 'builder', type: 'smoothstep' },
    { id: 'e-build-val', source: 'builder', target: 'schema_validator', type: 'smoothstep' },
    
    // Splits to branches
    { id: 'e-val-btq', source: 'schema_validator', target: 'backtest_quick', type: 'smoothstep' },
    { id: 'e-val-btf', source: 'schema_validator', target: 'backtest_full', type: 'smoothstep' },
    
    // BTF issues token (visual token link)
    { id: 'e-btf-tokbt', source: 'backtest_full', target: 'token_backtest', type: 'straight', animated: true, style: { strokeDasharray: '5, 5'} },
    
    // Flow into FinDebate
    { id: 'e-btf-findebate', source: 'backtest_full', target: 'findebate', type: 'smoothstep' },
    { id: 'e-findebate-bull', source: 'findebate', target: 'debate_bull', type: 'smoothstep' },
    { id: 'e-findebate-bear', source: 'findebate', target: 'debate_bear', type: 'smoothstep' },
    { id: 'e-bull-mod', source: 'debate_bull', target: 'debate_moderator', type: 'smoothstep' },
    { id: 'e-bear-mod', source: 'debate_bear', target: 'debate_moderator', type: 'smoothstep' },
    
    // Moderator issues token
    { id: 'e-mod-tokaud', source: 'debate_moderator', target: 'token_audit', type: 'straight', animated: true, style: { strokeDasharray: '5, 5'} },
    
    { id: 'e-mod-scenario', source: 'debate_moderator', target: 'scenario_battery', type: 'smoothstep' },
    { id: 'e-scenario-promo', source: 'scenario_battery', target: 'promotion_gate', type: 'smoothstep' },
    
    // Promo issues token
    { id: 'e-promo-tokpro', source: 'promotion_gate', target: 'token_promotion', type: 'straight', animated: true, style: { strokeDasharray: '5, 5'} },
    
    { id: 'e-promo-sentinel', source: 'promotion_gate', target: 'sentinel_deploy', type: 'smoothstep' },
    { id: 'e-sentinel-signal', source: 'sentinel_deploy', target: 'signal_card', type: 'smoothstep' },
];

export function VisualPipelineMap() {
    const nodeStatuses = useAegisStore(state => state.node_statuses);
    const tokenStates = useAegisStore(state => state.tokens);
    const edgePayloads = useAegisStore(state => state.edge_payloads);

    const nodes = useMemo(() => {
        return initialNodes.map(node => {
            if (node.type === "group") {
                return {
                    ...node,
                    style: { 
                        width: node.style?.width, 
                        height: node.style?.height, 
                        backgroundColor: 'rgba(255, 255, 255, 0.01)', 
                        border: '1px solid #2D333B',
                        borderRadius: '0px'
                    }
                };
            }
            if (node.type === "token") {
                return {
                    ...node,
                    data: {
                        ...node.data,
                        stage: tokenStates[(node.data as any).token_type] ?? "unissued",
                    }
                };
            } else if (node.type === "pipeline") {
                return {
                    ...node,
                    data: {
                        ...node.data,
                        status: nodeStatuses[node.id] ?? "IDLE",
                    }
                };
            }
            return node;
        });
    }, [nodeStatuses, tokenStates]);

    const edges = useMemo(() => {
        return initialEdges.map(edge => {
            const dynamicEdge = {
                ...edge,
                type: edge.type === 'smoothstep' ? 'data' : edge.type,
                data: {
                    ...edge.data,
                    payload: edgePayloads[edge.source]
                }
            };
            return dynamicEdge;
        });
    }, [edgePayloads]);

    return (
        <div className="w-full h-full bg-[#0C0E11] overflow-hidden relative group isolate">
            <ReactFlow 
                nodes={nodes}
                edges={edges}
                nodeTypes={nodeTypes}
                edgeTypes={edgeTypes}
                fitView
                fitViewOptions={{ padding: 0.1 }}
                className="bg-transparent"
                proOptions={{ hideAttribution: true }}
                minZoom={0.2}
                maxZoom={1.5}
            >
                <Background 
                    color="#2D333B" 
                    gap={20} 
                    size={0.5} 
                    variant={BackgroundVariant.Dots}
                    className="opacity-10"
                />
                <Controls 
                    className="!bg-[#111418] !border-[#2D333B] !rounded !shadow-none !p-0.5 !flex !flex-row group"
                    showInteractive={false}
                />
            </ReactFlow>
        </div>
    );
}

import { BackgroundVariant } from '@xyflow/react';

