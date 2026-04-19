import {
  LayoutDashboard,
  Bell,
  Lightbulb,
  Shield,
  Database,
  UtensilsCrossed,
  X,
} from 'lucide-react';

interface SidebarProps {
  activePage: string;
  onNavigate: (page: string) => void;
  isOpen: boolean;
  onClose: () => void;
}

const NAV_ITEMS = [
  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { id: 'data', label: 'Data Input', icon: Database },
  { id: 'alerts', label: 'Alerts', icon: Bell },
  { id: 'recommendations', label: 'Actions', icon: Lightbulb },
  { id: 'integrity', label: 'Integrity', icon: Shield },
];

export function Sidebar({ activePage, onNavigate, isOpen, onClose }: SidebarProps) {
  const visibleItems = NAV_ITEMS;

  return (
    <aside
      className={`
        fixed inset-y-0 left-0 z-50 lg:static
        transform transition-transform duration-200 ease-in-out
        ${isOpen ? 'translate-x-0' : '-translate-x-full'} lg:translate-x-0
        flex flex-col w-60 bg-gray-900 text-white shrink-0
      `}
    >
      {/* Brand + close button on mobile */}
      <div className="flex items-center justify-between px-4 h-16 border-b border-gray-800">
        <div className="flex items-center gap-3">
          <UtensilsCrossed className="w-6 h-6 text-blue-400 shrink-0" />
          <span className="text-sm font-semibold tracking-tight truncate">
            EightySix
          </span>
        </div>
        <button
          onClick={onClose}
          className="lg:hidden p-1.5 rounded-md text-gray-400 hover:text-white hover:bg-gray-800 transition-colors cursor-pointer"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-3 px-2 space-y-1 overflow-y-auto">
        {visibleItems.map((item) => {
          const Icon = item.icon;
          const isActive = activePage === item.id;

          return (
            <button
              key={item.id}
              onClick={() => onNavigate(item.id)}
              className={`
                flex items-center gap-3 w-full rounded-lg px-3 py-2.5 text-sm font-medium
                transition-colors duration-150 cursor-pointer
                ${
                  isActive
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-400 hover:text-white hover:bg-gray-800'
                }
              `}
              title={item.label}
            >
              <Icon className="w-5 h-5 shrink-0" />
              <span className="truncate">{item.label}</span>
            </button>
          );
        })}
      </nav>

    </aside>
  );
}
