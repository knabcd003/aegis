import { useState } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';

interface NavItem {
  label: string;
  icon: string;
  path: string;
}

interface NavGroup {
  title: string;
  items: NavItem[];
}

const NAV_GROUPS: NavGroup[] = [
  {
    title: 'Observe',
    items: [
      { label: 'Mission Control', icon: 'dashboard', path: '/' },
      { label: 'Portfolio', icon: 'account_balance', path: '/portfolio' },
      { label: 'System Health', icon: 'health_and_safety', path: '/health' },
    ],
  },
  {
    title: 'Pipeline',
    items: [
      { label: 'Pipeline Map', icon: 'hub', path: '/pipeline' },
      { label: 'Components', icon: 'widgets', path: '/components' },
      { label: 'Sandbox', icon: 'biotech', path: '/sandbox' },
    ],
  },
  {
    title: 'Analyze',
    items: [
      { label: 'Glass Box', icon: 'policy', path: '/glass-box' },
      { label: 'Arena', icon: 'leaderboard', path: '/arena' },
      { label: 'Debates', icon: 'forum', path: '/debates' },
      { label: 'Budget', icon: 'payments', path: '/budget' },
    ],
  },
  {
    title: 'Settings',
    items: [
      { label: 'Connectors', icon: 'settings', path: '/settings' },
    ],
  },
];

function NewSentinelModal({ onClose }: { onClose: () => void }) {
  const navigate = useNavigate();

  const choose = (path: string) => {
    onClose();
    navigate(path);
  };

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 z-[60] bg-black/60 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="fixed z-[70] left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-[520px] max-w-[95vw]">
        <div className="rounded-2xl bg-[#151512]/95 border border-[#8e8e88]/20 shadow-[0_24px_64px_rgba(0,0,0,0.6)] backdrop-blur-xl overflow-hidden">

          {/* Header */}
          <div className="px-8 pt-8 pb-6 border-b border-white/5">
            <div className="flex items-center gap-3 mb-1">
              <span
                className="material-symbols-outlined text-[22px] text-[#ACCEC5]"
                style={{ fontVariationSettings: "'FILL' 1, 'wght' 400" }}
              >
                add_circle
              </span>
              <h2 className="font-headline text-2xl font-light text-on-surface tracking-tight">
                New Sentinel
              </h2>
            </div>
            <p className="text-[0.8125rem] text-[#8e8e88] leading-relaxed">
              Choose how you want to define your investment mandate.
            </p>
          </div>

          {/* Options */}
          <div className="p-6 grid grid-cols-2 gap-4">

            {/* Option 1 — Guided Form with Aria */}
            <button
              id="new-sentinel-guided-form"
              onClick={() => choose('/intake')}
              className="group relative flex flex-col gap-4 p-6 rounded-xl bg-[#1c1c18] border border-[#8e8e88]/15 hover:border-[#ACCEC5]/40 hover:bg-[#1f1f1b] transition-all duration-200 text-left"
            >
              <div className="w-10 h-10 rounded-lg bg-[#ACCEC5]/10 border border-[#ACCEC5]/20 flex items-center justify-center group-hover:bg-[#ACCEC5]/15 transition-colors">
                <span
                  className="material-symbols-outlined text-[22px] text-[#ACCEC5]"
                  style={{ fontVariationSettings: "'FILL' 0, 'wght' 300" }}
                >
                  tune
                </span>
              </div>

              <div className="space-y-1.5">
                <div className="flex items-center gap-2">
                  <span className="text-[0.875rem] font-semibold text-on-surface">
                    Guided Form
                  </span>
                  <span className="text-[9px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded bg-[#ACCEC5]/10 text-[#ACCEC5]">
                    Aria
                  </span>
                </div>
                <p className="text-[0.75rem] text-[#8e8e88] leading-relaxed">
                  Fill out your mandate section-by-section. Aria watches every
                  field and gives real-time context, suggestions, and conflict
                  warnings.
                </p>
              </div>

              <div className="flex items-center gap-1.5 text-[#ACCEC5] text-[0.75rem] font-medium group-hover:gap-2.5 transition-all">
                <span>Start form</span>
                <span className="material-symbols-outlined text-[16px]">arrow_forward</span>
              </div>
            </button>

            {/* Option 2 — LLM Chat Intake */}
            <button
              id="new-sentinel-llm-chat"
              onClick={() => choose('/llm-intake')}
              className="group relative flex flex-col gap-4 p-6 rounded-xl bg-[#1c1c18] border border-[#8e8e88]/15 hover:border-[#b8a9f5]/40 hover:bg-[#1f1f1b] transition-all duration-200 text-left"
            >
              <div className="w-10 h-10 rounded-lg bg-[#b8a9f5]/10 border border-[#b8a9f5]/20 flex items-center justify-center group-hover:bg-[#b8a9f5]/15 transition-colors">
                <span
                  className="material-symbols-outlined text-[22px] text-[#b8a9f5]"
                  style={{ fontVariationSettings: "'FILL' 0, 'wght' 300" }}
                >
                  smart_toy
                </span>
              </div>

              <div className="space-y-1.5">
                <div className="flex items-center gap-2">
                  <span className="text-[0.875rem] font-semibold text-on-surface">
                    LLM Chat
                  </span>
                  <span className="text-[9px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded bg-[#b8a9f5]/10 text-[#b8a9f5]">
                    Conversational
                  </span>
                </div>
                <p className="text-[0.75rem] text-[#8e8e88] leading-relaxed">
                  Just talk. The AI extracts your mandate through natural
                  conversation and builds the schema from your answers.
                </p>
              </div>

              <div className="flex items-center gap-1.5 text-[#b8a9f5] text-[0.75rem] font-medium group-hover:gap-2.5 transition-all">
                <span>Start chat</span>
                <span className="material-symbols-outlined text-[16px]">arrow_forward</span>
              </div>
            </button>
          </div>

          {/* Footer */}
          <div className="px-6 pb-6 flex justify-end">
            <button
              onClick={onClose}
              className="px-4 py-2 text-[0.75rem] text-[#8e8e88] hover:text-on-surface transition-colors"
            >
              Cancel
            </button>
          </div>
        </div>
      </div>
    </>
  );
}

