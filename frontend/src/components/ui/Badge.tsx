import { cn } from '@/lib/utils';

interface BadgeProps {
  children: React.ReactNode;
  variant?: 'default' | 'success' | 'error' | 'warning' | 'info';
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export default function Badge({
  children,
  variant = 'default',
  size = 'md',
  className
}: BadgeProps) {
  const variants = {
    default: 'bg-gray-100 text-gray-700',
    success: 'bg-success-100 text-success-700',
    error: 'bg-error-100 text-error-700',
    warning: 'bg-warning-100 text-warning-700',
    info: 'bg-blue-100 text-blue-700'
  };

  const sizes = {
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-2.5 py-1 text-sm',
    lg: 'px-3 py-1.5 text-base'
  };

  return (
    <span className={cn(
      'inline-flex items-center gap-1 rounded-full font-semibold',
      variants[variant],
      sizes[size],
      className
    )}>
      {children}
    </span>
  );
}
