/**
 * Button Component
 * Uses design system CSS variables and utility classes from index.css
 *
 * Features:
 * - Multiple variants (primary, secondary, outline, ghost, success, error)
 * - Three sizes (sm, md, lg) using CSS variable heights
 * - Loading state with spinner
 * - Icon support (left and right)
 * - Smooth animations via Framer Motion
 * - Full accessibility support
 */

import { motion, HTMLMotionProps } from 'framer-motion';
import { forwardRef } from 'react';

export interface ButtonProps extends Omit<HTMLMotionProps<"button">, 'size'> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'outline' | 'success' | 'error';
  size?: 'sm' | 'md' | 'lg';
  isLoading?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({
    variant = 'primary',
    size = 'md',
    isLoading = false,
    leftIcon,
    rightIcon,
    children,
    className = '',
    disabled,
    ...props
  }, ref) => {

    // Use CSS utility classes from index.css instead of inline Tailwind
    // This leverages the design system's CSS variables
    const variantClasses = {
      primary: 'btn-primary',
      secondary: 'btn-secondary',
      outline: 'btn-outline',
      ghost: 'btn-ghost',
      success: 'btn-success',
      error: 'btn-error',
    };

    const sizeClasses = {
      sm: 'btn-sm',
      md: '', // Default size, no additional class needed
      lg: 'btn-lg',
    };

    return (
      <motion.button
        ref={ref}
        className={`btn ${variantClasses[variant]} ${sizeClasses[size]} ${className}`}
        disabled={disabled || isLoading}
        whileHover={{ scale: disabled || isLoading ? 1 : 1.02 }}
        whileTap={{ scale: disabled || isLoading ? 1 : 0.98 }}
        transition={{ duration: 0.15 }}
        {...props}
      >
        {isLoading && (
          <svg
            className="animate-spin"
            style={{ width: '1rem', height: '1rem' }}
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            />
          </svg>
        )}
        {!isLoading && leftIcon}
        {children}
        {rightIcon}
      </motion.button>
    );
  }
);

Button.displayName = 'Button';
