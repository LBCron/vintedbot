import { forwardRef, InputHTMLAttributes } from 'react';
import { cn } from '../../lib/utils';
import { LucideIcon } from 'lucide-react';

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  icon?: LucideIcon;
  containerClassName?: string;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className, label, error, icon: Icon, containerClassName, ...props }, ref) => {
    return (
      <div className={cn("space-y-2", containerClassName)}>
        {label && (
          <label className="text-sm font-medium text-slate-300">
            {label}
          </label>
        )}
        <div className="relative">
          {Icon && (
            <Icon className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
          )}
          <input
            className={cn(
              "w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white",
              "placeholder:text-slate-500 backdrop-blur-sm",
              "focus:outline-none focus:border-violet-500/50 focus:bg-white/10",
              "transition-all duration-300",
              "disabled:opacity-50 disabled:cursor-not-allowed",
              Icon && "pl-11",
              error && "border-red-500/50 focus:border-red-500",
              className
            )}
            ref={ref}
            {...props}
          />
        </div>
        {error && (
          <p className="text-sm text-red-400">{error}</p>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';
