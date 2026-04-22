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
        label: "Build",
        items: [
            { name: "Intake Mandate", path: "/intake", icon: PlusCircle },
        ],
    },
    {
        label: "Observe",
        items: [
            { name: "Mission Control", path: "/command", icon: Activity },
            { name: "MLOps Arena", path: "/arena", icon: BarChart3 },
            { name: "Debate Theater", path: "/audit", icon: MessageSquare },
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
        <div className="flex h-screen w-screen overflow-hidden bg-surface text-on-surface selection:bg-primary-container selection:text-on-primary-container font-body">
            {/* Editorial Sidebar */}
            <aside className="w-64 flex flex-col border-r border-white/5 bg-surface shrink-0 z-50">
                <div className="px-6 py-8">
                    <h1 className="font-headline text-2xl font-light text-[#E5E2DE]">Aegis AI</h1>
                    <p className="text-[0.6875rem] uppercase tracking-[0.2em] text-muted-foreground mt-1 font-medium">Intelligence Core v2.4</p>
                </div>

                <nav className="flex-1 overflow-y-auto space-y-1">
                    {sections.map((section) => (
                        <div key={section.label} className="mb-4">
                            <ul className="space-y-1">
                                {section.items.map((item) => {
                                    const isActive = location.pathname === item.path;
                                    return (
                                        <li key={item.name}>
                                            <Link
                                                to={item.path}
                                                className={cn(
                                                    "flex items-center gap-3 px-4 py-3 transition-all duration-200 group relative",
                                                    isActive
                                                        ? "bg-[#1c1c1b] text-primary border-r-2 border-primary-container rounded-none"
                                                        : "text-muted-foreground hover:text-[#E5E2DE] hover:bg-[#1a1a19]"
                                                )}
                                            >
                                                <item.icon className={cn("w-5 h-5 transition-transform group-hover:scale-110", isActive ? "text-primary" : "text-muted-foreground")} />
                                                <span className="text-[0.8125rem] font-normal tracking-wide">{item.name}</span>
                                            </Link>
                                        </li>
                                    );
                                })}
                            </ul>
                        </div>
                    ))}
                </nav>

                <div className="px-4 mb-4">
                    <button className="w-full bg-primary-container text-on-primary-container py-2.5 rounded-lg text-[0.8125rem] font-medium flex items-center justify-center gap-2 transition-transform active:scale-95 shadow-lg">
                        <PlusCircle className="w-4 h-4" />
                        Deploy New Node
                    </button>
                </div>

                <div className="mt-auto border-t border-white/5 pt-4">
                    <Link to="/docs" className="flex items-center gap-3 px-4 py-2 text-muted-foreground hover:text-[#E5E2DE] text-[0.8125rem]">
                        <Library className="w-4 h-4" />
                        Documentation
                    </Link>
                    <Link to="/settings" className="flex items-center gap-3 px-4 py-2 text-muted-foreground hover:text-[#E5E2DE] text-[0.8125rem]">
                        <Settings className="w-4 h-4" />
                        Settings
                    </Link>
                </div>
            </aside>

            {/* Main Content Area */}
            <div className="flex-1 flex flex-col h-full overflow-hidden bg-surface">
                {/* Top Bar (Glassmorphism) */}
                <header className="flex justify-between items-center w-full px-8 sticky top-0 z-40 glass-panel h-16 shadow-[0_1px_0_0_rgba(255,255,255,0.05)]">
                    <div className="flex items-center gap-8">
                        <h2 className="font-headline text-xl font-semibold italic text-[#E5E2DE]">
                            {sections.flatMap(s => s.items).find(i => i.path === location.pathname)?.name || "Mission Control"}
                        </h2>
                        <div className="hidden md:flex gap-6">
                            <span className="text-primary font-medium border-b-2 border-primary-container pb-1 text-[0.8125rem] cursor-default whitespace-nowrap">Live Overview</span>
                            <span className="text-muted-foreground font-normal hover:text-[#E5E2DE] text-[0.8125rem] cursor-pointer transition-colors whitespace-nowrap">Historical Logs</span>
                        </div>
                    </div>

                    <div className="flex items-center gap-4">
                        <div className="relative">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground w-4 h-4" />
                            <input 
                                className="bg-surface-container-low border-none rounded-lg pl-9 pr-4 py-1.5 text-[0.8125rem] text-on-surface placeholder:text-muted-foreground w-64 focus:ring-1 focus:ring-primary-container transition-all" 
                                placeholder="Search instruments..." 
                                type="text"
                            />
                        </div>
                        <div className="flex items-center gap-2 ml-4">
                            <button className="p-2 hover:bg-[#1a1a19] rounded-full transition-colors text-muted-foreground hover:text-[#E5E2DE]">
                                <HeartPulse className="w-5 h-5" />
                            </button>
                            <button className="p-2 hover:bg-[#1a1a19] rounded-full transition-colors text-muted-foreground hover:text-[#E5E2DE] relative">
                                <Bell className="w-5 h-5" />
                                <span className="absolute top-2.5 right-2.5 w-2 h-2 bg-primary rounded-full border-2 border-surface"></span>
                            </button>
                            <div className="w-8 h-8 rounded-full bg-surface-container-highest flex items-center justify-center ml-2 border border-white/5">
                                <User className="w-5 h-5 text-on-surface-variant" />
                            </div>
                        </div>
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

