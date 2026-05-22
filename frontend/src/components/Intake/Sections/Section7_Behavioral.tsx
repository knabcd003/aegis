import { useIntakeStore } from '../../../store/intakeStore';
import { SegmentedControl } from '../SegmentedControl';
import { Stepper } from '../Stepper';
import { MultiSelectChips } from '../MultiSelectChips';
import { Toggle } from '../Toggle';
import { Info, ArrowRight } from 'lucide-react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

/**
 * Utility to merge tailwind classes
 */
function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

interface SectionProps {
  onFieldFocus?: (path: string) => void;
  onFieldBlur?: () => void;
}

export function Section7_Behavioral({ onFieldFocus, onFieldBlur }: SectionProps) {
  const schema = useIntakeStore((state) => state.schema);
  const updateField = useIntakeStore((state) => state.updateField);
  const setCurrentSection = useIntakeStore((state) => state.setCurrentSection);
  const unlockSection = useIntakeStore((state) => state.unlockSection);

  const profile = schema.behavioral_profile;
  const riskRegret = schema.risk_mandate.tier_2_risk_context.regret_asymmetry;

  const handleEditSection2 = () => {
    unlockSection(2);
    setCurrentSection(2);
  };

  // Regret Profile Summary Derived Logic
  const getRegretSummary = () => {
    if (!riskRegret.type) return "Complete Section 2 to see your regret profile.";
    
    const { type, magnitude } = riskRegret;
    
    if (type === 'loss_regret_dominant') {
      if (magnitude === 'mild') return "You regret holding losers slightly more than missing winners. Exits will lean time-based.";
      if (magnitude === 'moderate') return "You strongly regret holding losers. Exits will be strict and time-based.";
      if (magnitude === 'severe') return "Holding losers is your primary fear. Exits will be aggressive and time-enforced.";
    }
    
    if (type === 'miss_regret_dominant') {
      if (magnitude === 'mild') return "You regret missing winners slightly more. Trailing stops will allow momentum to run.";
      if (magnitude === 'moderate') return "Missing winners bothers you significantly. Exits will use wide trailing stops.";
      if (magnitude === 'severe') return "Missing winners is your primary concern. Maximum continuation mode — no time-based override.";
    }
    
    if (type === 'balanced') return "Balanced regret profile. Hybrid exit rules — time-based floor with trailing stop.";
    
    return "Complete Section 2 to see your regret profile.";
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
      
      {/* 7.0 REGRET SUMMARY CARD */}
      <div className="p-6 bg-secondary/5 border border-secondary/20 rounded-2xl relative overflow-hidden group">
        <div className="absolute left-0 top-0 bottom-0 w-1 bg-secondary shadow-[0_0_15px_rgba(172,206,197,0.5)]" />
        <div className="space-y-2">
          <label className="text-[0.625rem] font-bold uppercase tracking-[0.2em] text-secondary">
            Regret Profile (from Section 2)
          </label>
          <p className={cn(
            "text-[0.9375rem] font-medium leading-relaxed",
            !riskRegret.type ? "text-[#8e8e88] italic" : "text-on-surface"
          )}>
            {getRegretSummary()}
          </p>
          <button 
            onClick={handleEditSection2}
            className="flex items-center gap-1.5 text-[0.6875rem] font-bold text-[#8e8e88] hover:text-secondary transition-colors pt-2"
          >
            Edit in Section 2 <ArrowRight size={12} />
          </button>
        </div>
      </div>

      {/* 7.1 DISPOSITION EFFECT */}
      <div className="space-y-6" data-field-path="behavioral_profile.disposition_effect_tendency.self_assessed">
        <div className="space-y-1">
          <label className="text-[0.6875rem] font-bold uppercase tracking-[0.15em] text-[#8e8e88]">
            How often do you sell winning positions too early?
          </label>
          <p className="text-xs text-[#8e8e88]/60">
            Taking profits prematurely before the momentum has exhausted.
          </p>
        </div>
        <SegmentedControl
          value={profile.disposition_effect_tendency.self_assessed}
          onChange={(val) => updateField('behavioral_profile.disposition_effect_tendency.self_assessed', val)}
          options={[
            { value: 'strong', label: 'Often', description: "I regularly exit winners before they've fully played out" },
            { value: 'moderate', label: 'Sometimes', description: "Occasionally I take profits too soon" },
            { value: 'mild', label: 'Rarely', description: "I generally let winners run" },
            { value: 'none', label: 'Never', description: "I have no issue holding winning positions" }
          ]}
        />
      </div>

      {/* 7.2 LOSS AVERSION */}
      <div className="pt-10 border-t border-white/5 space-y-6" data-field-path="behavioral_profile.loss_aversion_coefficient">
        <label className="text-[0.6875rem] font-bold uppercase tracking-[0.15em] text-[#8e8e88]">
          When you lose $1,000, how does it feel compared to gaining $1,000?
        </label>
        <SegmentedControl
          value={profile.loss_aversion_coefficient}
          onChange={(val) => updateField('behavioral_profile.loss_aversion_coefficient', val)}
          options={[
            { value: 'standard_2to1', label: 'Twice as bad', description: "Standard loss aversion — losses sting about 2x more than gains" },
            { value: 'elevated_3to1', label: 'Three times as bad', description: "Losses hit significantly harder than equivalent gains" },
            { value: 'severe_4plus_to_1', label: 'Four times or more', description: "Losses are deeply painful relative to equivalent gains" }
          ]}
        />
      </div>

      {/* 7.3 OVERTRADING */}
      <div className="pt-10 border-t border-white/5 space-y-6">
        <label className="text-[0.6875rem] font-bold uppercase tracking-[0.15em] text-[#8e8e88]">
          Do you tend to overtrade or chase signals?
        </label>
        <SegmentedControl
          value={profile.overtrading_tendency.self_assessed}
          onChange={(val) => updateField('behavioral_profile.overtrading_tendency.self_assessed', val)}
          options={[
            { value: 'frequent', label: 'Often', description: "I regularly enter more positions than I should" },
            { value: 'occasional', label: 'Sometimes', description: "Occasionally I chase signals I shouldn't" },
            { value: 'rare', label: 'Rarely', description: "I generally wait for high-conviction setups" },
            { value: 'none', label: 'Never', description: "I have strong discipline around signal selection" }
          ]}
        />
      </div>

      {/* 7.4 REVIEW & COOLING OFF */}
      <div className="pt-10 border-t border-white/5 grid grid-cols-1 md:grid-cols-2 gap-10">
        <div className="space-y-6">
          <div className="space-y-1">
            <label className="text-[0.6875rem] font-bold uppercase tracking-[0.15em] text-[#8e8e88]">
              Consecutive losing trades before review
            </label>
            <p className="text-[0.625rem] text-[#8e8e88]/50 leading-relaxed uppercase tracking-wider">
              Aegis pauses and asks for review. This is not a shutdown.
            </p>
          </div>
          <Stepper
            label="Consecutive losses before review"
            value={profile.max_consecutive_losses_review_trigger || 5}
            onChange={(val) => updateField('behavioral_profile.max_consecutive_losses_review_trigger', val)}
            min={3}
            max={15}
          />
        </div>

        <div className="space-y-6">
          <label className="text-[0.6875rem] font-bold uppercase tracking-[0.15em] text-[#8e8e88]">
            What triggers a mandatory cooling-off period?
          </label>
          <MultiSelectChips
            value={profile.cooling_off_requirements.trigger || []}
            onChange={(val) => updateField('behavioral_profile.cooling_off_requirements.trigger', val)}
            options={[
              { value: 'drawdown_breach', label: 'Drawdown Breach' },
              { value: 'consecutive_loss_threshold', label: 'Consecutive Loss Threshold' },
              { value: 'major_adverse_event', label: 'Major Adverse Event' }
            ]}
          />
        </div>
      </div>

      {/* 7.5 COOLING OFF DURATION */}
      {(profile.cooling_off_requirements.trigger?.length || 0) > 0 && (
        <div className="pt-8 animate-in fade-in slide-in-from-top-4 duration-500">
          <div className="space-y-4 max-w-sm">
            <div className="space-y-1">
              <label className="text-[0.6875rem] font-bold uppercase tracking-[0.15em] text-[#8e8e88]">
                Cooling-off period duration (Days)
              </label>
              <p className="text-[0.625rem] text-[#8e8e88]/50 leading-relaxed uppercase tracking-wider">
                New positions are blocked. Existing positions continue normally.
              </p>
            </div>
            <Stepper
              label="Cooling-off duration"
              value={profile.cooling_off_requirements.cooling_off_days || 3}
              onChange={(val) => updateField('behavioral_profile.cooling_off_requirements.cooling_off_days', val)}
              min={1}
              max={30}
            />
          </div>
        </div>
      )}

      {/* 7.6 SIGNAL OVERRIDE */}
      <div className="pt-10 border-t border-white/5 space-y-8">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          <Toggle
            label="Can you manually reject a signal?"
            helper="Allows you to veto a system signal you disagree with"
            value={profile.signal_override_policy.can_user_override}
            onChange={(val) => updateField('behavioral_profile.signal_override_policy.can_user_override', val)}
          />
          {profile.signal_override_policy.can_user_override && (
            <div className="animate-in fade-in slide-in-from-left-4 duration-500">
              <Toggle
                label="Require a written reason for each override?"
                helper="Forces you to document why you rejected the signal"
                value={profile.signal_override_policy.override_documentation_required}
                onChange={(val) => updateField('behavioral_profile.signal_override_policy.override_documentation_required', val)}
              />
            </div>
          )}
        </div>
      </div>

      {/* 7.7 ENFORCEMENT SUMMARY PANEL */}
      <div className="p-6 bg-white/2 border border-white/5 rounded-2xl space-y-4">
        <div className="flex items-center gap-2 text-[#8e8e88]">
          <Info size={16} />
          <span className="text-[0.6875rem] font-bold uppercase tracking-widest">How these settings affect strategy generation</span>
        </div>
        <div className="space-y-3 pl-6 border-l border-white/5">
          {['strong', 'moderate'].includes(profile.disposition_effect_tendency.self_assessed) && (
            <p className="text-xs text-[#8e8e88] leading-relaxed animate-in fade-in slide-in-from-left-2">• Minimum hold period enforced on winning positions before exits are permitted</p>
          )}
          {profile.loss_aversion_coefficient === 'elevated_3to1' && (
            <p className="text-xs text-[#8e8e88] leading-relaxed animate-in fade-in slide-in-from-left-2">• Stop distances tightened to 1.5× ATR. Position sizes reduced 15% to compensate.</p>
          )}
          {profile.loss_aversion_coefficient === 'severe_4plus_to_1' && (
            <p className="text-xs text-[#8e8e88] leading-relaxed animate-in fade-in slide-in-from-left-2">• Stop distances tightened to 1.0× ATR. Position sizes reduced 25%. Only top-decile signals entered.</p>
          )}
          {profile.overtrading_tendency.self_assessed === 'frequent' && (
            <p className="text-xs text-[#8e8e88] leading-relaxed animate-in fade-in slide-in-from-left-2">• Signal threshold raised to top 20th percentile. 48-hour lockout between new position entries.</p>
          )}
          {profile.overtrading_tendency.self_assessed === 'occasional' && (
            <p className="text-xs text-[#8e8e88] leading-relaxed animate-in fade-in slide-in-from-left-2">• Signal threshold raised to top 30th percentile.</p>
          )}
          {(profile.cooling_off_requirements.trigger?.length || 0) > 0 && (
            <p className="text-xs text-[#8e8e88] leading-relaxed animate-in fade-in slide-in-from-left-2">
              • System blocks all new entries for {profile.cooling_off_requirements.cooling_off_days || 'X'} days after a {profile.cooling_off_requirements.trigger?.join('/') || 'trigger'} event.
            </p>
          )}
          {Object.values(profile.disposition_effect_tendency).every(v => !v || v === 'none' || v === 'mild' || v === 'rare') && 
           profile.loss_aversion_coefficient === 'standard_2to1' && 
           !profile.cooling_off_requirements.trigger?.length && (
            <p className="text-xs text-[#8e8e88]/40 italic leading-relaxed">No mechanical behavioral adjustments active. Using institutional standard defaults.</p>
          )}
        </div>
      </div>

      {/* 7.8 DETAIL BOX */}
      <div className="pt-10 border-t border-white/5 space-y-3">
        <label className="text-[0.6875rem] font-bold uppercase tracking-[0.15em] text-[#8e8e88]">
          Psychological Patterns & Drawdown Commitments
        </label>
        <textarea
          value={profile.behavioral_constraints_during_drawdown || ''}
          onChange={(e) => updateField('behavioral_profile.behavioral_constraints_during_drawdown', e.target.value)}
          placeholder="Describe your psychological relationship with trading. What patterns have you noticed in yourself — good and bad?"
          className="w-full bg-surface-container/30 border border-white/5 rounded-xl px-4 py-3 text-sm text-on-surface placeholder-[#8e8e88]/30 min-h-[150px] outline-none focus:border-secondary/30 transition-all"
        />
      </div>
    </div>
  );
}
