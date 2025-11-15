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
  Settings as SettingsIcon,
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '../components/common/Tabs';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { GlassCard } from '../components/ui/GlassCard';
import { QuotaCard } from '../components/ui/QuotaCard';
import Avatar from '../components/common/Avatar';

export default function Settings() {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState('profile');
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
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      <div className="max-w-7xl mx-auto p-4 md:p-6 lg:p-8 space-y-8">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex items-center gap-4"
        >
          <div className="p-4 bg-gradient-to-br from-violet-500 to-purple-600 rounded-2xl shadow-lg shadow-violet-500/50">
            <SettingsIcon className="w-8 h-8 text-white" />
          </div>
          <div>
            <h1 className="text-4xl md:text-5xl font-bold bg-gradient-to-r from-white via-violet-200 to-purple-200 bg-clip-text text-transparent">
              Settings
            </h1>
            <p className="text-slate-400 mt-1">
              Manage your account preferences and configuration
            </p>
          </div>
        </motion.div>

        {/* Tabs */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.1 }}
        >
          <Tabs defaultValue="profile" onValueChange={setActiveTab}>
            {/* Glass-morphism tabs */}
            <GlassCard className="p-2 mb-8" noPadding>
              <TabsList variant="underline" className="flex flex-wrap gap-2">
                <TabsTrigger value="profile" variant="underline" className="flex items-center gap-2 px-4 py-2 rounded-lg transition-all hover:bg-white/10 data-[state=active]:bg-white/10 data-[state=active]:text-violet-400">
                  <User className="w-4 h-4" />
                  <span className="hidden sm:inline">Profile</span>
                </TabsTrigger>
                <TabsTrigger value="security" variant="underline" className="flex items-center gap-2 px-4 py-2 rounded-lg transition-all hover:bg-white/10 data-[state=active]:bg-white/10 data-[state=active]:text-violet-400">
                  <Lock className="w-4 h-4" />
                  <span className="hidden sm:inline">Security</span>
                </TabsTrigger>
                <TabsTrigger value="notifications" variant="underline" className="flex items-center gap-2 px-4 py-2 rounded-lg transition-all hover:bg-white/10 data-[state=active]:bg-white/10 data-[state=active]:text-violet-400">
                  <Bell className="w-4 h-4" />
                  <span className="hidden sm:inline">Notifications</span>
                </TabsTrigger>
                <TabsTrigger value="ai" variant="underline" className="flex items-center gap-2 px-4 py-2 rounded-lg transition-all hover:bg-white/10 data-[state=active]:bg-white/10 data-[state=active]:text-violet-400">
                  <Sparkles className="w-4 h-4" />
                  <span className="hidden sm:inline">AI</span>
                </TabsTrigger>
                <TabsTrigger value="appearance" variant="underline" className="flex items-center gap-2 px-4 py-2 rounded-lg transition-all hover:bg-white/10 data-[state=active]:bg-white/10 data-[state=active]:text-violet-400">
                  <Palette className="w-4 h-4" />
                  <span className="hidden sm:inline">Appearance</span>
                </TabsTrigger>
                <TabsTrigger value="subscription" variant="underline" className="flex items-center gap-2 px-4 py-2 rounded-lg transition-all hover:bg-white/10 data-[state=active]:bg-white/10 data-[state=active]:text-violet-400">
                  <CreditCard className="w-4 h-4" />
                  <span className="hidden sm:inline">Subscription</span>
                </TabsTrigger>
                <TabsTrigger value="integrations" variant="underline" className="flex items-center gap-2 px-4 py-2 rounded-lg transition-all hover:bg-white/10 data-[state=active]:bg-white/10 data-[state=active]:text-violet-400">
                  <Plug className="w-4 h-4" />
                  <span className="hidden sm:inline">Integrations</span>
                </TabsTrigger>
              </TabsList>
            </GlassCard>

            {/* Profile Tab */}
            <TabsContent value="profile">
              <div className="space-y-6">
                <GlassCard>
                  <h2 className="text-2xl font-bold text-white mb-6">
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
                        <Button variant="outline" size="md">
                          Change Photo
                        </Button>
                        <p className="text-sm text-slate-400 mt-2">
                          JPG, PNG or GIF. Max size 2MB
                        </p>
                      </div>
                    </div>

                    {/* Form Fields */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <Input
                        label="Full Name"
                        type="text"
                        defaultValue={user?.name}
                        icon={User}
                      />

                      <div className="relative">
                        <Input
                          label="Email"
                          type="email"
                          defaultValue={user?.email}
                          icon={User}
                        />
                        <Badge variant="success" size="sm" className="absolute right-2 top-9">
                          Verified
                        </Badge>
                      </div>

                      <Input
                        label="Phone"
                        type="tel"
                        placeholder="+33 6 12 34 56 78"
                      />

                      <div>
                        <label className="block text-sm font-medium text-slate-300 mb-2">
                          Language
                        </label>
                        <select className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white focus:outline-none focus:border-violet-500/50 focus:bg-white/10 transition-all">
                          <option>Français</option>
                          <option>English</option>
                          <option>Español</option>
                        </select>
                      </div>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-slate-300 mb-2">
                        Timezone
                      </label>
                      <select className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white focus:outline-none focus:border-violet-500/50 focus:bg-white/10 transition-all">
                        <option>Europe/Paris (GMT+1)</option>
                        <option>America/New_York (GMT-5)</option>
                        <option>Asia/Tokyo (GMT+9)</option>
                      </select>
                    </div>

                    <div className="flex justify-end">
                      <Button icon={Save}>
                        Save Changes
                      </Button>
                    </div>
                  </div>
                </GlassCard>

                {/* Vinted Account */}
                <GlassCard className="bg-gradient-to-br from-green-500/10 to-emerald-500/10 border-green-500/30">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <div className="p-3 bg-green-500/20 rounded-xl border border-green-500/30">
                        <CheckCircle className="w-6 h-6 text-green-400" />
                      </div>
                      <div>
                        <h3 className="font-semibold text-white mb-1">
                          Vinted Account Connected
                        </h3>
                        <p className="text-sm text-slate-400">
                          @{user?.name?.toLowerCase().replace(' ', '')}
                        </p>
                      </div>
                    </div>
                    <Button variant="outline">
                      Reconnect
                    </Button>
                  </div>
                </GlassCard>
              </div>
            </TabsContent>

            {/* Security Tab */}
            <TabsContent value="security">
              <div className="space-y-6">
                <GlassCard>
                  <h2 className="text-2xl font-bold text-white mb-6">
                    Password
                  </h2>

                  <div className="space-y-4">
                    <Input
                      label="Current Password"
                      type="password"
                      icon={Lock}
                    />

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <Input
                        label="New Password"
                        type="password"
                        icon={Lock}
                      />

                      <Input
                        label="Confirm New Password"
                        type="password"
                        icon={Lock}
                      />
                    </div>

                    <div className="flex justify-end">
                      <Button>Update Password</Button>
                    </div>
                  </div>
                </GlassCard>

                <GlassCard>
                  <h2 className="text-2xl font-bold text-white mb-4">
                    Two-Factor Authentication
                  </h2>
                  <p className="text-sm text-slate-400 mb-6">
                    Add an extra layer of security to your account
                  </p>

                  <div className="flex items-center justify-between p-4 bg-white/5 border border-white/10 rounded-xl">
                    <div className="flex items-center gap-3">
                      <Badge variant="error" size="sm">Disabled</Badge>
                      <span className="text-sm text-slate-300">
                        Two-factor authentication is not enabled
                      </span>
                    </div>
                    <Button variant="primary">Enable 2FA</Button>
                  </div>
                </GlassCard>

                <GlassCard className="bg-gradient-to-br from-red-500/10 to-orange-500/10 border-red-500/30">
                  <h2 className="text-2xl font-bold text-red-400 mb-2">
                    Danger Zone
                  </h2>
                  <p className="text-sm text-red-300/80 mb-4">
                    Irreversible actions. Please be careful.
                  </p>
                  <Button variant="danger">
                    Delete Account
                  </Button>
                </GlassCard>
              </div>
            </TabsContent>

            {/* Notifications Tab */}
            <TabsContent value="notifications">
              <div className="space-y-6">
                <GlassCard>
                  <h2 className="text-2xl font-bold text-white mb-6">
                    Email Notifications
                  </h2>

                  <div className="space-y-3">
                    {[
                      { key: 'emailMessages', label: 'New messages', description: 'Get notified when someone sends you a message' },
                      { key: 'emailSales', label: 'Sales confirmations', description: 'Receive confirmation when an item is sold' },
                      { key: 'emailWeekly', label: 'Weekly reports', description: 'Get a summary of your activity every week' },
                      { key: 'emailTips', label: 'Tips and tricks', description: 'Learn how to optimize your listings' },
                    ].map((item, index) => (
                      <motion.div
                        key={item.key}
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: index * 0.1 }}
                        className="flex items-start justify-between p-4 bg-white/5 border border-white/10 rounded-xl hover:bg-white/10 transition-all"
                      >
                        <div className="flex-1">
                          <h4 className="font-medium text-white mb-1">
                            {item.label}
                          </h4>
                          <p className="text-sm text-slate-400">
                            {item.description}
                          </p>
                        </div>
                        <label className="relative inline-flex items-center cursor-pointer ml-4">
                          <input
                            type="checkbox"
                            checked={notifications[item.key as keyof typeof notifications] as boolean}
                            onChange={(e) => setNotifications({ ...notifications, [item.key]: e.target.checked })}
                            className="sr-only peer"
                          />
                          <div className="w-11 h-6 bg-white/10 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-violet-500/30 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-violet-600"></div>
                        </label>
                      </motion.div>
                    ))}
                  </div>
                </GlassCard>

                <GlassCard>
                  <h2 className="text-2xl font-bold text-white mb-6">
                    Push Notifications
                  </h2>

                  <div className="space-y-3">
                    {[
                      { key: 'pushMessages', label: 'Real-time messages', description: 'Get instant notifications for new messages' },
                      { key: 'pushPublish', label: 'Publication success', description: 'Know when your items are published' },
                      { key: 'pushErrors', label: 'Error alerts', description: 'Get notified about errors or issues' },
                      { key: 'pushFeatures', label: 'New features', description: 'Learn about new features and updates' },
                    ].map((item, index) => (
                      <motion.div
                        key={item.key}
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: index * 0.1 }}
                        className="flex items-start justify-between p-4 bg-white/5 border border-white/10 rounded-xl hover:bg-white/10 transition-all"
                      >
                        <div className="flex-1">
                          <h4 className="font-medium text-white mb-1">
                            {item.label}
                          </h4>
                          <p className="text-sm text-slate-400">
                            {item.description}
                          </p>
                        </div>
                        <label className="relative inline-flex items-center cursor-pointer ml-4">
                          <input
                            type="checkbox"
                            checked={notifications[item.key as keyof typeof notifications] as boolean}
                            onChange={(e) => setNotifications({ ...notifications, [item.key]: e.target.checked })}
                            className="sr-only peer"
                          />
                          <div className="w-11 h-6 bg-white/10 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-violet-500/30 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-violet-600"></div>
                        </label>
                      </motion.div>
                    ))}
                  </div>
                </GlassCard>
              </div>
            </TabsContent>

            {/* AI Tab */}
            <TabsContent value="ai">
              <div className="space-y-6">
                <GlassCard>
                  <div className="flex items-center gap-3 mb-6">
                    <div className="p-2 bg-violet-500/20 rounded-lg border border-violet-500/30">
                      <Sparkles className="w-6 h-6 text-violet-400" />
                    </div>
                    <h2 className="text-2xl font-bold text-white">
                      AI Generation Settings
                    </h2>
                  </div>

                  <div className="space-y-6">
                    {/* Creativity Slider */}
                    <div>
                      <div className="flex items-center justify-between mb-3">
                        <label className="block text-sm font-medium text-slate-300">
                          Creativity Level
                        </label>
                        <span className="text-sm font-semibold text-violet-400">
                          {aiSettings.creativity}%
                        </span>
                      </div>
                      <input
                        type="range"
                        min="0"
                        max="100"
                        value={aiSettings.creativity}
                        onChange={(e) => setAiSettings({ ...aiSettings, creativity: parseInt(e.target.value) })}
                        className="w-full h-2 bg-white/10 rounded-lg appearance-none cursor-pointer accent-violet-500"
                      />
                      <div className="flex justify-between text-xs text-slate-400 mt-2">
                        <span>Factual</span>
                        <span>Creative</span>
                      </div>
                    </div>

                    {/* Description Length */}
                    <div>
                      <label className="block text-sm font-medium text-slate-300 mb-3">
                        Description Length
                      </label>
                      <div className="flex gap-2">
                        {['short', 'medium', 'long'].map((length) => (
                          <button
                            key={length}
                            onClick={() => setAiSettings({ ...aiSettings, descriptionLength: length })}
                            className={`flex-1 px-4 py-2 rounded-xl font-medium transition-all ${
                              aiSettings.descriptionLength === length
                                ? 'bg-gradient-to-r from-violet-500 to-purple-600 text-white shadow-lg shadow-violet-500/50'
                                : 'bg-white/5 border border-white/10 text-slate-300 hover:bg-white/10'
                            }`}
                          >
                            {length.charAt(0).toUpperCase() + length.slice(1)}
                          </button>
                        ))}
                      </div>
                    </div>

                    {/* Pricing */}
                    <div>
                      <h3 className="text-sm font-medium text-slate-300 mb-3">
                        Smart Pricing
                      </h3>
                      <div className="space-y-3">
                        <div className="flex items-center justify-between p-4 bg-white/5 border border-white/10 rounded-xl">
                          <span className="text-sm text-slate-300">
                            Enable automatic price suggestions
                          </span>
                          <label className="relative inline-flex items-center cursor-pointer">
                            <input
                              type="checkbox"
                              checked={aiSettings.autoPrice}
                              onChange={(e) => setAiSettings({ ...aiSettings, autoPrice: e.target.checked })}
                              className="sr-only peer"
                            />
                            <div className="w-11 h-6 bg-white/10 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-violet-500/30 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-violet-600"></div>
                          </label>
                        </div>

                        {aiSettings.autoPrice && (
                          <motion.div
                            initial={{ opacity: 0, height: 0 }}
                            animate={{ opacity: 1, height: 'auto' }}
                            exit={{ opacity: 0, height: 0 }}
                          >
                            <label className="block text-sm font-medium text-slate-300 mb-2">
                              Pricing Strategy
                            </label>
                            <select
                              value={aiSettings.pricingStrategy}
                              onChange={(e) => setAiSettings({ ...aiSettings, pricingStrategy: e.target.value })}
                              className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white focus:outline-none focus:border-violet-500/50 focus:bg-white/10 transition-all"
                            >
                              <option value="optimal">Optimal (Balanced)</option>
                              <option value="quick">Quick Sale (-15%)</option>
                              <option value="profit">Maximum Profit (+20%)</option>
                            </select>
                          </motion.div>
                        )}
                      </div>
                    </div>

                    <div className="flex justify-end">
                      <Button icon={Save}>
                        Save AI Settings
                      </Button>
                    </div>
                  </div>
                </GlassCard>
              </div>
            </TabsContent>

            {/* Appearance Tab */}
            <TabsContent value="appearance">
              <GlassCard>
                <h2 className="text-2xl font-bold text-white mb-6">
                  Theme
                </h2>

                <div className="grid grid-cols-3 gap-4 mb-8">
                  {[
                    { value: 'light', label: 'Light', icon: '🌞' },
                    { value: 'dark', label: 'Dark', icon: '🌙' },
                    { value: 'auto', label: 'Auto', icon: '🔄' },
                  ].map((theme) => (
                    <motion.button
                      key={theme.value}
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      className="p-6 border-2 border-white/10 bg-white/5 rounded-xl hover:border-violet-500/50 hover:bg-white/10 transition-all"
                    >
                      <div className="text-4xl mb-2">{theme.icon}</div>
                      <div className="font-medium text-white">{theme.label}</div>
                    </motion.button>
                  ))}
                </div>

                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-2">
                      Interface Density
                    </label>
                    <select className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white focus:outline-none focus:border-violet-500/50 focus:bg-white/10 transition-all">
                      <option>Comfortable (Default)</option>
                      <option>Compact</option>
                      <option>Spacious</option>
                    </select>
                  </div>

                  <div className="flex items-center justify-between p-4 bg-white/5 border border-white/10 rounded-xl">
                    <div>
                      <h4 className="font-medium text-white mb-1">
                        Enable Animations
                      </h4>
                      <p className="text-sm text-slate-400">
                        Smooth transitions and effects
                      </p>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input type="checkbox" defaultChecked className="sr-only peer" />
                      <div className="w-11 h-6 bg-white/10 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-violet-500/30 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-violet-600"></div>
                    </label>
                  </div>
                </div>
              </GlassCard>
            </TabsContent>

            {/* Subscription Tab */}
            <TabsContent value="subscription">
              <div className="space-y-6">
                {/* Current Plan */}
                <GlassCard>
                  <div className="flex items-center justify-between mb-6">
                    <div>
                      <h2 className="text-2xl font-bold text-white mb-1">
                        Current Plan: {user?.plan.toUpperCase()}
                      </h2>
                      <p className="text-sm text-slate-400">
                        Active since {new Date(user?.created_at || '').toLocaleDateString()}
                      </p>
                    </div>
                    <Badge variant="primary" size="lg">FREE</Badge>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <QuotaCard
                      icon={Sparkles}
                      label="AI Analyses"
                      used={user?.quotas_used.ai_analyses_month || 0}
                      total={user?.quotas_limit.ai_analyses_month || 0}
                      color="violet"
                    />
                    <QuotaCard
                      icon={User}
                      label="Drafts"
                      used={user?.quotas_used.drafts || 0}
                      total={user?.quotas_limit.drafts || 0}
                      color="blue"
                    />
                    <QuotaCard
                      icon={CheckCircle}
                      label="Publications"
                      used={user?.quotas_used.publications_month || 0}
                      total={user?.quotas_limit.publications_month || 0}
                      color="green"
                    />
                    <QuotaCard
                      icon={CreditCard}
                      label="Storage"
                      used={Math.round(user?.quotas_used.photos_storage_mb || 0)}
                      total={user?.quotas_limit.photos_storage_mb || 0}
                      unit="MB"
                      color="orange"
                    />
                  </div>
                </GlassCard>

                {/* Pro Plan Promo */}
                <GlassCard className="bg-gradient-to-br from-violet-500/20 to-purple-600/20 border-violet-500/30">
                  <div className="flex items-start justify-between mb-6">
                    <div>
                      <div className="flex items-center gap-3 mb-2">
                        <Sparkles className="w-8 h-8 text-violet-400" />
                        <h2 className="text-3xl font-bold text-white">
                          Upgrade to PRO
                        </h2>
                      </div>
                      <p className="text-slate-200 text-lg">
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
                    ].map((feature, index) => (
                      <motion.div
                        key={feature}
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: index * 0.05 }}
                        className="flex items-center gap-2 text-white"
                      >
                        <CheckCircle className="w-5 h-5 text-green-400 flex-shrink-0" />
                        <span>{feature}</span>
                      </motion.div>
                    ))}
                  </div>

                  <Button size="lg" className="bg-white text-violet-600 hover:bg-gray-100">
                    Upgrade Now
                  </Button>
                </GlassCard>
              </div>
            </TabsContent>

            {/* Integrations Tab */}
            <TabsContent value="integrations">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {[
                  { name: 'Telegram', description: 'Receive notifications on Telegram', status: 'connected', icon: '📱' },
                  { name: 'Google Sheets', description: 'Export your data automatically', status: 'not-connected', icon: '📊' },
                  { name: 'Notion', description: 'Sync your drafts with Notion', status: 'not-connected', icon: '📝' },
                  { name: 'Zapier', description: 'Automate with 5000+ apps', status: 'not-connected', icon: '⚡' },
                  { name: 'Discord', description: 'Notifications in your Discord server', status: 'not-connected', icon: '🔔' },
                  { name: 'Webhooks', description: 'Custom webhooks integration', status: 'not-connected', icon: '🔗' },
                ].map((integration, index) => (
                  <motion.div
                    key={integration.name}
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: index * 0.1 }}
                  >
                    <GlassCard hover>
                      <div className="flex items-start justify-between mb-4">
                        <div className="flex items-center gap-3">
                          <div className="text-3xl">{integration.icon}</div>
                          <div>
                            <h3 className="font-semibold text-white">
                              {integration.name}
                            </h3>
                            <p className="text-sm text-slate-400 mt-1">
                              {integration.description}
                            </p>
                          </div>
                        </div>
                      </div>
                      {integration.status === 'connected' ? (
                        <div className="flex items-center justify-between">
                          <Badge variant="success" size="sm">Connected</Badge>
                          <button className="text-sm text-slate-400 hover:text-red-400 transition-colors">
                            Disconnect
                          </button>
                        </div>
                      ) : (
                        <Button variant="outline" className="w-full">
                          Connect
                        </Button>
                      )}
                    </GlassCard>
                  </motion.div>
                ))}
              </div>
            </TabsContent>
          </Tabs>
        </motion.div>
      </div>
    </div>
  );
}
