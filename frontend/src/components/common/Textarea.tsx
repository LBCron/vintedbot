import { forwardRef, useEffect, useRef, useState } from 'react';
import { motion } from 'framer-motion';

export interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  error?: string;
  helperText?: string;
  autoResize?: boolean;
  maxLength?: number;
  showCount?: boolean;
  fullWidth?: boolean;
}

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({
    label,
    error,
    helperText,
    autoResize = true,
    maxLength,
    showCount = false,
    fullWidth = false,
    className = '',
    ...props
  }, ref) => {
    const [isFocused, setIsFocused] = useState(false);
    const [hasValue, setHasValue] = useState(!!props.value || !!props.defaultValue);
    const [charCount, setCharCount] = useState(0);
    const textareaRef = useRef<HTMLTextAreaElement>(null);

    // Auto-resize functionality
    useEffect(() => {
      if (autoResize && textareaRef.current) {
        textareaRef.current.style.height = 'auto';
        textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
      }
    }, [props.value, autoResize]);

    const handleFocus = () => setIsFocused(true);
    const handleBlur = (e: React.FocusEvent<HTMLTextAreaElement>) => {
      setIsFocused(false);
      setHasValue(!!e.target.value);
      props.onBlur?.(e);
    };

    const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
      setHasValue(!!e.target.value);
      setCharCount(e.target.value.length);
      props.onChange?.(e);
    };

    return (
      <div className={`${fullWidth ? 'w-full' : ''}`}>
        <div className="relative">
          {/* Textarea */}
          <textarea
            ref={(node) => {
              if (typeof ref === 'function') ref(node);
              else if (ref) ref.current = node;
              // @ts-ignore
              textareaRef.current = node;
            }}
            className={`
              w-full px-4 py-3 rounded-lg
              border-2 transition-all duration-200
              bg-white dark:bg-neutral-900
              text-neutral-900 dark:text-neutral-100
              placeholder-transparent
              focus:outline-none focus:ring-0
              resize-none
              ${error
                ? 'border-error-500 focus:border-error-600'
                : 'border-neutral-300 dark:border-neutral-700 focus:border-primary-500'
              }
              ${props.disabled ? 'opacity-50 cursor-not-allowed' : ''}
              ${className}
            `}
            placeholder={label}
            onFocus={handleFocus}
            onBlur={handleBlur}
            onChange={handleChange}
            maxLength={maxLength}
            rows={autoResize ? 1 : props.rows || 4}
            {...props}
          />

          {/* Floating Label */}
          {label && (
            <motion.label
              className={`
                absolute left-4 pointer-events-none transition-all duration-200
                ${isFocused || hasValue
                  ? '-top-2.5 text-xs bg-white dark:bg-neutral-900 px-1'
                  : 'top-3 text-base'
                }
                ${error
                  ? 'text-error-600'
                  : isFocused
                    ? 'text-primary-600 dark:text-primary-400'
                    : 'text-neutral-500 dark:text-neutral-400'
                }
              `}
            >
              {label}
            </motion.label>
          )}
        </div>

        {/* Footer with Helper Text and Character Count */}
        <div className="flex items-center justify-between mt-1.5">
          {(error || helperText) && (
            <motion.p
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className={`text-sm ${error ? 'text-error-600' : 'text-neutral-600 dark:text-neutral-400'}`}
            >
              {error || helperText}
            </motion.p>
          )}

          {showCount && maxLength && (
            <span className={`text-sm ml-auto ${charCount > maxLength * 0.9 ? 'text-warning-600' : 'text-neutral-500 dark:text-neutral-400'}`}>
              {charCount}/{maxLength}
            </span>
          )}
        </div>
      </div>
    );
  }
);

Textarea.displayName = 'Textarea';
