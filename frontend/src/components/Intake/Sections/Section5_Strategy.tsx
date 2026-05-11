import { useState, useMemo } from 'react';
import { useIntakeStore } from '../../../store/intakeStore';
import { MultiSelectChips } from '../MultiSelectChips';
import { SegmentedControl } from '../SegmentedControl';
import { CatalystCardGrid } from '../CatalystCardGrid';
import { HorizonAllocationBuilder } from '../HorizonAllocationBuilder';
import { AlertTriangle, Info } from 'lucide-react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

/**
 * Utility to merge tailwind classes
 */
function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

const BIOTECH_CATALYSTS = [
  'fda_pdufa_biotech',
  'clinical_trial_readout_phase3',
  'clinical_trial_readout_phase2'
];

export function Section5_Strategy() {
  const schema = useIntakeStore((state) => state.schema);
  const updateField = useIntakeStore((state) => state.updateField);

  // Local validity states to gate the lock button in parent
  const [isCatalystValid, setIsCatalystValid] = useState(false);
  const [isHorizonValid, setIsHorizonValid] = useState(false);

  const strategy = schema.strategy_mandate;
  const universe = schema.universe_mandate;
  const capital = schema.capital_structure;

  // CROSS-SECTION WARNINGS LOGIC
  const activeBiotechCatalysts = useMemo(() => {
    return strategy.catalyst_types.filter(c => 
      c.permitted && 
      BIOTECH_CATALYSTS.includes(c.catalyst_type) &&
      Object.values(c.risk_acknowledgments).every(v => v === true)
    );
  }, [strategy.catalyst_types]);

  const hasActiveBiotech = activeBiotechCatalysts.length > 0;

  // Condition A: Biotech permitted but sector excluded
  const sectorExclusions = universe.tier_1_hard_filters.sectors_excluded || [];
  const hasSectorConflict = hasActiveBiotech && (
    sectorExclusions.includes('healthcare') || 
    sectorExclusions.includes('biotech')
  );

  // Condition B: Biotech permitted but profitability screen applied
  const screens = universe.fundamental_screens.screens || [];
  const hasProfitabilityConflict = hasActiveBiotech && screens.some(s => 
    s.screen_type === 'profitability_required' && (
      s.applies_to_catalyst_types.includes('all') ||
      s.applies_to_catalyst_types.some(t => BIOTECH_CATALYSTS.includes(t))
    )
  );

  // Condition C: Short squeeze setup but short selling disabled
  const squeezePermitted = strategy.catalyst_types.find(c => c.catalyst_type === 'short_squeeze_setup')?.permitted;
  const hasShortSellingConflict = squeezePermitted && !capital.short_selling_permitted;

  return (
    <div className="space-y-12 animate-in fade-in slide-in-from-bottom-4 duration-700">
      {/* 5.1 CATALYST TYPES */}
      <div className="space-y-6">
        <div className="space-y-1">
          <label className="text-[0.6875rem] font-bold uppercase tracking-[0.15em] text-[#8e8e88]">
            Active Catalysts
          </label>
          <p className="text-xs text-[#8e8e88]/60">
            Select the market catalysts Aegis will monitor. Each requires specific risk acknowledgment.
          </p>
        </div>
        
        <CatalystCardGrid
          value={strategy.catalyst_types}
          onChange={(val) => updateField('strategy_mandate.catalyst_types', val)}
          onValidityChange={setIsCatalystValid}
        />

        {/* CROSS-SECTION WARNINGS PANEL */}
        <div className="space-y-3">
          {hasSectorConflict && (
            <div className="p-4 bg-terracotta/10 border border-terracotta/30 rounded-xl flex items-start gap-3 animate-in shake duration-500">
              <AlertTriangle size={18} className="text-terracotta mt-0.5" />
              <div className="space-y-1">
                <p className="text-[0.8125rem] font-bold text-terracotta">Universe Conflict (Blocking)</p>
                <p className="text-xs text-terracotta/80 leading-relaxed">
                  Biotech catalyst types are enabled but healthcare/biotech is excluded from your universe in Section 4. 
                  These are mutually exclusive — resolve in Section 4.
                </p>
              </div>
            </div>
          )}

          {hasProfitabilityConflict && (
            <div className="p-4 bg-terracotta/10 border border-terracotta/30 rounded-xl flex items-start gap-3 animate-in shake duration-500">
              <AlertTriangle size={18} className="text-terracotta mt-0.5" />
              <div className="space-y-1">
                <p className="text-[0.8125rem] font-bold text-terracotta">Screening Conflict (Blocking)</p>
                <p className="text-xs text-terracotta/80 leading-relaxed">
                  A profitability screen in Section 4 applies to biotech catalyst types. 94%+ of PDUFA candidates are pre-revenue — 
                  this will produce an empty universe. Update the screen's scope in Section 4.
                </p>
              </div>
            </div>
          )}

          {hasShortSellingConflict && (
            <div className="p-4 bg-amber-500/10 border border-amber-500/20 rounded-xl flex items-start gap-3 animate-in fade-in duration-500">
              <Info size={18} className="text-amber-500 mt-0.5" />
              <div className="space-y-1">
                <p className="text-[0.8125rem] font-bold text-amber-500">Strategy Limitation</p>
                <p className="text-xs text-amber-500/80 leading-relaxed">
                  Short squeeze setups are enabled but short selling is disabled in Section 1. 
                  Only long-side squeeze strategies will be generated.
                </p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* 5.2 HORIZON ALLOCATION */}
      <div className="pt-10 border-t border-white/5 space-y-6">
        <div className="space-y-1">
          <label className="text-[0.6875rem] font-bold uppercase tracking-[0.15em] text-[#8e8e88]">
            Capital Allocation by Holding Period
          </label>
          <p className="text-xs text-[#8e8e88]/60 leading-relaxed">
            Divide your capital across holding period windows. Weights must total 100%. 
            The system optimizes exit triggers within each window.
          </p>
        </div>

        <HorizonAllocationBuilder
          value={strategy.horizon_allocation}
          onChange={(val) => updateField('strategy_mandate.horizon_allocation', val)}
          onValidityChange={setIsHorizonValid}
        />
      </div>

      {/* 5.3 STRATEGY EXCLUSIONS */}
      <div className="pt-10 border-t border-white/5 space-y-6">
        <div className="space-y-1">
          <label className="text-[0.6875rem] font-bold uppercase tracking-[0.15em] text-[#8e8e88]">
            Strategy types to never generate
          </label>
          <p className="text-xs text-[#8e8e88]/60">
            Aegis will explicitly avoid these strategy architectures regardless of signal strength.
          </p>
        </div>

        <MultiSelectChips
          value={strategy.strategy_types_excluded}
          onChange={(val) => updateField('strategy_mandate.strategy_types_excluded', val)}
          options={[
            { value: 'market_neutral', label: 'Market Neutral' },
            { value: 'long_short', label: 'Long / Short' },
            { value: 'intraday_scalping', label: 'Intraday Scalping' },
            { value: 'options_only', label: 'Options Only' },
            { value: 'pairs_trading', label: 'Pairs Trading' }
          ]}
        />
      </div>

      {/* 5.4 COMPLEXITY */}
      <div className="pt-10 border-t border-white/5 space-y-6">
        <label className="text-[0.6875rem] font-bold uppercase tracking-[0.15em] text-[#8e8e88]">
          Strategy complexity
        </label>
        <SegmentedControl
          value={strategy.tier_2_strategy_context.complexity_preference}
          onChange={(val) => updateField('strategy_mandate.tier_2_strategy_context.complexity_preference', val)}
          options={[
            { value: 'simple_rules', label: 'Simple', description: 'Clear rules, easy to understand and monitor' },
            { value: 'moderate_complexity', label: 'Moderate', description: 'Multi-factor signals with reasonable transparency' },
            { value: 'maximum_sophistication', label: 'Maximum', description: 'Full optimization, highest potential edge' }
          ]}
        />
      </div>

      {/* 5.5 DETAIL BOX */}
      <div className="pt-10 border-t border-white/5 space-y-3">
        <label className="text-[0.6875rem] font-bold uppercase tracking-[0.15em] text-[#8e8e88]">
          Strategy Philosophy & Execution Thesis
        </label>
        <textarea
          value={strategy.strategy_detail_thesis || ''}
          onChange={(e) => updateField('strategy_mandate.strategy_detail_thesis', e.target.value)}
          placeholder="How do you think about entering and exiting trades? Describe the kinds of setups you're looking for..."
          className="w-full bg-surface-container/30 border border-white/5 rounded-xl px-4 py-3 text-sm text-on-surface placeholder-[#8e8e88]/30 min-h-[150px] outline-none focus:border-secondary/30 transition-all"
        />
      </div>

      {/* INLINE VALIDATION ERRORS BEFORE LOCK */}
      <div className="pt-8 border-t border-white/5 space-y-3">
        {(!isCatalystValid) && (
          <p className="text-[0.75rem] text-terracotta font-medium">• At least one catalyst type must be fully authorized.</p>
        )}
        {(!isHorizonValid) && (
          <p className="text-[0.75rem] text-terracotta font-medium">• Capital allocation must total exactly 100%.</p>
        )}
        {(hasSectorConflict || hasProfitabilityConflict) && (
          <p className="text-[0.75rem] text-terracotta font-medium">• Resolve the conflict flagged above before locking this section.</p>
        )}
      </div>
    </div>
  );
}
