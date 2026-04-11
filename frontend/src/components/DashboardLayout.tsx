import type { ReactNode } from "react";
import { Link, useLocation } from "react-router-dom";
import {
    Activity, Beaker, LineChart, PlusCircle, Settings,
    BarChart3, HeartPulse, Library, GitBranch, MessageSquare,
    Blocks, ChevronDown, DollarSign, Search, Bell, User,
    ChevronRight, Info, ShieldCheck, Globe
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useState, useEffect } from "react";

interface DashboardLayoutProps {
    children: ReactNode;
}

interface NavSection {
    label: string;
    items: { name: string; path: string; icon: any }[];
}

const sections: NavSection[] = [
    {
        label: "Observe",
        items: [
            { name: "Mission Control", path: "/command", icon: Activity },
            { name: "Portfolio Tracker", path: "/portfolio", icon: DollarSign },
            { name: "System Health", path: "/health", icon: HeartPulse },
        ],
    },
    {
        label: "Pipeline",
        items: [
            { name: "Visual Map", path: "/command", icon: Blocks },
            { name: "Component Library", path: "/vcl", icon: Library },
        ],
    },
    {
        label: "Analyze",
        items: [
            { name: "Glass Box", path: "/glassbox", icon: Info },
            { name: "MLOps Arena", path: "/arena", icon: BarChart3 },
            { name: "Debate Theater", path: "/audit", icon: MessageSquare },
            { name: "Budget Dashboard", path: "/budget", icon: DollarSign },
        ],
    },
    {
        label: "Settings",
        items: [
            { name: "Intake Mandate", path: "/intake", icon: PlusCircle },
            { name: "Connectors", path: "/connectors", icon: ShieldCheck },
            { name: "World Monitor", path: "/monitor", icon: Globe },
        ],
    },
];

import { useAegisStore } from "@/lib/store";
import { AuditChatUI } from "./AuditChatUI";

