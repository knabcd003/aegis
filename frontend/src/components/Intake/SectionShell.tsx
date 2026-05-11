import type { ReactNode } from 'react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

/**
 * Utility to merge tailwind classes
 */
function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

interface SectionShellProps {
  sectionNumber: number;
  title: string;
  description: string;
  locked: boolean;
  validated: boolean;
  children: ReactNode;
  onLock: () => void;
  onUnlock: () => void;
  lockDisabled?: boolean;
}

export function SectionShell({
  sectionNumber,
  title,
  description,
  locked,
  validated,
  children,
  onLock,
  onUnlock,
  lockDisabled = false,
}: SectionShellProps) {
  return (
    <div 
      className={cn(
        "relative rounded-2xl transition-all duration-500 overflow-hidden",
        "bg-surface-container/40 border border-white/5 shadow-2xl",
        locked ? "border-white/10" : "border-primary/10"
      )}
    >
      {/* SECTION HEADER */}
      <div className="p-8 pb-4">
        <div className="flex items-start justify-between">
          <div className="space-y-3">
            {/* Badge - Using Sage (#ACCEC5) for better visibility */}
            <div className="inline-flex items-center justify-center px-2.5 py-1 rounded-md bg-secondary/10 border border-secondary/20">
              <span className="text-[0.625rem] font-bold uppercase tracking-[0.2em] text-secondary">
                Section {sectionNumber.toString().padStart(2, '0')}
              </span>
            </div>

            {/* Title & Description */}
            <div>
              <h2 className="font-headline text-3xl font-light text-on-surface tracking-tight serif-text">
                {title}
              </h2>
              <p className="text-sm text-[#8e8e88] mt-2 max-w-2xl leading-relaxed">
                {description}
              </p>
            </div>
          </div>

          {/* LOCK STATUS INDICATOR - Using Terracotta (#FFB59E) */}
          {locked && (
            <div className="flex items-center gap-2 px-3 py-1.5 bg-primary-fixed-dim/10 border border-primary-fixed-dim/20 rounded-full">
              <span className="material-symbols-outlined text-[16px] text-primary-fixed-dim">lock</span>
              <span className="text-[0.6875rem] font-bold uppercase tracking-[0.1em] text-primary-fixed-dim">Mandate Locked</span>
            </div>
          )}
        </div>
      </div>

      {/* CONTENT AREA */}
      <div className="relative p-8 pt-4">
        {/* Children content */}
        <div className={cn(
          "transition-all duration-500",
          locked && "opacity-30 pointer-events-none blur-[1px] grayscale"
        )}>
          {children}
        </div>

        {/* LOCKED OVERLAY */}
        {locked && (
          <div className="absolute inset-0 z-10 flex flex-col items-center justify-center bg-surface/10 backdrop-blur-[2px]">
            {/* Visual spacer to prevent buttons from overlapping with blurred content too awkwardly */}
            <div className="h-12" />
          </div>
        )}
      </div>

      {/* ACTION FOOTER */}
      <div className="px-8 py-6 bg-surface/30 border-t border-white/5 flex items-center justify-between">
        <div className="flex items-center gap-2">
          {locked ? (
            <div className="flex items-center gap-2 text-[#8e8e88]">
              <span className="material-symbols-outlined text-[18px]">verified</span>
              <span className="text-[0.75rem] font-medium tracking-wide">Section validated and synced to backend.</span>
            </div>
          ) : (
            <div className="flex items-center gap-2 text-[#8e8e88]">
              <span className="material-symbols-outlined text-[18px]">
                {validated ? 'check_circle' : 'pending'}
              </span>
              <span className="text-[0.75rem] font-medium tracking-wide">
                {validated ? 'Ready to lock mandate.' : 'Awaiting section validation...'}
              </span>
            </div>
          )}
        </div>

        <div className="flex items-center gap-4">
          {locked ? (
            <button
              onClick={onUnlock}
              className="flex items-center gap-2 px-5 py-2.5 rounded-lg border border-white/10 text-on-surface text-[0.8125rem] font-semibold hover:bg-white/5 transition-all active:scale-95"
            >
              <span className="material-symbols-outlined text-[18px]">lock_open</span>
              Unlock to Edit
            </button>
          ) : validated ? (
            <button
              onClick={onLock}
              disabled={lockDisabled}
              className={cn(
                "flex items-center gap-2 px-6 py-2.5 rounded-lg text-[0.8125rem] font-semibold transition-all active:scale-95",
                lockDisabled 
                  ? "bg-white/5 text-[#8e8e88] cursor-not-allowed border border-white/5" 
                  : "bg-primary-container text-on-primary-container hover:brightness-110 shadow-lg shadow-primary/10"
              )}
            >
              <span className="material-symbols-outlined text-[18px]">lock</span>
              Lock Section
            </button>
          ) : (
            <button
              disabled
              className="flex items-center gap-2 px-6 py-2.5 rounded-lg bg-white/5 border border-white/5 text-[#8e8e88] text-[0.8125rem] font-semibold cursor-not-allowed opacity-50"
            >
              <span className="material-symbols-outlined text-[18px]">rule</span>
              Validate Section
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
