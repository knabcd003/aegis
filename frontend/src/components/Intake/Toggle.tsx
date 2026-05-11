import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

/**
 * Utility to merge tailwind classes
 */
function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

interface ToggleProps {
  label: string;
  value: boolean;
  onChange: (value: boolean) => void;
  helper?: string;
  disabled?: boolean;
}

export function Toggle({
  label,
  value,
  onChange,
  helper,
  disabled = false,
}: ToggleProps) {
  return (
    <div className={cn("flex items-start justify-between gap-4 py-2", disabled && "opacity-40 pointer-events-none")}>
      <div className="space-y-1">
        <label className="text-[0.6875rem] font-bold uppercase tracking-[0.15em] text-[#8e8e88]">
          {label}
        </label>
        {helper && (
          <p className="text-xs text-[#8e8e88]/60 leading-relaxed max-w-md">
            {helper}
          </p>
        )}
      </div>
      
      <button
        type="button"
        onClick={() => onChange(!value)}
        className={cn(
          "relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out outline-none",
          value ? "bg-secondary" : "bg-white/10"
        )}
      >
        <span
          className={cn(
            "pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out",
            value ? "translate-x-5" : "translate-x-0"
          )}
        />
      </button>
    </div>
  );
}
