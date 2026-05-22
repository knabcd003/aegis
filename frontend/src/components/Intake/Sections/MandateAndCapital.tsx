import { useState, useCallback } from 'react';
import { useIntakeStore } from '../../../store/intakeStore';
import { SegmentedControl } from '../SegmentedControl';
import { Slider } from '../Slider';
import { Toggle } from '../Toggle';

interface SectionProps {
  onFieldFocus?: (path: string) => void;
  onFieldBlur?: () => void;
}

export function MandateAndCapital({ onFieldFocus, onFieldBlur }: SectionProps) {
  const schema = useIntakeStore((state) => state.schema);
  const updateField = useIntakeStore((state) => state.updateField);

  // Local state for capital input to avoid cursor-jump from format-on-render
  const [capitalRaw, setCapitalRaw] = useState<string>(
    schema.capital_structure.investable_capital_usd != null
      ? String(schema.capital_structure.investable_capital_usd)
      : ''
  );
  const [capitalFocused, setCapitalFocused] = useState(false);

  const handleCapitalFocus = useCallback(() => {
    setCapitalFocused(true);
    // Show raw number (strip commas if any)
    setCapitalRaw((prev) => prev.replace(/,/g, ''));
  }, []);

  const handleCapitalBlur = useCallback(() => {
    setCapitalFocused(false);
    const num = parseFloat(capitalRaw.replace(/,/g, ''));
    if (!isNaN(num)) {
      updateField('capital_structure.investable_capital_usd', num);
      setCapitalRaw(num.toLocaleString());
    } else {
      setCapitalRaw('');
      updateField('capital_structure.investable_capital_usd', null);
    }
  }, [capitalRaw, updateField]);

  const handleCapitalChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setCapitalRaw(e.target.value);
  }, []);

  // Ticker input blur handler — split by comma, trim, uppercase, filter empty, write array
  const handleTickerBlur = useCallback((path: string, raw: string) => {
    const tickers = raw
      .split(',')
      .map((t) => t.trim().toUpperCase())
      .filter(Boolean);
    updateField(path, tickers);
  }, [updateField]);

  return (
    <div 
      className="space-y-10 animate-in fade-in slide-in-from-bottom-4 duration-700"
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
      {/* 1.1 INVESTOR SOPHISTICATION */}
      <div className="space-y-4" data-field-path="mandate_identification.investor_sophistication">
        <div className="space-y-1">
          <label className="text-[0.6875rem] font-bold uppercase tracking-[0.15em] text-[#8e8e88]">
            Investor Sophistication
          </label>
          <p className="text-xs text-[#8e8e88]/60">
            This determines the complexity of fields surfaced throughout the intake.
          </p>
        </div>
        <SegmentedControl
          value={schema.mandate_identification.investor_sophistication}
          onChange={(val) => updateField('mandate_identification.investor_sophistication', val)}
          options={[
            { value: 'retail_novice', label: 'Novice', description: 'Simplified UI, more guidance' },
            { value: 'retail_experienced', label: 'Experienced', description: 'Full field set, standard terms' },
            { value: 'semi_professional', label: 'Semi-Professional', description: 'Active trader with structured approach' },
            { value: 'professional', label: 'Professional', description: 'Advanced metrics, institutional terms' }
          ]}
        />
      </div>

      <div className="grid grid-cols-2 gap-10">
        {/* 1.2 INVESTABLE CAPITAL */}
        <div className="space-y-3" data-field-path="capital_structure.investable_capital_usd">
          <label className="text-[0.6875rem] font-bold uppercase tracking-[0.15em] text-[#8e8e88]">
            Investable Capital (USD)
          </label>
          <div className="relative group">
            <span className="absolute left-4 top-1/2 -translate-y-1/2 text-[#8e8e88] font-mono">$</span>
            <input
              type="text"
              value={capitalFocused ? capitalRaw : (capitalRaw || '')}
              onChange={handleCapitalChange}
              onFocus={handleCapitalFocus}
              onBlur={handleCapitalBlur}
              placeholder="0.00"
              className="w-full bg-surface-container/50 border border-white/5 rounded-xl pl-8 pr-4 py-3 text-lg font-mono text-on-surface outline-none focus:border-secondary/30 focus:ring-1 focus:ring-secondary/20 transition-all"
            />
          </div>
          <p className="text-[0.625rem] text-[#8e8e88]/50 italic">
            Total capital Aegis is authorized to manage for this mandate.
          </p>
        </div>

        {/* 1.3 ACCOUNT TYPE */}
        <div className="space-y-3" data-field-path="mandate_identification.account_type">
          <label className="text-[0.6875rem] font-bold uppercase tracking-[0.15em] text-[#8e8e88]">
            Account Type
          </label>
          <select
            value={schema.mandate_identification.account_type || ''}
            onChange={(e) => updateField('mandate_identification.account_type', e.target.value)}
            className="w-full bg-surface-container/50 border border-white/5 rounded-xl px-4 py-3.5 text-on-surface outline-none focus:border-secondary/30 transition-all appearance-none cursor-pointer"
          >
            <option value="" disabled>Select account type...</option>
            {schema.mandate_identification._account_type_options.map((opt: string) => (
              <option key={opt} value={opt} className="bg-surface-container text-on-surface">
                {opt.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* CAPITAL STRUCTURE */}
      <div className="pt-10 border-t border-white/5 space-y-8">
        <h3 className="text-[1.125rem] font-light text-on-surface serif-text">
          Capital Structure
        </h3>

        {/* Sliders */}
        <div className="grid grid-cols-2 gap-10">
          <Slider
            label="Reserved cash buffer"
            value={schema.capital_structure.reserved_cash_pct ?? 10}
            min={0}
            max={50}
            step={5}
            suffix="%"
            onChange={(val) => updateField('capital_structure.reserved_cash_pct', val)}
            helper="Minimum cash percentage never deployed"
          />
          <Slider
            label="Max deployed capital"
            value={schema.capital_structure.max_deployed_pct ?? 80}
            min={50}
            max={100}
            step={5}
            suffix="%"
            onChange={(val) => updateField('capital_structure.max_deployed_pct', val)}
            helper="Maximum percentage in live positions simultaneously"
          />
        </div>

        {/* Permission Toggles */}
        <div className="grid grid-cols-3 gap-6">
          <Toggle
            label="Leverage permitted"
            value={schema.capital_structure.leverage_permitted ?? false}
            onChange={(val) => updateField('capital_structure.leverage_permitted', val)}
          />
          <Toggle
            label="Options permitted"
            value={schema.capital_structure.options_permitted ?? false}
            onChange={(val) => updateField('capital_structure.options_permitted', val)}
          />
          <Toggle
            label="Short selling permitted"
            value={schema.capital_structure.short_selling_permitted ?? false}
            onChange={(val) => updateField('capital_structure.short_selling_permitted', val)}
          />
        </div>

        {/* Ticker Inputs */}
        <div className="grid grid-cols-2 gap-10">
          <div className="space-y-3">
            <label className="text-[0.6875rem] font-bold uppercase tracking-[0.15em] text-[#8e8e88]">
              Existing holdings (tickers)
            </label>
            <input
              type="text"
              defaultValue={(schema.capital_structure.existing_holdings ?? []).join(', ')}
              onBlur={(e) => handleTickerBlur('capital_structure.existing_holdings', e.target.value)}
              placeholder="AAPL, MSFT, GOOG"
              className="w-full bg-surface-container/50 border border-white/5 rounded-xl px-4 py-3 text-sm font-mono text-on-surface placeholder-[#8e8e88]/30 outline-none focus:border-secondary/30 focus:ring-1 focus:ring-secondary/20 transition-all"
            />
            <p className="text-[0.6875rem] text-[#8e8e88]/60 leading-relaxed italic">
              Tickers you currently hold outside Aegis — for correlation awareness
            </p>
          </div>
          <div className="space-y-3">
            <label className="text-[0.6875rem] font-bold uppercase tracking-[0.15em] text-[#8e8e88]">
              Tickers to never trade
            </label>
            <input
              type="text"
              defaultValue={(schema.capital_structure.tickers_never_touch ?? []).join(', ')}
              onBlur={(e) => handleTickerBlur('capital_structure.tickers_never_touch', e.target.value)}
              placeholder="GME, AMC"
              className="w-full bg-surface-container/50 border border-white/5 rounded-xl px-4 py-3 text-sm font-mono text-on-surface placeholder-[#8e8e88]/30 outline-none focus:border-secondary/30 focus:ring-1 focus:ring-secondary/20 transition-all"
            />
            <p className="text-[0.6875rem] text-[#8e8e88]/60 leading-relaxed italic">
              Absolute exclusions — Aegis will never touch these
            </p>
          </div>
        </div>
      </div>

      {/* 1.4 MANDATE ROLE */}
      <div className="space-y-4" data-field-path="mandate_identification.mandate_role">
        <label className="text-[0.6875rem] font-bold uppercase tracking-[0.15em] text-[#8e8e88]">
          Mandate Role
        </label>
        <SegmentedControl
          value={schema.mandate_identification.mandate_role}
          onChange={(val) => updateField('mandate_identification.mandate_role', val)}
          options={[
            { value: 'entire_liquid_portfolio', label: 'Entire Portfolio', description: 'Primary wealth engine' },
            { value: 'growth_sleeve', label: 'Growth Sleeve', description: 'Alpha-seeking component' },
            { value: 'income_sleeve', label: 'Income Sleeve', description: 'Yield-focused component' },
            { value: 'satellite_speculative', label: 'Satellite', description: 'High-risk speculative bucket' }
          ]}
        />
      </div>

      {/* 1.5 PROSE FIELDS (PROMPTS ARIA) */}
      <div className="pt-6 border-t border-white/5 space-y-6">
        <div className="space-y-3" data-field-path="mandate_identification.mandate_inception_reason">
          <label className="text-[0.6875rem] font-bold uppercase tracking-[0.15em] text-[#8e8e88]">
            Inception Reason
          </label>
          <textarea
            value={schema.mandate_identification.mandate_inception_reason || ''}
            onChange={(e) => updateField('mandate_identification.mandate_inception_reason', e.target.value)}
            placeholder="Why are you establishing this mandate now? (e.g. dissatisfaction with current manager, windfall, etc.)"
            className="w-full bg-surface-container/30 border border-white/5 rounded-xl px-4 py-3 text-sm text-on-surface placeholder-[#8e8e88]/30 min-h-[100px] outline-none focus:border-secondary/30 transition-all"
          />
        </div>
      </div>
    </div>
  );
}
