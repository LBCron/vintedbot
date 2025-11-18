import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Plus,
  Users,
  TrendingUp,
  Eye,
  Package,
  DollarSign,
  CheckCircle2,
  XCircle,
  MoreVertical,
  Settings,
  Trash2,
  RefreshCw,
  AlertCircle,
  Zap,
  Sparkles,
  EyeOff
} from 'lucide-react';
import { accountsAPI } from '../api/client';
import LoadingSpinner from '../components/common/LoadingSpinner';
import toast from 'react-hot-toast';
import type { VintedAccount } from '../types';
import { logger } from '../utils/logger';
import { formatPrice, formatNumber, cn } from '../lib/utils';

export default function Accounts() {
  const [accounts, setAccounts] = useState<VintedAccount[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);
  const [addMode, setAddMode] = useState<'auto' | 'manual'>('auto');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [activeMenu, setActiveMenu] = useState<string | null>(null);

  // Auto login form
  const [autoLogin, setAutoLogin] = useState({ email: '', password: '', nickname: 'Mon Compte Vinted' });

  // Manual form
  const [newAccount, setNewAccount] = useState({ name: '', cookie: '', user_agent: '' });

  useEffect(() => {
    loadAccounts();
  }, []);

  const loadAccounts = async () => {
    try {
      const response = await accountsAPI.getAccounts();
      // MEDIUM BUG FIX #9: Safe access to nested response data
      setAccounts(response?.data?.accounts || []);
    } catch (error) {
      logger.error('Failed to load accounts', error);
      toast.error('Erreur lors du chargement des comptes');
    } finally {
      setLoading(false);
    }
  };

  const handleAddAccount = async () => {
    setIsSubmitting(true);
    try {
      // Both modes now use manual cookie entry (auto mode = simplified instructions)
      const payload = {
        nickname: newAccount.name || 'Mon Compte Vinted',
        cookie: newAccount.cookie,
        user_agent: newAccount.user_agent || 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
      };

      await accountsAPI.addAccount(payload);
      toast.success('Compte Vinted ajouté avec succès !');

      setShowAddModal(false);
      setAutoLogin({ email: '', password: '', nickname: 'Mon Compte Vinted' });
      setNewAccount({ name: '', cookie: '', user_agent: '' });
      setShowPassword(false);
      loadAccounts();
    } catch (error: any) {
      const errorMsg = error.response?.data?.detail || 'Erreur lors de l\'ajout du compte';
      toast.error(errorMsg);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleSwitch = async (accountId: string) => {
    try {
      await accountsAPI.switchAccount(accountId);
      toast.success('Compte changé avec succès !');
      loadAccounts();
    } catch (error) {
      toast.error('Erreur lors du changement de compte');
    }
  };

  const handleDelete = async (accountId: string) => {
    if (!confirm('Supprimer ce compte ?')) return;

    try {
      await accountsAPI.deleteAccount(accountId);
      toast.success('Compte supprimé');
      loadAccounts();
    } catch (error) {
      toast.error('Erreur lors de la suppression');
    }
  };

  // Calculate global stats from accounts
  const globalStats = {
    total_listings: accounts.reduce((sum, acc) => sum + (acc.listings_count || 0), 0),
    total_sold: accounts.reduce((sum, acc) => sum + (acc.sold_count || 0), 0),
    total_revenue: accounts.reduce((sum, acc) => sum + (acc.revenue || 0), 0),
    total_views: accounts.reduce((sum, acc) => sum + (acc.views || 0), 0),
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <LoadingSpinner size="large" />
      </div>
    );
  }

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
              <Users className="w-10 h-10" />
              <h1 className="text-4xl font-bold">Comptes Vinted</h1>
            </div>
            <p className="text-brand-100 text-lg max-w-2xl">
              Gérez plusieurs comptes Vinted depuis une seule interface.
              Synchronisez vos statistiques et optimisez vos ventes.
            </p>
          </motion.div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 -mt-6">
        {/* Global Stats */}
        <div className="grid md:grid-cols-4 gap-6 mb-8">
          <StatsCard
            icon={Package}
            label="Total Annonces"
            value={formatNumber(globalStats.total_listings)}
            color="blue"
            delay={0}
          />
          <StatsCard
            icon={CheckCircle2}
            label="Articles Vendus"
            value={formatNumber(globalStats.total_sold)}
            color="green"
            delay={0.1}
          />
          <StatsCard
            icon={DollarSign}
            label="Revenus Total"
            value={formatPrice(globalStats.total_revenue)}
            color="purple"
            delay={0.2}
          />
          <StatsCard
            icon={Eye}
            label="Vues Totales"
            value={formatNumber(globalStats.total_views)}
            color="orange"
            delay={0.3}
          />
        </div>

        {/* Accounts Grid */}
        <div className="pb-12">
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {/* Add Account Card */}
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              whileHover={{ scale: 1.02 }}
              onClick={() => setShowAddModal(true)}
              className="bg-gradient-to-br from-brand-500 to-purple-600 rounded-2xl p-8 flex flex-col items-center justify-center cursor-pointer hover:shadow-2xl transition-all text-white min-h-[280px]"
            >
              <div className="w-20 h-20 bg-white/20 rounded-full flex items-center justify-center mb-4 backdrop-blur-sm">
                <Plus className="w-10 h-10" />
              </div>
              <h3 className="text-2xl font-bold mb-2">Ajouter un compte</h3>
              <p className="text-brand-100 text-center text-sm">
                Connectez un nouveau compte Vinted
              </p>
            </motion.div>

            {/* Account Cards */}
            {accounts.map((account, index) => (
              <AccountCard
                key={account.id}
                account={account}
                index={index + 1}
                activeMenu={activeMenu}
                onToggleMenu={(id) => setActiveMenu(activeMenu === id ? null : id)}
                onSync={() => toast.success('Synchronisation en cours...')}
                onSwitch={() => handleSwitch(account.id)}
                onDelete={() => handleDelete(account.id)}
              />
            ))}
          </div>
        </div>
      </div>

      {/* Add Account Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4 overflow-y-auto">
          <div className="bg-white rounded-lg max-w-md w-full my-8 max-h-[90vh] flex flex-col">
            <div className="flex items-center justify-between p-6 pb-4 border-b">
              <h2 className="text-xl font-bold text-gray-900">Connecter un compte Vinted</h2>
              <button
                type="button"
                onClick={() => {
                  setShowAddModal(false);
                  setAutoLogin({ email: '', password: '', nickname: 'Mon Compte Vinted' });
                  setNewAccount({ name: '', cookie: '', user_agent: '' });
                  setShowPassword(false);
                }}
                className="text-gray-400 hover:text-gray-600 p-1"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div className="overflow-y-auto p-6 pt-4">
            {/* Toggle between Guided and Advanced */}
            <div className="flex gap-2 mb-6 p-1 bg-gray-100 rounded-lg">
              <button
                type="button"
                onClick={() => setAddMode('auto')}
                className={`flex-1 py-2 px-4 rounded-lg font-medium transition-all ${
                  addMode === 'auto'
                    ? 'bg-primary-600 text-white shadow-sm'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                <Sparkles className="w-4 h-4 inline mr-1" /> Mode Guidé
              </button>
              <button
                type="button"
                onClick={() => setAddMode('manual')}
                className={`flex-1 py-2 px-4 rounded-lg font-medium transition-all ${
                  addMode === 'manual'
                    ? 'bg-primary-600 text-white shadow-sm'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                Mode Avancé
              </button>
            </div>

            {addMode === 'auto' ? (
              <div className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-4">
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                    <h3 className="font-semibold text-blue-900 mb-2 text-sm">Ordinateur</h3>
                    <p className="text-xs text-blue-800 mb-3">
                      Extension Chrome - Capture automatique en 1 clic
                    </p>
                    <a
                      href="/download-extension.html"
                      target="_blank"
                      className="inline-block w-full text-center px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium text-sm transition-colors"
                    >
                      Extension Chrome
                    </a>
                  </div>

                  <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
                    <h3 className="font-semibold text-purple-900 mb-2 text-sm">iPhone/Android</h3>
                    <p className="text-xs text-purple-800 mb-3">
                      Bookmarklet mobile - Capture en 1 tap
                    </p>
                    <a
                      href="/mobile-connector.html"
                      target="_blank"
                      className="inline-block w-full text-center px-3 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 font-medium text-sm transition-colors"
                    >
                      Version Mobile
                    </a>
                  </div>
                </div>

                <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-4">
                  <h3 className="font-semibold text-green-900 mb-2">Méthode Manuelle - 3 étapes simples</h3>
                  <ol className="text-sm text-green-800 space-y-2">
                    <li className="flex items-start gap-2">
                      <span className="font-bold min-w-[20px]">1.</span>
                      <span>Ouvrez <a href="https://www.vinted.fr" target="_blank" rel="noopener noreferrer" className="underline font-semibold">vinted.fr</a> et connectez-vous</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="font-bold min-w-[20px]">2.</span>
                      <span>Appuyez sur <kbd className="px-2 py-1 bg-white rounded border">F12</kbd> → Onglet <strong>Application</strong> (ou Storage) → <strong>Cookies</strong> → vinted.fr</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="font-bold min-w-[20px]">3.</span>
                      <span>Trouvez le cookie nommé <code className="bg-green-100 px-2 py-0.5 rounded font-bold">_vinted_fr_session</code> et copiez UNIQUEMENT sa valeur (pas son nom, juste la valeur)</span>
                    </li>
                  </ol>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Nom du compte
                  </label>
                  <input
                    type="text"
                    value={newAccount.name}
                    onChange={(e) => setNewAccount({ ...newAccount, name: e.target.value })}
                    className="input"
                    placeholder="Mon Compte Principal"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Cookie _vinted_fr_session
                  </label>
                  <textarea
                    value={newAccount.cookie}
                    onChange={(e) => setNewAccount({ ...newAccount, cookie: e.target.value })}
                    className="input min-h-[100px] font-mono text-xs"
                    placeholder="Collez ici UNIQUEMENT la valeur du cookie nommé _vinted_fr_session (pas les autres cookies)"
                  />
                  <div className="mt-2 space-y-1">
                    <p className="text-xs text-gray-500">
                      Le cookie ressemble à: BAh7CEkiD3Nlc3Npb25faWQGOgZF...
                    </p>
                    <p className="text-xs text-yellow-700 bg-yellow-50 border border-yellow-200 rounded p-2">
                      <strong>Important:</strong> Copiez UNIQUEMENT la valeur du cookie nommé <code className="bg-yellow-100 px-1 rounded font-semibold">_vinted_fr_session</code> (pas les autres cookies comme v-udt, etc.)
                    </p>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    User Agent (optionnel)
                  </label>
                  <input
                    type="text"
                    value={newAccount.user_agent}
                    onChange={(e) => setNewAccount({ ...newAccount, user_agent: e.target.value })}
                    className="input text-xs font-mono"
                    placeholder="Laissez vide pour utiliser le user agent par défaut"
                  />
                </div>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3 mb-4">
                  <p className="text-sm text-yellow-800">
                    Pour les utilisateurs avancés - entrez manuellement vos cookies
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Nom du compte
                  </label>
                  <input
                    type="text"
                    value={newAccount.name}
                    onChange={(e) => setNewAccount({ ...newAccount, name: e.target.value })}
                    className="input"
                    placeholder="Mon Compte Principal"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Cookie _vinted_fr_session
                  </label>
                  <textarea
                    value={newAccount.cookie}
                    onChange={(e) => setNewAccount({ ...newAccount, cookie: e.target.value })}
                    className="input min-h-[80px] font-mono text-xs"
                    placeholder="Collez uniquement la valeur du cookie _vinted_fr_session..."
                  />
                  <p className="text-xs text-yellow-700 bg-yellow-50 border border-yellow-200 rounded p-2 mt-2">
                    <strong>Important:</strong> Uniquement le cookie <code className="bg-yellow-100 px-1 rounded font-semibold">_vinted_fr_session</code>
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    User Agent
                  </label>
                  <input
                    type="text"
                    value={newAccount.user_agent}
                    onChange={(e) => setNewAccount({ ...newAccount, user_agent: e.target.value })}
                    className="input text-xs font-mono"
                    placeholder="Mozilla/5.0..."
                  />
                </div>
              </div>
            )}
            </div>

            <div className="flex gap-3 p-6 pt-4 border-t bg-gray-50">
              <button
                type="button"
                onClick={() => {
                  setShowAddModal(false);
                  setAutoLogin({ email: '', password: '', nickname: 'Mon Compte Vinted' });
                  setNewAccount({ name: '', cookie: '', user_agent: '' });
                  setShowPassword(false);
                }}
                disabled={isSubmitting}
                className="flex-1 px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 font-medium disabled:opacity-50"
              >
                Annuler
              </button>
              <button
                type="button"
                onClick={handleAddAccount}
                disabled={
                  isSubmitting ||
                  !newAccount.name ||
                  !newAccount.cookie
                }
                className="flex-1 btn-primary disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {isSubmitting ? (
                  <>
                    <LoadingSpinner size="small" />
                    Ajout en cours...
                  </>
                ) : (
                  'Connecter'
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function StatsCard({ icon: Icon, label, value, color, delay }: any) {
  const colorClasses = {
    blue: 'from-blue-50 to-blue-100 text-blue-600',
    green: 'from-green-50 to-green-100 text-green-600',
    purple: 'from-purple-50 to-purple-100 text-purple-600',
    orange: 'from-orange-50 to-orange-100 text-orange-600',
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay }}
      className="bg-white rounded-2xl shadow-lg p-6 hover:shadow-xl transition-shadow"
    >
      <div className={cn(
        "w-14 h-14 rounded-2xl flex items-center justify-center mb-4 bg-gradient-to-br",
        colorClasses[color as keyof typeof colorClasses]
      )}>
        <Icon className="w-7 h-7" />
      </div>
      <p className="text-sm text-gray-600 mb-1">{label}</p>
      <p className="text-2xl font-bold text-gray-900">{value}</p>
    </motion.div>
  );
}

function AccountCard({ account, index, activeMenu, onToggleMenu, onSync, onSwitch, onDelete }: any) {
  const getAccountStatus = (account: any) => {
    if (account.is_active) {
      return { color: 'bg-green-100 text-green-700', icon: CheckCircle2, label: 'Actif' };
    }
    return { color: 'bg-gray-100 text-gray-700', icon: AlertCircle, label: 'Inactif' };
  };

  const config = getAccountStatus(account);
  const StatusIcon = config.icon;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.1 }}
      whileHover={{ y: -4 }}
      className="bg-white rounded-2xl border-2 border-gray-200 p-6 hover:border-brand-300 hover:shadow-xl transition-all relative"
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-full bg-gradient-to-br from-brand-500 to-purple-600 flex items-center justify-center text-white font-bold text-lg">
            {account.name?.[0]?.toUpperCase() || 'V'}
          </div>
          <div>
            <h3 className="font-semibold text-gray-900">{account.name}</h3>
            {account.email && (
              <p className="text-sm text-gray-500">{account.email}</p>
            )}
          </div>
        </div>

        {/* Menu Button */}
        <div className="relative">
          <button
            onClick={() => onToggleMenu(account.id)}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <MoreVertical className="w-5 h-5 text-gray-600" />
          </button>

          <AnimatePresence>
            {activeMenu === account.id && (
              <motion.div
                initial={{ opacity: 0, scale: 0.95, y: -10 }}
                animate={{ opacity: 1, scale: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.95, y: -10 }}
                className="absolute right-0 top-full mt-2 w-48 bg-white rounded-xl shadow-xl border border-gray-200 py-2 z-10"
              >
                <button
                  onClick={() => {
                    onSync();
                    onToggleMenu(account.id);
                  }}
                  className="w-full px-4 py-2 text-left flex items-center gap-2 hover:bg-gray-50 transition-colors text-gray-700"
                >
                  <RefreshCw className="w-4 h-4" />
                  Synchroniser
                </button>
                {!account.is_active && (
                  <button
                    onClick={() => {
                      onSwitch();
                      onToggleMenu(account.id);
                    }}
                    className="w-full px-4 py-2 text-left flex items-center gap-2 hover:bg-gray-50 transition-colors text-gray-700"
                  >
                    <Settings className="w-4 h-4" />
                    Activer
                  </button>
                )}
                <div className="my-1 border-t border-gray-100" />
                <button
                  onClick={() => {
                    onDelete();
                    onToggleMenu(account.id);
                  }}
                  className="w-full px-4 py-2 text-left flex items-center gap-2 hover:bg-error-50 transition-colors text-error-600"
                >
                  <Trash2 className="w-4 h-4" />
                  Supprimer
                </button>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>

      {/* Status Badge */}
      <div className="mb-4">
        <span className={cn(
          "inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold",
          config.color
        )}>
          <StatusIcon className="w-3.5 h-3.5" />
          {config.label}
        </span>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 gap-4 mb-4">
        <div className="bg-gray-50 rounded-xl p-3">
          <p className="text-xs text-gray-600 mb-1">Annonces</p>
          <p className="text-lg font-bold text-gray-900">{account.listings_count || 0}</p>
        </div>
        <div className="bg-gray-50 rounded-xl p-3">
          <p className="text-xs text-gray-600 mb-1">Vendus</p>
          <p className="text-lg font-bold text-gray-900">{account.sold_count || 0}</p>
        </div>
        <div className="bg-gray-50 rounded-xl p-3">
          <p className="text-xs text-gray-600 mb-1">Revenus</p>
          <p className="text-lg font-bold text-gray-900">{formatPrice(account.revenue || 0)}</p>
        </div>
        <div className="bg-gray-50 rounded-xl p-3">
          <p className="text-xs text-gray-600 mb-1">Vues</p>
          <p className="text-lg font-bold text-gray-900">{formatNumber(account.views || 0)}</p>
        </div>
      </div>

      {/* Last Sync */}
      {account.last_used && (
        <div className="flex items-center justify-between text-xs text-gray-500 pt-4 border-t border-gray-100">
          <span className="flex items-center gap-1">
            <RefreshCw className="w-3 h-3" />
            Sync: {new Date(account.last_used).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })}
          </span>
          <button
            onClick={onSync}
            className="flex items-center gap-1 text-brand-600 hover:text-brand-700 font-medium transition-colors"
          >
            <Zap className="w-3 h-3" />
            Sync now
          </button>
        </div>
      )}
    </motion.div>
  );
}
