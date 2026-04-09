import React, { useState } from 'react';
import { useAegisStore } from '@/lib/store';
import { Rocket, FileWarning, Shield, CheckCircle } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

type DrawdownBucket = "A little (5-10%)" | "Some (10-20%)" | "A lot (20-40%)";
type RiskTolerance = "Conservative" | "Moderate" | "Aggressive";
type TimeHorizon = "Day Trading" | "Swing Trading" | "Long-term Holding";

export function IntakePathA() {
    const navigate = useNavigate();

    // Form State
    const [risk, setRisk] = useState<RiskTolerance>("Moderate");
    const [horizon, setHorizon] = useState<TimeHorizon>("Swing Trading");
    const [bucket, setBucket] = useState<DrawdownBucket | null>(null);
    const [rawDesire, setRawDesire] = useState("");
    
    // UI State
    const [isValidating, setIsValidating] = useState(false);
    const [validationResult, setValidationResult] = useState<any | null>(null);
    const [isConfirming, setIsConfirming] = useState(false);

    const isDesireSkipped = rawDesire.trim().length === 0;
    const isDesireValid = isDesireSkipped || rawDesire.trim().length >= 10;
    const isFormComplete = bucket !== null && isDesireValid;

    const handleValidate = async () => {
        setIsValidating(true);
        let max_dd = 0.15;
        if (bucket === "A little (5-10%)") max_dd = 0.05;
        if (bucket === "A lot (20-40%)") max_dd = 0.30;

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
        if (bucket === "A little (5-10%)") max_dd = 0.05;
        if (bucket === "A lot (20-40%)") max_dd = 0.30;

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
            
            // Set active Run ID in Zustand dynamically without WS for the immediate transition
            useAegisStore.setState({ active_run_id: data.workflow_id });
            
            // Route to observe to watch pipeline execution
            navigate("/command");
        } catch (err) {
            console.error(err);
        } finally {
            setIsConfirming(false);
        }
    };

    if (validationResult) {
        return (
            <div className="flex flex-col items-center justify-center p-8 bg-[#0d0d12] rounded-lg border border-border w-full max-w-2xl mx-auto">
                <Shield className="w-12 h-12 text-cyan-400 mb-4" />
                <h2 className="text-2xl font-bold text-white mb-2">Mandate Confirmation</h2>
                <p className="text-gray-400 mb-6 text-center">Aegis will cast these preferences into hard mathematical anchors. Please verify no contradictions exist.</p>
                
                <div className="w-full bg-[#1a1a24] rounded-md p-4 mb-6 border border-border">
                    {Object.entries(validationResult.mandate_summary).map(([key, val]) => (
                        <div key={key} className="flex justify-between py-2 border-b border-border/50 last:border-0 text-sm">
                            <span className="text-gray-400 uppercase tracking-widest">{key}</span>
                            <span className="text-white font-mono">{String(val)}</span>
                        </div>
                    ))}
                </div>

                {validationResult.contradictions.length > 0 && (
                    <div className="w-full bg-red-500/10 border border-red-500/30 rounded-md p-4 mb-6">
                        <div className="flex items-center gap-2 text-red-400 font-bold mb-2">
                            <FileWarning className="w-5 h-5" /> Contradictions Detected
                        </div>
                        <ul className="list-disc list-inside text-sm text-red-200/80">
                            {validationResult.contradictions.map((c: string, idx: number) => (
                                <li key={idx}>{c}</li>
                            ))}
                        </ul>
                    </div>
                )}

                <div className="flex gap-4 w-full">
                    <button onClick={() => setValidationResult(null)} className="flex-1 py-3 px-4 border border-border rounded-md text-gray-300 hover:bg-white/5 transition-colors">
                        Re-Edit
                    </button>
                    <button 
                        onClick={handleConfirm}
                        disabled={validationResult.contradictions.length > 0 || isConfirming}
                        className="flex-2 w-2/3 py-3 px-4 bg-cyan-600 hover:bg-cyan-500 text-white rounded-md font-bold tracking-widest uppercase disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                    >
                        {isConfirming ? "Spinning Up Pipeline..." : "Lock Mandate & Execute"}
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="w-full max-w-2xl mx-auto p-8 border border-border bg-[#14141b] rounded-lg">
            <h2 className="text-2xl font-semibold mb-6 flex items-center gap-2">
                <Rocket className="w-5 h-5 text-accent" />
                Intake Path A (Guided)
            </h2>
            
            <div className="space-y-8">
                {/* Drawdown Buckets */}
                <div>
                    <label className="block text-sm font-semibold uppercase tracking-wider text-muted-foreground mb-3">
                        How much can you lose before it stops being okay?
                    </label>
                    <div className="grid grid-cols-3 gap-3">
                        {(["A little (5-10%)", "Some (10-20%)", "A lot (20-40%)"] as DrawdownBucket[]).map((b) => (
                            <button
                                key={b}
                                onClick={() => setBucket(b)}
                                className={`py-3 px-4 rounded-md border text-sm transition-all ${
                                    bucket === b 
                                        ? "bg-accent/20 border-accent text-accent font-bold" 
                                        : "bg-background border-border text-gray-400 hover:bg-white/5"
                                }`}
                            >
                                {bucket === b ? "● " : "○ "} {b}
                            </button>
                        ))}
                    </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                    <div>
                        <label className="block text-sm font-semibold uppercase tracking-wider text-muted-foreground mb-2">Risk Tolerance</label>
                        <select 
                            className="w-full bg-background border border-border p-3 rounded-md text-sm text-white"
                            value={risk} onChange={e => setRisk(e.target.value as RiskTolerance)}
                        >
                            <option>Conservative</option>
                            <option>Moderate</option>
                            <option>Aggressive</option>
                        </select>
                    </div>
                    <div>
                        <label className="block text-sm font-semibold uppercase tracking-wider text-muted-foreground mb-2">Time Horizon</label>
                        <select 
                            className="w-full bg-background border border-border p-3 rounded-md text-sm text-white"
                            value={horizon} onChange={e => setHorizon(e.target.value as TimeHorizon)}
                        >
                            <option>Day Trading</option>
                            <option>Swing Trading</option>
                            <option>Long-term Holding</option>
                        </select>
                    </div>
                </div>

                <div>
                    <div className="flex justify-between items-baseline mb-2">
                        <label className="block text-sm font-semibold uppercase tracking-wider text-muted-foreground">
                            Raw Desire (Soft Intent)
                        </label>
                        <span className={`text-xs ${rawDesire.length >= 10 ? 'text-green-400' : 'text-gray-500'}`}>
                            {rawDesire.length} chars
                        </span>
                    </div>
                    <textarea 
                        className="w-full h-32 bg-background border border-border p-3 rounded-md text-sm text-gray-200 placeholder-gray-600 resize-none"
                        placeholder="e.g. Find me aerospace companies poised for a defense super-cycle..."
                        value={rawDesire}
                        onChange={e => setRawDesire(e.target.value)}
                    />
                    {!isDesireValid && !isDesireSkipped && (
                        <p className="text-red-400 text-xs mt-1">Please provide at least 10 characters, or leave completely blank to let Aegis decide.</p>
                    )}
                    {isDesireSkipped && (
                        <div className="flex items-center gap-1 mt-1 text-xs text-blue-400">
                            <CheckCircle className="w-3 h-3" /> Allowing Aegis autonomous discovery.
                        </div>
                    )}
                </div>

                <button 
                    disabled={!isFormComplete || isValidating}
                    onClick={handleValidate}
                    className="w-full py-4 bg-white hover:bg-gray-200 text-black rounded-md font-bold tracking-widest uppercase disabled:opacity-30 disabled:cursor-not-allowed transition-all"
                >
                    {isValidating ? "Validating Schema Constraints..." : "Validate Mandate"}
                </button>
            </div>
        </div>
    );
}
