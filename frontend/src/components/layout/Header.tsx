import { RefreshCw, ChevronDown, Menu, LogOut, User } from 'lucide-react';
import type { AppMode, Location } from '../../types/api';
import type { AuthUser } from '../../hooks/useStore';

interface HeaderProps {
  mode: AppMode;
  locations: Location[];
  activeLocationId: string | null;
  onLocationChange: (id: string | null) => void;
  onRecompute: () => void;
  dashboardStatus: 'green' | 'yellow' | 'red' | null;
  snapshotAt: string | null;
  loading: boolean;
  onMenuToggle: () => void;
  user: AuthUser | null;
  onLogout: () => void;
}

const STATUS_COLORS: Record<string, string> = {
  green: 'bg-emerald-400',
  yellow: 'bg-amber-400',
  red: 'bg-red-400',
};

function formatTimestamp(iso: string | null): string {
  if (!iso) return '--';
  try {
    const d = new Date(iso);
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  } catch {
    return iso;
  }
}

export function Header({
  mode,
  locations,
  activeLocationId,
  onLocationChange,
  onRecompute,
  dashboardStatus,
  snapshotAt,
  loading,
  onMenuToggle,
  user,
  onLogout,
}: HeaderProps) {
  return (
    <header className="flex items-center justify-between gap-2 min-h-14 px-3 sm:px-4 lg:px-6 py-2 bg-white border-b border-gray-200 shrink-0">
      {/* Left: Hamburger + Location selector + status */}
      <div className="flex items-center gap-2 sm:gap-4 min-w-0 flex-1">
        {/* Hamburger — mobile only */}
        <button
          onClick={onMenuToggle}
          className="lg:hidden p-1.5 -ml-1 rounded-md text-gray-600 hover:text-gray-900 hover:bg-gray-100 transition-colors cursor-pointer"
        >
          <Menu className="w-5 h-5" />
        </button>

        <div className="relative min-w-0 flex-1 sm:flex-none">
          <select
            value={activeLocationId ?? ''}
            onChange={(e) => onLocationChange(e.target.value || null)}
            className="appearance-none w-full sm:w-auto bg-gray-50 border border-gray-200 rounded-lg pl-3 pr-8 py-1.5 text-sm font-medium text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent cursor-pointer"
          >
            <option value="">Select location...</option>
            {locations.map((loc) => (
              <option key={loc.id} value={loc.id}>
                {loc.name}
              </option>
            ))}
          </select>
          <ChevronDown className="absolute right-2 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
        </div>

        {dashboardStatus && (
          <div className="flex items-center gap-1.5 shrink-0">
            <span
              className={`w-2.5 h-2.5 rounded-full ${STATUS_COLORS[dashboardStatus] ?? 'bg-gray-300'}`}
            />
            <span className="text-xs font-medium text-gray-500 capitalize hidden sm:inline">
              {dashboardStatus}
            </span>
          </div>
        )}

        {snapshotAt && (
          <span className="text-xs text-gray-400 hidden md:inline shrink-0">
            Updated {formatTimestamp(snapshotAt)}
          </span>
        )}
      </div>

      {/* Right: Mode badge + Recompute */}
      <div className="flex items-center gap-2 sm:gap-3 shrink-0">
        <span
          className={`
            inline-flex items-center px-2 py-0.5 rounded text-[11px] font-bold uppercase tracking-wider
            ${mode === 'demo' ? 'bg-amber-100 text-amber-700' : 'bg-emerald-100 text-emerald-700'}
          `}
        >
          {mode}
        </span>

        <button
          onClick={onRecompute}
          disabled={loading || !activeLocationId}
          className="inline-flex items-center gap-1.5 px-2.5 sm:px-3 py-1.5 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-150 cursor-pointer"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span className="hidden sm:inline">Recompute</span>
        </button>

        {/* User menu */}
        {user && (
          <div className="flex items-center gap-2 pl-2 sm:pl-3 border-l border-gray-200">
            <div className="hidden sm:flex items-center gap-1.5">
              <div className="w-6 h-6 rounded-full bg-gray-200 flex items-center justify-center">
                <User className="w-3.5 h-3.5 text-gray-600" />
              </div>
              <span className="text-xs font-medium text-gray-700 max-w-[100px] truncate">{user.full_name}</span>
              {user.role === 'admin' && (
                <span className="text-[10px] font-bold uppercase px-1.5 py-0.5 rounded bg-purple-100 text-purple-700">admin</span>
              )}
            </div>
            <button
              onClick={onLogout}
              title="Sign out"
              className="p-1.5 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-md transition-colors cursor-pointer"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        )}
      </div>
    </header>
  );
}
