import type { ReactNode } from "react";
import { Link, useLocation } from "react-router-dom";
import {
    Activity, Beaker, LineChart, PlusCircle, Settings,
    BarChart3, HeartPulse, Library, GitBranch, MessageSquare,
    Blocks, ChevronDown
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
            { name: "Command Center", path: "/command", icon: Activity },
            { name: "System Health", path: "/health", icon: HeartPulse },
        ],
    },
    {
        label: "Build",
        items: [
            { name: "Strategy Wizard", path: "/create", icon: PlusCircle },
            { name: "Sandbox", path: "/lab", icon: Beaker },
            { name: "Engine Library", path: "/engines", icon: Library },
        ],
    },
    {
        label: "Analyze",
        items: [
            { name: "MLOps Arena", path: "/arena", icon: BarChart3 },
            { name: "Audit Chat", path: "/audit", icon: MessageSquare },
            { name: "Version Control", path: "/versions", icon: GitBranch },
        ],
    },
];

export function DashboardLayout({ children }: DashboardLayoutProps) {
    const location = useLocation();
    const [serverStatus, setServerStatus] = useState<"online" | "offline">("offline");
    const [collapsed, setCollapsed] = useState<Record<string, boolean>>({});

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
        <div className="flex h-screen w-screen overflow-hidden bg-background text-foreground dark">
            {/* Sidebar */}
            <nav className="w-60 flex flex-col border-r border-border bg-card shrink-0">
                {/* Brand */}
                <div className="px-5 py-4 border-b border-border">
                    <h1 className="text-base font-semibold tracking-tight text-foreground">
                        Aegis AI
                    </h1>
                    <p className="text-[11px] text-muted-foreground mt-0.5">
                        Autonomous Trading Intelligence
                    </p>
                </div>

                {/* Navigation */}
                <div className="flex-1 overflow-y-auto py-3 scrollbar-thin">
                    {sections.map((section) => (
                        <div key={section.label} className="mb-1">
                            <button
                                onClick={() => toggleSection(section.label)}
                                className="w-full flex items-center justify-between px-5 py-1.5 text-[11px] font-semibold uppercase tracking-widest text-muted-foreground hover:text-foreground transition-colors"
                            >
                                <span>{section.label}</span>
                                <ChevronDown
                                    className={cn(
                                        "w-3 h-3 transition-transform",
                                        collapsed[section.label] && "-rotate-90"
                                    )}
                                />
                            </button>

                            {!collapsed[section.label] && (
                                <ul className="mt-0.5 space-y-0.5 px-3">
                                    {section.items.map((item) => {
                                        const isActive = location.pathname === item.path;
                                        return (
                                            <li key={item.path}>
                                                <Link
                                                    to={item.path}
                                                    className={cn(
                                                        "flex items-center gap-2.5 px-2.5 py-[7px] rounded-lg text-[13px] font-medium transition-all duration-150",
                                                        isActive
                                                            ? "bg-accent/12 text-accent"
                                                            : "text-muted-foreground hover:bg-muted/60 hover:text-foreground"
                                                    )}
                                                >
                                                    <item.icon className="w-4 h-4 shrink-0" />
                                                    <span>{item.name}</span>
                                                </Link>
                                            </li>
                                        );
                                    })}
                                </ul>
                            )}
                        </div>
                    ))}
                </div>

                {/* Settings Link */}
                <div className="px-3 py-2 border-t border-border">
                    <Link
                        to="/settings"
                        className={cn(
                            "flex items-center gap-2.5 px-2.5 py-[7px] rounded-lg text-[13px] font-medium transition-all duration-150",
                            location.pathname === "/settings"
                                ? "bg-accent/12 text-accent"
                                : "text-muted-foreground hover:bg-muted/60 hover:text-foreground"
                        )}
                    >
                        <Settings className="w-4 h-4 shrink-0" />
                        <span>Settings</span>
                    </Link>
                </div>

                {/* Status Footer */}
                <div className="px-5 py-3 border-t border-border">
                    <div className="flex items-center justify-between text-[11px] text-muted-foreground">
                        <span>API Server</span>
                        <div className="flex items-center gap-1.5">
                            <span
                                className={cn(
                                    "w-1.5 h-1.5 rounded-full",
                                    serverStatus === "online" ? "bg-emerald-500" : "bg-red-500"
                                )}
                            />
                            <span className={serverStatus === "online" ? "text-emerald-500" : "text-red-400"}>
                                {serverStatus === "online" ? "Online" : "Offline"}
                            </span>
                        </div>
                    </div>
                </div>
            </nav>

            {/* Main Content */}
            <main className="flex-1 flex flex-col h-full overflow-hidden">
                <div className="w-full h-full overflow-auto">
                    {children}
                </div>
            </main>
        </div>
    );
}
