import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Zap, Users, MessageCircle, RefreshCw, Save, Trash2, Check } from 'lucide-react';
import { automationAPI } from '../api/client';
import { GlassCard } from '../components/ui/GlassCard';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { EmptyState } from '../components/ui/EmptyState';
import type { AutomationRule } from '../types';
import { logger } from '../utils/logger';
import toast from 'react-hot-toast';

export default function Automation() {
  const [rules, setRules] = useState<AutomationRule[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'bump' | 'follow' | 'messages'>('bump');
  const [saving, setSaving] = useState(false);

  const [bumpConfig, setBumpConfig] = useState({
    enabled: true,
    interval_hours: 12,
    target_listings: [],
    daily_limit: 20,
    rotate_listings: true,
    skip_recent_hours: 6
  });

  const [followConfig, setFollowConfig] = useState({
    enabled: true,
    target_users: [],
    target_categories: '',
    daily_limit: 50,
    source: 'targeted',
    unfollow_after_days: 7
  });

  const [messageConfig, setMessageConfig] = useState({
    enabled: true,
    template: "Hi! I noticed you liked my {item_title}. I can offer it to you for {price}€. Interested?",
    delay_minutes: 30,
    daily_limit: 30,
    triggers: ['new_follower', 'new_like']
  });

  useEffect(() => {
    loadRules();
  }, []);

  const loadRules = async () => {
    try {
      const response = await automationAPI.getRules();
      setRules(response.data);

      const bumpRule = response.data.find((r: any) => r.type === 'bump');
      if (bumpRule && bumpRule.config) {
        try {
          const config = typeof bumpRule.config === 'string'
            ? JSON.parse(bumpRule.config)
            : bumpRule.config;
          setBumpConfig({ ...bumpConfig, ...config });
        } catch (e) {
          logger.error('Failed to parse bump config', e);
        }
      }

      const followRule = response.data.find((r: any) => r.type === 'follow');
      if (followRule && followRule.config) {
        try {
          const config = typeof followRule.config === 'string'
            ? JSON.parse(followRule.config)
            : followRule.config;
          setFollowConfig({ ...followConfig, ...config });
        } catch (e) {
          logger.error('Failed to parse follow config', e);
        }
      }

      const messageRule = response.data.find((r: any) => r.type === 'messages');
      if (messageRule && messageRule.config) {
        try {
          const config = typeof messageRule.config === 'string'
            ? JSON.parse(messageRule.config)
            : messageRule.config;
          setMessageConfig({ ...messageConfig, ...config });
        } catch (e) {
          logger.error('Failed to parse message config', e);
        }
      }
    } catch (error) {
      logger.error('Failed to load rules', error);
      toast.error('Failed to load automation rules');
    } finally {
      setLoading(false);
    }
  };

  const handleSaveBump = async () => {
    setSaving(true);
    try {
      await automationAPI.configureBump(bumpConfig);
      toast.success('Auto-Bump configuration saved!');
      loadRules();
    } catch (error: any) {
      toast.error('Failed to save: ' + (error.response?.data?.detail || 'Unknown error'));
    } finally {
      setSaving(false);
    }
  };

  const handleSaveFollow = async () => {
    setSaving(true);
    try {
      await automationAPI.configureFollow(followConfig);
      toast.success('Auto-Follow configuration saved!');
      loadRules();
    } catch (error: any) {
      toast.error('Failed to save: ' + (error.response?.data?.detail || 'Unknown error'));
    } finally {
      setSaving(false);
    }
  };

  const handleSaveMessages = async () => {
    setSaving(true);
    try {
      await automationAPI.configureMessages(messageConfig);
      toast.success('Auto-Messages configuration saved!');
      loadRules();
    } catch (error: any) {
      toast.error('Failed to save: ' + (error.response?.data?.detail || 'Unknown error'));
    } finally {
      setSaving(false);
    }
  };

  const toggleRule = async (ruleId: string, enabled: boolean) => {
    try {
      await automationAPI.updateRule(ruleId, { enabled });
      toast.success(`Rule ${enabled ? 'enabled' : 'disabled'}`);
      loadRules();
    } catch (error) {
      logger.error('Failed to toggle rule', error);
      toast.error('Failed to update rule');
    }
  };

  const deleteRule = async (ruleId: string) => {
    if (!confirm('Delete this automation rule?')) return;

    try {
      await automationAPI.deleteRule(ruleId);
      toast.success('Rule deleted');
      loadRules();
    } catch (error) {
      logger.error('Failed to delete rule', error);
      toast.error('Failed to delete rule');
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
              <p className="text-slate-400">Loading automation...</p>
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
          className="flex items-center gap-4"
        >
          <div className="p-4 bg-gradient-to-br from-violet-500 to-purple-600 rounded-2xl shadow-lg shadow-violet-500/50">
            <Zap className="w-8 h-8 text-white" />
          </div>
          <div>
            <h1 className="text-4xl md:text-5xl font-bold bg-gradient-to-r from-white via-violet-200 to-purple-200 bg-clip-text text-transparent">
              Automation
            </h1>
            <div className="flex items-center gap-2 mt-1">
              <Badge variant="warning" size="md">
                PREMIUM FEATURE
              </Badge>
              <p className="text-slate-400">
                Automate your Vinted activities
              </p>
            </div>
          </div>
        </motion.div>

        {/* Tabs */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.1 }}
        >
          <GlassCard className="p-2" noPadding>
            <div className="flex gap-2 flex-wrap">
              <button
                onClick={() => setActiveTab('bump')}
                className={`px-4 py-2 rounded-xl font-medium flex items-center gap-2 transition-all ${
                  activeTab === 'bump'
                    ? 'bg-gradient-to-r from-violet-500 to-purple-600 text-white shadow-lg shadow-violet-500/50'
                    : 'text-slate-300 hover:bg-white/5'
                }`}
              >
                <RefreshCw className="w-4 h-4" />
                Auto-Bump
              </button>
              <button
                onClick={() => setActiveTab('follow')}
                className={`px-4 py-2 rounded-xl font-medium flex items-center gap-2 transition-all ${
                  activeTab === 'follow'
                    ? 'bg-gradient-to-r from-violet-500 to-purple-600 text-white shadow-lg shadow-violet-500/50'
                    : 'text-slate-300 hover:bg-white/5'
                }`}
              >
                <Users className="w-4 h-4" />
                Auto-Follow
              </button>
              <button
                onClick={() => setActiveTab('messages')}
                className={`px-4 py-2 rounded-xl font-medium flex items-center gap-2 transition-all ${
                  activeTab === 'messages'
                    ? 'bg-gradient-to-r from-violet-500 to-purple-600 text-white shadow-lg shadow-violet-500/50'
                    : 'text-slate-300 hover:bg-white/5'
                }`}
              >
                <MessageCircle className="w-4 h-4" />
                Auto-Messages
              </button>
            </div>
          </GlassCard>
        </motion.div>

        {/* Tab Content */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          {activeTab === 'bump' && (
            <GlassCard>
              <h2 className="text-2xl font-bold text-white mb-2">
                Auto-Bump Configuration
              </h2>
              <p className="text-slate-400 mb-6">
                Automatically repost listings to keep them at the top. Saves money vs Vinted's paid bumps!
              </p>

              <div className="space-y-6">
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Bump Interval (hours)
                  </label>
                  <input
                    type="number"
                    className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder-slate-400 focus:outline-none focus:border-violet-500/50 focus:bg-white/10 transition-all"
                    value={bumpConfig.interval_hours}
                    onChange={(e) => setBumpConfig({...bumpConfig, interval_hours: parseInt(e.target.value) || 1})}
                    min={1}
                    max={24}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Daily Limit
                  </label>
                  <input
                    type="number"
                    className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder-slate-400 focus:outline-none focus:border-violet-500/50 focus:bg-white/10 transition-all"
                    value={bumpConfig.daily_limit}
                    onChange={(e) => setBumpConfig({...bumpConfig, daily_limit: parseInt(e.target.value) || 1})}
                    min={1}
                    max={100}
                  />
                </div>

                <div className="flex items-center gap-3 p-4 bg-white/5 border border-white/10 rounded-xl">
                  <input
                    type="checkbox"
                    id="randomize"
                    className="w-5 h-5 rounded border-white/20 bg-white/5 text-violet-600 focus:ring-violet-500"
                    checked={bumpConfig.rotate_listings}
                    onChange={(e) => setBumpConfig({...bumpConfig, rotate_listings: e.target.checked})}
                  />
                  <label htmlFor="randomize" className="text-sm text-slate-300 cursor-pointer">
                    Randomize order to avoid detection
                  </label>
                </div>

                <Button
                  onClick={handleSaveBump}
                  disabled={saving}
                  loading={saving}
                  icon={Save}
                >
                  {saving ? 'Saving...' : 'Save Configuration'}
                </Button>
              </div>
            </GlassCard>
          )}

          {activeTab === 'follow' && (
            <GlassCard>
              <h2 className="text-2xl font-bold text-white mb-2">
                Auto-Follow Configuration
              </h2>
              <p className="text-slate-400 mb-6">
                Automatically follow users to grow your audience. ~10% follow-back rate!
              </p>

              <div className="space-y-6">
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Target Categories
                  </label>
                  <input
                    type="text"
                    className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder-slate-400 focus:outline-none focus:border-violet-500/50 focus:bg-white/10 transition-all"
                    placeholder="e.g., fashion, shoes, accessories"
                    value={followConfig.target_categories}
                    onChange={(e) => setFollowConfig({...followConfig, target_categories: e.target.value})}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Daily Follow Limit
                  </label>
                  <input
                    type="number"
                    className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder-slate-400 focus:outline-none focus:border-violet-500/50 focus:bg-white/10 transition-all"
                    value={followConfig.daily_limit}
                    onChange={(e) => setFollowConfig({...followConfig, daily_limit: parseInt(e.target.value) || 1})}
                    min={1}
                    max={200}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Auto-Unfollow After (days)
                  </label>
                  <input
                    type="number"
                    className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder-slate-400 focus:outline-none focus:border-violet-500/50 focus:bg-white/10 transition-all"
                    value={followConfig.unfollow_after_days}
                    onChange={(e) => setFollowConfig({...followConfig, unfollow_after_days: parseInt(e.target.value) || 1})}
                    min={1}
                    max={30}
                  />
                </div>

                <Button
                  onClick={handleSaveFollow}
                  disabled={saving}
                  loading={saving}
                  icon={Save}
                >
                  {saving ? 'Saving...' : 'Save Configuration'}
                </Button>
              </div>
            </GlassCard>
          )}

          {activeTab === 'messages' && (
            <GlassCard>
              <h2 className="text-2xl font-bold text-white mb-2">
                Auto-Messages Configuration
              </h2>
              <p className="text-slate-400 mb-6">
                Send automatic messages to likers with personalized offers
              </p>

              <div className="space-y-6">
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Message Template
                  </label>
                  <textarea
                    className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder-slate-400 resize-none focus:outline-none focus:border-violet-500/50 focus:bg-white/10 transition-all min-h-[100px]"
                    placeholder="Hi! I noticed you liked my {item_title}. I can offer it to you for {price}€. Interested?"
                    value={messageConfig.template}
                    onChange={(e) => setMessageConfig({...messageConfig, template: e.target.value})}
                  />
                  <p className="text-xs text-slate-500 mt-2">
                    Variables: {'{item_title}'}, {'{price}'}, {'{brand}'}, {'{category}'}
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Delay After Like (minutes)
                  </label>
                  <input
                    type="number"
                    className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder-slate-400 focus:outline-none focus:border-violet-500/50 focus:bg-white/10 transition-all"
                    value={messageConfig.delay_minutes}
                    onChange={(e) => setMessageConfig({...messageConfig, delay_minutes: parseInt(e.target.value) || 1})}
                    min={1}
                    max={1440}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Daily Message Limit
                  </label>
                  <input
                    type="number"
                    className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder-slate-400 focus:outline-none focus:border-violet-500/50 focus:bg-white/10 transition-all"
                    value={messageConfig.daily_limit}
                    onChange={(e) => setMessageConfig({...messageConfig, daily_limit: parseInt(e.target.value) || 1})}
                    min={1}
                    max={100}
                  />
                </div>

                <Button
                  onClick={handleSaveMessages}
                  disabled={saving}
                  loading={saving}
                  icon={Save}
                >
                  {saving ? 'Saving...' : 'Save Template'}
                </Button>
              </div>
            </GlassCard>
          )}
        </motion.div>

        {/* Active Rules */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
        >
          <GlassCard>
            <h3 className="text-xl font-bold text-white mb-6">Active Rules</h3>
            {rules.length > 0 ? (
              <div className="space-y-3">
                {rules.map((rule, index) => (
                  <motion.div
                    key={rule.id}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.1 }}
                    className="flex items-center justify-between p-4 bg-white/5 border border-white/10 rounded-xl hover:bg-white/10 transition-all"
                  >
                    <div className="flex-1">
                      <p className="font-semibold text-white mb-1">
                        {rule.type.toUpperCase()} Automation
                      </p>
                      <p className="text-sm text-slate-400">
                        Last run: {rule.last_run ? new Date(rule.last_run).toLocaleString() : 'Never'}
                      </p>
                    </div>
                    <div className="flex items-center gap-4">
                      <label className="flex items-center gap-2 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={rule.enabled}
                          onChange={(e) => toggleRule(rule.id, e.target.checked)}
                          className="w-5 h-5 rounded border-white/20 bg-white/5 text-violet-600 focus:ring-violet-500"
                        />
                        <span className="text-sm text-slate-300">Enabled</span>
                      </label>
                      <Button
                        variant="danger"
                        size="sm"
                        onClick={() => deleteRule(rule.id)}
                        icon={Trash2}
                      >
                        Delete
                      </Button>
                    </div>
                  </motion.div>
                ))}
              </div>
            ) : (
              <EmptyState
                icon={Zap}
                title="No automation rules"
                description="Configure automation above to create your first rule"
              />
            )}
          </GlassCard>
        </motion.div>
      </div>
    </div>
  );
}
