import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Plus, Users, Check, Eye, EyeOff, X } from 'lucide-react';
import { accountsAPI } from '../api/client';
import { GlassCard } from '../components/ui/GlassCard';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { EmptyState } from '../components/ui/EmptyState';
import toast from 'react-hot-toast';
import type { VintedAccount } from '../types';
import { logger } from '../utils/logger';

export default function Accounts() {
  const [accounts, setAccounts] = useState<VintedAccount[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);
  const [addMode, setAddMode] = useState<'auto' | 'manual'>('auto');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const [newAccount, setNewAccount] = useState({ name: '', cookie: '', user_agent: '' });

  useEffect(() => {
    loadAccounts();
  }, []);

  const loadAccounts = async () => {
    try {
      const response = await accountsAPI.getAccounts();
      setAccounts(response.data.accounts || []);
    } catch (error) {
      logger.error('Failed to load accounts', error);
      toast.error('Failed to load accounts');
    } finally {
      setLoading(false);
    }
  };

  const handleAddAccount = async () => {
    setIsSubmitting(true);
    try {
      const payload = {
        nickname: newAccount.name || 'Mon Compte Vinted',
        cookie: newAccount.cookie,
        user_agent: newAccount.user_agent || 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
      };

      await accountsAPI.addAccount(payload);
      toast.success('Compte Vinted ajouté avec succès !');

      setShowAddModal(false);
      setNewAccount({ name: '', cookie: '', user_agent: '' });
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
      toast.success('Account switched successfully!');
      loadAccounts();
    } catch (error) {
      toast.error('Failed to switch account');
    }
  };

  const handleDelete = async (accountId: string) => {
    if (!confirm('Delete this account?')) return;

    try {
      await accountsAPI.deleteAccount(accountId);
      toast.success('Account deleted');
      loadAccounts();
    } catch (error) {
      toast.error('Failed to delete account');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 p-8">
        <div className="max-w-7xl mx-auto">
          <GlassCard className="p-12">
            <div className="flex flex-col items-center justify-center space-y-4">
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                className="w-12 h-12 border-4 border-violet-500/30 border-t-violet-500 rounded-full"
              />
              <p className="text-slate-400">Loading accounts...</p>
            </div>
          </GlassCard>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      <div className="max-w-7xl mx-auto p-4 md:p-6 lg:p-8 space-y-8">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex items-center justify-between"
        >
          <div className="flex items-center gap-4">
            <div className="p-4 bg-gradient-to-br from-violet-500 to-purple-600 rounded-2xl shadow-lg shadow-violet-500/50">
              <Users className="w-8 h-8 text-white" />
            </div>
            <div>
              <h1 className="text-4xl md:text-5xl font-bold bg-gradient-to-r from-white via-violet-200 to-purple-200 bg-clip-text text-transparent">
                Multi-Account Management
              </h1>
              <div className="flex items-center gap-2 mt-1">
                <Badge variant="warning" size="md">
                  PREMIUM FEATURE
                </Badge>
                <p className="text-slate-400">
                  Manage multiple Vinted accounts
                </p>
              </div>
            </div>
          </div>
          <Button
            onClick={() => setShowAddModal(true)}
            icon={Plus}
          >
            Add Account
          </Button>
        </motion.div>

        {/* Accounts Grid */}
        {accounts.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {accounts.map((account, index) => (
              <motion.div
                key={account.id}
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: index * 0.1 }}
              >
                <GlassCard hover className={account.is_active ? 'border-green-500/50' : ''}>
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-3">
                      <div className={`p-3 rounded-xl ${account.is_active ? 'bg-green-500/20 border border-green-500/30' : 'bg-white/5 border border-white/10'}`}>
                        <Users className={`w-6 h-6 ${account.is_active ? 'text-green-400' : 'text-slate-400'}`} />
                      </div>
                      <div>
                        <h3 className="font-semibold text-white">{account.name}</h3>
                        {account.email && (
                          <p className="text-sm text-slate-400">{account.email}</p>
                        )}
                      </div>
                    </div>
                    {account.is_active && (
                      <Badge variant="success" size="sm">
                        <Check className="w-3 h-3" />
                        Active
                      </Badge>
                    )}
                  </div>

                  <div className="text-sm text-slate-400 mb-4 space-y-1">
                    <p>Created: {new Date(account.created_at).toLocaleDateString()}</p>
                    {account.last_used && (
                      <p>Last used: {new Date(account.last_used).toLocaleDateString()}</p>
                    )}
                  </div>

                  <div className="flex gap-2">
                    {!account.is_active && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleSwitch(account.id)}
                        className="flex-1"
                      >
                        Switch
                      </Button>
                    )}
                    <Button
                      variant="danger"
                      size="sm"
                      onClick={() => handleDelete(account.id)}
                    >
                      Delete
                    </Button>
                  </div>
                </GlassCard>
              </motion.div>
            ))}
          </div>
        ) : (
          <EmptyState
            icon={Users}
            title="No accounts added yet"
            description="Add your first Vinted account to get started"
            action={{
              label: "Add Your First Account",
              onClick: () => setShowAddModal(true)
            }}
          />
        )}

        {/* Add Account Modal */}
        <AnimatePresence>
          {showAddModal && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4 overflow-y-auto"
              onClick={() => setShowAddModal(false)}
            >
              <motion.div
                initial={{ scale: 0.9, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                exit={{ scale: 0.9, opacity: 0 }}
                onClick={(e) => e.stopPropagation()}
                className="my-8 max-w-md w-full max-h-[90vh] flex flex-col"
              >
                <GlassCard className="overflow-hidden">
                  {/* Header */}
                  <div className="flex items-center justify-between pb-4 mb-4 border-b border-white/10">
                    <h2 className="text-2xl font-bold text-white">Connecter un compte Vinted</h2>
                    <button
                      onClick={() => setShowAddModal(false)}
                      className="p-2 hover:bg-white/10 rounded-lg transition-colors"
                    >
                      <X className="w-6 h-6 text-slate-400" />
                    </button>
                  </div>

                  <div className="space-y-6 overflow-y-auto max-h-[60vh]">
                    {/* Mode Toggle */}
                    <div className="flex gap-2 p-1 bg-white/5 rounded-xl border border-white/10">
                      <button
                        onClick={() => setAddMode('auto')}
                        className={`flex-1 py-2 px-4 rounded-lg font-medium transition-all ${
                          addMode === 'auto'
                            ? 'bg-gradient-to-r from-violet-500 to-purple-600 text-white shadow-lg shadow-violet-500/30'
                            : 'text-slate-300 hover:bg-white/5'
                        }`}
                      >
                        ✨ Mode Guidé
                      </button>
                      <button
                        onClick={() => setAddMode('manual')}
                        className={`flex-1 py-2 px-4 rounded-lg font-medium transition-all ${
                          addMode === 'manual'
                            ? 'bg-gradient-to-r from-violet-500 to-purple-600 text-white shadow-lg shadow-violet-500/30'
                            : 'text-slate-300 hover:bg-white/5'
                        }`}
                      >
                        🔧 Mode Avancé
                      </button>
                    </div>

                    {addMode === 'auto' && (
                      <div className="space-y-4">
                        <div className="grid grid-cols-1 gap-3">
                          <div className="bg-blue-500/10 border border-blue-500/30 rounded-xl p-4">
                            <h3 className="font-semibold text-blue-300 mb-2 text-sm">💻 Ordinateur</h3>
                            <p className="text-xs text-slate-400 mb-3">
                              Extension Chrome - Capture automatique en 1 clic
                            </p>
                            <a
                              href="/download-extension.html"
                              target="_blank"
                              className="inline-block w-full text-center px-3 py-2 bg-gradient-to-r from-blue-500 to-cyan-600 text-white rounded-lg hover:shadow-lg hover:shadow-blue-500/30 font-medium text-sm transition-all"
                            >
                              📦 Extension Chrome
                            </a>
                          </div>

                          <div className="bg-purple-500/10 border border-purple-500/30 rounded-xl p-4">
                            <h3 className="font-semibold text-purple-300 mb-2 text-sm">📱 iPhone/Android</h3>
                            <p className="text-xs text-slate-400 mb-3">
                              Bookmarklet mobile - Capture en 1 tap
                            </p>
                            <a
                              href="/mobile-connector.html"
                              target="_blank"
                              className="inline-block w-full text-center px-3 py-2 bg-gradient-to-r from-purple-500 to-pink-600 text-white rounded-lg hover:shadow-lg hover:shadow-purple-500/30 font-medium text-sm transition-all"
                            >
                              📱 Version Mobile
                            </a>
                          </div>
                        </div>

                        <div className="bg-green-500/10 border border-green-500/30 rounded-xl p-4">
                          <h3 className="font-semibold text-green-300 mb-2">📋 Méthode Manuelle - 3 étapes</h3>
                          <ol className="text-sm text-slate-300 space-y-2">
                            <li className="flex items-start gap-2">
                              <span className="font-bold min-w-[20px] text-green-400">1.</span>
                              <span>Ouvrez <a href="https://www.vinted.fr" target="_blank" rel="noopener noreferrer" className="underline text-violet-400">vinted.fr</a> et connectez-vous</span>
                            </li>
                            <li className="flex items-start gap-2">
                              <span className="font-bold min-w-[20px] text-green-400">2.</span>
                              <span>Appuyez sur <kbd className="px-2 py-1 bg-white/10 rounded border border-white/20">F12</kbd> → <strong>Application</strong> → <strong>Cookies</strong></span>
                            </li>
                            <li className="flex items-start gap-2">
                              <span className="font-bold min-w-[20px] text-green-400">3.</span>
                              <span>Copiez <code className="bg-green-500/20 px-2 py-0.5 rounded font-semibold">_vinted_fr_session</code></span>
                            </li>
                          </ol>
                        </div>
                      </div>
                    )}

                    {/* Form Fields */}
                    <div>
                      <label className="block text-sm font-medium text-slate-300 mb-2">
                        Nom du compte
                      </label>
                      <input
                        type="text"
                        value={newAccount.name}
                        onChange={(e) => setNewAccount({ ...newAccount, name: e.target.value })}
                        className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder-slate-400 focus:outline-none focus:border-violet-500/50 focus:bg-white/10 transition-all"
                        placeholder="Mon Compte Principal"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-slate-300 mb-2">
                        Cookie _vinted_fr_session
                      </label>
                      <textarea
                        value={newAccount.cookie}
                        onChange={(e) => setNewAccount({ ...newAccount, cookie: e.target.value })}
                        className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder-slate-400 font-mono text-xs resize-none focus:outline-none focus:border-violet-500/50 focus:bg-white/10 transition-all min-h-[100px]"
                        placeholder="Collez UNIQUEMENT la valeur du cookie _vinted_fr_session..."
                      />
                      <p className="text-xs text-yellow-400 bg-yellow-500/10 border border-yellow-500/30 rounded p-2 mt-2">
                        ⚠️ <strong>Important:</strong> Cookie <code className="bg-yellow-500/20 px-1 rounded">_vinted_fr_session</code> uniquement
                      </p>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-slate-300 mb-2">
                        User Agent (optionnel)
                      </label>
                      <input
                        type="text"
                        value={newAccount.user_agent}
                        onChange={(e) => setNewAccount({ ...newAccount, user_agent: e.target.value })}
                        className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder-slate-400 text-xs font-mono focus:outline-none focus:border-violet-500/50 focus:bg-white/10 transition-all"
                        placeholder="Laissez vide pour user agent par défaut"
                      />
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex gap-3 pt-4 mt-4 border-t border-white/10">
                    <Button
                      variant="outline"
                      onClick={() => setShowAddModal(false)}
                      disabled={isSubmitting}
                      className="flex-1"
                    >
                      Annuler
                    </Button>
                    <Button
                      onClick={handleAddAccount}
                      disabled={isSubmitting || !newAccount.name || !newAccount.cookie}
                      loading={isSubmitting}
                      className="flex-1"
                    >
                      {isSubmitting ? 'Ajout en cours...' : 'Connecter'}
                    </Button>
                  </div>
                </GlassCard>
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
