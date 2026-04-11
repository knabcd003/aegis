import { useState } from "react";
import { IntakePathA } from "@/components/Intake/IntakePathA";
import { IntakePathB } from "@/components/Intake/IntakePathB";
import { cn } from "@/lib/utils";
import { Rocket, FileJson, Info } from "lucide-react";

export function IntakePage() {
    const [path, setPath] = useState<"A" | "B">("A");

    return (
        <div className="flex flex-col h-full bg-[#0C0E11] overflow-hidden">
            {/* High-Density Sub-Nav */}
            <header className="h-12 border-b border-[#2D333B] bg-[#111418]/50 flex items-center px-6 shrink-0 gap-8">
                <button
                    onClick={() => setPath("A")}
                    className={cn(
                        "h-full px-2 text-[11px] font-bold uppercase tracking-widest transition-all relative",
                        path === "A" 
                            ? "text-white after:absolute after:bottom-[-1px] after:left-0 after:right-0 after:h-[2px] after:bg-white" 
                            : "text-white/30 hover:text-white/60"
                    )}
                >
                    Path_A: Systematic_Guided
                </button>
                <button
                    onClick={() => setPath("B")}
                    className={cn(
                        "h-full px-2 text-[11px] font-bold uppercase tracking-widest transition-all relative",
                        path === "B" 
                            ? "text-white after:absolute after:bottom-[-1px] after:left-0 after:right-0 after:h-[2px] after:bg-white" 
                            : "text-white/30 hover:text-white/60"
                    )}
                >
                    Path_B: Schema_Import
                </button>
            </header>

            <div className="flex-1 overflow-y-auto scrollbar-thin">
                <div className="max-w-4xl mx-auto py-10 px-6">
                    {/* Path Content */}
                    <div className="min-h-[400px]">
                        {path === "A" ? <IntakePathA /> : <IntakePathB />}
                    </div>

                    {/* Bottom Info Banner (Industrial) */}
                    <div className="mt-12 p-4 border border-[#2D333B] bg-[#111418] flex items-start gap-4">
                        <Info className="w-4 h-4 text-white/40 shrink-0 mt-0.5" />
                        <div className="space-y-1">
                            <h4 className="text-[10px] font-bold text-white uppercase tracking-widest">Structural Validation Enforcement (V7-S)</h4>
                            <p className="text-[10px] font-mono text-white/30 leading-relaxed">
                                Aegis V7 enforces strict Pydantic structural validation at Layer 1. 
                                LLM-as-Judge semantic validation at Layer 2 ensures your intent is economically viable. 
                                Contradicts will trigger a mandate block.
                            </p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
