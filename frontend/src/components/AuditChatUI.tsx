import { useState, useRef, useEffect } from "react";
import { Send, Bot, User, MessageSquare } from "lucide-react";

interface Message {
    role: "user" | "bot";
    content: string;
}

export function AuditChatUI({ runId }: { runId: string }) {
    const [messages, setMessages] = useState<Message[]>([
        { role: "bot", content: `Audit session initialized for run: ${runId}. What would you like to know about this pipeline execution?` }
    ]);
    const [input, setInput] = useState("");
    const scrollRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [messages]);

    const handleSend = () => {
        if (!input.trim()) return;
        setMessages(prev => [...prev, { role: "user", content: input }]);
        setInput("");
        
        // Mock response
        setTimeout(() => {
            setMessages(prev => [...prev, { 
                role: "bot", 
                content: "Based on the LangGraph trace, the Risk Agent vetoed the initial setup due to VPIN threshold (0.85) being too high during the verified Bullish regime. The parameters were adjusted in node 'quant_config'." 
            }]);
        }, 1000);
    };

    return (
        <div className="flex flex-col h-full w-full bg-[#16161f] border border-border/80 rounded-lg overflow-hidden">
            <div className="bg-[#1a1a24] p-3 border-b border-border/80 flex items-center gap-2">
                <MessageSquare className="w-4 h-4 text-cyan-400" />
                <h3 className="text-sm font-bold text-gray-200">Audit Chat</h3>
                <span className="text-xs text-muted-foreground ml-auto bg-black/30 px-2 py-0.5 rounded">{runId}</span>
            </div>
            
            <div ref={scrollRef} className="flex-1 overflow-y-auto p-4 space-y-4 scrollbar-thin scrollbar-thumb-gray-700">
                {messages.map((msg, i) => (
                    <div key={i} className={`flex gap-3 ${msg.role === "user" ? "flex-row-reverse" : "flex-row"}`}>
                        <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${msg.role === "user" ? "bg-blue-600/30 text-blue-400" : "bg-purple-600/30 text-purple-400"}`}>
                            {msg.role === "user" ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
                        </div>
                        <div className={`py-2 px-3 rounded-lg max-w-[85%] text-sm ${msg.role === "user" ? "bg-blue-600/20 text-blue-100" : "bg-card border border-border/50 text-gray-300"}`}>
                            {msg.content}
                        </div>
                    </div>
                ))}
            </div>

            <div className="p-3 bg-[#1a1a24] border-t border-border/80">
                <form 
                    onSubmit={(e) => { e.preventDefault(); handleSend(); }}
                    className="flex items-center gap-2"
                >
                    <input
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        placeholder="Ask about agent reasoning..."
                        className="flex-1 bg-black/40 border border-border/80 rounded-md px-3 py-2 text-sm text-gray-200 outline-none focus:border-cyan-500/50"
                    />
                    <button 
                        type="submit"
                        className="bg-cyan-500/20 hover:bg-cyan-500/30 text-cyan-400 p-2 rounded-md transition-colors"
                    >
                        <Send className="w-4 h-4" />
                    </button>
                </form>
            </div>
        </div>
    );
}
