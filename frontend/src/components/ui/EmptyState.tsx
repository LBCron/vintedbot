import { LucideIcon } from 'lucide-react';
import { GlassCard } from './GlassCard';
import { Button } from './Button';

interface EmptyStateProps {
  icon: LucideIcon;
  title: string;
  description: string;
  action?: {
    label: string;
    onClick: () => void;
    icon?: LucideIcon;
  };
  className?: string;
}

export function EmptyState({
  icon: Icon,
  title,
  description,
  action,
  className
}: EmptyStateProps) {
  return (
    <GlassCard className={`p-12 text-center ${className || ''}`}>
      <div className="mx-auto w-20 h-20 bg-gradient-to-br from-violet-500/20 to-purple-500/20 rounded-2xl flex items-center justify-center mb-6 border border-violet-500/30">
        <Icon className="w-10 h-10 text-violet-400" />
      </div>
      <h3 className="text-2xl font-bold text-white mb-3">{title}</h3>
      <p className="text-slate-400 text-lg mb-8 max-w-md mx-auto">{description}</p>
      {action && (
        <Button onClick={action.onClick} icon={action.icon}>
          {action.label}
        </Button>
      )}
    </GlassCard>
  );
}
