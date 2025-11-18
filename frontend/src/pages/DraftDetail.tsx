import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  Save,
  Trash2,
  Eye,
  Share2,
  Copy,
  Image as ImageIcon,
  Tag,
  DollarSign,
  Sparkles,
  Clock,
  History,
  X,
  Plus,
  GripVertical
} from 'lucide-react';
import { DragDropContext, Droppable, Draggable } from 'react-beautiful-dnd';
import Button from '@/components/ui/Button';
import Modal from '@/components/ui/Modal';
import Badge from '@/components/ui/Badge';
import toast from 'react-hot-toast';
import { formatPrice, formatDate } from '@/lib/utils';

export default function DraftDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [isSaving, setIsSaving] = useState(false);
  const [showPreview, setShowPreview] = useState(false);
  const [showHistory, setShowHistory] = useState(false);

  const [draft, setDraft] = useState({
    id: id,
    title: "Jean Levi's 501 Original - Comme neuf",
    description: "Magnifique jean Levi's 501 en excellent état. Porté seulement quelques fois. Taille W32 L34. Couleur bleu foncé classique. Aucun défaut, aucune tache. Parfait pour un look casual.\n\nMarque: Levi's\nModèle: 501 Original\nTaille: W32 L34\nCouleur: Bleu foncé\nÉtat: Comme neuf",
    price: 45,
    images: [
      '/placeholder1.jpg',
      '/placeholder2.jpg',
      '/placeholder3.jpg'
    ],
    category: 'Vêtements',
    brand: "Levi's",
    size: 'W32 L34',
    condition: 'Comme neuf',
    tags: ['jean', 'levis', '501', 'homme', 'vintage'],
    quality_score: 9.2,
    ai_suggestions: [
      {
        type: 'title',
        suggestion: "Jean Levi's 501 Original Vintage W32 L34 - État Neuf",
        reason: '+15% de vues avec mot-clé "Vintage"'
      },
      {
        type: 'price',
        suggestion: 42,
        reason: 'Prix optimal selon 250 ventes similaires'
      },
      {
        type: 'description',
        suggestion: 'Ajouter "Livraison rapide" augmente les conversions de 12%',
        reason: 'Mots-clés manquants'
      }
    ],
    versions: [
      { id: 1, date: new Date('2024-01-20T14:30:00'), changes: 'Version initiale (IA)' },
      { id: 2, date: new Date('2024-01-20T15:45:00'), changes: 'Prix modifié: 50€ → 45€' },
      { id: 3, date: new Date('2024-01-20T16:20:00'), changes: 'Description enrichie' }
    ],
    created_at: new Date('2024-01-20T14:30:00'),
    updated_at: new Date('2024-01-20T16:20:00')
  });

  const handleSave = async () => {
    setIsSaving(true);
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 1000));
    setIsSaving(false);
    toast.success('Brouillon sauvegardé !');
  };

  const handleImageReorder = (result: any) => {
    if (!result.destination) return;
    const items = Array.from(draft.images);
    const [reorderedItem] = items.splice(result.source.index, 1);
    items.splice(result.destination.index, 0, reorderedItem);
    setDraft({ ...draft, images: items });
  };

  const handleApplySuggestion = (suggestion: any) => {
    if (suggestion.type === 'title') {
      setDraft({ ...draft, title: suggestion.suggestion });
    } else if (suggestion.type === 'price') {
      setDraft({ ...draft, price: suggestion.suggestion });
    }
    toast.success('Suggestion appliquée !');
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <button
                onClick={() => navigate('/drafts')}
                className="p-2 hover:bg-gray-100 rounded-xl transition-colors"
              >
                <ArrowLeft className="w-5 h-5" />
              </button>
              <div>
                <h1 className="text-xl font-bold text-gray-900">Éditer le brouillon</h1>
                <p className="text-sm text-gray-600">
                  Dernière modification : {formatDate(draft.updated_at)}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <Button
                variant="ghost"
                icon={<History className="w-5 h-5" />}
                onClick={() => setShowHistory(true)}
              >
                Historique
              </Button>
              <Button
                variant="ghost"
                icon={<Eye className="w-5 h-5" />}
                onClick={() => setShowPreview(true)}
              >
                Aperçu
              </Button>
              <Button
                variant="secondary"
                icon={<Copy className="w-5 h-5" />}
              >
                Dupliquer
              </Button>
              <Button
                variant="primary"
                icon={<Save className="w-5 h-5" />}
                isLoading={isSaving}
                onClick={handleSave}
              >
                Sauvegarder
              </Button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-8">
        <div className="grid lg:grid-cols-3 gap-8">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-6">
            {/* Images Section */}
            <div className="bg-white rounded-2xl p-6 border border-gray-200">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                  <ImageIcon className="w-5 h-5" />
                  Photos ({draft.images.length}/20)
                </h2>
                <Button size="sm" icon={<Plus className="w-4 h-4" />}>
                  Ajouter
                </Button>
              </div>

              <DragDropContext onDragEnd={handleImageReorder}>
                <Droppable droppableId="images" direction="horizontal">
                  {(provided) => (
                    <div
                      ref={provided.innerRef}
                      {...provided.droppableProps}
                      className="grid grid-cols-3 gap-4"
                    >
                      {draft.images.map((image, index) => (
                        <Draggable key={index} draggableId={`image-${index}`} index={index}>
                          {(provided) => (
                            <div
                              ref={provided.innerRef}
                              {...provided.draggableProps}
                              {...provided.dragHandleProps}
                              className="relative aspect-square bg-gray-100 rounded-xl overflow-hidden group cursor-move"
                            >
                              <img
                                src={image}
                                alt={`Photo ${index + 1}`}
                                className="w-full h-full object-cover"
                              />
                              <div className="absolute inset-0 bg-black/0 group-hover:bg-black/50 transition-all flex items-center justify-center">
                                <button className="opacity-0 group-hover:opacity-100 w-8 h-8 bg-white rounded-full flex items-center justify-center text-error-600 hover:bg-error-50 transition-all">
                                  <X className="w-5 h-5" />
                                </button>
                              </div>
                              <div className="absolute top-2 left-2 bg-black/60 backdrop-blur-sm text-white text-xs font-semibold px-2 py-1 rounded-lg flex items-center gap-1">
                                <GripVertical className="w-3 h-3" />
                                #{index + 1}
                              </div>
                              {index === 0 && (
                                <Badge variant="success" size="sm" className="absolute top-2 right-2">
                                  Principale
                                </Badge>
                              )}
                            </div>
                          )}
                        </Draggable>
                      ))}
                      {provided.placeholder}
                    </div>
                  )}
                </Droppable>
              </DragDropContext>
            </div>

            {/* Title */}
            <div className="bg-white rounded-2xl p-6 border border-gray-200">
              <label className="block text-sm font-semibold text-gray-900 mb-2">Titre</label>
              <input
                type="text"
                value={draft.title}
                onChange={(e) => setDraft({ ...draft, title: e.target.value })}
                className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-brand-500 focus:border-transparent text-lg font-semibold"
                maxLength={100}
              />
              <p className="text-sm text-gray-500 mt-2">
                {draft.title.length}/100 caractères
              </p>
            </div>

            {/* Description */}
            <div className="bg-white rounded-2xl p-6 border border-gray-200">
              <label className="block text-sm font-semibold text-gray-900 mb-2">Description</label>
              <textarea
                value={draft.description}
                onChange={(e) => setDraft({ ...draft, description: e.target.value })}
                className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-brand-500 focus:border-transparent min-h-[300px] font-mono text-sm"
                maxLength={2000}
              />
              <p className="text-sm text-gray-500 mt-2">
                {draft.description.length}/2000 caractères
              </p>
            </div>

            {/* Details Grid */}
            <div className="grid md:grid-cols-2 gap-6">
              <div className="bg-white rounded-2xl p-6 border border-gray-200">
                <label className="block text-sm font-semibold text-gray-900 mb-2">Prix</label>
                <div className="relative">
                  <DollarSign className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                  <input
                    type="number"
                    value={draft.price}
                    onChange={(e) => setDraft({ ...draft, price: Number(e.target.value) })}
                    className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-brand-500 focus:border-transparent text-2xl font-bold"
                  />
                </div>
              </div>

              <div className="bg-white rounded-2xl p-6 border border-gray-200">
                <label className="block text-sm font-semibold text-gray-900 mb-2">Catégorie</label>
                <select
                  value={draft.category}
                  onChange={(e) => setDraft({ ...draft, category: e.target.value })}
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-brand-500 focus:border-transparent"
                >
                  <option>Vêtements</option>
                  <option>Chaussures</option>
                  <option>Accessoires</option>
                  <option>Autre</option>
                </select>
              </div>

              <div className="bg-white rounded-2xl p-6 border border-gray-200">
                <label className="block text-sm font-semibold text-gray-900 mb-2">Marque</label>
                <input
                  type="text"
                  value={draft.brand}
                  onChange={(e) => setDraft({ ...draft, brand: e.target.value })}
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-brand-500 focus:border-transparent"
                />
              </div>

              <div className="bg-white rounded-2xl p-6 border border-gray-200">
                <label className="block text-sm font-semibold text-gray-900 mb-2">Taille</label>
                <input
                  type="text"
                  value={draft.size}
                  onChange={(e) => setDraft({ ...draft, size: e.target.value })}
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-brand-500 focus:border-transparent"
                />
              </div>
            </div>

            {/* Tags */}
            <div className="bg-white rounded-2xl p-6 border border-gray-200">
              <label className="block text-sm font-semibold text-gray-900 mb-2">Tags</label>
              <div className="flex flex-wrap gap-2 mb-3">
                {draft.tags.map((tag, index) => (
                  <Badge key={index} variant="default">
                    #{tag}
                    <button
                      onClick={() => {
                        setDraft({
                          ...draft,
                          tags: draft.tags.filter((_, i) => i !== index)
                        });
                      }}
                      className="ml-1 hover:text-error-600"
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </Badge>
                ))}
              </div>
              <div className="flex gap-2">
                <input
                  type="text"
                  placeholder="Ajouter un tag..."
                  className="flex-1 px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-brand-500 focus:border-transparent"
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && e.currentTarget.value) {
                      setDraft({
                        ...draft,
                        tags: [...draft.tags, e.currentTarget.value]
                      });
                      e.currentTarget.value = '';
                    }
                  }}
                />
              </div>
            </div>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Quality Score */}
            <div className="bg-gradient-to-br from-brand-50 to-brand-100 rounded-2xl p-6 border-2 border-brand-200">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-12 h-12 bg-white rounded-xl shadow-sm flex items-center justify-center">
                  <Sparkles className="w-6 h-6 text-brand-600" />
                </div>
                <div>
                  <div className="text-3xl font-bold text-gray-900">{draft.quality_score}/10</div>
                  <div className="text-sm text-gray-600">Score qualité</div>
                </div>
              </div>
              <div className="w-full bg-white rounded-full h-3 overflow-hidden">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${draft.quality_score * 10}%` }}
                  className="h-full bg-gradient-to-r from-brand-500 to-brand-600"
                />
              </div>
            </div>

            {/* AI Suggestions */}
            <div className="bg-white rounded-2xl p-6 border border-gray-200">
              <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-brand-600" />
                Suggestions IA
              </h3>
              <div className="space-y-3">
                {draft.ai_suggestions.map((suggestion, index) => (
                  <div
                    key={index}
                    className="p-4 bg-brand-50 rounded-xl border border-brand-200"
                  >
                    <div className="flex items-start justify-between mb-2">
                      <Badge variant="info" size="sm">
                        {suggestion.type}
                      </Badge>
                    </div>
                    <p className="text-sm font-medium text-gray-900 mb-2">
                      {typeof suggestion.suggestion === 'string'
                        ? suggestion.suggestion
                        : formatPrice(suggestion.suggestion)}
                    </p>
                    <p className="text-xs text-gray-600 mb-3">{suggestion.reason}</p>
                    <Button
                      size="sm"
                      variant="primary"
                      onClick={() => handleApplySuggestion(suggestion)}
                      className="w-full"
                    >
                      Appliquer
                    </Button>
                  </div>
                ))}
              </div>
            </div>

            {/* Actions */}
            <div className="bg-white rounded-2xl p-6 border border-gray-200">
              <div className="space-y-3">
                <Button variant="primary" icon={<Share2 className="w-5 h-5" />} className="w-full">
                  Publier sur Vinted
                </Button>
                <Button variant="secondary" icon={<Save className="w-5 h-5" />} className="w-full">
                  Sauvegarder brouillon
                </Button>
                <Button variant="danger" icon={<Trash2 className="w-5 h-5" />} className="w-full">
                  Supprimer
                </Button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Preview Modal */}
      <Modal
        isOpen={showPreview}
        onClose={() => setShowPreview(false)}
        title="Aperçu Vinted"
        size="lg"
      >
        <div className="bg-gray-50 rounded-xl p-6">
          <div className="bg-white rounded-xl p-6 max-w-md mx-auto">
            <img
              src={draft.images[0]}
              alt="Preview"
              className="w-full aspect-square object-cover rounded-xl mb-4"
            />
            <h3 className="text-xl font-bold text-gray-900 mb-2">{draft.title}</h3>
            <div className="text-3xl font-bold text-brand-600 mb-4">
              {formatPrice(draft.price)}
            </div>
            <p className="text-sm text-gray-700 whitespace-pre-line">
              {draft.description}
            </p>
          </div>
        </div>
      </Modal>

      {/* History Modal */}
      <Modal
        isOpen={showHistory}
        onClose={() => setShowHistory(false)}
        title="Historique des modifications"
        size="md"
      >
        <div className="space-y-3">
          {draft.versions.map((version) => (
            <div
              key={version.id}
              className="flex items-start gap-4 p-4 bg-gray-50 rounded-xl"
            >
              <div className="w-10 h-10 bg-brand-50 rounded-full flex items-center justify-center text-brand-600 font-semibold flex-shrink-0">
                v{version.id}
              </div>
              <div className="flex-1">
                <p className="font-medium text-gray-900">{version.changes}</p>
                <p className="text-sm text-gray-500 mt-1">
                  {formatDate(version.date)}
                </p>
              </div>
              <Button size="sm" variant="ghost">
                Restaurer
              </Button>
            </div>
          ))}
        </div>
      </Modal>
    </div>
  );
}
