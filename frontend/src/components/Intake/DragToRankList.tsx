import { useMemo } from 'react';
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
} from '@dnd-kit/core';
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  verticalListSortingStrategy,
  useSortable,
} from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { GripVertical, X, Plus, Lock } from 'lucide-react';
import type { PriorityEntry, FlexibilityEntry } from '../../types/intake';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

const AVAILABLE_DIMENSIONS = [
  { id: 'capital_preservation', label: 'Capital Preservation' },
  { id: 'return_maximization', label: 'Return Maximization' },
  { id: 'consistency', label: 'Consistency' },
  { id: 'tax_efficiency', label: 'Tax Efficiency' },
  { id: 'catalyst_type_adherence', label: 'Catalyst Type Adherence' },
  { id: 'sector_focus', label: 'Sector Focus' },
  { id: 'execution_simplicity', label: 'Execution Simplicity' },
  { id: 'income_generation', label: 'Income Generation' },
];

interface SortableItemProps {
  id: string;
  entry: PriorityEntry;
  flexibility: string;
  onRemove: (id: string) => void;
  onFlexChange: (id: string, flex: string) => void;
  disabled?: boolean;
}

function SortableItem({ id, entry, flexibility, onRemove, onFlexChange, disabled }: SortableItemProps) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    zIndex: isDragging ? 50 : 0,
  };

  const dimensionLabel = AVAILABLE_DIMENSIONS.find(d => d.id === entry.dimension)?.label || entry.dimension;
  const isImmovable = flexibility === 'immovable';

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={cn(
        "group relative flex items-center gap-4 p-4 rounded-xl border transition-all duration-200",
        isDragging ? "bg-surface-container-high shadow-2xl scale-[1.02] border-secondary/30" : "bg-white/2 border-white/5 hover:border-white/10",
        isImmovable && "bg-terracotta/5 border-terracotta/20"
      )}
    >
      {/* Drag Handle */}
      <button
        {...attributes}
        {...listeners}
        disabled={disabled}
        className={cn(
          "p-1 -ml-1 text-[#8e8e88]/40 hover:text-secondary cursor-grab active:cursor-grabbing transition-colors",
          disabled && "hidden"
        )}
      >
        <GripVertical size={18} />
      </button>

      {/* Rank Badge */}
      <div className="flex items-center justify-center w-6 h-6 rounded-full bg-secondary/10 text-secondary text-[10px] font-mono font-bold">
        {entry.rank}
      </div>

      {/* Label */}
      <span className="flex-1 text-sm font-medium text-on-surface">
        {dimensionLabel}
      </span>

      {/* Flexibility Dropdown */}
      <div className="flex items-center gap-3">
        <select
          value={flexibility}
          onChange={(e) => onFlexChange(entry.dimension, e.target.value)}
          disabled={disabled}
          className={cn(
            "appearance-none bg-transparent outline-none text-xs font-bold uppercase tracking-wider px-2 py-1 rounded transition-all cursor-pointer",
            flexibility === 'flexible' && "text-[#8e8e88]",
            flexibility === 'moderate' && "text-on-surface",
            flexibility === 'strong' && "text-on-surface bg-secondary/10 px-3",
            flexibility === 'immovable' && "text-terracotta bg-terracotta/10 px-3 flex items-center gap-1"
          )}
        >
          <option value="flexible">Flexible</option>
          <option value="moderate">Moderate</option>
          <option value="strong">Strong</option>
          <option value="immovable">Immovable</option>
        </select>
        
        {isImmovable && <Lock size={12} className="text-terracotta -ml-8 pointer-events-none" />}

        <button
          onClick={() => onRemove(entry.dimension)}
          disabled={disabled}
          className="p-1.5 text-[#8e8e88]/40 hover:text-terracotta hover:bg-terracotta/10 rounded-lg transition-all"
        >
          <X size={16} />
        </button>
      </div>
    </div>
  );
}

interface DragToRankListProps {
  value: PriorityEntry[];
  flexibilityValue: FlexibilityEntry[];
  onChange: (value: PriorityEntry[]) => void;
  onFlexibilityChange: (value: FlexibilityEntry[]) => void;
  disabled?: boolean;
}

