import { useState, useEffect } from 'react';
import { Zap, Users, MessageCircle, RefreshCw } from 'lucide-react';
import { automationAPI } from '../api/client';
import LoadingSpinner from '../components/common/LoadingSpinner';
import type { AutomationRule } from '../types';
import { logger } from '../utils/logger';

export default function Automation() {
  const [rules, setRules] = useState<AutomationRule[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'bump' | 'follow' | 'messages'>('bump');
  
  const [saving, setSaving] = useState(false);
  const [saveMessage, setSaveMessage] = useState('');

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
    } finally {
      setLoading(false);
    }
  };

  const handleSaveBump = async () => {
    setSaving(true);
    setSaveMessage('');
    try {
      await automationAPI.configureBump(bumpConfig);
      setSaveMessage('✅ Auto-Bump configuration saved!');
      loadRules();
    } catch (error: any) {
      setSaveMessage('❌ Error: ' + (error.response?.data?.detail || 'Failed to save'));
    } finally {
      setSaving(false);
    }
  };

  const handleSaveFollow = async () => {
    setSaving(true);
    setSaveMessage('');
    try {
      await automationAPI.configureFollow(followConfig);
      setSaveMessage('✅ Auto-Follow configuration saved!');
      loadRules();
    } catch (error: any) {
      setSaveMessage('❌ Error: ' + (error.response?.data?.detail || 'Failed to save'));
    } finally {
      setSaving(false);
    }
  };

  const handleSaveMessages = async () => {
    setSaving(true);
    setSaveMessage('');
    try {
      await automationAPI.configureMessages(messageConfig);
      setSaveMessage('✅ Auto-Messages configuration saved!');
      loadRules();
    } catch (error: any) {
      setSaveMessage('❌ Error: ' + (error.response?.data?.detail || 'Failed to save'));
    } finally {
      setSaving(false);
    }
  };

  const toggleRule = async (ruleId: string, enabled: boolean) => {
    try {
      await automationAPI.updateRule(ruleId, { enabled });
      loadRules();
    } catch (error) {
      logger.error('Failed to toggle rule', error);
      alert('Failed to update rule');
    }
  };

  const deleteRule = async (ruleId: string) => {
    if (!confirm('Delete this automation rule?')) return;
    
    try {
      await automationAPI.deleteRule(ruleId);
      loadRules();
    } catch (error) {
      logger.error('Failed to delete rule', error);
      alert('Failed to delete rule');
    }
  };

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Automation</h1>
        <p className="text-gray-600 mt-2">
          🤖 PREMIUM FEATURE - Automate your Vinted activities
        </p>
      </div>

      <div className="flex gap-2">
        <button
          onClick={() => setActiveTab('bump')}
          className={`px-4 py-2 rounded-lg font-medium flex items-center gap-2 ${
            activeTab === 'bump'
              ? 'bg-primary-600 text-white'
              : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
          }`}
        >
          <RefreshCw className="w-4 h-4" />
          Auto-Bump
        </button>
        <button
          onClick={() => setActiveTab('follow')}
          className={`px-4 py-2 rounded-lg font-medium flex items-center gap-2 ${
            activeTab === 'follow'
              ? 'bg-primary-600 text-white'
              : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
          }`}
        >
          <Users className="w-4 h-4" />
          Auto-Follow
        </button>
        <button
          onClick={() => setActiveTab('messages')}
          className={`px-4 py-2 rounded-lg font-medium flex items-center gap-2 ${
            activeTab === 'messages'
              ? 'bg-primary-600 text-white'
              : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
          }`}
        >
          <MessageCircle className="w-4 h-4" />
          Auto-Messages
        </button>
      </div>

      {saveMessage && (
        <div className={`p-4 rounded-lg ${saveMessage.includes('✅') ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
          {saveMessage}
        </div>
      )}

      {loading ? (
        <div className="flex items-center justify-center h-64">
          <LoadingSpinner size="large" />
        </div>
      ) : (
        <>
          {activeTab === 'bump' && (
            <div className="card">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                Auto-Bump Configuration
              </h2>
              <p className="text-gray-600 mb-6">
                Automatically repost listings to keep them at the top. Saves money vs Vinted's paid bumps!
              </p>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Bump Interval (hours)
                  </label>
                  <input 
                    type="number" 
                    className="input" 
                    value={bumpConfig.interval_hours}
                    onChange={(e) => setBumpConfig({...bumpConfig, interval_hours: parseInt(e.target.value) || 1})}
                    min={1} 
                    max={24} 
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Daily Limit
                  </label>
                  <input 
                    type="number" 
                    className="input" 
                    value={bumpConfig.daily_limit}
                    onChange={(e) => setBumpConfig({...bumpConfig, daily_limit: parseInt(e.target.value) || 1})}
                    min={1} 
                    max={100} 
                  />
                </div>
                
                <div className="flex items-center gap-2">
                  <input 
                    type="checkbox" 
                    id="randomize" 
                    className="w-4 h-4"
                    checked={bumpConfig.rotate_listings}
                    onChange={(e) => setBumpConfig({...bumpConfig, rotate_listings: e.target.checked})}
                  />
                  <label htmlFor="randomize" className="text-sm text-gray-700">
                    Randomize order to avoid detection
                  </label>
                </div>
                
                <button 
                  onClick={handleSaveBump}
                  disabled={saving}
                  className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {saving ? 'Saving...' : 'Save Configuration'}
                </button>
              </div>
            </div>
          )}

          {activeTab === 'follow' && (
            <div className="card">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                Auto-Follow Configuration
              </h2>
              <p className="text-gray-600 mb-6">
                Automatically follow users to grow your audience. ~10% follow-back rate!
              </p>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Target Categories
                  </label>
                  <input
                    type="text"
                    className="input"
                    placeholder="e.g., fashion, shoes, accessories"
                    value={followConfig.target_categories}
                    onChange={(e) => setFollowConfig({...followConfig, target_categories: e.target.value})}
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Daily Follow Limit
                  </label>
                  <input 
                    type="number" 
                    className="input" 
                    value={followConfig.daily_limit}
                    onChange={(e) => setFollowConfig({...followConfig, daily_limit: parseInt(e.target.value) || 1})}
                    min={1} 
                    max={200} 
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Auto-Unfollow After (days)
                  </label>
                  <input 
                    type="number" 
                    className="input" 
                    value={followConfig.unfollow_after_days}
                    onChange={(e) => setFollowConfig({...followConfig, unfollow_after_days: parseInt(e.target.value) || 1})}
                    min={1} 
                    max={30} 
                  />
                </div>
                
                <button 
                  onClick={handleSaveFollow}
                  disabled={saving}
                  className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {saving ? 'Saving...' : 'Save Configuration'}
                </button>
              </div>
            </div>
          )}

          {activeTab === 'messages' && (
            <div className="card">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                Auto-Messages Configuration
              </h2>
              <p className="text-gray-600 mb-6">
                Send automatic messages to likers with personalized offers
              </p>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Message Template
                  </label>
                  <textarea
                    className="input min-h-[100px]"
                    placeholder="Hi! I noticed you liked my {item_title}. I can offer it to you for {price}€. Interested?"
                    value={messageConfig.template}
                    onChange={(e) => setMessageConfig({...messageConfig, template: e.target.value})}
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Variables: {'{item_title}'}, {'{price}'}, {'{brand}'}, {'{category}'}
                  </p>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Delay After Like (minutes)
                  </label>
                  <input 
                    type="number" 
                    className="input" 
                    value={messageConfig.delay_minutes}
                    onChange={(e) => setMessageConfig({...messageConfig, delay_minutes: parseInt(e.target.value) || 1})}
                    min={1} 
                    max={1440} 
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Daily Message Limit
                  </label>
                  <input 
                    type="number" 
                    className="input" 
                    value={messageConfig.daily_limit}
                    onChange={(e) => setMessageConfig({...messageConfig, daily_limit: parseInt(e.target.value) || 1})}
                    min={1} 
                    max={100} 
                  />
                </div>
                
                <button 
                  onClick={handleSaveMessages}
                  disabled={saving}
                  className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {saving ? 'Saving...' : 'Save Template'}
                </button>
              </div>
            </div>
          )}

          <div className="card">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Active Rules</h3>
            {rules.length > 0 ? (
              <div className="space-y-3">
                {rules.map((rule) => (
                  <div key={rule.id} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                    <div className="flex-1">
                      <p className="font-medium text-gray-900">
                        {rule.type.toUpperCase()} Automation
                      </p>
                      <p className="text-sm text-gray-600">
                        Last run: {rule.last_run ? new Date(rule.last_run).toLocaleString() : 'Never'}
                      </p>
                    </div>
                    <div className="flex items-center gap-3">
                      <label className="flex items-center gap-2">
                        <input
                          type="checkbox"
                          checked={rule.enabled}
                          onChange={(e) => toggleRule(rule.id, e.target.checked)}
                          className="w-4 h-4"
                        />
                        <span className="text-sm text-gray-700">Enabled</span>
                      </label>
                      <button
                        onClick={() => deleteRule(rule.id)}
                        className="text-red-600 hover:text-red-700 text-sm font-medium"
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-center py-8 text-gray-500">
                No automation rules configured yet
              </p>
            )}
          </div>
        </>
      )}
    </div>
  );
}
