import { useIntakeStore } from '../../../store/intakeStore';
import { SegmentedControl } from '../SegmentedControl';

export function MandateAndCapital() {
  const schema = useIntakeStore((state) => state.schema);
  const updateField = useIntakeStore((state) => state.updateField);

  // Helper for input updates
  const handleInputChange = (path: string, value: string) => {
    // Attempt to parse as number if it looks like one, else string
    const num = parseFloat(value.replace(/,/g, ''));
    updateField(path, isNaN(num) ? value : num);
  };

  return (
    <div className="space-y-10 animate-in fade-in slide-in-from-bottom-4 duration-700">
      {/* 1.1 INVESTOR SOPHISTICATION */}
      <div className="space-y-4">
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
            { value: 'professional', label: 'Professional', description: 'Advanced metrics, institutional terms' }
          ]}
        />
      </div>

      <div className="grid grid-cols-2 gap-10">
        {/* 1.2 INVESTABLE CAPITAL */}
        <div className="space-y-3">
          <label className="text-[0.6875rem] font-bold uppercase tracking-[0.15em] text-[#8e8e88]">
            Investable Capital (USD)
          </label>
          <div className="relative group">
            <span className="absolute left-4 top-1/2 -translate-y-1/2 text-[#8e8e88] font-mono">$</span>
            <input
              type="text"
              value={schema.capital_structure.investable_capital_usd?.toLocaleString() || ''}
              onChange={(e) => handleInputChange('capital_structure.investable_capital_usd', e.target.value)}
              placeholder="0.00"
              className="w-full bg-surface-container/50 border border-white/5 rounded-xl pl-8 pr-4 py-3 text-lg font-mono text-on-surface outline-none focus:border-secondary/30 focus:ring-1 focus:ring-secondary/20 transition-all"
            />
          </div>
          <p className="text-[0.625rem] text-[#8e8e88]/50 italic">
            Total capital Aegis is authorized to manage for this mandate.
          </p>
        </div>

        {/* 1.3 ACCOUNT TYPE */}
        <div className="space-y-3">
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

      {/* 1.4 MANDATE ROLE */}
      <div className="space-y-4">
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
        <div className="space-y-3">
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
