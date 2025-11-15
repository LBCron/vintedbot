import { motion, HTMLMotionProps } from 'framer-motion';
import { LucideIcon } from 'lucide-react';
import { cn } from '../../lib/utils';

interface ButtonProps extends Omit<HTMLMotionProps<"button">, "children"> {
  children: React.ReactNode;
  icon?: LucideIcon;
  variant?: 'primary' | 'outline' | 'ghost' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  className?: string;
  disabled?: boolean;
  loading?: boolean;
}

export function Button({
  children,
  icon: Icon,
  variant = 'primary',
  size = 'md',
  className,
  disabled,
  loading,
  ...props
}: ButtonProps) {
  const baseClasses = "relative overflow-hidden rounded-xl font-semibold transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed";

  const variants = {
    primary: "bg-gradient-to-r from-violet-500 to-purple-600 text-white hover:from-violet-600 hover:to-purple-700 shadow-lg shadow-violet-500/30 hover:shadow-violet-500/50",
    outline: "border-2 border-violet-500/50 text-violet-400 hover:bg-violet-500/10 hover:border-violet-400 backdrop-blur-sm",
    ghost: "text-slate-400 hover:text-white hover:bg-white/5",
    danger: "bg-gradient-to-r from-red-500 to-pink-600 text-white hover:from-red-600 hover:to-pink-700 shadow-lg shadow-red-500/30",
  };

  const sizes = {
    sm: "px-4 py-2 text-sm",
    md: "px-6 py-3 text-base",
    lg: "px-8 py-4 text-lg"
  };

  return (
    <motion.button
      className={cn(baseClasses, variants[variant], sizes[size], className)}
      disabled={disabled || loading}
      whileHover={{ scale: disabled ? 1 : 1.05 }}
      whileTap={{ scale: disabled ? 1 : 0.95 }}
      {...props}
    >
      <span className="flex items-center justify-center space-x-2">
        {loading && (
          <svg className="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
        )}
        {Icon && !loading && <Icon className="w-5 h-5" />}
        <span>{children}</span>
      </span>
    </motion.button>
  );
}
