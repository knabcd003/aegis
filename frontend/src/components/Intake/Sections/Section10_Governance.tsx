import { useIntakeStore } from '../../../store/intakeStore';
import { DragToRankList } from '../DragToRankList';
import { SegmentedControl } from '../SegmentedControl';
import { Toggle } from '../Toggle';
import { Slider } from '../Slider';
import { Stepper } from '../Stepper';
import { CheckCircle, AlertCircle, ArrowRight } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

interface SectionProps {
  onFieldFocus?: (path: string) => void;
  onFieldBlur?: () => void;
}

export function Section10_Governance({ onFieldFocus, onFieldBlur }: SectionProps) {
  const navigate = useNavigate();
  const schema = useIntakeStore((state) => state.schema);
  const sections = useIntakeStore((state) => state.sections);
  const updateField = useIntakeStore((state) => state.updateField);

  const gov = schema.governance_and_review || {};
  const triggers = gov.review_trigger_conditions || {};
  const pauses = gov.strategy_pause_conditions || {};
  const reporting = gov.performance_reporting_frequency;
  const attribution = gov.performance_attribution_framework || {};
  
  const priorities = schema.mandate_priority_hierarchy?.ordered_priorities || [];
  const flexibility = schema.mandate_priority_hierarchy?.preference_flexibility || [];
  
  const maxDrawdown = schema.risk_mandate?.tier_1_risk_constraints?.max_portfolio_drawdown_pct;

  // Check if all 10 sections are locked for the completion banner
  const allLocked = Object.values(sections).every(s => s.locked);

  const handleAttributionChange = (key: string, val: boolean) => {
    updateField(`governance_and_review.performance_attribution_framework.${key}`, val);
  };

  const calculateDrawdownThreshold = (sliderVal: number) => {
    if (maxDrawdown === null || maxDrawdown === undefined) return null;
    return ((sliderVal / 100) * maxDrawdown).toFixed(1);
  };

  return (
    <div 
      className="space-y-12 animate-in fade-in slide-in-from-bottom-4 duration-700"
      onFocusCapture={(e) => {
        const target = e.target as HTMLElement;
        const fieldEl = target.closest('[data-field-path]');
        if (fieldEl) {
          const path = fieldEl.getAttribute('data-field-path');
          if (path && onFieldFocus) onFieldFocus(path);
        }
      }}
      onBlurCapture={() => {
        if (onFieldBlur) onFieldBlur();
      }}
    >
      
      {/* COMPLETION BANNER */}
      {allLocked && (
        <div className="p-6 bg-secondary/15 border border-secondary/30 rounded-2xl flex items-start gap-4 animate-in zoom-in-95 duration-500 shadow-lg shadow-secondary/5">
          <div className="w-12 h-12 rounded-full bg-secondary/20 flex items-center justify-center shrink-0 border border-secondary/30">
            <CheckCircle size={24} className="text-secondary" />
          </div>
          <div className="flex-1 space-y-1">
            <h3 className="font-headline text-xl font-light text-on-surface serif-text">Mandate Ready for Review</h3>
            <p className="text-sm text-[#8e8e88] leading-relaxed">
              All sections are complete. Review your mandate summary and submit when ready.
            </p>
            <div className="flex items-center gap-3 pt-3">
              <button 
                onClick={() => navigate('/intake/review')}
                className="px-4 py-2 bg-secondary/20 border border-secondary/30 text-secondary text-xs font-bold uppercase tracking-widest rounded hover:bg-secondary/30 transition-all flex items-center gap-2"
              >
                Review Summary <ArrowRight size={14} />
              </button>
              <button 
                disabled
                className="px-4 py-2 bg-white/5 border border-white/10 text-[#8e8e88] text-xs font-bold uppercase tracking-widest rounded cursor-not-allowed"
              >
                Submit Mandate
              </button>
            </div>
          </div>
        </div>
      )}

      {/* MANDATE REVIEW */}
      <div className="space-y-6" data-field-path="governance_and_review.mandate_review_frequency">
        <div className="space-y-1">
          <label className="text-[1.125rem] font-light text-on-surface serif-text">Mandate Review Frequency</label>
          <p className="text-xs text-[#8e8e88]/60">Define the cadence for comprehensive structural assessment of your mandate.</p>
        </div>
        <SegmentedControl
          value={gov.mandate_review_frequency}
          onChange={(val) => updateField('governance_and_review.mandate_review_frequency', val)}
          options={[
            { value: 'monthly', label: 'Monthly' },
            { value: 'quarterly', label: 'Quarterly', description: 'Recommended' },
            { value: 'semi_annually', label: 'Semi-Annual' },
            { value: 'annually', label: 'Annual' },
            { value: 'event_driven_only', label: 'Event-Driven', description: 'Only when triggered' }
          ]}
        />
      </div>

      {/* REVIEW TRIGGERS */}
      <div className="pt-10 border-t border-white/5 space-y-8">
        <div className="space-y-1">
          <label className="text-[0.6875rem] font-bold uppercase tracking-[0.15em] text-[#8e8e88]">
            Automatic Review Triggers
          </label>
          <p className="text-xs text-[#8e8e88]/60 italic">Conditions that force a mandatory mandate review regardless of your scheduled frequency.</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-x-12 gap-y-10">
          <div className="space-y-4">
            <Slider
              label="Drawdown review threshold"
              helper="Trigger a review when cumulative drawdown reaches this percentage of your maximum limit"
              value={triggers.drawdown_pct_of_max_triggers_review || 75}
              min={50}
              max={100}
              step={5}
              onChange={(val) => updateField('governance_and_review.review_trigger_conditions.drawdown_pct_of_max_triggers_review', val)}
            />
            <div className="p-3 rounded-lg bg-white/2 border border-white/5 text-[0.6875rem] text-[#8e8e88] font-mono uppercase tracking-wider">
              {maxDrawdown ? (
                <>At your <span className="text-secondary font-bold">{maxDrawdown}%</span> max drawdown, this triggers at <span className="text-secondary font-bold">{calculateDrawdownThreshold(triggers.drawdown_pct_of_max_triggers_review || 75)}%</span></>
              ) : (
                <span className="flex items-center gap-2 text-terracotta/70">
                  <AlertCircle size={12} />
                  Set your drawdown limit in Section 2 to see the trigger threshold
                </span>
              )}
            </div>
          </div>

          <Stepper
            label="Consecutive losses before review"
            helper="Number of consecutive losing trades that triggers a mandatory review"
            value={triggers.consecutive_losses_triggers_review || 5}
            min={3}
            max={20}
            onChange={(val) => updateField('governance_and_review.review_trigger_conditions.consecutive_losses_triggers_review', val)}
          />

          <Toggle
            label="Trigger review on significant regime change"
            helper="Immediate notification when the system detects a structural shift in market volatility or correlation"
            value={triggers.regime_change_triggers_review}
            onChange={(val) => updateField('governance_and_review.review_trigger_conditions.regime_change_triggers_review', val)}
          />

          <Stepper
            label="Capital change threshold (%)"
            helper="Trigger review if investable capital changes by more than this percentage in either direction"
            value={triggers.capital_change_pct_triggers_review || 20}
            min={10}
            max={100}
            step={5}
            onChange={(val) => updateField('governance_and_review.review_trigger_conditions.capital_change_pct_triggers_review', val)}
          />
        </div>
      </div>

      {/* STRATEGY PAUSE */}
      <div className="pt-10 border-t border-white/5 space-y-6">
        <label className="text-[0.6875rem] font-bold uppercase tracking-[0.15em] text-[#8e8e88]">
          Automatic Pause Conditions
        </label>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          <Toggle
            label="Auto-pause on drawdown breach"
            helper="Halt all new position entries when maximum drawdown is hit. Existing positions continue their exit logic."
            value={pauses.auto_pause_on_drawdown_breach !== false}
            onChange={(val) => updateField('governance_and_review.strategy_pause_conditions.auto_pause_on_drawdown_breach', val)}
          />
          <Toggle
            label="Auto-pause on market circuit breaker"
            helper="Halt new entries when a market-wide circuit breaker is triggered (S&P 7%, 13%, or 20% intraday decline)"
            value={pauses.auto_pause_on_market_circuit_breaker}
            onChange={(val) => updateField('governance_and_review.strategy_pause_conditions.auto_pause_on_market_circuit_breaker', val)}
          />
        </div>
      </div>

      {/* REPORTING */}
      <div className="pt-10 border-t border-white/5 space-y-8">
        <div className="space-y-6">
          <label className="text-[0.6875rem] font-bold uppercase tracking-[0.15em] text-[#8e8e88]">
            Performance reporting frequency
          </label>
          <SegmentedControl
            value={reporting}
            onChange={(val) => updateField('governance_and_review.performance_reporting_frequency', val)}
            options={[
              { value: 'daily', label: 'Daily' },
              { value: 'weekly', label: 'Weekly', description: 'Recommended' },
              { value: 'monthly', label: 'Monthly' }
            ]}
          />
        </div>

        <div className="space-y-4">
          <label className="text-[0.6875rem] font-bold uppercase tracking-[0.15em] text-[#8e8e88]">
            Break down performance by
          </label>
          <div className="flex flex-wrap gap-4">
            {[
              { id: 'by_catalyst_type', label: 'Catalyst Type', desc: '(PEAD vs FDA vs M&A etc.)' },
              { id: 'by_sector', label: 'Sector' },
              { id: 'by_strategy_type', label: 'Strategy Type' },
              { id: 'by_holding_period', label: 'Holding Period' }
            ].map(item => (
              <label 
                key={item.id}
                className="flex items-center gap-3 p-4 rounded-xl bg-white/2 border border-white/5 hover:bg-white/5 hover:border-white/10 transition-all cursor-pointer group"
              >
                <div className="relative flex items-center justify-center">
                  <input
                    type="checkbox"
                    className="appearance-none w-5 h-5 rounded border border-white/20 bg-surface-container checked:bg-secondary checked:border-secondary transition-all cursor-pointer"
                    checked={attribution[item.id as keyof typeof attribution] === true}
                    onChange={(e) => handleAttributionChange(item.id, e.target.checked)}
                  />
                  {attribution[item.id as keyof typeof attribution] === true && (
                    <span className="absolute text-on-secondary pointer-events-none material-symbols-outlined text-[14px] font-bold">check</span>
                  )}
                </div>
                <div className="flex flex-col">
                  <span className="text-sm font-medium text-on-surface group-hover:text-secondary transition-colors">{item.label}</span>
                  {item.desc && <span className="text-[0.625rem] text-[#8e8e88]/60 uppercase tracking-widest">{item.desc}</span>}
                </div>
              </label>
            ))}
          </div>
        </div>
      </div>

      {/* PRIORITY HIERARCHY */}
      <div className="relative pt-12">
        <div className="absolute top-12 left-0 right-0 flex items-center">
          <div className="flex-1 h-px bg-white/10"></div>
          <span className="px-4 text-[0.625rem] font-bold uppercase tracking-[0.2em] text-[#8e8e88]">Priority Hierarchy</span>
          <div className="flex-1 h-px bg-white/10"></div>
        </div>
        
        <div className="pt-12 space-y-6">
          <div className="space-y-1">
            <label className="text-[1.125rem] font-light text-on-surface serif-text">What matters most to you?</label>
            <p className="text-xs text-[#8e8e88]/60">When the system has to make trade-offs, this ranking tells it which goals to protect and which to sacrifice. Drag to reorder. Set immovable for goals that can never be compromised.</p>
          </div>
          <DragToRankList
            value={priorities}
            flexibilityValue={flexibility}
            onChange={(val) => updateField('mandate_priority_hierarchy.ordered_priorities', val)}
            onFlexibilityChange={(val) => updateField('mandate_priority_hierarchy.preference_flexibility', val)}
          />
        </div>
      </div>

      {/* DETAIL BOXES */}
      <div className="pt-10 border-t border-white/5 grid grid-cols-1 md:grid-cols-2 gap-12">
        <div className="space-y-3">
          <label className="text-[0.6875rem] font-bold uppercase tracking-[0.15em] text-[#8e8e88]">
            Trade-off philosophy
          </label>
          <p className="text-[0.625rem] text-[#8e8e88]/50 italic">In your own words — when the system has to sacrifice one thing to get another, what should guide that decision?</p>
          <textarea
            value={schema.mandate_priority_hierarchy?.trade_off_philosophy || ''}
            onChange={(e) => updateField('mandate_priority_hierarchy.trade_off_philosophy', e.target.value)}
            placeholder="e.g. Always protect capital over capturing the last 5% of a move..."
            className="w-full bg-surface-container/30 border border-white/5 rounded-xl px-4 py-3 text-sm text-on-surface placeholder-[#8e8e88]/30 min-h-[120px] outline-none focus:border-secondary/30 transition-all"
          />
        </div>

        <div className="space-y-3">
          <label className="text-[0.6875rem] font-bold uppercase tracking-[0.15em] text-[#8e8e88]">
            Mandate governance
          </label>
          <p className="text-[0.625rem] text-[#8e8e88]/50 italic">Under what conditions would you amend or shut down this mandate entirely?</p>
          <textarea
            value={gov.mandate_amendment_policy || ''}
            onChange={(e) => updateField('governance_and_review.mandate_amendment_policy', e.target.value)}
            placeholder="e.g. If strategy Sharpe falls below 0.3 over a rolling 12-month period..."
            className="w-full bg-surface-container/30 border border-white/5 rounded-xl px-4 py-3 text-sm text-on-surface placeholder-[#8e8e88]/30 min-h-[120px] outline-none focus:border-secondary/30 transition-all"
          />
        </div>
      </div>

    </div>
  );
}
