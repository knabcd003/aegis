import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

/**
 * Utility to merge tailwind classes
 */
function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

interface RadioOption {
  value: string;
  label: string;
  description: string;
}

interface RadioGroupProps {
  options: RadioOption[];
  value: string | null;
  onChange: (value: string) => void;
  disabled?: boolean;
}

export function RadioGroup({
  options,
  value,
  onChange,
  disabled = false,
}: RadioGroupProps) {
  return (
    <div className={cn(
      "flex flex-col gap-2 w-full",
      disabled && "opacity-40 pointer-events-none"
    )}>
      {options.map((option) => {
        const isSelected = value === option.value;
        
        return (
          <button
            key={option.value}
            type="button"
            disabled={disabled}
            onClick={() => onChange(option.value)}
            className={cn(
              "relative flex flex-col items-start text-left px-4 py-3 rounded-xl border transition-all duration-150 group overflow-hidden",
              isSelected 
                ? "bg-secondary/10 border-secondary/30 ring-1 ring-secondary/20" 
                : "bg-surface-container-low/50 border-white/5 hover:bg-white/10 hover:border-white/10"
            )}
          >
            {/* Left Edge Accent Bar */}
            <div className={cn(
              "absolute left-0 top-0 bottom-0 w-1 transition-all duration-300",
              isSelected ? "bg-secondary scale-y-100" : "bg-secondary/0 scale-y-0"
            )} />

            {/* Label */}
            <span className={cn(
              "text-[0.875rem] font-medium transition-colors",
              isSelected ? "text-on-surface" : "text-[#8e8e88] group-hover:text-on-surface"
            )}>
              {option.label}
            </span>

            {/* Description */}
            <p className={cn(
              "text-[0.75rem] mt-0.5 leading-relaxed transition-colors",
              isSelected ? "text-[#8e8e88]" : "text-[#8e8e88]/50 group-hover:text-[#8e8e88]"
            )}>
              {option.description}
            </p>
          </button>
        );
      })}
    </div>
  );
}
