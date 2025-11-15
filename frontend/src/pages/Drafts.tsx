import { useState, useEffect, useMemo } from 'react';
import toast from 'react-hot-toast';
import { motion, AnimatePresence } from 'framer-motion';
import {
  CheckSquare,
  Square,
  Trash2,
  Send,
  Search,
  X,
  SlidersHorizontal,
  FileText,
  Package
} from 'lucide-react';
import { bulkAPI } from '../api/client';
import DraftCard from '../components/common/DraftCard';
import { GlassCard } from '../components/ui/GlassCard';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Badge } from '../components/ui/Badge';
import { EmptyState } from '../components/ui/EmptyState';
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
    if (!confirm('🚀 Publier cet article sur Vinted maintenant ?\n\nCette action utilisera la nouvelle publication directe optimisée avec anti-détection.')) return;

    setPublishingId(id);
    const loadingToast = toast.loading('Publication en cours... ⏳');

    try {
      const response = await bulkAPI.publishDraftDirect(id, 'auto');
      toast.dismiss(loadingToast);

      if (response.data.listing_url) {
        toast.success(
          <div>
            <strong>✅ Annonce publiée avec succès !</strong>
            <br />
            <a
              href={response.data.listing_url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-violet-400 hover:underline font-medium mt-1 inline-block"
            >
              Voir sur Vinted →
            </a>
          </div>,
          { duration: 5000 }
        );
      } else {
        toast.success(response.data.message || 'Annonce publiée avec succès ! 🎉');
      }

      loadDrafts();
    } catch (error: any) {
      toast.dismiss(loadingToast);
      const errorDetail = error.response?.data?.detail;
      const errorReason = error.response?.data?.reason;

      if (errorReason?.includes('Session expirée') || errorReason?.includes('cookie')) {
        toast.error(
          <div>
            <strong>❌ Session Vinted expirée</strong>
            <br />
            <span className="text-sm">Veuillez actualiser vos cookies Vinted dans les paramètres</span>
          </div>,
          { duration: 6000 }
        );
      } else if (errorReason?.includes('Captcha')) {
        toast.error(
          <div>
            <strong>⚠️ Captcha détecté</strong>
            <br />
            <span className="text-sm">Vinted demande une vérification. Réessayez dans quelques minutes.</span>
          </div>,
          { duration: 6000 }
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

  const categories = useMemo(() => {
    const cats = new Set(drafts.map(d => d.category).filter(Boolean));
    return Array.from(cats).sort();
  }, [drafts]);

  const filteredDrafts = useMemo(() => {
    let result = [...drafts];

    if (filter !== 'all') {
      result = result.filter(d => d.status === filter);
    }

    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      result = result.filter(d =>
        d.title?.toLowerCase().includes(query) ||
        d.description?.toLowerCase().includes(query) ||
        d.brand?.toLowerCase().includes(query) ||
        d.category?.toLowerCase().includes(query)
      );
    }

    if (categoryFilter !== 'all') {
      result = result.filter(d => d.category === categoryFilter);
    }

    if (priceRange.min) {
      const minPrice = parseFloat(priceRange.min);
      result = result.filter(d => d.price >= minPrice);
    }
    if (priceRange.max) {
      const maxPrice = parseFloat(priceRange.max);
      result = result.filter(d => d.price <= maxPrice);
    }

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
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      <div className="max-w-7xl mx-auto p-4 md:p-6 lg:p-8 space-y-6">
        {/* Header */}
        <motion.div
          className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4"
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <div>
            <h1 className="text-4xl md:text-5xl font-bold bg-gradient-to-r from-white via-violet-200 to-purple-200 bg-clip-text text-transparent">
              Drafts
            </h1>
            <div className="flex items-center gap-3 mt-2">
              <p className="text-lg text-slate-400">
                {filteredDrafts.length} of {drafts.length} draft{drafts.length !== 1 ? 's' : ''}
              </p>
              {selectedIds.size > 0 && (
                <Badge variant="info" size="md">
                  {selectedIds.size} selected
                </Badge>
              )}
            </div>
          </div>

          <div className="flex gap-2 flex-wrap">
            {filteredDrafts.length > 0 && (
              <Button
                onClick={toggleSelectAll}
                variant="outline"
                icon={selectedIds.size === filteredDrafts.length ? CheckSquare : Square}
              >
                Select All
              </Button>
            )}
          </div>
        </motion.div>

        {/* Search and Filters */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <GlassCard className="p-6 space-y-4">
            <div className="flex flex-col lg:flex-row gap-3">
              {/* Search Bar */}
              <div className="flex-1">
                <Input
                  type="text"
                  placeholder="Search by title, description, brand..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  icon={Search}
                />
              </div>

              {/* Status Filters */}
              <div className="flex gap-2 flex-wrap">
                {['all', 'ready', 'published', 'draft'].map((status) => (
                  <motion.button
                    key={status}
                    onClick={() => setFilter(status)}
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    className={`px-4 py-2.5 rounded-xl font-semibold transition-all ${
                      filter === status
                        ? 'bg-gradient-to-r from-violet-500 to-purple-600 text-white shadow-lg shadow-violet-500/30'
                        : 'bg-white/5 text-slate-300 hover:bg-white/10 border border-white/10'
                    }`}
                  >
                    {status.charAt(0).toUpperCase() + status.slice(1)}
                  </motion.button>
                ))}
              </div>

              {/* Advanced Filters Toggle */}
              <Button
                onClick={() => setShowAdvancedFilters(!showAdvancedFilters)}
                variant={showAdvancedFilters ? 'primary' : 'ghost'}
                icon={SlidersHorizontal}
              >
                Filters
              </Button>
            </div>

            {/* Advanced Filters */}
            <AnimatePresence>
              {showAdvancedFilters && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  transition={{ duration: 0.3 }}
                  className="overflow-hidden"
                >
                  <div className="pt-4 border-t border-white/10 space-y-4">
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      {/* Category Filter */}
                      <div>
                        <label className="block text-sm font-medium text-slate-300 mb-2">
                          Category
                        </label>
                        <select
                          value={categoryFilter}
                          onChange={(e) => setCategoryFilter(e.target.value)}
                          className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white focus:outline-none focus:border-violet-500/50 focus:bg-white/10 transition-all"
                        >
                          <option value="all">All Categories</option>
                          {categories.map((cat) => (
                            <option key={cat} value={cat}>{cat}</option>
                          ))}
                        </select>
                      </div>

                      {/* Price Range */}
                      <div>
                        <label className="block text-sm font-medium text-slate-300 mb-2">
                          Price Range (€)
                        </label>
                        <div className="flex gap-2">
                          <input
                            type="number"
                            placeholder="Min"
                            value={priceRange.min}
                            onChange={(e) => setPriceRange({ ...priceRange, min: e.target.value })}
                            className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder:text-slate-500 focus:outline-none focus:border-violet-500/50 focus:bg-white/10 transition-all"
                          />
                          <input
                            type="number"
                            placeholder="Max"
                            value={priceRange.max}
                            onChange={(e) => setPriceRange({ ...priceRange, max: e.target.value })}
                            className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder:text-slate-500 focus:outline-none focus:border-violet-500/50 focus:bg-white/10 transition-all"
                          />
                        </div>
                      </div>

                      {/* Sort By */}
                      <div>
                        <label className="block text-sm font-medium text-slate-300 mb-2">
                          Sort By
                        </label>
                        <select
                          value={sortBy}
                          onChange={(e) => setSortBy(e.target.value as any)}
                          className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white focus:outline-none focus:border-violet-500/50 focus:bg-white/10 transition-all"
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
                          className="px-4 py-2 text-sm font-medium text-slate-400 hover:text-white flex items-center gap-2 transition-colors"
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
          </GlassCard>
        </motion.div>

        {/* Content */}
        {loading ? (
          <GlassCard className="p-12">
            <div className="flex flex-col items-center justify-center space-y-4">
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                className="w-12 h-12 border-4 border-violet-500/30 border-t-violet-500 rounded-full"
              />
              <p className="text-slate-400">Loading drafts...</p>
            </div>
          </GlassCard>
        ) : filteredDrafts.length === 0 ? (
          <EmptyState
            icon={FileText}
            title="No drafts found"
            description={
              searchQuery || categoryFilter !== 'all' || filter !== 'all'
                ? "Try adjusting your filters to see more results"
                : "Upload photos to create your first AI-generated drafts"
            }
            action={{
              label: "Upload Photos",
              onClick: () => window.location.href = '/upload',
              icon: Package
            }}
          />
        ) : (
          <>
            <motion.div
              className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.3, delay: 0.2 }}
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
                  className="fixed bottom-0 left-0 right-0 z-50"
                >
                  <div className="backdrop-blur-xl bg-slate-900/90 border-t border-white/10 shadow-[0_-20px_50px_rgba(0,0,0,0.3)]">
                    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
                      <div className="flex items-center justify-between gap-4">
                        <div className="flex items-center gap-4">
                          <p className="text-sm font-semibold text-white">
                            {selectedIds.size} draft{selectedIds.size > 1 ? 's' : ''} selected
                          </p>
                          <button
                            onClick={() => setSelectedIds(new Set())}
                            className="text-sm text-slate-400 hover:text-white transition-colors"
                          >
                            Clear selection
                          </button>
                        </div>

                        <div className="flex gap-3">
                          <Button
                            onClick={handleBulkDelete}
                            disabled={bulkProcessing}
                            variant="danger"
                            icon={Trash2}
                            loading={bulkProcessing}
                          >
                            Delete Selected
                          </Button>
                          <Button
                            onClick={handleBulkPublish}
                            disabled={bulkProcessing}
                            variant="primary"
                            icon={Send}
                            loading={bulkProcessing}
                          >
                            Publish Selected
                          </Button>
                        </div>
                      </div>
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </>
        )}
      </div>
    </div>
  );
}
