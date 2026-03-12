import type { ReactNode } from "react";
import { Link, useLocation } from "react-router-dom";
import { LineChart, Beaker, Cpu, Activity, PlusCircle, Settings } from "lucide-react";
import { cn } from "@/lib/utils";

interface DashboardLayoutProps {
    children: ReactNode;
}

export function DashboardLayout({ children }: DashboardLayoutProps) {
    const location = useLocation();

    const navItems = [
        { name: "Command Center", path: "/command", icon: Activity },
        { name: "The Lab (Builder)", path: "/lab", icon: Beaker },
        { name: "MLOps Arena", path: "/arena", icon: LineChart },
        { name: "Deploy Sentinel", path: "/create", icon: PlusCircle },
        { name: "Settings", path: "/settings", icon: Settings },
    ];

    return (
        <div className="flex h-screen w-screen overflow-hidden bg-background text-foreground dark dark:bg-[#0d0d12]">
            {/* Sidebar Navigation */}
            <nav className="w-64 flex flex-col border-r border-border bg-[#14141b] backdrop-blur-md bg-opacity-80">
                <div className="p-4 border-b border-border flex items-center space-x-3">
                    <Cpu className="w-6 h-6 text-cyan-400" />
                    <h1 className="text-lg font-bold tracking-widest text-white uppercase font-mono">
                        Aegis AI
                    </h1>
                </div>

                <div className="flex-1 overflow-y-auto py-4">
                    <ul className="space-y-1 px-2">
                        {navItems.map((item) => {
                            const isActive = location.pathname.startsWith(item.path);
                            return (
                                <li key={item.path}>
                                    <Link
                                        to={item.path}
                                        className={cn(
                                            "flex items-center space-x-3 px-3 py-2 rounded-md text-sm font-medium transition-colors font-mono",
                                            isActive
                                                ? "bg-primary/20 text-cyan-400"
                                                : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                                        )}
                                    >
                                        <item.icon className="w-4 h-4" />
                                        <span>{item.name}</span>
                                    </Link>
                                </li>
                            );
                        })}
                    </ul>
                </div>

                {/* Status Footer */}
                <div className="p-4 border-t border-border flex flex-col space-y-2 text-xs font-mono text-muted-foreground">
                    <div className="flex justify-between items-center">
                        <span>FastAPI Server</span>
                        <div className="flex items-center space-x-1"><span className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span><span>Online</span></div>
                    </div>
                    <div className="flex justify-between items-center">
                        <span>Market Hours</span>
                        <span>Closed</span>
                    </div>
                </div>
            </nav>

            {/* Main Content Pane */}
            <main className="flex-1 flex flex-col h-full overflow-hidden relative">
                <div className="absolute inset-0 bg-[#0d0d12]"></div>
                {/* Content goes above the dark background */}
                <div className="relative z-10 w-full h-full p-4 flex flex-col">
                    {children}
                </div>
            </main>
        </div>
    );
}