export function DragToRankList({
  value,
  flexibilityValue,
  onChange,
  onFlexibilityChange,
  disabled = false,
}: DragToRankListProps) {
  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  const unrankedDimensions = useMemo(() => {
    const rankedIds = value.map(v => v.dimension);
    return AVAILABLE_DIMENSIONS.filter(d => !rankedIds.includes(d.id));
  }, [value]);

  const handleDragEnd = (event: any) => {
    const { active, over } = event;

    if (active.id !== over?.id) {
      const oldIndex = value.findIndex((item) => item.dimension === active.id);
      const newIndex = value.findIndex((item) => item.dimension === over?.id);

      const newItems = arrayMove(value, oldIndex, newIndex).map((item, index) => ({
        ...item,
        rank: index + 1,
      }));

      onChange(newItems);
      
      // Re-sync flexibilityValue to match new order
      const newFlex = newItems.map(item => {
        const existing = flexibilityValue.find(f => f.preference === item.dimension);
        return existing || { preference: item.dimension, flexibility: 'moderate', rationale: null };
      });
      onFlexibilityChange(newFlex);
    }
  };

  const handleAdd = (dimId: string) => {
    const newItems = [
      ...value,
      { rank: value.length + 1, dimension: dimId, rationale: null }
    ];
    onChange(newItems);

    const newFlex = [
      ...flexibilityValue,
      { preference: dimId, flexibility: 'moderate', rationale: null }
    ];
    onFlexibilityChange(newFlex);
  };

  const handleRemove = (dimId: string) => {
    const filtered = value.filter(v => v.dimension !== dimId);
    const reordered = filtered.map((v, i) => ({ ...v, rank: i + 1 }));
    onChange(reordered);

    const filteredFlex = flexibilityValue.filter(f => f.preference !== dimId);
    onFlexibilityChange(filteredFlex);
  };

  const handleFlexChange = (dimId: string, flex: string) => {
    const updatedFlex = flexibilityValue.map(f => 
      f.preference === dimId ? { ...f, flexibility: flex } : f
    );
    onFlexibilityChange(updatedFlex);
  };

  const immovableItems = flexibilityValue.filter(f => f.flexibility === 'immovable');

  return (
    <div className="space-y-10">
      
      {/* ZONE 1 - RANKED LIST */}
      <div className="space-y-4">
        <div className="space-y-1">
          <label className="text-[0.6875rem] font-bold uppercase tracking-[0.15em] text-[#8e8e88]">
            Your priorities — drag to reorder
          </label>
          <p className="text-[0.625rem] text-[#8e8e88]/50 uppercase tracking-widest">Most important at the top</p>
        </div>

        <DndContext
          sensors={sensors}
          collisionDetection={closestCenter}
          onDragEnd={handleDragEnd}
        >
          <SortableContext
            items={value.map(v => v.dimension)}
            strategy={verticalListSortingStrategy}
          >
            <div className="flex flex-col gap-2">
              {value.map((entry) => (
                <SortableItem
                  key={entry.dimension}
                  id={entry.dimension}
                  entry={entry}
                  flexibility={flexibilityValue.find(f => f.preference === entry.dimension)?.flexibility || 'moderate'}
                  onRemove={handleRemove}
                  onFlexChange={handleFlexChange}
                  disabled={disabled}
                />
              ))}
              {value.length === 0 && (
                <div className="py-8 border border-dashed border-white/5 rounded-xl flex items-center justify-center text-[#8e8e88]/30 italic text-sm">
                  Add priorities from the pool below
                </div>
              )}
            </div>
          </SortableContext>
        </DndContext>
      </div>

      {/* ZONE 2 - UNRANKED POOL */}
      <div className="pt-10 border-t border-white/10 space-y-4">
        <div className="space-y-1">
          <label className="text-[0.6875rem] font-bold uppercase tracking-[0.15em] text-[#8e8e88]">
            Not yet ranked
          </label>
          <p className="text-[0.625rem] text-[#8e8e88]/50 uppercase tracking-widest">Click + to add to your ranking</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {unrankedDimensions.map((dim) => (
            <div
              key={dim.id}
              className="flex items-center justify-between p-3 px-4 rounded-xl bg-white/2 border border-white/5 hover:bg-white/5 transition-all group"
            >
              <span className="text-sm text-[#8e8e88] group-hover:text-on-surface transition-colors">
                {dim.label}
              </span>
              <button
                onClick={() => handleAdd(dim.id)}
                disabled={disabled}
                className="p-1 rounded-lg bg-secondary/10 text-secondary hover:bg-secondary hover:text-on-secondary transition-all"
              >
                <Plus size={16} />
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* IMMOVABLE SUMMARY */}
      {immovableItems.length > 0 && (
        <div className="p-5 bg-terracotta/5 border border-terracotta/20 rounded-2xl space-y-3 animate-in slide-in-from-bottom-2 duration-300">
          <label className="text-[0.6875rem] font-bold uppercase tracking-[0.2em] text-terracotta">
            Immovable priorities
          </label>
          <div className="space-y-2">
            {immovableItems.map((item) => (
              <div key={item.preference} className="flex items-start gap-2 text-xs text-on-surface/80 leading-relaxed">
                <Lock size={14} className="text-terracotta mt-0.5 shrink-0" />
                <p>
                  <span className="font-bold text-on-surface">{AVAILABLE_DIMENSIONS.find(d => d.id === item.preference)?.label}</span> — Aegis will never sacrifice this, even at significant cost to other goals.
                </p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
