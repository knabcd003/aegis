import { useState } from "react";
import { Code2 } from "lucide-react";

interface ConfigEditorProps {
    initialConfig: Record<string, any>;
    onSave: (config: Record<string, any>) => void;
}

export function ConfigEditor({ initialConfig, onSave }: ConfigEditorProps) {
    const [jsonStr, setJsonStr] = useState(JSON.stringify(initialConfig, null, 4));
    const [error, setError] = useState<string | null>(null);

    const handleFormat = () => {
        try {
            const parsed = JSON.parse(jsonStr);
            setJsonStr(JSON.stringify(parsed, null, 4));
            setError(null);
            onSave(parsed);
        } catch (e: any) {
            setError(e.message);
        }
    };

    return (
        <div className="flex flex-col h-full w-full bg-[#14141b] border border-border/80 rounded-lg overflow-hidden font-mono shadow-xl text-sm">
            <div className="bg-[#1a1a24] p-3 border-b border-border/80 flex justify-between items-center">
                <div className="flex items-center gap-2 text-cyan-400">
                    <Code2 className="w-4 h-4" />
                    <span className="font-bold">parameter_config.json</span>
                </div>
                <button 
                    onClick={handleFormat}
                    className="bg-blue-500/20 hover:bg-blue-500/30 text-blue-400 px-3 py-1 rounded text-xs"
                >
                    Format & Save
                </button>
            </div>
            
            <div className="flex-1 p-2 relative">
                <textarea 
                    value={jsonStr}
                    onChange={(e) => setJsonStr(e.target.value)}
                    className="w-full h-full bg-transparent text-green-400/90 outline-none resize-none p-2 scrollbar-thin scrollbar-thumb-gray-700 font-mono"
                    spellCheck={false}
                />
                {error && (
                    <div className="absolute bottom-4 left-4 right-4 bg-red-500/10 border border-red-500/50 text-red-500 p-2 rounded text-xs break-words">
                        JSON Error: {error}
                    </div>
                )}
            </div>
        </div>
    );
}
