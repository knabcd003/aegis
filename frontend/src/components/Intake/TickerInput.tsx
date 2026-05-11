import { useState, KeyboardEvent } from 'react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';
import { X } from 'lucide-react';

/**
 * Utility to merge tailwind classes
 */
function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

interface TickerInputProps {
  label: string;
  value: string[];
  onChange: (value: string[]) => void;
  placeholder?: string;
  disabled?: boolean;
}

export function TickerInput({
  label,
  value = [],
  onChange,
  placeholder = "Type ticker and press Enter...",
  disabled = false,
}: TickerInputProps) {
  const [inputValue, setInputValue] = useState('');

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' || e.key === ',') {
      e.preventDefault();
      const ticker = inputValue.trim().toUpperCase();
      if (ticker && !value.includes(ticker)) {
        onChange([...value, ticker]);
        setInputValue('');
      }
    } else if (e.key === 'Backspace' && !inputValue && value.length > 0) {
      onChange(value.slice(0, -1));
    }
  };

  const removeTicker = (tickerToRemove: string) => {
    onChange(value.filter(t => t !== tickerToRemove));
  };

  return (
    <div className={cn("space-y-3 w-full", disabled && "opacity-40 pointer-events-none")}>
      <label className="text-[0.6875rem] font-bold uppercase tracking-[0.15em] text-[#8e8e88]">
        {label}
      </label>
      
      <div className={cn(
        "flex flex-wrap gap-2 p-2 bg-surface-container/50 border border-white/5 rounded-xl min-h-[52px] focus-within:border-secondary/30 transition-all",
        disabled && "cursor-not-allowed"
      )}>
        {value.map((ticker) => (
          <span 
            key={ticker}
            className="flex items-center gap-1.5 px-2.5 py-1 bg-secondary/10 border border-secondary/20 text-secondary rounded-lg text-xs font-mono font-bold animate-in zoom-in-95 duration-150"
          >
            {ticker}
            <button
              type="button"
              onClick={() => removeTicker(ticker)}
              className="hover:bg-secondary/20 rounded-sm transition-colors"
            >
              <X size={12} />
            </button>
          </span>
        ))}
        
        <input
          type="text"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={value.length === 0 ? placeholder : ""}
          disabled={disabled}
          className="flex-1 bg-transparent border-none outline-none text-sm font-mono text-on-surface min-w-[120px] py-1 px-2"
        />
      </div>
    </div>
  );
}
