import React from 'react';

export interface ContradictionEntry {
  field: string;
  issue: string;
}

export interface ValidationResponse {
  prose_fields: Record<string, string>;
  gap_questions: string[];
  contradictions: ContradictionEntry[];
  section_complete: boolean;
}

interface SectionValidatorProps {
  title: string;
  sectionNumber: number;
  detailPrompt: string;
  detailText: string;
  setDetailText: (text: string) => void;
  onValidate: () => void;
  validating: boolean;
  validationResponse: ValidationResponse | null;
  isLocked: boolean;
  onUnlock: () => void;
  children: React.ReactNode;
}

export function SectionValidator({
  title,
  sectionNumber,
  detailPrompt,
  detailText,
  setDetailText,
  onValidate,
  validating,
  validationResponse,
  isLocked,
  onUnlock,
  children
}: SectionValidatorProps) {

  const renderTextWithBadges = (text: string) => {
    if (!text) return null;
    return text.split(/(\[EXPLICIT\]|\[INFERRED\]|\[ASSUMED\])/g).map((part, i) => {
      if (part === '[EXPLICIT]') return <span key={i} className="bg-emerald-500/20 text-emerald-400 px-1.5 py-0.5 rounded text-[10px] font-bold tracking-widest ml-1 align-middle">EXPLICIT</span>;
      if (part === '[INFERRED]') return <span key={i} className="bg-amber-500/20 text-amber-400 px-1.5 py-0.5 rounded text-[10px] font-bold tracking-widest ml-1 align-middle">INFERRED</span>;
      if (part === '[ASSUMED]') return <span key={i} className="bg-orange-500/20 text-orange-400 px-1.5 py-0.5 rounded text-[10px] font-bold tracking-widest ml-1 align-middle">ASSUMED</span>;
      return <span key={i}>{part}</span>;
    });
  };

  return (
    <div className={`border rounded-xl transition-all ${isLocked ? 'border-primary/50 bg-primary/5' : 'border-white/10 bg-surface-container-low'} p-6 mb-6`}>
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-headline tracking-tight text-on-surface">
          <span className="text-[#8e8e88] mr-2">{sectionNumber}.</span>
          {title}
        </h2>
        {isLocked && (
          <button 
            onClick={onUnlock}
            className="flex items-center gap-1.5 text-[0.75rem] font-medium text-primary hover:text-primary/80 transition-colors"
          >
            <span className="material-symbols-outlined text-[16px]">lock_open</span>
            Unlock to Edit
          </button>
        )}
      </div>

      <div className={isLocked ? 'opacity-60 pointer-events-none' : ''}>
        {/* Structured Inputs */}
        <div className="space-y-4 mb-6">
          {children}
        </div>

        {/* Detail Box */}
        <div className="space-y-2 mb-6">
          <label className="block text-[0.8125rem] font-semibold text-on-surface flex items-center gap-1.5">
            <span className="material-symbols-outlined text-[16px] text-primary">chat</span>
            Context & Details
          </label>
          <p className="text-[0.75rem] text-[#8e8e88] italic">{detailPrompt}</p>
          <textarea
            value={detailText}
            onChange={(e) => setDetailText(e.target.value)}
            className="w-full h-24 bg-surface-container border border-white/5 rounded-lg p-3 text-[0.8125rem] text-on-surface focus:outline-none focus:ring-1 focus:ring-primary/50"
            placeholder="Write freely..."
          />
        </div>

        {/* Validate Button */}
        {!isLocked && (
          <div className="flex justify-end mb-6">
            <button
              onClick={onValidate}
              disabled={validating}
              className="px-6 py-2 bg-primary-container text-on-primary-container text-[0.8125rem] font-semibold rounded-lg hover:brightness-110 disabled:opacity-50 transition-all flex items-center gap-2"
            >
              {validating ? (
                <>
                  <span className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin"></span>
                  Validating...
                </>
              ) : (
                <>
                  <span className="material-symbols-outlined text-[18px]">verified</span>
                  Validate Section
                </>
              )}
            </button>
          </div>
        )}
      </div>

      {/* Validation Response UI */}
      {validationResponse && (
        <div className="mt-4 space-y-4 border-t border-white/10 pt-4">
          
          {/* Prose Fields (Badge Rendered) */}
          {Object.keys(validationResponse.prose_fields || {}).length > 0 && (
            <div className="space-y-2">
              <h4 className="text-[0.6875rem] font-bold uppercase tracking-widest text-[#8e8e88]">Captured Context</h4>
              <div className="grid grid-cols-1 gap-2">
                {Object.entries(validationResponse.prose_fields).map(([k, v]) => (
                  <div key={k} className="bg-surface-container p-3 rounded-lg border border-white/5 text-[0.8125rem]">
                    <div className="text-[0.625rem] text-primary font-mono mb-1">{k}</div>
                    <div className="text-on-surface leading-relaxed">{renderTextWithBadges(v)}</div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Gap Questions (Callout) */}
          {(validationResponse.gap_questions || []).length > 0 && !isLocked && (
            <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-4">
              <div className="flex items-start gap-2">
                <span className="material-symbols-outlined text-blue-400 text-[18px] mt-0.5">help</span>
                <div>
                  <h4 className="text-[0.75rem] font-bold text-blue-400 mb-1">More Detail Needed</h4>
                  <ul className="space-y-1">
                    {validationResponse.gap_questions.map((g, i) => (
                      <li key={i} className="text-[0.8125rem] text-blue-300/90">{g}</li>
                    ))}
                  </ul>
                  <p className="text-[0.6875rem] text-blue-400/70 mt-2 italic">Please update the detail box above and re-validate.</p>
                </div>
              </div>
            </div>
          )}

          {/* Contradictions (Warning) */}
          {(validationResponse.contradictions || []).length > 0 && !isLocked && (
            <div className="bg-amber-500/10 border border-amber-500/30 rounded-lg p-4">
              <div className="flex items-start gap-2">
                <span className="material-symbols-outlined text-amber-500 text-[18px] mt-0.5">warning</span>
                <div>
                  <h4 className="text-[0.75rem] font-bold text-amber-500 mb-1">Contradiction Detected</h4>
                  <ul className="space-y-2">
                    {validationResponse.contradictions.map((c, i) => (
                      <li key={i} className="text-[0.8125rem] text-amber-500/90">
                        <span className="font-mono text-[0.625rem] bg-amber-500/20 px-1 rounded mr-2">{c.field}</span>
                        {c.issue}
                      </li>
                    ))}
                  </ul>
                  <p className="text-[0.6875rem] text-amber-500/70 mt-2 italic">Please resolve the conflict and re-validate.</p>
                </div>
              </div>
            </div>
          )}

          {/* Success / Lock State Message */}
          {isLocked && validationResponse.section_complete && (
            <div className="flex items-center gap-2 text-emerald-400 text-[0.8125rem] font-medium pt-2">
              <span className="material-symbols-outlined text-[18px]">check_circle</span>
              Section locked and complete.
            </div>
          )}

        </div>
      )}
    </div>
  );
}
