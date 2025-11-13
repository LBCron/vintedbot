import { ResponsiveContainer, ScatterChart, Scatter, XAxis, YAxis, ZAxis, Tooltip, Cell } from 'recharts';
import type { PerformanceHeatmap } from '../types';

interface HeatmapChartProps {
  data: PerformanceHeatmap[];
}

const DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
const HOURS = Array.from({ length: 24 }, (_, i) => i);

export default function HeatmapChart({ data }: HeatmapChartProps) {
  const transformedData = data.map((item) => ({
    day: item.day_of_week,
    hour: item.hour,
    value: item.views + item.likes + item.messages,
  }));

  const maxValue = Math.max(...transformedData.map((d) => d.value));

  const getColor = (value: number) => {
    const intensity = value / maxValue;
    if (intensity > 0.7) return '#0ea5e9';
    if (intensity > 0.5) return '#38bdf8';
    if (intensity > 0.3) return '#7dd3fc';
    if (intensity > 0.1) return '#bae6fd';
    return '#e0f2fe';
  };

  return (
    <div className="w-full h-96">
      <ResponsiveContainer width="100%" height="100%">
        <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
          <XAxis
            type="number"
            dataKey="hour"
            name="Hour"
            domain={[0, 23]}
            ticks={HOURS}
            tickFormatter={(hour) => `${hour}h`}
          />
          <YAxis
            type="number"
            dataKey="day"
            name="Day"
            domain={[0, 6]}
            ticks={[0, 1, 2, 3, 4, 5, 6]}
            tickFormatter={(day) => DAYS[day]}
          />
          <ZAxis type="number" dataKey="value" range={[50, 400]} />
          <Tooltip
            cursor={{ strokeDasharray: '3 3' }}
            content={({ payload }) => {
              if (!payload || !payload[0]) return null;
              const data = payload[0].payload;
              return (
                <div className="bg-white p-3 rounded-lg shadow-lg border border-gray-200">
                  <p className="font-semibold">
                    {DAYS[data.day]} at {data.hour}:00
                  </p>
                  <p className="text-sm text-gray-600">
                    Activity: {data.value}
                  </p>
                </div>
              );
            }}
          />
          <Scatter data={transformedData}>
            {transformedData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={getColor(entry.value)} />
            ))}
          </Scatter>
        </ScatterChart>
      </ResponsiveContainer>
    </div>
  );
}
