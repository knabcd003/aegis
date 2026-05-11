import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

/**
 * Utility to merge tailwind classes
 */
function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

interface NumberInputProps {
  label: string;
  value: number | null;
  onChange: (value: number | null) => void;
  prefix?: string;
  suffix?: string;
  placeholder?: string;
  subtext?: string;
  step?: number;
  min?: number;
  max?: number;
  disabled?: boolean;
}

export function NumberInput({
  label,
  value,
  onChange,
  prefix,
  suffix,
  placeholder = "0.00",
  subtext,
  step = 1,
  min,
  max,
  disabled = false,
}: NumberInputProps) {
  
  const handleInputChange = (val: string) => {
    // Remove formatting characters for parsing
    const cleanVal = val.replace(/[^0-9.-]/g, '');
    const num = parseFloat(cleanVal);
    
    if (val === '') {
      onChange(null);
      return;
    }

    if (!isNaN(num)) {
      // Respect min/max if provided
      let finalNum = num;
      if (min !== undefined) finalNum = Math.max(min, finalNum);
      if (max !== undefined) finalNum = Math.min(max, finalNum);
      onChange(finalNum);
    }
  };

  const displayValue = value !== null ? value.toLocaleString() : '';

  return (
    <div className={cn("space-y-3 w-full", disabled && "opacity-40 pointer-events-none")}>
      <label className="text-[0.6875rem] font-bold uppercase tracking-[0.15em] text-[#8e8e88]">
        {label}
      </label>
      
      <div className="relative group">
        {prefix && (
          <span className="absolute left-4 top-1/2 -translate-y-1/2 text-[#8e8e88] font-mono select-none">
            {prefix}
          </span>
        )}
        <input
          type="text"
          value={displayValue}
          onChange={(e) => handleInputChange(e.target.value)}
          placeholder={placeholder}
          disabled={disabled}
          className={cn(
            "w-full bg-surface-container/50 border border-white/5 rounded-xl py-3 text-lg font-mono text-on-surface outline-none focus:border-secondary/30 focus:ring-1 focus:ring-secondary/20 transition-all",
            prefix ? "pl-8" : "pl-4",
            suffix ? "pr-10" : "pr-4"
          )}
        />
        {suffix && (
          <span className="absolute right-4 top-1/2 -translate-y-1/2 text-[#8e8e88] font-mono select-none">
            {suffix}
          </span>
        )}
      </div>

      {subtext && (
        <p className="text-[0.625rem] text-[#8e8e88]/50 italic leading-relaxed">
          {subtext}
        </p>
      )}
    </div>
  );
}
