import { useIntakeStore } from '../../../store/intakeStore';
import { Slider } from '../Slider';
import { Stepper } from '../Stepper';
import { RadioGroup } from '../RadioGroup';
import { SegmentedControl } from '../SegmentedControl';

interface SectionProps {
  onFieldFocus?: (path: string) => void;
  onFieldBlur?: () => void;
}

export function RiskMandate({ onFieldFocus, onFieldBlur }: SectionProps) {
  const schema = useIntakeStore((state) => state.schema);
  const updateField = useIntakeStore((state) => state.updateField);

  const riskConstraints = schema.risk_mandate.tier_1_risk_constraints;
  const riskContext = schema.risk_mandate.tier_2_risk_context;

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
      {/* 2.1 PRIMARY RISK GATES */}
      <div className="grid grid-cols-2 gap-10 items-start">
        <div data-field-path="risk_mandate.tier_1_risk_constraints.max_portfolio_drawdown_pct">
          <Slider
            label="Max Portfolio Drawdown"
            min={5}
            max={50}
            step={1}
            suffix="%"
            value={riskConstraints.max_portfolio_drawdown_pct}
            onChange={(val) => updateField('risk_mandate.tier_1_risk_constraints.max_portfolio_drawdown_pct', val)}
            helper="The structural limit for total peak-to-trough loss. This dictates the system's baseline volatility target."
          />
        </div>
        <div data-field-path="risk_mandate.tier_1_risk_constraints.max_daily_loss_pct">
          <Slider
            label="Max Daily Loss"
            min={1}
            max={10}
            step={0.5}
            suffix="%"
            value={riskConstraints.max_daily_loss_pct}
            onChange={(val) => updateField('risk_mandate.tier_1_risk_constraints.max_daily_loss_pct', val)}
            helper="Daily circuit breaker. Resets every market open based on starting-of-day NAV."
          />
        </div>
      </div>

      {/* 2.2 BREACH PROTOCOL */}
      <div className="space-y-4" data-field-path="risk_mandate.tier_1_risk_constraints.drawdown_breach_protocol">
        <div className="space-y-1">
          <label className="text-[0.6875rem] font-bold uppercase tracking-[0.15em] text-[#8e8e88]">
            Drawdown Breach Protocol
          </label>
          <p className="text-xs text-[#8e8e88]/60">
            Mandatory operational rule executed immediately if the maximum drawdown limit is breached.
          </p>
        </div>
        <RadioGroup
          value={riskConstraints.drawdown_breach_protocol}
          onChange={(val) => updateField('risk_mandate.tier_1_risk_constraints.drawdown_breach_protocol', val)}
          options={[
            { 
              value: 'pause_all_notify_user', 
              label: 'Pause & Notify', 
              description: 'Stop all trading activity immediately and alert the user. Requires manual restart.' 
            },
            { 
              value: 'reduce_position_sizes_50pct', 
              label: 'Liquidate 50%', 
              description: 'Immediately cut all position sizes by 50% and move to defensive posture.' 
            },
            { 
              value: 'manual_restart_required', 
              label: 'Full Shutdown', 
              description: 'Close all live positions and completely disable the pipeline until manual review.' 
            },
            { 
              value: 'reduce_and_notify', 
              label: 'Reduce & Notify', 
              description: 'De-leverage the portfolio and notify the user for a strategic review.' 
            }
          ]}
        />
      </div>

      {/* 2.3 CONCENTRATION LIMITS */}
      <div className="pt-10 border-t border-white/5 grid grid-cols-2 gap-10">
        <div className="space-y-8">
          <div data-field-path="risk_mandate.tier_1_risk_constraints.max_single_position_pct">
            <Slider
              label="Max Single Position (%)"
              min={2}
              max={25}
              step={1}
              suffix="%"
              value={riskConstraints.max_single_position_pct}
              onChange={(val) => updateField('risk_mandate.tier_1_risk_constraints.max_single_position_pct', val)}
            />
          </div>
          <div className="space-y-3" data-field-path="risk_mandate.tier_1_risk_constraints.max_single_position_usd">
            <label className="text-[0.6875rem] font-bold uppercase tracking-[0.15em] text-[#8e8e88]">
              Max Single Position (USD)
            </label>
            <div className="relative">
              <span className="absolute left-4 top-1/2 -translate-y-1/2 text-[#8e8e88] font-mono">$</span>
              <input
                type="text"
                value={riskConstraints.max_single_position_usd?.toLocaleString() || ''}
                onChange={(e) => {
                  const parsed = parseFloat(e.target.value.replace(/,/g, ''));
                  updateField('risk_mandate.tier_1_risk_constraints.max_single_position_usd', isNaN(parsed) ? null : parsed);
                }}
                placeholder="0.00"
                className="w-full bg-surface-container/50 border border-white/5 rounded-xl pl-8 pr-4 py-3 text-lg font-mono text-on-surface outline-none focus:border-secondary/30 transition-all"
              />
            </div>
          </div>
        </div>

        <div className="space-y-8">
          <div data-field-path="risk_mandate.tier_1_risk_constraints.max_sector_concentration_pct">
            <Slider
              label="Max Sector Concentration"
              min={10}
              max={60}
              step={5}
              suffix="%"
              value={riskConstraints.max_sector_concentration_pct}
              onChange={(val) => updateField('risk_mandate.tier_1_risk_constraints.max_sector_concentration_pct', val)}
            />
          </div>
          <div data-field-path="risk_mandate.tier_1_risk_constraints.max_concurrent_live_strategies">
            <Stepper
              label="Max concurrent live strategies"
              min={1}
              max={20}
              step={1}
              value={riskConstraints.max_concurrent_live_strategies}
              onChange={(val) => updateField('risk_mandate.tier_1_risk_constraints.max_concurrent_live_strategies', val)}
              helper="Maximum number of strategies running simultaneously — structural protection during market stress"
            />
          </div>
          <Slider
            label="Max ADV Exposure"
            min={1}
            max={10}
            step={0.5}
            suffix="%"
            value={riskConstraints.max_position_as_pct_of_adv}
            onChange={(val) => updateField('risk_mandate.tier_1_risk_constraints.max_position_as_pct_of_adv', val)}
            helper="Maximum position size as % of the asset's 20-day average daily volume."
          />
        </div>
      </div>

      {/* 2.4 BEHAVIORAL: REGRET ASYMMETRY */}
      <div className="pt-10 border-t border-white/5 space-y-8">
        <div className="space-y-4" data-field-path="risk_mandate.tier_2_risk_context.regret_asymmetry.type">
          <label className="text-[0.6875rem] font-bold uppercase tracking-[0.15em] text-[#8e8e88]">
            Regret Asymmetry
          </label>
          <SegmentedControl
            value={riskContext.regret_asymmetry.type}
            onChange={(val) => updateField('risk_mandate.tier_2_risk_context.regret_asymmetry.type', val)}
            options={[
              { value: 'loss_regret_dominant', label: 'Loss Dominant', description: 'Holding losers too long bothers me more' },
              { value: 'miss_regret_dominant', label: 'Miss Dominant', description: 'Selling winners too early bothers me more' },
              { value: 'balanced', label: 'Balanced', description: 'Both bother me equally' }
            ]}
          />
        </div>

        {riskContext.regret_asymmetry.type && (
          <div className="space-y-4 animate-in fade-in slide-in-from-top-2 duration-300">
            <label className="text-[0.6875rem] font-bold uppercase tracking-[0.15em] text-[#8e8e88]">
              Intensity
            </label>
            <SegmentedControl
              value={riskContext.regret_asymmetry.magnitude}
              onChange={(val) => updateField('risk_mandate.tier_2_risk_context.regret_asymmetry.magnitude', val)}
              options={[
                { value: 'mild', label: 'Mildly' },
                { value: 'moderate', label: 'Moderately' },
                { value: 'severe', label: 'Strongly' }
              ]}
            />
          </div>
        )}
      </div>
    </div>
  );
}
