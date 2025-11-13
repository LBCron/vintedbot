import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Search,
  BookOpen,
  PlayCircle,
  MessageCircle,
  Mail,
  ChevronDown,
  ChevronUp,
  HelpCircle,
  Sparkles,
  Upload,
  FileText,
  BarChart3,
  Clock,
} from 'lucide-react';

interface FAQItem {
  id: string;
  question: string;
  answer: string;
  category: string;
}

interface Guide {
  id: string;
  title: string;
  description: string;
  duration: string;
  icon: any;
}

const faqs: FAQItem[] = [
  {
    id: '1',
    question: 'Comment uploader mes photos ?',
    answer: 'Cliquez sur le bouton "Upload Photos" dans le dashboard ou allez directement sur /upload. Vous pouvez glisser-déposer jusqu\'à 500 photos. Les formats supportés sont : JPG, PNG, WEBP, HEIC. Taille max : 15MB par photo.',
    category: 'Upload',
  },
  {
    id: '2',
    question: 'Comment fonctionne la génération IA ?',
    answer: 'Notre IA analyse vos photos pour détecter automatiquement : la marque, la taille, la couleur, l\'état, et génère une description optimisée. Elle suggère aussi un prix basé sur le marché. Le score de confiance indique la qualité de l\'analyse (85%+ = excellent).',
    category: 'IA',
  },
  {
    id: '3',
    question: 'Comment optimiser mes prix ?',
    answer: 'L\'IA suggère un prix optimal basé sur : articles similaires vendus, état du produit, marque, et demande actuelle. Vous pouvez ajuster manuellement. Un prix 10-15% sous le marché = vente rapide. Au-dessus = plus de profit mais vente plus lente.',
    category: 'Pricing',
  },
  {
    id: '4',
    question: 'Puis-je modifier les drafts générés par l\'IA ?',
    answer: 'Oui ! Cliquez sur "Edit" sur n\'importe quel draft. Vous pouvez modifier le titre, la description, le prix, ajouter/supprimer des photos, et ajuster toutes les métadonnées avant publication.',
    category: 'Drafts',
  },
  {
    id: '5',
    question: 'Comment publier sur Vinted ?',
    answer: 'Allez dans "Manage Drafts", sélectionnez les drafts à publier, et cliquez sur "Publish". L\'IA a déjà optimisé vos annonces. Vous pouvez aussi programmer des publications automatiques avec le plan PRO.',
    category: 'Publishing',
  },
  {
    id: '6',
    question: 'Quelles sont les limites du plan gratuit ?',
    answer: 'Plan FREE : 20 analyses IA/mois, 50 drafts max, 10 publications/mois, analytics basiques. Pour débloquer plus, passez au plan PRO (19€/mois) avec analyses illimitées, auto-publication, et analytics avancées.',
    category: 'Pricing',
  },
];

const guides: Guide[] = [
  {
    id: '1',
    title: 'Guide de démarrage rapide',
    description: 'Apprenez les bases en 5 minutes',
    duration: '5 min',
    icon: BookOpen,
  },
  {
    id: '2',
    title: 'Guide des fonctionnalités IA',
    description: 'Maîtrisez l\'IA pour de meilleures annonces',
    duration: '10 min',
    icon: Sparkles,
  },
  {
    id: '3',
    title: 'Optimisation des prix',
    description: 'Vendez plus vite au meilleur prix',
    duration: '8 min',
    icon: BarChart3,
  },
  {
    id: '4',
    title: 'Meilleures pratiques photos',
    description: 'Prenez des photos qui vendent',
    duration: '12 min',
    icon: Upload,
  },
];

