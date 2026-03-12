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
        if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }, [messages]);

    useEffect(() => {
        if (runId && runId !== prevRunRef.current) {
            prevRunRef.current = runId;
            setMessages([{
                role: "system",
                content: `Session initialized for run ${runId.slice(0, 12)}…`
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
            if (!res.ok) { const err = await res.json().catch(() => ({})); throw new Error(err.detail || `HTTP ${res.status}`); }
            const data = await res.json();
            setContextLoaded(data.context_loaded);
            setDeepTracesLoaded(data.deep_traces_loaded);
            setMessages(prev => [...prev, { role: "bot", content: data.response }]);
        } catch (e: any) {
            setMessages(prev => [...prev, { role: "system", content: `Error: ${e.message}` }]);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="flex flex-col h-full w-full overflow-hidden">
            {/* Header */}
            <div className="px-4 py-2.5 border-b border-border flex items-center gap-2 shrink-0">
                <MessageSquare className="w-4 h-4 text-accent" />
                <span className="text-xs font-semibold text-muted-foreground">Audit Chat</span>
                <span className="text-[11px] text-muted-foreground font-mono ml-auto">
                    {runId ? `${runId.slice(0, 12)}…` : "No run"}
                </span>
                {contextLoaded && <Database className="w-3 h-3 text-emerald-500" />}
                {deepTracesLoaded && <span className="text-[10px] text-violet-400">Deep</span>}
            </div>

            {/* Messages */}
            <div ref={scrollRef} className="flex-1 overflow-y-auto p-4 space-y-3 scrollbar-thin">
                {messages.length === 0 && (
                    <div className="flex h-full items-center justify-center text-sm text-muted-foreground">
                        Select a run to begin.
                    </div>
                )}
                {messages.map((msg, i) => (
                    <div key={i} className={`flex gap-2.5 ${msg.role === "user" ? "flex-row-reverse" : ""}`}>
                        <div className={`w-7 h-7 rounded-full flex items-center justify-center shrink-0 ${
                            msg.role === "user" ? "bg-accent/15 text-accent" :
                            msg.role === "system" ? "bg-amber-500/15 text-amber-500" :
                            "bg-violet-500/15 text-violet-400"
                        }`}>
                            {msg.role === "user" ? <User className="w-3.5 h-3.5" /> : <Bot className="w-3.5 h-3.5" />}
                        </div>
                        <div className={`py-2 px-3 rounded-lg max-w-[85%] text-[13px] leading-relaxed whitespace-pre-wrap ${
                            msg.role === "user" ? "bg-accent/10 text-foreground" :
                            msg.role === "system" ? "border border-amber-500/20 bg-amber-500/5 text-amber-200 text-xs font-mono" :
                            "bg-card border border-border text-foreground"
                        }`}>
                            {msg.content}
                        </div>
                    </div>
                ))}
                {isLoading && (
                    <div className="flex gap-2.5">
                        <div className="w-7 h-7 rounded-full flex items-center justify-center bg-violet-500/15 text-violet-400">
                            <Bot className="w-3.5 h-3.5" />
                        </div>
                        <div className="py-2 px-3 rounded-lg bg-card border border-border text-muted-foreground text-sm flex items-center gap-2">
                            <Loader2 className="w-3.5 h-3.5 animate-spin" />
                            Thinking…
                        </div>
                    </div>
                )}
            </div>

            {/* Input */}
            <div className="p-3 border-t border-border shrink-0">
                <div className="flex gap-1 mb-2">
                    <button onClick={() => setInput("/load_deep_traces")}
                        className="text-[10px] bg-violet-500/10 hover:bg-violet-500/20 text-violet-400 px-2 py-0.5 rounded transition-colors">
                        /load_deep_traces
                    </button>
                    <button onClick={() => setInput("/patch ")}
                        className="text-[10px] bg-amber-500/10 hover:bg-amber-500/20 text-amber-500 px-2 py-0.5 rounded transition-colors">
                        /patch
                    </button>
                </div>
                <form onSubmit={e => { e.preventDefault(); sendMessage(); }} className="flex items-center gap-2">
                    <input type="text" value={input} onChange={e => setInput(e.target.value)}
                        placeholder={runId ? "Ask about this run…" : "Select a run first"}
                        disabled={!runId || isLoading}
                        className="flex-1 bg-background border border-border rounded-lg px-3 py-2 text-sm outline-none focus:ring-1 focus:ring-accent/50 disabled:opacity-50" />
                    <button type="submit" disabled={!runId || isLoading}
                        className="bg-accent text-accent-foreground p-2 rounded-lg hover:bg-accent/90 transition-colors disabled:opacity-50">
                        <Send className="w-4 h-4" />
                    </button>
                </form>
            </div>
        </div>
    );
}
