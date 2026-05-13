import { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { SectionValidator } from '../components/Intake/SectionValidator';
import type { ValidationResponse } from '../components/Intake/SectionValidator';
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors
} from '@dnd-kit/core';
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  verticalListSortingStrategy,
  useSortable
} from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';

const API = 'http://localhost:8000/api/intake';

type Step = 'input' | 'review' | 'launched';

// Priority Item Component for Section 7
function SortablePriorityItem({ id, label }: { id: string, label: string }) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
  } = useSortable({ id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      {...attributes}
      {...listeners}
      className="bg-surface-container border border-white/10 p-3 rounded-lg mb-2 flex items-center gap-3 cursor-grab active:cursor-grabbing text-[0.8125rem] text-on-surface"
    >
      <span className="material-symbols-outlined text-[#8e8e88] text-[18px]">drag_indicator</span>
      {label}
    </div>
  );
}

const DEFAULT_PRIORITIES = [
  { id: 'risk_control', label: 'Risk Control' },
  { id: 'universe_specificity', label: 'Universe Specificity' },
  { id: 'return_target', label: 'Return Target' },
  { id: 'diversification', label: 'Diversification' },
  { id: 'strategy_type_adherence', label: 'Strategy Type Adherence' },
  { id: 'fundamental_quality', label: 'Fundamental Quality' },
  { id: 'execution_feasibility', label: 'Execution Feasibility' },
];

