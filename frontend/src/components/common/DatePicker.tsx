import { useState, useRef, useEffect } from 'react';
import { Calendar as CalendarIcon, ChevronLeft, ChevronRight, X } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

interface DatePickerProps {
  value?: Date | null;
  onChange: (date: Date | null) => void;
  label?: string;
  placeholder?: string;
  error?: string;
  disabled?: boolean;
  minDate?: Date;
  maxDate?: Date;
}

interface DateRangePickerProps {
  value?: { start: Date | null; end: Date | null };
  onChange: (range: { start: Date | null; end: Date | null }) => void;
  label?: string;
  placeholder?: string;
  error?: string;
  disabled?: boolean;
  minDate?: Date;
  maxDate?: Date;
}

const MONTHS = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December'
];

const DAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

function getDaysInMonth(year: number, month: number): number {
  return new Date(year, month + 1, 0).getDate();
}

function getFirstDayOfMonth(year: number, month: number): number {
  return new Date(year, month, 1).getDay();
}

function isSameDay(date1: Date | null, date2: Date | null): boolean {
  if (!date1 || !date2) return false;
  return (
    date1.getFullYear() === date2.getFullYear() &&
    date1.getMonth() === date2.getMonth() &&
    date1.getDate() === date2.getDate()
  );
}

function isDateInRange(date: Date, start: Date | null, end: Date | null): boolean {
  if (!start || !end) return false;
  return date >= start && date <= end;
}

function formatDate(date: Date | null): string {
  if (!date) return '';
  return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
}

function Calendar({
  selectedDate,
  onSelect,
  minDate,
  maxDate,
  rangeStart,
  rangeEnd,
}: {
  selectedDate?: Date | null;
  onSelect: (date: Date) => void;
  minDate?: Date;
  maxDate?: Date;
  rangeStart?: Date | null;
  rangeEnd?: Date | null;
}) {
  const [currentMonth, setCurrentMonth] = useState(selectedDate || new Date());

  const year = currentMonth.getFullYear();
  const month = currentMonth.getMonth();
  const daysInMonth = getDaysInMonth(year, month);
  const firstDay = getFirstDayOfMonth(year, month);

  const prevMonth = () => {
    setCurrentMonth(new Date(year, month - 1));
  };

  const nextMonth = () => {
    setCurrentMonth(new Date(year, month + 1));
  };

  const isDisabled = (date: Date): boolean => {
    if (minDate && date < minDate) return true;
    if (maxDate && date > maxDate) return true;
    return false;
  };

  const days = [];

  // Empty cells for days before month starts
  for (let i = 0; i < firstDay; i++) {
    days.push(<div key={`empty-${i}`} className="h-10" />);
  }

  // Actual days
  for (let day = 1; day <= daysInMonth; day++) {
    const date = new Date(year, month, day);
    const isSelected = isSameDay(date, selectedDate);
    const isInRange = isDateInRange(date, rangeStart || null, rangeEnd || null);
    const isRangeStart = isSameDay(date, rangeStart);
    const isRangeEnd = isSameDay(date, rangeEnd);
    const disabled = isDisabled(date);
    const isToday = isSameDay(date, new Date());

    days.push(
      <motion.button
        key={day}
        whileHover={!disabled ? { scale: 1.1 } : {}}
        whileTap={!disabled ? { scale: 0.95 } : {}}
        type="button"
        onClick={() => !disabled && onSelect(date)}
        disabled={disabled}
        className={`h-10 rounded-lg text-sm font-medium transition-colors relative ${
          disabled
            ? 'text-gray-300 dark:text-gray-600 cursor-not-allowed'
            : isSelected || isRangeStart || isRangeEnd
            ? 'bg-primary-500 text-white'
            : isInRange
            ? 'bg-primary-100 dark:bg-primary-900/20 text-primary-700 dark:text-primary-300'
            : isToday
            ? 'bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-white ring-2 ring-primary-500'
            : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
        }`}
      >
        {day}
      </motion.button>
    );
  }

  return (
    <div className="p-4">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <button
          type="button"
          onClick={prevMonth}
          className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
        >
          <ChevronLeft className="w-5 h-5 text-gray-600 dark:text-gray-400" />
        </button>

        <div className="font-semibold text-gray-900 dark:text-white">
          {MONTHS[month]} {year}
        </div>

        <button
          type="button"
          onClick={nextMonth}
          className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
        >
          <ChevronRight className="w-5 h-5 text-gray-600 dark:text-gray-400" />
        </button>
      </div>

      {/* Day labels */}
      <div className="grid grid-cols-7 gap-1 mb-2">
        {DAYS.map((day) => (
          <div
            key={day}
            className="h-10 flex items-center justify-center text-xs font-medium text-gray-500 dark:text-gray-400"
          >
            {day}
          </div>
        ))}
      </div>

      {/* Days grid */}
      <div className="grid grid-cols-7 gap-1">{days}</div>
    </div>
  );
}

