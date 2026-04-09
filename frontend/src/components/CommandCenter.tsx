import React from 'react';
import { Network, Activity } from 'lucide-react';
import { VisualPipelineMap } from './VisualPipelineMap/VisualPipelineMap';
import { useAegisStore } from '@/lib/store';

export function CommandCenter() {
    const activeRun = useAegisStore(state => state.active_run_id);

    return (
        <div className="flex flex-col h-full overflow-hidden p-6 gap-6">
            <div className="flex items-center justify-between shrink-0">
                <div>
                    <h1 className="text-2xl font-semibold tracking-tight flex items-center gap-2.5">
                        <Activity className="w-6 h-6 text-accent" />
                        Command Center
                    </h1>
                    <p className="text-sm text-muted-foreground mt-1">
                        {activeRun 
                            ? `Monitoring Pipeline Execution: ${activeRun}`
                            : "Waiting for mandate. Head to INTAKE to deploy an autonomous runner."}
                    </p>
                </div>
            </div>

            {/* The main event — The Glass Box Topology */}
            <div className="flex-1 w-full min-h-0 bg-[#0d0d12] rounded-xl border border-border/60 shadow-xl overflow-hidden relative">
                <VisualPipelineMap />
            </div>
        </div>
    );
}
