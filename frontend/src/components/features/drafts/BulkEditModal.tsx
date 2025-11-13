import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Check, AlertTriangle, Sparkles } from 'lucide-react';
import { Dialog } from '@headlessui/react';

interface BulkEditModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (changes: BulkEditChanges) => void;
  selectedCount: number;
}

export interface BulkEditChanges {
  category?: string;
  brand?: string;
  condition?: string;
  priceAdjustment?: {
    type: 'increase' | 'decrease' | 'set';
    value: number;
  };
  tags?: {
    action: 'add' | 'remove' | 'replace';
    tags: string[];
  };
}

const CATEGORIES = [
  'Hoodies',
  'T-shirts',
  'Jeans',
  'Sneakers',
  'Jackets',
  'Dresses',
  'Bags',
  'Accessories',
];

const CONDITIONS = [
  'Neuf avec étiquette',
  'Très bon état',
  'Bon état',
  'État satisfaisant',
];

export default function BulkEditModal({
  isOpen,
  onClose,
  onSave,
  selectedCount,
}: BulkEditModalProps) {
  const [changes, setChanges] = useState<BulkEditChanges>({});
  const [priceType, setPriceType] = useState<'increase' | 'decrease' | 'set'>('increase');
  const [priceValue, setPriceValue] = useState<string>('');
  const [tagsAction, setTagsAction] = useState<'add' | 'remove' | 'replace'>('add');
  const [tagsInput, setTagsInput] = useState<string>('');

  const handleSave = () => {
    const finalChanges: BulkEditChanges = { ...changes };

    // Add price adjustment if set
    if (priceValue) {
      finalChanges.priceAdjustment = {
        type: priceType,
        value: parseFloat(priceValue),
      };
    }

    // Add tags if set
    if (tagsInput) {
      finalChanges.tags = {
        action: tagsAction,
        tags: tagsInput.split(',').map((tag) => tag.trim()),
      };
    }

    onSave(finalChanges);
    onClose();
  };

  const hasChanges =
    Object.keys(changes).length > 0 || priceValue !== '' || tagsInput !== '';

  return (
    <AnimatePresence>
      {isOpen && (
        <Dialog
          as={motion.div}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          open={isOpen}
          onClose={onClose}
          className="relative z-50"
        >
          {/* Backdrop */}
          <div className="fixed inset-0 bg-black/50" aria-hidden="true" />

          {/* Modal */}
          <div className="fixed inset-0 flex items-center justify-center p-4">
            <Dialog.Panel
              as={motion.div}
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="w-full max-w-2xl bg-white dark:bg-gray-900 rounded-xl shadow-2xl max-h-[90vh] overflow-hidden flex flex-col"
            >
              {/* Header */}
              <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-gray-800">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-primary-500 to-purple-500 flex items-center justify-center">
                    <Sparkles className="w-5 h-5 text-white" />
                  </div>
                  <div>
                    <Dialog.Title className="text-lg font-semibold text-gray-900 dark:text-white">
                      Bulk Edit Drafts
                    </Dialog.Title>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      Editing {selectedCount} draft{selectedCount > 1 ? 's' : ''}
                    </p>
                  </div>
                </div>

                <button
                  onClick={onClose}
                  className="p-2 text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Content */}
              <div className="flex-1 overflow-y-auto p-6 space-y-6">
                {/* Warning */}
                <div className="flex items-start gap-3 p-4 bg-warning-50 dark:bg-warning-900/20 border border-warning-200 dark:border-warning-800 rounded-lg">
                  <AlertTriangle className="w-5 h-5 text-warning-600 dark:text-warning-400 flex-shrink-0 mt-0.5" />
                  <div className="flex-1">
                    <p className="text-sm font-medium text-gray-900 dark:text-white">
                      Bulk changes will apply to all selected drafts
                    </p>
                    <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                      Only fill in the fields you want to modify. Empty fields will remain
                      unchanged.
                    </p>
                  </div>
                </div>

                {/* Category */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Category
                  </label>
                  <select
                    value={changes.category || ''}
                    onChange={(e) =>
                      setChanges({
                        ...changes,
                        category: e.target.value || undefined,
                      })
                    }
                    className="w-full px-4 py-2 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-colors"
                  >
                    <option value="">Don't change</option>
                    {CATEGORIES.map((cat) => (
                      <option key={cat} value={cat}>
                        {cat}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Brand */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Brand
                  </label>
                  <input
                    type="text"
                    value={changes.brand || ''}
                    onChange={(e) =>
                      setChanges({
                        ...changes,
                        brand: e.target.value || undefined,
                      })
                    }
                    placeholder="Leave empty to keep current brands"
                    className="w-full px-4 py-2 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-colors"
                  />
                </div>

                {/* Condition */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Condition
                  </label>
                  <select
                    value={changes.condition || ''}
                    onChange={(e) =>
                      setChanges({
                        ...changes,
                        condition: e.target.value || undefined,
                      })
                    }
                    className="w-full px-4 py-2 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-colors"
                  >
                    <option value="">Don't change</option>
                    {CONDITIONS.map((cond) => (
                      <option key={cond} value={cond}>
                        {cond}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Price Adjustment */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Price Adjustment
                  </label>
                  <div className="flex gap-2">
                    <select
                      value={priceType}
                      onChange={(e) =>
                        setPriceType(e.target.value as 'increase' | 'decrease' | 'set')
                      }
                      className="px-4 py-2 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-colors"
                    >
                      <option value="increase">Increase by</option>
                      <option value="decrease">Decrease by</option>
                      <option value="set">Set to</option>
                    </select>

                    <input
                      type="number"
                      value={priceValue}
                      onChange={(e) => setPriceValue(e.target.value)}
                      placeholder={priceType === 'set' ? 'New price' : 'Amount'}
                      min="0"
                      step="0.01"
                      className="flex-1 px-4 py-2 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-colors"
                    />

                    <div className="flex items-center px-4 py-2 bg-gray-100 dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg">
                      <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                        €
                      </span>
                    </div>
                  </div>
                  {priceValue && priceType !== 'set' && (
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
                      {priceType === 'increase' ? 'Add' : 'Subtract'} {priceValue}€{' '}
                      {priceType === 'increase' ? 'to' : 'from'} each draft's current price
                    </p>
                  )}
                </div>

                {/* Tags */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Tags
                  </label>
                  <div className="space-y-2">
                    <select
                      value={tagsAction}
                      onChange={(e) => setTagsAction(e.target.value as any)}
                      className="w-full px-4 py-2 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-colors"
                    >
                      <option value="add">Add tags</option>
                      <option value="remove">Remove tags</option>
                      <option value="replace">Replace all tags</option>
                    </select>

                    <input
                      type="text"
                      value={tagsInput}
                      onChange={(e) => setTagsInput(e.target.value)}
                      placeholder="Enter tags separated by commas (e.g., vintage, summer, casual)"
                      className="w-full px-4 py-2 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-colors"
                    />
                  </div>
                </div>
              </div>

              {/* Footer */}
              <div className="flex items-center justify-between px-6 py-4 border-t border-gray-200 dark:border-gray-800 bg-gray-50 dark:bg-gray-900">
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  {hasChanges
                    ? `Changes will be applied to ${selectedCount} draft${
                        selectedCount > 1 ? 's' : ''
                      }`
                    : 'No changes selected'}
                </p>

                <div className="flex gap-2">
                  <button
                    onClick={onClose}
                    className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleSave}
                    disabled={!hasChanges}
                    className="flex items-center gap-2 px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg transition-colors text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <Check className="w-4 h-4" />
                    Apply Changes
                  </button>
                </div>
              </div>
            </Dialog.Panel>
          </div>
        </Dialog>
      )}
    </AnimatePresence>
  );
}
