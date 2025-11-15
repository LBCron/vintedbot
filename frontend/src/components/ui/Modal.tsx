import { motion, AnimatePresence } from 'framer-motion';
import { X } from 'lucide-react';
import { GlassCard } from './GlassCard';
import { Button } from './Button';

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
  footer?: React.ReactNode;
  size?: 'sm' | 'md' | 'lg' | 'xl';
}

const sizeMap = {
  sm: 'max-w-md',
  md: 'max-w-lg',
  lg: 'max-w-2xl',
  xl: 'max-w-4xl',
};

export function Modal({
  isOpen,
  onClose,
  title,
  children,
  footer,
  size = 'md'
}: ModalProps) {
  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
          />

          {/* Modal */}
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            <motion.div
              className={`w-full ${sizeMap[size]} relative`}
              initial={{ opacity: 0, scale: 0.9, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.9, y: 20 }}
              transition={{ type: "spring", duration: 0.5 }}
            >
              <GlassCard className="p-6" noPadding>
                {/* Header */}
                <div className="flex items-center justify-between p-6 border-b border-white/10">
                  <h2 className="text-2xl font-bold text-white">{title}</h2>
                  <button
                    onClick={onClose}
                    className="p-2 hover:bg-white/5 rounded-lg transition-colors"
                  >
                    <X className="w-5 h-5 text-slate-400" />
                  </button>
                </div>

                {/* Content */}
                <div className="p-6">
                  {children}
                </div>

                {/* Footer */}
                {footer && (
                  <div className="flex items-center justify-end space-x-3 p-6 border-t border-white/10">
                    {footer}
                  </div>
                )}
              </GlassCard>
            </motion.div>
          </div>
        </>
      )}
    </AnimatePresence>
  );
}
