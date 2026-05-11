import { useIntakeStore } from '../store/intakeStore';
import { SectionShell } from '../components/Intake/SectionShell';
import { AgentPanel } from '../components/Intake/AgentPanel';
import { MandateAndCapital } from '../components/Intake/Sections/MandateAndCapital';
import { RiskMandate } from '../components/Intake/Sections/RiskMandate';
import { PerformanceTargets } from '../components/Intake/Sections/PerformanceTargets';
import type { AgentMessage } from '../types/intake';

export function IntakePageV10() {
  const { 
    currentSection, 
    setCurrentSection, 
    messages, 
    addMessage, 
    isThinking, 
    setThinking,
    sections,
    lockSection,
    unlockSection,
    setValidated
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

  return (
    <div className="flex min-h-screen bg-surface">
      {/* MAIN CONTENT AREA */}
      <div className="flex-1 pr-[380px]"> {/* Space for fixed AgentPanel */}
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
            {/* SECTION 1 */}
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
                   <p className="text-sm text-on-surface/80 leading-relaxed">
                     Once all Tier 1 fields are filled, trigger validation to proceed.
                   </p>
                   <button 
                     onClick={() => setValidated(1, true)}
                     className="px-4 py-2 bg-secondary/10 border border-secondary/20 text-secondary text-xs font-bold uppercase tracking-widest rounded hover:bg-secondary/20 transition-all"
                   >
                     Validate Section 01
                   </button>
                </div>
              </div>
            </SectionShell>

            {/* SECTION 2 */}
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
                   <p className="text-sm text-on-surface/80 leading-relaxed">
                     Risk parameters are Tier 1 constraints. They cannot be bypassed by the AI.
                   </p>
                   <button 
                     onClick={() => setValidated(2, true)}
                     className="px-4 py-2 bg-secondary/10 border border-secondary/20 text-secondary text-xs font-bold uppercase tracking-widest rounded hover:bg-secondary/20 transition-all"
                   >
                     Validate Section 02
                   </button>
                </div>
              </div>
            </SectionShell>

            {/* SECTION 3 */}
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
                   <p className="text-sm text-on-surface/80 leading-relaxed">
                     Return targets are advisory. They calibrate the AI's signal selection aggressiveness.
                   </p>
                   <button 
                     onClick={() => setValidated(3, true)}
                     className="px-4 py-2 bg-secondary/10 border border-secondary/20 text-secondary text-xs font-bold uppercase tracking-widest rounded hover:bg-secondary/20 transition-all"
                   >
                     Validate Section 03
                   </button>
                </div>
              </div>
            </SectionShell>
          </div>
        </div>
      </div>

      {/* AGENT PANEL */}
      <AgentPanel
        messages={messages}
        isThinking={isThinking}
        onSendMessage={handleSendMessage}
        currentSection={currentSection}
      />
    </div>
  );
}
