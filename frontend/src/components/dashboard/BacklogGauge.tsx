import { PieChart, Pie, Cell } from 'recharts';

interface BacklogGaugeProps {
  value: number; // 0 to 1
}

export function BacklogGauge({ value }: BacklogGaugeProps) {
  const clampedValue = Math.min(1, Math.max(0, value));
  const data = [
    { value: clampedValue },
    { value: 1 - clampedValue },
  ];
  const color = clampedValue > 0.8 ? '#ef4444' : clampedValue > 0.6 ? '#f59e0b' : '#22c55e';

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
        {(clampedValue * 100).toFixed(0)}%
      </span>
      <span className="text-xs text-gray-500">Backlog Risk</span>
    </div>
  );
}
