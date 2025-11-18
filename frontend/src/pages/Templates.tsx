import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Plus, Edit, Copy, Trash2, Search, FileText, Sparkles, X, Check } from 'lucide-react';
import { cn } from '@/lib/utils';
import toast from 'react-hot-toast';

interface Template {
  id: string;
  name: string;
  category: string;
  content: string;
  variables: string[];
  createdAt: string;
  isDefault: boolean;
}

const defaultTemplates: Template[] = [
  {
    id: '1',
    name: 'T-shirt',
    category: 'Vêtements',
    content: '{BRAND} {TYPE} en {MATERIAL}, taille {SIZE}.\n\nÉtat : {CONDITION}\n{DEFECTS_DESCRIPTION}\n\nCouleur : {COLOR}\nCoupe : {FIT}\n\nEnvoi rapide sous 24h 📦',
    variables: ['BRAND', 'TYPE', 'MATERIAL', 'SIZE', 'CONDITION', 'DEFECTS_DESCRIPTION', 'COLOR', 'FIT'],
    createdAt: '2024-01-01',
    isDefault: true,
  },
  {
    id: '2',
    name: 'Sneakers',
    category: 'Chaussures',
    content: '{BRAND} {MODEL} - Taille {SIZE}\n\nÉtat : {CONDITION}\nCouleur : {COLOR}\n\nBoîte originale : {HAS_BOX}\n\n100% authentique ✓',
    variables: ['BRAND', 'MODEL', 'SIZE', 'CONDITION', 'COLOR', 'HAS_BOX'],
    createdAt: '2024-01-01',
    isDefault: true,
  },
  {
    id: '3',
    name: 'Robe',
    category: 'Vêtements',
    content: 'Robe {BRAND} {STYLE}\n\nTaille : {SIZE}\nCouleur : {COLOR}\nÉtat : {CONDITION}\n\nParfaite pour {OCCASION} 🌸',
    variables: ['BRAND', 'STYLE', 'SIZE', 'COLOR', 'CONDITION', 'OCCASION'],
    createdAt: '2024-01-01',
    isDefault: true,
  },
];

