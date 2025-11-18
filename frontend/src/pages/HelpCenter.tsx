import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Search,
  ChevronDown,
  BookOpen,
  Video,
  MessageCircle,
  Mail,
  Clock,
  HelpCircle
} from 'lucide-react';
import { cn } from '../lib/utils';

export default function HelpCenter() {
  const [searchQuery, setSearchQuery] = useState('');
  const [openFAQ, setOpenFAQ] = useState<string | null>(null);

  const faqs = [
    {
      id: '1',
      question: 'Comment uploader mes photos ?',
      answer: 'Glissez-déposez jusqu\'à 20 photos dans la zone d\'upload, ou cliquez pour sélectionner. L\'IA analysera automatiquement vos photos et générera une description optimisée.'
    },
    {
      id: '2',
      question: 'Comment fonctionne la génération IA ?',
      answer: 'Notre IA utilise GPT-4 Vision pour analyser vos photos et détecter automatiquement la marque, la taille, la couleur et l\'état. Elle génère ensuite un titre et une description optimisés pour maximiser vos ventes.'
    },
    {
      id: '3',
      question: 'Comment optimiser mes prix ?',
      answer: 'Notre algorithme ML analyse 50,000+ ventes réelles pour suggérer le prix optimal. Vous pouvez choisir entre 4 stratégies : vente rapide, équilibré, premium ou compétitif.'
    },
    {
      id: '4',
      question: 'Puis-je modifier les drafts générés par l\'IA ?',
      answer: 'Absolument ! Tous les drafts sont entièrement modifiables. Vous pouvez ajuster le titre, la description, le prix, ajouter/supprimer des photos, etc.'
    }
  ];

  const guides = [
    {
      title: 'Guide de démarrage rapide',
      duration: '5 min',
      icon: <BookOpen className="w-5 h-5" />
    },
    {
      title: 'Guide des fonctionnalités IA',
      duration: '10 min',
      icon: <Video className="w-5 h-5" />
    },
    {
      title: 'Optimisation des prix',
      duration: '8 min',
      icon: <BookOpen className="w-5 h-5" />
    }
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Hero Section */}
      <div className="bg-gradient-to-br from-brand-600 via-brand-500 to-purple-600 text-white">
        <div className="max-w-4xl mx-auto px-6 py-20 text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
          >
            <HelpCircle className="w-16 h-16 mx-auto mb-6" />
            <h1 className="text-5xl font-bold mb-4">Comment pouvons-nous vous aider ?</h1>
            <p className="text-xl text-brand-100 mb-8">
              Recherchez dans notre base de connaissances ou contactez le support
            </p>

            {/* Search Bar */}
            <div className="relative max-w-2xl mx-auto">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-6 h-6 text-gray-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Rechercher un article d'aide..."
                className="w-full pl-14 pr-6 py-4 bg-white text-gray-900 rounded-2xl text-lg focus:outline-none focus:ring-4 focus:ring-white/20"
              />
            </div>
          </motion.div>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-6 -mt-12 pb-20">
        {/* Quick Actions */}
        <div className="grid md:grid-cols-2 gap-6 mb-16">
          <QuickAction
            icon={<MessageCircle className="w-8 h-8" />}
            title="Live Chat"
            description="Chattez avec notre équipe en temps réel"
            action="Démarrer"
            color="brand"
          />
          <QuickAction
            icon={<Mail className="w-8 h-8" />}
            title="Email Support"
            description="Réponse sous 2 heures en moyenne"
            action="Envoyer"
            color="purple"
          />
        </div>

        {/* Guides */}
        <div className="mb-16">
          <h2 className="text-3xl font-bold text-gray-900 mb-8">Guides populaires</h2>
          <div className="grid md:grid-cols-3 gap-6">
            {guides.map((guide, index) => (
              <motion.div
                key={guide.title}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                whileHover={{ y: -4 }}
                className="bg-white rounded-2xl p-6 border border-gray-200 hover:border-brand-300 hover:shadow-lg transition-all cursor-pointer"
              >
                <div className="w-12 h-12 bg-brand-50 rounded-xl flex items-center justify-center text-brand-600 mb-4">
                  {guide.icon}
                </div>
                <h3 className="font-semibold text-gray-900 mb-2">{guide.title}</h3>
                <div className="flex items-center gap-2 text-sm text-gray-500">
                  <Clock className="w-4 h-4" />
                  {guide.duration}
                </div>
              </motion.div>
            ))}
          </div>
        </div>

        {/* FAQ */}
        <div>
          <h2 className="text-3xl font-bold text-gray-900 mb-8">Questions fréquentes</h2>
          <div className="space-y-4">
            {faqs.map((faq) => (
              <motion.div
                key={faq.id}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="bg-white rounded-2xl border border-gray-200 overflow-hidden"
              >
                <button
                  onClick={() => setOpenFAQ(openFAQ === faq.id ? null : faq.id)}
                  className="w-full px-6 py-5 flex items-center justify-between text-left hover:bg-gray-50 transition-colors"
                >
                  <span className="font-semibold text-gray-900">{faq.question}</span>
                  <motion.div
                    animate={{ rotate: openFAQ === faq.id ? 180 : 0 }}
                    transition={{ duration: 0.2 }}
                  >
                    <ChevronDown className="w-5 h-5 text-gray-600" />
                  </motion.div>
                </button>

                <AnimatePresence>
                  {openFAQ === faq.id && (
                    <motion.div
                      initial={{ height: 0 }}
                      animate={{ height: 'auto' }}
                      exit={{ height: 0 }}
                      transition={{ duration: 0.2 }}
                      className="overflow-hidden"
                    >
                      <div className="px-6 pb-5 text-gray-600 leading-relaxed">
                        {faq.answer}
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </motion.div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

function QuickAction({ icon, title, description, action, color }: any) {
  const colors: any = {
    brand: 'from-brand-50 to-brand-100 border-brand-200',
    purple: 'from-purple-50 to-purple-100 border-purple-200'
  };

  return (
    <motion.div
      whileHover={{ y: -4 }}
      className={cn(
        "bg-gradient-to-br rounded-2xl p-8 border-2 cursor-pointer shadow-lg hover:shadow-xl transition-all",
        colors[color]
      )}
    >
      <div className="flex items-start gap-4">
        <div className="w-16 h-16 bg-white rounded-2xl flex items-center justify-center text-brand-600 shadow-sm">
          {icon}
        </div>
        <div className="flex-1">
          <h3 className="text-xl font-semibold text-gray-900 mb-2">{title}</h3>
          <p className="text-gray-600 mb-4">{description}</p>
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            className="btn btn-primary btn-sm"
          >
            {action}
          </motion.button>
        </div>
      </div>
    </motion.div>
  );
}
