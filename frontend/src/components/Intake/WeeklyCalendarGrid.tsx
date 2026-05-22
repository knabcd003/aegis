import { useState, useEffect } from 'react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

/**
 * Utility to merge tailwind classes
 */
function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

interface WeeklyCalendarGridProps {
  value: {
    days: string[];
    start_time_et: string | null;
    end_time_et: string | null;
  }[];
  onChange: (value: any[]) => void;
  disabled?: boolean;
}

const DAYS = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday'];
const HOURS = [9, 10, 11, 12, 13, 14, 15, 16]; // 9 AM to 4 PM start times

export function WeeklyCalendarGrid({
  value = [],
  onChange,
  disabled = false,
}: WeeklyCalendarGridProps) {
  // We'll simplify the state for the UI: a set of "day-hour" strings
  const [selectedCells, setSelectedCells] = useState<Set<string>>(new Set());

  // Initialize UI state from incoming schema value
  useEffect(() => {
    const newCells = new Set<string>();
    value.forEach(window => {
      if (window.start_time_et && window.end_time_et) {
        const startHour = parseInt(window.start_time_et.split(':')[0]);
        const endHour = parseInt(window.end_time_et.split(':')[0]);
        window.days.forEach(day => {
          for (let h = startHour; h < endHour; h++) {
            newCells.add(`${day}-${h}`);
          }
        });
      }
    });
    setSelectedCells(newCells);
  }, []);

  const toggleCell = (day: string, hour: number) => {
    if (disabled) return;
    const key = `${day}-${hour}`;
    const next = new Set(selectedCells);
    if (next.has(key)) {
      next.delete(key);
    } else {
      next.add(key);
    }
    setSelectedCells(next);
    
    // Map back to schema structure: group by day and contiguous hours
    const windows: any[] = [];
    
    DAYS.forEach(d => {
      const dayHours = HOURS.filter(h => next.has(`${d}-${h}`)).sort((a, b) => a - b);
      
      if (dayHours.length === 0) return;

      let currentWindow: any = null;

      dayHours.forEach(h => {
        if (!currentWindow) {
          currentWindow = { days: [d], start: h, end: h + 1 };
        } else if (h === currentWindow.end) {
          currentWindow.end = h + 1;
        } else {
          windows.push({
            days: currentWindow.days,
            start_time_et: `${currentWindow.start.toString().padStart(2, '0')}:00`,
            end_time_et: `${currentWindow.end.toString().padStart(2, '0')}:00`
          });
          currentWindow = { days: [d], start: h, end: h + 1 };
        }
      });

      if (currentWindow) {
        windows.push({
          days: currentWindow.days,
          start_time_et: `${currentWindow.start.toString().padStart(2, '0')}:00`,
          end_time_et: `${currentWindow.end.toString().padStart(2, '0')}:00`
        });
      }
    });

    // Final pass: merge identical windows across different days
    const merged: any[] = [];
    windows.forEach(w => {
      const match = merged.find(m => m.start_time_et === w.start_time_et && m.end_time_et === w.end_time_et);
      if (match) {
        if (!match.days.includes(w.days[0])) match.days.push(w.days[0]);
      } else {
        merged.push(w);
      }
    });

    onChange(merged);
  };

  return (
    <div className={cn("w-full overflow-hidden rounded-xl border border-white/5 bg-surface-container/30", disabled && "opacity-40 pointer-events-none")}>
      <div className="grid grid-cols-6 border-b border-white/5">
        <div className="p-3 border-r border-white/5 bg-white/5"></div>
        {DAYS.map(day => (
          <div key={day} className="p-3 text-center text-[0.625rem] font-bold uppercase tracking-widest text-[#8e8e88] border-r border-white/5 last:border-r-0">
            {day.slice(0, 3)}
          </div>
        ))}
      </div>

      <div className="divide-y divide-white/5">
        {HOURS.map(hour => (
          <div key={hour} className="grid grid-cols-6 group">
            <div className="p-3 border-r border-white/5 text-[0.625rem] font-medium text-[#8e8e88]/60 flex items-center justify-center bg-white/2">
              {hour > 12 ? hour - 12 : hour}{hour >= 12 ? ' PM' : ' AM'}
            </div>
            {DAYS.map(day => {
              const isSelected = selectedCells.has(`${day}-${hour}`);
              return (
                <button
                  key={`${day}-${hour}`}
                  onClick={() => toggleCell(day, hour)}
                  className={cn(
                    "h-12 border-r border-white/5 last:border-r-0 transition-all duration-200 outline-none",
                    isSelected 
                      ? "bg-secondary/20 shadow-[inset_0_0_20px_rgba(172,206,197,0.1)] border-secondary/30" 
                      : "hover:bg-white/5"
                  )}
                >
                  {isSelected && (
                    <div className="w-full h-full flex items-center justify-center">
                      <div className="w-1.5 h-1.5 rounded-full bg-secondary shadow-[0_0_8px_rgba(172,206,197,0.5)]" />
                    </div>
                  )}
                </button>
              );
            })}
          </div>
        ))}
      </div>
    </div>
  );
}
