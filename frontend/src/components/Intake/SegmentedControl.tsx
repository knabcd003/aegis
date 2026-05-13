import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

/**
 * Utility to merge tailwind classes
 */
function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

interface SegmentedOption {
  value: string;
  label: string;
  description?: string;
}

interface SegmentedControlProps {
  options: SegmentedOption[];
  value: string | null;
  onChange: (value: string) => void;
  disabled?: boolean;
}

export function SegmentedControl({
  options,
  value,
  onChange,
  disabled = false,
}: SegmentedControlProps) {
  return (
    <div 
      className={cn(
        "inline-flex p-1 rounded-xl bg-surface-container-low/50 border border-white/5 backdrop-blur-sm",
        disabled && "opacity-50 pointer-events-none grayscale"
      )}
    >
      <div className="flex items-stretch gap-1 w-full flex-wrap">
        {options.map((option) => {
          const isSelected = value === option.value;
          
          return (
            <button
              key={option.value}
              type="button"
              disabled={disabled}
              onClick={() => onChange(option.value)}
              className={cn(
                "flex-1 min-w-[80px] px-3 py-2.5 rounded-lg transition-all duration-300 flex flex-col items-center justify-center gap-0.5 relative group",
                isSelected 
                  ? "bg-secondary-fixed-dim text-on-secondary-fixed shadow-lg shadow-secondary/10 z-10" 
                  : "text-[#8e8e88] hover:text-on-surface hover:bg-white/5"
              )}
            >
              {/* Label */}
              <span className={cn(
                "text-[0.8125rem] font-semibold tracking-wide transition-colors",
                isSelected ? "text-on-secondary-fixed" : "text-[#8e8e88] group-hover:text-on-surface"
              )}>
                {option.label}
              </span>
              
              {/* Optional Description */}
              {option.description && (
                <span className={cn(
                  "text-[0.625rem] leading-tight transition-colors text-center max-w-[140px]",
                  isSelected ? "text-on-secondary-fixed/70" : "text-[#8e8e88]/60 group-hover:text-on-surface/50"
                )}>
                  {option.description}
                </span>
              )}

              {/* Active Indicator Bar (bottom) */}
              {isSelected && (
                <div className="absolute bottom-1 left-1/2 -translate-x-1/2 w-4 h-[2px] bg-on-secondary-fixed/30 rounded-full" />
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
}
