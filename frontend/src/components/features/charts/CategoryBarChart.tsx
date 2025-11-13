import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell } from 'recharts';
import { motion } from 'framer-motion';
import { Package, TrendingUp } from 'lucide-react';

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

  // Gradient colors for bars
  const colors = [
    '#3b82f6', // blue
    '#8b5cf6', // purple
    '#ec4899', // pink
    '#f59e0b', // amber
    '#10b981', // green
  ];

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl shadow-xl p-4">
          <p className="font-semibold text-gray-900 dark:text-white mb-2 flex items-center gap-2">
            <Package className="w-4 h-4 text-primary-500" />
            {label}
          </p>
          <p className="text-sm flex items-center gap-2">
            <span className="font-medium text-gray-600 dark:text-gray-400">Drafts:</span>
            <span className="font-bold text-primary-600 dark:text-primary-400">{payload[0].value}</span>
          </p>
        </div>
      );
    }
    return null;
  };

  const totalDrafts = chartData.reduce((sum, item) => sum + item.count, 0);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.1 }}
      className="card relative overflow-hidden"
    >
      {/* Gradient background decoration */}
      <div className="absolute top-0 left-0 w-64 h-64 bg-gradient-to-br from-purple-100/30 to-pink-100/30 dark:from-purple-900/10 dark:to-pink-900/10 rounded-full blur-3xl -z-0" />

      <div className="relative z-10">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h3 className="text-xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
              <Package className="w-6 h-6 text-purple-600 dark:text-purple-400" />
              Drafts by Category
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
              {totalDrafts} total drafts across {chartData.length} categories
            </p>
          </div>
        </div>

        <ResponsiveContainer width="100%" height={350}>
          <BarChart data={chartData}>
            <defs>
              {colors.map((color, index) => (
                <linearGradient key={index} id={`gradient${index}`} x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor={color} stopOpacity={0.9}/>
                  <stop offset="100%" stopColor={color} stopOpacity={0.6}/>
                </linearGradient>
              ))}
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" className="dark:stroke-gray-700" opacity={0.3} />
            <XAxis
              dataKey="category"
              stroke="#6b7280"
              style={{ fontSize: '13px', fontWeight: 500 }}
              angle={-15}
              textAnchor="end"
              height={80}
              tick={{ fill: '#6b7280' }}
            />
            <YAxis
              stroke="#6b7280"
              style={{ fontSize: '13px', fontWeight: 500 }}
              tick={{ fill: '#6b7280' }}
            />
            <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(0, 0, 0, 0.05)' }} />
            <Bar
              dataKey="count"
              name="Drafts"
              radius={[10, 10, 0, 0]}
              maxBarSize={60}
            >
              {chartData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={`url(#gradient${index % colors.length})`} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </motion.div>
  );
}
