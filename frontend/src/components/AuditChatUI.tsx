import { useState, useRef, useEffect } from "react";
import { Send, Bot, User, MessageSquare, Loader2, Database } from "lucide-react";

const API_BASE = "http://localhost:8000";

interface Message {
    role: "user" | "bot" | "system";
    content: string;
}

export function AuditChatUI({ runId }: { runId: string }) {
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [contextLoaded, setContextLoaded] = useState(false);
    const [deepTracesLoaded, setDeepTracesLoaded] = useState(false);
    const scrollRef = useRef<HTMLDivElement>(null);
    const prevRunRef = useRef<string>("");

    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [messages]);

    // Reset chat when run changes
    useEffect(() => {
        if (runId && runId !== prevRunRef.current) {
            prevRunRef.current = runId;
            setMessages([{
                role: "system",
                content: `Session initialized for run: ${runId.slice(0, 12)}… Send a message to load context and begin auditing.`
            }]);
            setContextLoaded(false);
            setDeepTracesLoaded(false);
        }
    }, [runId]);

    const sendMessage = async () => {
        if (!input.trim() || !runId || isLoading) return;
        
        const userMsg = input.trim();
        setInput("");
        setMessages(prev => [...prev, { role: "user", content: userMsg }]);
        setIsLoading(true);

        try {
            const res = await fetch(`${API_BASE}/api/audit/chat`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ run_id: runId, message: userMsg })
            });

            if (!res.ok) {
                const err = await res.json().catch(() => ({ detail: "Unknown error" }));
                throw new Error(err.detail || `HTTP ${res.status}`);
            }

            const data = await res.json();
            setContextLoaded(data.context_loaded);
            setDeepTracesLoaded(data.deep_traces_loaded);
            setMessages(prev => [...prev, { role: "bot", content: data.response }]);
        } catch (e: any) {
            setMessages(prev => [...prev, {
                role: "system",
                content: `Error: ${e.message}. Is the FastAPI server running with Ollama available?`
            }]);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="flex flex-col h-full w-full bg-[#16161f] border border-border/80 rounded-lg overflow-hidden">
            <div className="bg-[#1a1a24] p-3 border-b border-border/80 flex items-center gap-2">
                <MessageSquare className="w-4 h-4 text-cyan-400" />
                <h3 className="text-sm font-bold text-gray-200">Audit Chat</h3>
                <span className="text-xs text-muted-foreground ml-auto bg-black/30 px-2 py-0.5 rounded">
                    {runId ? `${runId.slice(0, 12)}…` : "No run selected"}
                </span>
                {contextLoaded && (
                    <span className="flex items-center gap-1 text-xs text-green-400">
                        <Database className="w-3 h-3" />
                        Context
                    </span>
                )}
                {deepTracesLoaded && (
                    <span className="text-xs text-purple-400">+ Deep</span>
                )}
            </div>
            
            <div ref={scrollRef} className="flex-1 overflow-y-auto p-4 space-y-4 scrollbar-thin scrollbar-thumb-gray-700">
                {messages.length === 0 && (
                    <div className="flex h-full items-center justify-center text-sm text-gray-500">
                        Select a run and ask a question to begin auditing.
                    </div>
                )}
                {messages.map((msg, i) => (
                    <div key={i} className={`flex gap-3 ${msg.role === "user" ? "flex-row-reverse" : "flex-row"}`}>
                        <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${
                            msg.role === "user" ? "bg-blue-600/30 text-blue-400" : 
                            msg.role === "system" ? "bg-yellow-600/30 text-yellow-400" :
                            "bg-purple-600/30 text-purple-400"
                        }`}>
                            {msg.role === "user" ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
                        </div>
                        <div className={`py-2 px-3 rounded-lg max-w-[85%] text-sm whitespace-pre-wrap ${
                            msg.role === "user" ? "bg-blue-600/20 text-blue-100" : 
                            msg.role === "system" ? "bg-yellow-500/10 border border-yellow-500/20 text-yellow-200 text-xs font-mono" :
                            "bg-card border border-border/50 text-gray-300"
                        }`}>
                            {msg.content}
                        </div>
                    </div>
                ))}
                {isLoading && (
                    <div className="flex gap-3">
                        <div className="w-8 h-8 rounded-full flex items-center justify-center bg-purple-600/30 text-purple-400">
                            <Bot className="w-4 h-4" />
                        </div>
                        <div className="py-2 px-3 rounded-lg bg-card border border-border/50 text-gray-400 text-sm flex items-center gap-2">
                            <Loader2 className="w-4 h-4 animate-spin" />
                            Auditor is thinking…
                        </div>
                    </div>
                )}
            </div>

            <div className="p-3 bg-[#1a1a24] border-t border-border/80">
                <div className="flex gap-1 mb-2">
                    <button
                        onClick={() => { setInput("/load_deep_traces"); }}
                        className="text-[10px] bg-purple-500/10 hover:bg-purple-500/20 text-purple-400 px-2 py-0.5 rounded transition-colors"
                    >
                        /load_deep_traces
                    </button>
                    <button
                        onClick={() => { setInput("/patch "); }}
                        className="text-[10px] bg-yellow-500/10 hover:bg-yellow-500/20 text-yellow-400 px-2 py-0.5 rounded transition-colors"
                    >
                        /patch
                    </button>
                </div>
                <form 
                    onSubmit={(e) => { e.preventDefault(); sendMessage(); }}
                    className="flex items-center gap-2"
                >
                    <input
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        placeholder={runId ? "Ask about agent reasoning, metrics, traces…" : "Select a run first"}
                        disabled={!runId || isLoading}
                        className="flex-1 bg-black/40 border border-border/80 rounded-md px-3 py-2 text-sm text-gray-200 outline-none focus:border-cyan-500/50 disabled:opacity-50"
                    />
                    <button 
                        type="submit"
                        disabled={!runId || isLoading}
                        className="bg-cyan-500/20 hover:bg-cyan-500/30 text-cyan-400 p-2 rounded-md transition-colors disabled:opacity-50"
                    >
                        <Send className="w-4 h-4" />
                    </button>
                </form>
            </div>
        </div>
    );
}
