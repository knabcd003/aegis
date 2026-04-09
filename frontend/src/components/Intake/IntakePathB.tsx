import React, { useState } from 'react';
import { useAegisStore } from '@/lib/store';
import { Code, FileWarning, Shield } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

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
            setSyntaxError(`Line ${e.message.match(/at position (\d+)/)?.[1] || "Unknown"}: Invalid JSON Syntax. ${e.message}`);
            return null;
        }

        const errors: string[] = [];
        if (parsed._schema_version !== "v7.0") errors.push("_schema_version must exactly match 'v7.0'.");
        if (!parsed.risk_tolerance) errors.push("risk_tolerance is a required string.");
        if (parsed.max_drawdown_target === undefined) errors.push("max_drawdown_target is a required float.");
        if (!parsed.time_horizon) errors.push("time_horizon is a required string.");
        if (!parsed.raw_desire) errors.push("raw_desire is a required string.");

        if (errors.length > 0) {
            setSchemaErrors(errors);
            return null;
        }

        return parsed;
    };

    const handleValidate = async () => {
        const parsedNode = validateJSONStructure();
        if (!parsedNode) return; // Blocked by local Schema/Syntax
        
        setIsValidating(true);
        try {
            const res = await fetch("http://localhost:8000/api/intake/validate", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ ...parsedNode, is_path_b: true })
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
        const parsedNode = JSON.parse(jsonInput); // Guaranteed safe here
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
            <div className="flex flex-col items-center justify-center p-8 bg-[#0d0d12] rounded-lg border border-border w-full max-w-2xl mx-auto">
                <Shield className="w-12 h-12 text-cyan-400 mb-4" />
                <h2 className="text-2xl font-bold text-white mb-2">Mandate Confirmation (Path B)</h2>
                <p className="text-gray-400 mb-6 text-center">Your JSON schema was successfully parsed into the following mathematical anchors.</p>
                
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
                        Re-Edit JSON
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
        <div className="w-full max-w-3xl mx-auto p-8 border border-border bg-[#14141b] rounded-lg">
            <h2 className="text-2xl font-semibold mb-2 flex items-center gap-2">
                <Code className="w-5 h-5 text-accent" />
                Intake Path B (Power User)
            </h2>
            <p className="text-sm text-muted-foreground mb-6">
                Paste the `aegis_intake_schema.json` generated by your external LLM session here.
            </p>
            
            <div className="space-y-4">
                <div className="relative group">
                    <textarea 
                        className="w-full h-80 bg-[#0d0d12] border border-border/80 focus:border-accent p-4 rounded-md text-sm font-mono text-cyan-300/80 placeholder-gray-600 resize-y"
                        spellCheck={false}
                        value={jsonInput}
                        onChange={e => setJsonInput(e.target.value)}
                    />
                </div>

                {syntaxError && (
                    <div className="bg-red-500/10 border-l-4 border-red-500 p-3 text-red-400 text-sm font-mono">
                        {syntaxError}
                    </div>
                )}

                {schemaErrors.length > 0 && (
                    <div className="bg-orange-500/10 border-l-4 border-orange-500 p-3 text-orange-400 text-sm font-mono">
                        Schema Violations Detected:
                        <ul className="list-disc list-inside mt-1">
                            {schemaErrors.map((err, i) => <li key={i}>{err}</li>)}
                        </ul>
                    </div>
                )}

                <button 
                    disabled={isValidating || jsonInput.trim() === ""}
                    onClick={handleValidate}
                    className="w-full py-4 bg-white hover:bg-gray-200 text-black rounded-md font-bold tracking-widest uppercase disabled:opacity-30 disabled:cursor-not-allowed transition-all"
                >
                    {isValidating ? "Validating Target Schema..." : "Parse JSON Structure"}
                </button>
            </div>
        </div>
    );
}
