/**
 * Card Component
 * Uses design system CSS variables and utility classes from index.css
 *
 * Features:
 * - Multiple variants (elevated with shadow, outlined, filled)
 * - Flexible padding options using CSS variables
 * - Optional hover effect with animation
 * - Composable with subcomponents (Header, Title, Description, Content, Footer)
 * - Full dark mode support
 */

import { motion, HTMLMotionProps } from 'framer-motion';
import { forwardRef } from 'react';

export interface CardProps extends HTMLMotionProps<"div"> {
  variant?: 'elevated' | 'outlined' | 'filled';
  padding?: 'none' | 'sm' | 'md' | 'lg';
  hover?: boolean;
}

export const Card = forwardRef<HTMLDivElement, CardProps>(
  ({
    variant = 'elevated',
    padding = 'md',
    hover = false,
    children,
    className = '',
    ...props
  }, ref) => {

    // Use .card utility class from index.css which already handles:
    // - Background color (var(--bg-primary))
    // - Border (var(--border-primary))
    // - Border radius (var(--card-radius))
    // - Base shadow (var(--shadow-sm))
    // - Transition (var(--transition-base))

    const variantClasses = {
      elevated: hover ? 'card-hover' : 'card',
      outlined: 'card border-2',
      filled: 'card',
    };

    const variantStyles = {
      elevated: {},
      outlined: {},
      filled: { backgroundColor: 'var(--bg-tertiary)' },
    };

    // Map padding sizes to CSS spacing variables
    const paddingStyles = {
      none: { padding: 0 },
      sm: { padding: 'var(--spacing-4)' },
      md: { padding: 'var(--card-padding)' }, // Default from design system
      lg: { padding: 'var(--spacing-8)' },
    };

    const motionProps = hover ? {
      whileHover: { y: -4 },
      transition: { duration: 0.2, ease: [0.4, 0, 0.2, 1] }
    } : {};

    return (
      <motion.div
        ref={ref}
        className={`${variantClasses[variant]} ${className}`}
        style={{ ...variantStyles[variant], ...paddingStyles[padding] }}
        {...motionProps}
        {...props}
      >
        {children}
      </motion.div>
    );
  }
);

Card.displayName = 'Card';

export const CardHeader = forwardRef<HTMLDivElement, HTMLMotionProps<"div">>(
  ({ children, className = '', ...props }, ref) => (
    <div ref={ref} className={`mb-4 ${className}`} {...props}>
      {children}
    </div>
  )
);

CardHeader.displayName = 'CardHeader';

export const CardTitle = forwardRef<HTMLHeadingElement, React.HTMLAttributes<HTMLHeadingElement>>(
  ({ children, className = '', ...props }, ref) => (
    <h3 ref={ref} className={`text-xl font-semibold text-neutral-900 dark:text-neutral-100 ${className}`} {...props}>
      {children}
    </h3>
  )
);

CardTitle.displayName = 'CardTitle';

export const CardDescription = forwardRef<HTMLParagraphElement, React.HTMLAttributes<HTMLParagraphElement>>(
  ({ children, className = '', ...props }, ref) => (
    <p ref={ref} className={`text-sm text-neutral-600 dark:text-neutral-400 mt-1 ${className}`} {...props}>
      {children}
    </p>
  )
);

CardDescription.displayName = 'CardDescription';

export const CardContent = forwardRef<HTMLDivElement, HTMLMotionProps<"div">>(
  ({ children, className = '', ...props }, ref) => (
    <div ref={ref} className={className} {...props}>
      {children}
    </div>
  )
);

CardContent.displayName = 'CardContent';

export const CardFooter = forwardRef<HTMLDivElement, HTMLMotionProps<"div">>(
  ({ children, className = '', ...props }, ref) => (
    <div ref={ref} className={`mt-4 pt-4 border-t border-neutral-200 dark:border-neutral-800 ${className}`} {...props}>
      {children}
    </div>
  )
);

CardFooter.displayName = 'CardFooter';
