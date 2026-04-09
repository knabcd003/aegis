import React from 'react';
import { ReactFlow, Background, Controls, Node, Edge } from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { nodeTypes, PipelineNodeData } from './NodeTypes';

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
    
    // Debate Children (absolute relative to parent = false in this array context unless specified, so absolute global is fine)
    { id: "findebate",       type: "pipeline", position: {x: 1200, y: 100}, data: {label: "FinDebate Orch",  status: "IDLE"}, parentId: "findebate_group", extent: 'parent' },
    { id: "debate_bull",     type: "pipeline", position: {x: 1200, y: 200}, data: {label: "Bull Agent",      status: "IDLE"}, parentId: "findebate_group", extent: 'parent' },
    { id: "debate_bear",     type: "pipeline", position: {x: 1450, y: 200}, data: {label: "Bear Agent",      status: "IDLE"}, parentId: "findebate_group", extent: 'parent' },
    { id: "debate_moderator",type: "pipeline", position: {x: 1325, y: 320}, data: {label: "Moderator",       status: "IDLE"}, parentId: "findebate_group", extent: 'parent' },
    
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
    return (
        <div className="w-full h-full bg-[#0d0d12] rounded-lg border border-border overflow-hidden">
            <ReactFlow 
                nodes={initialNodes}
                edges={initialEdges}
                nodeTypes={nodeTypes}
                fitView
                className="bg-[#050508]"
                proOptions={{ hideAttribution: true }}
            >
                <Background color="#1a1a24" gap={16} />
                <Controls className="!bg-[#1a1a24] !border-border !fill-white" />
            </ReactFlow>
        </div>
    );
}
