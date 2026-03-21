import type { ReactNode } from 'react';

interface CardProps {
  title: string;
  subtitle?: string;
  icon?: ReactNode;
  status?: 'green' | 'yellow' | 'red' | null;
  children: ReactNode;
  className?: string;
}

const statusColors: Record<string, string> = {
  green: 'bg-emerald-500',
  yellow: 'bg-amber-500',
  red: 'bg-red-500',
};

export function Card({ title, subtitle, icon, status, children, className = '' }: CardProps) {
  return (
    <div
      className={`bg-white rounded-xl shadow-sm border border-gray-200 ${className}`}
    >
      <div className="flex items-start justify-between px-5 pt-5 pb-3">
        <div className="flex items-center gap-2.5 min-w-0">
          {icon && (
            <span className="text-gray-400 shrink-0">{icon}</span>
          )}
          <div className="min-w-0">
            <h3 className="text-sm font-semibold text-gray-900 truncate">{title}</h3>
            {subtitle && (
              <p className="text-xs text-gray-500 mt-0.5 truncate">{subtitle}</p>
            )}
          </div>
        </div>
        {status && (
          <span
            className={`w-2.5 h-2.5 rounded-full shrink-0 mt-1 ${statusColors[status] ?? 'bg-gray-400'}`}
            title={status}
          />
        )}
      </div>
      <div className="px-5 pb-5">{children}</div>
    </div>
  );
}
