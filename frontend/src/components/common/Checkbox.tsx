import { forwardRef } from 'react';
import { motion } from 'framer-motion';
import { Check, Minus } from 'lucide-react';

export interface CheckboxProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'type'> {
  label?: string;
  description?: string;
  indeterminate?: boolean;
}

export const Checkbox = forwardRef<HTMLInputElement, CheckboxProps>(
  ({ label, description, indeterminate = false, className = '', ...props }, ref) => {
    return (
      <label className={`flex items-start gap-3 cursor-pointer group ${props.disabled ? 'opacity-50 cursor-not-allowed' : ''} ${className}`}>
        <div className="relative flex items-center justify-center">
          {/* Hidden Input */}
          <input
            ref={ref}
            type="checkbox"
            className="sr-only"
            {...props}
          />

          {/* Custom Checkbox */}
          <motion.div
            className={`
              w-5 h-5 rounded border-2 flex items-center justify-center transition-all duration-200
              ${props.checked || indeterminate
                ? 'bg-primary-600 border-primary-600'
                : 'bg-white dark:bg-neutral-900 border-neutral-300 dark:border-neutral-700 group-hover:border-primary-400'
              }
            `}
            whileHover={{ scale: props.disabled ? 1 : 1.1 }}
            whileTap={{ scale: props.disabled ? 1 : 0.95 }}
          >
            {indeterminate ? (
              <motion.div
                initial={{ scale: 0, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                exit={{ scale: 0, opacity: 0 }}
              >
                <Minus className="w-3 h-3 text-white" strokeWidth={3} />
              </motion.div>
            ) : props.checked ? (
              <motion.div
                initial={{ scale: 0, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                exit={{ scale: 0, opacity: 0 }}
              >
                <Check className="w-3 h-3 text-white" strokeWidth={3} />
              </motion.div>
            ) : null}
          </motion.div>
        </div>

        {/* Label and Description */}
        {(label || description) && (
          <div className="flex-1 pt-0.5">
            {label && (
              <span className="text-sm font-medium text-neutral-900 dark:text-neutral-100">
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
      </label>
    );
  }
);

Checkbox.displayName = 'Checkbox';
