import React, { useState } from 'react';
import { CheckCircle2, XCircle, FileText, Anchor, HelpCircle, Copy, CheckCircle, RefreshCcw } from "lucide-react";
import { useSignalFreshness } from '@/lib/useSignalFreshness';

export interface SignalCardData {
    card_id: string;
    sentinel_id: string;
    ticker: string;
    decision: "BUY" | "SELL" | "CLOSE";
    price: number;
    shares: number;
    timestamp: string;
    thesis: string;
    confidence: number;
    target_price?: number;
    stop_loss_price?: number;
    sub_agent_votes: Record<string, string>;
    quant_anchors: Record<string, string | number>;
    
    // V7 specific keys
    session_quality?: "nominal" | "degraded" | "severely_degraded";
    volatility_bucket?: "low_volatility" | "medium_volatility" | "high_volatility" | "speculative";
    bull_evidentiary_score?: number;
    bear_evidentiary_score?: number;
}

interface SignalCardProps {
    signal: SignalCardData;
    onAccept: (cardId: string) => Promise<void>;
    onDecline: (cardId: string) => Promise<void>;
}

export function SignalCard({ signal, onAccept, onDecline }: SignalCardProps) {
    const isBuy = signal.decision === "BUY";
    const { freshnessState, isLoading } = useSignalFreshness(
        signal.card_id, 
        signal.volatility_bucket || "medium_volatility"
    );
    
    const [copied, setCopied] = useState(false);

    const handleCopyExecution = () => {
        const costBasis = (signal.shares * signal.price).toFixed(2);
        const text = `ACTION: ${signal.decision}
TICKER: ${signal.ticker}
SHARES: ${signal.shares}
LIMIT PRICE: $${signal.price.toFixed(2)}
TARGET PRICE: ${signal.target_price ? '$' + signal.target_price.toFixed(2) : 'NONE'}
STOP LOSS: ${signal.stop_loss_price ? '$' + signal.stop_loss_price.toFixed(2) : 'NONE'}
EST TOTAL COST: $${costBasis}`;
        
        navigator.clipboard.writeText(text);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    const isDegraded = signal.session_quality && signal.session_quality !== "nominal";
    
    // Freshness guardrails
    const acceptEnabled = freshnessState?.accept_enabled ?? false;
    const failureReason = freshnessState?.failure_reason;

    return (
        <div className={`border bg-[#1a1a24] rounded-lg p-5 flex flex-col gap-4 font-mono shadow-lg relative overflow-hidden transition-colors ${isDegraded ? 'border-amber-500/50' : 'border-border/80'}`}>
            
            {/* Degraded Session Banner overlay */}
            {isDegraded && (
                <div className="absolute top-0 left-0 w-full bg-amber-500/20 text-amber-400 text-[10px] text-center font-bold tracking-widest py-0.5 border-b border-amber-500/30">
                    DEGRADED SESSION DETECTED — ELEVATED RISK
                </div>
            )}
            
            {/* Header */}
            <div className={`flex justify-between items-start ${isDegraded ? 'mt-3' : ''}`}>
                <div>
                    <div className="flex items-center gap-2 mb-1">
                        <span className={`px-2 py-0.5 rounded text-xs font-bold tracking-wider ${isBuy ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'}`}>
                            {signal.decision}
                        </span>
                        <h3 className="font-bold text-lg text-white">{signal.ticker}</h3>
                        
                        {/* Live Price Fetching Display */}
                        {freshnessState && (
                            <span className="flex items-center gap-1 text-xs text-muted-foreground ml-2 px-1.5 py-0.5 bg-background rounded-sm">
                                <RefreshCcw className="w-3 h-3 animate-spin text-blue-400" />
                                Live: ${freshnessState.current_price?.toFixed(2) || "---"}
                                {freshnessState.price_deviation_pct != null && (
                                    <span className={freshnessState.is_fresh ? "text-green-400 font-bold" : "text-amber-400 font-bold"}>
                                        ({(freshnessState.price_deviation_pct * 100).toFixed(2)}%)
                                    </span>
                                )}
                            </span>
                        )}
                    </div>
                    <div className="text-sm text-muted-foreground">
                        {signal.shares} shares @ ${signal.price.toFixed(2)} = ${(signal.shares * signal.price).toLocaleString()}
                    </div>
                </div>
                
                <div className="flex gap-4">
                    {/* FinDebate Evidentiary Scores */}
                    {signal.bull_evidentiary_score !== undefined && (
                        <div className="text-right text-xs text-muted-foreground hidden sm:block">
                            <div className="uppercase tracking-wider">Evidentiary</div>
                            <div className="flex gap-2 text-sm mt-0.5">
                                <span className="text-green-400" title="Bull Evidentiary">
                                    {(signal.bull_evidentiary_score * 100).toFixed(0)}%
                                </span>
                                <span className="text-red-400" title="Bear Evidentiary">
                                    {(signal.bear_evidentiary_score! * 100).toFixed(0)}%
                                </span>
                            </div>
                        </div>
                    )}
                    
                    <div className="text-right text-xs text-muted-foreground">
                        <div className="uppercase tracking-wider">Confidence</div>
                        <div className="text-lg font-bold text-cyan-400">{(signal.confidence * 100).toFixed(0)}%</div>
                    </div>
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
            
            {/* Formatted Copy Block */}
            <div className="bg-slate-950/80 rounded border border-slate-800 p-3 relative group">
                <div className="text-[10px] text-slate-500 uppercase tracking-widest mb-1.5 font-bold">Execution Block Setup</div>
                <pre className="text-xs text-blue-300 font-mono leading-tight">
                    ACTION: {signal.decision}{"\n"}
                    TICKER: {signal.ticker}{"\n"}
                    SHARES: {signal.shares}{"\n"}
                    LIMIT PRICE: ${signal.price.toFixed(2)}{"\n"}
                    TARGET PRICE: {signal.target_price ? '$' + signal.target_price.toFixed(2) : 'NONE'}{"\n"}
                    STOP LOSS: {signal.stop_loss_price ? '$' + signal.stop_loss_price.toFixed(2) : 'NONE'}{"\n"}
                    EST TOTAL COST: ${(signal.shares * signal.price).toFixed(2)}
                </pre>
                
                <button 
                    onClick={handleCopyExecution}
                    className="absolute top-3 right-3 p-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded transition-colors"
                    title="Copy Execution Details"
                >
                    {copied ? <CheckCircle className="w-4 h-4 text-green-400" /> : <Copy className="w-4 h-4" />}
                </button>
            </div>

            {/* Anchors & Votes Row */}
            <div className="grid grid-cols-2 gap-4">
                <div>
                    <div className="text-xs uppercase tracking-wider text-muted-foreground mb-2 flex items-center gap-1">
                        <Anchor className="w-3 h-3" /> Quant Anchors
                    </div>
                    <div className="space-y-1">
                        {Object.entries(signal.quant_anchors).map(([key, value]) => (
                            <div key={key} className="flex justify-between text-xs">
                                <span className="text-gray-400">{key.replace(/_/g, " ")}:</span>
                                <span className="text-blue-300 font-semibold">{value}</span>
                            </div>
                        ))}
                    </div>
                </div>

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
            <div className="flex gap-3 mt-2 pt-4 border-t border-border/40 relative">
                <div className="flex-1 relative group w-full">
                    <button
                        onClick={() => onAccept(signal.card_id)}
                        disabled={!acceptEnabled || isLoading}
                        className={`w-full flex items-center justify-center gap-2 py-2 rounded-md font-bold transition-colors ${
                            !acceptEnabled 
                            ? 'bg-slate-800/50 text-slate-500 cursor-not-allowed border border-slate-800' 
                            : 'bg-green-500/20 hover:bg-green-500/30 text-green-400'
                        }`}
                    >
                        <CheckCircle2 className="w-5 h-5" />
                        {isLoading ? "VERIFYING FRESHNESS..." : "ACCEPT"}
                    </button>
                    
                    {/* Failure Tooltip via Group Hover */}
                    {!acceptEnabled && !isLoading && (
                        <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-max max-w-xs p-2 bg-slate-900 border border-red-500/50 rounded shadow-2xl text-xs text-red-300 flex opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-10 flex-col items-center">
                            <div className="flex items-center gap-1 font-bold mb-1">
                                <HelpCircle className="w-3 h-3" />
                                EXECUTION LOCKED
                            </div>
                            <span>Reason: {failureReason?.toUpperCase().replace(/_/g, " ")}</span>
                        </div>
                    )}
                </div>
                
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