export function Sidebar() {
  const [showModal, setShowModal] = useState(false);

  return (
    <>
      <aside className="flex flex-col h-screen w-64 fixed left-0 top-0 bg-surface border-r border-white/5 z-50">
        {/* Brand */}
        <div className="px-6 pt-8 pb-6">
          <h1 className="font-headline text-2xl font-light text-on-surface tracking-tight">
            Aegis AI
          </h1>
          <p className="text-[0.6875rem] uppercase tracking-[0.15em] text-[#8e8e88] mt-1 font-label">
            Intelligence Core v7
          </p>
        </div>

        {/* Navigation Groups */}
        <nav className="flex-1 overflow-y-auto scrollbar-thin px-2 space-y-6">
          {NAV_GROUPS.map((group) => (
            <div key={group.title}>
              <h2 className="text-[0.625rem] font-bold uppercase tracking-[0.2em] text-[#8e8e88] px-4 mb-1.5">
                {group.title}
              </h2>
              <div className="space-y-0.5">
                {group.items.map((item) => (
                  <NavLink
                    key={item.path}
                    to={item.path}
                    end={item.path === '/'}
                    className={({ isActive }) =>
                      `flex items-center gap-3 px-4 py-2.5 transition-all duration-200 group relative ${
                        isActive
                          ? 'bg-[#1c1c1b] text-[#FFB59E]'
                          : 'text-[#8e8e88] hover:text-on-surface hover:bg-[#1a1a19]'
                      }`
                    }
                  >
                    {({ isActive }) => (
                      <>
                        {isActive && (
                          <span className="absolute right-0 top-1 bottom-1 w-[2px] bg-primary-container rounded-l" />
                        )}
                        <span
                          className={`material-symbols-outlined text-[20px] transition-transform duration-200 ${
                            !isActive ? 'group-hover:translate-x-0.5' : ''
                          }`}
                          style={{
                            fontVariationSettings: isActive
                              ? "'FILL' 1, 'wght' 400, 'GRAD' 0, 'opsz' 20"
                              : "'FILL' 0, 'wght' 300, 'GRAD' 0, 'opsz' 20",
                          }}
                        >
                          {item.icon}
                        </span>
                        <span className="text-[0.8125rem] tracking-wide font-label">
                          {item.label}
                        </span>
                      </>
                    )}
                  </NavLink>
                ))}
              </div>
            </div>
          ))}
        </nav>

        {/* Bottom Section */}
        <div className="px-4 pb-6 pt-4 border-t border-white/5 space-y-3">
          <button
            id="new-sentinel-btn"
            onClick={() => setShowModal(true)}
            className="w-full py-3 bg-primary-container text-on-primary-container text-[0.8125rem] font-semibold rounded-lg hover:brightness-110 active:scale-[0.98] transition-all duration-200 flex items-center justify-center gap-2"
          >
            <span
              className="material-symbols-outlined text-[18px]"
              style={{ fontVariationSettings: "'FILL' 1, 'wght' 500" }}
            >
              add_circle
            </span>
            New Sentinel
          </button>
          <div className="space-y-0.5">
            <a
              href="https://github.com"
              target="_blank"
              rel="noreferrer"
              className="flex items-center gap-3 px-3 py-2 text-[#8e8e88] hover:text-on-surface text-[0.75rem] transition-colors"
            >
              <span className="material-symbols-outlined text-[18px]" style={{ fontVariationSettings: "'wght' 300" }}>
                menu_book
              </span>
              Documentation
            </a>
          </div>
        </div>
      </aside>

      {showModal && <NewSentinelModal onClose={() => setShowModal(false)} />}
    </>
  );
}
