import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';
import { motion } from 'framer-motion';
import { PieChart as PieChartIcon, CheckCircle2 } from 'lucide-react';
import { useState } from 'react';

interface StatusPieChartProps {
  data?: Array<{
    name: string;
    value: number;
  }>;
}

const COLORS = [
  { main: '#3b82f6', gradient: ['#3b82f6', '#60a5fa'], name: 'Ready' },
  { main: '#10b981', gradient: ['#10b981', '#34d399'], name: 'Published' },
  { main: '#f59e0b', gradient: ['#f59e0b', '#fbbf24'], name: 'Pending' },
  { main: '#ef4444', gradient: ['#ef4444', '#f87171'], name: 'Failed' },
];

export default function StatusPieChart({ data }: StatusPieChartProps) {
  const [activeIndex, setActiveIndex] = useState<number | null>(null);

  // Sample data if none provided
  const chartData = data || [
    { name: 'Ready', value: 45 },
    { name: 'Published', value: 32 },
    { name: 'Pending', value: 18 },
    { name: 'Failed', value: 5 },
  ];

  const total = chartData.reduce((sum, item) => sum + item.value, 0);

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0];
      const percentage = ((data.value / total) * 100).toFixed(1);
      return (
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl shadow-xl p-4">
          <p className="font-semibold text-gray-900 dark:text-white mb-2 flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4" style={{ color: data.payload.fill }} />
            {data.name}
          </p>
          <div className="space-y-1">
            <p className="text-sm flex items-center justify-between gap-4">
              <span className="text-gray-600 dark:text-gray-400">Count:</span>
              <span className="font-bold text-gray-900 dark:text-white">{data.value}</span>
            </p>
            <p className="text-sm flex items-center justify-between gap-4">
              <span className="text-gray-600 dark:text-gray-400">Percentage:</span>
              <span className="font-bold" style={{ color: data.payload.fill }}>{percentage}%</span>
            </p>
          </div>
        </div>
      );
    }
    return null;
  };

  const renderCustomLabel = ({ cx, cy, midAngle, innerRadius, outerRadius, percent }: any) => {
    if (percent < 0.05) return null; // Don't show label if less than 5%

    const RADIAN = Math.PI / 180;
    const radius = innerRadius + (outerRadius - innerRadius) * 0.5;
    const x = cx + radius * Math.cos(-midAngle * RADIAN);
    const y = cy + radius * Math.sin(-midAngle * RADIAN);

    return (
      <text
        x={x}
        y={y}
        fill="white"
        textAnchor={x > cx ? 'start' : 'end'}
        dominantBaseline="central"
        className="font-bold text-sm"
        style={{ textShadow: '0 1px 3px rgba(0,0,0,0.3)' }}
      >
        {`${(percent * 100).toFixed(0)}%`}
      </text>
    );
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.2 }}
      className="card relative overflow-hidden"
    >
      {/* Gradient background decoration */}
      <div className="absolute bottom-0 right-0 w-64 h-64 bg-gradient-to-tl from-blue-100/30 to-green-100/30 dark:from-blue-900/10 dark:to-green-900/10 rounded-full blur-3xl -z-0" />

      <div className="relative z-10">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h3 className="text-xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
              <PieChartIcon className="w-6 h-6 text-green-600 dark:text-green-400" />
              Status Distribution
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
              {total} total items across {chartData.length} statuses
            </p>
          </div>
        </div>

        <div className="grid md:grid-cols-2 gap-6 items-center">
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <defs>
                {COLORS.map((color, index) => (
                  <linearGradient key={index} id={`statusGradient${index}`} x1="0" y1="0" x2="1" y2="1">
                    <stop offset="0%" stopColor={color.gradient[0]} />
                    <stop offset="100%" stopColor={color.gradient[1]} />
                  </linearGradient>
                ))}
              </defs>
              <Pie
                data={chartData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={renderCustomLabel}
                outerRadius={100}
                innerRadius={60}
                fill="#8884d8"
                dataKey="value"
                onMouseEnter={(_, index) => setActiveIndex(index)}
                onMouseLeave={() => setActiveIndex(null)}
                animationBegin={0}
                animationDuration={800}
              >
                {chartData.map((entry, index) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={`url(#statusGradient${index})`}
                    opacity={activeIndex === null || activeIndex === index ? 1 : 0.6}
                    style={{
                      filter: activeIndex === index ? 'drop-shadow(0 4px 6px rgba(0,0,0,0.1))' : 'none',
                      transition: 'all 0.3s ease'
                    }}
                  />
                ))}
              </Pie>
              <Tooltip content={<CustomTooltip />} />
            </PieChart>
          </ResponsiveContainer>

          {/* Custom Legend with Stats */}
          <div className="space-y-3">
            {chartData.map((item, index) => {
              const percentage = ((item.value / total) * 100).toFixed(1);
              const isActive = activeIndex === index;

              return (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.3 + index * 0.1 }}
                  onMouseEnter={() => setActiveIndex(index)}
                  onMouseLeave={() => setActiveIndex(null)}
                  className={`p-3 rounded-lg transition-all cursor-pointer ${
                    isActive ? 'bg-gray-50 dark:bg-gray-800/50 shadow-sm' : 'hover:bg-gray-50 dark:hover:bg-gray-800/30'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div
                        className="w-4 h-4 rounded-full shadow-sm"
                        style={{ background: `linear-gradient(135deg, ${COLORS[index].gradient[0]}, ${COLORS[index].gradient[1]})` }}
                      />
                      <span className="font-medium text-gray-900 dark:text-white">{item.name}</span>
                    </div>
                    <div className="text-right">
                      <div className="font-bold text-gray-900 dark:text-white">{item.value}</div>
                      <div className="text-xs text-gray-500 dark:text-gray-400">{percentage}%</div>
                    </div>
                  </div>
                  {/* Progress bar */}
                  <div className="mt-2 h-1.5 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${percentage}%` }}
                      transition={{ duration: 0.8, delay: 0.4 + index * 0.1 }}
                      className="h-full rounded-full"
                      style={{ background: `linear-gradient(90deg, ${COLORS[index].gradient[0]}, ${COLORS[index].gradient[1]})` }}
                    />
                  </div>
                </motion.div>
              );
            })}
          </div>
        </div>
      </div>
    </motion.div>
  );
}
