import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  CheckSquare,
  Square,
  Trash2,
  Send,
  Edit,
  Copy,
  Download,
  Tag,
  DollarSign,
  X,
  ChevronDown,
} from 'lucide-react';
import { Menu } from '@headlessui/react';

interface BulkActionsProps {
  selectedCount: number;
  onSelectAll: () => void;
  onDeselectAll: () => void;
  onDelete: () => void;
  onPublish: () => void;
  onDuplicate: () => void;
  onExport: () => void;
  onBulkEdit: () => void;
  onBulkPrice: () => void;
  onBulkTag: () => void;
  totalCount: number;
}

export default function BulkActions({
  selectedCount,
  onSelectAll,
  onDeselectAll,
  onDelete,
  onPublish,
  onDuplicate,
  onExport,
  onBulkEdit,
  onBulkPrice,
  onBulkTag,
  totalCount,
}: BulkActionsProps) {
  const [showAdvanced, setShowAdvanced] = useState(false);

  const isAllSelected = selectedCount === totalCount;
  const hasSelection = selectedCount > 0;

  if (!hasSelection) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ y: 100, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        exit={{ y: 100, opacity: 0 }}
        className="fixed bottom-6 left-1/2 -translate-x-1/2 z-40"
      >
        <div className="bg-white dark:bg-gray-900 rounded-xl shadow-2xl border border-gray-200 dark:border-gray-700 p-4 min-w-[600px]">
          <div className="flex items-center gap-4">
            {/* Selection Info */}
            <div className="flex items-center gap-3">
              <button
                onClick={isAllSelected ? onDeselectAll : onSelectAll}
                className="flex items-center gap-2 px-3 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
              >
                {isAllSelected ? (
                  <CheckSquare className="w-4 h-4 text-primary-600" />
                ) : (
                  <Square className="w-4 h-4" />
                )}
                {isAllSelected ? 'Deselect All' : 'Select All'}
              </button>

              <div className="h-6 w-px bg-gray-300 dark:bg-gray-600" />

              <span className="text-sm font-medium text-gray-900 dark:text-white">
                {selectedCount} selected
              </span>
            </div>

            {/* Quick Actions */}
            <div className="flex items-center gap-2 ml-auto">
              <button
                onClick={onPublish}
                className="flex items-center gap-2 px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg transition-colors text-sm font-medium"
              >
                <Send className="w-4 h-4" />
                Publish
              </button>

              <button
                onClick={onDuplicate}
                className="flex items-center gap-2 px-4 py-2 bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg transition-colors text-sm font-medium"
              >
                <Copy className="w-4 h-4" />
                Duplicate
              </button>

              {/* More Actions Dropdown */}
              <Menu as="div" className="relative">
                <Menu.Button className="flex items-center gap-2 px-4 py-2 bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg transition-colors text-sm font-medium">
                  More
                  <ChevronDown className="w-4 h-4" />
                </Menu.Button>

                <Menu.Items className="absolute bottom-full mb-2 right-0 w-56 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-xl p-2 focus:outline-none">
                  <Menu.Item>
                    {({ active }) => (
                      <button
                        onClick={onBulkEdit}
                        className={`${
                          active ? 'bg-gray-100 dark:bg-gray-700' : ''
                        } flex items-center gap-3 w-full px-3 py-2 text-sm text-gray-700 dark:text-gray-300 rounded-md transition-colors`}
                      >
                        <Edit className="w-4 h-4" />
                        Bulk Edit Fields
                      </button>
                    )}
                  </Menu.Item>

                  <Menu.Item>
                    {({ active }) => (
                      <button
                        onClick={onBulkPrice}
                        className={`${
                          active ? 'bg-gray-100 dark:bg-gray-700' : ''
                        } flex items-center gap-3 w-full px-3 py-2 text-sm text-gray-700 dark:text-gray-300 rounded-md transition-colors`}
                      >
                        <DollarSign className="w-4 h-4" />
                        Adjust Prices
                      </button>
                    )}
                  </Menu.Item>

                  <Menu.Item>
                    {({ active }) => (
                      <button
                        onClick={onBulkTag}
                        className={`${
                          active ? 'bg-gray-100 dark:bg-gray-700' : ''
                        } flex items-center gap-3 w-full px-3 py-2 text-sm text-gray-700 dark:text-gray-300 rounded-md transition-colors`}
                      >
                        <Tag className="w-4 h-4" />
                        Manage Tags
                      </button>
                    )}
                  </Menu.Item>

                  <Menu.Item>
                    {({ active }) => (
                      <button
                        onClick={onExport}
                        className={`${
                          active ? 'bg-gray-100 dark:bg-gray-700' : ''
                        } flex items-center gap-3 w-full px-3 py-2 text-sm text-gray-700 dark:text-gray-300 rounded-md transition-colors`}
                      >
                        <Download className="w-4 h-4" />
                        Export Data
                      </button>
                    )}
                  </Menu.Item>

                  <div className="h-px bg-gray-200 dark:bg-gray-700 my-2" />

                  <Menu.Item>
                    {({ active }) => (
                      <button
                        onClick={onDelete}
                        className={`${
                          active ? 'bg-error-50 dark:bg-error-900/20' : ''
                        } flex items-center gap-3 w-full px-3 py-2 text-sm text-error-600 dark:text-error-400 rounded-md transition-colors`}
                      >
                        <Trash2 className="w-4 h-4" />
                        Delete Selected
                      </button>
                    )}
                  </Menu.Item>
                </Menu.Items>
              </Menu>

              <button
                onClick={onDeselectAll}
                className="p-2 text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
                title="Clear selection"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </motion.div>
    </AnimatePresence>
  );
}
