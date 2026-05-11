import { useState } from 'react';
import { useIntakeStore } from '../store/intakeStore';
import { SectionShell } from '../components/Intake/SectionShell';
import { AgentPanel } from '../components/Intake/AgentPanel';
import { MandateAndCapital } from '../components/Intake/Sections/MandateAndCapital';
import { RiskMandate } from '../components/Intake/Sections/RiskMandate';
import { PerformanceTargets } from '../components/Intake/Sections/PerformanceTargets';
import { UniverseMandate } from '../components/Intake/Sections/UniverseMandate';
import { CatalystCardGrid } from '../components/Intake/CatalystCardGrid';
import type { AgentMessage, CatalystTypeEntry } from '../types/intake';

export function IntakePageV10() {
  const [testCatalysts, setTestCatalysts] = useState<CatalystTypeEntry[]>([]);
  const [isCatalystValid, setIsCatalystValid] = useState(false);

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
    
    // Simulate agent response
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
                <div className="p-6 bg-secondary/5 border border-secondary/10 rounded-xl space-y-3">
                   <button onClick={() => setValidated(1, true)} className="px-4 py-2 bg-secondary/10 border border-secondary/20 text-secondary text-xs font-bold uppercase tracking-widest rounded">Validate Section 01</button>
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
                <div className="p-6 bg-secondary/5 border border-secondary/10 rounded-xl space-y-3">
                   <button onClick={() => setValidated(2, true)} className="px-4 py-2 bg-secondary/10 border border-secondary/20 text-secondary text-xs font-bold uppercase tracking-widest rounded">Validate Section 02</button>
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
                <div className="p-6 bg-secondary/5 border border-secondary/10 rounded-xl space-y-3">
                   <button onClick={() => setValidated(3, true)} className="px-4 py-2 bg-secondary/10 border border-secondary/20 text-secondary text-xs font-bold uppercase tracking-widest rounded">Validate Section 03</button>
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
                <div className="p-6 bg-secondary/5 border border-secondary/10 rounded-xl space-y-3">
                   <button onClick={() => setValidated(4, true)} className="px-4 py-2 bg-secondary/10 border border-secondary/20 text-secondary text-xs font-bold uppercase tracking-widest rounded">Validate Section 04</button>
                </div>
              </div>
            </SectionShell>

            {/* SECTION 5 (TEST) */}
            <SectionShell
              sectionNumber={5}
              title="Strategy & Catalysts"
              description="Select the market catalysts Aegis will monitor and define your multi-period risk allocation."
              locked={sections[5].locked}
              validated={sections[5].validated}
              onLock={() => lockSection(5)}
              onUnlock={() => unlockSection(5)}
            >
              <div className="space-y-8">
                <div className="space-y-4">
                  <label className="text-[0.6875rem] font-bold uppercase tracking-[0.15em] text-[#8e8e88]">
                    Active Catalysts
                  </label>
                  <CatalystCardGrid
                    value={testCatalysts}
                    onChange={setTestCatalysts}
                    onValidityChange={setIsCatalystValid}
                  />
                </div>
                <div className="p-6 bg-secondary/5 border border-secondary/10 rounded-xl space-y-3">
                   <p className="text-sm text-on-surface/80 leading-relaxed">
                     Valid: {isCatalystValid ? "YES" : "NO"}
                   </p>
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
