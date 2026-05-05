import React, { useState, useRef, useEffect } from 'react';

interface ChatMessage {
  id: string;
  role: 'user' | 'system';
  content: string;
}

interface ConversationalChatProps {
  onStageChange: (stage: number) => void;
  onSchemaUpdate: (schema: any) => void;
  onComplete: () => void;
  sessionIdOverride?: string | null;
  onSessionInit?: (sessionId: string) => void;
  schemaWip?: any;
}

export function ConversationalChat({ onStageChange, onSchemaUpdate, onComplete, sessionIdOverride, onSessionInit, schemaWip }: ConversationalChatProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [localSessionId, setLocalSessionId] = useState<string | null>(null);
  
  const sessionId = sessionIdOverride !== undefined ? sessionIdOverride : localSessionId;
  
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Initial greeting (Stage 0)
  useEffect(() => {
    sendMessage('', true);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const sendMessage = async (text: string, isInit = false) => {
    if (!text.trim() && !isInit) return;
    
    if (!isInit) {
      setMessages(prev => [...prev, { id: Date.now().toString(), role: 'user', content: text }]);
      setInputValue('');
    }
    
    setIsLoading(true);
    try {
      const res = await fetch('http://localhost:8000/api/intake/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          message: isInit ? 'init' : text,
          schema_update: !isInit ? schemaWip : undefined
        })
      });
      
      if (!res.ok) throw new Error('Network response was not ok');
      const data = await res.json();
      
      if (!sessionId && data.session_id) {
        if (onSessionInit) {
          onSessionInit(data.session_id);
        } else {
          setLocalSessionId(data.session_id);
        }
        // Persist session ID in session storage if needed
        sessionStorage.setItem('aegis_intake_session', data.session_id);
      }
      
      setMessages(prev => [...prev, { id: (Date.now() + 1).toString(), role: 'system', content: data.response }]);
      onStageChange(data.current_stage);
      onSchemaUpdate(data.schema_wip);
      
      if (data.current_stage === 8 || data.locked) {
        onComplete();
      }
    } catch (err) {
      console.error('Chat error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage(inputValue);
    }
  };

  return (
    <div className="flex flex-col h-[500px] bg-surface-container border border-white/5 rounded-xl overflow-hidden">
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {messages.map((msg) => (
          <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div 
              className={`max-w-[80%] p-4 rounded-2xl ${
                msg.role === 'user' 
                  ? 'bg-primary-container text-on-primary-container rounded-tr-sm' 
                  : 'bg-surface-container-high text-on-surface rounded-tl-sm border border-white/5'
              }`}
            >
              <p className="text-sm leading-relaxed whitespace-pre-wrap">{msg.content}</p>
            </div>
          </div>
        ))}
        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-surface-container-high border border-white/5 rounded-2xl rounded-tl-sm p-4 flex gap-1 items-center">
              <span className="w-2 h-2 rounded-full bg-[#8e8e88] animate-bounce" style={{ animationDelay: '0ms' }} />
              <span className="w-2 h-2 rounded-full bg-[#8e8e88] animate-bounce" style={{ animationDelay: '150ms' }} />
              <span className="w-2 h-2 rounded-full bg-[#8e8e88] animate-bounce" style={{ animationDelay: '300ms' }} />
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
      
      <div className="p-4 bg-surface-container-low border-t border-white/5">
        <div className="relative flex items-center">
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Type your response..."
            disabled={isLoading}
            className="w-full bg-surface-container border border-white/10 rounded-full pl-6 pr-12 py-4 text-sm text-on-surface placeholder:text-[#8e8e88] focus:outline-none focus:ring-1 focus:ring-primary/50 disabled:opacity-50"
          />
          <button 
            onClick={() => sendMessage(inputValue)}
            disabled={!inputValue.trim() || isLoading}
            className="absolute right-2 p-2 rounded-full bg-primary-container text-on-primary-container disabled:opacity-50 hover:brightness-110 transition-all flex items-center justify-center"
          >
            <span className="material-symbols-outlined text-[20px]">arrow_upward</span>
          </button>
        </div>
      </div>
    </div>
  );
}
