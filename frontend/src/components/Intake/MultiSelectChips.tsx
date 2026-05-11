import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';
import { Check } from 'lucide-react';

/**
 * Utility to merge tailwind classes
 */
function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

interface MultiSelectOption {
  value: string;
  label: string;
}

interface MultiSelectChipsProps {
  options: MultiSelectOption[];
  value: string[];
  onChange: (value: string[]) => void;
  disabled?: boolean;
  maxSelections?: number;
}

export function MultiSelectChips({
  options,
  value = [],
  onChange,
  disabled = false,
  maxSelections,
}: MultiSelectChipsProps) {
  
  const handleToggle = (optionValue: string) => {
    if (value.includes(optionValue)) {
      onChange(value.filter(v => v !== optionValue));
    } else {
      if (maxSelections && value.length >= maxSelections) return;
      onChange([...value, optionValue]);
    }
  };

  const isMaxReached = maxSelections !== undefined && value.length >= maxSelections;

  return (
    <div className={cn(
      "flex flex-wrap gap-2 w-full",
      disabled && "opacity-40 pointer-events-none"
    )}>
      {options.map((option) => {
        const isSelected = value.includes(option.value);
        const canSelect = !isMaxReached || isSelected;

        return (
          <button
            key={option.value}
            type="button"
            disabled={disabled || (!canSelect && !disabled)}
            onClick={() => handleToggle(option.value)}
            className={cn(
              "flex items-center gap-1 px-3 py-1.5 rounded-full text-[0.75rem] font-medium border transition-all duration-150",
              isSelected 
                ? "bg-secondary/15 border-secondary/40 text-secondary" 
                : "bg-surface-container-low/50 border-white/5 text-[#8e8e88] hover:bg-white/10 hover:border-white/10 hover:text-on-surface",
              !canSelect && !isSelected && "opacity-50 pointer-events-none cursor-not-allowed"
            )}
          >
            {isSelected && (
              <Check size={12} className="shrink-0" />
            )}
            <span>{option.label}</span>
          </button>
        );
      })}
    </div>
  );
}
