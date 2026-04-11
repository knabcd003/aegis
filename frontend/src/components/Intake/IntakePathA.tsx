import React, { useState } from 'react';
import { useAegisStore } from '@/lib/store';
import { 
    Rocket, FileWarning, Shield, CheckCircle, ChevronRight, Activity, 
    Zap, Clock, Target, AlertTriangle, Lock, Info, 
    MessageSquare, LineChart, ShieldCheck 
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { cn } from "@/lib/utils";

type DrawdownBucket = "Low (5%)" | "Balanced (15%)" | "High (30%)";
type RiskTolerance = "Conservative" | "Moderate" | "Aggressive";
type TimeHorizon = "Intraday" | "Swing" | "Multi-Week";

export function IntakePathA() {
    const navigate = useNavigate();

    // Form State
    const [risk, setRisk] = useState<RiskTolerance>("Moderate");
    const [horizon, setHorizon] = useState<TimeHorizon>("Swing");
    const [bucket, setBucket] = useState<DrawdownBucket>("Balanced (15%)");
    const [rawDesire, setRawDesire] = useState("");
    
    // UI State
    const [isValidating, setIsValidating] = useState(false);
    const [validationResult, setValidationResult] = useState<any | null>(null);
    const [isConfirming, setIsConfirming] = useState(false);

    const isDesireValid = rawDesire.trim().length === 0 || rawDesire.trim().length >= 10;

    const handleValidate = async () => {
        setIsValidating(true);
        let max_dd = 0.15;
        if (bucket === "Low (5%)") max_dd = 0.05;
        if (bucket === "High (30%)") max_dd = 0.30;

        try {
            const res = await fetch("http://localhost:8000/api/intake/validate", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    risk_tolerance: risk,
                    time_horizon: horizon,
                    max_drawdown_target: max_dd,
                    raw_desire: rawDesire,
                    is_path_b: false
                })
            });
            if (!res.ok) throw new Error("Validation failed");
            const data = await res.json();
            setValidationResult(data);
        } catch (err) {
            console.error(err);
        } finally {
            setIsValidating(false);
        }
    };

    const handleConfirm = async () => {
        setIsConfirming(true);
        let max_dd = 0.15;
        if (bucket === "Low (5%)") max_dd = 0.05;
        if (bucket === "High (30%)") max_dd = 0.30;

        try {
            const res = await fetch("http://localhost:8000/api/intake/confirm", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    risk_tolerance: risk,
                    time_horizon: horizon,
                    max_drawdown_target: max_dd,
                    raw_desire: rawDesire,
                    is_path_b: false
                })
            });
            const data = await res.json();
            useAegisStore.setState({ active_run_id: data.workflow_id });
            navigate("/command");
        } catch (err) {
            console.error(err);
        } finally {
            setIsConfirming(false);
        }
    };

    if (validationResult) {
        return (
            <div className="max-w-3xl mx-auto border border-[#2D333B] bg-[#111418]">
                <div className="px-8 py-6 border-b border-[#2D333B] bg-white/5 flex items-center justify-between">
                    <div className="flex items-center gap-4">
                        <div className="w-10 h-10 border border-[#2D333B] flex items-center justify-center">
                            <Lock className="w-5 h-5 text-white/60" />
                        </div>
                        <div>
                            <h2 className="text-sm font-bold text-white uppercase tracking-[0.1em]">Mandate Lock: V7 Compliance</h2>
                            <p className="text-[10px] text-white/40 uppercase tracking-widest font-mono mt-1">Constraint_Verification_Active</p>
                        </div>
                    </div>
                    <div className="flex items-center gap-2 text-[10px] font-mono text-white/40">
                        <span className="w-1.5 h-1.5 rounded-full bg-white opacity-40" />
                        SCHEMA: V7.0_STABLE
                    </div>
                </div>

                <div className="p-8 space-y-8">
                    {/* Contradictions */}
                    {validationResult.contradictions.length > 0 && (
                        <div className="border border-red-900 bg-red-950/20 p-6">
                            <div className="flex items-start gap-4">
                                <AlertTriangle className="w-5 h-5 text-red-500 shrink-0" />
                                <div>
                                    <h3 className="font-bold text-[10px] text-red-400 uppercase tracking-widest">Logic Faults Detected</h3>
                                    <ul className="space-y-2 mt-4">
                                        {validationResult.contradictions.map((c: string, i: number) => (
                                            <li key={i} className="flex items-center gap-2 text-[10px] font-mono text-white/60">
                                                <span className="w-1 h-1 bg-red-500" />
                                                {c}
                                            </li>
                                        ))}
                                    </ul>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Mandate Table */}
                    <div className="grid grid-cols-2 border border-[#2D333B] bg-[#0C0E11]">
                        {Object.entries(validationResult.mandate_summary).map(([key, val]) => (
                            <div key={key} className="flex flex-col p-4 border-r border-b border-[#2D333B]">
                                <span className="text-[9px] text-white/20 uppercase tracking-widest mb-1.5 font-bold">{key.replace(/_/g, " ")}</span>
                                <div className="flex items-center justify-between">
                                    <span className="text-white font-mono text-sm uppercase">{String(val)}</span>
                                    <ShieldCheck className="w-3.5 h-3.5 text-white/10" />
                                </div>
                            </div>
                        ))}
                    </div>

                    <div className="p-4 border border-[#2D333B] bg-[#0C0E11] flex items-start gap-4">
                        <Info className="w-4 h-4 text-white/20 shrink-0 mt-0.5" />
                        <p className="text-[10px] font-mono text-white/40 leading-relaxed uppercase">
                            Parameters confirmed. Injection into simulation loop authorized. 
                            Zero-agency violation bounds enforced.
                        </p>
                    </div>

                    <div className="flex gap-4 pt-4">
                        <button 
                            onClick={() => setValidationResult(null)} 
                            className="flex-1 h-12 border border-[#2D333B] text-[10px] font-bold text-white/40 hover:text-white uppercase tracking-widest transition-all"
                        >
                            Reset Architecture
                        </button>
                        <button 
                            onClick={handleConfirm}
                            disabled={validationResult.contradictions.length > 0 || isConfirming}
                            className="flex-[2] h-12 bg-white text-black text-[10px] font-bold uppercase tracking-[0.2em] transition-all disabled:opacity-20 flex items-center justify-center gap-2"
                        >
                            {isConfirming ? "Initializing..." : "Lock Mandate & Build"}
                        </button>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="max-w-4xl mx-auto space-y-12">
            <header className="space-y-3">
                <div className="inline-flex items-center gap-2 text-[10px] font-bold text-white/40 uppercase tracking-[0.2em]">
                    <Rocket className="w-3.5 h-3.5" />
                    Path_A :: Guided_Flow
                </div>
                <h1 className="text-2xl font-bold tracking-tight text-white uppercase tracking-[0.1em]">Construct Mandate</h1>
                <p className="text-white/40 text-[11px] font-mono uppercase">Boundaries immutable upon build initialization.</p>
            </header>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                {/* Risk Bucket */}
                <div className="space-y-4">
                    <label className="text-[10px] font-bold text-white/30 uppercase tracking-[0.3em] flex items-center gap-2">
                        <Zap className="w-3.5 h-3.5" /> Risk_Profile
                    </label>
                    <div className="grid grid-cols-1 gap-2">
                        {(["Conservative", "Moderate", "Aggressive"] as RiskTolerance[]).map((r) => (
                            <button
                                key={r}
                                onClick={() => setRisk(r)}
                                className={cn(
                                    "flex items-center justify-between p-4 border transition-all text-left",
                                    risk === r 
                                        ? "bg-white/5 border-white" 
                                        : "bg-[#111418] border-[#2D333B] hover:border-white/20"
                                )}
                            >
                                <div>
                                    <p className={cn("text-[10px] font-bold uppercase", risk === r ? "text-white" : "text-white/40")}>{r}</p>
                                    <p className="text-[9px] font-mono text-white/20 mt-1 uppercase">
                                        {r === "Conservative" ? "Preservation" : r === "Moderate" ? "Risk-Adjusted" : "Volatility_Capture"}
                                    </p>
                                </div>
                                <div className={cn("w-1 h-1", risk === r ? "bg-white" : "bg-white/5")} />
                            </button>
                        ))}
                    </div>
                </div>

                {/* Drawdown Bucket */}
                <div className="space-y-4">
                    <label className="text-[10px] font-bold text-white/30 uppercase tracking-[0.3em] flex items-center gap-2">
                        <Shield className="w-3.5 h-3.5" /> Drawdown_Limit
                    </label>
                    <div className="grid grid-cols-1 gap-2">
                        {(["Low (5%)", "Balanced (15%)", "High (30%)"] as DrawdownBucket[]).map((b) => (
                            <button
                                key={b}
                                onClick={() => setBucket(b)}
                                className={cn(
                                    "flex items-center justify-between p-4 border transition-all text-left",
                                    bucket === b 
                                        ? "bg-white/5 border-white" 
                                        : "bg-[#111418] border-[#2D333B] hover:border-white/20"
                                )}
                            >
                                <div>
                                    <p className={cn("text-[10px] font-bold uppercase", bucket === b ? "text-white" : "text-white/40")}>{b}</p>
                                    <p className="text-[9px] font-mono text-white/20 mt-1 uppercase">Hard Stop-Loss Barrier</p>
                                </div>
                                <div className={cn("w-1 h-1", bucket === b ? "bg-white" : "bg-white/5")} />
                            </button>
                        ))}
                    </div>
                </div>

                {/* Horizon Bucket */}
                <div className="space-y-4">
                    <label className="text-[10px] font-bold text-white/30 uppercase tracking-[0.3em] flex items-center gap-2">
                        <Clock className="w-3.5 h-3.5" /> Time_Horizon
                    </label>
                    <div className="grid grid-cols-1 gap-2">
                        {(["Intraday", "Swing", "Multi-Week"] as TimeHorizon[]).map((h) => (
                            <button
                                key={h}
                                onClick={() => setHorizon(h)}
                                className={cn(
                                    "flex items-center justify-between p-4 border transition-all text-left",
                                    horizon === h 
                                        ? "bg-white/5 border-white" 
                                        : "bg-[#111418] border-[#2D333B] hover:border-white/20"
                                )}
                            >
                                <div>
                                    <p className={cn("text-[10px] font-bold uppercase", horizon === h ? "text-white" : "text-white/40")}>{h}</p>
                                    <p className="text-[9px] font-mono text-white/20 mt-1 uppercase">Holding Duration Logic</p>
                                </div>
                                <div className={cn("w-1 h-1", horizon === h ? "bg-white" : "bg-white/5")} />
                            </button>
                        ))}
                    </div>
                </div>
            </div>

            <div className="space-y-4">
                <div className="flex items-center justify-between">
                    <label className="text-[10px] font-bold text-white/30 uppercase tracking-[0.3em] flex items-center gap-2">
                        <MessageSquare className="w-3.5 h-3.5" /> Strategy_Linguistic_Intent
                    </label>
                    <span className="text-[9px] text-white/20 font-mono uppercase">{rawDesire.length} :: 500 CHARS</span>
                </div>
                <div className="relative border border-[#2D333B] bg-[#111418]">
                    <textarea 
                        className="w-full h-32 bg-transparent p-6 text-[11px] font-mono text-white/60 placeholder-white/10 outline-none focus:border-white/20 transition-all resize-none"
                        placeholder="SPECIFY MANDATE PARAMETERS. E.G. CAPTURE ALPHA IN ENERGY DRIFT BUT AVOID LEVERAGE POOLS..."
                        value={rawDesire}
                        onChange={e => setRawDesire(e.target.value.slice(0, 500))}
                    />
                    <div className="absolute bottom-4 right-4 opacity-5">
                        <LineChart className="w-10 h-10 text-white" />
                    </div>
                </div>
                {!isDesireValid && (
                    <p className="text-red-900 text-[10px] font-mono uppercase tracking-widest">MIN_LENGTH_VIOLATION :: REQUIRE 10+ CHARACTERS</p>
                )}
            </div>

            <div className="pt-6 flex justify-center">
                <button 
                    disabled={!isDesireValid || isValidating}
                    onClick={handleValidate}
                    className="w-full h-14 bg-white text-black font-bold tracking-[0.3em] uppercase text-xs transition-all disabled:opacity-20 flex items-center justify-center gap-4"
                >
                    {isValidating ? (
                        <>
                            <Activity className="w-4 h-4 animate-spin" />
                            Verifying_Schema_Integrity...
                        </>
                    ) : (
                        <>
                            Initialize_Build_Mandate
                            <ChevronRight className="w-4 h-4" />
                        </>
                    )}
                </button>
            </div>

            <p className="text-center text-[9px] font-mono text-white/20 uppercase tracking-widest">
                Structural Validation (Pydantic V7) Enforcement Active.
            </p>
        </div>
    );
}

