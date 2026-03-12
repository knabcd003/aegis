import { useState } from "react";
import { BookOpen, Layers, Target, Activity, ShieldHalf, Play, CheckCircle2, Bot } from "lucide-react";
import { ConfigEditor } from "./ConfigEditor";

export function CreateWizard() {
    const [step, setStep] = useState(1);
    
    // Final mock config output
    const [config, setConfig] = useState<Record<string, any>>({
        template: "macro-fundamental",
        universe: ["AAPL", "MSFT", "NVDA"],
        quant_engines: { vpin: true, hmm: true },
        llm: { model: "claude-3-5-sonnet", temperature: 0.1 }
    });

    const steps = [
        { id: 1, name: "Thesis", icon: BookOpen },
        { id: 2, name: "Universe", icon: Layers },
        { id: 3, name: "Template", icon: Target },
        { id: 4, name: "Quant", icon: Activity },
        { id: 5, name: "LLM Pipeline", icon: Bot },
        { id: 6, name: "Deploy", icon: Play },
    ];

    return (
        <div className="flex flex-col h-full w-full bg-background p-6 overflow-hidden">
            <div className="flex items-center justify-between mb-8 border-b border-border pb-4 shrink-0">
                <div>
                    <h1 className="text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
                        <ShieldHalf className="h-6 w-6 text-blue-500" />
                        Deploy New Sentinel
                    </h1>
                    <p className="text-muted-foreground mt-1 text-sm">
                        Design and launch a live agentic trading thesis.
                    </p>
                </div>
            </div>

            <div className="flex gap-8 flex-1 min-h-0">
                {/* Stepper Sidebar */}
                <div className="w-64 shrink-0 flex flex-col gap-2">
                    {steps.map((s) => {
                        const active = step === s.id;
                        const complete = step > s.id;
                        return (
                            <div 
                                key={s.id} 
                                className={`flex items-center gap-3 p-3 rounded-lg border font-mono text-sm transition-colors ${
                                    active ? "bg-blue-500/10 border-blue-500/30 text-blue-400" 
                                    : complete ? "border-green-500/20 text-green-500/70"
                                    : "border-transparent text-gray-500"
                                }`}
                            >
                                {complete ? <CheckCircle2 className="w-5 h-5" /> : <s.icon className="w-5 h-5" />}
                                <span className={`font-semibold ${active ? "" : "font-medium"}`}>
                                    {s.id}. {s.name}
                                </span>
                            </div>
                        );
                    })}
                </div>

                {/* Content Area */}
                <div className="flex-1 bg-card/50 border border-border rounded-lg p-8 flex flex-col overflow-y-auto relative scrollbar-thin scrollbar-thumb-gray-700">
                    {step === 1 && (
                        <div className="animate-in fade-in slide-in-from-right-4 duration-500">
                            <h2 className="text-xl font-bold text-white mb-6">1. What do you believe? (Thesis Definition)</h2>
                            <p className="text-gray-400 mb-6 text-sm">
                                Before selecting assets or templates, articulate the market inefficiency you believe exists. The Long-Term Memory chain will index this thesis.
                            </p>
                            <textarea 
                                className="w-full h-48 bg-[#0d0d12] border border-border/80 rounded-lg p-4 text-green-400 font-mono text-sm outline-none focus:border-cyan-500/50"
                                placeholder="e.g., The market underreacts to sequential upward revisions in capital expenditure for tech mega-caps with verified AI revenue streams, until the 3rd consecutive quarter."
                            ></textarea>
                        </div>
                    )}
                    
                    {step === 2 && (
                        <div className="animate-in fade-in slide-in-from-right-4 duration-500">
                            <h2 className="text-xl font-bold text-white mb-6">2. Asset Universe</h2>
                            <p className="text-gray-400 mb-6 text-sm">Map the symbols relevant to testing this thesis.</p>
                            <input 
                                type="text"
                                className="w-full bg-[#0d0d12] border border-border/80 rounded-lg p-4 text-blue-400 font-mono text-sm outline-none focus:border-cyan-500/50 uppercase"
                                placeholder="AAPL, MSFT, NVDA, GOOGL"
                                defaultValue="AAPL, MSFT, NVDA"
                            />
                        </div>
                    )}

                    {step === 3 && (
                        <div className="animate-in fade-in slide-in-from-right-4 duration-500">
                            <h2 className="text-xl font-bold text-white mb-6">3. Template Matching</h2>
                            <p className="text-gray-400 mb-6 text-sm">Select the structural routing template that best fits your thesis.</p>
                            <div className="grid grid-cols-2 gap-4">
                                <div className="border border-blue-500/50 bg-blue-500/10 p-5 rounded-lg cursor-pointer hover:bg-blue-500/20 transition-colors">
                                    <h3 className="font-bold text-blue-400 mb-2">Macro-Fundamental</h3>
                                    <p className="text-xs text-gray-400">Focuses on SEC 10-Q/K, earnings calls, and macroeconomic data releases. Highly rigorous graph.</p>
                                </div>
                                <div className="border border-border/50 bg-[#0d0d12] opacity-50 p-5 rounded-lg cursor-pointer">
                                    <h3 className="font-bold text-gray-400 mb-2">High-Frequency Intraday</h3>
                                    <p className="text-xs text-gray-500">Relies primarily on order book toxicity (VPIN) and momentum breaks.</p>
                                </div>
                            </div>
                        </div>
                    )}

                    {step === 4 && (
                        <div className="animate-in fade-in slide-in-from-right-4 duration-500 h-full flex flex-col">
                            <h2 className="text-xl font-bold text-white mb-6">4. Quant Engine Configuration</h2>
                            <p className="text-gray-400 mb-4 text-sm">Enable and tune the traditional math nodes (Plugin Layer).</p>
                            <div className="flex-1 min-h-0 border border-border/50 rounded-lg overflow-hidden">
                                <ConfigEditor initialConfig={config} onSave={setConfig} />
                            </div>
                        </div>
                    )}

                    {step === 5 && (
                        <div className="animate-in fade-in slide-in-from-right-4 duration-500">
                            <h2 className="text-xl font-bold text-white mb-6">5. LLM Pipeline Setup</h2>
                            <p className="text-gray-400 mb-6 text-sm">Configure the intelligence backend for semantic reasoning.</p>
                            <div className="space-y-4">
                                <div className="flex items-center justify-between p-4 border border-border/50 rounded-lg bg-[#0d0d12]">
                                    <span className="font-bold text-gray-300">Primary Analyst Node</span>
                                    <span className="text-cyan-400 font-mono">claude-3-5-sonnet</span>
                                </div>
                                <div className="flex items-center justify-between p-4 border border-border/50 rounded-lg bg-[#0d0d12]">
                                    <span className="font-bold text-gray-300">Fast Fallback Node (Uncertainty &gt; 0.8)</span>
                                    <span className="text-purple-400 font-mono">qwen-2.5-32b</span>
                                </div>
                            </div>
                        </div>
                    )}

                    {step === 6 && (
                        <div className="flex flex-col items-center justify-center h-full animate-in zoom-in-95 duration-500">
                            <ShieldHalf className="w-16 h-16 text-green-500 mb-6" />
                            <h2 className="text-2xl font-bold text-white mb-2">Configuration Complete</h2>
                            <p className="text-gray-400 mb-8 max-w-md text-center text-sm">
                                The `Macro-Fundamental` thesis against `[AAPL, MSFT, NVDA]` is ready for simulated execution in the Sandbox.
                            </p>
                            <button className="bg-green-500/20 hover:bg-green-500/30 text-green-400 border border-green-500/50 px-8 py-3 rounded-md font-bold text-lg transition-transform hover:scale-105 flex items-center gap-2 shadow-[0_0_15px_rgba(34,197,94,0.3)]">
                                <Play className="w-5 h-5 fill-current" />
                                Launch Sandbox
                            </button>
                        </div>
                    )}

                    {/* Nav Footer */}
                    <div className="mt-auto pt-6 flex justify-between">
                        <button 
                            onClick={() => setStep(s => Math.max(1, s - 1))}
                            className={`px-4 py-2 rounded text-sm font-semibold transition-colors ${step === 1 ? 'opacity-0 pointer-events-none' : 'text-gray-400 hover:text-white hover:bg-white/5'}`}
                        >
                            Back
                        </button>
                        {step < 6 && (
                            <button 
                                onClick={() => setStep(s => Math.min(6, s + 1))}
                                className="bg-blue-600 hover:bg-blue-500 text-white px-6 py-2 rounded text-sm font-bold shadow-lg transition-colors"
                            >
                                Next Step
                            </button>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