export function IntakePage() {
  const navigate = useNavigate();
  const [step, setStep] = useState<Step>('input');
  
  // Section 1 State
  const [s1Capital, setS1Capital] = useState<number | ''>('');
  const [s1AccountType, setS1AccountType] = useState('taxable');
  const [s1Existing, setS1Existing] = useState('');
  const [s1NeverTouch, setS1NeverTouch] = useState('');
  const [s1Detail, setS1Detail] = useState('');
  
  // Section 2 State
  const [s2Drawdown, setS2Drawdown] = useState<number | ''>('');
  const [s2Concurrent, setS2Concurrent] = useState<number | ''>('');
  const [s2Leverage, setS2Leverage] = useState(false);
  const [s2Detail, setS2Detail] = useState('');

  // Section 3 State
  const [s3Objective, setS3Objective] = useState('growth');
  const [s3Return, setS3Return] = useState<number | ''>('');
  const [s3Benchmark, setS3Benchmark] = useState('SPY');
  const [s3Horizon, setS3Horizon] = useState<number | ''>('');
  const [s3Detail, setS3Detail] = useState('');

  // Section 4 State
  const [s4Assets, setS4Assets] = useState<string[]>([]);
  const [s4Sectors, setS4Sectors] = useState<string[]>([]);
  const [s4Volume, setS4Volume] = useState<number | ''>('');
  const [s4Detail, setS4Detail] = useState('');

  // Section 5 State
  const [s5Catalysts, setS5Catalysts] = useState<string[]>([]);
  const [s5Options, setS5Options] = useState(false);
  const [s5Short, setS5Short] = useState(false);
  const [s5Detail, setS5Detail] = useState('');

  // Section 6 State
  const [s6Brokerage, setS6Brokerage] = useState('');
  const [s6PrePost, setS6PrePost] = useState(false);
  const [s6Order, setS6Order] = useState('limit');
  const [s6Detail, setS6Detail] = useState('');

  // Section 7 State
  const [s7Priorities, setS7Priorities] = useState(DEFAULT_PRIORITIES);
  const [s7Detail, setS7Detail] = useState(''); // Trade-off philosophy

  // Section States (locked & validation responses)
  const [validatingSection, setValidatingSection] = useState<number | null>(null);
  const [sectionResponses, setSectionResponses] = useState<Record<number, ValidationResponse>>({});
  const [lockedSections, setLockedSections] = useState<Record<number, boolean>>({});

  // Review state
  const [reviewing, setReviewing] = useState(false);
  const [reviewResult, setReviewResult] = useState<any>(null);
  const [confirming, setConfirming] = useState(false);
  const [confirmResult, setConfirmResult] = useState<any>(null);
  const [error, setError] = useState('');

  // Load draft from localStorage on mount
  useEffect(() => {
    const draft = localStorage.getItem('aegis_intake_draft');
    if (draft) {
      try {
        const parsed = JSON.parse(draft);
        setS1Capital(parsed.s1Capital ?? '');
        setS1AccountType(parsed.s1AccountType ?? 'taxable');
        setS1Existing(parsed.s1Existing ?? '');
        setS1NeverTouch(parsed.s1NeverTouch ?? '');
        setS1Detail(parsed.s1Detail ?? '');
        
        setS2Drawdown(parsed.s2Drawdown ?? '');
        setS2Concurrent(parsed.s2Concurrent ?? '');
        setS2Leverage(parsed.s2Leverage ?? false);
        setS2Detail(parsed.s2Detail ?? '');

        setS3Objective(parsed.s3Objective ?? 'growth');
        setS3Return(parsed.s3Return ?? '');
        setS3Benchmark(parsed.s3Benchmark ?? 'SPY');
        setS3Horizon(parsed.s3Horizon ?? '');
        setS3Detail(parsed.s3Detail ?? '');

        setS4Assets(parsed.s4Assets ?? []);
        setS4Sectors(parsed.s4Sectors ?? []);
        setS4Volume(parsed.s4Volume ?? '');
        setS4Detail(parsed.s4Detail ?? '');

        setS5Catalysts(parsed.s5Catalysts ?? []);
        setS5Options(parsed.s5Options ?? false);
        setS5Short(parsed.s5Short ?? false);
        setS5Detail(parsed.s5Detail ?? '');

        setS6Brokerage(parsed.s6Brokerage ?? '');
        setS6PrePost(parsed.s6PrePost ?? false);
        setS6Order(parsed.s6Order ?? 'limit');
        setS6Detail(parsed.s6Detail ?? '');

        setS7Priorities(parsed.s7Priorities ?? DEFAULT_PRIORITIES);
        setS7Detail(parsed.s7Detail ?? '');

        setSectionResponses(parsed.sectionResponses ?? {});
        setLockedSections(parsed.lockedSections ?? {});
      } catch (e) {
        console.error('Failed to parse draft', e);
      }
    }
  }, []);

  // Save to localStorage on change
  useEffect(() => {
    const state = {
      s1Capital, s1AccountType, s1Existing, s1NeverTouch, s1Detail,
      s2Drawdown, s2Concurrent, s2Leverage, s2Detail,
      s3Objective, s3Return, s3Benchmark, s3Horizon, s3Detail,
      s4Assets, s4Sectors, s4Volume, s4Detail,
      s5Catalysts, s5Options, s5Short, s5Detail,
      s6Brokerage, s6PrePost, s6Order, s6Detail,
      s7Priorities, s7Detail,
      sectionResponses, lockedSections
    };
    localStorage.setItem('aegis_intake_draft', JSON.stringify(state));
  }, [
    s1Capital, s1AccountType, s1Existing, s1NeverTouch, s1Detail,
    s2Drawdown, s2Concurrent, s2Leverage, s2Detail,
    s3Objective, s3Return, s3Benchmark, s3Horizon, s3Detail,
    s4Assets, s4Sectors, s4Volume, s4Detail,
    s5Catalysts, s5Options, s5Short, s5Detail,
    s6Brokerage, s6PrePost, s6Order, s6Detail,
    s7Priorities, s7Detail,
    sectionResponses, lockedSections
  ]);

  const unlockSectionAndDownstream = (sectionId: number) => {
    setLockedSections(prev => {
      const next = { ...prev };
      for (let i = sectionId; i <= 7; i++) {
        next[i] = false;
      }
      return next;
    });
  };

  const handleValidateSection = async (sectionId: number, structured_fields: any, detail_text: string) => {
    setValidatingSection(sectionId);
    try {
      const res = await fetch(`${API}/validate/validate_section`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ section_id: sectionId, structured_fields, detail_text })
      });
      const data = await res.json();
      setSectionResponses(prev => ({ ...prev, [sectionId]: data }));
      if (data.section_complete) {
        setLockedSections(prev => ({ ...prev, [sectionId]: true }));
      }
    } catch (e) {
      console.error(e);
    }
    setValidatingSection(null);
  };

  // Build the full v9 schema from all section states
  const buildFullSchema = () => {
    return {
      _schema_version: 'v9.0',
      _path: 'A',
      mandate_hard_constraints: {
        investable_capital: s1Capital ? Number(s1Capital) : null,
        account_type: s1AccountType,
        max_portfolio_drawdown_pct: s2Drawdown ? Number(s2Drawdown) / 100 : null,
        max_concurrent_live_strategies: s2Concurrent ? Number(s2Concurrent) : null,
        leverage_permitted: s2Leverage,
        universe_hard_filters: {
          asset_classes_permitted: s4Assets,
          sectors_of_interest: s4Sectors,
          min_avg_daily_volume_usd: s4Volume ? Number(s4Volume) : null,
          tickers_never_touch: s1NeverTouch ? s1NeverTouch.split(',').map(s => s.trim()) : []
        }
      },
      investor_profile: {
        ...(sectionResponses[1]?.prose_fields || {})
      },
      portfolio_scope: {
        ...(sectionResponses[1]?.prose_fields || {})
      },
      risk_profile: {
        ...(sectionResponses[2]?.prose_fields || {})
      },
      performance_targets: {
        primary_objective: s3Objective,
        target_annual_return_pct: s3Return ? Number(s3Return) / 100 : null,
        benchmark: s3Benchmark,
        target_return_horizon_months: s3Horizon ? Number(s3Horizon) : null,
        ...(sectionResponses[3]?.prose_fields || {})
      },
      universe_mandate: {
        existing_holdings: s1Existing ? s1Existing.split(',').map(s => s.trim()) : [],
        ...(sectionResponses[4]?.prose_fields || {})
      },
      strategy_intent: {
        ...(sectionResponses[5]?.prose_fields || {})
      },
      execution_profile: {
        brokerage_constraints: s6Brokerage,
        pre_post_market_capable: s6PrePost,
        order_type_philosophy: s6Order,
        ...(sectionResponses[6]?.prose_fields || {})
      },
      mandate_priority_hierarchy: {
        ordered_priorities: s7Priorities.map((p, i) => ({ rank: i + 1, dimension: p.id })),
        ...(sectionResponses[7]?.prose_fields || {})
      }
    };
  };

  const handleReview = async () => {
    setReviewing(true);
    setError('');
    const schema = buildFullSchema();
    try {
      const res = await fetch(`${API}/confirm/review`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(schema)
      });
      const data = await res.json();
      setReviewResult(data);
      setStep('review');
    } catch (e: any) {
      setError(e.message || 'Review failed');
    }
    setReviewing(false);
  };

  const handleConfirm = async () => {
    setConfirming(true);
    try {
      const res = await fetch(`${API}/confirm`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(reviewResult.schema_updated)
      });
      const data = await res.json();
      setConfirmResult(data);
      setStep('launched');
      localStorage.removeItem('aegis_intake_draft');
    } catch (e: any) {
      setError(e.message || 'Confirmation failed');
    }
    setConfirming(false);
  };

  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates })
  );

  const handleDragEnd = (event: any) => {
    const { active, over } = event;
    if (over && active.id !== over.id) {
      setS7Priorities((items) => {
        const oldIndex = items.findIndex(i => i.id === active.id);
        const newIndex = items.findIndex(i => i.id === over.id);
        return arrayMove(items, oldIndex, newIndex);
      });
      unlockSectionAndDownstream(7);
    }
  };

  const allSectionsLocked = useMemo(() => {
    return [1,2,3,4,5,6,7].every(i => lockedSections[i]);
  }, [lockedSections]);

  if (step === 'input') {
    return (
      <div className="max-w-3xl mx-auto space-y-8 pb-32">
        <div>
          <h1 className="font-headline text-4xl font-light tracking-tight text-on-surface">
            Define Your Mandate
          </h1>
          <p className="text-[#8e8e88] mt-2 max-w-2xl leading-relaxed">
            Fill out each section below to construct your investment mandate. Validating a section locks it in.
          </p>
        </div>

        <SectionValidator
          title="Foundation"
          sectionNumber={1}
          detailPrompt="Tell us about your existing portfolio and what role you want Aegis to play."
          detailText={s1Detail}
          setDetailText={(t) => { setS1Detail(t); unlockSectionAndDownstream(1); }}
          isLocked={!!lockedSections[1]}
          onUnlock={() => unlockSectionAndDownstream(1)}
          validating={validatingSection === 1}
          validationResponse={sectionResponses[1]}
          onValidate={() => handleValidateSection(1, { capital: s1Capital, accountType: s1AccountType, existing: s1Existing, neverTouch: s1NeverTouch }, s1Detail)}
        >
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs text-[#8e8e88] mb-1">Investable Capital ($)</label>
              <input type="number" value={s1Capital} onChange={(e) => { setS1Capital(Number(e.target.value)); unlockSectionAndDownstream(1); }} className="w-full bg-surface-container border border-white/5 rounded-lg px-3 py-2 text-sm focus:ring-1 focus:ring-primary/50 text-on-surface" placeholder="100000" />
            </div>
            <div>
              <label className="block text-xs text-[#8e8e88] mb-1">Account Type</label>
              <select value={s1AccountType} onChange={(e) => { setS1AccountType(e.target.value); unlockSectionAndDownstream(1); }} className="w-full bg-surface-container border border-white/5 rounded-lg px-3 py-2 text-sm focus:ring-1 focus:ring-primary/50 text-on-surface">
                <option value="taxable">Taxable Brokerage</option>
                <option value="ira">Traditional IRA</option>
                <option value="roth">Roth IRA</option>
                <option value="401k">401k</option>
              </select>
            </div>
            <div>
              <label className="block text-xs text-[#8e8e88] mb-1">Existing Holdings (Tickers)</label>
              <input type="text" value={s1Existing} onChange={(e) => { setS1Existing(e.target.value); unlockSectionAndDownstream(1); }} className="w-full bg-surface-container border border-white/5 rounded-lg px-3 py-2 text-sm focus:ring-1 focus:ring-primary/50 text-on-surface" placeholder="AAPL, TSLA" />
            </div>
            <div>
              <label className="block text-xs text-[#8e8e88] mb-1">Holdings to Never Touch (Tickers)</label>
              <input type="text" value={s1NeverTouch} onChange={(e) => { setS1NeverTouch(e.target.value); unlockSectionAndDownstream(1); }} className="w-full bg-surface-container border border-white/5 rounded-lg px-3 py-2 text-sm focus:ring-1 focus:ring-primary/50 text-on-surface" placeholder="VTI" />
            </div>
          </div>
        </SectionValidator>

        <SectionValidator
          title="Risk"
          sectionNumber={2}
          detailPrompt="How do you think about risk? Describe your tolerance for volatility, overnight gaps, concentration, and past experiences."
          detailText={s2Detail}
          setDetailText={(t) => { setS2Detail(t); unlockSectionAndDownstream(2); }}
          isLocked={!!lockedSections[2]}
          onUnlock={() => unlockSectionAndDownstream(2)}
          validating={validatingSection === 2}
          validationResponse={sectionResponses[2]}
          onValidate={() => handleValidateSection(2, { drawdown: s2Drawdown, concurrent: s2Concurrent, leverage: s2Leverage }, s2Detail)}
        >
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs text-[#8e8e88] mb-1">Max Portfolio Drawdown (%)</label>
              <input type="number" max="100" min="1" value={s2Drawdown} onChange={(e) => { setS2Drawdown(Number(e.target.value)); unlockSectionAndDownstream(2); }} className="w-full bg-surface-container border border-white/5 rounded-lg px-3 py-2 text-sm focus:ring-1 focus:ring-primary/50 text-on-surface" placeholder="15" />
            </div>
            <div>
              <label className="block text-xs text-[#8e8e88] mb-1">Max Concurrent Strategies</label>
              <input type="number" value={s2Concurrent} onChange={(e) => { setS2Concurrent(Number(e.target.value)); unlockSectionAndDownstream(2); }} className="w-full bg-surface-container border border-white/5 rounded-lg px-3 py-2 text-sm focus:ring-1 focus:ring-primary/50 text-on-surface" placeholder="5" />
            </div>
            <div className="col-span-2 flex items-center gap-2">
              <input type="checkbox" checked={s2Leverage} onChange={(e) => { setS2Leverage(e.target.checked); unlockSectionAndDownstream(2); }} className="w-4 h-4" />
              <label className="text-sm text-on-surface">Permit Leverage</label>
            </div>
          </div>
        </SectionValidator>

        <SectionValidator
          title="Performance Targets"
          sectionNumber={3}
          detailPrompt="What does success look like? What would make you pull the plug on this?"
          detailText={s3Detail}
          setDetailText={(t) => { setS3Detail(t); unlockSectionAndDownstream(3); }}
          isLocked={!!lockedSections[3]}
          onUnlock={() => unlockSectionAndDownstream(3)}
          validating={validatingSection === 3}
          validationResponse={sectionResponses[3]}
          onValidate={() => handleValidateSection(3, { objective: s3Objective, return: s3Return, benchmark: s3Benchmark, horizon: s3Horizon }, s3Detail)}
        >
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs text-[#8e8e88] mb-1">Primary Objective</label>
              <select value={s3Objective} onChange={(e) => { setS3Objective(e.target.value); unlockSectionAndDownstream(3); }} className="w-full bg-surface-container border border-white/5 rounded-lg px-3 py-2 text-sm focus:ring-1 focus:ring-primary/50 text-on-surface">
                <option value="growth">Capital Growth</option>
                <option value="income">Income Generation</option>
                <option value="beat_benchmark">Beat Benchmark</option>
                <option value="risk_adjusted">Risk-Adjusted Return</option>
              </select>
            </div>
            <div>
              <label className="block text-xs text-[#8e8e88] mb-1">Target Annual Return (%)</label>
              <input type="number" value={s3Return} onChange={(e) => { setS3Return(Number(e.target.value)); unlockSectionAndDownstream(3); }} className="w-full bg-surface-container border border-white/5 rounded-lg px-3 py-2 text-sm focus:ring-1 focus:ring-primary/50 text-on-surface" placeholder="20" />
            </div>
            <div>
              <label className="block text-xs text-[#8e8e88] mb-1">Benchmark</label>
              <input type="text" value={s3Benchmark} onChange={(e) => { setS3Benchmark(e.target.value); unlockSectionAndDownstream(3); }} className="w-full bg-surface-container border border-white/5 rounded-lg px-3 py-2 text-sm focus:ring-1 focus:ring-primary/50 text-on-surface" placeholder="SPY" />
            </div>
            <div>
              <label className="block text-xs text-[#8e8e88] mb-1">Target Horizon (Months)</label>
              <input type="number" value={s3Horizon} onChange={(e) => { setS3Horizon(Number(e.target.value)); unlockSectionAndDownstream(3); }} className="w-full bg-surface-container border border-white/5 rounded-lg px-3 py-2 text-sm focus:ring-1 focus:ring-primary/50 text-on-surface" placeholder="12" />
            </div>
          </div>
        </SectionValidator>

        <SectionValidator
          title="Universe"
          sectionNumber={4}
          detailPrompt="What do you want to trade and why? Include fundamental requirements (profitability, P/E) and market insights."
          detailText={s4Detail}
          setDetailText={(t) => { setS4Detail(t); unlockSectionAndDownstream(4); }}
          isLocked={!!lockedSections[4]}
          onUnlock={() => unlockSectionAndDownstream(4)}
          validating={validatingSection === 4}
          validationResponse={sectionResponses[4]}
          onValidate={() => handleValidateSection(4, { assets: s4Assets, sectors: s4Sectors, volume: s4Volume }, s4Detail)}
        >
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs text-[#8e8e88] mb-1">Asset Classes (comma separated)</label>
              <input type="text" value={s4Assets.join(', ')} onChange={(e) => { setS4Assets(e.target.value.split(',').map(s=>s.trim())); unlockSectionAndDownstream(4); }} className="w-full bg-surface-container border border-white/5 rounded-lg px-3 py-2 text-sm focus:ring-1 focus:ring-primary/50 text-on-surface" placeholder="Equities, ETFs" />
            </div>
            <div>
              <label className="block text-xs text-[#8e8e88] mb-1">Sectors of Interest</label>
              <input type="text" value={s4Sectors.join(', ')} onChange={(e) => { setS4Sectors(e.target.value.split(',').map(s=>s.trim())); unlockSectionAndDownstream(4); }} className="w-full bg-surface-container border border-white/5 rounded-lg px-3 py-2 text-sm focus:ring-1 focus:ring-primary/50 text-on-surface" placeholder="Technology, Biotech" />
            </div>
            <div className="col-span-2">
              <label className="block text-xs text-[#8e8e88] mb-1">Min Daily Volume (USD)</label>
              <input type="number" value={s4Volume} onChange={(e) => { setS4Volume(Number(e.target.value)); unlockSectionAndDownstream(4); }} className="w-full bg-surface-container border border-white/5 rounded-lg px-3 py-2 text-sm focus:ring-1 focus:ring-primary/50 text-on-surface" placeholder="1000000" />
            </div>
          </div>
        </SectionValidator>

        <SectionValidator
          title="Strategy Intent"
          sectionNumber={5}
          detailPrompt="How do you think about entering and exiting trades? Describe the setups you're looking for."
          detailText={s5Detail}
          setDetailText={(t) => { setS5Detail(t); unlockSectionAndDownstream(5); }}
          isLocked={!!lockedSections[5]}
          onUnlock={() => unlockSectionAndDownstream(5)}
          validating={validatingSection === 5}
          validationResponse={sectionResponses[5]}
          onValidate={() => handleValidateSection(5, { catalysts: s5Catalysts, options: s5Options, short: s5Short }, s5Detail)}
        >
          <div className="grid grid-cols-2 gap-4">
            <div className="col-span-2">
              <label className="block text-xs text-[#8e8e88] mb-1">Catalysts (comma separated)</label>
              <input type="text" value={s5Catalysts.join(', ')} onChange={(e) => { setS5Catalysts(e.target.value.split(',').map(s=>s.trim())); unlockSectionAndDownstream(5); }} className="w-full bg-surface-container border border-white/5 rounded-lg px-3 py-2 text-sm focus:ring-1 focus:ring-primary/50 text-on-surface" placeholder="Earnings, FDA Approvals" />
            </div>
            <div className="flex items-center gap-2">
              <input type="checkbox" checked={s5Options} onChange={(e) => { setS5Options(e.target.checked); unlockSectionAndDownstream(5); }} className="w-4 h-4" />
              <label className="text-sm text-on-surface">Permit Options</label>
            </div>
            <div className="flex items-center gap-2">
              <input type="checkbox" checked={s5Short} onChange={(e) => { setS5Short(e.target.checked); unlockSectionAndDownstream(5); }} className="w-4 h-4" />
              <label className="text-sm text-on-surface">Permit Short Selling</label>
            </div>
          </div>
        </SectionValidator>

        <SectionValidator
          title="Execution"
          sectionNumber={6}
          detailPrompt="When can you realistically act on a trade signal? Describe your available windows and execution constraints."
          detailText={s6Detail}
          setDetailText={(t) => { setS6Detail(t); unlockSectionAndDownstream(6); }}
          isLocked={!!lockedSections[6]}
          onUnlock={() => unlockSectionAndDownstream(6)}
          validating={validatingSection === 6}
          validationResponse={sectionResponses[6]}
          onValidate={() => handleValidateSection(6, { brokerage: s6Brokerage, prepost: s6PrePost, order: s6Order }, s6Detail)}
        >
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs text-[#8e8e88] mb-1">Brokerage</label>
              <input type="text" value={s6Brokerage} onChange={(e) => { setS6Brokerage(e.target.value); unlockSectionAndDownstream(6); }} className="w-full bg-surface-container border border-white/5 rounded-lg px-3 py-2 text-sm focus:ring-1 focus:ring-primary/50 text-on-surface" placeholder="Interactive Brokers" />
            </div>
            <div>
              <label className="block text-xs text-[#8e8e88] mb-1">Order Type Preference</label>
              <select value={s6Order} onChange={(e) => { setS6Order(e.target.value); unlockSectionAndDownstream(6); }} className="w-full bg-surface-container border border-white/5 rounded-lg px-3 py-2 text-sm focus:ring-1 focus:ring-primary/50 text-on-surface">
                <option value="limit">Limit Orders Only</option>
                <option value="market">Market Orders OK</option>
              </select>
            </div>
            <div className="col-span-2 flex items-center gap-2">
              <input type="checkbox" checked={s6PrePost} onChange={(e) => { setS6PrePost(e.target.checked); unlockSectionAndDownstream(6); }} className="w-4 h-4" />
              <label className="text-sm text-on-surface">Can trade pre-market / after-hours</label>
            </div>
          </div>
        </SectionValidator>

        <SectionValidator
          title="Priorities"
          sectionNumber={7}
          detailPrompt="In your own words, when the system has to sacrifice one thing to get another, what should guide that decision?"
          detailText={s7Detail}
          setDetailText={(t) => { setS7Detail(t); unlockSectionAndDownstream(7); }}
          isLocked={!!lockedSections[7]}
          onUnlock={() => unlockSectionAndDownstream(7)}
          validating={validatingSection === 7}
          validationResponse={sectionResponses[7]}
          onValidate={() => handleValidateSection(7, { priorities: s7Priorities.map(p=>p.id) }, s7Detail)}
        >
          <div>
            <label className="block text-xs text-[#8e8e88] mb-2">Drag to Rank Dimensions (Highest Priority Top)</label>
            <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
              <SortableContext items={s7Priorities.map(p => p.id)} strategy={verticalListSortingStrategy}>
                <div className="space-y-1">
                  {s7Priorities.map(p => (
                    <SortablePriorityItem key={p.id} id={p.id} label={p.label} />
                  ))}
                </div>
              </SortableContext>
            </DndContext>
          </div>
        </SectionValidator>

        <div className="flex justify-end pt-4 border-t border-white/10">
          <button
            onClick={handleReview}
            disabled={!allSectionsLocked || reviewing}
            className="px-8 py-3 bg-primary-container text-on-primary-container text-[0.8125rem] font-semibold rounded-lg hover:brightness-110 disabled:opacity-50 transition-all flex items-center gap-2"
          >
            {reviewing ? 'Synthesizing...' : 'Review Full Mandate'}
            {!reviewing && <span className="material-symbols-outlined text-[18px]">arrow_forward</span>}
          </button>
        </div>
        {error && <div className="text-destructive text-sm text-right mt-2">{error}</div>}

      </div>
    );
  }

  // ─── Step: Review ────────────────────────────────────────
  if (step === 'review' && reviewResult) {
    const canConfirm = reviewResult.is_valid;

    return (
      <div className="max-w-3xl mx-auto space-y-8 pb-32">
        <div>
          <h1 className="font-headline text-4xl font-light tracking-tight text-on-surface">
            Confirm Your Mandate
          </h1>
          <p className="text-[#8e8e88] mt-2 leading-relaxed">
            Review the final synthesis. Once locked, Aegis begins autonomous execution.
          </p>
        </div>

        {/* Hard Errors */}
        {reviewResult.hard_errors.length > 0 && (
          <section className="bg-destructive/10 border border-destructive/30 rounded-xl p-6 space-y-3">
            <div className="flex items-center gap-2">
              <span className="material-symbols-outlined text-destructive text-[20px]">error</span>
              <h3 className="text-[0.6875rem] font-bold uppercase tracking-widest text-destructive">
                Critical Errors (Blocks Confirmation)
              </h3>
            </div>
            <ul className="list-disc pl-5 space-y-1">
              {reviewResult.hard_errors.map((e: string, i: number) => (
                <li key={i} className="text-sm text-destructive/90">{e}</li>
              ))}
            </ul>
          </section>
        )}

        {/* Cross-Section Contradictions */}
        {reviewResult.cross_section_contradictions.length > 0 && (
          <section className="bg-amber-500/10 border border-amber-500/30 rounded-xl p-6 space-y-3">
            <div className="flex items-center gap-2">
              <span className="material-symbols-outlined text-amber-500 text-[20px]">warning</span>
              <h3 className="text-[0.6875rem] font-bold uppercase tracking-widest text-amber-500">
                Cross-Section Conflicts
              </h3>
            </div>
            <ul className="list-disc pl-5 space-y-1">
              {reviewResult.cross_section_contradictions.map((c: string, i: number) => (
                <li key={i} className="text-sm text-amber-500/90">{c}</li>
              ))}
            </ul>
          </section>
        )}

        <div className="pt-4 border-t border-white/5 flex justify-between items-center">
          <button
            onClick={() => setStep('input')}
            className="flex items-center gap-2 px-4 py-2.5 text-[#8e8e88] hover:text-on-surface text-[0.8125rem] transition-colors"
          >
            <span className="material-symbols-outlined text-[18px]">arrow_back</span>
            Edit Mandate
          </button>
          <button
            onClick={handleConfirm}
            disabled={confirming || !canConfirm}
            className="px-8 py-3 bg-primary-container text-on-primary-container text-[0.8125rem] font-semibold rounded-lg hover:brightness-110 transition-all disabled:opacity-50 flex items-center gap-2"
          >
            {confirming ? 'Locking...' : 'Lock Mandate'}
          </button>
        </div>
      </div>
    );
  }

  // ─── Step: Launched ──────────────────────────────────────
  return (
    <div className="max-w-3xl mx-auto space-y-8">
      <div className="bg-surface-container-low border border-secondary/20 rounded-xl p-10 text-center space-y-6">
        <div className="w-16 h-16 rounded-full bg-secondary/20 mx-auto flex items-center justify-center">
          <span className="material-symbols-outlined text-secondary text-[32px]" style={{ fontVariationSettings: "'FILL' 1" }}>
            rocket_launch
          </span>
        </div>
        <div>
          <h2 className="font-headline text-3xl font-light tracking-tight text-on-surface">
            Sentinel Launched
          </h2>
          <p className="text-[#8e8e88] mt-2">
            Your mandate is locked. The pipeline is now generating and evaluating strategies.
          </p>
        </div>
        {confirmResult && (
          <div className="bg-surface-container rounded-lg border border-white/5 px-4 py-3 inline-flex items-center gap-3 mx-auto">
            <span className="text-[0.6875rem] text-[#8e8e88] uppercase tracking-widest">Workflow</span>
            <code className="text-sm font-mono text-on-surface">{confirmResult.workflow_id}</code>
          </div>
        )}
        <div className="flex justify-center gap-3 pt-4">
          <button
            onClick={() => navigate('/pipeline')}
            className="px-6 py-3 bg-primary-container text-on-primary-container text-[0.8125rem] font-semibold rounded-lg hover:brightness-110 transition-all flex items-center gap-2"
          >
            <span className="material-symbols-outlined text-[18px]">hub</span>
            Watch Pipeline
          </button>
          <button
            onClick={() => navigate('/')}
            className="px-6 py-3 border border-white/10 text-on-surface-variant hover:text-on-surface text-[0.8125rem] font-medium rounded-lg hover:bg-white/5 transition-all"
          >
            Mission Control
          </button>
        </div>
      </div>
    </div>
  );
}
