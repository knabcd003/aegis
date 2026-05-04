import { useState, useRef } from 'react';
import { useLocation } from 'react-router-dom';
import { UserProfileDropdown } from './UserProfileDropdown';

const PAGE_TITLES: Record<string, string> = {
  '/': 'Mission Control',
  '/portfolio': 'Portfolio Tracker',
  '/health': 'System Health',
  '/pipeline': 'Pipeline Map',
  '/components': 'Component Library',
  '/sandbox': 'Sandbox',
  '/glass-box': 'Glass Box',
  '/arena': 'Arena',
  '/debates': 'Debate Theater',
  '/budget': 'Budget Dashboard',
  '/intake': 'Intake',
  '/settings': 'Connectors',
};

export function Topbar() {
  const location = useLocation();
  const pageTitle = PAGE_TITLES[location.pathname] || 'Aegis AI';
  const [profileOpen, setProfileOpen] = useState(false);
  const avatarRef = useRef<HTMLButtonElement>(null);

  return (
    <header className="flex justify-between items-center w-full px-8 h-16 sticky top-0 z-40 bg-surface/80 backdrop-blur-md shadow-[0_1px_0_0_rgba(255,255,255,0.05)]">
      {/* Left: Page Title */}
      <div className="flex items-center gap-4">
        <h2 className="font-headline text-lg font-medium tracking-tight text-on-surface">
          {pageTitle}
        </h2>
      </div>

      {/* Right: Status Indicators */}
      <div className="flex items-center gap-4 text-[#8e8e88]">
        {/* Session quality indicator */}
        <div className="flex items-center gap-2 bg-surface-container px-3 py-1.5 rounded-lg border border-white/5">
          <span className="w-1.5 h-1.5 rounded-full bg-secondary animate-pulse" />
          <span className="text-[0.6875rem] font-label uppercase tracking-widest text-[#8e8e88]">
            System Online
          </span>
        </div>

        {/* Notifications */}
        <button
          className="p-2 hover:bg-[#1a1a19] rounded-lg transition-colors relative"
          title="Notifications"
        >
          <span
            className="material-symbols-outlined text-[20px]"
            style={{ fontVariationSettings: "'wght' 300" }}
          >
            notifications
          </span>
        </button>

        {/* Avatar + Profile Dropdown */}
        <div className="relative">
          <button
            ref={avatarRef}
            onClick={() => setProfileOpen((prev) => !prev)}
            className={`w-8 h-8 rounded-full border flex items-center justify-center transition-all duration-200 ${
              profileOpen
                ? 'bg-primary-container border-primary-container'
                : 'bg-surface-container-high border-white/10 hover:border-white/20'
            }`}
            title="Account"
          >
            <span
              className={`material-symbols-outlined text-[18px] ${
                profileOpen ? 'text-on-primary-container' : 'text-[#8e8e88]'
              }`}
              style={{
                fontVariationSettings: profileOpen
                  ? "'FILL' 1, 'wght' 400"
                  : "'wght' 300",
              }}
            >
              person
            </span>
          </button>
          <UserProfileDropdown
            open={profileOpen}
            onClose={() => setProfileOpen(false)}
            anchorRef={avatarRef}
          />
        </div>
      </div>
    </header>
  );
}
