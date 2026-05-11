import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

/**
 * Utility to merge tailwind classes
 */
function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

interface SliderProps {
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

export function Slider({
  label,
  value,
  min,
  max,
  step = 1,
  onChange,
  suffix = '',
  helper,
  disabled = false,
}: SliderProps) {
  const displayValue = value ?? min;
  const percentage = ((displayValue - min) / (max - min)) * 100;

  return (
    <div className={cn("space-y-3 w-full", disabled && "opacity-40 pointer-events-none")}>
      <div className="flex items-center justify-between">
        <label className="text-[0.6875rem] font-bold uppercase tracking-[0.15em] text-[#8e8e88]">
          {label}
        </label>
        <span className="text-[0.9375rem] font-mono text-secondary font-bold">
          {displayValue}{suffix}
        </span>
      </div>

      <div className="relative h-6 flex items-center group">
        {/* Track Background */}
        <div className="absolute w-full h-1.5 bg-surface-container rounded-full border border-white/5" />
        
        {/* Active Fill */}
        <div 
          className="absolute h-1.5 bg-secondary/30 rounded-full" 
          style={{ width: `${percentage}%` }}
        />

        {/* Range Input */}
        <input
          type="range"
          min={min}
          max={max}
          step={step}
          value={displayValue}
          onChange={(e) => onChange(Number(e.target.value))}
          disabled={disabled}
          className="absolute w-full h-6 appearance-none bg-transparent cursor-pointer z-10 
            [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-4 [&::-webkit-slider-thumb]:h-4 
            [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-secondary 
            [&::-webkit-slider-thumb]:border-2 [&::-webkit-slider-thumb]:border-surface-container 
            [&::-webkit-slider-thumb]:shadow-lg [&::-webkit-slider-thumb]:shadow-secondary/20 
            [&::-webkit-slider-thumb]:transition-transform [&::-webkit-slider-thumb]:duration-150
            [&::-webkit-slider-thumb]:hover:scale-125 [&::-moz-range-thumb]:w-4 [&::-moz-range-thumb]:h-4 
            [&::-moz-range-thumb]:rounded-full [&::-moz-range-thumb]:bg-secondary"
        />
      </div>

      {helper && (
        <p className="text-[0.6875rem] text-[#8e8e88]/60 leading-relaxed italic">
          {helper}
        </p>
      )}
    </div>
  );
}
