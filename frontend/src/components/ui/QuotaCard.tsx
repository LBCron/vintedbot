import { motion } from 'framer-motion';
import { LucideIcon } from 'lucide-react';
import { GlassCard } from './GlassCard';
import { cn } from '../../lib/utils';

interface QuotaCardProps {
  icon: LucideIcon;
  label: string;
  used: number;
  total: number;
  unit?: string;
  color?: 'violet' | 'blue' | 'green' | 'orange' | 'red';
}

const colorMap = {
  violet: {
    bg: 'bg-violet-500/20',
    border: 'border-violet-500/30',
    text: 'text-violet-400',
    ring: 'stroke-violet-500',
    track: 'stroke-violet-500/20',
  },
  blue: {
    bg: 'bg-blue-500/20',
    border: 'border-blue-500/30',
    text: 'text-blue-400',
    ring: 'stroke-blue-500',
    track: 'stroke-blue-500/20',
  },
  green: {
    bg: 'bg-green-500/20',
    border: 'border-green-500/30',
    text: 'text-green-400',
    ring: 'stroke-green-500',
    track: 'stroke-green-500/20',
  },
  orange: {
    bg: 'bg-orange-500/20',
    border: 'border-orange-500/30',
    text: 'text-orange-400',
    ring: 'stroke-orange-500',
    track: 'stroke-orange-500/20',
  },
  red: {
    bg: 'bg-red-500/20',
    border: 'border-red-500/30',
    text: 'text-red-400',
    ring: 'stroke-red-500',
    track: 'stroke-red-500/20',
  },
};

export function QuotaCard({
  icon: Icon,
  label,
  used,
  total,
  unit = '',
  color = 'violet'
}: QuotaCardProps) {
  const percentage = (used / total) * 100;
  const circumference = 2 * Math.PI * 36; // radius = 36
  const strokeDashoffset = circumference - (percentage / 100) * circumference;
  const colors = colorMap[color];

  return (
    <GlassCard hover className="p-6">
      <div className="flex items-center justify-between mb-4">
        <div className={cn("p-2 rounded-lg", colors.bg, colors.border, "border")}>
          <Icon className={cn("w-5 h-5", colors.text)} />
        </div>
        <div className="text-right">
          <p className="text-sm text-slate-400">{label}</p>
          <p className={cn("text-lg font-bold", colors.text)}>
            {used}/{total} {unit}
          </p>
        </div>
      </div>

      {/* Circular Progress */}
      <div className="flex justify-center">
        <div className="relative w-32 h-32">
          <svg className="transform -rotate-90 w-32 h-32">
            {/* Background circle */}
            <circle
              cx="64"
              cy="64"
              r="36"
              className={colors.track}
              strokeWidth="8"
              fill="none"
            />
            {/* Progress circle */}
            <motion.circle
              cx="64"
              cy="64"
              r="36"
              className={colors.ring}
              strokeWidth="8"
              fill="none"
              strokeLinecap="round"
              initial={{ strokeDashoffset: circumference }}
              animate={{ strokeDashoffset }}
              transition={{ duration: 1, ease: "easeOut" }}
              style={{
                strokeDasharray: circumference,
              }}
            />
          </svg>
          {/* Percentage text */}
          <div className="absolute inset-0 flex items-center justify-center">
            <motion.span
              className={cn("text-2xl font-bold", colors.text)}
              initial={{ opacity: 0, scale: 0 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.5, delay: 0.3 }}
            >
              {Math.round(percentage)}%
            </motion.span>
          </div>
        </div>
      </div>
    </GlassCard>
  );
}
