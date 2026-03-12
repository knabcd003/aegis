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
        <div className="space-y-3">
            {proposals.map((prop) => (
                <div key={prop.proposal_id} className="border border-violet-500/20 bg-card rounded-lg p-4">
                    <div className="flex items-center justify-between mb-3 border-b border-border pb-2">
                        <h4 className="text-violet-400 font-semibold text-sm flex items-center gap-2">
                            <ArrowRight className="w-3.5 h-3.5" />
                            Optimization Proposal
                        </h4>
                        <span className="text-[10px] text-muted-foreground font-mono">{prop.proposal_id}</span>
                    </div>

                    <div className="flex items-center gap-2 mb-3 bg-muted/40 p-2 rounded-lg border border-border text-xs font-mono">
                        <span className="text-muted-foreground">{prop.target_param}:</span>
                        <span className="line-through text-red-400">{JSON.stringify(prop.current_value)}</span>
                        <ArrowRight className="w-3 h-3 text-muted-foreground shrink-0" />
                        <span className="text-emerald-500 font-semibold">{JSON.stringify(prop.proposed_value)}</span>
                    </div>

                    <div className="text-[13px] text-foreground mb-3 leading-relaxed">
                        <strong className="text-foreground">Rationale:</strong>{" "}
                        <span className="text-muted-foreground">{prop.rationale}</span>
                    </div>

                    <div className="grid grid-cols-2 gap-3 mb-3 text-xs bg-muted/30 p-3 rounded-lg">
                        <div>
                            <div className="text-[10px] text-muted-foreground uppercase tracking-wider mb-1">Expected Delta</div>
                            <ul className="text-accent space-y-0.5">
                                <li>Sharpe: {prop.expected_delta.sharpe}</li>
                                <li>Alpha: {prop.expected_delta.alpha_pct}</li>
                                <li>Trades: +{prop.expected_delta.additional_trades}</li>
                            </ul>
                        </div>
                        <div>
                            <div className="text-[10px] text-muted-foreground uppercase tracking-wider mb-1">Risk of Change</div>
                            <div className="text-amber-500 leading-snug">{prop.risk_of_change}</div>
                        </div>
                    </div>

                    <div className="flex gap-2 pt-2 border-t border-border">
                        <button
                            onClick={() => onApprove(prop.proposal_id)}
                            className="flex-1 flex items-center justify-center gap-1.5 bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-500 py-1.5 rounded-lg text-xs font-medium transition-colors border border-emerald-500/20"
                        >
                            <Check className="w-3.5 h-3.5" /> Approve
                        </button>
                        <button
                            onClick={() => onModify(prop.proposal_id)}
                            className="flex-1 flex items-center justify-center gap-1.5 bg-accent/10 hover:bg-accent/20 text-accent py-1.5 rounded-lg text-xs font-medium transition-colors border border-accent/20"
                        >
                            <Edit className="w-3.5 h-3.5" /> Modify
                        </button>
                        <button
                            onClick={() => onReject(prop.proposal_id)}
                            className="flex-1 flex items-center justify-center gap-1.5 bg-red-500/10 hover:bg-red-500/20 text-red-400 py-1.5 rounded-lg text-xs font-medium transition-colors border border-red-500/20"
                        >
                            <X className="w-3.5 h-3.5" /> Reject
                        </button>
                    </div>
                </div>
            ))}
        </div>
    );
}