export function DatePicker({
  value,
  onChange,
  label,
  placeholder = 'Select date',
  error,
  disabled = false,
  minDate,
  maxDate,
}: DatePickerProps) {
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSelect = (date: Date) => {
    onChange(date);
    setIsOpen(false);
  };

  const handleClear = (e: React.MouseEvent) => {
    e.stopPropagation();
    onChange(null);
  };

  return (
    <div className="w-full" ref={containerRef}>
      {label && (
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          {label}
        </label>
      )}

      <div className="relative">
        <button
          type="button"
          onClick={() => !disabled && setIsOpen(!isOpen)}
          disabled={disabled}
          className={`w-full px-4 py-2.5 pr-10 border rounded-lg bg-white dark:bg-gray-800 text-left transition-all focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent ${
            error
              ? 'border-error-500 focus:ring-error-500'
              : 'border-gray-300 dark:border-gray-600'
          } ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
        >
          <span className={value ? 'text-gray-900 dark:text-white' : 'text-gray-500 dark:text-gray-400'}>
            {value ? formatDate(value) : placeholder}
          </span>
        </button>

        <div className="absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none">
          <CalendarIcon className="w-5 h-5 text-gray-400" />
        </div>

        {value && !disabled && (
          <button
            type="button"
            onClick={handleClear}
            className="absolute inset-y-0 right-10 flex items-center pr-3 pointer-events-auto hover:text-error-600"
          >
            <X className="w-4 h-4 text-gray-400" />
          </button>
        )}

        <AnimatePresence>
          {isOpen && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.2 }}
              className="absolute z-50 mt-2 bg-white dark:bg-gray-800 rounded-lg shadow-lg ring-1 ring-black/5 dark:ring-white/10"
            >
              <Calendar
                selectedDate={value}
                onSelect={handleSelect}
                minDate={minDate}
                maxDate={maxDate}
              />
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {error && (
        <motion.p
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="mt-2 text-sm text-error-600 dark:text-error-400"
        >
          {error}
        </motion.p>
      )}
    </div>
  );
}

export function DateRangePicker({
  value = { start: null, end: null },
  onChange,
  label,
  placeholder = 'Select date range',
  error,
  disabled = false,
  minDate,
  maxDate,
}: DateRangePickerProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [selectingEnd, setSelectingEnd] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
        setSelectingEnd(false);
      }
    }

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSelect = (date: Date) => {
    if (!value.start || selectingEnd) {
      if (!value.start) {
        onChange({ start: date, end: null });
        setSelectingEnd(true);
      } else {
        if (date >= value.start) {
          onChange({ ...value, end: date });
          setIsOpen(false);
          setSelectingEnd(false);
        } else {
          // If selected date is before start, swap them
          onChange({ start: date, end: value.start });
          setIsOpen(false);
          setSelectingEnd(false);
        }
      }
    } else {
      onChange({ start: date, end: null });
      setSelectingEnd(true);
    }
  };

  const handleClear = (e: React.MouseEvent) => {
    e.stopPropagation();
    onChange({ start: null, end: null });
    setSelectingEnd(false);
  };

  const displayText = () => {
    if (value.start && value.end) {
      return `${formatDate(value.start)} - ${formatDate(value.end)}`;
    } else if (value.start) {
      return `${formatDate(value.start)} - ...`;
    }
    return placeholder;
  };

  return (
    <div className="w-full" ref={containerRef}>
      {label && (
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          {label}
        </label>
      )}

      <div className="relative">
        <button
          type="button"
          onClick={() => !disabled && setIsOpen(!isOpen)}
          disabled={disabled}
          className={`w-full px-4 py-2.5 pr-10 border rounded-lg bg-white dark:bg-gray-800 text-left transition-all focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent ${
            error
              ? 'border-error-500 focus:ring-error-500'
              : 'border-gray-300 dark:border-gray-600'
          } ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
        >
          <span className={value.start ? 'text-gray-900 dark:text-white' : 'text-gray-500 dark:text-gray-400'}>
            {displayText()}
          </span>
        </button>

        <div className="absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none">
          <CalendarIcon className="w-5 h-5 text-gray-400" />
        </div>

        {value.start && !disabled && (
          <button
            type="button"
            onClick={handleClear}
            className="absolute inset-y-0 right-10 flex items-center pr-3 pointer-events-auto hover:text-error-600"
          >
            <X className="w-4 h-4 text-gray-400" />
          </button>
        )}

        <AnimatePresence>
          {isOpen && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.2 }}
              className="absolute z-50 mt-2 bg-white dark:bg-gray-800 rounded-lg shadow-lg ring-1 ring-black/5 dark:ring-white/10"
            >
              <Calendar
                selectedDate={selectingEnd ? value.end : value.start}
                onSelect={handleSelect}
                minDate={minDate}
                maxDate={maxDate}
                rangeStart={value.start}
                rangeEnd={value.end}
              />
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {error && (
        <motion.p
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="mt-2 text-sm text-error-600 dark:text-error-400"
        >
          {error}
        </motion.p>
      )}
    </div>
  );
}
