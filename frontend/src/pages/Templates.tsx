import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Plus, Edit, Copy, Trash2, Search, FileText, Sparkles } from 'lucide-react';
import { Badge } from '../components/common/Badge';

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
    category: 'Clothing',
    content: '{BRAND} {TYPE} en {MATERIAL}, taille {SIZE}.\n\nÉtat : {CONDITION}\n{DEFECTS_DESCRIPTION}\n\nCouleur : {COLOR}\nCoupe : {FIT}\n\nEnvoi rapide sous 24h 📦\nN\'hésitez pas pour toute question !',
    variables: ['BRAND', 'TYPE', 'MATERIAL', 'SIZE', 'CONDITION', 'DEFECTS_DESCRIPTION', 'COLOR', 'FIT'],
    createdAt: '2024-01-01',
    isDefault: true,
  },
  {
    id: '2',
    name: 'Sneakers',
    category: 'Shoes',
    content: '{BRAND} {MODEL} - Taille {SIZE}\n\nÉtat : {CONDITION}\nCouleur : {COLOR}\n\n{DEFECTS_DESCRIPTION}\n\nBoîte originale : {HAS_BOX}\nAccessoires : {ACCESSORIES}\n\n100% authentique ✓\nEnvoi soigné 📦',
    variables: ['BRAND', 'MODEL', 'SIZE', 'CONDITION', 'COLOR', 'DEFECTS_DESCRIPTION', 'HAS_BOX', 'ACCESSORIES'],
    createdAt: '2024-01-01',
    isDefault: true,
  },
  {
    id: '3',
    name: 'Hoodie',
    category: 'Clothing',
    content: 'Hoodie {BRAND} {COLOR}, taille {SIZE}\n\nÉtat : {CONDITION}\nMatière : {MATERIAL}\n\n{DEFECTS_DESCRIPTION}\n\nPerfect pour l\'automne/hiver 🍂\nEnvoi rapide et soigné 📦',
    variables: ['BRAND', 'COLOR', 'SIZE', 'CONDITION', 'MATERIAL', 'DEFECTS_DESCRIPTION'],
    createdAt: '2024-01-01',
    isDefault: true,
  },
];

