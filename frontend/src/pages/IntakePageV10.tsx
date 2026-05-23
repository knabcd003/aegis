import { useState, useEffect, useRef } from 'react';
import { useIntakeStore } from '../store/intakeStore';
import { SectionShell } from '../components/Intake/SectionShell';
import { AriaCard } from '../components/Intake/AriaCard';
import { MandateAndCapital } from '../components/Intake/Sections/MandateAndCapital';
import { RiskMandate } from '../components/Intake/Sections/RiskMandate';
import { PerformanceTargets } from '../components/Intake/Sections/PerformanceTargets';
import { UniverseMandate } from '../components/Intake/Sections/UniverseMandate';
import { Section5_Strategy } from '../components/Intake/Sections/Section5_Strategy';
import { Section6_Operations } from '../components/Intake/Sections/Section6_Operations';
import { Section7_Behavioral } from '../components/Intake/Sections/Section7_Behavioral';
import { Section8_Tax } from '../components/Intake/Sections/Section8_Tax';
import { Section9_Macro } from '../components/Intake/Sections/Section9_Macro';
import { Section10_Governance } from '../components/Intake/Sections/Section10_Governance';
import { Bot, AlertTriangle, CheckCircle2 } from 'lucide-react';

const BIOTECH_CATALYSTS = [
  'fda_pdufa_biotech',
  'clinical_trial_readout_phase3',
  'clinical_trial_readout_phase2'
];

