import { useState } from 'react';
import { motion } from 'framer-motion';
import { CreditCard, User as UserIcon, Shield, Globe, CheckCircle, XCircle, AlertCircle, Settings as SettingsIcon } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import QuotaCard from '../components/common/QuotaCard';
import { vintedAPI } from '../api/client';
import { GlassCard } from '../components/ui/GlassCard';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import toast from 'react-hot-toast';

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
          <Badge className="bg-green-500/20 border-green-500/30 text-green-400">
            <CheckCircle className="w-4 h-4 mr-1" />
            Session Valid
          </Badge>
        );
      case 'expired':
        return (
          <Badge className="bg-red-500/20 border-red-500/30 text-red-400">
            <XCircle className="w-4 h-4 mr-1" />
            Session Expired
          </Badge>
        );
      case 'missing':
        return (
          <Badge className="bg-yellow-500/20 border-yellow-500/30 text-yellow-400">
            <AlertCircle className="w-4 h-4 mr-1" />
            No Session Configured
          </Badge>
        );
      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      {/* Header */}
      <motion.div
        className="p-8"
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <div className="flex items-center space-x-4 mb-2">
          <div className="p-3 bg-gradient-to-br from-violet-500 to-purple-600 rounded-2xl shadow-lg shadow-violet-500/50">
            <SettingsIcon className="w-8 h-8 text-white" />
          </div>
          <div>
            <h1 className="text-4xl md:text-5xl font-bold bg-gradient-to-r from-white via-violet-200 to-purple-200 bg-clip-text text-transparent">
              Settings
            </h1>
            <p className="text-slate-400">Manage your account and subscription</p>
          </div>
        </div>
      </motion.div>

      <div className="max-w-4xl mx-auto px-8 space-y-8 pb-12">
        {/* Profile Information */}
        <GlassCard className="p-6">
          <div className="flex items-center gap-3 mb-6">
            <div className="p-3 bg-violet-500/20 rounded-lg border border-violet-500/30">
              <UserIcon className="w-6 h-6 text-violet-400" />
            </div>
            <h2 className="text-xl font-semibold text-white">Profile Information</h2>
          </div>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-400 mb-2">
                Full Name
              </label>
              <input
                type="text"
                value={user?.name}
                className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:border-violet-500/50 focus:bg-white/10 transition-all"
                disabled
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-400 mb-2">
                Email
              </label>
              <input
                type="email"
                value={user?.email}
                className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:border-violet-500/50 focus:bg-white/10 transition-all"
                disabled
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-400 mb-2">
                Current Plan
              </label>
              <div className="flex items-center gap-2">
                <Badge className="bg-violet-500/20 border-violet-500/30 text-violet-300">
                  {user?.plan.toUpperCase()}
                </Badge>
                <span className="text-sm text-slate-400">
                  Active since {new Date(user?.created_at || '').toLocaleDateString()}
                </span>
              </div>
            </div>
          </div>
        </GlassCard>

        {/* Current Usage */}
        <GlassCard className="p-6">
          <div className="flex items-center gap-3 mb-6">
            <div className="p-3 bg-purple-500/20 rounded-lg border border-purple-500/30">
              <Shield className="w-6 h-6 text-purple-400" />
            </div>
            <h2 className="text-xl font-semibold text-white">Current Usage</h2>
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
        </GlassCard>

        {/* Vinted Configuration */}
        <GlassCard className="p-6">
          <div className="flex items-center gap-3 mb-6">
            <div className="p-3 bg-blue-500/20 rounded-lg border border-blue-500/30">
              <Globe className="w-6 h-6 text-blue-400" />
            </div>
            <div>
              <h2 className="text-xl font-semibold text-white">Vinted Configuration</h2>
              <p className="text-sm text-slate-400">Configure your Vinted session to publish listings</p>
            </div>
          </div>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-400 mb-2">
                Vinted Cookie
              </label>
              <p className="text-xs text-slate-500 mb-2">
                Extract your Vinted cookies from your browser (F12 → Application → Cookies → vinted.fr)
              </p>
              <textarea
                value={vintedCookie}
                onChange={(e) => setVintedCookie(e.target.value)}
                placeholder="_vinted_fr_session=abc123; anon_id=xyz789; _gcl_au=123; ..."
                rows={4}
                className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg focus:outline-none focus:ring-2 focus:ring-violet-500/50 text-sm font-mono text-white placeholder-slate-500"
              />
            </div>

            <div className="flex flex-col sm:flex-row gap-3">
              <Button
                onClick={handleSaveSession}
                disabled={isSaving || !vintedCookie.trim()}
                className="flex-1"
              >
                {isSaving ? 'Saving...' : 'Save Session'}
              </Button>
              <Button
                onClick={handleTestSession}
                disabled={isTesting}
                variant="outline"
                className="flex-1"
                icon={CheckCircle}
              >
                {isTesting ? 'Testing...' : 'Test Session'}
              </Button>
            </div>

            {sessionStatus !== 'unknown' && (
              <div className="mt-4">
                {getSessionStatusDisplay()}
              </div>
            )}

            <div className="mt-4 p-4 bg-blue-500/10 border border-blue-500/30 rounded-lg">
              <p className="text-sm text-blue-300 font-medium mb-2">
                📚 How to get your Vinted cookie:
              </p>
              <ol className="text-xs text-blue-400 space-y-1 list-decimal list-inside">
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
        </GlassCard>

        {/* Upgrade Your Plan */}
        <GlassCard className="p-6">
          <div className="flex items-center gap-3 mb-6">
            <div className="p-3 bg-green-500/20 rounded-lg border border-green-500/30">
              <CreditCard className="w-6 h-6 text-green-400" />
            </div>
            <div>
              <h2 className="text-xl font-semibold text-white">Upgrade Your Plan</h2>
              <p className="text-sm text-slate-400">Get more features and higher limits</p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {plans.map((plan) => (
              <div
                key={plan.name}
                className={`p-6 rounded-lg border-2 transition-all ${
                  user?.plan.toLowerCase() === plan.name.toLowerCase()
                    ? 'border-violet-500 bg-violet-500/10'
                    : 'border-white/10 bg-white/5 hover:border-white/20'
                }`}
              >
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-white">{plan.name}</h3>
                  <div className="text-right">
                    <p className="text-2xl font-bold text-white">${plan.price}</p>
                    <p className="text-xs text-slate-400">per month</p>
                  </div>
                </div>

                <ul className="space-y-2 mb-6">
                  {plan.features.map((feature, index) => (
                    <li key={index} className="flex items-center gap-2 text-sm text-slate-300">
                      <Shield className="w-4 h-4 text-green-400" />
                      {feature}
                    </li>
                  ))}
                </ul>

                {user?.plan.toLowerCase() === plan.name.toLowerCase() ? (
                  <div className="px-4 py-2 bg-violet-500/20 border border-violet-500/30 text-violet-300 rounded-lg text-center font-medium">
                    Current Plan
                  </div>
                ) : (
                  <Button
                    onClick={() => toast.info('Stripe integration coming soon!')}
                    className="w-full"
                  >
                    {plan.price === 0 ? 'Downgrade' : 'Upgrade'}
                  </Button>
                )}
              </div>
            ))}
          </div>
        </GlassCard>
      </div>
    </div>
  );
}
