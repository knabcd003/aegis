import { useIntakeStore } from '../../../store/intakeStore';
import { SegmentedControl } from '../SegmentedControl';
import { RadioGroup } from '../RadioGroup';
import { Slider } from '../Slider';
import { Toggle } from '../Toggle';
import { Info, AlertTriangle } from 'lucide-react';
import { useEffect, useMemo } from 'react';

export function Section8_Tax() {
  const schema = useIntakeStore((state) => state.schema);
  const updateField = useIntakeStore((state) => state.updateField);

  // Robust field access with fallbacks
  const tax = schema?.tax_and_legal || {};
  const mandate = schema?.mandate_and_capital || {};
  const returnMandate = schema?.return_mandate || {};
  const strategy = schema?.strategy_mandate || {};

  // AUTO-SUGGEST TAX STATUS BASED ON SECTION 1
  useEffect(() => {
    if (tax && !tax.account_tax_status) {
      const mapping: Record<string, string> = {
        individual_taxable: 'fully_taxable',
        traditional_ira: 'tax_deferred_traditional',
        roth_ira: 'tax_exempt_roth',
        '401k_solo': 'tax_deferred_traditional',
        sep_ira: 'tax_deferred_traditional'
      };
      const suggested = mapping[mandate.account_type];
      if (suggested) {
        updateField('tax_and_legal.account_tax_status', suggested);
      }
    }
  }, [mandate.account_type, tax, updateField]);

  const isTaxable = tax.account_tax_status === 'fully_taxable';

  // COMPUTED AFTER-TAX IMPACT
  const afterTaxReturn = useMemo(() => {
    const gross = returnMandate.target_annual_return_pct || 0;
    const rate = tax.estimated_marginal_tax_rate_pct || 0;
    return (gross * (1 - rate / 100)).toFixed(1);
  }, [returnMandate.target_annual_return_pct, tax.estimated_marginal_tax_rate_pct]);

  // CROSS-SECTION WARNINGS
  const allShortTerm = useMemo(() => {
    return (strategy.horizon_allocation?.length || 0) > 0 && 
           strategy.horizon_allocation.every((h: any) => h.max_days < 365);
  }, [strategy.horizon_allocation]);

  const hasShortTerm = useMemo(() => {
    return (strategy.horizon_allocation?.length || 0) > 0 &&
           strategy.horizon_allocation.some((h: any) => h.max_days < 365);
  }, [strategy.horizon_allocation]);

  const showRule09 = allShortTerm && tax.short_term_gains_tolerance?.level === 'strongly_prefer_to_avoid';
  
  const showRule10 = (tax.estimated_marginal_tax_rate_pct || 0) >= 32 && 
                     hasShortTerm && 
                     ['neutral', 'acceptable', 'indifferent'].includes(tax.short_term_gains_tolerance?.level || '');

  const showERISA = ['traditional_ira', '401k_solo', 'sep_ira'].includes(mandate.account_type);

  return (
    <div className="space-y-12 animate-in fade-in slide-in-from-bottom-4 duration-700">
      
      {/* 8.1 ACCOUNT TAX STATUS */}
      <div className="space-y-6">
        <div className="space-y-1">
          <label className="text-[0.6875rem] font-bold uppercase tracking-[0.15em] text-[#8e8e88]">
            Account tax treatment
          </label>
          <p className="text-xs text-[#8e8e88]/60">
            Determines how gains and losses are treated and directly affects strategy design.
          </p>
        </div>
        <SegmentedControl
          value={tax.account_tax_status}
          onChange={(val) => updateField('tax_and_legal.account_tax_status', val)}
          options={[
            { value: 'fully_taxable', label: 'Fully Taxable', description: 'Standard brokerage account — all gains subject to capital gains tax' },
            { value: 'tax_deferred_traditional', label: 'Tax-Deferred', description: 'Traditional IRA or 401(k) — gains grow tax-deferred' },
            { value: 'tax_exempt_roth', label: 'Tax-Exempt', description: 'Roth IRA — gains grow and withdraw tax-free' },
            { value: 'partially_sheltered', label: 'Partially Sheltered', description: 'Mixed structure — some tax-advantaged, some taxable' }
          ]}
        />
      </div>

      {/* 8.2 TAXABLE ACCOUNT FIELDS */}
      {isTaxable && (
        <div className="space-y-12 animate-in fade-in slide-in-from-top-4 duration-500">
          
          {/* MARGINAL RATE */}
          <div className="pt-10 border-t border-white/5 space-y-6">
            <div className="space-y-1">
              <label className="text-[0.6875rem] font-bold uppercase tracking-[0.15em] text-[#8e8e88]">
                Estimated marginal tax rate
              </label>
              <p className="text-xs text-[#8e8e88]/60">Used to weight after-tax returns in strategy evaluation.</p>
            </div>
            <SegmentedControl
              value={tax.estimated_marginal_tax_rate_pct?.toString() || null}
              onChange={(val) => updateField('tax_and_legal.estimated_marginal_tax_rate_pct', parseInt(val))}
              options={[
                { value: '10', label: '10%' },
                { value: '12', label: '12%' },
                { value: '22', label: '22%' },
                { value: '24', label: '24%' },
                { value: '32', label: '32%' },
                { value: '35', label: '35%' },
                { value: '37', label: '37%', description: 'Top bracket' }
              ]}
            />
            {tax.estimated_marginal_tax_rate_pct && returnMandate.target_annual_return_pct && (
              <p className="text-[0.6875rem] text-[#8e8e88]/60 font-medium italic">
                At {tax.estimated_marginal_tax_rate_pct}% marginal rate, a {returnMandate.target_annual_return_pct}% gross annual return becomes approximately {afterTaxReturn}% after tax on short-term gains.
              </p>
            )}
          </div>

          {/* SHORT TERM TOLERANCE */}
          <div className="pt-10 border-t border-white/5 space-y-6">
            <div className="space-y-1">
              <label className="text-[0.6875rem] font-bold uppercase tracking-[0.15em] text-[#8e8e88]">
                Short-term capital gains tolerance
              </label>
              <p className="text-xs text-[#8e8e88]/60">Most post-catalyst strategies hold under 12 months.</p>
            </div>
            <RadioGroup
              value={tax.short_term_gains_tolerance?.level || null}
              onChange={(val) => updateField('tax_and_legal.short_term_gains_tolerance.level', val)}
              options={[
                { value: 'strongly_prefer_to_avoid', label: 'Strongly Prefer to Avoid', description: "Minimizing short-term gains is a primary concern" },
                { value: 'prefer_to_avoid', label: 'Prefer to Avoid', description: "Would rather avoid short-term gains where possible" },
                { value: 'neutral', label: 'Neutral', description: "No strong preference — optimize for returns regardless" },
                { value: 'acceptable', label: 'Acceptable', description: "Short-term gains are fine — returns matter more" },
                { value: 'indifferent', label: 'Indifferent', description: "Tax treatment is not a consideration" }
              ]}
            />
            
            {showRule09 && (
              <div className="p-4 bg-amber-500/10 border border-amber-500/20 rounded-xl flex items-start gap-3 animate-in shake duration-500">
                <AlertTriangle size={18} className="text-amber-500 mt-0.5" />
                <div className="space-y-1">
                  <p className="text-[0.8125rem] font-bold text-amber-500">Mandate Contradiction</p>
                  <p className="text-xs text-amber-500/80 leading-relaxed">
                    All your horizon buckets are under 365 days. Every strategy generated will produce short-term gains. Add a long-term bucket in Section 5 or adjust your tolerance here.
                  </p>
                </div>
              </div>
            )}

            {showRule10 && (
              <div className="p-4 bg-blue-500/10 border border-blue-500/20 rounded-xl flex items-start gap-3 animate-in fade-in duration-500">
                <Info size={18} className="text-blue-400 mt-0.5" />
                <div className="space-y-1">
                  <p className="text-[0.8125rem] font-bold text-blue-400">Tax Efficiency Advisory</p>
                  <p className="text-xs text-blue-400/80 leading-relaxed">
                    At {tax.estimated_marginal_tax_rate_pct}% marginal rate, short-term gains on sub-365-day strategies are taxed as ordinary income. Your after-tax returns will be materially lower.
                  </p>
                </div>
              </div>
            )}
          </div>

          {/* PREFERENCES & HARVESTING */}
          <div className="pt-10 border-t border-white/5 grid grid-cols-1 md:grid-cols-2 gap-10">
            <div className="space-y-6">
              <Slider
                label="Long-term gain preference"
                min={0}
                max={100}
                step={5}
                suffix="%"
                value={tax.long_term_holding_preference_pct}
                onChange={(val) => updateField('tax_and_legal.long_term_holding_preference_pct', val)}
                helper="Percentage of realized gains you'd prefer to be long-term (held 12+ months)."
              />
            </div>
            <div className="space-y-6">
              <label className="text-[0.6875rem] font-bold uppercase tracking-[0.15em] text-[#8e8e88]">
                Tax-loss harvesting
              </label>
              <SegmentedControl
                value={tax.tax_loss_harvesting_directive}
                onChange={(val) => updateField('tax_and_legal.tax_loss_harvesting_directive', val)}
                options={[
                  { value: 'active', label: 'Active', description: "Proactively realize losses" },
                  { value: 'passive_opportunistic', label: 'Opportunistic', description: "Harvest naturally occurring losses" },
                  { value: 'none', label: 'None', description: "Ignore tax timing" }
                ]}
              />
            </div>
          </div>

          {/* WASH SALE & LOT METHOD */}
          <div className="pt-10 border-t border-white/5 grid grid-cols-1 md:grid-cols-2 gap-10">
            <Toggle
              label="Track wash sale rules"
              helper="Enable if you trade the same securities manually in other accounts."
              value={tax.wash_sale_awareness_required}
              onChange={(val) => updateField('tax_and_legal.wash_sale_awareness_required', val)}
            />
            <div className="space-y-4">
              <label className="text-[0.6875rem] font-bold uppercase tracking-[0.15em] text-[#8e8e88]">
                Tax lot accounting method
              </label>
              <SegmentedControl
                value={tax.specific_tax_lot_method}
                onChange={(val) => updateField('tax_and_legal.specific_tax_lot_method', val)}
                options={[
                  { value: 'fifo', label: 'FIFO' },
                  { value: 'lifo', label: 'LIFO' },
                  { value: 'hifo', label: 'HIFO', description: 'Highest cost basis' },
                  { value: 'specific_identification', label: 'Specific ID' }
                ]}
              />
            </div>
          </div>

        </div>
      )}

      {/* 8.3 ALL ACCOUNT TYPES */}
      <div className="pt-10 border-t border-white/5 space-y-10">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-10">
          <div className="space-y-4">
            <label className="text-[0.6875rem] font-bold uppercase tracking-[0.15em] text-[#8e8e88]">
              Tax jurisdiction
            </label>
            <SegmentedControl
              value={tax.jurisdiction || 'us'}
              onChange={(val) => updateField('tax_and_legal.jurisdiction', val)}
              options={[
                { value: 'us', label: 'United States' },
                { value: 'canada', label: 'Canada' },
                { value: 'uk', label: 'United Kingdom' },
                { value: 'eu_member', label: 'European Union' },
                { value: 'other', label: 'Other' }
              ]}
            />
          </div>
          {showERISA && (
            <div className="animate-in fade-in duration-500">
              <Toggle
                label="ERISA applies to this account"
                helper="Applies to employer-sponsored retirement accounts."
                value={tax.erisa_applicable}
                onChange={(val) => updateField('tax_and_legal.erisa_applicable', val)}
              />
            </div>
          )}
        </div>

        {/* LEGAL DISCLOSURE */}
        <div className="space-y-4">
          <div className="p-4 bg-amber-500/10 border border-amber-500/20 rounded-xl flex items-start gap-3">
            <AlertTriangle size={18} className="text-amber-500 mt-0.5" />
            <p className="text-xs text-amber-500/80 leading-relaxed">
              Disclosure only — Aegis does not enforce blackout periods or restricted securities lists. You are solely responsible for compliance with your applicable trading policies.
            </p>
          </div>
          <div className="space-y-2">
            <label className="text-[0.6875rem] font-bold uppercase tracking-[0.15em] text-[#8e8e88]">
              Legal trading restrictions
            </label>
            <textarea
              value={tax.legal_trading_restrictions_disclosure || ''}
              onChange={(e) => updateField('tax_and_legal.legal_trading_restrictions_disclosure', e.target.value)}
              placeholder="e.g. Corporate insider blackout periods, employer pre-clearance requirements, FINRA restrictions..."
              className="w-full bg-surface-container/30 border border-white/5 rounded-xl px-4 py-3 text-sm text-on-surface placeholder-[#8e8e88]/30 min-h-[100px] outline-none focus:border-secondary/30 transition-all"
            />
          </div>
        </div>
      </div>

      {/* 8.4 DETAIL BOX */}
      <div className="pt-10 border-t border-white/5 space-y-3">
        <label className="text-[0.6875rem] font-bold uppercase tracking-[0.15em] text-[#8e8e88]">
          Tax Context & Regulatory Constraints
        </label>
        <textarea
          value={tax.regulatory_constraints || ''}
          onChange={(e) => updateField('tax_and_legal.regulatory_constraints', e.target.value)}
          placeholder="Any additional tax context or legal constraints? Include anything relevant to how gains and losses should be handled..."
          className="w-full bg-surface-container/30 border border-white/5 rounded-xl px-4 py-3 text-sm text-on-surface placeholder-[#8e8e88]/30 min-h-[150px] outline-none focus:border-secondary/30 transition-all"
        />
      </div>
    </div>
  );
}
