import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  CreditCard,
  User as UserIcon,
  Shield,
  Globe,
  CheckCircle,
  XCircle,
  AlertCircle,
  Bell,
  Lock,
  Settings as SettingsIcon,
  Moon,
  Sun,
  Languages
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import QuotaCard from '../components/common/QuotaCard';
import { vintedAPI } from '../api/client';
import toast from 'react-hot-toast';
import LoadingSpinner from '../components/common/LoadingSpinner';
import { cn } from '../lib/utils';

type SettingsTab = 'profile' | 'notifications' | 'security' | 'billing' | 'preferences';

export default function Settings() {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState<SettingsTab>('profile');
  const [vintedCookie, setVintedCookie] = useState('');
  const [sessionStatus, setSessionStatus] = useState<'unknown' | 'missing' | 'valid' | 'expired'>('unknown');
  const [isSaving, setIsSaving] = useState(false);
  const [isTesting, setIsTesting] = useState(false);

  // Notification settings
  const [emailNotifications, setEmailNotifications] = useState(true);
  const [pushNotifications, setPushNotifications] = useState(false);

  // Preferences
  const [language, setLanguage] = useState('fr');
  const [darkMode, setDarkMode] = useState(false);

  const tabs = [
    { id: 'profile' as SettingsTab, label: 'Profil', icon: UserIcon },
    { id: 'notifications' as SettingsTab, label: 'Notifications', icon: Bell },
    { id: 'security' as SettingsTab, label: 'Sécurité', icon: Lock },
    { id: 'billing' as SettingsTab, label: 'Facturation', icon: CreditCard },
    { id: 'preferences' as SettingsTab, label: 'Préférences', icon: SettingsIcon },
  ];

  const plans = [
    { name: 'Free', price: 0, features: ['20 AI analyses/month', '50 drafts', '10 publications/month', '500 MB storage'] },
    { name: 'Starter', price: 19, features: ['200 AI analyses/month', '500 drafts', '100 publications/month', '5 GB storage'] },
    { name: 'Pro', price: 49, features: ['1000 AI analyses/month', '2000 drafts', '500 publications/month', '20 GB storage'] },
    { name: 'Scale', price: 99, features: ['5000 AI analyses/month', '10000 drafts', '2500 publications/month', '100 GB storage'] },
  ];

  const handleSaveSession = async () => {
    if (!vintedCookie.trim()) {
      toast.error('Please enter a Vinted cookie');
      return;
    }

    setIsSaving(true);
    try {
      await vintedAPI.saveSession(vintedCookie);
      toast.success('Vinted session saved successfully!');
      setVintedCookie('');
      setSessionStatus('valid');
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to save session');
    } finally {
      setIsSaving(false);
    }
  };

  const handleTestSession = async () => {
    setIsTesting(true);
    try {
      const response = await vintedAPI.testSession();
      const data = response.data;

      if (data.ok) {
        setSessionStatus('valid');
        toast.success('Vinted session is valid!');
      } else {
        setSessionStatus(data.status || 'expired');
        if (data.status === 'missing') {
          toast.error('No Vinted session configured. Please add your cookie.');
        } else if (data.status === 'expired') {
          toast.error('Your Vinted session has expired. Please update your cookie.');
        } else {
          toast.error(data.message || 'Session test failed');
        }
      }
    } catch (error: any) {
      setSessionStatus('expired');
      toast.error(error.response?.data?.detail || 'Failed to test session');
    } finally {
      setIsTesting(false);
    }
  };

  const getSessionStatusDisplay = () => {
    switch (sessionStatus) {
      case 'valid':
        return (
          <div className="flex items-center gap-2 px-3 py-2 bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-400 rounded-lg">
            <CheckCircle className="w-5 h-5" />
            <span className="font-medium">Session Valid</span>
          </div>
        );
      case 'expired':
        return (
          <div className="flex items-center gap-2 px-3 py-2 bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400 rounded-lg">
            <XCircle className="w-5 h-5" />
            <span className="font-medium">Session Expired</span>
          </div>
        );
      case 'missing':
        return (
          <div className="flex items-center gap-2 px-3 py-2 bg-yellow-50 dark:bg-yellow-900/20 text-yellow-700 dark:text-yellow-400 rounded-lg">
            <AlertCircle className="w-5 h-5" />
            <span className="font-medium">No Session Configured</span>
          </div>
        );
      default:
        return null;
    }
  };

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
              <SettingsIcon className="w-10 h-10" />
              <h1 className="text-4xl font-bold">Paramètres</h1>
            </div>
            <p className="text-brand-100 text-lg max-w-2xl">
              Gérez votre profil, vos notifications et vos préférences
            </p>
          </motion.div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 -mt-6">
        <div className="bg-white rounded-2xl shadow-lg overflow-hidden">
          <div className="flex flex-col md:flex-row">
            {/* Sidebar Tabs */}
            <div className="md:w-64 bg-gray-50 border-r border-gray-200">
              <nav className="p-4 space-y-1">
                {tabs.map((tab) => {
                  const Icon = tab.icon;
                  const isActive = activeTab === tab.id;

                  return (
                    <button
                      key={tab.id}
                      onClick={() => setActiveTab(tab.id)}
                      className={cn(
                        "w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all text-left relative",
                        isActive
                          ? "bg-brand-600 text-white shadow-md"
                          : "text-gray-700 hover:bg-gray-100"
                      )}
                    >
                      <Icon className="w-5 h-5 flex-shrink-0" />
                      <span className="font-medium">{tab.label}</span>
                      {isActive && (
                        <motion.div
                          layoutId="activeTab"
                          className="absolute inset-0 bg-brand-600 rounded-xl -z-10"
                          transition={{ type: 'spring', stiffness: 500, damping: 30 }}
                        />
                      )}
                    </button>
                  );
                })}
              </nav>
            </div>

            {/* Content Area */}
            <div className="flex-1 p-8">
              <AnimatePresence mode="wait">
                <motion.div
                  key={activeTab}
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                  transition={{ duration: 0.2 }}
                >
                  {activeTab === 'profile' && <ProfileTab user={user} />}
                  {activeTab === 'notifications' && (
                    <NotificationsTab
                      emailNotifications={emailNotifications}
                      setEmailNotifications={setEmailNotifications}
                      pushNotifications={pushNotifications}
                      setPushNotifications={setPushNotifications}
                    />
                  )}
                  {activeTab === 'security' && (
                    <SecurityTab
                      vintedCookie={vintedCookie}
                      setVintedCookie={setVintedCookie}
                      sessionStatus={sessionStatus}
                      isSaving={isSaving}
                      isTesting={isTesting}
                      handleSaveSession={handleSaveSession}
                      handleTestSession={handleTestSession}
                      getSessionStatusDisplay={getSessionStatusDisplay}
                    />
                  )}
                  {activeTab === 'billing' && <BillingTab user={user} plans={plans} />}
                  {activeTab === 'preferences' && (
                    <PreferencesTab
                      language={language}
                      setLanguage={setLanguage}
                      darkMode={darkMode}
                      setDarkMode={setDarkMode}
                    />
                  )}
                </motion.div>
              </AnimatePresence>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// Profile Tab Component
function ProfileTab({ user }: any) {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Informations du profil</h2>
        <p className="text-gray-600">Gérez vos informations personnelles</p>
      </div>

      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Nom complet
          </label>
          <input type="text" value={user?.name} className="input" disabled />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Email
          </label>
          <input type="email" value={user?.email} className="input" disabled />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Plan actuel
          </label>
          <div className="flex items-center gap-2">
            <span className="px-3 py-1 bg-primary-100 text-primary-700 rounded-full text-sm font-medium">
              {user?.plan?.toUpperCase() || 'FREE'}
            </span>
            <span className="text-sm text-gray-600">
              Actif depuis {new Date(user?.created_at || '').toLocaleDateString()}
            </span>
          </div>
        </div>
      </div>

      {/* Usage Section */}
      <div className="mt-8">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Utilisation actuelle</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <QuotaCard
            label="AI Analyses"
            used={user?.quotas_used?.ai_analyses_month || 0}
            limit={user?.quotas_limit?.ai_analyses_month || 0}
            unit="this month"
          />
          <QuotaCard
            label="Drafts"
            used={user?.quotas_used?.drafts || 0}
            limit={user?.quotas_limit?.drafts || 0}
          />
          <QuotaCard
            label="Publications"
            used={user?.quotas_used?.publications_month || 0}
            limit={user?.quotas_limit?.publications_month || 0}
            unit="this month"
          />
          <QuotaCard
            label="Storage"
            used={Math.round(user?.quotas_used?.photos_storage_mb || 0)}
            limit={user?.quotas_limit?.photos_storage_mb || 0}
            unit="MB"
          />
        </div>
      </div>
    </div>
  );
}

