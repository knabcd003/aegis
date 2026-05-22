import { useState } from 'react';
import { useIntakeStore } from '../../../store/intakeStore';
import { MultiSelectChips } from '../MultiSelectChips';
import { SegmentedControl } from '../SegmentedControl';
import { NumberInput } from '../NumberInput';
import { Toggle } from '../Toggle';
import { TickerInput } from '../TickerInput';
import { DynamicScreenBuilder } from '../DynamicScreenBuilder';
import { AlertTriangle } from 'lucide-react';

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

export function UniverseMandate({ onFieldFocus, onFieldBlur }: SectionProps) {
  const schema = useIntakeStore((state) => state.schema);
  const updateField = useIntakeStore((state) => state.updateField);
  const [sectorConflictError, setSectorConflictError] = useState<string | null>(null);

  const filters = schema.universe_mandate.tier_1_hard_filters;
  const screensConfig = schema.universe_mandate.fundamental_screens;

  // Resolve available catalysts from Section 5 (Strategy)
  const strategyCatalysts = schema.strategy_mandate?.catalyst_types || [];
  const availableCatalysts = strategyCatalysts
    .filter((c: any) => c.permitted)
    .map((c: any) => c.catalyst_type);

  const handleSectorSelect = (path: string, currentSelected: string[], targetList: string[], value: string[]) => {
    // Check if any new value exists in the other list
    const addedValue = value.find(v => !currentSelected.includes(v));
    if (addedValue && targetList.includes(addedValue)) {
      setSectorConflictError("Already in the other list — remove it there first.");
      setTimeout(() => setSectorConflictError(null), 3000);
      return;
    }
    updateField(path, value);
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
      {/* 4.1 ASSET CLASSES & GEOGRAPHIES */}
      <div className="grid grid-cols-2 gap-10">
        <div className="space-y-4" data-field-path="universe_mandate.tier_1_hard_filters.asset_classes_permitted">
          <label className="text-[0.6875rem] font-bold uppercase tracking-[0.15em] text-[#8e8e88]">
            Asset Classes Permitted
          </label>
          <MultiSelectChips
            value={filters.asset_classes_permitted}
            onChange={(val) => updateField('universe_mandate.tier_1_hard_filters.asset_classes_permitted', val)}
            options={[
              { value: 'us_equities', label: 'US Equities' },
              { value: 'etfs', label: 'ETFs' },
              { value: 'equity_options', label: 'Equity Options' },
              { value: 'us_adrs', label: 'US ADRs' },
              { value: 'canadian_equities', label: 'Canadian Equities' }
            ]}
          />
        </div>

        <div className="space-y-4" data-field-path="universe_mandate.tier_1_hard_filters.geographies_permitted">
          <label className="text-[0.6875rem] font-bold uppercase tracking-[0.15em] text-[#8e8e88]">
            Geographies Permitted
          </label>
          <MultiSelectChips
            value={filters.geographies_permitted}
            onChange={(val) => updateField('universe_mandate.tier_1_hard_filters.geographies_permitted', val)}
            options={[
              { value: 'us', label: 'United States' },
              { value: 'canada', label: 'Canada' },
              { value: 'uk', label: 'United Kingdom' },
              { value: 'eu', label: 'European Union' },
              { value: 'asia_pacific', label: 'Asia Pacific' }
            ]}
          />
        </div>
      </div>

      {/* 4.2 MARKET CAP & LIQUIDITY */}
      <div className="pt-10 border-t border-white/5 space-y-10">
        <div className="space-y-4">
          <label className="text-[0.6875rem] font-bold uppercase tracking-[0.15em] text-[#8e8e88]">
            Min Market Cap
          </label>
          <SegmentedControl
            value={filters.market_cap_min_usd?.toString() || null}
            onChange={(val) => updateField('universe_mandate.tier_1_hard_filters.market_cap_min_usd', parseInt(val))}
            options={[
              { value: '50000000', label: '$50M+', description: 'Micro / Small Cap' },
              { value: '300000000', label: '$300M+', description: 'Small / Mid Cap' },
              { value: '2000000000', label: '$2B+', description: 'Mid / Large Cap' },
              { value: '10000000000', label: '$10B+', description: 'Large Cap Only' }
            ]}
          />
        </div>

        <div className="space-y-4">
          <label className="text-[0.6875rem] font-bold uppercase tracking-[0.15em] text-[#8e8e88]">
            Max Market Cap
          </label>
          <SegmentedControl
            value={filters.market_cap_max_usd?.toString() || 'none'}
            onChange={(val) => updateField('universe_mandate.tier_1_hard_filters.market_cap_max_usd', val === 'none' ? null : parseInt(val))}
            options={[
              { value: '2000000000', label: '$2B', description: 'Up to Mid Cap' },
              { value: '10000000000', label: '$10B', description: 'Up to Large Cap' },
              { value: '50000000000', label: '$50B', description: 'Up to Mega Cap' },
              { value: 'none', label: 'No Cap', description: 'Full range' }
            ]}
          />
        </div>

        <div className="grid grid-cols-2 gap-10">
          <div className="space-y-4" data-field-path="universe_mandate.tier_1_hard_filters.min_avg_daily_volume_usd">
            <label className="text-[0.6875rem] font-bold uppercase tracking-[0.15em] text-[#8e8e88]">
              Min Avg Daily Volume (USD)
            </label>
            <SegmentedControl
              value={filters.min_avg_daily_volume_usd?.toString() || null}
              onChange={(val) => updateField('universe_mandate.tier_1_hard_filters.min_avg_daily_volume_usd', parseInt(val))}
              options={[
                { value: '500000', label: '$500K' },
                { value: '1000000', label: '$1M', description: 'Recommended' },
                { value: '2000000', label: '$2M' },
                { value: '5000000', label: '$5M' },
                { value: '10000000', label: '$10M' }
              ]}
            />
          </div>

          <NumberInput
            label="Min Price (USD)"
            value={filters.price_min_usd}
            onChange={(val) => updateField('universe_mandate.tier_1_hard_filters.price_min_usd', val)}
            prefix="$"
            subtext="Minimum stock price — filters out penny stocks and highly manipulated names."
          />
        </div>
      </div>

      {/* 4.3 SECTOR FOCUS */}
      <div className="pt-10 border-t border-white/5 space-y-8">
        <Toggle
          label="Restrict universe ONLY to selected sectors"
          value={filters.restrict_to_sectors_of_interest}
          onChange={(val) => updateField('universe_mandate.tier_1_hard_filters.restrict_to_sectors_of_interest', val)}
          helper="Off = Aegis trades any sector. On = limited to sectors selected below."
        />

        <div className="space-y-4">
          <div className="flex justify-between items-center">
            <label className="text-[0.6875rem] font-bold uppercase tracking-[0.15em] text-[#8e8e88]">
              {filters.restrict_to_sectors_of_interest ? "Permitted Sectors (hard filter)" : "Preferred Sectors (advisory)"}
            </label>
            {sectorConflictError && (
              <span className="text-[0.625rem] text-terracotta font-bold uppercase animate-pulse">
                {sectorConflictError}
              </span>
            )}
          </div>
          <MultiSelectChips
            value={filters.sectors_of_interest}
            onChange={(val) => handleSectorSelect('universe_mandate.tier_1_hard_filters.sectors_of_interest', filters.sectors_of_interest, filters.sectors_excluded, val)}
            options={GICS_SECTORS}
          />
        </div>

        <div className="space-y-4">
          <label className="text-[0.6875rem] font-bold uppercase tracking-[0.15em] text-[#8e8e88]">
            Sectors to exclude completely
          </label>
          <MultiSelectChips
            value={filters.sectors_excluded}
            onChange={(val) => handleSectorSelect('universe_mandate.tier_1_hard_filters.sectors_excluded', filters.sectors_excluded, filters.sectors_of_interest, val)}
            options={GICS_SECTORS}
          />
        </div>
      </div>

      {/* 4.4 TICKER FOCUS & EXCLUSIONS */}
      <div className="pt-10 border-t border-white/5 grid grid-cols-2 gap-10">
        <TickerInput
          label="Focus on specific tickers (optional)"
          value={filters.specific_tickers_focus}
          onChange={(val) => updateField('universe_mandate.tier_1_hard_filters.specific_tickers_focus', val)}
        />
        <TickerInput
          label="Tickers to never trade"
          value={filters.specific_tickers_exclude}
          onChange={(val) => updateField('universe_mandate.tier_1_hard_filters.specific_tickers_exclude', val)}
        />
      </div>

      {/* 4.5 ESG EXCLUSIONS */}
      <div className="pt-10 border-t border-white/5 space-y-4">
        <label className="text-[0.6875rem] font-bold uppercase tracking-[0.15em] text-[#8e8e88]">
          ESG Hard Exclusions
        </label>
        <MultiSelectChips
          value={filters.esg_hard_exclusions}
          onChange={(val) => updateField('universe_mandate.tier_1_hard_filters.esg_hard_exclusions', val)}
          options={[
            { value: 'weapons', label: 'Weapons' },
            { value: 'tobacco', label: 'Tobacco' },
            { value: 'gambling', label: 'Gambling' },
            { value: 'adult_content', label: 'Adult Content' },
            { value: 'cannabis', label: 'Cannabis' },
            { value: 'fossil_fuels', label: 'Fossil Fuels' }
          ]}
        />
      </div>

      {/* 4.6 FUNDAMENTAL SCREENS */}
      <div className="pt-10 border-t border-white/5 space-y-10">
        <Toggle
          label="Apply fundamental quality screens"
          value={screensConfig.fundamental_screens_enabled}
          onChange={(val) => updateField('universe_mandate.fundamental_screens.fundamental_screens_enabled', val)}
          helper="Filter the universe based on financial ratios and quality metrics."
        />

        {screensConfig.fundamental_screens_enabled && (
          <div className="space-y-8 animate-in fade-in slide-in-from-top-4 duration-500">
            <DynamicScreenBuilder
              screens={screensConfig.screens}
              onChange={(val) => updateField('universe_mandate.fundamental_screens.screens', val)}
              availableCatalystTypes={availableCatalysts}
            />

            {/* Validation Warnings from Agent */}
            {screensConfig.fundamental_screen_compatibility_warnings?.length > 0 && (
              <div className="space-y-2">
                {screensConfig.fundamental_screen_compatibility_warnings.map((warning: string, i: number) => (
                  <div key={i} className="p-3 bg-amber-500/10 border border-amber-500/20 rounded-xl flex items-start gap-3">
                    <AlertTriangle size={16} className="text-amber-500 mt-0.5" />
                    <p className="text-xs text-amber-500/90 leading-relaxed">{warning}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* 4.7 DETAIL BOX */}
      <div className="pt-10 border-t border-white/5 space-y-3">
        <label className="text-[0.6875rem] font-bold uppercase tracking-[0.15em] text-[#8e8e88]">
          Market Focus & Selection Thesis
        </label>
        <textarea
          value={schema.universe_mandate.universe_detail_thesis || ''}
          onChange={(e) => updateField('universe_mandate.universe_detail_thesis', e.target.value)}
          placeholder="What do you want to trade and why? Include what you know about these markets..."
          className="w-full bg-surface-container/30 border border-white/5 rounded-xl px-4 py-3 text-sm text-on-surface placeholder-[#8e8e88]/30 min-h-[120px] outline-none focus:border-secondary/30 transition-all"
        />
      </div>
    </div>
  );
}
