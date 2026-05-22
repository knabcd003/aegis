import { useIntakeStore } from '../../../store/intakeStore';
import { WeeklyCalendarGrid } from '../WeeklyCalendarGrid';
import { Toggle } from '../Toggle';
import { SegmentedControl } from '../SegmentedControl';
import { Info } from 'lucide-react';
import { useState } from 'react';

const BROKERAGE_SUGGESTIONS = [
  'TD Ameritrade',
  'Interactive Brokers',
  'Fidelity',
  'Schwab',
  'Robinhood',
  'Webull',
  'Tastytrade',
  'Other'
];

interface SectionProps {
  onFieldFocus?: (path: string) => void;
  onFieldBlur?: () => void;
}

export function Section6_Operations({ onFieldFocus, onFieldBlur }: SectionProps) {
  const schema = useIntakeStore((state) => state.schema);
  const updateField = useIntakeStore((state) => state.updateField);
  const [showSuggestions, setShowSuggestions] = useState(false);

  const ops = schema.operational_mandate;
  const constraints = ops.tier_1_operational_constraints;
  const context = ops.tier_2_execution_context;
  const strategy = schema.strategy_mandate;

  // CROSS-SECTION WARNING
  const peadPermitted = strategy.catalyst_types.some((c: any) => c.catalyst_type === 'pead_earnings_momentum' && c.permitted);
  const showLatencyWarning = (constraints.max_execution_latency_minutes || 0) >= 90 && peadPermitted;

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
      
      {/* 6.1 EXECUTION WINDOWS */}
      <div className="space-y-6" data-field-path="operational_mandate.tier_1_operational_constraints.available_windows">
        <div className="space-y-1">
          <label className="text-[0.6875rem] font-bold uppercase tracking-[0.15em] text-[#8e8e88]">
            When can you trade?
          </label>
          <p className="text-xs text-[#8e8e88]/60 leading-relaxed">
            The system will only generate strategies you can realistically execute. Be accurate — an unexecutable strategy is worse than no strategy.
          </p>
        </div>

        <WeeklyCalendarGrid
          value={constraints.available_windows}
          onChange={(val) => updateField('operational_mandate.tier_1_operational_constraints.available_windows', val)}
        />

        <Toggle
          label="I can trade pre-market and after-hours"
          helper="Before 9:30 AM and after 4:00 PM ET"
          value={constraints.pre_post_market_capable}
          onChange={(val) => updateField('operational_mandate.tier_1_operational_constraints.pre_post_market_capable', val)}
        />
      </div>

      {/* 6.2 EXECUTION SPEED */}
      <div className="pt-10 border-t border-white/5 space-y-6" data-field-path="operational_mandate.tier_1_operational_constraints.max_execution_latency_minutes">
        <div className="space-y-1">
          <label className="text-[0.6875rem] font-bold uppercase tracking-[0.15em] text-[#8e8e88]">
            How quickly can you act on a signal?
          </label>
          <p className="text-xs text-[#8e8e88]/60">From receiving the alert to order entered.</p>
        </div>

        <SegmentedControl
          value={constraints.max_execution_latency_minutes?.toString() || null}
          onChange={(val) => updateField('operational_mandate.tier_1_operational_constraints.max_execution_latency_minutes', parseInt(val))}
          options={[
            { value: '10', label: '< 15 min', description: 'Always at your desk' },
            { value: '22', label: '15–30 min', description: 'Usually available quickly' },
            { value: '45', label: '30–60 min', description: 'Check signals periodically' },
            { value: '90', label: '1–2 hours', description: 'Limited availability' },
            { value: '150', label: '2+ hours', description: 'Check once or twice daily' }
          ]}
        />

        {showLatencyWarning && (
          <div className="p-4 bg-blue-500/10 border border-blue-500/20 rounded-xl flex items-start gap-3 animate-in fade-in duration-500">
            <Info size={18} className="text-blue-400 mt-0.5" />
            <div className="space-y-1">
              <p className="text-[0.8125rem] font-bold text-blue-400">Signal Quality Advisory</p>
              <p className="text-xs text-blue-400/80 leading-relaxed">
                At 1–2+ hour latency, PEAD strategies will use multi-day drift entries rather than breakout entries. Signal quality will be reduced.
              </p>
            </div>
          </div>
        )}
      </div>

      {/* 6.3 AUTOMATION */}
      <div className="pt-10 border-t border-white/5 space-y-6">
        <label className="text-[0.6875rem] font-bold uppercase tracking-[0.15em] text-[#8e8e88]">
          Execution mode
        </label>
        <SegmentedControl
          value={constraints.automation_level}
          onChange={(val) => updateField('operational_mandate.tier_1_operational_constraints.automation_level', val)}
          options={[
            { value: 'semi_automated_confirmation_required', label: 'Confirm Each Trade', description: 'Review and approve each signal before it executes' },
            { value: 'fully_manual', label: 'Manual Execution', description: 'Execute trades yourself from the signal card' }
          ]}
        />
      </div>

      {/* 6.4 BROKER & ORDERS */}
      <div className="pt-10 border-t border-white/5 grid grid-cols-1 md:grid-cols-2 gap-8">
        <div className="space-y-4 relative">
          <label className="text-[0.6875rem] font-bold uppercase tracking-[0.15em] text-[#8e8e88]">
            Brokerage
          </label>
          <div className="relative">
            <input
              type="text"
              value={context.brokerage || ''}
              onChange={(e) => updateField('operational_mandate.tier_2_execution_context.brokerage', e.target.value)}
              onFocus={() => setShowSuggestions(true)}
              onBlur={() => setTimeout(() => setShowSuggestions(false), 200)}
              placeholder="e.g. TD Ameritrade, Interactive Brokers"
              className="w-full bg-surface-container/30 border border-white/5 rounded-xl px-4 py-3 text-sm text-on-surface placeholder-[#8e8e88]/30 outline-none focus:border-secondary/30 transition-all"
            />
            {showSuggestions && (
              <div className="absolute z-10 w-full mt-2 bg-surface-container border border-white/10 rounded-xl shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-200">
                <div className="p-2 grid grid-cols-1 gap-1">
                  {BROKERAGE_SUGGESTIONS.map(s => (
                    <button
                      key={s}
                      onClick={() => updateField('operational_mandate.tier_2_execution_context.brokerage', s)}
                      className="text-left px-3 py-2 text-xs text-[#8e8e88] hover:text-on-surface hover:bg-white/5 rounded-lg transition-all"
                    >
                      {s}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        <div className="space-y-4">
          <label className="text-[0.6875rem] font-bold uppercase tracking-[0.15em] text-[#8e8e88]">
            Preferred order type
          </label>
          <SegmentedControl
            value={context.order_type_philosophy}
            onChange={(val) => updateField('operational_mandate.tier_2_execution_context.order_type_philosophy', val)}
            options={[
              { value: 'market_orders_acceptable', label: 'Market Orders', description: 'Immediate execution at current price' },
              { value: 'limit_orders_preferred', label: 'Limit Orders', description: 'Only fill at your specified price or better' },
              { value: 'stop_limit_preferred', label: 'Stop-Limit', description: 'Conditional limit order on price trigger' }
            ]}
          />
        </div>
      </div>

      {/* 6.5 DETAIL BOX */}
      <div className="pt-10 border-t border-white/5 space-y-3">
        <label className="text-[0.6875rem] font-bold uppercase tracking-[0.15em] text-[#8e8e88]">
          Operational Context & Constraints
        </label>
        <textarea
          value={context.execution_friction_context || ''}
          onChange={(e) => updateField('operational_mandate.tier_2_execution_context.execution_friction_context', e.target.value)}
          placeholder="When can you realistically act on a trade? Describe your available windows and any constraints — day job, travel schedule, time zones..."
          className="w-full bg-surface-container/30 border border-white/5 rounded-xl px-4 py-3 text-sm text-on-surface placeholder-[#8e8e88]/30 min-h-[150px] outline-none focus:border-secondary/30 transition-all"
        />
      </div>
    </div>
  );
}
