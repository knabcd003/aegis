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
      { label: 'Intake', icon: 'tune', path: '/intake' },
      { label: 'LLM Intake', icon: 'smart_toy', path: '/llm-intake' },
      { label: 'Connectors', icon: 'settings', path: '/settings' },
    ],
  },
];

export function Sidebar() {
  const navigate = useNavigate();

  return (
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
                      {/* Active indicator bar */}
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
          onClick={() => navigate('/intake')}
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
  );
}
