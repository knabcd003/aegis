import React from 'react';
import { Activity, ShieldAlert, Zap, Terminal, ChevronRight, Share2, Download, Bell, User, Search as SearchIcon, HeartPulse, MessageSquare, Info, Target, TrendingUp, AlertTriangle, Cpu, Globe, Blocks } from 'lucide-react';
import { VisualPipelineMap } from './VisualPipelineMap/VisualPipelineMap';
import { useAegisStore } from '@/lib/store';
import { cn } from "@/lib/utils";
import { Link } from 'react-router-dom';

export function CommandCenter() {
    const activeRun = useAegisStore(state => state.active_run_id);
    const sessionQuality = useAegisStore(state => state.session_quality);

    // If there is no active run and no data, show an empty state to guide the user journey
    if (!activeRun) {
        return (
            <div className="p-8 h-full flex flex-col items-center justify-center space-y-6 max-w-lg mx-auto text-center">
                <div className="w-16 h-16 rounded-2xl bg-surface-container-high border border-white/5 flex items-center justify-center mb-2 shadow-sm">
                    <Blocks className="w-8 h-8 text-muted-foreground" />
                </div>
                <h2 className="font-headline text-3xl text-on-surface">No Active Pipeline</h2>
                <p className="text-[0.8125rem] text-muted-foreground leading-relaxed">
                    Aegis AI is standing by. Your providers and price feeds are configured, but no strategy is currently deployed.
                </p>
                <Link to="/intake" className="mt-4 px-6 py-3 bg-primary-container text-on-primary-container font-bold text-[0.8125rem] uppercase tracking-widest rounded-lg hover:opacity-90 transition-opacity">
                    Deploy a Strategy
                </Link>
            </div>
        );
    }

    return (
        <div className="p-8 space-y-8 max-w-screen-2xl mx-auto">
            {/* Real data will go here once the pipeline is active */}
            <div className="bg-surface-container p-6 border border-white/5 rounded-xl text-center text-muted-foreground text-[0.8125rem]">
                Pipeline active. Waiting for signals...
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
