import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Grid3x3,
  List,
  Plus,
  Search,
  Eye,
  Heart,
  Clock,
  CheckCircle2,
  Trash2,
  Edit3,
  Copy,
  MoreVertical,
  Image as ImageIcon,
  TrendingUp,
  Calendar,
  Package,
  Send,
  X,
  Filter as FilterIcon,
  SlidersHorizontal
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { cn, formatPrice, formatDate } from '@/lib/utils';
import toast from 'react-hot-toast';
import { bulkAPI } from '@/api/client';
import { logger } from '@/utils/logger';
import type { Draft } from '@/types';

type ViewMode = 'grid' | 'list';
type FilterStatus = 'all' | 'draft' | 'ready' | 'published';

export default function Drafts() {
  const navigate = useNavigate();
  const [viewMode, setViewMode] = useState<ViewMode>('grid');
  const [filterStatus, setFilterStatus] = useState<FilterStatus>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [drafts, setDrafts] = useState<Draft[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedDrafts, setSelectedDrafts] = useState<string[]>([]);
  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false);
  const [categoryFilter, setCategoryFilter] = useState<string>('all');
  const [priceRange, setPriceRange] = useState<{ min: string; max: string }>({ min: '', max: '' });

  useEffect(() => {
    loadDrafts();
  }, [filterStatus]);

  const loadDrafts = async () => {
    try {
      setLoading(true);
      const params = filterStatus !== 'all' ? { status: filterStatus } : {};
      const response = await bulkAPI.getDrafts(params);
      setDrafts(response.data.drafts);
    } catch (error) {
      logger.error('Failed to load drafts', error);
      toast.error('Erreur lors du chargement des brouillons');
    } finally {
      setLoading(false);
    }
  };

  const filteredDrafts = drafts.filter(draft => {
    const matchesStatus = filterStatus === 'all' || draft.status === filterStatus;
    const matchesSearch = searchQuery === '' ||
      draft.title?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      draft.description?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      draft.brand?.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCategory = categoryFilter === 'all' || draft.category === categoryFilter;

    let matchesPrice = true;
    if (priceRange.min) {
      matchesPrice = matchesPrice && (draft.price || 0) >= parseFloat(priceRange.min);
    }
    if (priceRange.max) {
      matchesPrice = matchesPrice && (draft.price || 0) <= parseFloat(priceRange.max);
    }

    return matchesStatus && matchesSearch && matchesCategory && matchesPrice;
  });

  const statusCounts = {
    all: drafts.length,
    draft: drafts.filter(d => d.status === 'draft').length,
    ready: drafts.filter(d => d.status === 'ready').length,
    published: drafts.filter(d => d.status === 'published').length,
  };

  const categories = Array.from(new Set(drafts.map(d => d.category).filter(Boolean)));

  const handleBulkAction = async (action: 'publish' | 'delete' | 'duplicate') => {
    if (selectedDrafts.length === 0) {
      toast.error('Sélectionnez au moins un brouillon');
      return;
    }

    if (action === 'delete') {
      if (!confirm(`Supprimer ${selectedDrafts.length} brouillon(s) ?`)) return;

      try {
        // Use Promise.allSettled to handle partial failures
        const results = await Promise.allSettled(
          selectedDrafts.map(id => bulkAPI.deleteDraft(id))
        );

        const failed = results.filter(r => r.status === 'rejected').length;
        const succeeded = results.length - failed;

        if (failed > 0) {
          toast.error(`${failed} brouillon(s) non supprimé(s), ${succeeded} supprimé(s)`);
        } else {
          toast.success(`${selectedDrafts.length} brouillon(s) supprimé(s)`);
        }

        setSelectedDrafts([]);
        await loadDrafts(); // Wait for reload
      } catch (error) {
        toast.error('Erreur lors de la suppression');
      }
    } else if (action === 'publish') {
      try {
        // Wait for the promise to complete before clearing selection
        await toast.promise(
          Promise.all(selectedDrafts.map(id => bulkAPI.publishDraftDirect(id, 'auto'))),
          {
            loading: `Publication de ${selectedDrafts.length} brouillon(s)...`,
            success: `${selectedDrafts.length} brouillon(s) publié(s) !`,
            error: 'Erreur lors de la publication'
          }
        );
        setSelectedDrafts([]);
        await loadDrafts(); // Wait for reload
      } catch (error) {
        // Error already handled by toast.promise
        logger.error('Bulk publish failed', error);
      }
    }
  };

  const toggleSelect = (id: string) => {
    setSelectedDrafts(prev =>
      prev.includes(id)
        ? prev.filter(dId => dId !== id)
        : [...prev, id]
    );
  };

  const toggleSelectAll = () => {
    if (selectedDrafts.length === filteredDrafts.length) {
      setSelectedDrafts([]);
    } else {
      setSelectedDrafts(filteredDrafts.map(d => d.id));
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-brand-600 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-gray-600">Chargement des brouillons...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 -m-8">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-6 py-6">
          <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 mb-1">Brouillons</h1>
              <p className="text-gray-600">
                {filteredDrafts.length} brouillon(s) • {selectedDrafts.length} sélectionné(s)
              </p>
            </div>

            <div className="flex items-center gap-3">
              {/* View Mode Toggle */}
              <div className="flex bg-gray-100 rounded-xl p-1">
                <button
                  onClick={() => setViewMode('grid')}
                  className={cn(
                    "p-2 rounded-lg transition-all",
                    viewMode === 'grid'
                      ? "bg-white shadow-sm text-brand-600"
                      : "text-gray-600 hover:text-gray-900"
                  )}
                >
                  <Grid3x3 className="w-5 h-5" />
                </button>
                <button
                  onClick={() => setViewMode('list')}
                  className={cn(
                    "p-2 rounded-lg transition-all",
                    viewMode === 'list'
                      ? "bg-white shadow-sm text-brand-600"
                      : "text-gray-600 hover:text-gray-900"
                  )}
                >
                  <List className="w-5 h-5" />
                </button>
              </div>

              <button
                onClick={() => navigate('/upload')}
                className="bg-gradient-to-r from-brand-600 to-purple-600 text-white px-6 py-3 rounded-xl font-semibold shadow-lg hover:shadow-xl transition-all flex items-center gap-2"
              >
                <Plus className="w-5 h-5" />
                Nouveau
              </button>
            </div>
          </div>

          {/* Search & Filters */}
          <div className="flex flex-col md:flex-row gap-4 mt-6">
            {/* Search */}
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Rechercher un brouillon..."
                className="w-full pl-10 pr-4 py-3 bg-gray-50 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent"
              />
            </div>

            {/* Status Filter */}
            <div className="flex gap-2 overflow-x-auto pb-2">
              {(['all', 'draft', 'ready', 'published'] as FilterStatus[]).map(status => (
                <button
                  key={status}
                  onClick={() => setFilterStatus(status)}
                  className={cn(
                    "px-4 py-2 rounded-xl text-sm font-medium whitespace-nowrap transition-all",
                    filterStatus === status
                      ? "bg-brand-600 text-white shadow-md"
                      : "bg-white text-gray-700 hover:bg-gray-50 border border-gray-200"
                  )}
                >
                  {status === 'all' ? 'Tous' : status.charAt(0).toUpperCase() + status.slice(1)}
                  <span className="ml-2 opacity-75">({statusCounts[status]})</span>
                </button>
              ))}
            </div>

            <button
              onClick={() => setShowAdvancedFilters(!showAdvancedFilters)}
              className={cn(
                "px-4 py-2 rounded-xl font-medium flex items-center gap-2 transition-all",
                showAdvancedFilters
                  ? "bg-brand-100 text-brand-700"
                  : "bg-white text-gray-700 hover:bg-gray-50 border border-gray-200"
              )}
            >
              <SlidersHorizontal className="w-4 h-4" />
              Filtres
            </button>
          </div>

          {/* Advanced Filters */}
          <AnimatePresence>
            {showAdvancedFilters && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: 'auto', opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                className="overflow-hidden mt-4"
              >
                <div className="bg-gray-50 rounded-xl p-4 grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Catégorie
                    </label>
                    <select
                      value={categoryFilter}
                      onChange={(e) => setCategoryFilter(e.target.value)}
                      className="w-full px-3 py-2 bg-white border border-gray-200 rounded-lg"
                    >
                      <option value="all">Toutes</option>
                      {categories.map(cat => (
                        <option key={cat} value={cat}>{cat}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Prix min (€)
                    </label>
                    <input
                      type="number"
                      value={priceRange.min}
                      onChange={(e) => setPriceRange({ ...priceRange, min: e.target.value })}
                      className="w-full px-3 py-2 bg-white border border-gray-200 rounded-lg"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Prix max (€)
                    </label>
                    <input
                      type="number"
                      value={priceRange.max}
                      onChange={(e) => setPriceRange({ ...priceRange, max: e.target.value })}
                      className="w-full px-3 py-2 bg-white border border-gray-200 rounded-lg"
                    />
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Bulk Actions */}
          <AnimatePresence>
            {selectedDrafts.length > 0 && (
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className="mt-4 bg-brand-50 border border-brand-200 rounded-xl p-4 flex items-center justify-between"
              >
                <div className="flex items-center gap-4">
                  <span className="text-brand-700 font-medium">
                    {selectedDrafts.length} sélectionné(s)
                  </span>
                  <button
                    onClick={toggleSelectAll}
                    className="text-sm text-brand-600 hover:text-brand-700"
                  >
                    {selectedDrafts.length === filteredDrafts.length ? 'Tout désélectionner' : 'Tout sélectionner'}
                  </button>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => handleBulkAction('publish')}
                    className="px-4 py-2 bg-brand-600 text-white rounded-lg hover:bg-brand-700 transition-colors text-sm font-medium flex items-center gap-2"
                  >
                    <Send className="w-4 h-4" />
                    Publier
                  </button>
                  <button
                    onClick={() => handleBulkAction('delete')}
                    className="px-4 py-2 bg-error-50 text-error-600 rounded-lg hover:bg-error-100 transition-colors text-sm font-medium flex items-center gap-2"
                  >
                    <Trash2 className="w-4 h-4" />
                    Supprimer
                  </button>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-6 py-8">
        {filteredDrafts.length === 0 ? (
          <EmptyState searchQuery={searchQuery} />
        ) : viewMode === 'grid' ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {filteredDrafts.map((draft, index) => (
              <DraftCardGrid
                key={draft.id}
                draft={draft}
                index={index}
                isSelected={selectedDrafts.includes(draft.id)}
                onSelect={() => toggleSelect(draft.id)}
              />
            ))}
          </div>
        ) : (
          <div className="space-y-3">
            {filteredDrafts.map((draft, index) => (
              <DraftCardList
                key={draft.id}
                draft={draft}
                index={index}
                isSelected={selectedDrafts.includes(draft.id)}
                onSelect={() => toggleSelect(draft.id)}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function DraftCardGrid({ draft, index, isSelected, onSelect }: any) {
  const navigate = useNavigate();

  const statusConfig = {
    draft: { color: 'bg-gray-100 text-gray-700', label: 'Brouillon' },
    ready: { color: 'bg-blue-100 text-blue-700', label: 'Prêt' },
    published: { color: 'bg-success-100 text-success-700', label: 'Publié' },
  };

  const config = statusConfig[draft.status as keyof typeof statusConfig] || statusConfig.draft;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05 }}
      whileHover={{ y: -4 }}
      className={cn(
        "bg-white rounded-2xl border-2 overflow-hidden transition-all cursor-pointer group",
        isSelected
          ? "border-brand-500 shadow-lg ring-2 ring-brand-200"
          : "border-gray-200 hover:border-brand-200 hover:shadow-md"
      )}
    >
      {/* Image */}
      <div className="relative aspect-square bg-gray-100 overflow-hidden">
        <img
          src={draft.photos?.[0]?.url || '/placeholder.jpg'}
          alt={draft.title || 'Draft'}
          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
          onClick={() => navigate(`/drafts/${draft.id}`)}
        />

        {/* Checkbox */}
        <div className="absolute top-3 left-3">
          <button
            onClick={(e) => {
              e.stopPropagation();
              onSelect();
            }}
            className={cn(
              "w-6 h-6 rounded-lg border-2 transition-all",
              isSelected
                ? "bg-brand-600 border-brand-600"
                : "bg-white/90 backdrop-blur-sm border-white hover:border-brand-400"
            )}
          >
            {isSelected && <CheckCircle2 className="w-full h-full text-white p-0.5" />}
          </button>
        </div>

        {/* Status Badge */}
        <div className="absolute top-3 right-3">
          <span className={cn(
            "px-3 py-1 rounded-full text-xs font-semibold backdrop-blur-sm",
            config.color
          )}>
            {config.label}
          </span>
        </div>
      </div>

      {/* Content */}
      <div className="p-4" onClick={() => navigate(`/drafts/${draft.id}`)}>
        <h3 className="font-semibold text-gray-900 line-clamp-2 mb-2 group-hover:text-brand-600 transition-colors">
          {draft.title || 'Sans titre'}
        </h3>

        <p className="text-sm text-gray-600 line-clamp-2 mb-3">
          {draft.description || 'Pas de description'}
        </p>

        <div className="flex items-center justify-between">
          <span className="text-2xl font-bold text-gray-900">
            {formatPrice(draft.price || 0)}
          </span>
          {draft.confidence && (
            <div className="flex items-center gap-1 bg-brand-50 text-brand-700 px-2 py-1 rounded-lg">
              <TrendingUp className="w-4 h-4" />
              <span className="text-sm font-semibold">{(draft.confidence * 10).toFixed(1)}/10</span>
            </div>
          )}
        </div>

        <div className="mt-3 flex items-center gap-2 text-xs text-gray-500">
          <Calendar className="w-3 h-3" />
          {draft.created_at ? formatDate(new Date(draft.created_at)) : 'Date inconnue'}
        </div>
      </div>
    </motion.div>
  );
}

function DraftCardList({ draft, index, isSelected, onSelect }: any) {
  const navigate = useNavigate();

  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.03 }}
      className={cn(
        "bg-white rounded-xl border-2 p-4 transition-all cursor-pointer hover:shadow-md",
        isSelected
          ? "border-brand-500 shadow-md ring-2 ring-brand-200"
          : "border-gray-200 hover:border-brand-200"
      )}
      onClick={() => navigate(`/drafts/${draft.id}`)}
    >
      <div className="flex items-center gap-4">
        {/* Checkbox */}
        <button
          onClick={(e) => {
            e.stopPropagation();
            onSelect();
          }}
          className={cn(
            "w-6 h-6 rounded-lg border-2 flex-shrink-0 transition-all",
            isSelected
              ? "bg-brand-600 border-brand-600"
              : "bg-white border-gray-300 hover:border-brand-400"
          )}
        >
          {isSelected && <CheckCircle2 className="w-full h-full text-white p-0.5" />}
        </button>

        {/* Image */}
        <div className="w-20 h-20 rounded-xl bg-gray-100 overflow-hidden flex-shrink-0">
          <img
            src={draft.photos?.[0]?.url || '/placeholder.jpg'}
            alt={draft.title || 'Draft'}
            className="w-full h-full object-cover"
          />
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <h3 className="font-semibold text-gray-900 truncate mb-1">
            {draft.title || 'Sans titre'}
          </h3>
          <p className="text-sm text-gray-600 line-clamp-1 mb-2">
            {draft.description || 'Pas de description'}
          </p>
          <div className="flex items-center gap-4 text-sm text-gray-500">
            <span className="flex items-center gap-1">
              <Calendar className="w-4 h-4" />
              {draft.created_at ? formatDate(new Date(draft.created_at)) : 'Date inconnue'}
            </span>
          </div>
        </div>

        {/* Price & Status */}
        <div className="flex items-center gap-4 flex-shrink-0">
          <div className="text-right">
            <div className="text-2xl font-bold text-gray-900">
              {formatPrice(draft.price || 0)}
            </div>
            {draft.confidence && (
              <div className="text-sm text-brand-600 font-semibold">
                Score: {(draft.confidence * 10).toFixed(1)}/10
              </div>
            )}
          </div>
        </div>
      </div>
    </motion.div>
  );
}

function EmptyState({ searchQuery }: { searchQuery: string }) {
  const navigate = useNavigate();

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      className="text-center py-20"
    >
      <div className="w-32 h-32 bg-gradient-to-br from-gray-100 to-gray-200 rounded-full flex items-center justify-center mx-auto mb-6">
        <ImageIcon className="w-16 h-16 text-gray-400" />
      </div>
      {searchQuery ? (
        <>
          <h3 className="text-2xl font-bold text-gray-900 mb-2">
            Aucun résultat
          </h3>
          <p className="text-gray-600 mb-6">
            Aucun brouillon ne correspond à "{searchQuery}"
          </p>
        </>
      ) : (
        <>
          <h3 className="text-2xl font-bold text-gray-900 mb-2">
            Aucun brouillon
          </h3>
          <p className="text-gray-600 mb-6">
            Commencez par uploader des photos pour créer votre premier brouillon
          </p>
          <button
            onClick={() => navigate('/upload')}
            className="bg-gradient-to-r from-brand-600 to-purple-600 text-white text-lg px-8 py-3 rounded-xl font-semibold shadow-lg hover:shadow-xl transition-all inline-flex items-center gap-2"
          >
            <Plus className="w-5 h-5" />
            Créer mon premier brouillon
          </button>
        </>
      )}
    </motion.div>
  );
}
