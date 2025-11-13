import { useState, useRef, ReactNode, cloneElement, ReactElement } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

export interface TooltipProps {
  content: ReactNode;
  children: ReactElement;
  position?: 'top' | 'bottom' | 'left' | 'right';
  delay?: number;
  offset?: number;
  className?: string;
}

export const Tooltip = ({
  content,
  children,
  position = 'top',
  delay = 300,
  offset = 8,
  className = '',
}: TooltipProps) => {
  const [isVisible, setIsVisible] = useState(false);
  const timeoutRef = useRef<NodeJS.Timeout>();
  const triggerRef = useRef<HTMLDivElement>(null);

  const showTooltip = () => {
    timeoutRef.current = setTimeout(() => {
      setIsVisible(true);
    }, delay);
  };

  const hideTooltip = () => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
    setIsVisible(false);
  };

  // Position styles
  const positions = {
    top: {
      tooltip: 'bottom-full left-1/2 -translate-x-1/2 mb-2',
      arrow: 'top-full left-1/2 -translate-x-1/2 -mt-1',
      arrowRotate: 'rotate-180',
      initial: { opacity: 0, y: 4, scale: 0.95 },
      animate: { opacity: 1, y: 0, scale: 1 },
    },
    bottom: {
      tooltip: 'top-full left-1/2 -translate-x-1/2 mt-2',
      arrow: 'bottom-full left-1/2 -translate-x-1/2 -mb-1',
      arrowRotate: '',
      initial: { opacity: 0, y: -4, scale: 0.95 },
      animate: { opacity: 1, y: 0, scale: 1 },
    },
    left: {
      tooltip: 'right-full top-1/2 -translate-y-1/2 mr-2',
      arrow: 'left-full top-1/2 -translate-y-1/2 -ml-1',
      arrowRotate: 'rotate-90',
      initial: { opacity: 0, x: 4, scale: 0.95 },
      animate: { opacity: 1, x: 0, scale: 1 },
    },
    right: {
      tooltip: 'left-full top-1/2 -translate-y-1/2 ml-2',
      arrow: 'right-full top-1/2 -translate-y-1/2 -mr-1',
      arrowRotate: '-rotate-90',
      initial: { opacity: 0, x: -4, scale: 0.95 },
      animate: { opacity: 1, x: 0, scale: 1 },
    },
  };

  const currentPosition = positions[position];

  return (
    <div
      ref={triggerRef}
      className="relative inline-flex"
      onMouseEnter={showTooltip}
      onMouseLeave={hideTooltip}
      onFocus={showTooltip}
      onBlur={hideTooltip}
    >
      {/* Clone children to pass ref */}
      {cloneElement(children, {
        'aria-describedby': isVisible ? 'tooltip' : undefined,
      })}

      {/* Tooltip */}
      <AnimatePresence>
        {isVisible && (
          <motion.div
            id="tooltip"
            role="tooltip"
            initial={currentPosition.initial}
            animate={currentPosition.animate}
            exit={currentPosition.initial}
            transition={{ duration: 0.15, ease: [0.4, 0, 0.2, 1] }}
            className={`
              absolute ${currentPosition.tooltip} z-50 pointer-events-none
              ${className}
            `}
          >
            {/* Tooltip Content */}
            <div
              className="
                px-3 py-2 rounded-lg
                bg-neutral-900 dark:bg-neutral-100
                text-white dark:text-neutral-900
                text-sm font-medium
                shadow-lg
                max-w-xs
                whitespace-nowrap
              "
            >
              {content}
            </div>

            {/* Arrow */}
            <div className={`absolute ${currentPosition.arrow}`}>
              <div
                className={`
                  w-2 h-2
                  bg-neutral-900 dark:bg-neutral-100
                  transform rotate-45 ${currentPosition.arrowRotate}
                `}
              />
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

// Rich Tooltip with custom content
export interface RichTooltipProps {
  title?: string;
  description?: ReactNode;
  children: ReactElement;
  position?: 'top' | 'bottom' | 'left' | 'right';
  delay?: number;
  maxWidth?: string;
  className?: string;
}

export const RichTooltip = ({
  title,
  description,
  children,
  position = 'top',
  delay = 300,
  maxWidth = '18rem',
  className = '',
}: RichTooltipProps) => {
  const [isVisible, setIsVisible] = useState(false);
  const timeoutRef = useRef<NodeJS.Timeout>();

  const showTooltip = () => {
    timeoutRef.current = setTimeout(() => {
      setIsVisible(true);
    }, delay);
  };

  const hideTooltip = () => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
    setIsVisible(false);
  };

  const positions = {
    top: {
      tooltip: 'bottom-full left-1/2 -translate-x-1/2 mb-2',
      arrow: 'top-full left-1/2 -translate-x-1/2 -mt-1',
      arrowRotate: 'rotate-180',
      initial: { opacity: 0, y: 4, scale: 0.95 },
      animate: { opacity: 1, y: 0, scale: 1 },
    },
    bottom: {
      tooltip: 'top-full left-1/2 -translate-x-1/2 mt-2',
      arrow: 'bottom-full left-1/2 -translate-x-1/2 -mb-1',
      arrowRotate: '',
      initial: { opacity: 0, y: -4, scale: 0.95 },
      animate: { opacity: 1, y: 0, scale: 1 },
    },
    left: {
      tooltip: 'right-full top-1/2 -translate-y-1/2 mr-2',
      arrow: 'left-full top-1/2 -translate-y-1/2 -ml-1',
      arrowRotate: 'rotate-90',
      initial: { opacity: 0, x: 4, scale: 0.95 },
      animate: { opacity: 1, x: 0, scale: 1 },
    },
    right: {
      tooltip: 'left-full top-1/2 -translate-y-1/2 ml-2',
      arrow: 'right-full top-1/2 -translate-y-1/2 -mr-1',
      arrowRotate: '-rotate-90',
      initial: { opacity: 0, x: -4, scale: 0.95 },
      animate: { opacity: 1, x: 0, scale: 1 },
    },
  };

  const currentPosition = positions[position];

  return (
    <div
      className="relative inline-flex"
      onMouseEnter={showTooltip}
      onMouseLeave={hideTooltip}
      onFocus={showTooltip}
      onBlur={hideTooltip}
    >
      {cloneElement(children, {
        'aria-describedby': isVisible ? 'rich-tooltip' : undefined,
      })}

      <AnimatePresence>
        {isVisible && (
          <motion.div
            id="rich-tooltip"
            role="tooltip"
            initial={currentPosition.initial}
            animate={currentPosition.animate}
            exit={currentPosition.initial}
            transition={{ duration: 0.15, ease: [0.4, 0, 0.2, 1] }}
            className={`
              absolute ${currentPosition.tooltip} z-50 pointer-events-none
              ${className}
            `}
            style={{ maxWidth }}
          >
            {/* Rich Tooltip Content */}
            <div
              className="
                p-4 rounded-xl
                bg-white dark:bg-neutral-900
                border-2 border-neutral-200 dark:border-neutral-800
                shadow-2xl
              "
            >
              {title && (
                <h4 className="text-sm font-bold text-neutral-900 dark:text-neutral-100 mb-1">
                  {title}
                </h4>
              )}
              {description && (
                <div className="text-xs text-neutral-600 dark:text-neutral-400 whitespace-normal">
                  {description}
                </div>
              )}
            </div>

            {/* Arrow */}
            <div className={`absolute ${currentPosition.arrow}`}>
              <div
                className={`
                  w-3 h-3
                  bg-white dark:bg-neutral-900
                  border-neutral-200 dark:border-neutral-800
                  transform rotate-45 ${currentPosition.arrowRotate}
                  ${position === 'top' ? 'border-t-2 border-l-2' : ''}
                  ${position === 'bottom' ? 'border-b-2 border-r-2' : ''}
                  ${position === 'left' ? 'border-b-2 border-l-2' : ''}
                  ${position === 'right' ? 'border-t-2 border-r-2' : ''}
                `}
              />
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};
