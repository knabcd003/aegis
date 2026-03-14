import { useState } from "react";
import { BookOpen, Layers, Target, Activity, ShieldHalf, Play, CheckCircle2, Bot, Loader2, DollarSign } from "lucide-react";
import { ConfigEditor } from "./ConfigEditor";
import { useNavigate } from "react-router-dom";

export function CreateWizard() {
    const navigate = useNavigate();
    const [step, setStep] = useState(1);
    
    // User Form State
    const [thesis, setThesis] = useState("");
    const [tradingStyle, setTradingStyle] = useState("swing");
    const [riskTolerance, setRiskTolerance] = useState("moderate");
    const [capital, setCapital] = useState(100000);
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
        
        setGenerationStatus("Building structural scaffold based on risk parameters...");
        
        try {
            const res = await fetch("http://localhost:8000/api/systems/generate", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    thesis,
                    trading_style: tradingStyle,
                    risk_tolerance: riskTolerance,
                    diversification: diversification,
                    capital: capital
                })
            });
            
            if (!res.ok) throw new Error("Generation failed");
            
            setGenerationStatus("LLM evaluating thesis for feature detection...");
            
            const data = await res.json();
            
            setGenerationStatus("Merging and validating schema...");
            
            await new Promise(r => setTimeout(r, 800));
            
            setConfig(data.config);
            setStep(5);
        } catch (error) {
            console.error("Failed to generate system:", error);
            setGenerationStatus("Error generating system. Please try again.");
        } finally {
            setIsGenerating(false);
        }
    };
    
    const deploySystem = async () => {
        try {
            await fetch("http://localhost:8000/api/mlops/sweep", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    tickers: config.asset_universe?.tickers || [],
                    n_trials: 5,
                    models_to_test: [config.analyst_engine?.model || "qwen3:8b"]
                })
            });
            setStep(6);
        } catch (error) {
            console.error("Deployment failed:", error);
        }
    };

    const capitalPresets = [
        { label: "$10K", value: 10000 },
        { label: "$50K", value: 50000 },
        { label: "$100K", value: 100000 },
        { label: "$500K", value: 500000 },
    ];

    return (
        <div className="flex flex-col h-full w-full bg-background p-6 overflow-hidden">
            <div className="flex items-center justify-between mb-8 border-b border-border pb-4 shrink-0">
                <div>
                    <h1 className="text-2xl font-semibold tracking-tight text-foreground flex items-center gap-2.5">
                        <ShieldHalf className="h-6 w-6 text-accent" />
                        Deploy New Sentinel
                    </h1>
                    <p className="text-muted-foreground mt-1 text-sm">
                        Design and launch a live agentic trading thesis.
                    </p>
                </div>
            </div>

            <div className="flex gap-8 flex-1 min-h-0">
                {/* Stepper Sidebar */}
                <div className="w-64 shrink-0 flex flex-col gap-1.5">
                    {steps.map((s) => {
                        const active = step === s.id;
                        const complete = step > s.id;
                        return (
                            <div 
                                key={s.id} 
                                className={`flex items-center gap-3 p-3 rounded-lg border text-sm transition-colors ${
                                    active ? "bg-accent/10 border-accent/30 text-accent" 
                                    : complete ? "border-emerald-500/20 text-emerald-500/70"
                                    : "border-transparent text-muted-foreground"
                                }`}
                            >
                                {complete ? <CheckCircle2 className="w-5 h-5" /> : <s.icon className="w-5 h-5" />}
                                <span className={`${active ? "font-semibold" : "font-medium"}`}>
                                    {s.id}. {s.name}
                                </span>
                            </div>
                        );
                    })}
                </div>

                {/* Content Area */}
                <div className="flex-1 bg-card/50 border border-border rounded-lg p-8 flex flex-col overflow-y-auto relative scrollbar-thin">
                    {step === 1 && (
                        <div className="animate-in fade-in slide-in-from-right-4 duration-500">
                            <h2 className="text-xl font-semibold text-foreground mb-2">1. What do you believe?</h2>
                            <p className="text-muted-foreground mb-6 text-sm">
                                Articulate the market inefficiency you believe exists. The Intelligence layer will use this to determine which data connectors to enable.
                            </p>
                            <textarea 
                                value={thesis}
                                onChange={e => setThesis(e.target.value)}
                                className="w-full h-32 bg-background border border-border rounded-lg p-4 text-foreground font-mono text-sm outline-none focus:ring-1 focus:ring-accent/50 mb-6 placeholder:text-muted-foreground"
                                placeholder="e.g., The market underreacts to sequential upward revisions in capital expenditure for tech mega-caps..."
                            />
                            <p className="text-muted-foreground mb-4 text-sm font-semibold">Planned Trading Horizon:</p>
                            <div className="grid grid-cols-3 gap-4">
                                {["intraday", "swing", "position"].map(style => (
                                    <div 
                                        key={style}
                                        onClick={() => setTradingStyle(style)}
                                        className={`border p-4 rounded-lg cursor-pointer transition-colors text-center capitalize ${
                                            tradingStyle === style 
                                            ? 'border-accent/50 bg-accent/10 text-accent font-semibold' 
                                            : 'border-border bg-background text-muted-foreground hover:bg-muted/40'
                                        }`}
                                    >
                                        {style}
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                    
                    {step === 2 && (
                        <div className="animate-in fade-in slide-in-from-right-4 duration-500">
                            <h2 className="text-xl font-semibold text-foreground mb-2">2. Risk Profile</h2>
                            <p className="text-muted-foreground mb-6 text-sm">This determines structural constraints like VPIN toxicity thresholds, HMM regime requirements, and maximum position sizing.</p>
                            
                            <div className="space-y-4 mb-6">
                                {[
                                    { val: "conservative", desc: "Tight VPIN ceilings, strictly Bull regimes, max 5% positions." },
                                    { val: "moderate", desc: "Standard thresholds, permits sideways regimes, max 10% positions." },
                                    { val: "aggressive", desc: "High toxicity tolerance, permits shorting in Bear regimes, max 25% positions." }
                                ].map(risk => (
                                    <div 
                                        key={risk.val}
                                        onClick={() => setRiskTolerance(risk.val)}
                                        className={`border p-5 rounded-lg cursor-pointer transition-colors flex flex-col gap-1 ${
                                            riskTolerance === risk.val 
                                            ? 'border-accent/50 bg-accent/10' 
                                            : 'border-border bg-background hover:bg-muted/40'
                                        }`}
                                    >
                                        <div className={`font-semibold capitalize ${riskTolerance === risk.val ? 'text-accent' : 'text-foreground'}`}>{risk.val}</div>
                                        <div className="text-xs text-muted-foreground">{risk.desc}</div>
                                    </div>
                                ))}
                            </div>

                            {/* Capital Input */}
                            <div className="border-t border-border pt-6">
                                <div className="flex items-center gap-2 mb-3">
                                    <DollarSign className="w-4 h-4 text-accent" />
                                    <span className="text-sm font-semibold text-foreground">Starting Capital</span>
                                </div>
                                <div className="flex items-center gap-3">
                                    <div className="relative flex-1 max-w-xs">
                                        <span className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground text-sm">$</span>
                                        <input 
                                            type="number" 
                                            value={capital} 
                                            onChange={e => setCapital(parseInt(e.target.value) || 0)}
                                            className="w-full bg-background border border-border rounded-lg pl-7 pr-3 py-2 text-sm font-mono outline-none focus:ring-1 focus:ring-accent/50"
                                            min={1000}
                                            step={1000}
                                        />
                                    </div>
                                    <div className="flex gap-1.5">
                                        {capitalPresets.map(p => (
                                            <button 
                                                key={p.value}
                                                onClick={() => setCapital(p.value)}
                                                className={`px-2.5 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                                                    capital === p.value 
                                                    ? 'bg-accent/10 text-accent border border-accent/30' 
                                                    : 'border border-border text-muted-foreground hover:bg-muted/40'
                                                }`}
                                            >
                                                {p.label}
                                            </button>
                                        ))}
                                    </div>
                                </div>
                                <p className="text-[11px] text-muted-foreground mt-2">
                                    Paper capital for sandbox backtesting. This doesn't affect real money until promoted to production.
                                </p>
                            </div>
                        </div>
                    )}

                    {step === 3 && (
                        <div className="animate-in fade-in slide-in-from-right-4 duration-500">
                            <h2 className="text-xl font-semibold text-foreground mb-2">3. Diversification Preference</h2>
                            <p className="text-muted-foreground mb-6 text-sm">How wide of a net do you want this Sentinel to cast?</p>
                            <div className="grid grid-cols-2 gap-4">
                                {[
                                    { val: "concentrated", desc: "Top 3-5 high-conviction names only. Highly volatile." },
                                    { val: "broad", desc: "10+ names across sub-sectors or broad market ETFs." }
                                ].map(div => (
                                    <div 
                                        key={div.val}
                                        onClick={() => setDiversification(div.val)}
                                        className={`border p-5 rounded-lg cursor-pointer transition-colors flex flex-col gap-1 ${
                                            diversification === div.val 
                                            ? 'border-violet-500/50 bg-violet-500/10' 
                                            : 'border-border bg-background hover:bg-muted/40'
                                        }`}
                                    >
                                        <div className={`font-semibold capitalize ${diversification === div.val ? 'text-violet-400' : 'text-foreground'}`}>{div.val}</div>
                                        <div className="text-xs text-muted-foreground">{div.desc}</div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {step === 4 && (
                        <div className="animate-in zoom-in slide-in-from-bottom-4 duration-500 h-full flex flex-col items-center justify-center">
                            {isGenerating ? (
                                <>
                                    <Loader2 className="w-16 h-16 text-accent animate-spin mb-6" />
                                    <h2 className="text-xl font-semibold text-foreground mb-2">Synthesizing Sentinel...</h2>
                                    <p className="text-accent font-mono text-sm max-w-md text-center">{generationStatus}</p>
                                </>
                            ) : (
                                <div className="text-red-400">{generationStatus}</div>
                            )}
                        </div>
                    )}

                    {step === 5 && (
                        <div className="animate-in fade-in slide-in-from-right-4 duration-500 h-full flex flex-col">
                            <h2 className="text-xl font-semibold text-foreground mb-2">5. Review Configuration Schema</h2>
                            <p className="text-muted-foreground mb-4 text-sm">The engine has merged your structural rules with LLM feature selection. You may adjust the raw JSON before deployment.</p>
                            <div className="flex-1 min-h-0 border border-border rounded-lg overflow-hidden">
                                {Object.keys(config).length > 0 && (
                                    <ConfigEditor initialConfig={config} onSave={setConfig} />
                                )}
                            </div>
                        </div>
                    )}

                    {step === 6 && (
                        <div className="flex flex-col items-center justify-center h-full animate-in zoom-in-95 duration-500">
                            <ShieldHalf className="w-16 h-16 text-emerald-500 mb-6" />
                            <h2 className="text-2xl font-semibold text-foreground mb-2">Sandbox Validation Initiated</h2>
                            <p className="text-muted-foreground mb-2 max-w-md text-center text-sm">
                                The Sentinel <span className="font-mono text-accent">{config.name}</span> has been queued for a historical sweep across {config.asset_universe?.tickers?.length || 0} tickers with {new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(config.sandbox?.capital || capital)} capital.
                            </p>
                            <div className="flex gap-3 mt-6">
                                <button onClick={() => navigate('/lab')} 
                                    className="bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-500 border border-emerald-500/30 px-6 py-2.5 rounded-lg font-semibold text-sm transition-colors">
                                    Go to Sandbox
                                </button>
                                <button onClick={() => navigate('/arena')} 
                                    className="bg-accent/10 hover:bg-accent/20 text-accent border border-accent/30 px-6 py-2.5 rounded-lg font-semibold text-sm transition-colors">
                                    View Leaderboard
                                </button>
                            </div>
                        </div>
                    )}

                    {/* Nav Footer */}
                    <div className="mt-auto pt-6 flex justify-between">
                        <button 
                            onClick={() => setStep(s => Math.max(1, s - 1))}
                            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${step === 1 || step === 4 || step === 6 ? 'opacity-0 pointer-events-none' : 'text-muted-foreground hover:text-foreground hover:bg-muted/40'}`}
                        >
                            Back
                        </button>
                        {step < 5 && step !== 4 && (
                            <button 
                                onClick={() => step === 3 ? generateSystem() : setStep(s => Math.min(6, s + 1))}
                                className="bg-accent hover:bg-accent/90 text-accent-foreground px-6 py-2 rounded-lg text-sm font-semibold transition-colors"
                            >
                                {step === 3 ? "Generate System" : "Next Step"}
                            </button>
                        )}
                        {step === 5 && (
                            <button 
                                onClick={deploySystem}
                                className="bg-emerald-600 hover:bg-emerald-500 text-white px-6 py-2 rounded-lg text-sm font-semibold transition-colors flex items-center gap-2"
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
