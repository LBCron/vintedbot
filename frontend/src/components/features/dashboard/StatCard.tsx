import { motion } from 'framer-motion';
import { LucideIcon, TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { LineChart, Line, ResponsiveContainer } from 'recharts';
import { Tooltip } from '../../common/Tooltip';

interface StatCardProps {
  title: string;
  value: string | number;
  change?: number;
  changeLabel?: string;
  icon: LucideIcon;
  iconColor: string;
  sparklineData?: number[];
  onClick?: () => void;
  info?: string;
}

export default function StatCard({
  title,
  value,
  change,
  changeLabel = 'vs last period',
  icon: Icon,
  iconColor,
  sparklineData,
  onClick,
  info,
}: StatCardProps) {
  const isPositive = change && change > 0;
  const isNegative = change && change < 0;
  const isNeutral = !change || change === 0;

  // Format sparkline data for recharts
  const chartData = sparklineData?.map((value, index) => ({ value, index })) || [];

  const TrendIcon = isPositive ? TrendingUp : isNegative ? TrendingDown : Minus;
  const trendColor = isPositive
    ? 'text-success-600 dark:text-success-400'
    : isNegative
    ? 'text-error-600 dark:text-error-400'
    : 'text-gray-500 dark:text-gray-400';

  return (
    <motion.div
      whileHover={{ y: -4, boxShadow: '0 20px 60px rgba(99, 102, 241, 0.15)' }}
      transition={{ duration: 0.2 }}
      onClick={onClick}
      className={`card hover:shadow-premium transition-all ${onClick ? 'cursor-pointer' : ''}`}
    >
      <div className="flex items-start justify-between mb-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
              {title}
            </p>
            {info && (
              <Tooltip content={info}>
                <div className="w-4 h-4 rounded-full bg-gray-100 dark:bg-gray-800 flex items-center justify-center cursor-help">
                  <span className="text-xs text-gray-500 dark:text-gray-400">?</span>
                </div>
              </Tooltip>
            )}
          </div>

          <p className="text-3xl font-bold text-gray-900 dark:text-white">
            {value}
          </p>
        </div>

        {/* Icon Circle */}
        <div className={`w-12 h-12 rounded-full flex items-center justify-center ${iconColor}`}>
          <Icon className="w-6 h-6" />
        </div>
      </div>

      <div className="flex items-center justify-between">
        {/* Change Badge */}
        {change !== undefined && (
          <div className="flex items-center gap-1.5">
            <div className={`flex items-center gap-0.5 px-2 py-1 rounded-full ${
              isPositive
                ? 'bg-success-100 dark:bg-success-900/20'
                : isNegative
                ? 'bg-error-100 dark:bg-error-900/20'
                : 'bg-gray-100 dark:bg-gray-800'
            }`}>
              <TrendIcon className={`w-3 h-3 ${trendColor}`} />
              <span className={`text-xs font-semibold ${trendColor}`}>
                {isPositive && '+'}
                {change}%
              </span>
            </div>

            <span className="text-xs text-gray-500 dark:text-gray-400">
              {changeLabel}
            </span>
          </div>
        )}

        {/* Mini Sparkline */}
        {sparklineData && sparklineData.length > 0 && (
          <div className="ml-auto w-24 h-8">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData}>
                <Line
                  type="monotone"
                  dataKey="value"
                  stroke={isPositive ? '#22c55e' : isNegative ? '#ef4444' : '#6366f1'}
                  strokeWidth={2}
                  dot={false}
                  animationDuration={1000}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>
    </motion.div>
  );
}
