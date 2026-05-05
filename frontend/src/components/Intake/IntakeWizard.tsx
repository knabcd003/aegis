import React from 'react';

interface IntakeWizardProps {
  stage: number;
  schemaWip: any;
  onUpdate: (patch: any) => void;
  onNext: () => void;
}

const STAGE_TITLES: Record<number, string> = {
  1: "Foundation: Capital & Account",
  2: "Risk Profile & Drawdown",
  3: "Performance Targets & Horizon",
  4: "Universe & Strategy Intent",
  5: "Execution & Constraints",
  6: "Priority & Trade-offs",
  7: "Synthesis & Review"
};

export function IntakeWizard({ stage, schemaWip, onUpdate, onNext }: IntakeWizardProps) {
  if (!schemaWip) return <div className="p-6 text-[#8e8e88]">Loading schema...</div>;

  const handleChange = (path: string[], value: any) => {
    // Basic deep patch builder
    let patch: any = {};
    let current = patch;
    for (let i = 0; i < path.length - 1; i++) {
      current[path[i]] = {};
      current = current[path[i]];
    }
    current[path[path.length - 1]] = value;
    onUpdate(patch);
  };

  const renderStage = () => {
    switch (stage) {
      case 1:
        return (
          <div className="space-y-4">
            <div>
              <label className="block text-[0.6875rem] font-bold uppercase tracking-widest text-on-surface-variant mb-1">Investable Capital ($)</label>
              <input 
                type="number" 
                value={schemaWip.mandate_hard_constraints?.investable_capital || ''}
                onChange={e => handleChange(['mandate_hard_constraints', 'investable_capital'], parseFloat(e.target.value) || null)}
                className="w-full bg-surface-container border border-white/5 rounded-lg px-4 py-3 text-[0.8125rem] text-on-surface focus:outline-none focus:ring-1 focus:ring-primary/50"
                placeholder="e.g. 500000"
              />
            </div>
            <div>
              <label className="block text-[0.6875rem] font-bold uppercase tracking-widest text-on-surface-variant mb-1">Account Type</label>
              <input 
                type="text" 
                value={schemaWip.mandate_hard_constraints?.account_type || ''}
                onChange={e => handleChange(['mandate_hard_constraints', 'account_type'], e.target.value)}
                className="w-full bg-surface-container border border-white/5 rounded-lg px-4 py-3 text-[0.8125rem] text-on-surface focus:outline-none focus:ring-1 focus:ring-primary/50"
                placeholder="e.g. Margin, IRA, Cash"
              />
            </div>
          </div>
        );
      case 2:
        return (
          <div className="space-y-4">
            <div>
              <label className="block text-[0.6875rem] font-bold uppercase tracking-widest text-on-surface-variant mb-1">Max Portfolio Drawdown (%)</label>
              <input 
                type="number" step="0.01"
                value={schemaWip.mandate_hard_constraints?.max_portfolio_drawdown_pct || ''}
                onChange={e => handleChange(['mandate_hard_constraints', 'max_portfolio_drawdown_pct'], parseFloat(e.target.value) || null)}
                className="w-full bg-surface-container border border-white/5 rounded-lg px-4 py-3 text-[0.8125rem] text-on-surface"
                placeholder="e.g. 0.15 for 15%"
              />
            </div>
            <div>
              <label className="block text-[0.6875rem] font-bold uppercase tracking-widest text-on-surface-variant mb-1">Volatility Tolerance</label>
              <input 
                type="text" 
                value={schemaWip.risk_profile?.volatility_tolerance || ''}
                onChange={e => handleChange(['risk_profile', 'volatility_tolerance'], e.target.value)}
                className="w-full bg-surface-container border border-white/5 rounded-lg px-4 py-3 text-[0.8125rem] text-on-surface"
                placeholder="e.g. High, Medium, Low"
              />
            </div>
          </div>
        );
      case 3:
        return (
          <div className="space-y-4">
            <div>
              <label className="block text-[0.6875rem] font-bold uppercase tracking-widest text-on-surface-variant mb-1">Target Annual Return (%)</label>
              <input 
                type="number" step="0.01"
                value={schemaWip.performance_targets?.target_annual_return_pct || ''}
                onChange={e => handleChange(['performance_targets', 'target_annual_return_pct'], parseFloat(e.target.value) || null)}
                className="w-full bg-surface-container border border-white/5 rounded-lg px-4 py-3 text-[0.8125rem] text-on-surface"
                placeholder="e.g. 0.30 for 30%"
              />
            </div>
          </div>
        );
      case 4:
        return (
          <div className="space-y-4">
            <div>
              <label className="block text-[0.6875rem] font-bold uppercase tracking-widest text-on-surface-variant mb-1">Raw Desire / Universe</label>
              <textarea 
                rows={3}
                value={schemaWip.universe_mandate?.raw_desire || ''}
                onChange={e => handleChange(['universe_mandate', 'raw_desire'], e.target.value)}
                className="w-full bg-surface-container border border-white/5 rounded-lg px-4 py-3 text-[0.8125rem] text-on-surface resize-none"
                placeholder="e.g. I want to trade tech momentum..."
              />
            </div>
            <div>
              <label className="block text-[0.6875rem] font-bold uppercase tracking-widest text-on-surface-variant mb-1">Catalyst Preferences</label>
              <input 
                type="text" 
                value={schemaWip.strategy_intent?.catalyst_preferences || ''}
                onChange={e => handleChange(['strategy_intent', 'catalyst_preferences'], e.target.value)}
                className="w-full bg-surface-container border border-white/5 rounded-lg px-4 py-3 text-[0.8125rem] text-on-surface"
                placeholder="e.g. Earnings, breakouts, macro"
              />
            </div>
          </div>
        );
      case 5:
        return (
          <div className="space-y-4">
            <div>
              <label className="block text-[0.6875rem] font-bold uppercase tracking-widest text-on-surface-variant mb-1">Max Concurrent Live Strategies</label>
              <input 
                type="number"
                value={schemaWip.mandate_hard_constraints?.max_concurrent_live_strategies || ''}
                onChange={e => handleChange(['mandate_hard_constraints', 'max_concurrent_live_strategies'], parseInt(e.target.value) || null)}
                className="w-full bg-surface-container border border-white/5 rounded-lg px-4 py-3 text-[0.8125rem] text-on-surface"
                placeholder="e.g. 5"
              />
            </div>
          </div>
        );
      case 6:
        return (
          <div className="space-y-4">
            <div>
              <label className="block text-[0.6875rem] font-bold uppercase tracking-widest text-on-surface-variant mb-1">Priority Trade-offs</label>
              <textarea 
                rows={3}
                value={schemaWip.mandate_priority_hierarchy?.conflict_notes || ''}
                onChange={e => handleChange(['mandate_priority_hierarchy', 'conflict_notes'], e.target.value)}
                className="w-full bg-surface-container border border-white/5 rounded-lg px-4 py-3 text-[0.8125rem] text-on-surface resize-none"
                placeholder="e.g. Prioritize risk management over returns..."
              />
            </div>
          </div>
        );
      case 7:
        return (
          <div className="space-y-4">
            <p className="text-[0.8125rem] text-[#8e8e88] leading-relaxed">
              You have completed all stages. Review your mandate schema below or click "Lock Mandate" to finish.
            </p>
            <div className="bg-surface-container rounded-lg p-4 font-mono text-[0.6875rem] text-on-surface h-48 overflow-y-auto">
              {JSON.stringify(schemaWip, null, 2)}
            </div>
          </div>
        );
      default:
        return null;
    }
  };

  return (
    <div className="bg-surface-container-low border border-white/5 rounded-xl flex flex-col h-[500px]">
      <div className="p-6 border-b border-white/5">
        <div className="flex justify-between items-center mb-2">
          <h2 className="font-headline text-2xl font-light tracking-tight text-on-surface">
            Stage {stage}: {STAGE_TITLES[stage] || "Initialization"}
          </h2>
          <span className="text-[0.6875rem] font-bold text-[#8e8e88]">{stage}/7</span>
        </div>
        <div className="w-full bg-surface-container h-1.5 rounded-full overflow-hidden">
          <div 
            className="bg-primary h-full transition-all duration-300"
            style={{ width: `${(stage / 7) * 100}%` }}
          />
        </div>
      </div>
      
      <div className="flex-1 overflow-y-auto p-6">
        {renderStage()}
      </div>
      
      <div className="p-4 border-t border-white/5 flex justify-end">
        <button 
          onClick={onNext}
          className="px-6 py-2.5 bg-primary-container text-on-primary-container text-[0.8125rem] font-semibold rounded-lg hover:brightness-110 transition-all flex items-center gap-2"
        >
          {stage === 7 ? 'Lock Mandate' : 'Next Stage'}
          <span className="material-symbols-outlined text-[18px]">
            {stage === 7 ? 'check_circle' : 'arrow_forward'}
          </span>
        </button>
      </div>
    </div>
  );
}
