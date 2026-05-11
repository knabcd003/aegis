import { useState, useEffect } from 'react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';
import { AlertTriangle, Check, ChevronDown, ChevronUp } from 'lucide-react';
import type { CatalystTypeEntry } from '../../types/intake';
import { Toggle } from './Toggle';

/**
 * Utility to merge tailwind classes
 */
function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

const RISK_ACKNOWLEDGMENT_DEFS = [
  {
    key: 'iv_crush_risk_acknowledged',
    label: "IV Crush Risk",
    description: "Implied volatility collapses after the decision regardless of direction, destroying option premium value."
  },
  {
    key: 'gap_risk_acknowledged',
    label: "Gap Risk",
    description: "The position can gap dramatically overnight on the catalyst event."
  },
  {
    key: 'binary_event_risk_acknowledged',
    label: "Binary Event Risk",
    description: "The outcome is binary with extreme price reactions in either direction."
  },
  {
    key: 'information_leakage_risk_acknowledged',
    label: "Information Leakage Risk",
    description: "Pre-event trading can contaminate the post-catalyst signal."
  },
  {
    key: 'pre_revenue_universe_acknowledged',
    label: "Pre-Revenue Universe",
    description: "Nearly all candidates in this category are pre-revenue companies."
  }
];

const CATALYST_TYPE_DEFS = [
  {
    value: 'pead_earnings_momentum',
    label: "PEAD Earnings Momentum",
    description: "Post-earnings announcement drift. Trades the continuation of price movement after an earnings surprise — not the earnings event itself.",
    required_acknowledgments: ['gap_risk_acknowledged']
  },
  {
    value: 'fda_pdufa_biotech',
    label: "FDA / PDUFA Biotech",
    description: "Trades momentum following FDA approval decisions on PDUFA target dates. Binary outcome — stocks can gap 40-60% in either direction.",
    required_acknowledgments: ['iv_crush_risk_acknowledged', 'gap_risk_acknowledged', 'binary_event_risk_acknowledged', 'information_leakage_risk_acknowledged', 'pre_revenue_universe_acknowledged']
  },
  {
    value: 'clinical_trial_readout_phase3',
    label: "Phase III Clinical Readout",
    description: "Momentum following Phase III trial data announcements. Same binary risk profile as FDA decisions.",
    required_acknowledgments: ['iv_crush_risk_acknowledged', 'gap_risk_acknowledged', 'binary_event_risk_acknowledged', 'information_leakage_risk_acknowledged', 'pre_revenue_universe_acknowledged']
  },
  {
    value: 'clinical_trial_readout_phase2',
    label: "Phase II Clinical Readout",
    description: "Earlier stage trial results. Smaller drift magnitude, higher failure rates than Phase III.",
    required_acknowledgments: ['iv_crush_risk_acknowledged', 'gap_risk_acknowledged', 'binary_event_risk_acknowledged', 'information_leakage_risk_acknowledged', 'pre_revenue_universe_acknowledged']
  },
  {
    value: 'ma_announcement',
    label: "M&A Announcement",
    description: "Momentum following merger or acquisition announcements. Deal-break risk applies.",
    required_acknowledgments: ['gap_risk_acknowledged', 'binary_event_risk_acknowledged']
  },
  {
    value: 'index_reconstitution',
    label: "Index Reconstitution",
    description: "Trades forced buying/selling pressure from index additions and deletions. Predictable calendar-driven events.",
    required_acknowledgments: ['gap_risk_acknowledged']
  },
  {
    value: 'management_change',
    label: "Management Change",
    description: "CEO or CFO change momentum. Lower volatility than binary events.",
    required_acknowledgments: ['gap_risk_acknowledged']
  },
  {
    value: 'secondary_offering',
    label: "Secondary Offering",
    description: "Post-secondary offering momentum recovery from the dilution dip.",
    required_acknowledgments: ['gap_risk_acknowledged']
  },
  {
    value: 'short_squeeze_setup',
    label: "Short Squeeze Setup",
    description: "High short-interest catalyst momentum. Long-side only if short selling is disabled.",
    required_acknowledgments: ['gap_risk_acknowledged', 'binary_event_risk_acknowledged']
  },
  {
    value: 'macro_data_surprise',
    label: "Macro Data Surprise",
    description: "Sector and index momentum following economic data surprises. Lower idiosyncratic risk, higher market beta.",
    required_acknowledgments: ['gap_risk_acknowledged']
  }
];

interface CatalystCardGridProps {
  value: CatalystTypeEntry[];
  onChange: (value: CatalystTypeEntry[]) => void;
  onValidityChange?: (valid: boolean) => void;
  disabled?: boolean;
}

