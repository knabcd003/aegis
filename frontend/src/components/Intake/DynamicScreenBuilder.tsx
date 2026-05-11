import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';
import { X, Plus, AlertCircle } from 'lucide-react';
import type { FundamentalScreen } from '../../types/intake';
import { NumberInput } from './NumberInput';
import { MultiSelectChips } from './MultiSelectChips';

/**
 * Utility to merge tailwind classes
 */
function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

const CATALYST_TYPE_LABELS: Record<string, string> = {
  pead_earnings_momentum: "PEAD",
  fda_pdufa_biotech: "FDA/PDUFA",
  clinical_trial_readout_phase3: "Phase III",
  clinical_trial_readout_phase2: "Phase II",
  ma_announcement: "M&A",
  index_reconstitution: "Index Recon",
  management_change: "Mgmt Change",
  secondary_offering: "Secondary",
  short_squeeze_setup: "Short Squeeze",
  macro_data_surprise: "Macro",
};

const DEFAULT_CATALYST_TYPES = Object.keys(CATALYST_TYPE_LABELS);

interface DynamicScreenBuilderProps {
  screens: FundamentalScreen[];
  onChange: (screens: FundamentalScreen[]) => void;
  availableCatalystTypes?: string[];
  disabled?: boolean;
}

export function DynamicScreenBuilder({
  screens = [],
  onChange,
  availableCatalystTypes = [],
  disabled = false,
}: DynamicScreenBuilderProps) {
  
  const catalystOptions = (availableCatalystTypes.length > 0 ? availableCatalystTypes : DEFAULT_CATALYST_TYPES)
    .map(val => ({ value: val, label: CATALYST_TYPE_LABELS[val] || val }));

  const multiSelectOptions = [{ value: 'all', label: 'All' }, ...catalystOptions];

  const addScreen = () => {
    if (screens.length >= 8) return;
    const newScreen: FundamentalScreen = {
      id: crypto.randomUUID(),
      screen_type: null,
      threshold: null,
      flexibility: null,
      applies_to_catalyst_types: [],
      custom_description: null,
    };
    onChange([...screens, newScreen]);
  };

  const removeScreen = (id: string) => {
    onChange(screens.filter(s => s.id !== id));
  };

  const updateScreen = (id: string, updates: Partial<FundamentalScreen>) => {
    onChange(screens.map(s => s.id === id ? { ...s, ...updates } : s));
  };

  const getThresholdPlaceholder = (type: string | null) => {
    switch (type) {
      case 'max_debt_to_equity': return "e.g. 2.0";
      case 'max_pe_ratio': return "e.g. 30";
      case 'max_pb_ratio': return "e.g. 5";
      case 'min_revenue_growth_pct': return "e.g. 10";
      case 'min_market_cap_separate': return "e.g. 500,000,000";
      default: return "";
    }
  };

  const needsThreshold = (type: string | null) => 
    ['max_debt_to_equity', 'max_pe_ratio', 'max_pb_ratio', 'min_revenue_growth_pct', 'min_market_cap_separate'].includes(type || '');

  return (
    <div className={cn("space-y-3 w-full", disabled && "opacity-40 pointer-events-none")}>
      <div className="space-y-2">
        {screens.map((screen) => {
          const showWarning = screen.screen_type === 'profitability_required' && 
            (screen.applies_to_catalyst_types.includes('all') || 
             screen.applies_to_catalyst_types.some(t => ['fda_pdufa_biotech', 'clinical_trial_readout_phase3', 'clinical_trial_readout_phase2'].includes(t)));

          return (
            <div key={screen.id} className="group relative flex flex-col gap-4 p-4 bg-surface-container/30 border border-white/5 rounded-xl hover:border-white/10 transition-all">
              <div className="flex flex-wrap items-start gap-4">
                {/* Screen Type Dropdown */}
                <div className="w-[220px] space-y-2">
                  <label className="text-[0.625rem] font-bold uppercase tracking-widest text-[#8e8e88]/50">Screen Type</label>
                  <select
                    value={screen.screen_type || ''}
                    onChange={(e) => updateScreen(screen.id, { screen_type: e.target.value })}
                    className="w-full bg-surface-container/50 border border-white/5 rounded-lg px-3 py-2 text-sm text-on-surface outline-none focus:border-secondary/30"
                  >
                    <option value="" disabled>Select screen...</option>
                    <option value="profitability_required">Profitability Required</option>
                    <option value="revenue_positive">Revenue Positive</option>
                    <option value="positive_fcf">Positive Free Cash Flow</option>
                    <option value="max_debt_to_equity">Max Debt / Equity</option>
                    <option value="max_pe_ratio">Max P/E Ratio</option>
                    <option value="max_pb_ratio">Max P/B Ratio</option>
                    <option value="min_revenue_growth_pct">Min Revenue Growth %</option>
                    <option value="min_market_cap_separate">Min Market Cap</option>
                    <option value="custom">Custom</option>
                  </select>
                </div>

                {/* Threshold Input */}
                {needsThreshold(screen.screen_type) && (
                  <div className="w-[140px] pt-4">
                    <NumberInput
                      label=""
                      value={screen.threshold}
                      onChange={(val) => updateScreen(screen.id, { threshold: val })}
                      placeholder={getThresholdPlaceholder(screen.screen_type)}
                    />
                  </div>
                )}

                {/* Flexibility Dropdown */}
                <div className="w-[160px] space-y-2">
                  <label className="text-[0.625rem] font-bold uppercase tracking-widest text-[#8e8e88]/50">Flexibility</label>
                  <select
                    value={screen.flexibility || ''}
                    onChange={(e) => updateScreen(screen.id, { flexibility: e.target.value })}
                    className="w-full bg-surface-container/50 border border-white/5 rounded-lg px-3 py-2 text-sm text-on-surface outline-none focus:border-secondary/30"
                  >
                    <option value="" disabled>Flexibility...</option>
                    <option value="hard_filter">Hard Filter</option>
                    <option value="soft_preference">Soft Preference</option>
                    <option value="advisory_only">Advisory Only</option>
                  </select>
                </div>

                {/* Multi-Select Chips for Catalyst Types */}
                <div className="flex-1 space-y-2">
                  <label className="text-[0.625rem] font-bold uppercase tracking-widest text-[#8e8e88]/50">Applies To</label>
                  <MultiSelectChips
                    options={multiSelectOptions}
                    value={screen.applies_to_catalyst_types}
                    onChange={(val) => updateScreen(screen.id, { applies_to_catalyst_types: val })}
                  />
                </div>

                {/* Remove Button */}
                <button
                  type="button"
                  onClick={() => removeScreen(screen.id)}
                  className="mt-6 p-1.5 text-[#8e8e88]/30 hover:text-terracotta hover:bg-terracotta/10 rounded-lg transition-all"
                >
                  <X size={18} />
                </button>
              </div>

              {/* Custom Description */}
              {screen.screen_type === 'custom' && (
                <div className="w-full animate-in fade-in slide-in-from-top-1">
                   <input
                     type="text"
                     value={screen.custom_description || ''}
                     onChange={(e) => updateScreen(screen.id, { custom_description: e.target.value })}
                     placeholder="Describe your custom screen"
                     className="w-full bg-surface-container/50 border border-white/5 rounded-lg px-3 py-2 text-sm text-on-surface outline-none focus:border-secondary/30 transition-all"
                   />
                </div>
              )}

              {/* Compatibility Warning */}
              {showWarning && (
                <div className="flex gap-2 p-3 bg-amber-500/10 border border-amber-500/20 rounded-lg animate-in slide-in-from-left-2 duration-300">
                  <AlertCircle size={16} className="text-amber-500 shrink-0" />
                  <p className="text-[0.6875rem] text-amber-500/90 leading-relaxed">
                    Profitability screens applied to biotech catalyst types will produce an empty universe. 94%+ of PDUFA candidates are pre-revenue. Consider restricting to non-biotech catalyst types.
                  </p>
                </div>
              )}
            </div>
          );
        })}
      </div>

      <button
        type="button"
        disabled={screens.length >= 8 || disabled}
        onClick={addScreen}
        className="w-full py-4 rounded-xl border border-dashed border-white/10 bg-surface-container-low/20 text-[#8e8e88] hover:bg-white/5 hover:border-white/20 hover:text-on-surface transition-all flex items-center justify-center gap-2 group disabled:opacity-30"
      >
        <Plus size={18} className="group-hover:scale-110 transition-transform" />
        <span className="text-xs font-bold uppercase tracking-widest">Add Screening Rule</span>
      </button>
    </div>
  );
}
