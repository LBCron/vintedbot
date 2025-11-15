import { motion } from 'framer-motion';
import { LucideIcon } from 'lucide-react';
import { GlassCard } from './GlassCard';
import { cn } from '../../lib/utils';

interface StatCardProps {
  icon: LucideIcon;
  label: string;
  value: string | number | React.ReactNode;
  trend?: {
    value: string;
    direction: 'up' | 'down';
  };
  gradient?: string;
  className?: string;
}

export function StatCard({
  icon: Icon,
  label,
  value,
  trend,
  gradient,
  className
}: StatCardProps) {
  return (
    <GlassCard hover className={cn("p-6", className)}>
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <div className={cn(
            "p-3 rounded-xl backdrop-blur-sm",
            gradient || "bg-violet-500/20 border border-violet-500/30"
          )}>
            <Icon className="w-6 h-6 text-violet-400" />
          </div>
          <div>
            <p className="text-sm text-slate-400 font-medium">{label}</p>
            <motion.div
              className="text-3xl font-bold text-white mt-1"
              initial={{ opacity: 0, scale: 0.5 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.5, delay: 0.1 }}
            >
              {value}
            </motion.div>
          </div>
        </div>
        {trend && (
          <div className={cn(
            "flex items-center space-x-1 px-3 py-1 rounded-lg",
            trend.direction === 'up'
              ? 'text-green-400 bg-green-500/10'
              : 'text-red-400 bg-red-500/10'
          )}>
            <span className="text-lg">{trend.direction === 'up' ? '↑' : '↓'}</span>
            <span className="text-sm font-semibold">{trend.value}</span>
          </div>
        )}
      </div>
    </GlassCard>
  );
}
