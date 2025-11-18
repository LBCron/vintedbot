import { Fragment, useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { Dialog, Combobox, Transition } from '@headlessui/react';
import { useAuth } from '../contexts/AuthContext';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Search,
  Upload,
  FileText,
  BarChart3,
  Settings,
  HelpCircle,
  FileEdit,
  Send,
  MessageCircle,
  Clock,
  User,
  LogOut,
  Zap,
  TrendingUp,
  Calendar,
  Archive,
  Sparkles,
  Command,
} from 'lucide-react';
import { Badge } from './common/Badge';

interface CommandItem {
  id: string;
  name: string;
  description?: string;
  icon: any;
  action: () => void;
  category: 'pages' | 'actions' | 'drafts' | 'recent';
  keywords?: string[];
  badge?: string;
}

interface CommandPaletteProps {
  open: boolean;
  onClose: () => void;
}

// Mock data - in real app, this would come from API/state
const mockRecentDrafts = [
  { id: '1', title: 'Hoodie Nike gris', price: 30 },
  { id: '2', title: 'Jordan 1 High', price: 120 },
  { id: '3', title: 'T-shirt Supreme', price: 45 },
];

const mockRecentSearches = [
  'Hoodies > 50€',
  'Sneakers Nike',
  'Drafts non publiés',
];

