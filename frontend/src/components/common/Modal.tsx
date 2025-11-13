import { forwardRef, useEffect, ReactNode } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X } from 'lucide-react';

export interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  children: ReactNode;
  size?: 'sm' | 'md' | 'lg' | 'xl' | 'full';
  closeOnOverlayClick?: boolean;
  closeOnEscape?: boolean;
  showCloseButton?: boolean;
  className?: string;
}

export interface ModalHeaderProps {
  children: ReactNode;
  className?: string;
}

export interface ModalContentProps {
  children: ReactNode;
  className?: string;
}

export interface ModalFooterProps {
  children: ReactNode;
  className?: string;
}

export const Modal = forwardRef<HTMLDivElement, ModalProps>(
  ({
    isOpen,
    onClose,
    children,
    size = 'md',
    closeOnOverlayClick = true,
    closeOnEscape = true,
    showCloseButton = true,
    className = '',
  }, ref) => {
    const sizes = {
      sm: 'max-w-md',
      md: 'max-w-lg',
      lg: 'max-w-2xl',
      xl: 'max-w-4xl',
      full: 'max-w-7xl mx-4',
    };

    // Lock body scroll when modal is open
    useEffect(() => {
      if (isOpen) {
        document.body.style.overflow = 'hidden';
        return () => {
          document.body.style.overflow = '';
        };
      }
    }, [isOpen]);

    // Handle escape key
    useEffect(() => {
      if (!closeOnEscape) return;

      const handleEscape = (e: KeyboardEvent) => {
        if (e.key === 'Escape' && isOpen) {
          onClose();
        }
      };

      document.addEventListener('keydown', handleEscape);
      return () => document.removeEventListener('keydown', handleEscape);
    }, [isOpen, onClose, closeOnEscape]);

    return (
      <AnimatePresence>
        {isOpen && (
          <>
            {/* Overlay */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.2 }}
              onClick={() => closeOnOverlayClick && onClose()}
              className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50"
            />

            {/* Modal Container */}
            <div className="fixed inset-0 z-50 flex items-center justify-center p-4 pointer-events-none">
              <motion.div
                ref={ref}
                initial={{ opacity: 0, scale: 0.95, y: 20 }}
                animate={{ opacity: 1, scale: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.95, y: 20 }}
                transition={{ duration: 0.2, ease: [0.4, 0, 0.2, 1] }}
                onClick={(e) => e.stopPropagation()}
                className={`relative w-full ${sizes[size]} pointer-events-auto max-h-[90vh] flex flex-col ${className}`}
                style={{
                  backgroundColor: 'var(--bg-primary)',
                  borderRadius: 'var(--radius-2xl)',
                  boxShadow: 'var(--shadow-2xl)',
                }}
              >
                {/* Close Button */}
                {showCloseButton && (
                  <motion.button
                    onClick={onClose}
                    whileHover={{ scale: 1.1, rotate: 90 }}
                    whileTap={{ scale: 0.9 }}
                    className="absolute top-4 right-4 p-2 rounded-lg hover:bg-neutral-100 dark:hover:bg-neutral-800 transition-colors z-10"
                  >
                    <X className="w-5 h-5 text-neutral-600 dark:text-neutral-400" />
                  </motion.button>
                )}

                {/* Modal Content */}
                {children}
              </motion.div>
            </div>
          </>
        )}
      </AnimatePresence>
    );
  }
);

Modal.displayName = 'Modal';

// Modal Header Component
export const ModalHeader = forwardRef<HTMLDivElement, ModalHeaderProps>(
  ({ children, className = '' }, ref) => {
    return (
      <div
        ref={ref}
        className={`
          px-6 py-5 border-b border-neutral-200 dark:border-neutral-800
          ${className}
        `}
      >
        {children}
      </div>
    );
  }
);

ModalHeader.displayName = 'ModalHeader';

// Modal Title Component
export const ModalTitle = ({ children, className = '' }: { children: ReactNode; className?: string }) => {
  return (
    <h2 className={`text-2xl font-bold text-neutral-900 dark:text-neutral-100 ${className}`}>
      {children}
    </h2>
  );
};

// Modal Description Component
export const ModalDescription = ({ children, className = '' }: { children: ReactNode; className?: string }) => {
  return (
    <p className={`text-sm text-neutral-600 dark:text-neutral-400 mt-1 ${className}`}>
      {children}
    </p>
  );
};

// Modal Content Component
export const ModalContent = forwardRef<HTMLDivElement, ModalContentProps>(
  ({ children, className = '' }, ref) => {
    return (
      <div
        ref={ref}
        className={`
          px-6 py-5 overflow-y-auto scrollbar-thin flex-1
          ${className}
        `}
      >
        {children}
      </div>
    );
  }
);

ModalContent.displayName = 'ModalContent';

// Modal Footer Component
export const ModalFooter = forwardRef<HTMLDivElement, ModalFooterProps>(
  ({ children, className = '' }, ref) => {
    return (
      <div
        ref={ref}
        className={`
          px-6 py-4 border-t border-neutral-200 dark:border-neutral-800
          flex items-center justify-end gap-3
          ${className}
        `}
      >
        {children}
      </div>
    );
  }
);

ModalFooter.displayName = 'ModalFooter';

// Confirmation Modal Preset
export interface ConfirmModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  description?: string;
  confirmText?: string;
  cancelText?: string;
  variant?: 'danger' | 'primary';
  isLoading?: boolean;
}

export const ConfirmModal = ({
  isOpen,
  onClose,
  onConfirm,
  title,
  description,
  confirmText = 'Confirm',
  cancelText = 'Cancel',
  variant = 'primary',
  isLoading = false,
}: ConfirmModalProps) => {
  return (
    <Modal isOpen={isOpen} onClose={onClose} size="sm">
      <ModalHeader>
        <ModalTitle>{title}</ModalTitle>
        {description && <ModalDescription>{description}</ModalDescription>}
      </ModalHeader>
      <ModalFooter>
        <motion.button
          onClick={onClose}
          disabled={isLoading}
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          className="px-4 py-2 rounded-lg border-2 border-neutral-300 dark:border-neutral-700 hover:bg-neutral-100 dark:hover:bg-neutral-800 transition-colors disabled:opacity-50"
        >
          {cancelText}
        </motion.button>
        <motion.button
          onClick={onConfirm}
          disabled={isLoading}
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          className={`
            px-4 py-2 rounded-lg text-white transition-colors disabled:opacity-50
            ${variant === 'danger'
              ? 'bg-error-600 hover:bg-error-700'
              : 'bg-primary-600 hover:bg-primary-700'
            }
          `}
        >
          {isLoading ? 'Loading...' : confirmText}
        </motion.button>
      </ModalFooter>
    </Modal>
  );
};
