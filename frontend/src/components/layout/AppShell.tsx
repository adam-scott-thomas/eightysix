import { useState, type ReactNode } from 'react';
import { Sidebar } from './Sidebar';
import { Header } from './Header';
import type { AppMode, Location } from '../../types/api';
import type { AuthUser } from '../../hooks/useStore';

interface AppShellProps {
  mode: AppMode;
  onModeChange: (mode: AppMode) => void;
  activePage: string;
  onNavigate: (page: string) => void;
  locations: Location[];
  activeLocationId: string | null;
  onLocationChange: (id: string | null) => void;
  onRecompute: () => void;
  dashboardStatus: 'green' | 'yellow' | 'red' | null;
  snapshotAt: string | null;
  loading: boolean;
  user: AuthUser | null;
  onLogout: () => void;
  children: ReactNode;
}

export function AppShell({
  mode,
  onModeChange,
  activePage,
  onNavigate,
  locations,
  activeLocationId,
  onLocationChange,
  onRecompute,
  dashboardStatus,
  snapshotAt,
  loading,
  user,
  onLogout,
  children,
}: AppShellProps) {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Backdrop for mobile sidebar */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar — always visible on desktop, slide-in overlay on mobile */}
      <Sidebar
        mode={mode}
        onModeChange={onModeChange}
        activePage={activePage}
        onNavigate={(page) => {
          onNavigate(page);
          setSidebarOpen(false);
        }}
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
      />

      <div className="flex-1 flex flex-col overflow-hidden min-w-0">
        <Header
          mode={mode}
          locations={locations}
          activeLocationId={activeLocationId}
          onLocationChange={onLocationChange}
          onRecompute={onRecompute}
          dashboardStatus={dashboardStatus}
          snapshotAt={snapshotAt}
          loading={loading}
          onMenuToggle={() => setSidebarOpen(true)}
          user={user}
          onLogout={onLogout}
        />
        <main className="flex-1 overflow-y-auto p-3 sm:p-4 lg:p-6 bg-gray-50">
          {children}
        </main>
      </div>
    </div>
  );
}
