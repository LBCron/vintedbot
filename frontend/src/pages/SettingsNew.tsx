import { useState } from 'react';
import { motion } from 'framer-motion';
import {
  User,
  Lock,
  Bell,
  Sparkles,
  Palette,
  CreditCard,
  Plug,
  Save,
  CheckCircle,
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '../components/common/Tabs';
import { Badge } from '../components/common/Badge';
import Avatar from '../components/common/Avatar';
import Progress from '../components/common/Progress';
import QuotaCard from '../components/common/QuotaCard';

export default function Settings() {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState('profile');
  const [isDarkMode, setIsDarkMode] = useState(false);
  const [notifications, setNotifications] = useState({
    emailMessages: true,
    emailSales: true,
    emailWeekly: false,
    emailTips: false,
    pushMessages: true,
    pushPublish: true,
    pushErrors: true,
    pushFeatures: false,
  });

  const [aiSettings, setAiSettings] = useState({
    creativity: 50,
    descriptionLength: 'medium',
    tone: ['warm', 'transparent'],
    autoPrice: true,
    pricingStrategy: 'optimal',
    autoTags: true,
    detectStyle: true,
    autoLearn: true,
  });

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Settings</h1>
        <p className="text-gray-600 dark:text-gray-400 mt-2">
          Manage your account preferences and configuration
        </p>
      </motion.div>

      {/* Tabs */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.1 }}
      >
        <Tabs defaultValue="profile" onValueChange={setActiveTab}>
          <TabsList variant="underline" className="mb-8">
            <TabsTrigger value="profile" variant="underline">
              <User className="w-4 h-4 mr-2" />
              Profile
            </TabsTrigger>
            <TabsTrigger value="security" variant="underline">
              <Lock className="w-4 h-4 mr-2" />
              Security
            </TabsTrigger>
            <TabsTrigger value="notifications" variant="underline">
              <Bell className="w-4 h-4 mr-2" />
              Notifications
            </TabsTrigger>
            <TabsTrigger value="ai" variant="underline">
              <Sparkles className="w-4 h-4 mr-2" />
              AI
            </TabsTrigger>
            <TabsTrigger value="appearance" variant="underline">
              <Palette className="w-4 h-4 mr-2" />
              Appearance
            </TabsTrigger>
            <TabsTrigger value="subscription" variant="underline">
              <CreditCard className="w-4 h-4 mr-2" />
              Subscription
            </TabsTrigger>
            <TabsTrigger value="integrations" variant="underline">
              <Plug className="w-4 h-4 mr-2" />
              Integrations
            </TabsTrigger>
          </TabsList>

          {/* Profile Tab */}
          <TabsContent value="profile">
            <div className="space-y-6">
              <div className="card p-6">
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-6">
                  Profile Information
                </h2>

                <div className="space-y-6">
                  {/* Avatar */}
                  <div className="flex items-center gap-6">
                    <Avatar
                      src={user?.avatar}
                      fallback={user?.name?.charAt(0)}
                      size="2xl"
                    />
                    <div>
                      <button className="px-4 py-2 bg-primary-50 dark:bg-primary-900/20 text-primary-700 dark:text-primary-400 rounded-lg hover:bg-primary-100 dark:hover:bg-primary-900/40 font-medium transition-colors">
                        Change Photo
                      </button>
                      <p className="text-sm text-gray-500 dark:text-gray-400 mt-2">
                        JPG, PNG or GIF. Max size 2MB
                      </p>
                    </div>
                  </div>

                  {/* Form Fields */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Full Name
                      </label>
                      <input
                        type="text"
                        defaultValue={user?.name}
                        className="w-full px-4 py-2 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Email
                      </label>
                      <div className="relative">
                        <input
                          type="email"
                          defaultValue={user?.email}
                          className="w-full px-4 py-2 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all"
                        />
                        <Badge variant="success" size="sm" className="absolute right-2 top-1/2 -translate-y-1/2">
                          Verified
                        </Badge>
                      </div>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Phone
                      </label>
                      <input
                        type="tel"
                        placeholder="+33 6 12 34 56 78"
                        className="w-full px-4 py-2 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Language
                      </label>
                      <select className="w-full px-4 py-2 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all">
                        <option>Français</option>
                        <option>English</option>
                        <option>Español</option>
                      </select>
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Timezone
                    </label>
                    <select className="w-full px-4 py-2 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all">
                      <option>Europe/Paris (GMT+1)</option>
                      <option>America/New_York (GMT-5)</option>
                      <option>Asia/Tokyo (GMT+9)</option>
                    </select>
                  </div>

                  <div className="flex justify-end">
                    <button className="px-6 py-2.5 bg-primary-500 hover:bg-primary-600 text-white rounded-lg flex items-center gap-2 font-medium transition-colors">
                      <Save className="w-4 h-4" />
                      Save Changes
                    </button>
                  </div>
                </div>
              </div>

              {/* Vinted Account */}
              <div className="card p-6 bg-gradient-to-br from-success-50 to-emerald-50 dark:from-success-900/20 dark:to-emerald-900/20 border-success-200 dark:border-success-800">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div className="p-3 bg-success-100 dark:bg-success-900/40 rounded-lg">
                      <CheckCircle className="w-6 h-6 text-success-600 dark:text-success-400" />
                    </div>
                    <div>
                      <h3 className="font-semibold text-gray-900 dark:text-white mb-1">
                        Vinted Account Connected
                      </h3>
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        @{user?.name?.toLowerCase().replace(' ', '')}
                      </p>
                    </div>
                  </div>
                  <button className="px-4 py-2 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 font-medium transition-colors">
                    Reconnect
                  </button>
                </div>
              </div>
            </div>
          </TabsContent>

          {/* Security Tab */}
          <TabsContent value="security">
            <div className="space-y-6">
              <div className="card p-6">
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-6">
                  Password
                </h2>

                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Current Password
                    </label>
                    <input
                      type="password"
                      className="w-full px-4 py-2 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all"
                    />
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        New Password
                      </label>
                      <input
                        type="password"
                        className="w-full px-4 py-2 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Confirm New Password
                      </label>
                      <input
                        type="password"
                        className="w-full px-4 py-2 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all"
                      />
                    </div>
                  </div>

                  <button className="px-6 py-2.5 bg-primary-500 hover:bg-primary-600 text-white rounded-lg font-medium transition-colors">
                    Update Password
                  </button>
                </div>
              </div>

              <div className="card p-6">
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
                  Two-Factor Authentication
                </h2>
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-6">
                  Add an extra layer of security to your account
                </p>

                <div className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                  <div className="flex items-center gap-3">
                    <Badge variant="error" size="sm">Disabled</Badge>
                    <span className="text-sm text-gray-700 dark:text-gray-300">
                      Two-factor authentication is not enabled
                    </span>
                  </div>
                  <button className="px-4 py-2 bg-primary-500 hover:bg-primary-600 text-white rounded-lg font-medium transition-colors">
                    Enable 2FA
                  </button>
                </div>
              </div>

              <div className="card p-6 bg-error-50 dark:bg-error-900/20 border-error-200 dark:border-error-800">
                <h2 className="text-xl font-semibold text-error-900 dark:text-error-300 mb-2">
                  Danger Zone
                </h2>
                <p className="text-sm text-error-700 dark:text-error-400 mb-4">
                  Irreversible actions. Please be careful.
                </p>
                <button className="px-4 py-2 bg-error-500 hover:bg-error-600 text-white rounded-lg font-medium transition-colors">
                  Delete Account
                </button>
              </div>
            </div>
          </TabsContent>

          {/* Notifications Tab */}
          <TabsContent value="notifications">
            <div className="space-y-6">
              <div className="card p-6">
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-6">
                  Email Notifications
                </h2>

                <div className="space-y-4">
                  {[
                    { key: 'emailMessages', label: 'New messages', description: 'Get notified when someone sends you a message' },
                    { key: 'emailSales', label: 'Sales confirmations', description: 'Receive confirmation when an item is sold' },
                    { key: 'emailWeekly', label: 'Weekly reports', description: 'Get a summary of your activity every week' },
                    { key: 'emailTips', label: 'Tips and tricks', description: 'Learn how to optimize your listings' },
                  ].map((item) => (
                    <div key={item.key} className="flex items-start justify-between p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                      <div className="flex-1">
                        <h4 className="font-medium text-gray-900 dark:text-white mb-1">
                          {item.label}
                        </h4>
                        <p className="text-sm text-gray-600 dark:text-gray-400">
                          {item.description}
                        </p>
                      </div>
                      <label className="relative inline-flex items-center cursor-pointer">
                        <input
                          type="checkbox"
                          checked={notifications[item.key as keyof typeof notifications] as boolean}
                          onChange={(e) => setNotifications({ ...notifications, [item.key]: e.target.checked })}
                          className="sr-only peer"
                        />
                        <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 dark:peer-focus:ring-primary-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-primary-600"></div>
                      </label>
                    </div>
                  ))}
                </div>
              </div>

              <div className="card p-6">
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-6">
                  Push Notifications
                </h2>

                <div className="space-y-4">
                  {[
                    { key: 'pushMessages', label: 'Real-time messages', description: 'Get instant notifications for new messages' },
                    { key: 'pushPublish', label: 'Publication success', description: 'Know when your items are published' },
                    { key: 'pushErrors', label: 'Error alerts', description: 'Get notified about errors or issues' },
                    { key: 'pushFeatures', label: 'New features', description: 'Learn about new features and updates' },
                  ].map((item) => (
                    <div key={item.key} className="flex items-start justify-between p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                      <div className="flex-1">
                        <h4 className="font-medium text-gray-900 dark:text-white mb-1">
                          {item.label}
                        </h4>
                        <p className="text-sm text-gray-600 dark:text-gray-400">
                          {item.description}
                        </p>
                      </div>
                      <label className="relative inline-flex items-center cursor-pointer">
                        <input
                          type="checkbox"
                          checked={notifications[item.key as keyof typeof notifications] as boolean}
                          onChange={(e) => setNotifications({ ...notifications, [item.key]: e.target.checked })}
                          className="sr-only peer"
                        />
                        <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 dark:peer-focus:ring-primary-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-primary-600"></div>
                      </label>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </TabsContent>

          {/* AI Tab */}
          <TabsContent value="ai">
            <div className="space-y-6">
              <div className="card p-6">
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-6">
                  AI Generation Settings
                </h2>

                <div className="space-y-6">
                  {/* Creativity Slider */}
                  <div>
                    <div className="flex items-center justify-between mb-3">
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                        Creativity Level
                      </label>
                      <span className="text-sm text-gray-600 dark:text-gray-400">
                        {aiSettings.creativity}%
                      </span>
                    </div>
                    <input
                      type="range"
                      min="0"
                      max="100"
                      value={aiSettings.creativity}
                      onChange={(e) => setAiSettings({ ...aiSettings, creativity: parseInt(e.target.value) })}
                      className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer dark:bg-gray-700"
                    />
                    <div className="flex justify-between text-xs text-gray-500 dark:text-gray-400 mt-2">
                      <span>Factual</span>
                      <span>Creative</span>
                    </div>
                  </div>

                  {/* Description Length */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                      Description Length
                    </label>
                    <div className="flex gap-2">
                      {['short', 'medium', 'long'].map((length) => (
                        <button
                          key={length}
                          onClick={() => setAiSettings({ ...aiSettings, descriptionLength: length })}
                          className={`flex-1 px-4 py-2 rounded-lg font-medium transition-all ${
                            aiSettings.descriptionLength === length
                              ? 'bg-primary-500 text-white'
                              : 'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700'
                          }`}
                        >
                          {length.charAt(0).toUpperCase() + length.slice(1)}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Pricing */}
                  <div>
                    <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                      Smart Pricing
                    </h3>
                    <div className="space-y-3">
                      <div className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                        <span className="text-sm text-gray-700 dark:text-gray-300">
                          Enable automatic price suggestions
                        </span>
                        <label className="relative inline-flex items-center cursor-pointer">
                          <input
                            type="checkbox"
                            checked={aiSettings.autoPrice}
                            onChange={(e) => setAiSettings({ ...aiSettings, autoPrice: e.target.checked })}
                            className="sr-only peer"
                          />
                          <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 dark:peer-focus:ring-primary-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-primary-600"></div>
                        </label>
                      </div>

                      {aiSettings.autoPrice && (
                        <div>
                          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                            Pricing Strategy
                          </label>
                          <select
                            value={aiSettings.pricingStrategy}
                            onChange={(e) => setAiSettings({ ...aiSettings, pricingStrategy: e.target.value })}
                            className="w-full px-4 py-2 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all"
                          >
                            <option value="optimal">Optimal (Balanced)</option>
                            <option value="quick">Quick Sale (-15%)</option>
                            <option value="profit">Maximum Profit (+20%)</option>
                          </select>
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="flex justify-end">
                    <button className="px-6 py-2.5 bg-primary-500 hover:bg-primary-600 text-white rounded-lg flex items-center gap-2 font-medium transition-colors">
                      <Save className="w-4 h-4" />
                      Save AI Settings
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </TabsContent>

          {/* Appearance Tab */}
          <TabsContent value="appearance">
            <div className="card p-6">
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-6">
                Theme
              </h2>

              <div className="grid grid-cols-3 gap-4 mb-8">
                {[
                  { value: 'light', label: 'Light', icon: '🌞' },
                  { value: 'dark', label: 'Dark', icon: '🌙' },
                  { value: 'auto', label: 'Auto', icon: '🔄' },
                ].map((theme) => (
                  <button
                    key={theme.value}
                    className="p-6 border-2 border-gray-200 dark:border-gray-700 rounded-lg hover:border-primary-500 transition-all"
                  >
                    <div className="text-4xl mb-2">{theme.icon}</div>
                    <div className="font-medium text-gray-900 dark:text-white">{theme.label}</div>
                  </button>
                ))}
              </div>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Interface Density
                  </label>
                  <select className="w-full px-4 py-2 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all">
                    <option>Comfortable (Default)</option>
                    <option>Compact</option>
                    <option>Spacious</option>
                  </select>
                </div>

                <div className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                  <div>
                    <h4 className="font-medium text-gray-900 dark:text-white mb-1">
                      Enable Animations
                    </h4>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      Smooth transitions and effects
                    </p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input type="checkbox" defaultChecked className="sr-only peer" />
                    <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 dark:peer-focus:ring-primary-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-primary-600"></div>
                  </label>
                </div>
              </div>
            </div>
          </TabsContent>

          {/* Subscription Tab */}
          <TabsContent value="subscription">
            <div className="space-y-6">
              {/* Current Plan */}
              <div className="card p-6">
                <div className="flex items-center justify-between mb-6">
                  <div>
                    <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-1">
                      Current Plan: {user?.plan.toUpperCase()}
                    </h2>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      Active since {new Date(user?.created_at || '').toLocaleDateString()}
                    </p>
                  </div>
                  <Badge variant="primary" size="lg">FREE</Badge>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                  <QuotaCard
                    label="AI Analyses"
                    used={user?.quotas_used.ai_analyses_month || 0}
                    limit={user?.quotas_limit.ai_analyses_month || 0}
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
                  />
                  <QuotaCard
                    label="Storage"
                    used={Math.round(user?.quotas_used.photos_storage_mb || 0)}
                    limit={user?.quotas_limit.photos_storage_mb || 0}
                    unit="MB"
                  />
                </div>
              </div>

              {/* Pro Plan Promo */}
              <div className="card p-8 bg-gradient-primary text-white">
                <div className="flex items-start justify-between mb-6">
                  <div>
                    <h2 className="text-2xl font-bold mb-2">
                      Upgrade to PRO
                    </h2>
                    <p className="text-white/90 text-lg">
                      Unlock unlimited features and boost your sales
                    </p>
                  </div>
                  <Badge variant="warning" size="lg">
                    19€/month
                  </Badge>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-6">
                  {[
                    'Unlimited AI analyses',
                    'Unlimited drafts',
                    'Unlimited publications',
                    'Advanced analytics',
                    'Auto-scheduling',
                    'Priority support',
                    'Custom templates',
                    'API access',
                  ].map((feature) => (
                    <div key={feature} className="flex items-center gap-2">
                      <CheckCircle className="w-5 h-5 flex-shrink-0" />
                      <span>{feature}</span>
                    </div>
                  ))}
                </div>

                <button className="px-8 py-3 bg-white text-primary-600 rounded-lg hover:bg-gray-100 font-semibold transition-colors">
                  Upgrade Now
                </button>
              </div>
            </div>
          </TabsContent>

          {/* Integrations Tab */}
          <TabsContent value="integrations">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {[
                { name: 'Telegram', description: 'Receive notifications on Telegram', status: 'connected' },
                { name: 'Google Sheets', description: 'Export your data automatically', status: 'not-connected' },
                { name: 'Notion', description: 'Sync your drafts with Notion', status: 'not-connected' },
                { name: 'Zapier', description: 'Automate with 5000+ apps', status: 'not-connected' },
                { name: 'Discord', description: 'Notifications in your Discord server', status: 'not-connected' },
                { name: 'Webhooks', description: 'Custom webhooks integration', status: 'not-connected' },
              ].map((integration) => (
                <div key={integration.name} className="card p-6">
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-center gap-3">
                      <div>
                        <h3 className="font-semibold text-gray-900 dark:text-white">
                          {integration.name}
                        </h3>
                        <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                          {integration.description}
                        </p>
                      </div>
                    </div>
                  </div>
                  {integration.status === 'connected' ? (
                    <div className="flex items-center justify-between">
                      <Badge variant="success" size="sm">Connected</Badge>
                      <button className="text-sm text-gray-600 dark:text-gray-400 hover:text-error-500">
                        Disconnect
                      </button>
                    </div>
                  ) : (
                    <button className="w-full px-4 py-2 bg-primary-50 dark:bg-primary-900/20 text-primary-700 dark:text-primary-400 rounded-lg hover:bg-primary-100 dark:hover:bg-primary-900/40 font-medium transition-colors">
                      Connect
                    </button>
                  )}
                </div>
              ))}
            </div>
          </TabsContent>
        </Tabs>
      </motion.div>
    </div>
  );
}