// Notifications Tab Component
function NotificationsTab({ emailNotifications, setEmailNotifications, pushNotifications, setPushNotifications }: any) {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Notifications</h2>
        <p className="text-gray-600">Gérez vos préférences de notification</p>
      </div>

      <div className="space-y-4">
        <ToggleSwitch
          label="Notifications par email"
          description="Recevez des notifications par email pour les nouvelles ventes et messages"
          enabled={emailNotifications}
          onChange={setEmailNotifications}
        />

        <ToggleSwitch
          label="Notifications push"
          description="Recevez des notifications push sur votre navigateur"
          enabled={pushNotifications}
          onChange={setPushNotifications}
        />
      </div>
    </div>
  );
}

// Security Tab Component
function SecurityTab({ vintedCookie, setVintedCookie, sessionStatus, isSaving, isTesting, handleSaveSession, handleTestSession, getSessionStatusDisplay }: any) {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Sécurité</h2>
        <p className="text-gray-600">Gérez votre session Vinted et vos paramètres de sécurité</p>
      </div>

      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Cookie Vinted
          </label>
          <p className="text-xs text-gray-500 mb-2">
            Extraire vos cookies Vinted depuis votre navigateur (F12 → Application → Cookies → vinted.fr)
          </p>
          <textarea
            value={vintedCookie}
            onChange={(e) => setVintedCookie(e.target.value)}
            placeholder="_vinted_fr_session=abc123; anon_id=xyz789; _gcl_au=123; ..."
            rows={4}
            className="w-full px-4 py-2 bg-white border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 text-sm font-mono text-gray-900"
          />
        </div>

        <div className="flex flex-col sm:flex-row gap-3">
          <button
            onClick={handleSaveSession}
            disabled={isSaving || !vintedCookie.trim()}
            className="flex-1 px-4 py-2 bg-primary-600 hover:bg-primary-700 disabled:bg-gray-400 text-white rounded-lg font-medium flex items-center justify-center gap-2 transition-colors"
          >
            {isSaving ? (
              <>
                <LoadingSpinner size="small" />
                Enregistrement...
              </>
            ) : (
              'Enregistrer la session'
            )}
          </button>
          <button
            onClick={handleTestSession}
            disabled={isTesting}
            className="flex-1 px-4 py-2 bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white rounded-lg font-medium flex items-center justify-center gap-2 transition-colors"
          >
            {isTesting ? (
              <>
                <LoadingSpinner size="small" />
                Test en cours...
              </>
            ) : (
              <>
                <CheckCircle className="w-4 h-4" />
                Tester la session
              </>
            )}
          </button>
        </div>

        {sessionStatus !== 'unknown' && (
          <div className="mt-4">
            {getSessionStatusDisplay()}
          </div>
        )}
      </div>
    </div>
  );
}

