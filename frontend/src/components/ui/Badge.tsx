import { cn } from '../../lib/utils';

interface BadgeProps {
  children: React.ReactNode;
  variant?: 'default' | 'success' | 'warning' | 'danger' | 'info';
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export function Badge({
  children,
  variant = 'default',
  size = 'md',
  className
}: BadgeProps) {
  const variants = {
    default: 'bg-violet-500/20 text-violet-400 border-violet-500/30',
    success: 'bg-green-500/20 text-green-400 border-green-500/30',
    warning: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
    danger: 'bg-red-500/20 text-red-400 border-red-500/30',
    info: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
  };

  const sizes = {
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-3 py-1 text-sm',
    lg: 'px-4 py-1.5 text-base',
  };

  return (
    <span
      className={cn(
        'inline-flex items-center font-semibold rounded-lg border backdrop-blur-sm',
        variants[variant],
        sizes[size],
        className
      )}
    >
      {children}
    </span>
  );
}