export default function Templates() {
  const [templates, setTemplates] = useState<Template[]>(defaultTemplates);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [isCreating, setIsCreating] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState<Template | null>(null);
  const [previewData, setPreviewData] = useState<Record<string, string>>({});

  const categories = Array.from(new Set(templates.map(t => t.category)));

  const filteredTemplates = templates.filter(template => {
    const matchesSearch = template.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      template.content.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCategory = selectedCategory === 'all' || template.category === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  const handleDelete = (id: string) => {
    if (confirm('Supprimer ce template ?')) {
      setTemplates(templates.filter(t => t.id !== id));
      toast.success('Template supprimé');
    }
  };

  const handleDuplicate = (template: Template) => {
    const newTemplate = {
      ...template,
      id: Date.now().toString(),
      name: `${template.name} (copie)`,
      isDefault: false,
      createdAt: new Date().toISOString()
    };
    setTemplates([...templates, newTemplate]);
    toast.success('Template dupliqué');
  };

  const renderPreview = (content: string) => {
    let result = content;
    Object.entries(previewData).forEach(([key, value]) => {
      result = result.replace(new RegExp(`{${key}}`, 'g'), value || `{${key}}`);
    });
    return result;
  };

  return (
    <div className="min-h-screen bg-gray-50 -m-8">
      {/* Header */}
      <div className="bg-gradient-to-br from-brand-600 via-purple-600 to-brand-700 text-white">
        <div className="max-w-7xl mx-auto px-6 py-12">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
          >
            <div className="flex items-center gap-3 mb-3">
              <motion.div
                initial={{ scale: 0, rotate: -180 }}
                animate={{ scale: 1, rotate: 0 }}
                transition={{ type: 'spring', delay: 0.2 }}
                className="w-14 h-14 bg-white/20 rounded-2xl backdrop-blur-sm flex items-center justify-center"
              >
                <FileText className="w-8 h-8" />
              </motion.div>
              <h1 className="text-4xl font-bold">Templates</h1>
            </div>
            <p className="text-brand-100 text-lg">
              Créez des descriptions réutilisables pour vos articles
            </p>
          </motion.div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 -mt-8 pb-12">
        {/* Search & Filters */}
        <div className="bg-white rounded-2xl p-6 border border-gray-200 shadow-sm mb-6">
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
            <div className="flex gap-2">
              <button
                onClick={() => setSelectedCategory('all')}
                className={cn(
                  "px-4 py-2 rounded-xl text-sm font-medium transition-all",
                  selectedCategory === 'all'
                    ? "bg-brand-600 text-white shadow-md"
                    : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                )}
              >
                Tous
              </button>
              {categories.map(cat => (
                <button
                  key={cat}
                  onClick={() => setSelectedCategory(cat)}
                  className={cn(
                    "px-4 py-2 rounded-xl text-sm font-medium transition-all",
                    selectedCategory === cat
                      ? "bg-brand-600 text-white shadow-md"
                      : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                  )}
                >
                  {cat}
                </button>
              ))}
            </div>
            <button
              onClick={() => setIsCreating(true)}
              className="bg-gradient-to-r from-brand-600 to-purple-600 text-white px-6 py-3 rounded-xl font-semibold shadow-lg hover:shadow-xl transition-all flex items-center gap-2"
            >
              <Plus className="w-5 h-5" />
              Nouveau
            </button>
          </div>
        </div>

        {/* Templates Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredTemplates.map((template, index) => (
            <TemplateCard
              key={template.id}
              template={template}
              index={index}
              onEdit={() => setSelectedTemplate(template)}
              onDuplicate={() => handleDuplicate(template)}
              onDelete={() => handleDelete(template.id)}
            />
          ))}
        </div>

        {/* Preview Modal */}
        <AnimatePresence>
          {selectedTemplate && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-6"
              onClick={() => setSelectedTemplate(null)}
            >
              <motion.div
                initial={{ scale: 0.9, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                exit={{ scale: 0.9, opacity: 0 }}
                className="bg-white rounded-2xl max-w-3xl w-full max-h-[90vh] overflow-hidden"
                onClick={(e) => e.stopPropagation()}
              >
                <div className="bg-gradient-to-r from-brand-600 to-purple-600 text-white p-6">
                  <div className="flex items-center justify-between">
                    <h3 className="text-2xl font-bold">{selectedTemplate.name}</h3>
                    <button
                      onClick={() => setSelectedTemplate(null)}
                      className="p-2 hover:bg-white/20 rounded-lg transition-colors"
                    >
                      <X className="w-6 h-6" />
                    </button>
                  </div>
                </div>

                <div className="p-6 overflow-y-auto max-h-[70vh]">
                  {/* Variables Input */}
                  <div className="mb-6">
                    <h4 className="font-semibold text-gray-900 mb-4">Variables</h4>
                    <div className="grid grid-cols-2 gap-4">
                      {selectedTemplate.variables.map(variable => (
                        <div key={variable}>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            {variable}
                          </label>
                          <input
                            type="text"
                            value={previewData[variable] || ''}
                            onChange={(e) => setPreviewData({ ...previewData, [variable]: e.target.value })}
                            className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-500"
                            placeholder={`Entrez ${variable}`}
                          />
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Preview */}
                  <div>
                    <h4 className="font-semibold text-gray-900 mb-4">Prévisualisation</h4>
                    <div className="bg-gray-50 p-4 rounded-xl border border-gray-200 whitespace-pre-wrap font-mono text-sm">
                      {renderPreview(selectedTemplate.content)}
                    </div>
                  </div>

                  <div className="mt-6 flex gap-3">
                    <button
                      onClick={() => {
                        navigator.clipboard.writeText(renderPreview(selectedTemplate.content));
                        toast.success('Copié dans le presse-papier !');
                      }}
                      className="flex-1 bg-brand-600 text-white px-6 py-3 rounded-xl font-semibold hover:bg-brand-700 transition-colors flex items-center justify-center gap-2"
                    >
                      <Copy className="w-5 h-5" />
                      Copier
                    </button>
                    <button
                      onClick={() => setSelectedTemplate(null)}
                      className="px-6 py-3 bg-gray-100 text-gray-700 rounded-xl font-semibold hover:bg-gray-200 transition-colors"
                    >
                      Fermer
                    </button>
                  </div>
                </div>
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}

function TemplateCard({ template, index, onEdit, onDuplicate, onDelete }: any) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05 }}
      whileHover={{ y: -4, scale: 1.02 }}
      className="bg-white rounded-2xl border border-gray-200 p-6 hover:shadow-lg transition-all group"
    >
      <div className="flex items-start justify-between mb-4">
        <div>
          <h3 className="font-bold text-gray-900 mb-1 group-hover:text-brand-600 transition-colors">
            {template.name}
          </h3>
          <span className="text-sm text-gray-500">{template.category}</span>
        </div>
        {template.isDefault && (
          <span className="bg-brand-100 text-brand-700 px-2 py-1 rounded-lg text-xs font-semibold flex items-center gap-1">
            <Sparkles className="w-3 h-3" />
            Défaut
          </span>
        )}
      </div>

      <p className="text-sm text-gray-600 line-clamp-3 mb-4 whitespace-pre-wrap">
        {template.content}
      </p>

      <div className="flex flex-wrap gap-2 mb-4">
        {template.variables.slice(0, 4).map(variable => (
          <span
            key={variable}
            className="text-xs bg-gray-100 text-gray-700 px-2 py-1 rounded font-mono"
          >
            {variable}
          </span>
        ))}
        {template.variables.length > 4 && (
          <span className="text-xs bg-gray-100 text-gray-700 px-2 py-1 rounded">
            +{template.variables.length - 4}
          </span>
        )}
      </div>

      <div className="flex gap-2">
        <button
          onClick={onEdit}
          className="flex-1 py-2 bg-brand-600 text-white rounded-lg hover:bg-brand-700 transition-colors text-sm font-medium flex items-center justify-center gap-2"
        >
          <Edit className="w-4 h-4" />
          Utiliser
        </button>
        <button
          onClick={onDuplicate}
          className="p-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
        >
          <Copy className="w-4 h-4" />
        </button>
        {!template.isDefault && (
          <button
            onClick={onDelete}
            className="p-2 bg-error-50 text-error-600 rounded-lg hover:bg-error-100 transition-colors"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        )}
      </div>
    </motion.div>
  );
}
