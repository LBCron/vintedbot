/**
 * Badge Component - Uses design system classes from index.css
 */
import { forwardRef, memo } from 'react';
import { motion, HTMLMotionProps } from 'framer-motion';

export interface BadgeProps extends HTMLMotionProps<"span"> {
  variant?: 'default' | 'primary' | 'success' | 'warning' | 'error';
  size?: 'sm' | 'md' | 'lg';
  dot?: boolean;
}

export const Badge = memo(forwardRef<HTMLSpanElement, BadgeProps>(
  ({
    variant = 'default',
    size = 'md',
    dot = false,
    children,
    className = '',
    ...props
  }, ref) => {

    // Use .badge utility classes from index.css
    const variantClasses = {
      default: 'badge',
      primary: 'badge badge-primary',
      success: 'badge badge-success',
      warning: 'badge badge-warning',
      error: 'badge badge-error',
    };

    const sizeStyles = {
      sm: { fontSize: 'var(--text-xs)', padding: 'var(--spacing-1) var(--spacing-2)' },
      md: { fontSize: 'var(--text-sm)', padding: 'var(--spacing-1) var(--spacing-2\\.5)' },
      lg: { fontSize: 'var(--text-base)', padding: 'var(--spacing-1\\.5) var(--spacing-3)' },
    };

    return (
      <motion.span
        ref={ref}
        className={`${variantClasses[variant]} ${className}`}
        style={sizeStyles[size]}
        initial={{ scale: 0.8, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ duration: 0.2 }}
        {...props}
      >
        {dot && (
          <span
            className="rounded-full"
            style={{
              width: '0.375rem',
              height: '0.375rem',
              backgroundColor: 'currentColor',
              opacity: 0.7,
            }}
          />
        )}
        {children}
      </motion.span>
    );
  }
));

Badge.displayName = 'Badge';
