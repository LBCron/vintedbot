import { useState, useEffect } from 'react';
import { Plus, Users, Check, Eye, EyeOff } from 'lucide-react';
import { accountsAPI } from '../api/client';
import LoadingSpinner from '../components/common/LoadingSpinner';
import toast from 'react-hot-toast';
import type { VintedAccount } from '../types';
import { logger } from '../utils/logger';

export default function Accounts() {
  const [accounts, setAccounts] = useState<VintedAccount[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);
  const [addMode, setAddMode] = useState<'auto' | 'manual'>('auto');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

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
      setAccounts(response.data.accounts || []);
    } catch (error) {
      logger.error('Failed to load accounts', error);
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
      toast.success('✅ Compte Vinted ajouté avec succès !');

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
      alert('Account switched successfully!');
      loadAccounts();
    } catch (error) {
      alert('Failed to switch account');
    }
  };

  const handleDelete = async (accountId: string) => {
    if (!confirm('Delete this account?')) return;
    
    try {
      await accountsAPI.deleteAccount(accountId);
      loadAccounts();
    } catch (error) {
      alert('Failed to delete account');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner size="large" />
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Multi-Account Management</h1>
          <p className="text-gray-600 mt-2">
            👥 PREMIUM FEATURE - Manage multiple Vinted accounts
          </p>
        </div>
        <button
          type="button"
          onClick={() => setShowAddModal(true)}
          className="btn-primary flex items-center gap-2"
        >
          <Plus className="w-5 h-5" />
          Add Account
        </button>
      </div>

      {accounts.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {accounts.map((account) => (
            <div key={account.id} className="card">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className={`p-3 rounded-lg ${account.is_active ? 'bg-green-100' : 'bg-gray-100'}`}>
                    <Users className={`w-6 h-6 ${account.is_active ? 'text-green-600' : 'text-gray-600'}`} />
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900">{account.name}</h3>
                    {account.email && (
                      <p className="text-sm text-gray-600">{account.email}</p>
                    )}
                  </div>
                </div>
                {account.is_active && (
                  <Check className="w-5 h-5 text-green-600" />
                )}
              </div>

              <div className="text-sm text-gray-600 mb-4">
                <p>Created: {new Date(account.created_at).toLocaleDateString()}</p>
                {account.last_used && (
                  <p>Last used: {new Date(account.last_used).toLocaleDateString()}</p>
                )}
              </div>

              <div className="flex gap-2">
                {!account.is_active && (
                  <button
                    type="button"
                    onClick={() => handleSwitch(account.id)}
                    className="flex-1 px-3 py-2 bg-primary-50 text-primary-700 rounded-lg hover:bg-primary-100 text-sm font-medium"
                  >
                    Switch
                  </button>
                )}
                <button
                  type="button"
                  onClick={() => handleDelete(account.id)}
                  className="px-3 py-2 bg-red-50 text-red-700 rounded-lg hover:bg-red-100 text-sm font-medium"
                >
                  Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="card text-center py-12">
          <Users className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-600">No accounts added yet</p>
          <button
            type="button"
            onClick={() => setShowAddModal(true)}
            className="btn-primary mt-4"
          >
            Add Your First Account
          </button>
        </div>
      )}

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
                ✨ Mode Guidé
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
                🔧 Mode Avancé
              </button>
            </div>

            {addMode === 'auto' ? (
              <div className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-4">
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                    <h3 className="font-semibold text-blue-900 mb-2 text-sm">💻 Ordinateur</h3>
                    <p className="text-xs text-blue-800 mb-3">
                      Extension Chrome - Capture automatique en 1 clic
                    </p>
                    <a
                      href="/download-extension.html"
                      target="_blank"
                      className="inline-block w-full text-center px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium text-sm transition-colors"
                    >
                      📦 Extension Chrome
                    </a>
                  </div>

                  <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
                    <h3 className="font-semibold text-purple-900 mb-2 text-sm">📱 iPhone/Android</h3>
                    <p className="text-xs text-purple-800 mb-3">
                      Bookmarklet mobile - Capture en 1 tap
                    </p>
                    <a
                      href="/mobile-connector.html"
                      target="_blank"
                      className="inline-block w-full text-center px-3 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 font-medium text-sm transition-colors"
                    >
                      📱 Version Mobile
                    </a>
                  </div>
                </div>

                <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-4">
                  <h3 className="font-semibold text-green-900 mb-2">📋 Méthode Manuelle - 3 étapes simples</h3>
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
                      💡 Le cookie ressemble à: BAh7CEkiD3Nlc3Npb25faWQGOgZF...
                    </p>
                    <p className="text-xs text-yellow-700 bg-yellow-50 border border-yellow-200 rounded p-2">
                      ⚠️ <strong>Important:</strong> Copiez UNIQUEMENT la valeur du cookie nommé <code className="bg-yellow-100 px-1 rounded font-semibold">_vinted_fr_session</code> (pas les autres cookies comme v-udt, etc.)
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
                    ⚙️ Pour les utilisateurs avancés - entrez manuellement vos cookies
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
                    ⚠️ <strong>Important:</strong> Uniquement le cookie <code className="bg-yellow-100 px-1 rounded font-semibold">_vinted_fr_session</code>
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
