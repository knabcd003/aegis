import { useEffect } from 'react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';
import { X, Plus, Check } from 'lucide-react';
import type { HorizonBucket } from '../../types/intake';
import { Stepper } from './Stepper';
import { Slider } from './Slider';

/**
 * Utility to merge tailwind classes
 */
function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

interface HorizonAllocationBuilderProps {
  value: HorizonBucket[];
  onChange: (value: HorizonBucket[]) => void;
  onValidityChange?: (valid: boolean) => void;
  disabled?: boolean;
}

const PRESETS = {
  pead: [
    { label: "Short Swing", min: 5, max: 21, weight: 0.65 },
    { label: "Intermediate", min: 21, max: 63, weight: 0.35 }
  ],
  biotech: [
    { label: "Event Window", min: 3, max: 14, weight: 0.50 },
    { label: "Extended Drift", min: 14, max: 45, weight: 0.50 }
  ]
};

export function HorizonAllocationBuilder({
  value = [],
  onChange,
  onValidityChange,
  disabled = false,
}: HorizonAllocationBuilderProps) {
  
  // Total weight calculation
  const totalWeight = value.reduce((sum, b) => sum + (b.capital_weight || 0), 0);
  const roundedTotal = Math.round(totalWeight * 100);
  const isValid = roundedTotal === 100;

  useEffect(() => {
    onValidityChange?.(isValid);
  }, [roundedTotal, isValid]);

  // Ensure at least one bucket if empty
  useEffect(() => {
    if (value.length === 0) {
      addBucket();
    }
  }, []);

  const addBucket = () => {
    if (value.length >= 5) return;
    const newBucket: HorizonBucket = {
      id: crypto.randomUUID(),
      label: "",
      min_days: 1,
      max_days: 30,
      capital_weight: 0
    };
    onChange([...value, newBucket]);
  };

  const removeBucket = (id: string) => {
    if (value.length <= 1) return;
    onChange(value.filter(b => b.id !== id));
  };

  const updateBucket = (id: string, updates: Partial<HorizonBucket>) => {
    const newValue = value.map(b => {
      if (b.id === id) {
        const merged = { ...b, ...updates };
        // Max days auto-correction
        if (merged.max_days <= merged.min_days) {
          merged.max_days = merged.min_days + 1;
        }
        return merged;
      }
      return b;
    });
    onChange(newValue);
  };

  const applyPreset = (type: 'pead' | 'biotech' | 'custom') => {
    if (type === 'custom') {
      onChange([{
        id: crypto.randomUUID(),
        label: "",
        min_days: 1,
        max_days: 30,
        capital_weight: 0
      }]);
      return;
    }
    const preset = PRESETS[type].map(p => ({
      id: crypto.randomUUID(),
      label: p.label,
      min_days: p.min,
      max_days: p.max,
      capital_weight: p.weight
    }));
    onChange(preset);
  };

  const showPresets = value.length === 0 || value.every(b => !b.label);

  return (
    <div className={cn("space-y-6 w-full", disabled && "opacity-40 pointer-events-none")}>
      {/* PRESETS */}
      {showPresets && (
        <div className="flex items-center gap-3 animate-in fade-in slide-in-from-top-2 duration-500">
          <span className="text-[0.625rem] font-bold uppercase tracking-widest text-[#8e8e88]/50">Presets:</span>
          <button 
            onClick={() => applyPreset('pead')}
            className="px-3 py-1 bg-secondary/10 border border-secondary/20 text-secondary text-[0.6875rem] font-bold rounded-full hover:bg-secondary/20 transition-all"
          >
            PEAD Standard
          </button>
          <button 
            onClick={() => applyPreset('biotech')}
            className="px-3 py-1 bg-secondary/10 border border-secondary/20 text-secondary text-[0.6875rem] font-bold rounded-full hover:bg-secondary/20 transition-all"
          >
            Biotech Focus
          </button>
          <button 
            onClick={() => applyPreset('custom')}
            className="px-3 py-1 bg-white/5 border border-white/10 text-on-surface/60 text-[0.6875rem] font-bold rounded-full hover:bg-white/10 transition-all"
          >
            Custom
          </button>
        </div>
      )}

      {/* BUCKET LIST */}
      <div className="space-y-2">
        {value.map((bucket) => (
          <div 
            key={bucket.id}
            className="flex items-center gap-4 p-4 bg-surface-container/30 border border-white/5 rounded-xl group transition-all hover:border-white/10"
          >
            {/* Label */}
            <div className="space-y-1.5">
              <label className="text-[0.625rem] font-bold uppercase tracking-widest text-[#8e8e88]">Name</label>
              <input
                type="text"
                value={bucket.label}
                onChange={(e) => updateBucket(bucket.id, { label: e.target.value })}
                placeholder="e.g. Short Swing"
                className="w-[160px] bg-white/5 border border-white/5 rounded-lg px-3 py-2 text-sm text-on-surface outline-none focus:border-secondary/30 transition-all"
              />
            </div>

            {/* Min Days */}
            <div className="space-y-1.5">
              <label className="text-[0.625rem] font-bold uppercase tracking-widest text-[#8e8e88]">Min Days</label>
              <Stepper
                label="Min Days"
                value={bucket.min_days}
                onChange={(val) => updateBucket(bucket.id, { min_days: val })}
                min={1}
                max={364}
              />
            </div>

            {/* Max Days */}
            <div className="space-y-1.5">
              <label className="text-[0.625rem] font-bold uppercase tracking-widest text-[#8e8e88]">Max Days</label>
              <Stepper
                label="Max Days"
                value={bucket.max_days}
                onChange={(val) => updateBucket(bucket.id, { max_days: val })}
                min={bucket.min_days + 1}
                max={365}
              />
            </div>

            {/* Capital Weight */}
            <div className="flex-1 space-y-1.5 min-w-[200px]">
              <div className="flex justify-between">
                <label className="text-[0.625rem] font-bold uppercase tracking-widest text-[#8e8e88]">Allocation</label>
                <span className="text-[0.625rem] font-mono font-bold text-secondary">
                  {Math.round(bucket.capital_weight * 100)}%
                </span>
              </div>
              <Slider
                label="Allocation Weight"
                value={bucket.capital_weight}
                onChange={(val) => updateBucket(bucket.id, { capital_weight: val })}
                min={0}
                max={1.0}
                step={0.01}
              />
            </div>

            {/* Remove */}
            <button
              onClick={() => removeBucket(bucket.id)}
              disabled={value.length <= 1}
              className={cn(
                "p-2 rounded-lg transition-all",
                value.length <= 1 
                  ? "opacity-0 pointer-events-none" 
                  : "text-[#8e8e88]/40 hover:text-terracotta hover:bg-terracotta/10"
              )}
            >
              <X size={18} />
            </button>
          </div>
        ))}
      </div>

      {/* SUMMARY BAR */}
      <div className="flex flex-col gap-4">
        <div className={cn(
          "flex items-center justify-between px-6 py-4 rounded-xl border transition-all",
          roundedTotal === 100 ? "bg-secondary/5 border-secondary/20" : 
          roundedTotal > 100 ? "bg-terracotta/5 border-terracotta/20" : "bg-amber-500/5 border-amber-500/20"
        )}>
          <div className="flex items-center gap-3">
            {roundedTotal === 100 ? (
              <Check size={18} className="text-secondary" />
            ) : (
              <div className={cn("w-2 h-2 rounded-full animate-pulse", roundedTotal > 100 ? "bg-terracotta" : "bg-amber-500")} />
            )}
            <span className={cn(
              "text-[0.8125rem] font-bold tracking-wide",
              roundedTotal === 100 ? "text-secondary" : 
              roundedTotal > 100 ? "text-terracotta" : "text-amber-500"
            )}>
              Total Allocation: {roundedTotal}%
              {roundedTotal < 100 && ` — ${100 - roundedTotal}% unallocated`}
              {roundedTotal > 100 && ` — exceeds 100%`}
              {roundedTotal === 100 && ` ✓`}
            </span>
          </div>
        </div>

        {/* ADD BUTTON */}
        <button
          onClick={addBucket}
          disabled={value.length >= 5}
          className={cn(
            "w-full h-14 flex items-center justify-center gap-2 border-2 border-dashed rounded-xl transition-all",
            value.length >= 5 
              ? "opacity-40 border-white/5 cursor-not-allowed" 
              : "border-white/5 bg-white/5 text-[#8e8e88] hover:bg-white/10 hover:border-white/10 active:scale-[0.99]"
          )}
        >
          <Plus size={18} />
          <span className="text-[0.6875rem] font-bold uppercase tracking-widest">Add Holding Period</span>
        </button>
      </div>
    </div>
  );
}
