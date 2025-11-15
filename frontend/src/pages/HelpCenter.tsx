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
  LifeBuoy,
} from 'lucide-react';
import { GlassCard } from '../components/ui/GlassCard';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';

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
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      <div className="max-w-7xl mx-auto p-4 md:p-6 lg:p-8 space-y-8">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex flex-col items-center gap-4 text-center"
        >
          <div className="p-4 bg-gradient-to-br from-violet-500 to-purple-600 rounded-2xl shadow-lg shadow-violet-500/50">
            <LifeBuoy className="w-8 h-8 text-white" />
          </div>
          <div>
            <h1 className="text-4xl md:text-5xl font-bold bg-gradient-to-r from-white via-violet-200 to-purple-200 bg-clip-text text-transparent mb-2">
              Help Center
            </h1>
            <p className="text-slate-400 text-lg">
              Search our knowledge base or contact support
            </p>
          </div>
        </motion.div>

        {/* Search Bar */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.1 }}
          className="max-w-2xl mx-auto"
        >
          <GlassCard noPadding>
            <div className="relative">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-6 h-6 text-slate-400" />
              <input
                type="text"
                placeholder="Search for help..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-14 pr-4 py-4 bg-transparent border-none text-white text-lg placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-violet-500/50 rounded-2xl"
              />
            </div>
          </GlassCard>
        </motion.div>

        {/* Quick Actions */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.2 }}
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6"
        >
          {guides.map((guide, index) => (
            <motion.div
              key={guide.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 + index * 0.05 }}
            >
              <GlassCard hover className="h-full">
                <div className="flex flex-col items-center text-center gap-3">
                  <div className="p-3 bg-violet-500/20 rounded-xl border border-violet-500/30">
                    <guide.icon className="w-6 h-6 text-violet-400" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-white mb-1">
                      {guide.title}
                    </h3>
                    <p className="text-sm text-slate-400 mb-2">
                      {guide.description}
                    </p>
                    <div className="flex items-center justify-center gap-2 text-xs text-slate-500">
                      <Clock className="w-4 h-4" />
                      {guide.duration}
                    </div>
                  </div>
                </div>
              </GlassCard>
            </motion.div>
          ))}
        </motion.div>

        {/* FAQ Section */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3 }}
          className="space-y-6"
        >
          <h2 className="text-3xl font-bold bg-gradient-to-r from-white via-violet-200 to-purple-200 bg-clip-text text-transparent">
            Frequently Asked Questions
          </h2>

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
                >
                  <GlassCard noPadding>
                    <button
                      onClick={() => setOpenFAQ(openFAQ === faq.id ? null : faq.id)}
                      className="w-full p-6 flex items-center justify-between text-left hover:bg-white/5 transition-colors rounded-2xl"
                    >
                      <div className="flex items-center gap-4 flex-1">
                        <div className="p-2 bg-violet-500/20 rounded-lg border border-violet-500/30">
                          <HelpCircle className="w-5 h-5 text-violet-400" />
                        </div>
                        <div className="flex-1">
                          <h3 className="font-semibold text-white">
                            {faq.question}
                          </h3>
                          <Badge variant="info" size="sm" className="mt-1">
                            {faq.category}
                          </Badge>
                        </div>
                      </div>
                      {openFAQ === faq.id ? (
                        <ChevronUp className="w-5 h-5 text-slate-400" />
                      ) : (
                        <ChevronDown className="w-5 h-5 text-slate-400" />
                      )}
                    </button>

                    <AnimatePresence>
                      {openFAQ === faq.id && (
                        <motion.div
                          initial={{ height: 0, opacity: 0 }}
                          animate={{ height: 'auto', opacity: 1 }}
                          exit={{ height: 0, opacity: 0 }}
                          transition={{ duration: 0.2 }}
                          className="border-t border-white/10"
                        >
                          <div className="p-6 pt-4 text-slate-300">
                            {faq.answer}
                          </div>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </GlassCard>
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
        >
          <GlassCard className="bg-gradient-to-br from-violet-500/10 to-purple-500/10 border-violet-500/30">
            <div className="text-center max-w-2xl mx-auto">
              <div className="flex items-center justify-center gap-3 mb-4">
                <div className="p-3 bg-violet-500/20 rounded-xl border border-violet-500/30">
                  <MessageCircle className="w-6 h-6 text-violet-400" />
                </div>
                <h2 className="text-2xl font-bold text-white">
                  Still need help?
                </h2>
              </div>
              <p className="text-slate-300 mb-6">
                Our support team is here to help you succeed
              </p>

              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <Button icon={MessageCircle} size="lg">
                  Live Chat
                </Button>
                <Button variant="outline" icon={Mail} size="lg">
                  Send Email
                </Button>
              </div>

              <div className="mt-6 text-sm text-slate-400 space-y-1">
                <p>Average response time: ~2 hours</p>
                <p>Support hours: Mon-Fri 9AM-6PM CET</p>
              </div>
            </div>
          </GlassCard>
        </motion.div>

        {/* Video Tutorials */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
          className="space-y-6"
        >
          <h2 className="text-3xl font-bold bg-gradient-to-r from-white via-violet-200 to-purple-200 bg-clip-text text-transparent">
            Video Tutorials
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {['Upload in 60 seconds', 'AI in 3 minutes', 'Optimal Pricing'].map((title, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.5 + index * 0.1 }}
              >
                <GlassCard hover className="cursor-pointer">
                  <div className="aspect-video bg-gradient-to-br from-violet-500/20 to-purple-500/20 rounded-lg flex items-center justify-center mb-4 border border-violet-500/30">
                    <PlayCircle className="w-12 h-12 text-violet-400" />
                  </div>
                  <h3 className="font-semibold text-white">{title}</h3>
                  <p className="text-sm text-slate-400 mt-1">Watch tutorial</p>
                </GlassCard>
              </motion.div>
            ))}
          </div>
        </motion.div>
      </div>
    </div>
  );
}
