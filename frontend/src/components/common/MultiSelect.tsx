import { Fragment, useState } from 'react';
import { Combobox, Transition } from '@headlessui/react';
import { Check, ChevronsUpDown, X } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export interface MultiSelectOption {
  value: string;
  label: string;
  description?: string;
  disabled?: boolean;
}

interface MultiSelectProps {
  options: MultiSelectOption[];
  value: string[];
  onChange: (value: string[]) => void;
  placeholder?: string;
  label?: string;
  error?: string;
  disabled?: boolean;
  maxSelections?: number;
  searchPlaceholder?: string;
}

export default function MultiSelect({
  options,
  value = [],
  onChange,
  placeholder = 'Select items...',
  label,
  error,
  disabled = false,
  maxSelections,
  searchPlaceholder = 'Search...',
}: MultiSelectProps) {
  const [query, setQuery] = useState('');

  const selectedOptions = options.filter((option) => value.includes(option.value));

  const filteredOptions =
    query === ''
      ? options
      : options.filter((option) =>
          option.label.toLowerCase().includes(query.toLowerCase()) ||
          option.description?.toLowerCase().includes(query.toLowerCase())
        );

  const handleSelect = (newValue: string[]) => {
    if (maxSelections && newValue.length > maxSelections) {
      return;
    }
    onChange(newValue);
  };

  const removeOption = (optionValue: string) => {
    onChange(value.filter((v) => v !== optionValue));
  };

  const canSelectMore = !maxSelections || value.length < maxSelections;

  return (
    <div className="w-full">
      {label && (
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          {label}
          {maxSelections && (
            <span className="ml-2 text-xs text-gray-500 dark:text-gray-400">
              ({value.length}/{maxSelections})
            </span>
          )}
        </label>
      )}

      <Combobox value={value} onChange={handleSelect} multiple disabled={disabled}>
        <div className="relative">
          {/* Selected Tags */}
          {selectedOptions.length > 0 && (
            <div className="flex flex-wrap gap-2 mb-2">
              <AnimatePresence>
                {selectedOptions.map((option) => (
                  <motion.div
                    key={option.value}
                    initial={{ scale: 0, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    exit={{ scale: 0, opacity: 0 }}
                    transition={{ duration: 0.2 }}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-primary-100 dark:bg-primary-900/20 text-primary-700 dark:text-primary-300 rounded-lg text-sm font-medium"
                  >
                    <span>{option.label}</span>
                    <button
                      type="button"
                      onClick={() => removeOption(option.value)}
                      disabled={disabled}
                      className="hover:bg-primary-200 dark:hover:bg-primary-800 rounded p-0.5 transition-colors disabled:opacity-50"
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </motion.div>
                ))}
              </AnimatePresence>
            </div>
          )}

          {/* Input */}
          <div className="relative">
            <Combobox.Input
              className={`w-full px-4 py-2.5 pr-10 border rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all ${
                error
                  ? 'border-error-500 focus:ring-error-500'
                  : 'border-gray-300 dark:border-gray-600'
              } ${disabled ? 'opacity-50 cursor-not-allowed' : ''} ${
                !canSelectMore ? 'cursor-not-allowed' : ''
              }`}
              displayValue={() => ''}
              onChange={(event) => setQuery(event.target.value)}
              placeholder={selectedOptions.length === 0 ? placeholder : searchPlaceholder}
              disabled={disabled || !canSelectMore}
            />
            <Combobox.Button className="absolute inset-y-0 right-0 flex items-center pr-3">
              <ChevronsUpDown className="w-5 h-5 text-gray-400" />
            </Combobox.Button>
          </div>

          {/* Options Dropdown */}
          <Transition
            as={Fragment}
            leave="transition ease-in duration-100"
            leaveFrom="opacity-100"
            leaveTo="opacity-0"
            afterLeave={() => setQuery('')}
          >
            <Combobox.Options className="absolute z-10 mt-2 w-full max-h-60 overflow-auto rounded-lg bg-white dark:bg-gray-800 shadow-lg ring-1 ring-black/5 dark:ring-white/10 focus:outline-none">
              {filteredOptions.length === 0 && query !== '' ? (
                <div className="px-4 py-3 text-sm text-gray-500 dark:text-gray-400">
                  No results found.
                </div>
              ) : (
                filteredOptions.map((option) => {
                  const isSelected = value.includes(option.value);
                  const isDisabled = option.disabled || (!isSelected && !canSelectMore);

                  return (
                    <Combobox.Option
                      key={option.value}
                      value={option.value}
                      disabled={isDisabled}
                      className={({ active }) =>
                        `relative cursor-pointer select-none py-3 px-4 ${
                          active
                            ? 'bg-primary-50 dark:bg-primary-900/20 text-primary-900 dark:text-primary-100'
                            : 'text-gray-900 dark:text-gray-100'
                        } ${isDisabled ? 'opacity-50 cursor-not-allowed' : ''}`
                      }
                    >
                      {({ selected, active }) => (
                        <div className="flex items-start">
                          <div className="flex-1">
                            <div
                              className={`block truncate ${
                                selected ? 'font-semibold' : 'font-normal'
                              }`}
                            >
                              {option.label}
                            </div>
                            {option.description && (
                              <div className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                                {option.description}
                              </div>
                            )}
                          </div>
                          {isSelected && (
                            <Check className="w-5 h-5 text-primary-600 dark:text-primary-400 flex-shrink-0 ml-2" />
                          )}
                        </div>
                      )}
                    </Combobox.Option>
                  );
                })
              )}
            </Combobox.Options>
          </Transition>
        </div>
      </Combobox>

      {/* Error Message */}
      {error && (
        <motion.p
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="mt-2 text-sm text-error-600 dark:text-error-400"
        >
          {error}
        </motion.p>
      )}

      {/* Max Selections Warning */}
      {maxSelections && value.length >= maxSelections && (
        <motion.p
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="mt-2 text-sm text-warning-600 dark:text-warning-400"
        >
          Maximum {maxSelections} selection{maxSelections !== 1 ? 's' : ''} reached
        </motion.p>
      )}
    </div>
  );
}