export default function HelpCenter() {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [openFAQ, setOpenFAQ] = useState<string | null>(null);

  const categories = ['all', ...Array.from(new Set(faqs.map((f) => f.category)))];

  const filteredFAQs = faqs.filter((faq) => {
    const matchesSearch =
      faq.question.toLowerCase().includes(searchQuery.toLowerCase()) ||
      faq.answer.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCategory = selectedCategory === 'all' || faq.category === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  return (
    <div className="max-w-7xl mx-auto space-y-8">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center"
      >
        <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-4">
          💁 How can we help you?
        </h1>
        <p className="text-lg text-gray-600 dark:text-gray-400">
          Search our knowledge base or contact support
        </p>
      </motion.div>

      {/* Search Bar */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.1 }}
        className="max-w-2xl mx-auto"
      >
        <div className="relative">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-6 h-6 text-gray-400" />
          <input
            type="text"
            placeholder="Search for help..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-14 pr-4 py-4 bg-white dark:bg-gray-800 border-2 border-gray-200 dark:border-gray-700 rounded-xl text-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all shadow-lg"
          />
        </div>
      </motion.div>

      {/* Quick Actions */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.2 }}
        className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
      >
        {guides.map((guide, index) => (
          <motion.div
            key={guide.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 + index * 0.05 }}
            whileHover={{ y: -4 }}
            className="card p-6 cursor-pointer hover:shadow-premium transition-all group"
          >
            <div className="flex items-start gap-4">
              <div className="p-3 bg-primary-50 dark:bg-primary-900/20 rounded-xl group-hover:bg-primary-100 dark:group-hover:bg-primary-900/40 transition-colors">
                <guide.icon className="w-6 h-6 text-primary-600 dark:text-primary-400" />
              </div>
              <div className="flex-1">
                <h3 className="font-semibold text-gray-900 dark:text-white mb-1">
                  {guide.title}
                </h3>
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                  {guide.description}
                </p>
                <div className="flex items-center gap-2 text-xs text-gray-500">
                  <Clock className="w-4 h-4" />
                  {guide.duration}
                </div>
              </div>
            </div>
          </motion.div>
        ))}
      </motion.div>

      {/* FAQ Section */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.3 }}
      >
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">
          🔥 Frequently Asked Questions
        </h2>

        {/* Category Filter */}
        <div className="flex gap-2 overflow-x-auto pb-4 mb-6">
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

        {/* FAQ List */}
        <div className="space-y-3">
          <AnimatePresence>
            {filteredFAQs.map((faq, index) => (
              <motion.div
                key={faq.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ delay: index * 0.05 }}
                className="card overflow-hidden"
              >
                <button
                  onClick={() => setOpenFAQ(openFAQ === faq.id ? null : faq.id)}
                  className="w-full p-6 flex items-center justify-between text-left hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
                >
                  <div className="flex items-center gap-4 flex-1">
                    <div className="p-2 bg-primary-50 dark:bg-primary-900/20 rounded-lg">
                      <HelpCircle className="w-5 h-5 text-primary-600 dark:text-primary-400" />
                    </div>
                    <div className="flex-1">
                      <h3 className="font-semibold text-gray-900 dark:text-white">
                        {faq.question}
                      </h3>
                    </div>
                  </div>
                  {openFAQ === faq.id ? (
                    <ChevronUp className="w-5 h-5 text-gray-400" />
                  ) : (
                    <ChevronDown className="w-5 h-5 text-gray-400" />
                  )}
                </button>

                <AnimatePresence>
                  {openFAQ === faq.id && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: 'auto', opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      transition={{ duration: 0.2 }}
                      className="border-t border-gray-200 dark:border-gray-700"
                    >
                      <div className="p-6 pt-4 text-gray-600 dark:text-gray-400">
                        {faq.answer}
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </motion.div>
            ))}
          </AnimatePresence>
        </div>
      </motion.div>

      {/* Contact Support */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.4 }}
        className="card p-8 bg-gradient-to-br from-primary-50 to-purple-50 dark:from-primary-900/20 dark:to-purple-900/20 border-primary-200 dark:border-primary-800"
      >
        <div className="text-center max-w-2xl mx-auto">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
            💬 Still need help?
          </h2>
          <p className="text-gray-600 dark:text-gray-400 mb-6">
            Our support team is here to help you succeed
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <button className="px-6 py-3 bg-primary-500 hover:bg-primary-600 text-white rounded-lg inline-flex items-center justify-center gap-2 font-medium transition-colors">
              <MessageCircle className="w-5 h-5" />
              Live Chat
            </button>
            <button className="px-6 py-3 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-900 dark:text-white border-2 border-gray-200 dark:border-gray-700 rounded-lg inline-flex items-center justify-center gap-2 font-medium transition-colors">
              <Mail className="w-5 h-5" />
              Send Email
            </button>
          </div>

          <div className="mt-6 text-sm text-gray-600 dark:text-gray-400">
            <p>Average response time: ~2 hours</p>
            <p>Support hours: Mon-Fri 9AM-6PM CET</p>
          </div>
        </div>
      </motion.div>

      {/* Video Tutorials */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.5 }}
      >
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">
          🎥 Video Tutorials
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {['Upload in 60 seconds', 'AI in 3 minutes', 'Optimal Pricing'].map((title, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.5 + index * 0.1 }}
              whileHover={{ y: -4 }}
              className="card p-4 cursor-pointer group hover:shadow-premium transition-all"
            >
              <div className="aspect-video bg-gradient-to-br from-primary-100 to-purple-100 dark:from-primary-900/40 dark:to-purple-900/40 rounded-lg flex items-center justify-center mb-4 group-hover:from-primary-200 group-hover:to-purple-200 dark:group-hover:from-primary-900/60 dark:group-hover:to-purple-900/60 transition-colors">
                <PlayCircle className="w-12 h-12 text-primary-600 dark:text-primary-400" />
              </div>
              <h3 className="font-semibold text-gray-900 dark:text-white">{title}</h3>
            </motion.div>
          ))}
        </div>
      </motion.div>
    </div>
  );
}
