import { memo, useCallback, useMemo } from 'react';
import { motion } from 'framer-motion';
import CountUp from 'react-countup';
import { TrendingUp, TrendingDown, LucideIcon } from 'lucide-react';

interface StatsCardProps {
  title: string;
  value: string | number;
  change?: number;
  icon?: React.ReactNode | LucideIcon;
  subtitle?: string;
  format?: 'number' | 'currency' | 'percent';
  trend?: number;
}

const StatsCard = memo<StatsCardProps>(({ title, value, change, icon, subtitle, format = 'number', trend }) => {
  const isPositive = useMemo(() =>
    (change !== undefined && change > 0) || (trend !== undefined && trend > 0),
    [change, trend]
  );

  const isNegative = useMemo(() =>
    (change !== undefined && change < 0) || (trend !== undefined && trend < 0),
    [change, trend]
  );

  const displayChange = useMemo(() =>
    change !== undefined ? change : trend,
    [change, trend]
  );

  const formatValue = useCallback((val: number): string => {
    if (format === 'currency') return `${val}€`;
    if (format === 'percent') return `${val}%`;
    return val.toLocaleString();
  }, [format]);

  const numericValue = useMemo(() =>
    typeof value === 'number' ? value : parseFloat(value.toString()) || 0,
    [value]
  );

  const displayValue = useMemo(() =>
    typeof value === 'string' && isNaN(parseFloat(value)) ? value : null,
    [value]
  );

  // Handle icon rendering - check if it's a component or already a JSX element
  const renderIcon = useCallback(() => {
    if (!icon) return null;

    // If icon is already a React element (JSX), render it directly
    if (typeof icon === 'object' && 'type' in icon) {
      return icon;
    }

    // If icon is a component function, instantiate it
    if (typeof icon === 'function') {
      const IconComponent = icon as LucideIcon;
      return <IconComponent className="w-6 h-6 text-primary-600 dark:text-primary-400" />;
    }

    return null;
  }, [icon]);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ scale: 1.02, boxShadow: '0 10px 30px rgba(0,0,0,0.1)' }}
      transition={{ duration: 0.2 }}
      className="card hover:shadow-lg transition-all"
    >
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <p className="text-sm font-medium text-gray-600 dark:text-gray-400">{title}</p>
          <p className="text-3xl font-bold text-gray-900 dark:text-white mt-1">
            {displayValue ? (
              displayValue
            ) : (
              <CountUp
                end={numericValue}
                duration={2}
                separator=","
                formattingFn={formatValue}
                preserveValue
              />
            )}
          </p>

          {subtitle && (
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">{subtitle}</p>
          )}

          {displayChange !== undefined && (
            <div className={`flex items-center gap-1 mt-2 ${isPositive ? 'text-green-600' : isNegative ? 'text-red-600' : 'text-gray-600'}`}>
              {isPositive && <TrendingUp className="w-4 h-4" />}
              {isNegative && <TrendingDown className="w-4 h-4" />}
              <span className="text-sm font-medium">
                {isPositive && '+'}{displayChange}%
                {trend !== undefined ? ' ce mois' : ''}
              </span>
            </div>
          )}
        </div>

        {icon && (
          <div className="p-3 bg-primary-50 dark:bg-primary-900/20 rounded-lg">
            {renderIcon()}
          </div>
        )}
      </div>
    </motion.div>
  );
});

StatsCard.displayName = 'StatsCard';

export default StatsCard;
