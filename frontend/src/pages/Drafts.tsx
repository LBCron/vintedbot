import { useState, useEffect } from 'react';
import toast from 'react-hot-toast';
import { motion, AnimatePresence } from 'framer-motion';
import { CheckSquare, Square, Trash2, Send } from 'lucide-react';
import { bulkAPI } from '../api/client';
import DraftCard from '../components/common/DraftCard';
import LoadingSpinner from '../components/common/LoadingSpinner';
import type { Draft } from '../types';
import { logger } from '../utils/logger';

export default function Drafts() {
  const [drafts, setDrafts] = useState<Draft[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string>('all');
  const [publishingId, setPublishingId] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [bulkProcessing, setBulkProcessing] = useState(false);

  useEffect(() => {
    loadDrafts();
  }, [filter]);

  const loadDrafts = async () => {
    try {
      const params = filter !== 'all' ? { status: filter } : {};
      const response = await bulkAPI.getDrafts(params);
      setDrafts(response.data.drafts);
    } catch (error) {
      logger.error('Failed to load drafts', error);
    } finally {
      setLoading(false);
    }
  };

  const handlePublish = async (id: string) => {
    if (!confirm('Publish this draft to Vinted?')) return;

    setPublishingId(id);
    try {
      await bulkAPI.publishDraft(id);
      toast.success('Draft published successfully!');
      loadDrafts();
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to publish draft');
    } finally {
      setPublishingId(null);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Delete this draft?')) return;

    setDeletingId(id);
    try {
      await bulkAPI.deleteDraft(id);
      toast.success('Draft deleted successfully!');
      loadDrafts();
    } catch (error) {
      toast.error('Failed to delete draft');
    } finally {
      setDeletingId(null);
    }
  };

  const toggleSelection = (id: string) => {
    setSelectedIds(prev => {
      const newSet = new Set(prev);
      if (newSet.has(id)) {
        newSet.delete(id);
      } else {
        newSet.add(id);
      }
      return newSet;
    });
  };

  const toggleSelectAll = () => {
    if (selectedIds.size === filteredDrafts.length) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(filteredDrafts.map(d => d.id)));
    }
  };

  const handleBulkPublish = async () => {
    const count = selectedIds.size;
    if (count === 0) return;
    if (!confirm(`Publish ${count} draft${count > 1 ? 's' : ''} to Vinted?`)) return;

    setBulkProcessing(true);
    let successCount = 0;
    let errorCount = 0;

    for (const id of selectedIds) {
      try {
        await bulkAPI.publishDraft(id);
        successCount++;
      } catch (error) {
        errorCount++;
        logger.error(`Failed to publish draft ${id}`, error);
      }
    }

    if (successCount > 0) {
      toast.success(`${successCount} draft${successCount > 1 ? 's' : ''} published successfully!`);
    }
    if (errorCount > 0) {
      toast.error(`Failed to publish ${errorCount} draft${errorCount > 1 ? 's' : ''}`);
    }

    setSelectedIds(new Set());
    setBulkProcessing(false);
    loadDrafts();
  };

  const handleBulkDelete = async () => {
    const count = selectedIds.size;
    if (count === 0) return;
    if (!confirm(`Delete ${count} draft${count > 1 ? 's' : ''}?`)) return;

    setBulkProcessing(true);
    let successCount = 0;
    let errorCount = 0;

    for (const id of selectedIds) {
      try {
        await bulkAPI.deleteDraft(id);
        successCount++;
      } catch (error) {
        errorCount++;
        logger.error(`Failed to delete draft ${id}`, error);
      }
    }

    if (successCount > 0) {
      toast.success(`${successCount} draft${successCount > 1 ? 's' : ''} deleted successfully!`);
    }
    if (errorCount > 0) {
      toast.error(`Failed to delete ${errorCount} draft${errorCount > 1 ? 's' : ''}`);
    }

    setSelectedIds(new Set());
    setBulkProcessing(false);
    loadDrafts();
  };

  const filteredDrafts = drafts;

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">📋 Drafts</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-2">
            {drafts.length} draft{drafts.length !== 1 ? 's' : ''} total
            {selectedIds.size > 0 && (
              <span className="ml-2 text-primary-600 dark:text-primary-400 font-medium">
                • {selectedIds.size} selected
              </span>
            )}
          </p>
        </div>

        <div className="flex gap-2 flex-wrap">
          {filteredDrafts.length > 0 && (
            <button
              onClick={toggleSelectAll}
              className="px-4 py-2 bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700 font-medium flex items-center gap-2"
            >
              {selectedIds.size === filteredDrafts.length ? (
                <CheckSquare className="w-4 h-4" />
              ) : (
                <Square className="w-4 h-4" />
              )}
              Select All
            </button>
          )}
          <button
            onClick={() => setFilter('all')}
            className={`px-4 py-2 rounded-lg font-medium ${
              filter === 'all'
                ? 'bg-primary-600 text-white'
                : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600'
            }`}
          >
            All
          </button>
          <button
            onClick={() => setFilter('ready')}
            className={`px-4 py-2 rounded-lg font-medium ${
              filter === 'ready'
                ? 'bg-primary-600 text-white'
                : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600'
            }`}
          >
            Ready
          </button>
          <button
            onClick={() => setFilter('published')}
            className={`px-4 py-2 rounded-lg font-medium ${
              filter === 'published'
                ? 'bg-primary-600 text-white'
                : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600'
            }`}
          >
            Published
          </button>
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-64">
          <LoadingSpinner size="large" />
        </div>
      ) : filteredDrafts.length === 0 ? (
        <div className="card text-center py-12">
          <p className="text-gray-600 dark:text-gray-400">No drafts found</p>
        </div>
      ) : (
        <>
          <motion.div
            className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.3 }}
          >
            {filteredDrafts.map((draft, index) => (
              <motion.div
                key={draft.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.05, duration: 0.3 }}
              >
                <DraftCard
                  draft={draft}
                  onPublish={draft.status !== 'published' ? handlePublish : undefined}
                  onDelete={handleDelete}
                  isSelected={selectedIds.has(draft.id)}
                  onToggleSelect={() => toggleSelection(draft.id)}
                />
              </motion.div>
            ))}
          </motion.div>

          {/* Bulk Action Bar */}
          <AnimatePresence>
            {selectedIds.size > 0 && (
              <motion.div
                initial={{ y: 100, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                exit={{ y: 100, opacity: 0 }}
                transition={{ type: "spring", stiffness: 300, damping: 30 }}
                className="fixed bottom-0 left-0 right-0 bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 shadow-lg z-50"
              >
              <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
                <div className="flex items-center justify-between gap-4">
                  <div className="flex items-center gap-4">
                    <p className="text-sm font-medium text-gray-900 dark:text-white">
                      {selectedIds.size} draft{selectedIds.size > 1 ? 's' : ''} selected
                    </p>
                    <button
                      onClick={() => setSelectedIds(new Set())}
                      className="text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white"
                    >
                      Clear selection
                    </button>
                  </div>

                  <div className="flex gap-3">
                    <button
                      onClick={handleBulkDelete}
                      disabled={bulkProcessing}
                      className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 font-medium"
                    >
                      {bulkProcessing ? (
                        <LoadingSpinner size="small" />
                      ) : (
                        <Trash2 className="w-4 h-4" />
                      )}
                      Delete Selected
                    </button>
                    <button
                      onClick={handleBulkPublish}
                      disabled={bulkProcessing}
                      className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 font-medium"
                    >
                      {bulkProcessing ? (
                        <LoadingSpinner size="small" />
                      ) : (
                        <Send className="w-4 h-4" />
                      )}
                      Publish Selected
                    </button>
                  </div>
                </div>
              </div>
              </motion.div>
            )}
          </AnimatePresence>
        </>
      )}
    </div>
  );
}
