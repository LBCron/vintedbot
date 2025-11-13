import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

interface DraftsTimelineChartProps {
  data?: Array<{
    date: string;
    drafts: number;
    published: number;
  }>;
}

export default function DraftsTimelineChart({ data }: DraftsTimelineChartProps) {
  // Sample data if none provided
  const chartData = data || [
    { date: 'Jan', drafts: 12, published: 8 },
    { date: 'Feb', drafts: 19, published: 13 },
    { date: 'Mar', drafts: 23, published: 18 },
    { date: 'Apr', drafts: 28, published: 21 },
    { date: 'May', drafts: 32, published: 25 },
    { date: 'Jun', drafts: 38, published: 30 },
  ];

  return (
    <div className="card">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
        📈 Drafts Timeline
      </h3>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis
            dataKey="date"
            stroke="#6b7280"
            style={{ fontSize: '12px' }}
          />
          <YAxis
            stroke="#6b7280"
            style={{ fontSize: '12px' }}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#fff',
              border: '1px solid #e5e7eb',
              borderRadius: '8px',
              fontSize: '14px'
            }}
          />
          <Legend
            wrapperStyle={{ fontSize: '14px' }}
          />
          <Line
            type="monotone"
            dataKey="drafts"
            stroke="#3b82f6"
            strokeWidth={2}
            name="Total Drafts"
            dot={{ fill: '#3b82f6', r: 4 }}
            activeDot={{ r: 6 }}
          />
          <Line
            type="monotone"
            dataKey="published"
            stroke="#10b981"
            strokeWidth={2}
            name="Published"
            dot={{ fill: '#10b981', r: 4 }}
            activeDot={{ r: 6 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