export function DashboardLayout({ children }: DashboardLayoutProps) {
    const location = useLocation();
    const [serverStatus, setServerStatus] = useState<"online" | "offline">("offline");
    const [collapsed, setCollapsed] = useState<Record<string, boolean>>({});
    const [isAuditOpen, setIsAuditOpen] = useState(false);
    
    const active_run_id = useAegisStore(state => state.active_run_id);

    useEffect(() => {
        const check = async () => {
            try {
                const res = await fetch("http://localhost:8000/api/health");
                setServerStatus(res.ok ? "online" : "offline");
            } catch {
                setServerStatus("offline");
            }
        };
        check();
        const interval = setInterval(check, 15_000);
        return () => clearInterval(interval);
    }, []);

    const toggleSection = (label: string) => {
        setCollapsed((prev) => ({ ...prev, [label]: !prev[label] }));
    };

    return (
        <div className="flex h-screen w-screen overflow-hidden bg-[#0C0E11] text-[#E1E1E1] selection:bg-white/10 font-sans">
            {/* Unified Industrial Sidebar */}
            <nav className="w-60 flex flex-col border-r border-[#2D333B] bg-[#111418] shrink-0">
                <div className="px-5 py-6 border-b border-[#2D333B]">
                    <h1 className="text-sm font-bold tracking-tight text-white flex items-center gap-2">
                        <ShieldCheck className="w-4 h-4 text-white" />
                        AEGIS COMMAND
                        <span className="text-[9px] px-1.5 py-0.5 rounded bg-white/5 text-white/50 border border-white/10 uppercase tracking-tighter">V7-F</span>
                    </h1>
                </div>

                <div className="flex-1 overflow-y-auto px-2 py-4 scrollbar-thin">
                    {sections.map((section) => (
                        <div key={section.label} className="mb-6">
                            <div className="px-3 mb-2 text-[10px] font-bold uppercase tracking-[0.15em] text-white/30">
                                {section.label}
                            </div>
                            <ul className="space-y-0.5">
                                {section.items.map((item) => {
                                    const isActive = location.pathname === item.path;
                                    return (
                                        <li key={item.name}>
                                            <Link
                                                to={item.path}
                                                className={cn(
                                                    "flex items-center gap-2.5 px-3 py-1.5 rounded text-[12.5px] font-medium transition-colors",
                                                    isActive
                                                        ? "bg-white/5 text-white border border-white/10"
                                                        : "text-white/50 hover:bg-white/5 hover:text-white"
                                                )}
                                            >
                                                <item.icon className={cn("w-3.5 h-3.5 shrink-0", isActive ? "text-white" : "text-white/30")} />
                                                <span>{item.name}</span>
                                            </Link>
                                        </li>
                                    );
                                })}
                            </ul>
                        </div>
                    ))}
                </div>

                {/* System Stats (Industrial) */}
                <div className="p-4 border-t border-[#2D333B] bg-black/20">
                    <div className="space-y-3">
                        <div className="flex items-center justify-between text-[10px] font-bold uppercase tracking-widest">
                            <span className="text-white/30 text-xs">GATEWAY_OS</span>
                            <div className="flex items-center gap-1.5">
                                <span className={cn(
                                    "w-1 h-1 rounded-full",
                                    serverStatus === "online" ? "bg-emerald-500" : "bg-red-500"
                                )} />
                                <span className={serverStatus === "online" ? "text-emerald-500" : "text-red-400"}>
                                    {serverStatus === "online" ? "LIVE" : "DCR"}
                                </span>
                            </div>
                        </div>
                        <div className="space-y-1">
                            <div className="text-[9px] text-white/20 uppercase font-bold tracking-tighter">Active Session</div>
                            <code className="text-[10px] font-mono text-white/40 block truncate">
                                {active_run_id || "SYS_IDLE_STANDBY"}
                            </code>
                        </div>
                    </div>
                </div>
            </nav>

            {/* Main Operational Body */}
            <div className="flex-1 flex flex-col h-full overflow-hidden bg-[#0C0E11]">
                {/* Secondary Header (Tabs/Breadcrumbs) */}
                <header className="h-10 border-b border-[#2D333B] bg-[#111418]/50 flex items-center justify-between px-6 shrink-0 z-10">
                    <div className="flex items-center gap-2 text-[11px] font-bold text-white/40 uppercase tracking-widest">
                        <span className="hover:text-white cursor-pointer transition-colors">Workspace</span>
                        <ChevronRight className="w-3 h-3 opacity-20" />
                        <span className="text-white tracking-normal lowercase font-mono">
                            /{sections.flatMap(s => s.items).find(i => i.path === location.pathname)?.path.replace('/', '') || "home"}
                        </span>
                    </div>

                    <div className="flex items-center gap-4">
                        <div className="px-3 py-1 rounded bg-white/5 border border-white/10 flex items-center gap-2">
                             <div className="w-1 h-1 rounded-full bg-blue-500" />
                             <span className="text-[9px] font-bold text-white/60 uppercase tracking-widest">Mandate: V7-ALPHA-SWING</span>
                        </div>
                        <button 
                            onClick={() => setIsAuditOpen(true)}
                            className="h-7 flex items-center gap-2 px-3 rounded bg-white/5 border border-white/10 text-[10px] font-bold text-white hover:bg-white/10 transition-all uppercase tracking-widest"
                        >
                            <MessageSquare className="w-3 h-3" />
                            Audit
                        </button>
                    </div>
                </header>

                <main className="flex-1 overflow-auto relative scrollbar-thin">
                    {children}
                </main>
            </div>

            {/* Global Audit Side-Drawer */}
            {isAuditOpen && (
                <div className="fixed inset-y-0 right-0 w-[420px] bg-[#111418] border-l border-[#2D333B] shadow-2xl z-50 flex flex-col animate-in slide-in-from-right duration-200">
                    <div className="px-5 py-4 border-b border-[#2D333B] flex items-center justify-between bg-black/20">
                        <div>
                            <h2 className="text-xs font-bold text-white uppercase tracking-[0.2em]">Audit Inspector</h2>
                            <p className="text-[9px] text-white/30 uppercase font-mono mt-1">Ref: {active_run_id?.slice(0, 16) || "NO_ACTIVE_REF"}</p>
                        </div>
                        <button 
                            onClick={() => setIsAuditOpen(false)}
                            className="p-1 px-2 rounded border border-white/10 text-[10px] text-white/50 hover:text-white hover:bg-white/5 transition-all font-bold uppercase"
                        >
                            Close
                        </button>
                    </div>
                    <div className="flex-1 overflow-hidden">
                        <AuditChatUI runId={active_run_id || ""} />
                    </div>
                </div>
            )}
        </div>
    );
}

