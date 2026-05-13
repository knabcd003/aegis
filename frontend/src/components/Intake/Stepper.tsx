import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

/**
 * Utility to merge tailwind classes
 */
function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

interface StepperProps {
  label: string;
  value: number | null;
  min: number;
  max: number;
  step?: number;
  onChange: (value: number) => void;
  suffix?: string;
  helper?: string;
  disabled?: boolean;
}

export function Stepper({
  label,
  value,
  min,
  max,
  step = 1,
  onChange,
  suffix = '',
  helper,
  disabled = false,
}: StepperProps) {
  const displayValue = value ?? min;

  const increment = () => {
    if (displayValue + step <= max) onChange(displayValue + step);
  };

  const decrement = () => {
    if (displayValue - step >= min) onChange(displayValue - step);
  };

  return (
    <div className={cn("space-y-3 w-full", disabled && "opacity-40 pointer-events-none")}>
      <label className="text-[0.6875rem] font-bold uppercase tracking-[0.15em] text-[#8e8e88]">
        {label}
      </label>
      
      <div className="flex items-center gap-4">
        <div className="flex-1 flex items-center bg-surface-container/50 border border-white/5 rounded-xl px-2 py-2 overflow-hidden group">
          <button
            type="button"
            onClick={decrement}
            disabled={displayValue <= min}
            className="w-10 h-10 rounded-lg flex items-center justify-center text-on-surface hover:bg-white/5 disabled:opacity-20 transition-all"
          >
            <span className="material-symbols-outlined text-[20px]">remove</span>
          </button>
          
          <div className="flex-1 text-center font-mono text-lg font-bold text-on-surface">
            {displayValue}{suffix}
          </div>

          <button
            type="button"
            onClick={increment}
            disabled={displayValue >= max}
            className="w-10 h-10 rounded-lg flex items-center justify-center text-on-surface hover:bg-white/5 disabled:opacity-20 transition-all"
          >
            <span className="material-symbols-outlined text-[20px]">add</span>
          </button>
        </div>
      </div>

      {helper && (
        <p className="text-[0.6875rem] text-[#8e8e88]/60 leading-relaxed italic">
          {helper}
        </p>
      )}
    </div>
  );
}