// Billing Tab Component
function BillingTab({ user, plans }: any) {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Facturation</h2>
        <p className="text-gray-600">Gérez votre abonnement et vos paiements</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {plans.map((plan: any) => (
          <div
            key={plan.name}
            className={cn(
              "p-6 rounded-xl border-2 transition-all",
              user?.plan?.toLowerCase() === plan.name.toLowerCase()
                ? 'border-primary-500 bg-primary-50'
                : 'border-gray-200 bg-white hover:border-primary-200'
            )}
          >
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">{plan.name}</h3>
              <div className="text-right">
                <p className="text-2xl font-bold text-gray-900">{plan.price}€</p>
                <p className="text-xs text-gray-600">par mois</p>
              </div>
            </div>

            <ul className="space-y-2 mb-6">
              {plan.features.map((feature: string, index: number) => (
                <li key={index} className="flex items-center gap-2 text-sm text-gray-700">
                  <CheckCircle className="w-4 h-4 text-green-600" />
                  {feature}
                </li>
              ))}
            </ul>

            {user?.plan?.toLowerCase() === plan.name.toLowerCase() ? (
              <div className="px-4 py-2 bg-primary-100 text-primary-700 rounded-lg text-center font-medium">
                Plan actuel
              </div>
            ) : (
              <button
                onClick={() => toast.success('Intégration Stripe bientôt disponible!')}
                className="w-full btn-primary"
              >
                {plan.price === 0 ? 'Rétrograder' : 'Mettre à niveau'}
              </button>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

// Preferences Tab Component
function PreferencesTab({ language, setLanguage, darkMode, setDarkMode }: any) {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Préférences</h2>
        <p className="text-gray-600">Personnalisez votre expérience</p>
      </div>

      <div className="space-y-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Langue
          </label>
          <select
            value={language}
            onChange={(e) => setLanguage(e.target.value)}
            className="input"
          >
            <option value="fr">Français</option>
            <option value="en">English</option>
            <option value="es">Español</option>
          </select>
        </div>

        <ToggleSwitch
          label="Mode sombre"
          description="Activer le thème sombre pour une meilleure expérience visuelle"
          enabled={darkMode}
          onChange={setDarkMode}
          icon={darkMode ? Moon : Sun}
        />
      </div>
    </div>
  );
}

// Toggle Switch Component
function ToggleSwitch({ label, description, enabled, onChange, icon: Icon }: any) {
  return (
    <div className="flex items-center justify-between p-4 bg-gray-50 rounded-xl">
      <div className="flex items-center gap-3">
        {Icon && <Icon className="w-5 h-5 text-gray-600" />}
        <div>
          <p className="font-medium text-gray-900">{label}</p>
          <p className="text-sm text-gray-600">{description}</p>
        </div>
      </div>
      <button
        onClick={() => onChange(!enabled)}
        className={cn(
          "relative inline-flex h-6 w-11 items-center rounded-full transition-colors",
          enabled ? "bg-primary-600" : "bg-gray-300"
        )}
      >
        <span
          className={cn(
            "inline-block h-4 w-4 transform rounded-full bg-white transition-transform",
            enabled ? "translate-x-6" : "translate-x-1"
          )}
        />
      </button>
    </div>
  );
}
