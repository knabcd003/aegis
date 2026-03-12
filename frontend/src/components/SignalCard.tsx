import { CheckCircle2, XCircle, FileText } from "lucide-react";

export interface SignalCardData {
    card_id: string;
    sentinel_id: string;
    ticker: string;
    decision: "BUY" | "SELL";
    price: number;
    shares: number;
    timestamp: string;
    thesis: string;
    confidence: number;
    sub_agent_votes: Record<string, string>;
    quant_anchors: Record<string, string | number>;
}

interface SignalCardProps {
    signal: SignalCardData;
    onAccept: (cardId: string) => Promise<void>;
    onDecline: (cardId: string) => Promise<void>;
}

export function SignalCard({ signal, onAccept, onDecline }: SignalCardProps) {
    const isBuy = signal.decision === "BUY";

    return (
        <div className="border border-border/80 bg-[#1a1a24] rounded-lg p-5 flex flex-col gap-4 font-mono shadow-lg relative overflow-hidden">
            {/* Header */}
            <div className="flex justify-between items-start">
                <div>
                    <div className="flex items-center gap-2 mb-1">
                        <span className={`px-2 py-0.5 rounded text-xs font-bold tracking-wider ${isBuy ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'}`}>
                            {signal.decision}
                        </span>
                        <h3 className="font-bold text-lg text-white">{signal.ticker}</h3>
                    </div>
                    <div className="text-sm text-muted-foreground">
                        {signal.shares} shares @ ${signal.price.toFixed(2)} = ${(signal.shares * signal.price).toLocaleString()}
                    </div>
                </div>
                <div className="text-right text-xs text-muted-foreground">
                    <div className="uppercase tracking-wider">Confidence</div>
                    <div className="text-lg font-bold text-cyan-400">{(signal.confidence * 100).toFixed(0)}%</div>
                </div>
            </div>

            {/* Analyst Thesis */}
            <div className="bg-background/50 rounded p-3 border border-border/50">
                <div className="flex items-center gap-2 mb-2 text-primary text-xs uppercase tracking-wider font-semibold">
                    <FileText className="w-4 h-4" />
                    Analyst Thesis
                </div>
                <p className="text-sm text-gray-300 leading-relaxed font-sans">
                    "{signal.thesis}"
                </p>
            </div>

            {/* Anchors & Votes Row */}
            <div className="grid grid-cols-2 gap-4">
                {/* Quant Anchors */}
                <div>
                    <div className="text-xs uppercase tracking-wider text-muted-foreground mb-2">Quant Anchors</div>
                    <div className="space-y-1">
                        {Object.entries(signal.quant_anchors).map(([key, value]) => (
                            <div key={key} className="flex justify-between text-xs">
                                <span className="text-gray-400">{key.replace(/_/g, " ")}:</span>
                                <span className="text-blue-300 font-semibold">{value}</span>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Sub-Agent Votes */}
                <div>
                    <div className="text-xs uppercase tracking-wider text-muted-foreground mb-2">Sub-Agent Votes</div>
                    <div className="space-y-1">
                        {Object.entries(signal.sub_agent_votes).map(([agent, vote]) => (
                            <div key={agent} className="flex justify-between text-xs">
                                <span className="text-gray-400">{agent}:</span>
                                <span className={`font-semibold ${vote.includes("APPROVED") || vote.includes("BULLISH") ? 'text-green-400' : 'text-red-400'}`}>
                                    {vote} {vote.includes("APPROVED") || vote.includes("BULLISH") ? '✓' : '✗'}
                                </span>
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            {/* Actions */}
            <div className="flex gap-3 mt-2 pt-4 border-t border-border/40">
                <button
                    onClick={() => onAccept(signal.card_id)}
                    className="flex-1 flex items-center justify-center gap-2 bg-green-500/20 hover:bg-green-500/30 text-green-400 py-2 rounded-md font-bold transition-colors"
                >
                    <CheckCircle2 className="w-5 h-5" />
                    ACCEPT
                </button>
                <button
                    onClick={() => onDecline(signal.card_id)}
                    className="flex-1 flex items-center justify-center gap-2 bg-red-500/20 hover:bg-red-500/30 text-red-400 py-2 rounded-md font-bold transition-colors"
                >
                    <XCircle className="w-5 h-5" />
                    DECLINE
                </button>
            </div>
        </div>
    );
}
