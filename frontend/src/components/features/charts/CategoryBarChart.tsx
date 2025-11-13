import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

interface CategoryBarChartProps {
  data?: Array<{
    category: string;
    count: number;
  }>;
}

export default function CategoryBarChart({ data }: CategoryBarChartProps) {
  // Sample data if none provided
  const chartData = data || [
    { category: 'Vêtements', count: 45 },
    { category: 'Chaussures', count: 32 },
    { category: 'Accessoires', count: 28 },
    { category: 'Sacs', count: 21 },
    { category: 'Bijoux', count: 15 },
  ];

  return (
    <div className="card">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
        📊 Drafts by Category
      </h3>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis
            dataKey="category"
            stroke="#6b7280"
            style={{ fontSize: '12px' }}
            angle={-15}
            textAnchor="end"
            height={80}
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
          <Legend wrapperStyle={{ fontSize: '14px' }} />
          <Bar
            dataKey="count"
            fill="#3b82f6"
            name="Drafts"
            radius={[8, 8, 0, 0]}
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
