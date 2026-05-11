import { useState, useRef, useEffect } from 'react';
import * as ScrollArea from '@radix-ui/react-scroll-area';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';
import type { AgentMessage } from '../../types/intake';

/**
 * Utility to merge tailwind classes
 */
function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

interface AgentPanelProps {
  messages: AgentMessage[];
  isThinking: boolean;
  onSendMessage: (text: string) => void;
  currentSection: number;
}

export function AgentPanel({
  messages,
  isThinking,
  onSendMessage,
  currentSection,
}: AgentPanelProps) {
  const [inputValue, setInputValue] = useState('');
  const viewportRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom
  useEffect(() => {
    if (viewportRef.current) {
      const viewport = viewportRef.current;
      viewport.scrollTop = viewport.scrollHeight;
    }
  }, [messages, isThinking]);

  const handleSend = () => {
    if (!inputValue.trim() || isThinking) return;
    onSendMessage(inputValue.trim());
    setInputValue('');
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <aside className="w-[380px] h-screen fixed right-0 top-0 bg-surface-container-lowest border-l border-white/5 flex flex-col z-40">
      {/* HEADER */}
      <div className="px-6 py-8 border-b border-white/5 flex items-center justify-between bg-surface-container-lowest/80 backdrop-blur-md">
        <div className="flex items-center gap-3">
          {/* Avatar / Status Dot */}
          <div className="relative">
            <div className="w-10 h-10 rounded-full bg-secondary/10 flex items-center justify-center border border-secondary/20">
              <span className="material-symbols-outlined text-secondary text-[20px]">smart_toy</span>
            </div>
            <div className={cn(
              "absolute -bottom-0.5 -right-0.5 w-3 h-3 rounded-full border-2 border-surface-container-lowest transition-colors duration-500",
              isThinking ? "bg-amber-500 animate-pulse" : "bg-emerald-500"
            )} />
          </div>
          
          <div>
            <h3 className="font-headline text-lg font-light tracking-tight text-on-surface serif-text leading-none">
              Aria
            </h3>
            <p className="text-[0.625rem] uppercase tracking-[0.15em] text-[#8e8e88] mt-1 font-bold">
              {isThinking ? 'Analyzing Mandate...' : 'Ready to Guide'}
            </p>
          </div>
        </div>

        <div className="px-2.5 py-1 rounded-md bg-white/5 border border-white/10">
          <span className="text-[0.625rem] font-bold uppercase tracking-[0.1em] text-[#8e8e88]">
            Section {currentSection.toString().padStart(2, '0')}
          </span>
        </div>
      </div>

      {/* MESSAGES AREA */}
      <ScrollArea.Root className="flex-1 overflow-hidden">
        <ScrollArea.Viewport 
          ref={viewportRef}
          className="w-full h-full p-6 scroll-smooth"
        >
          <div className="space-y-6">
            {messages.map((msg) => (
              <div 
                key={msg.id} 
                className={cn(
                  "flex flex-col max-w-[90%] transition-all duration-300",
                  msg.role === 'user' ? "ml-auto items-end" : "items-start"
                )}
              >
                {/* Bubble */}
                <div className={cn(
                  "px-4 py-3 rounded-2xl relative",
                  msg.role === 'agent' 
                    ? "bg-surface-container border border-white/5 border-l-2 border-l-secondary serif-text text-[0.9375rem] text-on-surface shadow-xl"
                    : "bg-primary/5 border border-primary/10 text-on-surface text-[0.8125rem]"
                )}>
                  {msg.content}
                </div>
                
                {/* Timestamp / Role */}
                <span className="text-[0.625rem] text-[#8e8e88] mt-1.5 px-1 uppercase tracking-widest font-bold">
                  {msg.timestamp}
                </span>
              </div>
            ))}

            {/* THINKING INDICATOR */}
            {isThinking && (
              <div className="flex flex-col items-start max-w-[90%] animate-in fade-in slide-in-from-bottom-2 duration-300">
                <div className="bg-surface-container border border-white/5 border-l-2 border-l-secondary px-4 py-4 rounded-2xl flex gap-1.5">
                  <div className="w-1.5 h-1.5 rounded-full bg-secondary/50 animate-bounce [animation-delay:-0.3s]" />
                  <div className="w-1.5 h-1.5 rounded-full bg-secondary/50 animate-bounce [animation-delay:-0.15s]" />
                  <div className="w-1.5 h-1.5 rounded-full bg-secondary/50 animate-bounce" />
                </div>
              </div>
            )}
          </div>
        </ScrollArea.Viewport>
        <ScrollArea.Scrollbar 
          className="flex select-none touch-none p-0.5 bg-transparent transition-colors duration-150 ease-out hover:bg-white/5 data-[orientation=vertical]:w-1.5"
          orientation="vertical"
        >
          <ScrollArea.Thumb className="flex-1 bg-white/10 rounded-[10px] relative before:content-[''] before:absolute before:top-1/2 before:left-1/2 before:-translate-x-1/2 before:-translate-y-1/2 before:w-full before:h-full before:min-w-[44px] before:min-h-[44px]" />
        </ScrollArea.Scrollbar>
      </ScrollArea.Root>

      {/* INPUT AREA */}
      <div className="p-6 border-t border-white/5 bg-surface-container-lowest/80 backdrop-blur-md">
        <div className="relative group transition-all duration-300">
          <textarea
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isThinking}
            rows={2}
            placeholder="Type a message..."
            className={cn(
              "w-full bg-surface-container border border-white/10 rounded-xl px-4 py-3 text-[0.875rem] text-on-surface placeholder-[#8e8e88]/50 resize-none outline-none focus:border-primary/30 focus:ring-1 focus:ring-primary/20 transition-all scrollbar-thin",
              isThinking && "opacity-50 cursor-not-allowed"
            )}
            style={{ minHeight: '80px', maxHeight: '160px' }}
          />
          
          <button
            onClick={handleSend}
            disabled={!inputValue.trim() || isThinking}
            className={cn(
              "absolute right-3 bottom-3 w-8 h-8 rounded-lg flex items-center justify-center transition-all duration-200",
              !inputValue.trim() || isThinking 
                ? "bg-white/5 text-[#8e8e88] cursor-not-allowed" 
                : "bg-primary text-on-primary-fixed hover:scale-105 active:scale-95 shadow-lg shadow-primary/20"
            )}
          >
            <span className="material-symbols-outlined text-[18px]">send</span>
          </button>
        </div>
        
        <div className="mt-3 flex items-center justify-between">
          <span className="text-[0.625rem] text-[#8e8e88]/50 flex items-center gap-1">
            <span className="material-symbols-outlined text-[12px]">keyboard_return</span>
            <span>Enter to send</span>
          </span>
          <span className="text-[0.625rem] text-[#8e8e88]/50">
            Aria v10.0 • AI Guide
          </span>
        </div>
      </div>
    </aside>
  );
}
