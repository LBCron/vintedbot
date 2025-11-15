import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Plus, Edit, Copy, Trash2, Search, FileText, Sparkles } from 'lucide-react';
import { GlassCard } from '../components/ui/GlassCard';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { EmptyState } from '../components/ui/EmptyState';

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
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      <div className="max-w-7xl mx-auto p-4 md:p-6 lg:p-8 space-y-8">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4"
        >
          <div className="flex items-center gap-4">
            <div className="p-4 bg-gradient-to-br from-violet-500 to-purple-600 rounded-2xl shadow-lg shadow-violet-500/50">
              <FileText className="w-8 h-8 text-white" />
            </div>
            <div>
              <h1 className="text-4xl md:text-5xl font-bold bg-gradient-to-r from-white via-violet-200 to-purple-200 bg-clip-text text-transparent">
                Description Templates
              </h1>
              <p className="text-slate-400 mt-1">
                Create and manage reusable templates for your listings
              </p>
            </div>
          </div>
          <Button
            onClick={() => setIsCreating(true)}
            icon={Plus}
          >
            New Template
          </Button>
        </motion.div>

        {/* Search and Filters */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.1 }}
        >
          <GlassCard className="p-6">
            <div className="flex flex-col md:flex-row gap-4">
              {/* Search */}
              <div className="flex-1 relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                <input
                  type="text"
                  placeholder="Search templates..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-10 pr-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder-slate-400 focus:outline-none focus:border-violet-500/50 focus:bg-white/10 transition-all"
                />
              </div>

              {/* Category Filter */}
              <div className="flex gap-2 overflow-x-auto pb-2">
                {categories.map((category) => (
                  <button
                    key={category}
                    onClick={() => setSelectedCategory(category)}
                    className={`px-4 py-2 rounded-xl font-medium transition-all whitespace-nowrap ${
                      selectedCategory === category
                        ? 'bg-gradient-to-r from-violet-500 to-purple-600 text-white shadow-lg shadow-violet-500/30'
                        : 'bg-white/5 border border-white/10 text-slate-300 hover:bg-white/10'
                    }`}
                  >
                    {category === 'all' ? 'All' : category}
                  </button>
                ))}
              </div>
            </div>
          </GlassCard>
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
              >
                <GlassCard hover>
                  {/* Header */}
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex-1">
                      <h3 className="text-lg font-semibold text-white mb-2">
                        {template.name}
                      </h3>
                      <div className="flex items-center gap-2">
                        <Badge variant="info" size="sm">
                          {template.category}
                        </Badge>
                        {template.isDefault && (
                          <Badge variant="primary" size="sm">
                            Default
                          </Badge>
                        )}
                      </div>
                    </div>
                    <div className="flex gap-1">
                      <button
                        className="p-2 text-slate-400 hover:text-violet-400 hover:bg-violet-500/10 rounded-lg transition-colors"
                        title="Edit template"
                      >
                        <Edit className="w-4 h-4" />
                      </button>
                      <button
                        className="p-2 text-slate-400 hover:text-green-400 hover:bg-green-500/10 rounded-lg transition-colors"
                        title="Duplicate template"
                      >
                        <Copy className="w-4 h-4" />
                      </button>
                      {!template.isDefault && (
                        <button
                          className="p-2 text-slate-400 hover:text-red-400 hover:bg-red-500/10 rounded-lg transition-colors"
                          title="Delete template"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      )}
                    </div>
                  </div>

                  {/* Content Preview */}
                  <div className="mb-4">
                    <p className="text-sm text-slate-300 line-clamp-4 whitespace-pre-wrap font-mono text-xs bg-white/5 border border-white/10 p-3 rounded-lg">
                      {template.content}
                    </p>
                  </div>

                  {/* Variables */}
                  <div className="mb-4">
                    <div className="flex items-center gap-2 mb-2">
                      <Sparkles className="w-4 h-4 text-violet-400" />
                      <span className="text-xs font-medium text-slate-400">
                        Variables ({template.variables.length})
                      </span>
                    </div>
                    <div className="flex flex-wrap gap-1">
                      {template.variables.slice(0, 4).map((variable) => (
                        <span
                          key={variable}
                          className="px-2 py-1 text-xs font-mono bg-violet-500/20 border border-violet-500/30 text-violet-300 rounded"
                        >
                          {`{${variable}}`}
                        </span>
                      ))}
                      {template.variables.length > 4 && (
                        <span className="px-2 py-1 text-xs text-slate-500">
                          +{template.variables.length - 4} more
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Footer */}
                  <div className="flex items-center justify-between text-xs text-slate-400 pt-4 border-t border-white/10">
                    <span>Created {new Date(template.createdAt).toLocaleDateString()}</span>
                    <button className="px-3 py-1.5 bg-violet-500/20 border border-violet-500/30 text-violet-300 rounded-lg hover:bg-violet-500/30 font-medium transition-colors">
                      Use Template
                    </button>
                  </div>
                </GlassCard>
              </motion.div>
            ))}
          </AnimatePresence>
        </motion.div>

        {/* Empty State */}
        {filteredTemplates.length === 0 && (
          <EmptyState
            icon={FileText}
            title="No templates found"
            description={searchQuery ? 'Try adjusting your search criteria' : 'Create your first template to get started'}
            action={{
              label: 'Create Template',
              onClick: () => setIsCreating(true),
              icon: Plus
            }}
          />
        )}

        {/* Info Card */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3 }}
        >
          <GlassCard className="bg-gradient-to-br from-violet-500/10 to-purple-500/10 border-violet-500/30">
            <div className="flex items-start gap-4">
              <div className="p-3 bg-violet-500/20 rounded-xl border border-violet-500/30">
                <Sparkles className="w-6 h-6 text-violet-400" />
              </div>
              <div className="flex-1">
                <h3 className="font-semibold text-white mb-1">
                  Pro Tip: Using Variables
                </h3>
                <p className="text-sm text-slate-300">
                  Use variables like {'{BRAND}'}, {'{SIZE}'}, {'{COLOR}'} in your templates. The AI will automatically fill them based on your product photos and data. Create consistent, professional listings faster!
                </p>
              </div>
            </div>
          </GlassCard>
        </motion.div>
      </div>
    </div>
  );
}
