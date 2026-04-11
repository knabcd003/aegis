import React, { useState } from 'react';
import { useAegisStore } from '@/lib/store';
import { 
    Code, FileWarning, Shield, Terminal, Zap, ShieldCheck, 
    Info, Check, AlertTriangle, Activity 
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { cn } from "@/lib/utils";

export function IntakePathB() {
    const navigate = useNavigate();
    
    // Form and UI State
    const [jsonInput, setJsonInput] = useState('{\n  "_schema_version": "v7.0",\n  "risk_tolerance": "moderate",\n  "max_drawdown_target": 0.15,\n  "time_horizon": "swing",\n  "raw_desire": "I am looking for macro drift in energy."\n}');
    const [syntaxError, setSyntaxError] = useState<string | null>(null);
    const [schemaErrors, setSchemaErrors] = useState<string[]>([]);
    
    const [isValidating, setIsValidating] = useState(false);
    const [validationResult, setValidationResult] = useState<any | null>(null);
    const [isConfirming, setIsConfirming] = useState(false);

    const validateJSONStructure = (): any | null => {
        setSyntaxError(null);
        setSchemaErrors([]);
        
        let parsed;
        try {
            parsed = JSON.parse(jsonInput);
        } catch (e: any) {
            setSyntaxError(`Syntax Error: ${e.message}`);
            return null;
        }

        const errors: string[] = [];
        if (parsed._schema_version !== "v7.0") errors.push("_schema_version mismatch: Expected 'v7.0'");
        if (!parsed.risk_tolerance) errors.push("Missing required: risk_tolerance");
        if (parsed.max_drawdown_target === undefined) errors.push("Missing required: max_drawdown_target");
        if (!parsed.time_horizon) errors.push("Missing required: time_horizon");
        if (!parsed.raw_desire) errors.push("Missing required: raw_desire");

        if (errors.length > 0) {
            setSchemaErrors(errors);
            return null;
        }

        return parsed;
    };

    const handleValidate = async () => {
        const parsedNode = validateJSONStructure();
        if (!parsedNode) return;
        
        setIsValidating(true);
        try {
            const res = await fetch("http://localhost:8000/api/intake/validate", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ ...parsedNode, is_path_b: true })
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
        const parsedNode = JSON.parse(jsonInput);
        try {
            const res = await fetch("http://localhost:8000/api/intake/confirm", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ ...parsedNode, is_path_b: true })
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
                            <ShieldCheck className="w-5 h-5 text-white/60" />
                        </div>
                        <div>
                            <h2 className="text-sm font-bold text-white uppercase tracking-[0.1em]">Schema Mandate Lock</h2>
                            <p className="text-[10px] text-white/40 uppercase tracking-widest font-mono mt-1">JSON-Validated_Alpha_Constraints</p>
                        </div>
                    </div>
                    <div className="flex items-center gap-2 text-[10px] font-mono text-white/40">
                        <span className="w-1.5 h-1.5 rounded-full bg-white opacity-40" />
                        EXTERNAL_SCHEMA: IMPORTED
                    </div>
                </div>

                <div className="p-8 space-y-8">
                    {validationResult.contradictions.length > 0 && (
                        <div className="border border-red-900 bg-red-950/20 p-6">
                            <div className="flex items-start gap-4">
                                <AlertTriangle className="w-5 h-5 text-red-500 shrink-0" />
                                <div>
                                    <h3 className="font-bold text-[10px] text-red-400 uppercase tracking-widest">Semantic Logic Faults</h3>
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

                    <div className="grid grid-cols-2 border border-[#2D333B] bg-[#0C0E11]">
                        {Object.entries(validationResult.mandate_summary).map(([key, val]) => (
                            <div key={key} className="flex flex-col p-4 border-r border-b border-[#2D333B]">
                                <span className="text-[9px] text-white/20 uppercase tracking-widest mb-1.5 font-bold">{key}</span>
                                <p className="text-white font-mono text-sm uppercase">{String(val)}</p>
                            </div>
                        ))}
                    </div>

                    <div className="flex gap-4 pt-4">
                        <button onClick={() => setValidationResult(null)} className="flex-1 h-12 border border-[#2D333B] text-[10px] font-bold text-white/40 hover:text-white uppercase tracking-widest transition-all">
                            Back to Editor
                        </button>
                        <button 
                            onClick={handleConfirm}
                            disabled={validationResult.contradictions.length > 0 || isConfirming}
                            className="flex-[2] h-12 bg-white text-black text-[10px] font-bold uppercase tracking-[0.2em] transition-all disabled:opacity-20 flex items-center justify-center gap-2"
                        >
                            {isConfirming ? "Committing..." : "Commit JSON Mandate"}
                        </button>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="max-w-4xl mx-auto space-y-8">
            <header className="space-y-3">
                <div className="inline-flex items-center gap-2 text-[10px] font-bold text-white/40 uppercase tracking-[0.2em]">
                    <Terminal className="w-3.5 h-3.5" />
                    Path_B :: Direct_Schema_Import
                </div>
                <h1 className="text-2xl font-bold tracking-tight text-white uppercase tracking-[0.1em]">Import Configuration</h1>
                <p className="text-white/40 text-[11px] font-mono uppercase">V7.0 JSON schema integration for external agents.</p>
            </header>
            
            <div className="border border-[#2D333B] bg-[#111418] relative overflow-hidden">
                <div className="flex items-center justify-between px-4 py-2 border-b border-[#2D333B] bg-white/5">
                    <span className="text-[10px] font-mono text-white/40 uppercase tracking-widest">aegis_mandate_v7.json</span>
                    <Code className="w-3 h-3 text-white/20" />
                </div>
                <textarea 
                    className="w-full h-[400px] bg-transparent p-6 text-[12px] font-mono text-white/60 leading-relaxed outline-none resize-none scrollbar-thin"
                    spellCheck={false}
                    value={jsonInput}
                    onChange={e => setJsonInput(e.target.value)}
                />
            </div>

            <div className="space-y-4">
                {syntaxError && (
                    <div className="p-4 border border-red-900 bg-red-950/10 text-red-400 text-[10px] font-mono uppercase tracking-widest flex items-center gap-3">
                        <AlertTriangle className="w-4 h-4 shrink-0" />
                        {syntaxError}
                    </div>
                )}
                {schemaErrors.length > 0 && (
                    <div className="p-4 border border-orange-900 bg-orange-950/10 text-orange-400 text-[10px] font-mono space-y-2 uppercase tracking-widest">
                        <p className="font-bold">Schema Faults Found:</p>
                        <ul className="space-y-1">
                            {schemaErrors.map((err, i) => <li key={i} className="flex items-center gap-2 opacity-80">
                                <span className="w-1 h-1 bg-orange-500" />
                                {err}
                            </li>)}
                        </ul>
                    </div>
                )}

                <button 
                    disabled={isValidating || jsonInput.trim() === ""}
                    onClick={handleValidate}
                    className="w-full h-14 bg-white text-black font-bold tracking-[0.3em] uppercase text-xs transition-all disabled:opacity-20 flex items-center justify-center gap-4"
                >
                    {isValidating ? (
                        <>
                            <Activity className="w-4 h-4 animate-spin" />
                            Structural Audit in Progress...
                        </>
                    ) : (
                        <>
                            <Zap className="w-4 h-4 fill-current" />
                            Parse & Validate Mandate
                        </>
                    )}
                </button>
            </div>
            
            <div className="flex items-center justify-center gap-6 text-[10px] font-mono text-white/20 uppercase tracking-widest">
                <span className="flex items-center gap-1.5"><ShieldCheck className="w-3 h-3" /> Pydantic L1</span>
                <span className="flex items-center gap-1.5"><Terminal className="w-3 h-3" /> Alpha-Strict</span>
            </div>
        </div>
    );
}

