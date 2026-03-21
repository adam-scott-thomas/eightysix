import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';

interface MenuChartProps {
  items: Array<{ item_name: string; units_sold: number; margin_band: string | null }>;
}

const MARGIN_COLORS: Record<string, string> = {
  high: '#22c55e',
  good: '#22c55e',
  medium: '#f59e0b',
  moderate: '#f59e0b',
  low: '#ef4444',
  poor: '#ef4444',
  unknown: '#9ca3af',
};

export function MenuChart({ items }: MenuChartProps) {
  return (
    <ResponsiveContainer width="100%" height={160}>
      <BarChart
        data={items}
        layout="vertical"
        margin={{ left: 80, right: 10, top: 5, bottom: 5 }}
      >
        <XAxis type="number" fontSize={11} />
        <YAxis type="category" dataKey="item_name" fontSize={11} width={75} />
        <Tooltip />
        <Bar dataKey="units_sold" radius={[0, 4, 4, 0]}>
          {items.map((item, i) => (
            <Cell
              key={i}
              fill={MARGIN_COLORS[(item.margin_band || 'unknown').toLowerCase()] || MARGIN_COLORS.unknown}
            />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
