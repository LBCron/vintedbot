import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Area, AreaChart } from 'recharts';
import { motion } from 'framer-motion';
import { TrendingUp, Calendar } from 'lucide-react';

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

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl shadow-xl p-4">
          <p className="font-semibold text-gray-900 dark:text-white mb-2 flex items-center gap-2">
            <Calendar className="w-4 h-4 text-primary-500" />
            {label}
          </p>
          {payload.map((entry: any, index: number) => (
            <p key={index} className="text-sm flex items-center gap-2 mb-1" style={{ color: entry.color }}>
              <span className="w-3 h-3 rounded-full" style={{ backgroundColor: entry.color }} />
              <span className="font-medium">{entry.name}:</span>
              <span className="font-bold">{entry.value}</span>
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="card relative overflow-hidden"
    >
      {/* Gradient background decoration */}
      <div className="absolute top-0 right-0 w-64 h-64 bg-gradient-to-br from-primary-100/30 to-purple-100/30 dark:from-primary-900/10 dark:to-purple-900/10 rounded-full blur-3xl -z-0" />

      <div className="relative z-10">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h3 className="text-xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
              <TrendingUp className="w-6 h-6 text-primary-600 dark:text-primary-400" />
              Drafts Timeline
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
              Track your drafts creation and publication over time
            </p>
          </div>
        </div>

        <ResponsiveContainer width="100%" height={350}>
          <AreaChart data={chartData}>
            <defs>
              <linearGradient id="colorDrafts" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3}/>
                <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
              </linearGradient>
              <linearGradient id="colorPublished" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#10b981" stopOpacity={0.3}/>
                <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" className="dark:stroke-gray-700" opacity={0.3} />
            <XAxis
              dataKey="date"
              stroke="#6b7280"
              style={{ fontSize: '13px', fontWeight: 500 }}
              tick={{ fill: '#6b7280' }}
            />
            <YAxis
              stroke="#6b7280"
              style={{ fontSize: '13px', fontWeight: 500 }}
              tick={{ fill: '#6b7280' }}
            />
            <Tooltip content={<CustomTooltip />} cursor={{ stroke: '#9ca3af', strokeWidth: 1 }} />
            <Legend
              wrapperStyle={{ fontSize: '14px', fontWeight: 500, paddingTop: '20px' }}
              iconType="circle"
            />
            <Area
              type="monotone"
              dataKey="drafts"
              stroke="#3b82f6"
              strokeWidth={3}
              fill="url(#colorDrafts)"
              name="Total Drafts"
              dot={{ fill: '#3b82f6', r: 5, strokeWidth: 2, stroke: '#fff' }}
              activeDot={{ r: 7, strokeWidth: 2 }}
            />
            <Area
              type="monotone"
              dataKey="published"
              stroke="#10b981"
              strokeWidth={3}
              fill="url(#colorPublished)"
              name="Published"
              dot={{ fill: '#10b981', r: 5, strokeWidth: 2, stroke: '#fff' }}
              activeDot={{ r: 7, strokeWidth: 2 }}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </motion.div>
  );
}
