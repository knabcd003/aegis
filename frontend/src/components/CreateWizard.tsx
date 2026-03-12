import { useState } from "react";
import { BookOpen, Layers, Target, Activity, ShieldHalf, Play, CheckCircle2, Bot, Loader2 } from "lucide-react";
import { ConfigEditor } from "./ConfigEditor";

export function CreateWizard() {
    const [step, setStep] = useState(1);
    
    // User Form State
    const [thesis, setThesis] = useState("");
    const [tradingStyle, setTradingStyle] = useState("swing");
    const [riskTolerance, setRiskTolerance] = useState("moderate");
    const [diversification, setDiversification] = useState("broad");
    
    // Generation State
    const [isGenerating, setIsGenerating] = useState(false);
    const [generationStatus, setGenerationStatus] = useState("");
    
    // Final config output
    const [config, setConfig] = useState<Record<string, any>>({});

    const steps = [
        { id: 1, name: "Thesis & Style", icon: BookOpen },
        { id: 2, name: "Risk Profile", icon: Target },
        { id: 3, name: "Diversification", icon: Layers },
        { id: 4, name: "AI Generation", icon: Bot },
        { id: 5, name: "Config Review", icon: Activity },
        { id: 6, name: "Deploy", icon: Play },
    ];

    const generateSystem = async () => {
        setIsGenerating(true);
        setStep(4);
        
        // Progress sequence
        setGenerationStatus("Building structural scaffold based on risk parameters...");
        
        try {
            const res = await fetch("http://localhost:8000/api/systems/generate", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    thesis,
                    trading_style: tradingStyle,
                    risk_tolerance: riskTolerance,
                    diversification: diversification
                })
            });
            
            if (!res.ok) throw new Error("Generation failed");
            
            setGenerationStatus("LLM evaluating thesis for feature detection...");
            
            const data = await res.json();
            
            setGenerationStatus("Merging and validating schema...");
            
            // Artificial delay to show the final status briefly
            await new Promise(r => setTimeout(r, 800));
            
            setConfig(data.config);
            setStep(5); // Move to review step
        } catch (error) {
            console.error("Failed to generate system:", error);
            setGenerationStatus("Error generating system. Please try again.");
        } finally {
            setIsGenerating(false);
        }
    };
    
    const deploySystem = async () => {
        try {
            // Re-using the MLflow sweep endpoint as the "Sandbox Launch" target
            await fetch("http://localhost:8000/api/mlops/sweep", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    tickers: config.asset_universe?.tickers || [],
                    n_trials: 5,
                    models_to_test: [config.analyst_engine?.model || "qwen3:8b"]
                })
            });
            // We could redirect to the Lab here, but for now we just show Step 6
            setStep(6);
        } catch (error) {
            console.error("Deployment failed:", error);
        }
    };

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
                            <h2 className="text-xl font-bold text-white mb-6">1. What do you believe? (Thesis & Style)</h2>
                            <p className="text-gray-400 mb-6 text-sm">
                                Articulate the market inefficiency you believe exists. The Intelligence layer will use this to determine which data connectors to enable.
                            </p>
                            <textarea 
                                value={thesis}
                                onChange={e => setThesis(e.target.value)}
                                className="w-full h-32 bg-[#0d0d12] border border-border/80 rounded-lg p-4 text-green-400 font-mono text-sm outline-none focus:border-cyan-500/50 mb-6"
                                placeholder="e.g., The market underreacts to sequential upward revisions in capital expenditure for tech mega-caps..."
                            />
                            <p className="text-gray-400 mb-4 text-sm font-bold">Planned Trading Horizon:</p>
                            <div className="grid grid-cols-3 gap-4">
                                {["intraday", "swing", "position"].map(style => (
                                    <div 
                                        key={style}
                                        onClick={() => setTradingStyle(style)}
                                        className={`border p-4 rounded-lg cursor-pointer transition-colors text-center capitalize ${tradingStyle === style ? 'border-blue-500/50 bg-blue-500/10 text-blue-400 font-bold' : 'border-border/50 bg-[#0d0d12] text-gray-500 hover:bg-[#14141b]'}`}
                                    >
                                        {style}
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                    
                    {step === 2 && (
                        <div className="animate-in fade-in slide-in-from-right-4 duration-500">
                            <h2 className="text-xl font-bold text-white mb-6">2. Risk Profile</h2>
                            <p className="text-gray-400 mb-6 text-sm">This determines structural constraints like VPIN toxicity thresholds, HMM regime requirements, and maximum position sizing.</p>
                            <div className="space-y-4">
                                {[
                                    { val: "conservative", desc: "Tight VPIN ceilings, strictly Bull regimes, max 5% positions." },
                                    { val: "moderate", desc: "Standard thresholds, permits sideways regimes, max 10% positions." },
                                    { val: "aggressive", desc: "High toxicity tolerance, permits shorting in Bear regimes, max 25% positions." }
                                ].map(risk => (
                                    <div 
                                        key={risk.val}
                                        onClick={() => setRiskTolerance(risk.val)}
                                        className={`border p-5 rounded-lg cursor-pointer transition-colors flex flex-col gap-1 ${riskTolerance === risk.val ? 'border-blue-500/50 bg-blue-500/10' : 'border-border/50 bg-[#0d0d12] hover:bg-[#14141b]'}`}
                                    >
                                        <div className={`font-bold capitalize ${riskTolerance === risk.val ? 'text-blue-400' : 'text-gray-300'}`}>{risk.val}</div>
                                        <div className="text-xs text-gray-500">{risk.desc}</div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {step === 3 && (
                        <div className="animate-in fade-in slide-in-from-right-4 duration-500">
                            <h2 className="text-xl font-bold text-white mb-6">3. Diversification Preference</h2>
                            <p className="text-gray-400 mb-6 text-sm">How wide of a net do you want this Sentinel to cast?</p>
                            <div className="grid grid-cols-2 gap-4">
                                {[
                                    { val: "concentrated", desc: "Top 3-5 high-conviction names only. Highly volalite." },
                                    { val: "broad", desc: "10+ names across sub-sectors or broad market ETFs." }
                                ].map(div => (
                                    <div 
                                        key={div.val}
                                        onClick={() => setDiversification(div.val)}
                                        className={`border p-5 rounded-lg cursor-pointer transition-colors flex flex-col gap-1 ${diversification === div.val ? 'border-purple-500/50 bg-purple-500/10' : 'border-border/50 bg-[#0d0d12] hover:bg-[#14141b]'}`}
                                    >
                                        <div className={`font-bold capitalize ${diversification === div.val ? 'text-purple-400' : 'text-gray-300'}`}>{div.val}</div>
                                        <div className="text-xs text-gray-500">{div.desc}</div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {step === 4 && (
                        <div className="animate-in zoom-in slide-in-from-bottom-4 duration-500 h-full flex flex-col items-center justify-center">
                            {isGenerating ? (
                                <>
                                    <Loader2 className="w-16 h-16 text-cyan-500 animate-spin mb-6" />
                                    <h2 className="text-xl font-bold text-white mb-2">Synthesizing Sentinel...</h2>
                                    <p className="text-cyan-400 font-mono text-sm max-w-md text-center">{generationStatus}</p>
                                </>
                            ) : (
                                <div className="text-red-500">{generationStatus}</div>
                            )}
                        </div>
                    )}

                    {step === 5 && (
                        <div className="animate-in fade-in slide-in-from-right-4 duration-500 h-full flex flex-col">
                            <h2 className="text-xl font-bold text-white mb-2">5. Review Configuration Schema</h2>
                            <p className="text-gray-400 mb-4 text-sm">The engine has merged your structural rules with LLM feature selection. You may adjust the raw JSON before deployment.</p>
                            <div className="flex-1 min-h-0 border border-border/50 rounded-lg overflow-hidden shadow-[0_0_15px_rgba(59,130,246,0.1)]">
                                {Object.keys(config).length > 0 && (
                                    <ConfigEditor initialConfig={config} onSave={setConfig} />
                                )}
                            </div>
                        </div>
                    )}

                    {step === 6 && (
                        <div className="flex flex-col items-center justify-center h-full animate-in zoom-in-95 duration-500">
                            <ShieldHalf className="w-16 h-16 text-green-500 mb-6" />
                            <h2 className="text-2xl font-bold text-white mb-2">Sandbox Validation Initiated</h2>
                            <p className="text-gray-400 mb-8 max-w-md text-center text-sm">
                                The Sentinel `{config.name}` has been queued for a historical sweep across {config.asset_universe?.tickers?.length || 0} tickers.
                            </p>
                            <div className="flex gap-4">
                                <button onClick={() => window.location.href = '/lab'} className="bg-green-500/20 hover:bg-green-500/30 text-green-400 border border-green-500/50 px-8 py-3 rounded-md font-bold text-lg transition-transform hover:scale-105 shadow-[0_0_15px_rgba(34,197,94,0.3)]">
                                    Go to The Lab
                                </button>
                                <button onClick={() => window.location.href = '/arena'} className="bg-blue-500/20 hover:bg-blue-500/30 text-blue-400 border border-blue-500/50 px-8 py-3 rounded-md font-bold text-lg transition-colors">
                                    View Leaderboard
                                </button>
                            </div>
                        </div>
                    )}

                    {/* Nav Footer */}
                    <div className="mt-auto pt-6 flex justify-between">
                        <button 
                            onClick={() => setStep(s => Math.max(1, s - 1))}
                            className={`px-4 py-2 rounded text-sm font-semibold transition-colors ${step === 1 || step === 4 || step === 6 ? 'opacity-0 pointer-events-none' : 'text-gray-400 hover:text-white hover:bg-white/5'}`}
                        >
                            Back
                        </button>
                        {step < 5 && step !== 4 && (
                            <button 
                                onClick={() => step === 3 ? generateSystem() : setStep(s => Math.min(6, s + 1))}
                                className="bg-blue-600 hover:bg-blue-500 text-white px-6 py-2 rounded text-sm font-bold shadow-lg transition-colors"
                            >
                                {step === 3 ? "Generate System" : "Next Step"}
                            </button>
                        )}
                        {step === 5 && (
                            <button 
                                onClick={deploySystem}
                                className="bg-green-600 hover:bg-green-500 text-white px-6 py-2 rounded text-sm font-bold shadow-lg transition-colors flex items-center gap-2"
                            >
                                <Play className="w-4 h-4" />
                                Launch in Sandbox
                            </button>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
