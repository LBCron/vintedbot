import { forwardRef, useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Check, ChevronDown, X, Search } from 'lucide-react';

export interface SelectOption {
  value: string;
  label: string;
  disabled?: boolean;
  description?: string;
}

export interface SelectProps extends Omit<React.HTMLAttributes<HTMLDivElement>, 'onChange'> {
  label?: string;
  error?: string;
  helperText?: string;
  placeholder?: string;
  options: SelectOption[];
  value?: string | string[];
  onChange?: (value: string | string[]) => void;
  multiple?: boolean;
  searchable?: boolean;
  clearable?: boolean;
  disabled?: boolean;
  fullWidth?: boolean;
}

export const Select = forwardRef<HTMLDivElement, SelectProps>(
  ({
    label,
    error,
    helperText,
    placeholder = 'Select an option',
    options,
    value,
    onChange,
    multiple = false,
    searchable = false,
    clearable = false,
    disabled = false,
    fullWidth = false,
    className = '',
    ...props
  }, ref) => {
    const [isOpen, setIsOpen] = useState(false);
    const [searchQuery, setSearchQuery] = useState('');
    const [highlightedIndex, setHighlightedIndex] = useState(0);
    const containerRef = useRef<HTMLDivElement>(null);
    const searchInputRef = useRef<HTMLInputElement>(null);

    // Get selected option(s) label
    const getSelectedLabel = () => {
      if (!value || (Array.isArray(value) && value.length === 0)) return placeholder;

      if (Array.isArray(value)) {
        const selectedOptions = options.filter(opt => value.includes(opt.value));
        return selectedOptions.length > 0
          ? `${selectedOptions.length} selected`
          : placeholder;
      }

      const selectedOption = options.find(opt => opt.value === value);
      return selectedOption?.label || placeholder;
    };

    // Filter options based on search query
    const filteredOptions = searchable && searchQuery
      ? options.filter(opt =>
          opt.label.toLowerCase().includes(searchQuery.toLowerCase()) ||
          opt.description?.toLowerCase().includes(searchQuery.toLowerCase())
        )
      : options;

    // Handle option selection
    const handleSelect = (optionValue: string) => {
      if (multiple) {
        const currentValues = Array.isArray(value) ? value : [];
        const newValues = currentValues.includes(optionValue)
          ? currentValues.filter(v => v !== optionValue)
          : [...currentValues, optionValue];
        onChange?.(newValues);
      } else {
        onChange?.(optionValue);
        setIsOpen(false);
      }
    };

    // Handle clear
    const handleClear = (e: React.MouseEvent) => {
      e.stopPropagation();
      onChange?.(multiple ? [] : '');
    };

    // Check if option is selected
    const isSelected = (optionValue: string) => {
      if (Array.isArray(value)) return value.includes(optionValue);
      return value === optionValue;
    };

    // Close dropdown when clicking outside
    useEffect(() => {
      const handleClickOutside = (event: MouseEvent) => {
        if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
          setIsOpen(false);
          setSearchQuery('');
        }
      };

      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    // Focus search input when dropdown opens
    useEffect(() => {
      if (isOpen && searchable && searchInputRef.current) {
        searchInputRef.current.focus();
      }
    }, [isOpen, searchable]);

    // Keyboard navigation
    const handleKeyDown = (e: React.KeyboardEvent) => {
      if (disabled) return;

      switch (e.key) {
        case 'Enter':
        case ' ':
          if (!isOpen) {
            setIsOpen(true);
          } else if (filteredOptions[highlightedIndex]) {
            handleSelect(filteredOptions[highlightedIndex].value);
          }
          e.preventDefault();
          break;
        case 'ArrowDown':
          if (!isOpen) {
            setIsOpen(true);
          } else {
            setHighlightedIndex(prev =>
              prev < filteredOptions.length - 1 ? prev + 1 : prev
            );
          }
          e.preventDefault();
          break;
        case 'ArrowUp':
          setHighlightedIndex(prev => prev > 0 ? prev - 1 : 0);
          e.preventDefault();
          break;
        case 'Escape':
          setIsOpen(false);
          setSearchQuery('');
          break;
      }
    };

    return (
      <div ref={containerRef} className={`relative ${fullWidth ? 'w-full' : ''}`} {...props}>
        {/* Label */}
        {label && (
          <label className={`
            block text-sm font-medium mb-1.5
            ${error ? 'text-error-600' : 'text-neutral-700 dark:text-neutral-300'}
          `}>
            {label}
          </label>
        )}

        {/* Select Button */}
        <motion.button
          type="button"
          ref={ref}
          onClick={() => !disabled && setIsOpen(!isOpen)}
          onKeyDown={handleKeyDown}
          disabled={disabled}
          className={`
            w-full px-4 py-3 rounded-lg border-2 transition-all duration-200
            bg-white dark:bg-neutral-900
            text-left flex items-center justify-between gap-2
            ${error
              ? 'border-error-500 focus:border-error-600'
              : 'border-neutral-300 dark:border-neutral-700 focus:border-primary-500'
            }
            ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
            ${isOpen ? 'border-primary-500 ring-2 ring-primary-500/20' : ''}
            ${className}
          `}
          whileHover={!disabled ? { scale: 1.01 } : {}}
        >
          <span className={`flex-1 truncate ${!value || (Array.isArray(value) && value.length === 0) ? 'text-neutral-500' : 'text-neutral-900 dark:text-neutral-100'}`}>
            {getSelectedLabel()}
          </span>

          <div className="flex items-center gap-1">
            {clearable && value && (Array.isArray(value) ? value.length > 0 : true) && (
              <motion.div
                whileHover={{ scale: 1.2 }}
                whileTap={{ scale: 0.9 }}
                onClick={handleClear}
                className="p-0.5 hover:bg-neutral-200 dark:hover:bg-neutral-700 rounded"
              >
                <X className="w-4 h-4 text-neutral-500" />
              </motion.div>
            )}
            <motion.div
              animate={{ rotate: isOpen ? 180 : 0 }}
              transition={{ duration: 0.2 }}
            >
              <ChevronDown className="w-4 h-4 text-neutral-500" />
            </motion.div>
          </div>
        </motion.button>

        {/* Dropdown */}
        <AnimatePresence>
          {isOpen && (
            <motion.div
              initial={{ opacity: 0, y: -10, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -10, scale: 0.95 }}
              transition={{ duration: 0.15 }}
              className="absolute z-50 w-full mt-2 py-2 bg-white dark:bg-neutral-900 rounded-lg border-2 border-neutral-200 dark:border-neutral-800 shadow-xl max-h-80 overflow-hidden flex flex-col"
            >
              {/* Search Input */}
              {searchable && (
                <div className="px-3 pb-2 border-b border-neutral-200 dark:border-neutral-800">
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-neutral-500" />
                    <input
                      ref={searchInputRef}
                      type="text"
                      value={searchQuery}
                      onChange={(e) => {
                        setSearchQuery(e.target.value);
                        setHighlightedIndex(0);
                      }}
                      placeholder="Search..."
                      className="w-full pl-9 pr-3 py-2 bg-neutral-100 dark:bg-neutral-800 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
                      onClick={(e) => e.stopPropagation()}
                    />
                  </div>
                </div>
              )}

              {/* Options List */}
              <div className="overflow-y-auto scrollbar-thin">
                {filteredOptions.length === 0 ? (
                  <div className="px-4 py-3 text-sm text-neutral-500 text-center">
                    No options found
                  </div>
                ) : (
                  filteredOptions.map((option, index) => (
                    <motion.button
                      key={option.value}
                      type="button"
                      onClick={() => !option.disabled && handleSelect(option.value)}
                      onMouseEnter={() => setHighlightedIndex(index)}
                      disabled={option.disabled}
                      className={`
                        w-full px-4 py-2.5 text-left flex items-center justify-between gap-2
                        transition-colors duration-150
                        ${option.disabled
                          ? 'opacity-50 cursor-not-allowed'
                          : 'cursor-pointer'
                        }
                        ${isSelected(option.value)
                          ? 'bg-primary-50 dark:bg-primary-900/20 text-primary-700 dark:text-primary-400'
                          : highlightedIndex === index
                            ? 'bg-neutral-100 dark:bg-neutral-800'
                            : 'hover:bg-neutral-50 dark:hover:bg-neutral-800/50'
                        }
                      `}
                      whileHover={!option.disabled ? { x: 4 } : {}}
                    >
                      <div className="flex-1 min-w-0">
                        <div className="text-sm font-medium text-neutral-900 dark:text-neutral-100 truncate">
                          {option.label}
                        </div>
                        {option.description && (
                          <div className="text-xs text-neutral-600 dark:text-neutral-400 truncate">
                            {option.description}
                          </div>
                        )}
                      </div>

                      {isSelected(option.value) && (
                        <motion.div
                          initial={{ scale: 0 }}
                          animate={{ scale: 1 }}
                          exit={{ scale: 0 }}
                        >
                          <Check className="w-4 h-4 text-primary-600" strokeWidth={3} />
                        </motion.div>
                      )}
                    </motion.button>
                  ))
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Helper Text or Error */}
        {(error || helperText) && (
          <motion.p
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className={`text-sm mt-1.5 ${error ? 'text-error-600' : 'text-neutral-600 dark:text-neutral-400'}`}
          >
            {error || helperText}
          </motion.p>
        )}
      </div>
    );
  }
);

Select.displayName = 'Select';
