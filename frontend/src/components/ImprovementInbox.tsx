import { Check, X, Edit, MessageSquare, ArrowRight } from "lucide-react";

export interface Proposal {
    proposal_id: string;
    target_param: string;
    current_value: any;
    proposed_value: any;
    rationale: string;
    expected_delta: {
        sharpe: string;
        alpha_pct: string;
        additional_trades: number;
    };
    risk_of_change: string;
}

interface ImprovementInboxProps {
    proposals: Proposal[];
    onApprove: (id: string) => void;
    onReject: (id: string) => void;
    onModify: (id: string) => void;
}

export function ImprovementInbox({ proposals, onApprove, onReject, onModify }: ImprovementInboxProps) {
    if (proposals.length === 0) {
        return (
            <div className="flex flex-col items-center justify-center p-8 text-muted-foreground border border-border/50 rounded-lg border-dashed">
                <MessageSquare className="w-8 h-8 mb-2 opacity-50" />
                <p className="text-sm">Inbox is empty.</p>
                <p className="text-xs mt-1">Run a Sandbox simulation to generate AI improvement proposals.</p>
            </div>
        );
    }

    return (
        <div className="space-y-4">
            {proposals.map((prop) => (
                <div key={prop.proposal_id} className="border border-purple-500/30 bg-[#16161f] rounded-lg p-4 font-mono">
                    <div className="flex items-center justify-between mb-3 border-b border-border/50 pb-2">
                        <h4 className="text-purple-400 font-bold flex items-center gap-2">
                            <ArrowRight className="w-4 h-4" />
                            Optimization Proposal
                        </h4>
                        <span className="text-xs text-muted-foreground">{prop.proposal_id}</span>
                    </div>

                    <div className="flex items-center gap-3 mb-4 bg-background/50 p-2 rounded border border-border/50 text-sm">
                        <span className="text-gray-400">{prop.target_param}:</span>
                        <span className="line-through text-red-400">{JSON.stringify(prop.current_value)}</span>
                        <ArrowRight className="w-4 h-4 text-muted-foreground" />
                        <span className="text-green-400 font-bold">{JSON.stringify(prop.proposed_value)}</span>
                    </div>

                    <div className="text-sm text-gray-300 mb-4 leading-relaxed font-sans">
                        <strong className="text-white">Rationale:</strong> {prop.rationale}
                    </div>

                    <div className="grid grid-cols-2 gap-4 mb-4 text-xs bg-background/30 p-3 rounded">
                        <div>
                            <div className="text-gray-500 uppercase tracking-wider mb-1 mt-0">Expected Delta</div>
                            <ul className="text-cyan-400 space-y-1">
                                <li>Sharpe: {prop.expected_delta.sharpe}</li>
                                <li>Alpha: {prop.expected_delta.alpha_pct}</li>
                                <li>Trades: +{prop.expected_delta.additional_trades}</li>
                            </ul>
                        </div>
                        <div>
                            <div className="text-gray-500 uppercase tracking-wider mb-1 mt-0">Risk of Change</div>
                            <div className="text-orange-300 leading-snug">{prop.risk_of_change}</div>
                        </div>
                    </div>

                    <div className="flex gap-2 pt-2 border-t border-border/40">
                        <button
                            onClick={() => onApprove(prop.proposal_id)}
                            className="flex-1 flex items-center justify-center gap-2 bg-green-500/10 hover:bg-green-500/20 text-green-400 py-1.5 rounded text-sm transition-colors border border-green-500/20"
                        >
                            <Check className="w-4 h-4" /> Approve
                        </button>
                        <button
                            onClick={() => onModify(prop.proposal_id)}
                            className="flex-1 flex items-center justify-center gap-2 bg-blue-500/10 hover:bg-blue-500/20 text-blue-400 py-1.5 rounded text-sm transition-colors border border-blue-500/20"
                        >
                            <Edit className="w-4 h-4" /> Modify
                        </button>
                        <button
                            onClick={() => onReject(prop.proposal_id)}
                            className="flex-1 flex items-center justify-center gap-2 bg-red-500/10 hover:bg-red-500/20 text-red-400 py-1.5 rounded text-sm transition-colors border border-red-500/20"
                        >
                            <X className="w-4 h-4" /> Reject
                        </button>
                    </div>
                </div>
            ))}
        </div>
    );
}
