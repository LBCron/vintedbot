import { useState, useEffect, useMemo } from 'react';
import toast from 'react-hot-toast';
import { motion, AnimatePresence } from 'framer-motion';
import { CheckSquare, Square, Trash2, Send, Search, Filter, X, SlidersHorizontal } from 'lucide-react';
import { bulkAPI } from '../api/client';
import DraftCard from '../components/common/DraftCard';
import LoadingSpinner from '../components/common/LoadingSpinner';
import type { Draft } from '../types';
import { logger } from '../utils/logger';

export default function Drafts() {
  const [drafts, setDrafts] = useState<Draft[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false);
  const [categoryFilter, setCategoryFilter] = useState<string>('all');
  const [priceRange, setPriceRange] = useState<{ min: string; max: string }>({ min: '', max: '' });
  const [sortBy, setSortBy] = useState<'date' | 'price' | 'confidence'>('date');
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
    // Show confirmation dialog with enhanced messaging
    if (!confirm('Publier cet article sur Vinted maintenant ?\n\nCette action utilisera la nouvelle publication directe optimisée avec anti-détection.')) return;

    setPublishingId(id);

    // Show loading toast
    const loadingToast = toast.loading('Publication en cours... ⏳');

    try {
      // Use the new optimized 1-click publish endpoint
      const response = await bulkAPI.publishDraftDirect(id, 'auto');

      // Dismiss loading toast
      toast.dismiss(loadingToast);

      // Show success message with listing URL if available
      if (response.data.listing_url) {
        toast.success(
          <div>
            <strong>Annonce publiée avec succès !</strong>
            <br />
            <a
              href={response.data.listing_url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-primary-600 hover:underline font-medium mt-1 inline-block"
            >
              Voir sur Vinted →
            </a>
          </div>,
          { duration: 5000 }
        );
      } else {
        toast.success(response.data.message || 'Annonce publiée avec succès !');
      }

      // Reload drafts to update status
      loadDrafts();
    } catch (error: any) {
      // Dismiss loading toast
      toast.dismiss(loadingToast);

      // Enhanced error handling
      const errorDetail = error.response?.data?.detail;
      const errorReason = error.response?.data?.reason;

      if (errorReason?.includes('Session expirée') || errorReason?.includes('cookie')) {
        toast.error(
          <div>
            <strong>Session Vinted expirée</strong>
            <br />
            <span className="text-sm">Veuillez actualiser vos cookies Vinted dans les paramètres</span>
          </div>,
          { duration: 6000 }
        );
      } else if (errorReason?.includes('Captcha')) {
        toast.error(
          <div>
            <strong>Captcha détecté</strong>
            <br />
            <span className="text-sm">Vinted demande une vérification. Réessayez dans quelques minutes.</span>
          </div>,
          { duration: 6000 }
        );
      } else if (errorReason?.includes('photo')) {
        toast.error(
          <div>
            <strong>Erreur photos</strong>
            <br />
            <span className="text-sm">{errorReason}</span>
          </div>,
          { duration: 5000 }
        );
      } else {
        toast.error(errorDetail || errorReason || 'Échec de la publication. Veuillez réessayer.');
      }

      logger.error('Failed to publish draft', error);
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

  // Get unique categories from drafts
  const categories = useMemo(() => {
    const cats = new Set(drafts.map(d => d.category).filter(Boolean));
    return Array.from(cats).sort();
  }, [drafts]);

  // Advanced filtering and sorting
  const filteredDrafts = useMemo(() => {
    let result = [...drafts];

    // Status filter
    if (filter !== 'all') {
      result = result.filter(d => d.status === filter);
    }

    // Search query
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      result = result.filter(d =>
        d.title?.toLowerCase().includes(query) ||
        d.description?.toLowerCase().includes(query) ||
        d.brand?.toLowerCase().includes(query) ||
        d.category?.toLowerCase().includes(query)
      );
    }

    // Category filter
    if (categoryFilter !== 'all') {
      result = result.filter(d => d.category === categoryFilter);
    }

    // Price range filter
    if (priceRange.min) {
      const minPrice = parseFloat(priceRange.min);
      result = result.filter(d => d.price >= minPrice);
    }
    if (priceRange.max) {
      const maxPrice = parseFloat(priceRange.max);
      result = result.filter(d => d.price <= maxPrice);
    }

    // Sorting
    result.sort((a, b) => {
      switch (sortBy) {
        case 'price':
          return (b.price || 0) - (a.price || 0);
        case 'confidence':
          return (b.confidence || 0) - (a.confidence || 0);
        case 'date':
        default:
          return new Date(b.created_at || 0).getTime() - new Date(a.created_at || 0).getTime();
      }
    });

    return result;
  }, [drafts, filter, searchQuery, categoryFilter, priceRange, sortBy]);

  const clearFilters = () => {
    setSearchQuery('');
    setCategoryFilter('all');
    setPriceRange({ min: '', max: '' });
    setFilter('all');
    setSortBy('date');
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

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Drafts</h1>
            <p className="text-gray-600 dark:text-gray-400 mt-2">
              {filteredDrafts.length} of {drafts.length} draft{drafts.length !== 1 ? 's' : ''}
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
                className="px-4 py-2 bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700 font-medium flex items-center gap-2 transition-colors"
              >
                {selectedIds.size === filteredDrafts.length ? (
                  <CheckSquare className="w-4 h-4" />
                ) : (
                  <Square className="w-4 h-4" />
                )}
                Select All
              </button>
            )}
          </div>
        </div>

        {/* Search and Filters */}
        <div className="card p-4 space-y-4">
          <div className="flex flex-col lg:flex-row gap-3">
            {/* Search Bar */}
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type="text"
                placeholder="Search by title, description, brand..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-10 py-2.5 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all"
              />
              {searchQuery && (
                <button
                  onClick={() => setSearchQuery('')}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                >
                  <X className="w-5 h-5" />
                </button>
              )}
            </div>

            {/* Status Filters */}
            <div className="flex gap-2">
              {['all', 'ready', 'published', 'draft'].map((status) => (
                <button
                  key={status}
                  onClick={() => setFilter(status)}
                  className={`px-4 py-2.5 rounded-lg font-medium transition-all ${
                    filter === status
                      ? 'bg-gradient-to-r from-primary-600 to-primary-700 text-white shadow-md'
                      : 'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700'
                  }`}
                >
                  {status.charAt(0).toUpperCase() + status.slice(1)}
                </button>
              ))}
            </div>

            {/* Advanced Filters Toggle */}
            <button
              onClick={() => setShowAdvancedFilters(!showAdvancedFilters)}
              className={`px-4 py-2.5 rounded-lg font-medium flex items-center gap-2 transition-all ${
                showAdvancedFilters
                  ? 'bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-400'
                  : 'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700'
              }`}
            >
              <SlidersHorizontal className="w-4 h-4" />
              Filters
            </button>
          </div>

          {/* Advanced Filters */}
          <AnimatePresence>
            {showAdvancedFilters && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: 'auto', opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                transition={{ duration: 0.2 }}
                className="overflow-hidden"
              >
                <div className="pt-4 border-t border-gray-200 dark:border-gray-700 space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {/* Category Filter */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Category
                      </label>
                      <select
                        value={categoryFilter}
                        onChange={(e) => setCategoryFilter(e.target.value)}
                        className="w-full px-3 py-2 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                      >
                        <option value="all">All Categories</option>
                        {categories.map((cat) => (
                          <option key={cat} value={cat}>{cat}</option>
                        ))}
                      </select>
                    </div>

                    {/* Price Range */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Price Range (€)
                      </label>
                      <div className="flex gap-2">
                        <input
                          type="number"
                          placeholder="Min"
                          value={priceRange.min}
                          onChange={(e) => setPriceRange({ ...priceRange, min: e.target.value })}
                          className="w-full px-3 py-2 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                        />
                        <input
                          type="number"
                          placeholder="Max"
                          value={priceRange.max}
                          onChange={(e) => setPriceRange({ ...priceRange, max: e.target.value })}
                          className="w-full px-3 py-2 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                        />
                      </div>
                    </div>

                    {/* Sort By */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Sort By
                      </label>
                      <select
                        value={sortBy}
                        onChange={(e) => setSortBy(e.target.value as any)}
                        className="w-full px-3 py-2 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                      >
                        <option value="date">Date (Newest)</option>
                        <option value="price">Price (Highest)</option>
                        <option value="confidence">AI Confidence</option>
                      </select>
                    </div>
                  </div>

                  {/* Clear Filters */}
                  {(searchQuery || categoryFilter !== 'all' || priceRange.min || priceRange.max || filter !== 'all' || sortBy !== 'date') && (
                    <div className="flex justify-end">
                      <button
                        onClick={clearFilters}
                        className="px-4 py-2 text-sm font-medium text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white flex items-center gap-2 transition-colors"
                      >
                        <X className="w-4 h-4" />
                        Clear All Filters
                      </button>
                    </div>
                  )}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
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