export function IntakePageV10() {
  const { 
    currentSection, 
    sections,
    lockSection,
    unlockSection,
    setValidated,
    schema,
    updateField,
    setCurrentSection,
  } = useIntakeStore();

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [submitSuccess, setSubmitSuccess] = useState<any>(null);

  const allLocked = Object.values(sections).every((s) => s.locked);
  const lockedCount = Object.values(sections).filter((s) => s.locked).length;

  const mapV10ToV9Schema = () => {
    const ident = schema.mandate_identification || {};
    const cap = schema.capital_structure || {};
    const risk = schema.risk_mandate || {};
    const t1Risk = risk.tier_1_risk_constraints || {};
    const t2Risk = risk.tier_2_risk_context || {};
    const ret = schema.return_mandate || {};
    const univ = schema.universe_mandate || {};
    const t1Univ = univ.tier_1_hard_filters || {};
    const t2Univ = univ.tier_2_context || {};
    const strat = schema.strategy_mandate || {};
    const t2Strat = strat.tier_2_strategy_context || {};
    const macro = schema.portfolio_scope_and_macro || {};
    const priority = schema.mandate_priority_hierarchy || {};

    return {
      _schema_version: "v9.0",
      mandate_hard_constraints: {
        investable_capital: cap.investable_capital_usd || 0,
        max_portfolio_drawdown_pct: (t1Risk.max_portfolio_drawdown_pct || 0) / 100,
        max_single_position_pct: (t1Risk.max_single_position_pct || 0) / 100,
        max_single_position_usd: t1Risk.max_single_position_usd || 0,
        max_sector_concentration_pct: (t1Risk.max_sector_concentration_pct || 0) / 100,
        max_concurrent_live_strategies: t1Risk.max_concurrent_live_strategies || 0,
        leverage_permitted: cap.leverage_permitted || false,
        account_type: ident.account_type || '',
        horizon_allocation: (strat.horizon_allocation || []).map((h: any) => ({
          label: h.label || '',
          min_days: h.min_days || 0,
          max_days: h.max_days || 0,
          capital_weight: (h.capital_weight || 0) / 100
        })),
        universe_hard_filters: {
          asset_classes_permitted: t1Univ.asset_classes_permitted || [],
          market_cap_range: [
            t1Univ.market_cap_min_usd || 0,
            t1Univ.market_cap_max_usd || 0
          ],
          min_avg_daily_volume_usd: t1Univ.min_avg_daily_volume_usd || 0,
          price_range: `${t1Univ.price_min_usd || 0}-100000`,
          geographies_permitted: t1Univ.geographies_permitted || [],
          sectors_of_interest: t1Univ.sectors_of_interest || [],
          sectors_to_avoid: t1Univ.sectors_excluded || [],
          esg_exclusions: t1Univ.esg_hard_exclusions || [],
          specific_tickers_focus: t1Univ.specific_tickers_focus || [],
          specific_tickers_exclude: t1Univ.specific_tickers_exclude || [],
          tickers_never_touch: cap.tickers_never_touch || []
        }
      },
      investor_profile: {
        summary: ident.existing_non_aegis_portfolio_description || '',
        investment_experience: ident.investment_experience || '',
        portfolio_context: ident.existing_non_aegis_portfolio_description || '',
        time_availability: ident.mandate_role || '',
        behavioral_history: ident.behavioral_history || ''
      },
      risk_profile: {
        volatility_tolerance: t2Risk.volatility_tolerance || '',
        gap_risk_tolerance: t2Risk.gap_risk_tolerance || '',
        concentration_tolerance: t2Risk.concentration_tolerance || '',
        tail_risk_tolerance: t2Risk.tail_risk_tolerance || '',
        time_risk_tolerance: t2Risk.time_risk_tolerance || '',
        correlation_risk: t2Risk.correlation_risk_context || '',
        regret_asymmetry: t2Risk.regret_asymmetry?.type || '',
        loss_aversion_context: t2Risk.loss_aversion_context || ''
      },
      performance_targets: {
        primary_objective: ret.primary_objective || '',
        target_annual_return_pct: (ret.target_annual_return_pct || 0) / 100,
        target_annual_return_context: ret.target_annual_return_context || '',
        benchmark: ret.benchmark || '',
        benchmark_context: ret.benchmark_context || '',
        return_character: ret.return_character?.smoothness_preference || '',
        min_acceptable_sharpe: ret.min_acceptable_sharpe || 0,
        target_return_horizon_months: ret.target_return_horizon_months || 0,
        success_definition: ret.success_definition || '',
        failure_definition: ret.failure_definition || ''
      },
      universe_mandate: {
        raw_desire: t2Univ.universe_description || '',
        universe_description: t2Univ.universe_description || '',
        sector_reasoning: t2Univ.sector_reasoning || '',
        asset_class_preferences: t2Univ.asset_class_preferences || '',
        liquidity_and_price_character: t2Univ.liquidity_and_price_character || '',
        equity_character: t2Univ.equity_character || '',
        options_context: t2Univ.options_context || '',
        etf_preferences: t2Univ.etf_preferences || '',
        existing_holdings: cap.existing_holdings || []
      },
      strategy_intent: {
        regime_preferences: t2Strat.regime_preferences || '',
        catalyst_preferences: t2Strat.catalyst_preferences || '',
        entry_philosophy: t2Strat.entry_philosophy || '',
        exit_philosophy: t2Strat.exit_philosophy || '',
        holding_philosophy: t2Strat.holding_philosophy || '',
        signal_type_preferences: t2Strat.signal_type_preferences || '',
        complexity_preference: t2Strat.complexity_preference || ''
      },
      horizon_mandate: {
        description: t2Strat.regime_preferences || ''
      },
      portfolio_scope: {
        ambition_description: macro.ambition_description || '',
        diversification_intent: macro.diversification_intent || '',
        correlation_intent: macro.correlation_intent || '',
        market_beta_intent: macro.market_beta_intent || '',
        portfolio_beta_existing: ident.portfolio_beta_existing || 0,
        pipeline_growth_intent: macro.pipeline_growth_intent || ''
      },
      mandate_priority_hierarchy: {
        ordered_priorities: (priority.ordered_priorities || []).map((p: any) => ({
          rank: p.rank || 0,
          dimension: p.dimension || '',
          rationale: p.rationale || ''
        })),
        preference_flexibility: (priority.preference_flexibility || []).map((f: any) => ({
          preference: f.preference || '',
          flexibility: f.flexibility || '',
          rationale: f.rationale || ''
        })),
        trade_off_philosophy: priority.trade_off_philosophy || ''
      }
    };
  };

  const handleSubmit = async () => {
    if (!allLocked) return;
    setIsSubmitting(true);
    setSubmitError(null);
    try {
      const v9Schema = mapV10ToV9Schema();
      // 1. Review
      const reviewRes = await fetch('http://localhost:8000/api/intake/confirm/review', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(v9Schema),
      });
      if (!reviewRes.ok) throw new Error('Mandate review failed.');
      const reviewData = await reviewRes.json();
      
      if (reviewData.hard_errors && reviewData.hard_errors.length > 0) {
        throw new Error(`Critical Validation Errors:\n${reviewData.hard_errors.join('\n')}`);
      }

      // 2. Confirm/Submit
      const confirmRes = await fetch('http://localhost:8000/api/intake/confirm', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(reviewData.schema_updated),
      });
      if (!confirmRes.ok) throw new Error('Mandate confirmation failed.');
      const confirmData = await confirmRes.json();
      
      setSubmitSuccess(confirmData);
      localStorage.removeItem('aegis_intake_draft_v10');
    } catch (err: any) {
      setSubmitError(err.message || 'Submission failed');
    } finally {
      setIsSubmitting(false);
    }
  };

  const [activeFieldPath, setActiveFieldPath] = useState<string | null>(null);

  const handleFieldFocus = (path: string) => setActiveFieldPath(path);
  const handleFieldBlur = () => setActiveFieldPath(null);

  // Track which section is most visible and update store so Aria knows
  const sectionRefs = useRef<Record<number, HTMLDivElement | null>>({});
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        let bestRatio = 0;
        let bestSection = -1;
        entries.forEach(entry => {
          if (entry.intersectionRatio > bestRatio) {
            bestRatio = entry.intersectionRatio;
            const n = parseInt(entry.target.getAttribute('data-section-num') ?? '-1');
            if (n > 0) bestSection = n;
          }
        });
        if (bestSection > 0) setCurrentSection(bestSection);
      },
      { threshold: [0.1, 0.3, 0.5], rootMargin: '-80px 0px -40% 0px' }
    );
    Object.values(sectionRefs.current).forEach(el => { if (el) observer.observe(el); });
    return () => observer.disconnect();
  }, [setCurrentSection]);

  const canLockSection1 = () => {
    const ident = schema.mandate_identification;
    const structure = schema.capital_structure;
    if (!ident.investor_sophistication) return false;
    if (!structure.investable_capital_usd || structure.investable_capital_usd <= 0) return false;
    if (!ident.account_type) return false;
    if (!ident.mandate_role) return false;
    return true;
  };

  const canLockSection2 = () => {
    const constraints = schema.risk_mandate.tier_1_risk_constraints;
    if (constraints.max_portfolio_drawdown_pct === null || constraints.max_portfolio_drawdown_pct === undefined || constraints.max_portfolio_drawdown_pct <= 0) return false;
    if (constraints.max_daily_loss_pct === null || constraints.max_daily_loss_pct === undefined || constraints.max_daily_loss_pct <= 0) return false;
    if (!constraints.drawdown_breach_protocol) return false;
    if (constraints.max_single_position_pct === null || constraints.max_single_position_pct === undefined || constraints.max_single_position_pct <= 0) return false;
    if (constraints.max_single_position_usd === null || constraints.max_single_position_usd === undefined || constraints.max_single_position_usd <= 0) return false;
    if (constraints.max_sector_concentration_pct === null || constraints.max_sector_concentration_pct === undefined || constraints.max_sector_concentration_pct <= 0) return false;
    if (constraints.max_concurrent_live_strategies === null || constraints.max_concurrent_live_strategies === undefined || constraints.max_concurrent_live_strategies <= 0) return false;
    return true;
  };

  const canLockSection3 = () => {
    const ret = schema.return_mandate;
    if (!ret.primary_objective) return false;
    return true;
  };

  const canLockSection4 = () => {
    const filters = schema.universe_mandate.tier_1_hard_filters;
    const screens = schema.universe_mandate.fundamental_screens;
    if (filters.asset_classes_permitted.length === 0) return false;
    if (filters.geographies_permitted.length === 0) return false;
    if (filters.market_cap_min_usd === undefined) return false;
    if (filters.min_avg_daily_volume_usd === undefined) return false;
    const conflicts = filters.sectors_of_interest.filter((s: string) => filters.sectors_excluded.includes(s));
    if (conflicts.length > 0) return false;
    if (screens.fundamental_screens_enabled) {
      const incomplete = screens.screens.some((s: any) => !s.screen_type || !s.flexibility);
      if (incomplete) return false;
    }
    return true;
  };

  const canLockSection5 = () => {
    const strategy = schema.strategy_mandate;
    const universe = schema.universe_mandate;
    const catalystValid = strategy.catalyst_types.some((c: any) => c.permitted && Object.values(c.risk_acknowledgments).every((v: any) => v === true));
    if (!catalystValid) return false;
    const totalWeight = strategy.horizon_allocation.reduce((sum: number, b: any) => sum + (b.capital_weight || 0), 0);
    if (Math.round(totalWeight * 100) !== 100) return false;
    const activeBiotech = strategy.catalyst_types.filter((c: any) => c.permitted && BIOTECH_CATALYSTS.includes(c.catalyst_type));
    const sectorExclusions = universe.tier_1_hard_filters.sectors_excluded || [];
    if (activeBiotech.length > 0 && (sectorExclusions.includes('healthcare') || sectorExclusions.includes('biotech'))) return false;
    const screens = universe.fundamental_screens.screens || [];
    const profitabilityConflict = activeBiotech.length > 0 && screens.some((s: any) => s.screen_type === 'profitability_required' && (s.applies_to_catalyst_types.includes('all') || s.applies_to_catalyst_types.some((t: any) => BIOTECH_CATALYSTS.includes(t))));
    if (profitabilityConflict) return false;
    const hasIncompleteBucket = strategy.horizon_allocation.some((b: any) => !b.label || !b.min_days || !b.max_days);
    if (hasIncompleteBucket) return false;
    return true;
  };

  const canLockSection6 = () => {
    const ops = schema.operational_mandate.tier_1_operational_constraints;
    if (ops.available_windows.length === 0) return false;
    if (!ops.max_execution_latency_minutes) return false;
    if (!ops.automation_level) return false;
    return true;
  };

  const canLockSection7 = () => {
    const profile = schema.behavioral_profile;
    if ((profile.cooling_off_requirements.trigger?.length || 0) > 0 && !profile.cooling_off_requirements.cooling_off_days) return false;
    return true;
  };

  const canLockSection8 = () => {
    return !!schema.tax_and_legal.account_tax_status;
  };

  const canLockSection9 = () => {
    const macro = schema.portfolio_scope_and_macro;
    if (!macro.regime_adaptivity_intent) return false;
    return true;
  };

  const canLockSection10 = () => {
    const gov = schema.governance_and_review;
    if (!gov) return false;
    if (!gov.mandate_review_frequency) return false;
    if (!gov.performance_reporting_frequency) return false;
    return true;
  };

  return (
    <div className="flex min-h-screen bg-surface">
      <div className="flex-1 pr-[340px]">
        <div className="max-w-4xl mx-auto px-8 space-y-12 pb-32 pt-12">
          <div className="space-y-2">
            <h1 className="font-headline text-5xl font-light tracking-tight text-on-surface serif-text">
              Guided Intake
            </h1>
            <p className="text-[#8e8e88] text-lg max-w-2xl leading-relaxed">
              The foundation of your autonomous trading pipeline. Section by section, we'll build your mandate.
            </p>
          </div>

          <div className="space-y-8">
            <div ref={el => { sectionRefs.current[1] = el; }} data-section-num="1">
            <SectionShell
              sectionNumber={1}
              title="Mandate & Capital"
              description="Define the account type, the capital Aegis will manage, and any global exclusions for your portfolio."
              locked={sections[1].locked}
              validated={sections[1].validated}
              onLock={() => lockSection(1)}
              onUnlock={() => unlockSection(1)}
              lockDisabled={!canLockSection1()}
            >
              <div className="space-y-8">
                <MandateAndCapital onFieldFocus={handleFieldFocus} onFieldBlur={handleFieldBlur} />
                <div className="p-6 bg-secondary/5 border border-secondary/10 rounded-xl space-y-3 text-right">
                   <button onClick={() => setValidated(1, true)} className="px-4 py-2 bg-secondary/10 border border-secondary/20 text-secondary text-xs font-bold uppercase tracking-widest rounded hover:bg-secondary/20 transition-all">Validate Section 01</button>
                </div>
              </div>
            </SectionShell>
            </div>

            <div ref={el => { sectionRefs.current[2] = el; }} data-section-num="2">
            <SectionShell
              sectionNumber={2}
              title="Risk Mandate"
              description="Establish the hard boundaries for drawdowns, daily loss limits, and position sizing logic."
              locked={sections[2].locked}
              validated={sections[2].validated}
              onLock={() => lockSection(2)}
              onUnlock={() => unlockSection(2)}
              lockDisabled={!sections[1].locked || !canLockSection2()}
            >
              <div className="space-y-8">
                <RiskMandate onFieldFocus={handleFieldFocus} onFieldBlur={handleFieldBlur} />
                <div className="p-6 bg-secondary/5 border border-secondary/10 rounded-xl space-y-3 text-right">
                   <button onClick={() => setValidated(2, true)} className="px-4 py-2 bg-secondary/10 border border-secondary/20 text-secondary text-xs font-bold uppercase tracking-widest rounded hover:bg-secondary/20 transition-all">Validate Section 02</button>
                </div>
              </div>
            </SectionShell>
            </div>

            <div ref={el => { sectionRefs.current[3] = el; }} data-section-num="3">
            <SectionShell
              sectionNumber={3}
              title="Performance Targets"
              description="Define your primary objectives, return expectations, and success metrics."
              locked={sections[3].locked}
              validated={sections[3].validated}
              onLock={() => lockSection(3)}
              onUnlock={() => unlockSection(3)}
              lockDisabled={!sections[2].locked || !canLockSection3()}
            >
              <div className="space-y-8">
                <PerformanceTargets onFieldFocus={handleFieldFocus} onFieldBlur={handleFieldBlur} />
                <div className="p-6 bg-secondary/5 border border-secondary/10 rounded-xl space-y-3 text-right">
                   <button onClick={() => setValidated(3, true)} className="px-4 py-2 bg-secondary/10 border border-secondary/20 text-secondary text-xs font-bold uppercase tracking-widest rounded hover:bg-secondary/20 transition-all">Validate Section 03</button>
                </div>
              </div>
            </SectionShell>
            </div>

            <div ref={el => { sectionRefs.current[4] = el; }} data-section-num="4">
            <SectionShell
              sectionNumber={4}
              title="Universe & Asset Class"
              description="Define your asset class focus, geographical boundaries, and fundamental screening rules."
              locked={sections[4].locked}
              validated={sections[4].validated}
              onLock={() => lockSection(4)}
              onUnlock={() => unlockSection(4)}
              lockDisabled={!sections[3].locked || !canLockSection4()}
            >
              <div className="space-y-8">
                <UniverseMandate onFieldFocus={handleFieldFocus} onFieldBlur={handleFieldBlur} />
                <div className="p-6 bg-secondary/5 border border-secondary/10 rounded-xl space-y-3 text-right">
                   <button onClick={() => setValidated(4, true)} className="px-4 py-2 bg-secondary/10 border border-secondary/20 text-secondary text-xs font-bold uppercase tracking-widest rounded hover:bg-secondary/20 transition-all">Validate Section 04</button>
                </div>
              </div>
            </SectionShell>
            </div>

            <div ref={el => { sectionRefs.current[5] = el; }} data-section-num="5">
            <SectionShell
              sectionNumber={5}
              title="Strategy & Catalysts"
              description="Select the market catalysts Aegis will monitor and define your multi-period risk allocation."
              locked={sections[5].locked}
              validated={sections[5].validated}
              onLock={() => lockSection(5)}
              onUnlock={() => unlockSection(5)}
              lockDisabled={!sections[4].locked || !canLockSection5()}
            >
              <div className="space-y-8">
                <Section5_Strategy onFieldFocus={handleFieldFocus} onFieldBlur={handleFieldBlur} />
                <div className="p-6 bg-secondary/5 border border-secondary/10 rounded-xl space-y-3 text-right">
                   <button onClick={() => setValidated(5, true)} className="px-4 py-2 bg-secondary/10 border border-secondary/20 text-secondary text-xs font-bold uppercase tracking-widest rounded hover:bg-secondary/20 transition-all">Validate Section 05</button>
                </div>
              </div>
            </SectionShell>
            </div>

            <div ref={el => { sectionRefs.current[6] = el; }} data-section-num="6">
            <SectionShell
              sectionNumber={6}
              title="Operational Mandate"
              description="Define your execution windows, speed limitations, and brokerage context."
              locked={sections[6].locked}
              validated={sections[6].validated}
              onLock={() => lockSection(6)}
              onUnlock={() => unlockSection(6)}
              lockDisabled={!sections[5].locked || !canLockSection6()}
            >
              <div className="space-y-8">
                <Section6_Operations onFieldFocus={handleFieldFocus} onFieldBlur={handleFieldBlur} />
                <div className="p-6 bg-secondary/5 border border-secondary/10 rounded-xl space-y-3 text-right">
                   <button onClick={() => setValidated(6, true)} className="px-4 py-2 bg-secondary/10 border border-secondary/20 text-secondary text-xs font-bold uppercase tracking-widest rounded hover:bg-secondary/20 transition-all">Validate Section 06</button>
                </div>
              </div>
            </SectionShell>
            </div>

            <div ref={el => { sectionRefs.current[7] = el; }} data-section-num="7">
            <SectionShell
              sectionNumber={7}
              title="Behavioral Profile"
              description="Capture your psychological relationship with risk and establish mechanical guardrails for drawdown scenarios."
              locked={sections[7].locked}
              validated={sections[7].validated}
              onLock={() => lockSection(7)}
              onUnlock={() => unlockSection(7)}
              lockDisabled={!sections[6].locked || !canLockSection7()}
            >
              <div className="space-y-8">
                <Section7_Behavioral onFieldFocus={handleFieldFocus} onFieldBlur={handleFieldBlur} />
                <div className="p-6 bg-secondary/5 border border-secondary/10 rounded-xl space-y-3 text-right">
                   <button onClick={() => setValidated(7, true)} className="px-4 py-2 bg-secondary/10 border border-secondary/20 text-secondary text-xs font-bold uppercase tracking-widest rounded hover:bg-secondary/20 transition-all">Validate Section 07</button>
                </div>
              </div>
            </SectionShell>
            </div>

            <div ref={el => { sectionRefs.current[8] = el; }} data-section-num="8">
            <SectionShell
              sectionNumber={8}
              title="Tax & Legal"
              description="Define your account's tax status, marginal rates, and any legal trading restrictions."
              locked={sections[8].locked}
              validated={sections[8].validated}
              onLock={() => lockSection(8)}
              onUnlock={() => unlockSection(8)}
              lockDisabled={!sections[7].locked || !canLockSection8()}
            >
              <div className="space-y-8">
                <Section8_Tax onFieldFocus={handleFieldFocus} onFieldBlur={handleFieldBlur} />
                <div className="p-6 bg-secondary/5 border border-secondary/10 rounded-xl space-y-3 text-right">
                   <button onClick={() => setValidated(8, true)} className="px-4 py-2 bg-secondary/10 border border-secondary/20 text-secondary text-xs font-bold uppercase tracking-widest rounded hover:bg-secondary/20 transition-all">Validate Section 08</button>
                </div>
              </div>
            </SectionShell>
            </div>

            <div ref={el => { sectionRefs.current[9] = el; }} data-section-num="9">
            <SectionShell
              sectionNumber={9}
              title="Portfolio Scope & Macro"
              description="Establish your target market beta, regime adaptivity, and current sector sentiment."
              locked={sections[9].locked}
              validated={sections[9].validated}
              onLock={() => lockSection(9)}
              onUnlock={() => unlockSection(9)}
              lockDisabled={!sections[8].locked || !canLockSection9()}
            >
              <div className="space-y-8">
                <Section9_Macro onFieldFocus={handleFieldFocus} onFieldBlur={handleFieldBlur} />
                <div className="p-6 bg-secondary/5 border border-secondary/10 rounded-xl space-y-3 text-right">
                   <button onClick={() => setValidated(9, true)} className="px-4 py-2 bg-secondary/10 border border-secondary/20 text-secondary text-xs font-bold uppercase tracking-widest rounded hover:bg-secondary/20 transition-all">Validate Section 09</button>
                </div>
              </div>
            </SectionShell>
            </div>

            <div ref={el => { sectionRefs.current[10] = el; }} data-section-num="10">
            <SectionShell
              sectionNumber={10}
              title="Governance & Attestation"
              description="Finalize your mandate priorities and attest to your compliance awareness."
              locked={sections[10].locked}
              validated={sections[10].validated}
              onLock={() => lockSection(10)}
              onUnlock={() => unlockSection(10)}
              lockDisabled={!sections[9].locked || !canLockSection10()}
            >
              <div className="space-y-8">
                <Section10_Governance onFieldFocus={handleFieldFocus} onFieldBlur={handleFieldBlur} />
                <div className="p-6 bg-secondary/5 border border-secondary/10 rounded-xl space-y-3 text-right">
                   <button onClick={() => setValidated(10, true)} className="px-4 py-2 bg-secondary/10 border border-secondary/20 text-secondary text-xs font-bold uppercase tracking-widest rounded hover:bg-secondary/20 transition-all">Validate Section 10</button>
                </div>
              </div>
            </SectionShell>
            </div>

            {/* SUBMIT MANDATE CONTROL CARD */}
            <div className="p-8 rounded-2xl bg-[#1c1c18]/40 border-2 border-[#8e8e88]/20 backdrop-blur-xl shadow-xl space-y-6">
              <div className="flex items-start gap-4">
                <div className={`p-2 rounded-lg ${allLocked ? 'bg-[#ACCEC5]/20 text-[#ACCEC5]' : 'bg-[#8e8e88]/10 text-[#8e8e88]'}`}>
                  <Bot size={24} />
                </div>
                <div className="space-y-1">
                  <h3 className="text-lg font-serif italic text-on-surface">Lock & Run Mandate Simulation</h3>
                  <p className="text-xs text-[#8e8e88]">
                    {allLocked 
                      ? "All 10 sections are locked. You are ready to launch the Aegis AI trader simulation."
                      : `Locked: ${lockedCount}/10 sections. You must complete and lock all sections before launching the simulation.`
                    }
                  </p>
                </div>
              </div>

              {submitError && (
                <div className="p-3 bg-terracotta/10 border border-terracotta/20 text-terracotta text-xs rounded-xl flex items-start gap-2">
                  <AlertTriangle size={16} className="mt-0.5 flex-shrink-0" />
                  <pre className="whitespace-pre-wrap font-sans">{submitError}</pre>
                </div>
              )}

              {submitSuccess && (
                <div className="p-4 bg-[#ACCEC5]/10 border border-[#ACCEC5]/20 text-[#ACCEC5] text-xs rounded-xl space-y-2">
                  <div className="flex items-center gap-2 font-bold uppercase tracking-wider">
                    <CheckCircle2 size={16} />
                    <span>Mandate Confirmed & Simulation Launched</span>
                  </div>
                  <p>Workflow ID: <code className="bg-white/5 px-1.5 py-0.5 rounded font-mono">{submitSuccess.workflow_id}</code></p>
                  <p>Status: <span className="capitalize font-semibold">{submitSuccess.status}</span></p>
                </div>
              )}

              <div className="flex justify-end items-center gap-4">
                {!allLocked && (
                  <span className="text-[11px] text-[#8e8e88] italic">
                    Remaining: {Object.entries(sections).filter(([_, s]) => !s.locked).map(([n]) => `Sec ${n}`).join(', ')}
                  </span>
                )}
                <button
                  disabled={!allLocked || isSubmitting || !!submitSuccess}
                  onClick={handleSubmit}
                  className={`px-6 py-3 font-bold uppercase tracking-wider text-xs rounded-xl transition-all ${
                    allLocked && !submitSuccess
                      ? 'bg-[#ACCEC5] text-[#151512] hover:shadow-lg hover:scale-[1.02] cursor-pointer'
                      : 'bg-white/5 border border-white/10 text-[#8e8e88] cursor-not-allowed'
                  }`}
                >
                  {isSubmitting ? 'Submitting...' : 'Submit Mandate'}
                </button>
              </div>
            </div>

          </div>
        </div>
      </div>
      <AriaCard 
        currentSection={currentSection} 
        schemaState={schema} 
        activeFieldPath={activeFieldPath}
        onFieldUpdate={updateField}
      />
    </div>
  );
}
