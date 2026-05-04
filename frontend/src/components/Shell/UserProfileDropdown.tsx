import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';

const API = 'http://localhost:8000/api/setup';

interface ProfileData {
  user_id: string;
  created_at: string | null;
  connected_services: string[];
  connected_count: number;
  provider_count: number;
  roles_assigned: number;
  roles_total: number;
}

interface Props {
  open: boolean;
  onClose: () => void;
  anchorRef: React.RefObject<HTMLElement | null>;
}

export function UserProfileDropdown({ open, onClose, anchorRef }: Props) {
  const [profile, setProfile] = useState<ProfileData | null>(null);
  const [loading, setLoading] = useState(true);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();

  useEffect(() => {
    if (!open) return;
    setLoading(true);
    fetch(`${API}/profile`)
      .then((r) => r.json())
      .then((data) => {
        setProfile(data);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [open]);

  // Close on click outside
  useEffect(() => {
    if (!open) return;
    const handler = (e: MouseEvent) => {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(e.target as Node) &&
        anchorRef.current &&
        !anchorRef.current.contains(e.target as Node)
      ) {
        onClose();
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [open, onClose, anchorRef]);

  // Close on Escape
  useEffect(() => {
    if (!open) return;
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', handler);
    return () => document.removeEventListener('keydown', handler);
  }, [open, onClose]);

  if (!open) return null;

  const navigateTo = (path: string) => {
    navigate(path);
    onClose();
  };

  const createdDate = profile?.created_at
    ? new Date(profile.created_at + 'Z').toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
      })
    : '—';

  return (
    <div
      ref={dropdownRef}
      className="absolute top-full right-0 mt-2 w-80 bg-surface border border-white/10 rounded-xl shadow-2xl shadow-black/40 z-[60] overflow-hidden animate-in fade-in slide-in-from-top-2 duration-200"
    >
      {/* Header */}
      <div className="p-5 border-b border-white/5">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-primary-container flex items-center justify-center">
            <span className="text-on-primary-container font-headline text-lg font-medium">
              {loading ? '…' : (profile?.user_id?.[0] || 'U').toUpperCase()}
            </span>
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-on-surface truncate">
              {loading ? 'Loading…' : profile?.user_id || 'User'}
            </p>
            <p className="text-[0.6875rem] text-[#8e8e88]">
              Member since {createdDate}
            </p>
          </div>
        </div>
      </div>

      {/* Stats Grid */}
      {!loading && profile && (
        <div className="grid grid-cols-3 divide-x divide-white/5 border-b border-white/5">
          <div className="p-3 text-center">
            <p className="text-lg font-headline font-medium text-on-surface">{profile.provider_count}</p>
            <p className="text-[0.625rem] uppercase tracking-widest text-[#8e8e88]">Providers</p>
          </div>
          <div className="p-3 text-center">
            <p className="text-lg font-headline font-medium text-on-surface">{profile.connected_count}</p>
            <p className="text-[0.625rem] uppercase tracking-widest text-[#8e8e88]">Services</p>
          </div>
          <div className="p-3 text-center">
            <p className="text-lg font-headline font-medium text-on-surface">
              {profile.roles_assigned}
              <span className="text-[#8e8e88] text-xs">/{profile.roles_total}</span>
            </p>
            <p className="text-[0.625rem] uppercase tracking-widest text-[#8e8e88]">Roles</p>
          </div>
        </div>
      )}

      {/* Connected Services */}
      {!loading && profile && profile.connected_services.length > 0 && (
        <div className="px-5 py-3 border-b border-white/5">
          <p className="text-[0.625rem] uppercase tracking-widest text-[#8e8e88] font-bold mb-2">
            Connected Services
          </p>
          <div className="flex flex-wrap gap-1.5">
            {profile.connected_services.map((svc) => (
              <span
                key={svc}
                className="px-2 py-0.5 bg-secondary/10 text-secondary text-[0.625rem] font-medium rounded border border-secondary/20"
              >
                {svc}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Actions */}
      <div className="p-2">
        <button
          onClick={() => navigateTo('/settings')}
          className="w-full flex items-center gap-3 px-3 py-2.5 text-on-surface-variant hover:text-on-surface hover:bg-surface-container-high rounded-lg transition-colors text-left"
        >
          <span
            className="material-symbols-outlined text-[18px]"
            style={{ fontVariationSettings: "'wght' 300" }}
          >
            settings
          </span>
          <div>
            <p className="text-[0.8125rem] font-medium">Provider Configuration</p>
            <p className="text-[0.625rem] text-[#8e8e88]">Manage AI models and data connections</p>
          </div>
        </button>

        <button
          onClick={() => navigateTo('/intake')}
          className="w-full flex items-center gap-3 px-3 py-2.5 text-on-surface-variant hover:text-on-surface hover:bg-surface-container-high rounded-lg transition-colors text-left"
        >
          <span
            className="material-symbols-outlined text-[18px]"
            style={{ fontVariationSettings: "'wght' 300" }}
          >
            tune
          </span>
          <div>
            <p className="text-[0.8125rem] font-medium">Mandate Settings</p>
            <p className="text-[0.625rem] text-[#8e8e88]">Configure trading strategies and constraints</p>
          </div>
        </button>

        <button
          onClick={() => navigateTo('/budget')}
          className="w-full flex items-center gap-3 px-3 py-2.5 text-on-surface-variant hover:text-on-surface hover:bg-surface-container-high rounded-lg transition-colors text-left"
        >
          <span
            className="material-symbols-outlined text-[18px]"
            style={{ fontVariationSettings: "'wght' 300" }}
          >
            payments
          </span>
          <div>
            <p className="text-[0.8125rem] font-medium">Budget & Quotas</p>
            <p className="text-[0.625rem] text-[#8e8e88]">Token usage and provider spend</p>
          </div>
        </button>

        <div className="my-1 border-t border-white/5" />

        <button
          onClick={() => navigateTo('/health')}
          className="w-full flex items-center gap-3 px-3 py-2.5 text-on-surface-variant hover:text-on-surface hover:bg-surface-container-high rounded-lg transition-colors text-left"
        >
          <span
            className="material-symbols-outlined text-[18px]"
            style={{ fontVariationSettings: "'wght' 300" }}
          >
            health_and_safety
          </span>
          <div>
            <p className="text-[0.8125rem] font-medium">System Health</p>
            <p className="text-[0.625rem] text-[#8e8e88]">Connector and provider diagnostics</p>
          </div>
        </button>
      </div>
    </div>
  );
}
