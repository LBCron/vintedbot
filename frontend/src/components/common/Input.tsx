/**
 * Input Component
 * Uses design system CSS variables and utility classes from index.css
 *
 * Features:
 * - Floating label animation
 * - Icon support (left and right)
 * - Error states with visual feedback
 * - Helper text
 * - Full accessibility support
 * - Uses CSS variable heights from design system
 */

import { forwardRef, useState } from 'react';
import { motion } from 'framer-motion';

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helperText?: string;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  fullWidth?: boolean;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({
    label,
    error,
    helperText,
    leftIcon,
    rightIcon,
    fullWidth = false,
    className = '',
    ...props
  }, ref) => {
    const [isFocused, setIsFocused] = useState(false);
    const [hasValue, setHasValue] = useState(!!props.value || !!props.defaultValue);

    const handleFocus = () => setIsFocused(true);
    const handleBlur = (e: React.FocusEvent<HTMLInputElement>) => {
      setIsFocused(false);
      setHasValue(!!e.target.value);
      props.onBlur?.(e);
    };

    return (
      <div className={`${fullWidth ? 'w-full' : ''}`}>
        <div className="relative">
          {/* Input - uses .input or .input-error utility classes */}
          <input
            ref={ref}
            className={`
              ${error ? 'input-error' : 'input'}
              placeholder-transparent
              ${leftIcon ? 'pl-11' : ''}
              ${rightIcon ? 'pr-11' : ''}
              ${className}
            `}
            placeholder={label}
            onFocus={handleFocus}
            onBlur={handleBlur}
            onChange={(e) => {
              setHasValue(!!e.target.value);
              props.onChange?.(e);
            }}
            {...props}
          />

          {/* Floating Label */}
          {label && (
            <motion.label
              className="absolute left-4 pointer-events-none"
              style={{
                transition: 'all var(--transition-fast)',
                top: isFocused || hasValue ? '-0.625rem' : '0.75rem',
                fontSize: isFocused || hasValue ? 'var(--text-xs)' : 'var(--text-base)',
                padding: isFocused || hasValue ? '0 var(--spacing-1)' : 0,
                backgroundColor: isFocused || hasValue ? 'var(--bg-primary)' : 'transparent',
                color: error
                  ? 'var(--error-600)'
                  : isFocused
                    ? 'var(--primary-600)'
                    : 'var(--text-tertiary)',
              }}
              animate={{
                y: isFocused || hasValue ? 0 : 0,
                scale: isFocused || hasValue ? 0.875 : 1,
              }}
            >
              {label}
            </motion.label>
          )}

          {/* Left Icon */}
          {leftIcon && (
            <div
              className="absolute left-3 top-1/2 -translate-y-1/2"
              style={{ color: 'var(--text-tertiary)' }}
            >
              {leftIcon}
            </div>
          )}

          {/* Right Icon */}
          {rightIcon && (
            <div
              className="absolute right-3 top-1/2 -translate-y-1/2"
              style={{ color: 'var(--text-tertiary)' }}
            >
              {rightIcon}
            </div>
          )}
        </div>

        {/* Helper Text or Error */}
        {(error || helperText) && (
          <motion.p
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            style={{
              marginTop: 'var(--spacing-1\\.5)',
              fontSize: 'var(--text-sm)',
              color: error ? 'var(--error-600)' : 'var(--text-secondary)',
            }}
          >
            {error || helperText}
          </motion.p>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';