export default function Templates() {
  const [templates, setTemplates] = useState<Template[]>(defaultTemplates);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [isCreating, setIsCreating] = useState(false);

  const filteredTemplates = templates.filter((template) => {
    const matchesSearch =
      template.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      template.content.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCategory = selectedCategory === 'all' || template.category === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  const categories = ['all', ...Array.from(new Set(templates.map((t) => t.category)))];

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center justify-between"
      >
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Description Templates
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-2">
            Create and manage reusable templates for your listings
          </p>
        </div>
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={() => setIsCreating(true)}
          className="px-6 py-3 bg-primary-500 hover:bg-primary-600 text-white rounded-lg flex items-center gap-2 font-medium shadow-lg transition-colors"
        >
          <Plus className="w-5 h-5" />
          New Template
        </motion.button>
      </motion.div>

      {/* Search and Filters */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.1 }}
        className="card p-6"
      >
        <div className="flex flex-col md:flex-row gap-4">
          {/* Search */}
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              placeholder="Search templates..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-3 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all"
            />
          </div>

          {/* Category Filter */}
          <div className="flex gap-2 overflow-x-auto pb-2">
            {categories.map((category) => (
              <button
                key={category}
                onClick={() => setSelectedCategory(category)}
                className={`px-4 py-2 rounded-lg font-medium transition-all whitespace-nowrap ${
                  selectedCategory === category
                    ? 'bg-primary-500 text-white'
                    : 'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700'
                }`}
              >
                {category === 'all' ? 'All' : category}
              </button>
            ))}
          </div>
        </div>
      </motion.div>

      {/* Templates Grid */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.2 }}
        className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
      >
        <AnimatePresence>
          {filteredTemplates.map((template, index) => (
            <motion.div
              key={template.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.9 }}
              transition={{ delay: index * 0.05 }}
              whileHover={{ y: -4 }}
              className="card p-6 hover:shadow-premium transition-all"
            >
              {/* Header */}
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-1">
                    {template.name}
                  </h3>
                  <div className="flex items-center gap-2">
                    <Badge variant="default" size="sm">
                      {template.category}
                    </Badge>
                    {template.isDefault && (
                      <Badge variant="primary" size="sm" dot>
                        Default
                      </Badge>
                    )}
                  </div>
                </div>
                <div className="flex gap-1">
                  <button
                    className="p-2 text-gray-400 hover:text-primary-500 hover:bg-primary-50 dark:hover:bg-primary-900/20 rounded-lg transition-colors"
                    title="Edit template"
                  >
                    <Edit className="w-4 h-4" />
                  </button>
                  <button
                    className="p-2 text-gray-400 hover:text-success-500 hover:bg-success-50 dark:hover:bg-success-900/20 rounded-lg transition-colors"
                    title="Duplicate template"
                  >
                    <Copy className="w-4 h-4" />
                  </button>
                  {!template.isDefault && (
                    <button
                      className="p-2 text-gray-400 hover:text-error-500 hover:bg-error-50 dark:hover:bg-error-900/20 rounded-lg transition-colors"
                      title="Delete template"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  )}
                </div>
              </div>

              {/* Content Preview */}
              <div className="mb-4">
                <p className="text-sm text-gray-600 dark:text-gray-400 line-clamp-4 whitespace-pre-wrap font-mono text-xs bg-gray-50 dark:bg-gray-800 p-3 rounded-lg">
                  {template.content}
                </p>
              </div>

              {/* Variables */}
              <div className="mb-4">
                <div className="flex items-center gap-2 mb-2">
                  <Sparkles className="w-4 h-4 text-primary-500" />
                  <span className="text-xs font-medium text-gray-600 dark:text-gray-400">
                    Variables ({template.variables.length})
                  </span>
                </div>
                <div className="flex flex-wrap gap-1">
                  {template.variables.slice(0, 4).map((variable) => (
                    <span
                      key={variable}
                      className="px-2 py-1 text-xs font-mono bg-primary-50 dark:bg-primary-900/20 text-primary-700 dark:text-primary-400 rounded"
                    >
                      {`{${variable}}`}
                    </span>
                  ))}
                  {template.variables.length > 4 && (
                    <span className="px-2 py-1 text-xs text-gray-500">
                      +{template.variables.length - 4} more
                    </span>
                  )}
                </div>
              </div>

              {/* Footer */}
              <div className="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400 pt-4 border-t border-gray-200 dark:border-gray-700">
                <span>Created {new Date(template.createdAt).toLocaleDateString()}</span>
                <button className="px-3 py-1.5 bg-primary-50 dark:bg-primary-900/20 text-primary-700 dark:text-primary-400 rounded-lg hover:bg-primary-100 dark:hover:bg-primary-900/40 font-medium transition-colors">
                  Use Template
                </button>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
      </motion.div>

      {/* Empty State */}
      {filteredTemplates.length === 0 && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="card p-12 text-center"
        >
          <FileText className="w-16 h-16 text-gray-300 dark:text-gray-600 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
            No templates found
          </h3>
          <p className="text-gray-600 dark:text-gray-400 mb-6">
            {searchQuery ? 'Try adjusting your search criteria' : 'Create your first template to get started'}
          </p>
          <button
            onClick={() => setIsCreating(true)}
            className="px-6 py-3 bg-primary-500 hover:bg-primary-600 text-white rounded-lg inline-flex items-center gap-2 font-medium transition-colors"
          >
            <Plus className="w-5 h-5" />
            Create Template
          </button>
        </motion.div>
      )}

      {/* Info Card */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.3 }}
        className="card p-6 bg-gradient-to-br from-primary-50 to-purple-50 dark:from-primary-900/20 dark:to-purple-900/20 border-primary-200 dark:border-primary-800"
      >
        <div className="flex items-start gap-4">
          <div className="p-3 bg-primary-100 dark:bg-primary-900/40 rounded-lg">
            <Sparkles className="w-6 h-6 text-primary-600 dark:text-primary-400" />
          </div>
          <div className="flex-1">
            <h3 className="font-semibold text-gray-900 dark:text-white mb-1">
              Pro Tip: Using Variables
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Use variables like {'{BRAND}'}, {'{SIZE}'}, {'{COLOR}'} in your templates. The AI will automatically fill them based on your product photos and data. Create consistent, professional listings faster!
            </p>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