export function CatalystCardGrid({
  value = [],
  onChange,
  onValidityChange,
  disabled = false,
}: CatalystCardGridProps) {

  // Check if at least one catalyst is permitted and fully acknowledged
  const checkValidity = (currentValue: CatalystTypeEntry[]) => {
    const valid = currentValue.some(entry => {
      if (!entry.permitted) return false;
      const def = CATALYST_TYPE_DEFS.find(d => d.value === entry.catalyst_type);
      if (!def) return false;
      return def.required_acknowledgments.every(key => (entry.risk_acknowledgments as any)[key]);
    });
    onValidityChange?.(valid);
  };

  useEffect(() => {
    checkValidity(value);
  }, [value]);

  const handleTogglePermitted = (catalystType: string) => {
    const existingEntry = value.find(e => e.catalyst_type === catalystType);
    
    if (!existingEntry) {
      // Create new entry if it doesn't exist
      const newEntry: CatalystTypeEntry = {
        catalyst_type: catalystType,
        permitted: true,
        risk_acknowledgments: {
          iv_crush_risk_acknowledged: false,
          gap_risk_acknowledged: false,
          binary_event_risk_acknowledged: false,
          information_leakage_risk_acknowledged: false,
          pre_revenue_universe_acknowledged: false,
        }
      };
      onChange([...value, newEntry]);
      return;
    }

    const newValue = value.map(entry => {
      if (entry.catalyst_type === catalystType) {
        const isEnabling = !entry.permitted;
        return {
          ...entry,
          permitted: isEnabling,
          risk_acknowledgments: isEnabling 
            ? entry.risk_acknowledgments 
            : {
                iv_crush_risk_acknowledged: false,
                gap_risk_acknowledged: false,
                binary_event_risk_acknowledged: false,
                information_leakage_risk_acknowledged: false,
                pre_revenue_universe_acknowledged: false,
              }
        };
      }
      return entry;
    });
    onChange(newValue);
  };

  const handleToggleAcknowledgment = (catalystType: string, ackKey: string) => {
    const newValue = value.map(entry => {
      if (entry.catalyst_type === catalystType) {
        return {
          ...entry,
          risk_acknowledgments: {
            ...entry.risk_acknowledgments,
            [ackKey]: !(entry.risk_acknowledgments as any)[ackKey]
          }
        };
      }
      return entry;
    });
    onChange(newValue);
  };

  return (
    <div className={cn("grid grid-cols-1 md:grid-cols-2 gap-3 w-full", disabled && "opacity-40 pointer-events-none")}>
      {CATALYST_TYPE_DEFS.map((def) => {
        const entry = value.find(e => e.catalyst_type === def.value) || {
          catalyst_type: def.value,
          permitted: false,
          risk_acknowledgments: {}
        } as CatalystTypeEntry;

        const isComplete = def.required_acknowledgments.every(key => (entry.risk_acknowledgments as any)[key]);
        const isIncomplete = entry.permitted && !isComplete;

        return (
          <div 
            key={def.value} 
            className={cn(
              "flex flex-col border rounded-xl transition-all duration-300 overflow-hidden",
              entry.permitted 
                ? (isIncomplete ? "bg-amber-500/5 border-amber-500/30" : "bg-secondary/5 border-secondary/30") 
                : "bg-surface-container/30 border-white/5"
            )}
          >
            {/* CARD HEADER */}
            <div className={cn(
              "flex items-start justify-between gap-4 p-4",
              entry.permitted && !isIncomplete && "bg-secondary/10 border-l-4 border-l-secondary"
            )}>
              <div className="space-y-1 pr-2">
                <h3 className={cn(
                  "text-[0.8125rem] font-medium tracking-tight",
                  entry.permitted ? "text-on-surface" : "text-on-surface/80"
                )}>
                  {def.label}
                </h3>
                <p className={cn(
                  "text-[0.7rem] leading-relaxed",
                  entry.permitted ? "text-on-surface/60" : "text-[#8e8e88]/60 line-clamp-2"
                )}>
                  {def.description}
                </p>
              </div>
              <div className="pt-1">
                <Toggle
                  label=""
                  value={entry.permitted}
                  onChange={() => handleTogglePermitted(def.value)}
                />
              </div>
            </div>

            {/* EXPANDED SECTION */}
            {entry.permitted && (
              <div className="p-4 pt-0 space-y-4 animate-in slide-in-from-top-2 duration-300">
                <div className="pt-4 border-t border-white/5 space-y-3">
                  <label className="text-[0.625rem] font-bold uppercase tracking-widest text-[#8e8e88]/50">
                    Required Risk Acknowledgments
                  </label>
                  <div className="space-y-3">
                    {def.required_acknowledgments.map((ackKey) => {
                      const ackDef = RISK_ACKNOWLEDGMENT_DEFS.find(a => a.key === ackKey)!;
                      const isChecked = (entry.risk_acknowledgments as any)[ackKey];
                      
                      return (
                        <label 
                          key={ackKey}
                          className="flex items-start gap-3 cursor-pointer group"
                        >
                          <div 
                            onClick={() => handleToggleAcknowledgment(def.value, ackKey)}
                            className={cn(
                              "mt-0.5 w-4 h-4 rounded border flex items-center justify-center transition-all",
                              isChecked ? "bg-secondary border-secondary" : "bg-surface-container-low border-white/10 group-hover:border-white/20"
                            )}
                          >
                            {isChecked && <Check size={10} className="text-surface font-bold" />}
                          </div>
                          <div className="space-y-0.5" onClick={() => handleToggleAcknowledgment(def.value, ackKey)}>
                            <p className={cn(
                              "text-[0.75rem] font-medium leading-none",
                              isChecked ? "text-on-surface" : "text-[#8e8e88]"
                            )}>
                              {ackDef.label}
                            </p>
                            <p className="text-[0.625rem] text-[#8e8e88]/60 leading-normal">
                              {ackDef.description}
                            </p>
                          </div>
                        </label>
                      );
                    })}
                  </div>
                </div>

                {isIncomplete && (
                  <div className="flex items-center gap-2 py-2 text-amber-500 animate-pulse">
                    <AlertTriangle size={14} />
                    <span className="text-[0.625rem] font-bold uppercase tracking-widest">
                      Complete all acknowledgments to enable
                    </span>
                  </div>
                )}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
