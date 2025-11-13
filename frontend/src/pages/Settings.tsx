import { useState } from 'react';
import { CreditCard, User as UserIcon, Shield, Globe, CheckCircle, XCircle, AlertCircle } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import QuotaCard from '../components/common/QuotaCard';
import { vintedAPI } from '../api/client';
import toast from 'react-hot-toast';
import LoadingSpinner from '../components/common/LoadingSpinner';

export default function Settings() {
  const { user } = useAuth();
  const [vintedCookie, setVintedCookie] = useState('');
  const [sessionStatus, setSessionStatus] = useState<'unknown' | 'missing' | 'valid' | 'expired'>('unknown');
  const [isSaving, setIsSaving] = useState(false);
  const [isTesting, setIsTesting] = useState(false);

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
    <div className="space-y-8 max-w-4xl">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Settings</h1>
        <p className="text-gray-600 mt-2">Manage your account and subscription</p>
      </div>

      <div className="card">
        <div className="flex items-center gap-3 mb-6">
          <div className="p-3 bg-primary-50 rounded-lg">
            <UserIcon className="w-6 h-6 text-primary-600" />
          </div>
          <div>
            <h2 className="text-xl font-semibold text-gray-900">Profile Information</h2>
          </div>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Full Name
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
              Current Plan
            </label>
            <div className="flex items-center gap-2">
              <span className="px-3 py-1 bg-primary-100 text-primary-700 rounded-full text-sm font-medium">
                {user?.plan.toUpperCase()}
              </span>
              <span className="text-sm text-gray-600">
                Active since {new Date(user?.created_at || '').toLocaleDateString()}
              </span>
            </div>
          </div>
        </div>
      </div>

      <div className="card">
        <div className="flex items-center gap-3 mb-6">
          <div className="p-3 bg-purple-50 rounded-lg">
            <Shield className="w-6 h-6 text-purple-600" />
          </div>
          <div>
            <h2 className="text-xl font-semibold text-gray-900">Current Usage</h2>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <QuotaCard
            label="AI Analyses"
            used={user?.quotas_used.ai_analyses_month || 0}
            limit={user?.quotas_limit.ai_analyses_month || 0}
            unit="this month"
          />
          <QuotaCard
            label="Drafts"
            used={user?.quotas_used.drafts || 0}
            limit={user?.quotas_limit.drafts || 0}
          />
          <QuotaCard
            label="Publications"
            used={user?.quotas_used.publications_month || 0}
            limit={user?.quotas_limit.publications_month || 0}
            unit="this month"
          />
          <QuotaCard
            label="Storage"
            used={Math.round(user?.quotas_used.photos_storage_mb || 0)}
            limit={user?.quotas_limit.photos_storage_mb || 0}
            unit="MB"
          />
        </div>
      </div>

      <div className="card">
        <div className="flex items-center gap-3 mb-6">
          <div className="p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
            <Globe className="w-6 h-6 text-blue-600 dark:text-blue-400" />
          </div>
          <div>
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Vinted Configuration</h2>
            <p className="text-sm text-gray-600 dark:text-gray-400">Configure your Vinted session to publish listings</p>
          </div>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Vinted Cookie
            </label>
            <p className="text-xs text-gray-500 dark:text-gray-400 mb-2">
              Extract your Vinted cookies from your browser (F12 → Application → Cookies → vinted.fr)
            </p>
            <textarea
              value={vintedCookie}
              onChange={(e) => setVintedCookie(e.target.value)}
              placeholder="_vinted_fr_session=abc123; anon_id=xyz789; _gcl_au=123; ..."
              rows={4}
              className="w-full px-4 py-2 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 text-sm font-mono text-gray-900 dark:text-white"
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
                  Saving...
                </>
              ) : (
                'Save Session'
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
                  Testing...
                </>
              ) : (
                <>
                  <CheckCircle className="w-4 h-4" />
                  Test Session
                </>
              )}
            </button>
          </div>

          {sessionStatus !== 'unknown' && (
            <div className="mt-4">
              {getSessionStatusDisplay()}
            </div>
          )}

          <div className="mt-4 p-4 bg-blue-50 dark:bg-blue-900/10 border border-blue-200 dark:border-blue-800 rounded-lg">
            <p className="text-sm text-blue-800 dark:text-blue-300 font-medium mb-2">
              📚 How to get your Vinted cookie:
            </p>
            <ol className="text-xs text-blue-700 dark:text-blue-400 space-y-1 list-decimal list-inside">
              <li>Open Chrome/Edge and go to <strong>vinted.fr</strong></li>
              <li>Log into your Vinted account</li>
              <li>Press <strong>F12</strong> to open DevTools</li>
              <li>Go to the <strong>Application</strong> tab</li>
              <li>In the left menu: Click <strong>Cookies</strong> → <strong>https://www.vinted.fr</strong></li>
              <li>Copy all cookies in the format shown above</li>
              <li>Paste here and click <strong>Save Session</strong></li>
              <li>Click <strong>Test Session</strong> to verify it works</li>
            </ol>
          </div>
        </div>
      </div>

      <div className="card">
        <div className="flex items-center gap-3 mb-6">
          <div className="p-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
            <CreditCard className="w-6 h-6 text-green-600 dark:text-green-400" />
          </div>
          <div>
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Upgrade Your Plan</h2>
            <p className="text-sm text-gray-600 dark:text-gray-400">Get more features and higher limits</p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {plans.map((plan) => (
            <div
              key={plan.name}
              className={`p-6 rounded-lg border-2 ${
                user?.plan.toLowerCase() === plan.name.toLowerCase()
                  ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20'
                  : 'border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800'
              }`}
            >
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">{plan.name}</h3>
                <div className="text-right">
                  <p className="text-2xl font-bold text-gray-900 dark:text-white">${plan.price}</p>
                  <p className="text-xs text-gray-600 dark:text-gray-400">per month</p>
                </div>
              </div>

              <ul className="space-y-2 mb-6">
                {plan.features.map((feature, index) => (
                  <li key={index} className="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300">
                    <Shield className="w-4 h-4 text-green-600 dark:text-green-400" />
                    {feature}
                  </li>
                ))}
              </ul>

              {user?.plan.toLowerCase() === plan.name.toLowerCase() ? (
                <div className="px-4 py-2 bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300 rounded-lg text-center font-medium">
                  Current Plan
                </div>
              ) : (
                <button
                  onClick={() => alert('Stripe integration coming soon!')}
                  className="w-full btn-primary"
                >
                  {plan.price === 0 ? 'Downgrade' : 'Upgrade'}
                </button>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
