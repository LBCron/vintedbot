import { forwardRef } from 'react';
import { motion } from 'framer-motion';

export interface ToggleProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'type' | 'size'> {
  label?: string;
  description?: string;
  size?: 'sm' | 'md' | 'lg';
}

export const Toggle = forwardRef<HTMLInputElement, ToggleProps>(
  ({ label, description, size = 'md', className = '', ...props }, ref) => {
    const sizes = {
      sm: { track: 'w-9 h-5', thumb: 'w-3 h-3', translate: 'translate-x-4' },
      md: { track: 'w-11 h-6', thumb: 'w-4 h-4', translate: 'translate-x-5' },
      lg: { track: 'w-14 h-7', thumb: 'w-5 h-5', translate: 'translate-x-7' },
    };

    const currentSize = sizes[size];

    return (
      <label className={`flex items-start gap-3 cursor-pointer group ${props.disabled ? 'opacity-50 cursor-not-allowed' : ''} ${className}`}>
        {/* Label and Description */}
        {(label || description) && (
          <div className="flex-1">
            {label && (
              <span className="text-sm font-medium text-neutral-900 dark:text-neutral-100 block">
                {label}
              </span>
            )}
            {description && (
              <p className="text-xs text-neutral-600 dark:text-neutral-400 mt-0.5">
                {description}
              </p>
            )}
          </div>
        )}

        <div className="relative flex items-center">
          {/* Hidden Input */}
          <input
            ref={ref}
            type="checkbox"
            className="sr-only"
            {...props}
          />

          {/* Track */}
          <motion.div
            className={`
              ${currentSize.track} rounded-full flex items-center p-1 transition-colors duration-200
              ${props.checked
                ? 'bg-primary-600'
                : 'bg-neutral-300 dark:bg-neutral-700'
              }
            `}
            whileHover={{ scale: props.disabled ? 1 : 1.05 }}
          >
            {/* Thumb */}
            <motion.div
              className={`${currentSize.thumb} rounded-full bg-white shadow-md`}
              layout
              transition={{
                type: "spring",
                stiffness: 700,
                damping: 30
              }}
              animate={{
                x: props.checked ? currentSize.translate : '0px'
              }}
            />
          </motion.div>
        </div>
      </label>
    );
  }
);

Toggle.displayName = 'Toggle';