export default function CommandPalette({ open, onClose }: CommandPaletteProps) {
  const navigate = useNavigate();
  // MEDIUM BUG FIX #11: Use AuthContext logout function
  const { logout } = useAuth();
  const [query, setQuery] = useState('');

  // Reset query when closing
  useEffect(() => {
    if (!open) {
      setQuery('');
    }
  }, [open]);

  // Define all available commands
  const allCommands: CommandItem[] = useMemo(() => [
    // Pages
    {
      id: 'page-dashboard',
      name: 'Dashboard',
      description: 'Vue d\'ensemble de votre activité',
      icon: TrendingUp,
      action: () => { navigate('/'); onClose(); },
      category: 'pages',
      keywords: ['home', 'accueil', 'overview'],
    },
    {
      id: 'page-upload',
      name: 'Upload Photos',
      description: 'Uploader et analyser vos photos',
      icon: Upload,
      action: () => { navigate('/upload'); onClose(); },
      category: 'pages',
      keywords: ['photo', 'image', 'télécharger', 'import'],
    },
    {
      id: 'page-drafts',
      name: 'Manage Drafts',
      description: 'Gérer vos brouillons',
      icon: FileText,
      action: () => { navigate('/drafts'); onClose(); },
      category: 'pages',
      keywords: ['brouillon', 'draft', 'liste'],
    },
    {
      id: 'page-publish',
      name: 'Publishing Schedule',
      description: 'Planifier vos publications',
      icon: Calendar,
      action: () => { navigate('/publish'); onClose(); },
      category: 'pages',
      keywords: ['publication', 'calendrier', 'schedule', 'planifier'],
      badge: 'NEW',
    },
    {
      id: 'page-messages',
      name: 'Messages',
      description: 'Gérer vos conversations',
      icon: MessageCircle,
      action: () => { navigate('/messages'); onClose(); },
      category: 'pages',
      keywords: ['chat', 'conversation', 'messaging'],
      badge: 'NEW',
    },
    {
      id: 'page-history',
      name: 'Activity History',
      description: 'Historique de vos actions',
      icon: Clock,
      action: () => { navigate('/history'); onClose(); },
      category: 'pages',
      keywords: ['historique', 'activity', 'timeline', 'actions'],
      badge: 'NEW',
    },
    {
      id: 'page-analytics',
      name: 'Analytics',
      description: 'Analyser vos performances',
      icon: BarChart3,
      action: () => { navigate('/analytics'); onClose(); },
      category: 'pages',
      keywords: ['statistiques', 'stats', 'performance', 'metrics'],
    },
    {
      id: 'page-templates',
      name: 'Templates',
      description: 'Gérer vos templates de description',
      icon: FileEdit,
      action: () => { navigate('/templates'); onClose(); },
      category: 'pages',
      keywords: ['template', 'modèle', 'description'],
    },
    {
      id: 'page-help',
      name: 'Help Center',
      description: 'Documentation et support',
      icon: HelpCircle,
      action: () => { navigate('/help'); onClose(); },
      category: 'pages',
      keywords: ['aide', 'support', 'faq', 'documentation'],
    },
    {
      id: 'page-settings',
      name: 'Settings',
      description: 'Paramètres de l\'application',
      icon: Settings,
      action: () => { navigate('/settings'); onClose(); },
      category: 'pages',
      keywords: ['paramètres', 'config', 'configuration', 'préférences'],
    },

    // Actions
    {
      id: 'action-new-draft',
      name: 'Create New Draft',
      description: 'Créer un brouillon manuellement',
      icon: FileEdit,
      action: () => {
        navigate('/drafts?action=create');
        onClose();
      },
      category: 'actions',
      keywords: ['créer', 'nouveau', 'draft', 'brouillon'],
    },
    {
      id: 'action-bulk-publish',
      name: 'Bulk Publish',
      description: 'Publier plusieurs drafts',
      icon: Send,
      action: () => {
        navigate('/drafts?action=bulk-publish');
        onClose();
      },
      category: 'actions',
      keywords: ['publier', 'masse', 'bulk', 'multiple'],
    },
    {
      id: 'action-export',
      name: 'Export Drafts',
      description: 'Exporter vos drafts en CSV',
      icon: Archive,
      action: () => {
        navigate('/drafts?action=export');
        onClose();
      },
      category: 'actions',
      keywords: ['exporter', 'télécharger', 'csv', 'export'],
    },
    {
      id: 'action-ai-optimize',
      name: 'AI Optimize All',
      description: 'Optimiser tous vos drafts avec l\'IA',
      icon: Sparkles,
      action: () => {
        navigate('/drafts?action=ai-optimize');
        onClose();
      },
      category: 'actions',
      keywords: ['ia', 'ai', 'optimiser', 'améliorer'],
      badge: 'PRO',
    },
    {
      id: 'action-logout',
      name: 'Logout',
      description: 'Se déconnecter',
      icon: LogOut,
      action: async () => {
        // MEDIUM BUG FIX #11: Call actual logout function
        await logout();
        navigate('/login');
        onClose();
      },
      category: 'actions',
      keywords: ['déconnexion', 'logout', 'quitter'],
    },

    // Recent drafts
    ...mockRecentDrafts.map((draft) => ({
      id: `draft-${draft.id}`,
      name: draft.title,
      description: `€${draft.price.toFixed(2)}`,
      icon: FileText,
      action: () => {
        navigate(`/drafts/${draft.id}`);
        onClose();
      },
      category: 'drafts' as const,
      keywords: [draft.title.toLowerCase(), 'draft', 'recent'],
    })),
  ], [navigate, onClose]);

  // Fuzzy search function
  const fuzzySearch = (text: string, search: string): boolean => {
    const searchLower = search.toLowerCase();
    const textLower = text.toLowerCase();

    // Direct match
    if (textLower.includes(searchLower)) return true;

    // Fuzzy match (each character in order)
    let searchIndex = 0;
    for (let i = 0; i < textLower.length && searchIndex < searchLower.length; i++) {
      if (textLower[i] === searchLower[searchIndex]) {
        searchIndex++;
      }
    }
    return searchIndex === searchLower.length;
  };

  // Filter commands based on query
  const filteredCommands = useMemo(() => {
    if (!query.trim()) {
      // Show recent/popular commands when no query
      return allCommands.filter(cmd =>
        cmd.category === 'pages' || cmd.category === 'drafts'
      );
    }

    const searchTerm = query.toLowerCase();
    return allCommands.filter((command) => {
      // Search in name
      if (fuzzySearch(command.name, searchTerm)) return true;

      // Search in description
      if (command.description && fuzzySearch(command.description, searchTerm)) return true;

      // Search in keywords
      if (command.keywords?.some(kw => fuzzySearch(kw, searchTerm))) return true;

      return false;
    });
  }, [query, allCommands]);

  // Group commands by category
  const groupedCommands = useMemo(() => {
    const groups: Record<string, CommandItem[]> = {
      pages: [],
      actions: [],
      drafts: [],
      recent: [],
    };

    filteredCommands.forEach((cmd) => {
      groups[cmd.category].push(cmd);
    });

    return groups;
  }, [filteredCommands]);

  const getCategoryLabel = (category: string) => {
    switch (category) {
      case 'pages': return 'Pages';
      case 'actions': return 'Actions rapides';
      case 'drafts': return 'Drafts récents';
      case 'recent': return 'Récent';
      default: return category;
    }
  };

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'pages': return Command;
      case 'actions': return Zap;
      case 'drafts': return FileText;
      case 'recent': return Clock;
      default: return Search;
    }
  };

  return (
    <Transition.Root show={open} as={Fragment} appear>
      <Dialog as="div" className="relative z-50" onClose={onClose}>
        {/* Backdrop */}
        <Transition.Child
          as={Fragment}
          enter="ease-out duration-300"
          enterFrom="opacity-0"
          enterTo="opacity-100"
          leave="ease-in duration-200"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <div className="fixed inset-0 bg-gray-900/50 backdrop-blur-sm" />
        </Transition.Child>

        <div className="fixed inset-0 z-10 overflow-y-auto p-4 sm:p-6 md:p-20">
          <Transition.Child
            as={Fragment}
            enter="ease-out duration-300"
            enterFrom="opacity-0 scale-95"
            enterTo="opacity-100 scale-100"
            leave="ease-in duration-200"
            leaveFrom="opacity-100 scale-100"
            leaveTo="opacity-0 scale-95"
          >
            <Dialog.Panel className="mx-auto max-w-2xl transform overflow-hidden rounded-xl bg-white dark:bg-gray-800 shadow-2xl ring-1 ring-black/5 dark:ring-white/10 transition-all">
              <Combobox onChange={(item: CommandItem) => item.action()}>
                {/* Search Input */}
                <div className="relative">
                  <Search className="pointer-events-none absolute left-4 top-3.5 h-5 w-5 text-gray-400" />
                  <Combobox.Input
                    className="h-12 w-full border-0 bg-transparent pl-11 pr-4 text-gray-900 dark:text-white placeholder:text-gray-400 focus:ring-0 sm:text-sm"
                    placeholder="Search pages, actions, drafts..."
                    onChange={(event) => setQuery(event.target.value)}
                    value={query}
                    autoComplete="off"
                  />
                  <div className="absolute right-4 top-3 flex items-center gap-1">
                    <kbd className="hidden sm:inline-block px-2 py-1 text-xs font-semibold text-gray-500 dark:text-gray-400 bg-gray-100 dark:bg-gray-700 rounded">
                      ESC
                    </kbd>
                  </div>
                </div>

                {/* Results */}
                {filteredCommands.length > 0 ? (
                  <Combobox.Options
                    static
                    className="max-h-96 scroll-py-2 overflow-y-auto py-2 text-sm text-gray-800 dark:text-gray-200"
                  >
                    {Object.entries(groupedCommands).map(([category, commands]) => {
                      if (commands.length === 0) return null;

                      const CategoryIcon = getCategoryIcon(category);

                      return (
                        <div key={category}>
                          {/* Category Header */}
                          <div className="flex items-center gap-2 px-4 py-2 text-xs font-semibold text-gray-500 dark:text-gray-400">
                            <CategoryIcon className="w-4 h-4" />
                            {getCategoryLabel(category)}
                          </div>

                          {/* Commands */}
                          {commands.map((command) => (
                            <Combobox.Option
                              key={command.id}
                              value={command}
                              className={({ active }) =>
                                `cursor-pointer select-none px-4 py-3 flex items-center gap-3 ${
                                  active
                                    ? 'bg-primary-50 dark:bg-primary-900/20'
                                    : ''
                                }`
                              }
                            >
                              {({ active }) => (
                                <>
                                  {/* Icon */}
                                  <div
                                    className={`flex-shrink-0 w-10 h-10 rounded-lg flex items-center justify-center ${
                                      active
                                        ? 'bg-primary-100 dark:bg-primary-900/40'
                                        : 'bg-gray-100 dark:bg-gray-700'
                                    }`}
                                  >
                                    <command.icon
                                      className={`w-5 h-5 ${
                                        active
                                          ? 'text-primary-600 dark:text-primary-400'
                                          : 'text-gray-600 dark:text-gray-400'
                                      }`}
                                    />
                                  </div>

                                  {/* Text */}
                                  <div className="flex-1 min-w-0">
                                    <div className="flex items-center gap-2">
                                      <p className="font-medium text-gray-900 dark:text-white truncate">
                                        {command.name}
                                      </p>
                                      {command.badge && (
                                        <Badge
                                          variant={command.badge === 'NEW' ? 'primary' : 'warning'}
                                          size="sm"
                                        >
                                          {command.badge}
                                        </Badge>
                                      )}
                                    </div>
                                    {command.description && (
                                      <p className="text-xs text-gray-600 dark:text-gray-400 truncate">
                                        {command.description}
                                      </p>
                                    )}
                                  </div>

                                  {/* Shortcut hint */}
                                  {active && (
                                    <kbd className="hidden sm:inline-block px-2 py-1 text-xs font-semibold text-gray-500 dark:text-gray-400 bg-gray-100 dark:bg-gray-700 rounded">
                                      ↵
                                    </kbd>
                                  )}
                                </>
                              )}
                            </Combobox.Option>
                          ))}
                        </div>
                      );
                    })}
                  </Combobox.Options>
                ) : (
                  /* Empty State */
                  <div className="px-6 py-14 text-center sm:px-14">
                    <Search className="mx-auto h-12 w-12 text-gray-400" />
                    <p className="mt-4 text-sm font-semibold text-gray-900 dark:text-white">
                      No results found
                    </p>
                    <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
                      {query
                        ? `No results for "${query}". Try a different search term.`
                        : 'Start typing to search pages, actions, and drafts.'}
                    </p>
                  </div>
                )}

                {/* Footer */}
                <div className="flex items-center justify-between border-t border-gray-200 dark:border-gray-700 px-4 py-3 text-xs text-gray-600 dark:text-gray-400">
                  <div className="flex items-center gap-4">
                    <div className="flex items-center gap-1">
                      <kbd className="px-2 py-1 font-semibold bg-gray-100 dark:bg-gray-700 rounded">↑↓</kbd>
                      <span>Navigate</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <kbd className="px-2 py-1 font-semibold bg-gray-100 dark:bg-gray-700 rounded">↵</kbd>
                      <span>Select</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <kbd className="px-2 py-1 font-semibold bg-gray-100 dark:bg-gray-700 rounded">ESC</kbd>
                      <span>Close</span>
                    </div>
                  </div>
                  <div className="hidden sm:block">
                    Tip: Use <kbd className="px-2 py-1 font-semibold bg-gray-100 dark:bg-gray-700 rounded">⌘K</kbd> anytime
                  </div>
                </div>
              </Combobox>
            </Dialog.Panel>
          </Transition.Child>
        </div>
      </Dialog>
    </Transition.Root>
  );
}
