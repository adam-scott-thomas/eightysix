import { PieChart, Pie, Cell } from 'recharts';

interface LaborGaugeProps {
  value: number; // 0 to ~0.5
}

export function LaborGauge({ value }: LaborGaugeProps) {
  // Normalize to 0-1 scale for the gauge (0.5 = 100%)
  const normalized = Math.min(1, Math.max(0, value / 0.5));
  const data = [
    { value: normalized },
    { value: 1 - normalized },
  ];
  const color = value > 0.35 ? '#ef4444' : value > 0.3 ? '#f59e0b' : '#22c55e';

  return (
    <div className="flex flex-col items-center">
      <PieChart width={120} height={70}>
        <Pie
          data={data}
          cx={60}
          cy={60}
          startAngle={180}
          endAngle={0}
          innerRadius={35}
          outerRadius={55}
          dataKey="value"
          stroke="none"
        >
          <Cell fill={color} />
          <Cell fill="#e5e7eb" />
        </Pie>
      </PieChart>
      <span className="text-lg font-semibold" style={{ color }}>
        {(value * 100).toFixed(1)}%
      </span>
      <span className="text-xs text-gray-500">Labor Cost Ratio</span>
    </div>
  );
}
