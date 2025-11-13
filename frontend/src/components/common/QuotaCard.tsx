import { memo, useMemo } from 'react';
import { motion } from 'framer-motion';

interface QuotaCardProps {
  label: string;
  used: number;
  limit: number;
  unit?: string;
  icon?: React.ReactNode;
}

const QuotaCard = memo<QuotaCardProps>(({ label, used, limit, unit = '', icon }) => {
  const percentage = useMemo(() => (used / limit) * 100, [used, limit]);
  const isWarning = percentage >= 80;
  const isDanger = percentage >= 95;

  return (
    <motion.div
      whileHover={{ scale: 1.02, y: -4 }}
      transition={{ duration: 0.2 }}
      className="card"
    >
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          {icon}
          <h3 className="font-medium text-gray-700 dark:text-gray-300">{label}</h3>
        </div>
        <span className="text-sm text-gray-500 dark:text-gray-400">
          {used}/{limit} {unit}
        </span>
      </div>

      <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2 overflow-hidden">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${Math.min(percentage, 100)}%` }}
          transition={{ duration: 1, ease: "easeOut" }}
          className={`h-2 rounded-full ${
            isDanger
              ? 'bg-red-500'
              : isWarning
              ? 'bg-yellow-500'
              : 'bg-primary-500'
          }`}
        />
      </div>
      
      <p className="mt-2 text-xs text-gray-600 dark:text-gray-400">
        {Math.round(percentage)}% used
      </p>
    </motion.div>
  );
});

QuotaCard.displayName = 'QuotaCard';

export default QuotaCard;
