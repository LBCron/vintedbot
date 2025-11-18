import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Plus,
  Search,
  Edit3,
  Copy,
  Trash2,
  Eye,
  Sparkles,
  Tag,
  Clock,
  CheckCircle2,
  FileText
} from 'lucide-react';
import { formatDate, cn } from '../lib/utils';
import toast from 'react-hot-toast';

type Category = 'all' | 'clothing' | 'shoes' | 'accessories' | 'other';

export default function Templates() {
  const [selectedCategory, setSelectedCategory] = useState<Category>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [hoveredTemplate, setHoveredTemplate] = useState<string | null>(null);

  const [templates] = useState([
    {
      id: '1',
      name: 'T-shirt basique',
      category: 'clothing',
      description: 'T-shirt [BRAND] [COLOR] en [MATERIAL]...',
      variables: ['BRAND', 'COLOR', 'MATERIAL', 'SIZE', 'CONDITION'],
      usage_count: 45,
      created_at: new Date('2024-01-10'),
      is_default: true
    },
    {
      id: '2',
      name: 'Sneakers',
      category: 'shoes',
      description: 'Baskets [BRAND] [MODEL] pointure [SIZE]...',
      variables: ['BRAND', 'MODEL', 'SIZE', 'CONDITION'],
      usage_count: 32,
      created_at: new Date('2024-01-15'),
      is_default: true
    },
    {
      id: '3',
      name: 'Robe élégante',
      category: 'clothing',
      description: 'Magnifique robe [BRAND] [COLOR]...',
      variables: ['BRAND', 'COLOR', 'SIZE', 'OCCASION'],
      usage_count: 28,
      created_at: new Date('2024-01-12'),
      is_default: false
    }
  ]);

  const categories = [
    { value: 'all', label: 'Tous', count: templates.length },
    { value: 'clothing', label: 'Vêtements', count: templates.filter(t => t.category === 'clothing').length },
    { value: 'shoes', label: 'Chaussures', count: templates.filter(t => t.category === 'shoes').length },
    { value: 'accessories', label: 'Accessoires', count: templates.filter(t => t.category === 'accessories').length },
    { value: 'other', label: 'Autre', count: templates.filter(t => t.category === 'other').length }
  ];

  const filteredTemplates = templates.filter(template => {
    const matchesCategory = selectedCategory === 'all' || template.category === selectedCategory;
    const matchesSearch = template.name.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesCategory && matchesSearch;
  });

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-gradient-to-br from-brand-600 via-brand-500 to-purple-600 text-white">
        <div className="max-w-7xl mx-auto px-6 py-12">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
          >
            <div className="flex items-center gap-3 mb-4">
              <FileText className="w-10 h-10" />
              <h1 className="text-4xl font-bold">Templates</h1>
            </div>
            <p className="text-brand-100 text-lg max-w-2xl">
              Créez des templates réutilisables pour gagner du temps.
              Utilisez des variables pour personnaliser automatiquement vos descriptions.
            </p>
          </motion.div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 -mt-6">
        {/* Search & Actions */}
        <div className="bg-white rounded-2xl shadow-lg p-6 mb-8">
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Rechercher un template..."
                className="w-full pl-10 pr-4 py-3 bg-gray-50 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-brand-500"
              />
            </div>
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => setShowCreateModal(true)}
              className="btn btn-primary flex items-center gap-2 whitespace-nowrap"
            >
              <Plus className="w-5 h-5" />
              Nouveau template
            </motion.button>
          </div>

          {/* Categories */}
          <div className="flex gap-2 mt-4 overflow-x-auto pb-2">
            {categories.map(cat => (
              <button
                key={cat.value}
                onClick={() => setSelectedCategory(cat.value as Category)}
                className={cn(
                  "px-4 py-2 rounded-xl text-sm font-medium whitespace-nowrap transition-all",
                  selectedCategory === cat.value
                    ? "bg-brand-600 text-white shadow-md"
                    : "bg-gray-50 text-gray-700 hover:bg-gray-100"
                )}
              >
                {cat.label}
                <span className="ml-2 opacity-75">({cat.count})</span>
              </button>
            ))}
          </div>
        </div>

        {/* Templates Grid */}
        <div className="pb-12">
          {filteredTemplates.length === 0 ? (
            <EmptyTemplates searchQuery={searchQuery} />
          ) : (
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
              {filteredTemplates.map((template, index) => (
                <TemplateCard
                  key={template.id}
                  template={template}
                  index={index}
                  isHovered={hoveredTemplate === template.id}
                  onHover={() => setHoveredTemplate(template.id)}
                  onLeave={() => setHoveredTemplate(null)}
                />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function TemplateCard({ template, index, isHovered, onHover, onLeave }: any) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05 }}
      whileHover={{ y: -4 }}
      onHoverStart={onHover}
      onHoverEnd={onLeave}
      className="bg-white rounded-2xl border-2 border-gray-200 p-6 hover:border-brand-300 hover:shadow-xl transition-all group relative overflow-hidden cursor-pointer"
    >
      {/* Default Badge */}
      {template.is_default && (
        <div className="absolute top-4 right-4">
          <span className="bg-brand-100 text-brand-700 px-3 py-1 rounded-full text-xs font-semibold flex items-center gap-1">
            <Sparkles className="w-3 h-3" />
            Par défaut
          </span>
        </div>
      )}

      {/* Icon */}
      <div className="w-14 h-14 bg-gradient-to-br from-brand-50 to-brand-100 rounded-2xl flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
        <FileText className="w-7 h-7 text-brand-600" />
      </div>

      {/* Title & Stats */}
      <h3 className="text-xl font-semibold text-gray-900 mb-2 group-hover:text-brand-600 transition-colors">
        {template.name}
      </h3>

      <div className="flex items-center gap-3 text-sm text-gray-500 mb-4">
        <span className="flex items-center gap-1">
          <Eye className="w-4 h-4" />
          {template.usage_count} utilisations
        </span>
        <span className="flex items-center gap-1">
          <Clock className="w-4 h-4" />
          {formatDate(template.created_at, 'd MMM')}
        </span>
      </div>

      {/* Description Preview */}
      <div className="relative mb-4">
        <div className={cn(
          "bg-gray-50 rounded-xl p-4 text-sm text-gray-700 font-mono transition-all",
          isHovered ? "max-h-32" : "max-h-20"
        )}>
          <p className={cn(isHovered ? "line-clamp-5" : "line-clamp-3")}>
            {template.description}
          </p>
        </div>
      </div>

      {/* Variables */}
      <div className="mb-4">
        <div className="text-xs font-semibold text-gray-500 mb-2 flex items-center gap-1">
          <Tag className="w-3 h-3" />
          Variables ({template.variables.length})
        </div>
        <div className="flex flex-wrap gap-2">
          {template.variables.slice(0, 3).map(variable => (
            <span
              key={variable}
              className="px-2 py-1 bg-brand-50 text-brand-700 rounded-lg text-xs font-mono font-semibold"
            >
              {variable}
            </span>
          ))}
          {template.variables.length > 3 && (
            <span className="px-2 py-1 bg-gray-100 text-gray-600 rounded-lg text-xs font-semibold">
              +{template.variables.length - 3}
            </span>
          )}
        </div>
      </div>

      {/* Actions */}
      <div className="flex gap-2 pt-4 border-t border-gray-100">
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          className="flex-1 btn btn-primary btn-sm flex items-center justify-center gap-2"
        >
          <CheckCircle2 className="w-4 h-4" />
          Utiliser
        </motion.button>
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          className="btn btn-secondary btn-sm p-2"
        >
          <Edit3 className="w-4 h-4" />
        </motion.button>
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          className="btn btn-secondary btn-sm p-2"
        >
          <Copy className="w-4 h-4" />
        </motion.button>
        {!template.is_default && (
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            className="btn btn-secondary btn-sm p-2 hover:bg-error-50 hover:text-error-600"
          >
            <Trash2 className="w-4 h-4" />
          </motion.button>
        )}
      </div>
    </motion.div>
  );
}

function EmptyTemplates({ searchQuery }: any) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="text-center py-20"
    >
      <div className="w-32 h-32 bg-gradient-to-br from-gray-100 to-gray-200 rounded-full flex items-center justify-center mx-auto mb-6">
        <FileText className="w-16 h-16 text-gray-400" />
      </div>
      {searchQuery ? (
        <>
          <h3 className="text-2xl font-bold text-gray-900 mb-2">Aucun résultat</h3>
          <p className="text-gray-600">Aucun template ne correspond à "{searchQuery}"</p>
        </>
      ) : (
        <>
          <h3 className="text-2xl font-bold text-gray-900 mb-2">Aucun template</h3>
          <p className="text-gray-600 mb-6">Créez votre premier template pour gagner du temps</p>
          <button className="btn btn-primary">
            <Plus className="w-5 h-5 mr-2" />
            Créer un template
          </button>
        </>
      )}
    </motion.div>
  );
}
