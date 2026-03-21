import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

interface MetricProps {
  label: string;
  value: string | number;
  subtext?: string;
  trend?: 'up' | 'down' | 'flat';
  variant?: 'default' | 'success' | 'warning' | 'danger';
}

const variantColor: Record<string, string> = {
  default: 'text-gray-900',
  success: 'text-emerald-600',
  warning: 'text-amber-600',
  danger: 'text-red-600',
};

const trendIcons = {
  up: TrendingUp,
  down: TrendingDown,
  flat: Minus,
};

const trendColor: Record<string, string> = {
  up: 'text-emerald-500',
  down: 'text-red-500',
  flat: 'text-gray-400',
};

export function Metric({ label, value, subtext, trend, variant = 'default' }: MetricProps) {
  const TrendIcon = trend ? trendIcons[trend] : null;

  return (
    <div className="space-y-1">
      <p className="text-xs font-medium uppercase tracking-wide text-gray-500">{label}</p>
      <div className="flex items-center gap-2">
        <span className={`text-2xl font-semibold ${variantColor[variant]}`}>{value}</span>
        {TrendIcon && (
          <TrendIcon className={`w-4 h-4 ${trendColor[trend!]}`} />
        )}
      </div>
      {subtext && (
        <p className="text-xs text-gray-500">{subtext}</p>
      )}
    </div>
  );
}
