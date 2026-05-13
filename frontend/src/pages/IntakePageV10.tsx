import { useState } from 'react';
import { useIntakeStore } from '../store/intakeStore';
import { SectionShell } from '../components/Intake/SectionShell';
import { AgentPanel } from '../components/Intake/AgentPanel';
import { MandateAndCapital } from '../components/Intake/Sections/MandateAndCapital';
import { RiskMandate } from '../components/Intake/Sections/RiskMandate';
import { PerformanceTargets } from '../components/Intake/Sections/PerformanceTargets';
import { UniverseMandate } from '../components/Intake/Sections/UniverseMandate';
import { Section5_Strategy } from '../components/Intake/Sections/Section5_Strategy';
import { Section6_Operations } from '../components/Intake/Sections/Section6_Operations';
import { Section7_Behavioral } from '../components/Intake/Sections/Section7_Behavioral';
import { Section8_Tax } from '../components/Intake/Sections/Section8_Tax';
import type { AgentMessage } from '../types/intake';

const BIOTECH_CATALYSTS = [
  'fda_pdufa_biotech',
  'clinical_trial_readout_phase3',
  'clinical_trial_readout_phase2'
];

export function IntakePageV10() {
  const { 
    currentSection, 
    messages, 
    addMessage, 
    isThinking, 
    setThinking,
    sections,
    lockSection,
    unlockSection,
    setValidated,
    schema
  } = useIntakeStore();

  const handleSendMessage = (text: string) => {
    const userMsg: AgentMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: text,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      section: currentSection
    };
    addMessage(userMsg);
    
    setThinking(true);
    setTimeout(() => {
      const agentMsg: AgentMessage = {
        id: (Date.now() + 1).toString(),
        role: 'agent',
        content: `I've noted that. Let's focus on completing Section ${currentSection}.`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        section: currentSection
      };
      addMessage(agentMsg);
      setThinking(false);
    }, 1500);
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
    const catalystValid = strategy.catalyst_types.some(c => c.permitted && Object.values(c.risk_acknowledgments).every(v => v === true));
    if (!catalystValid) return false;
    const totalWeight = strategy.horizon_allocation.reduce((sum, b) => sum + (b.capital_weight || 0), 0);
    if (Math.round(totalWeight * 100) !== 100) return false;
    const activeBiotech = strategy.catalyst_types.filter(c => c.permitted && BIOTECH_CATALYSTS.includes(c.catalyst_type));
    const sectorExclusions = universe.tier_1_hard_filters.sectors_excluded || [];
    if (activeBiotech.length > 0 && (sectorExclusions.includes('healthcare') || sectorExclusions.includes('biotech'))) return false;
    const screens = universe.fundamental_screens.screens || [];
    const profitabilityConflict = activeBiotech.length > 0 && screens.some(s => s.screen_type === 'profitability_required' && (s.applies_to_catalyst_types.includes('all') || s.applies_to_catalyst_types.some(t => BIOTECH_CATALYSTS.includes(t))));
    if (profitabilityConflict) return false;
    const hasIncompleteBucket = strategy.horizon_allocation.some(b => !b.label || !b.min_days || !b.max_days);
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

  return (
    <div className="flex min-h-screen bg-surface">
      <div className="flex-1 pr-[380px]">
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
            <SectionShell
              sectionNumber={1}
              title="Mandate & Capital"
              description="Define the account type, the capital Aegis will manage, and any global exclusions for your portfolio."
              locked={sections[1].locked}
              validated={sections[1].validated}
              onLock={() => lockSection(1)}
              onUnlock={() => unlockSection(1)}
            >
              <div className="space-y-8">
                <MandateAndCapital />
                <div className="p-6 bg-secondary/5 border border-secondary/10 rounded-xl space-y-3 text-right">
                   <button onClick={() => setValidated(1, true)} className="px-4 py-2 bg-secondary/10 border border-secondary/20 text-secondary text-xs font-bold uppercase tracking-widest rounded hover:bg-secondary/20 transition-all">Validate Section 01</button>
                </div>
              </div>
            </SectionShell>

            <SectionShell
              sectionNumber={2}
              title="Risk Mandate"
              description="Establish the hard boundaries for drawdowns, daily loss limits, and position sizing logic."
              locked={sections[2].locked}
              validated={sections[2].validated}
              onLock={() => lockSection(2)}
              onUnlock={() => unlockSection(2)}
            >
              <div className="space-y-8">
                <RiskMandate />
                <div className="p-6 bg-secondary/5 border border-secondary/10 rounded-xl space-y-3 text-right">
                   <button onClick={() => setValidated(2, true)} className="px-4 py-2 bg-secondary/10 border border-secondary/20 text-secondary text-xs font-bold uppercase tracking-widest rounded hover:bg-secondary/20 transition-all">Validate Section 02</button>
                </div>
              </div>
            </SectionShell>

            <SectionShell
              sectionNumber={3}
              title="Performance Targets"
              description="Define your primary objectives, return expectations, and success metrics."
              locked={sections[3].locked}
              validated={sections[3].validated}
              onLock={() => lockSection(3)}
              onUnlock={() => unlockSection(3)}
            >
              <div className="space-y-8">
                <PerformanceTargets />
                <div className="p-6 bg-secondary/5 border border-secondary/10 rounded-xl space-y-3 text-right">
                   <button onClick={() => setValidated(3, true)} className="px-4 py-2 bg-secondary/10 border border-secondary/20 text-secondary text-xs font-bold uppercase tracking-widest rounded hover:bg-secondary/20 transition-all">Validate Section 03</button>
                </div>
              </div>
            </SectionShell>

            <SectionShell
              sectionNumber={4}
              title="Universe & Asset Class"
              description="Define your asset class focus, geographical boundaries, and fundamental screening rules."
              locked={sections[4].locked}
              validated={sections[4].validated}
              onLock={() => lockSection(4)}
              onUnlock={() => unlockSection(4)}
              lockDisabled={!canLockSection4()}
            >
              <div className="space-y-8">
                <UniverseMandate />
                <div className="p-6 bg-secondary/5 border border-secondary/10 rounded-xl space-y-3 text-right">
                   <button onClick={() => setValidated(4, true)} className="px-4 py-2 bg-secondary/10 border border-secondary/20 text-secondary text-xs font-bold uppercase tracking-widest rounded hover:bg-secondary/20 transition-all">Validate Section 04</button>
                </div>
              </div>
            </SectionShell>

            <SectionShell
              sectionNumber={5}
              title="Strategy & Catalysts"
              description="Select the market catalysts Aegis will monitor and define your multi-period risk allocation."
              locked={sections[5].locked}
              validated={sections[5].validated}
              onLock={() => lockSection(5)}
              onUnlock={() => unlockSection(5)}
              lockDisabled={!canLockSection5()}
            >
              <div className="space-y-8">
                <Section5_Strategy />
                <div className="p-6 bg-secondary/5 border border-secondary/10 rounded-xl space-y-3 text-right">
                   <button onClick={() => setValidated(5, true)} className="px-4 py-2 bg-secondary/10 border border-secondary/20 text-secondary text-xs font-bold uppercase tracking-widest rounded hover:bg-secondary/20 transition-all">Validate Section 05</button>
                </div>
              </div>
            </SectionShell>

            <SectionShell
              sectionNumber={6}
              title="Operational Mandate"
              description="Define your execution windows, speed limitations, and brokerage context."
              locked={sections[6].locked}
              validated={sections[6].validated}
              onLock={() => lockSection(6)}
              onUnlock={() => unlockSection(6)}
              lockDisabled={!canLockSection6()}
            >
              <div className="space-y-8">
                <Section6_Operations />
                <div className="p-6 bg-secondary/5 border border-secondary/10 rounded-xl space-y-3 text-right">
                   <button onClick={() => setValidated(6, true)} className="px-4 py-2 bg-secondary/10 border border-secondary/20 text-secondary text-xs font-bold uppercase tracking-widest rounded hover:bg-secondary/20 transition-all">Validate Section 06</button>
                </div>
              </div>
            </SectionShell>

            <SectionShell
              sectionNumber={7}
              title="Behavioral Profile"
              description="Capture your psychological relationship with risk and establish mechanical guardrails for drawdown scenarios."
              locked={sections[7].locked}
              validated={sections[7].validated}
              onLock={() => lockSection(7)}
              onUnlock={() => unlockSection(7)}
              lockDisabled={!canLockSection7()}
            >
              <div className="space-y-8">
                <Section7_Behavioral />
                <div className="p-6 bg-secondary/5 border border-secondary/10 rounded-xl space-y-3 text-right">
                   <button onClick={() => setValidated(7, true)} className="px-4 py-2 bg-secondary/10 border border-secondary/20 text-secondary text-xs font-bold uppercase tracking-widest rounded hover:bg-secondary/20 transition-all">Validate Section 07</button>
                </div>
              </div>
            </SectionShell>

            <SectionShell
              sectionNumber={8}
              title="Tax & Legal"
              description="Define your account's tax status, marginal rates, and any legal trading restrictions."
              locked={sections[8].locked}
              validated={sections[8].validated}
              onLock={() => lockSection(8)}
              onUnlock={() => unlockSection(8)}
              lockDisabled={!canLockSection8()}
            >
              <div className="space-y-8">
                <Section8_Tax />
                <div className="p-6 bg-secondary/5 border border-secondary/10 rounded-xl space-y-3 text-right">
                   <button onClick={() => setValidated(8, true)} className="px-4 py-2 bg-secondary/10 border border-secondary/20 text-secondary text-xs font-bold uppercase tracking-widest rounded hover:bg-secondary/20 transition-all">Validate Section 08</button>
                </div>
              </div>
            </SectionShell>
          </div>
        </div>
      </div>
      <AgentPanel messages={messages} isThinking={isThinking} onSendMessage={handleSendMessage} currentSection={currentSection} />
    </div>
  );
}
