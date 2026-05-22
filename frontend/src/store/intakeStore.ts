import { create } from 'zustand';
import { produce } from 'immer';
import type { AgentMessage, IntakeSchemaV10 } from '../types/intake';
import initialSchema from '../../public/aegis_intake_package/2_blank_schema.json';

interface SectionState {
  locked: boolean;
  validated: boolean;
  validatedAt: string | null;
  checksum: string | null;
}

interface IntakeState {
  currentSection: number;
  schema: IntakeSchemaV10;
  sections: Record<number, SectionState>;
  messages: AgentMessage[];
  isThinking: boolean;
}

interface IntakeActions {
  updateField: (path: string, value: any) => void;
  setCurrentSection: (n: number) => void;
  lockSection: (n: number) => void;
  unlockSection: (n: number) => void;
  setValidated: (n: number, v: boolean) => void;
  addMessage: (msg: AgentMessage) => void;
  setThinking: (v: boolean) => void;
  reset: () => void;
}

const STORAGE_KEY = 'aegis_intake_draft_v10';

// Initialize 10 sections
const defaultSections: Record<number, SectionState> = {};
for (let i = 1; i <= 10; i++) {
  defaultSections[i] = {
    locked: false,
    validated: false,
    validatedAt: null,
    checksum: null,
  };
}

// Helper to set nested value by dot notation
const setNestedValue = (obj: any, path: string, value: any) => {
  const keys = path.split('.');
  let current = obj;
  for (let i = 0; i < keys.length - 1; i++) {
    if (current[keys[i]] === undefined || current[keys[i]] === null) current[keys[i]] = {};
    current = current[keys[i]];
  }
  current[keys[keys.length - 1]] = value;
};

// Initial state recovery from localStorage
const getInitialState = (): Partial<IntakeState> => {
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) {
      const parsed = JSON.parse(saved);
      if (parsed.schema?._schema_version === 'v10.0') {
        return {
          schema: parsed.schema,
          sections: parsed.sections,
          currentSection: parsed.currentSection || 1,
          messages: parsed.messages || [],
        };
      }
    }
  } catch (e) {
    console.error('Failed to restore intake state from localStorage', e);
  }
  return {};
};

export const useIntakeStore = create<IntakeState & IntakeActions>((set) => ({
  // State
  currentSection: 1,
  schema: initialSchema as unknown as IntakeSchemaV10,
  sections: defaultSections,
  messages: [],
  isThinking: false,

  // Restore saved state
  ...getInitialState(),

  // Actions
  updateField: (path, value) => set(produce((state: IntakeState) => {
    setNestedValue(state.schema, path, value);
    
    // Lock Invalidation: If section N is edited, invalidate it and unlock/invalidate downstream (N+1 to 10)
    const getSectionForPath = (p: string): number => {
      if (p.startsWith('mandate_identification') || p.startsWith('capital_structure')) return 1;
      if (p.startsWith('risk_mandate')) return 2;
      if (p.startsWith('return_mandate')) return 3;
      if (p.startsWith('universe_mandate')) return 4;
      if (p.startsWith('strategy_mandate')) return 5;
      if (p.startsWith('operational_mandate')) return 6;
      if (p.startsWith('behavioral_profile')) return 7;
      if (p.startsWith('tax_and_legal')) return 8;
      if (p.startsWith('portfolio_scope_and_macro')) return 9;
      if (p.startsWith('governance_and_review')) return 10;
      return 0;
    };

    const n = getSectionForPath(path);
    if (n > 0) {
      state.sections[n].validated = false;
      for (let i = n + 1; i <= 10; i++) {
        state.sections[i].locked = false;
        state.sections[i].validated = false;
        state.sections[i].validatedAt = null;
      }
    }

    // Trigger automated checks if relevant fields changed
    if (path.includes('max_portfolio_drawdown_pct') || path.includes('target_annual_return_pct')) {
      const drawdown = state.schema.risk_mandate.tier_1_risk_constraints.max_portfolio_drawdown_pct;
      const targetReturn = state.schema.return_mandate.target_annual_return_pct;

      if (drawdown && targetReturn) {
        const impliedVol = drawdown / 2;
        const impliedSharpe = targetReturn / impliedVol;
        
        let feasibility: 'achievable' | 'difficult' | 'implausible' = 'achievable';
        if (impliedSharpe > 2.0) feasibility = 'implausible';
        else if (impliedSharpe > 1.2) feasibility = 'difficult';

        state.schema.filing_notes.sharpe_feasibility_check = {
          implied_sharpe_required: parseFloat(impliedSharpe.toFixed(2)),
          feasibility,
          explanation: feasibility === 'implausible' 
            ? `Target return of ${targetReturn}% with only ${drawdown}% drawdown implies a Sharpe ratio of ${impliedSharpe.toFixed(2)}. This is statistically implausible.`
            : `Implied Sharpe: ${impliedSharpe.toFixed(2)}.`
        };
      }
    }
  })),

  setCurrentSection: (n) => set({ currentSection: n }),

  lockSection: (n) => set(produce((state: IntakeState) => {
    state.sections[n].locked = true;
    state.sections[n].validatedAt = new Date().toISOString();
  })),

  unlockSection: (n) => set(produce((state: IntakeState) => {
    state.sections[n].locked = false;
  })),

  setValidated: (n, v) => set(produce((state: IntakeState) => {
    state.sections[n].validated = v;
  })),

  addMessage: (msg) => set(produce((state: IntakeState) => {
    state.messages.push(msg);
  })),

  setThinking: (v) => set({ isThinking: v }),

  reset: () => set({
    currentSection: 1,
    schema: initialSchema as unknown as IntakeSchemaV10,
    sections: defaultSections,
    messages: [],
    isThinking: false,
  }),


}));

// Debounced Persistence
let saveTimeout: ReturnType<typeof setTimeout> | null = null;
useIntakeStore.subscribe((state) => {
  if (saveTimeout) clearTimeout(saveTimeout);
  saveTimeout = setTimeout(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({
      schema: state.schema,
      sections: state.sections,
      currentSection: state.currentSection,
      messages: state.messages,
    }));
  }, 500);
});
