import { useState, useMemo } from 'react';
import { useIntakeStore } from '../../../store/intakeStore';
import { Slider } from '../Slider';
import { SegmentedControl } from '../SegmentedControl';
import { MultiSelectChips } from '../MultiSelectChips';
import { Info } from 'lucide-react';

const GICS_SECTORS = [
  { value: 'technology', label: 'Technology' },
  { value: 'healthcare', label: 'Healthcare' },
  { value: 'financials', label: 'Financials' },
  { value: 'consumer_discretionary', label: 'Consumer Discretionary' },
  { value: 'consumer_staples', label: 'Consumer Staples' },
  { value: 'industrials', label: 'Industrials' },
  { value: 'energy', label: 'Energy' },
  { value: 'materials', label: 'Materials' },
  { value: 'real_estate', label: 'Real Estate' },
  { value: 'utilities', label: 'Utilities' },
  { value: 'communication_services', label: 'Communication Services' },
  { value: 'biotech', label: 'Biotech' }
];

interface SectionProps {
  onFieldFocus?: (path: string) => void;
  onFieldBlur?: () => void;
}

export function Section9_Macro({ onFieldFocus, onFieldBlur }: SectionProps) {
  const schema = useIntakeStore((state) => state.schema);
  const updateField = useIntakeStore((state) => state.updateField);
  const [sectorConflictError, setSectorConflictError] = useState<string | null>(null);

  const macro = schema.portfolio_scope_and_macro;
  const sophistication = schema.mandate_identification.investor_sophistication;
  const sectorsOfInterest = schema.universe_mandate.tier_1_hard_filters.sectors_of_interest || [];

  const isProfessional = ['semi_professional', 'professional'].includes(sophistication);

  const handleSectorSelect = (path: string, currentSelected: string[], otherList: string[], value: string[]) => {
    const addedValue = value.find(v => !currentSelected.includes(v));
    if (addedValue && otherList.includes(addedValue)) {
      setSectorConflictError("Already in the other list — remove it there first.");
      setTimeout(() => setSectorConflictError(null), 3000);
      return;
    }
    updateField(path, value);
  };

  const headwindConflicts = useMemo(() => {
    return macro.sectors_with_headwinds?.filter((s: any) => sectorsOfInterest.includes(s)) || [];
  }, [macro.sectors_with_headwinds, sectorsOfInterest]);

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
      
      {/* 9.1 PORTFOLIO CONTEXT */}
      <div className="space-y-12">
        {isProfessional && (
          <div className="space-y-8 animate-in fade-in slide-in-from-top-4 duration-500">
            <div className="space-y-4" data-field-path="portfolio_scope_and_macro.market_beta_intent">
              <Slider
                label="Target market beta"
                min={-1.0}
                max={2.0}
                step={0.1}
                value={macro.market_beta_intent}
                onChange={(val) => updateField('portfolio_scope_and_macro.market_beta_intent', val)}
                helper="How correlated should this mandate be to the overall market? 0 = uncorrelated, 1 = market."
              />
              <div className="flex justify-between px-1">
                {['-1.0', '0.0', '1.0', '2.0'].map((mark) => (
                  <div key={mark} className="flex flex-col items-center gap-1">
                    <div className={`w-0.5 h-1.5 ${['0.0', '1.0'].includes(mark) ? 'bg-secondary' : 'bg-white/10'}`} />
                    <span className="text-[10px] font-bold text-[#8e8e88] uppercase tracking-tighter">
                      {mark === '-1.0' ? 'Inverse' : mark === '0.0' ? 'Neutral' : mark === '1.0' ? 'Market' : '2× Beta'}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        <div className="space-y-6" data-field-path="portfolio_scope_and_macro.regime_adaptivity_intent">
          <div className="space-y-1">
            <label className="text-[0.6875rem] font-bold uppercase tracking-[0.15em] text-[#8e8e88]">
              Regime adaptivity
            </label>
            <p className="text-xs text-[#8e8e88]/60">Should the system adjust strategy selection when market conditions change?</p>
          </div>
          <SegmentedControl
            value={macro.regime_adaptivity_intent}
            onChange={(val) => updateField('portfolio_scope_and_macro.regime_adaptivity_intent', val)}
            options={[
              { value: 'adaptive_to_regime', label: 'Adaptive', description: 'Adjust strategy selection and weighting as regime shifts' },
              { value: 'strategy_consistent_regardless_of_regime', label: 'Consistent', description: 'Maintain configured approach regardless of conditions' }
            ]}
          />
        </div>
      </div>

      {/* 9.2 SECTOR VIEWS */}
      <div className="pt-10 border-t border-white/5 space-y-10">
        <div className="space-y-1">
          <label className="text-[1.125rem] font-light text-on-surface serif-text">Current Sector Views</label>
          <p className="text-xs text-[#8e8e88]/60">Your views on sector momentum bias strategy selection within permitted sectors.</p>
        </div>

        <div className="space-y-6" data-field-path="portfolio_scope_and_macro.sectors_with_tailwinds">
          <div className="flex justify-between items-center">
            <label className="text-[0.6875rem] font-bold uppercase tracking-[0.15em] text-[#8e8e88]">
              Sectors with tailwinds
            </label>
            {sectorConflictError && (
              <span className="text-[0.625rem] text-terracotta font-bold uppercase animate-pulse">
                {sectorConflictError}
              </span>
            )}
          </div>
          <MultiSelectChips
            value={macro.sectors_with_tailwinds || []}
            onChange={(val) => handleSectorSelect('portfolio_scope_and_macro.sectors_with_tailwinds', macro.sectors_with_tailwinds || [], macro.sectors_with_headwinds || [], val)}
            options={GICS_SECTORS}
          />
          <p className="text-xs text-[#8e8e88]/60 mt-1">Sectors you currently see as having positive momentum or strong fundamentals</p>
        </div>

        <div className="space-y-6" data-field-path="portfolio_scope_and_macro.sectors_with_headwinds">
          <label className="text-[0.6875rem] font-bold uppercase tracking-[0.15em] text-[#8e8e88]">
            Sectors with headwinds
          </label>
          <MultiSelectChips
            value={macro.sectors_with_headwinds || []}
            onChange={(val) => handleSectorSelect('portfolio_scope_and_macro.sectors_with_headwinds', macro.sectors_with_headwinds || [], macro.sectors_with_tailwinds || [], val)}
            options={GICS_SECTORS}
          />
          <p className="text-xs text-[#8e8e88]/60 mt-1">Sectors you currently see as facing pressure or deteriorating fundamentals</p>
          
          {headwindConflicts.length > 0 && (
            <div className="p-4 bg-blue-500/10 border border-blue-500/20 rounded-xl flex items-start gap-3 animate-in fade-in duration-500">
              <Info size={18} className="text-blue-400 mt-0.5" />
              <div className="space-y-1">
                <p className="text-[0.8125rem] font-bold text-blue-400">Sector Focus Overlap</p>
                <p className="text-xs text-blue-400/80 leading-relaxed">
                  One or more sectors you see as facing headwinds ({headwindConflicts.map((s: any) => GICS_SECTORS.find((g: any) => g.value === s)?.label).join(', ')}) are in your preferred universe from Section 4. Aria will flag this during validation.
                </p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* 9.3 DETAIL BOX */}
      <div className="pt-10 border-t border-white/5 space-y-3">
        <label className="text-[0.6875rem] font-bold uppercase tracking-[0.15em] text-[#8e8e88]">
          Current regime beliefs
        </label>
        <textarea
          value={macro.current_regime_beliefs || ''}
          onChange={(e) => updateField('portfolio_scope_and_macro.current_regime_beliefs', e.target.value)}
          placeholder="Describe your current view on market conditions..."
          className="w-full bg-surface-container/30 border border-white/5 rounded-xl px-4 py-3 text-sm text-on-surface placeholder-[#8e8e88]/30 min-h-[150px] outline-none focus:border-secondary/30 transition-all"
        />
      </div>
    </div>
  );
}
