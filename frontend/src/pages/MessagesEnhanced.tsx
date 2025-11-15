import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Search,
  Send,
  Sparkles,
  Settings as SettingsIcon,
  MessageSquare,
  Zap,
  ThumbsUp,
  ThumbsDown
} from 'lucide-react';
import { Badge } from '../components/ui/Badge';
import { GlassCard } from '../components/ui/GlassCard';
import { Button } from '../components/ui/Button';
import toast from 'react-hot-toast';

interface AIResponse {
  response: string;
  intention: string;
  confidence: number;
  tone: string;
}

interface AISettings {
  auto_reply_enabled: boolean;
  tone: 'friendly' | 'professional' | 'casual';
  mode: 'auto' | 'draft' | 'notify';
}

export default function MessagesEnhanced() {
  const [messageInput, setMessageInput] = useState('');
  const [aiResponse, setAiResponse] = useState<AIResponse | null>(null);
  const [generating, setGenerating] = useState(false);
  const [settings, setSettings] = useState<AISettings>({
    auto_reply_enabled: false,
    tone: 'friendly',
    mode: 'draft'
  });
  const [showSettings, setShowSettings] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Mock conversation data
  const mockConversation = {
    user: { name: 'Marie Dupont' },
    item: { name: 'Nike Air Max 90', price: 89.99 },
    lastMessage: 'Bonjour, est-ce que l\'article est toujours disponible ?'
  };

  const mockMessages = [
    {
      id: '1',
      text: 'Bonjour ! Je suis intéressée par votre article. Est-ce qu\'il est toujours disponible ?',
      timestamp: new Date(Date.now() - 10 * 60000),
      isOwn: false,
    },
    {
      id: '2',
      text: 'Super ! Pourriez-vous me donner plus de détails sur l\'état ?',
      timestamp: new Date(Date.now() - 5 * 60000),
      isOwn: false,
    }
  ];

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      const response = await fetch('/api/v1/ai-messages/settings', {
        credentials: 'include'
      });
      const data = await response.json();
      setSettings(data);
    } catch (error) {
      console.error('Failed to load AI settings:', error);
    }
  };

  const generateAIResponse = async (incomingMessage: string) => {
    setGenerating(true);
    const loadingToast = toast.loading('🤖 Generating AI response...');

    try {
      const response = await fetch('/api/v1/ai-messages/generate-response', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          message: incomingMessage,
          article_context: {
            title: mockConversation.item.name,
            price: mockConversation.item.price,
            condition: 'Excellent état',
            size: 'M'
          },
          tone: settings.tone
        })
      });

      const data = await response.json();
      setAiResponse(data);
      setMessageInput(data.response);
      toast.success(`✨ AI response ready! (${Math.round(data.confidence * 100)}% confidence)`, { id: loadingToast });
    } catch (error) {
      toast.error('Failed to generate AI response', { id: loadingToast });
      console.error('AI generation error:', error);
    } finally {
      setGenerating(false);
    }
  };

  const saveSettings = async () => {
    try {
      await fetch('/api/v1/ai-messages/settings', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(settings)
      });
      toast.success('Settings saved!');
      setShowSettings(false);
    } catch (error) {
      toast.error('Failed to save settings');
    }
  };

  const sendMessage = () => {
    if (!messageInput.trim()) return;
    toast.success('Message sent!');
    setMessageInput('');
    setAiResponse(null);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      {/* Header */}
      <motion.div
        className="p-8"
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="p-3 bg-gradient-to-br from-violet-500 to-purple-600 rounded-2xl shadow-lg shadow-violet-500/50">
              <MessageSquare className="w-8 h-8 text-white" />
            </div>
            <div>
              <h1 className="text-4xl md:text-5xl font-bold bg-gradient-to-r from-white via-violet-200 to-purple-200 bg-clip-text text-transparent">
                AI Messages
              </h1>
              <p className="text-slate-400">GPT-4 powered auto-replies</p>
            </div>
          </div>

          <div className="flex gap-3">
            <Badge className={settings.auto_reply_enabled ? "bg-green-500/20 border-green-500/30 text-green-300" : "bg-slate-700/50"}>
              {settings.auto_reply_enabled ? '✨ AI ON' : 'AI OFF'}
            </Badge>
            <Button variant="outline" icon={SettingsIcon} onClick={() => setShowSettings(!showSettings)}>
              Settings
            </Button>
          </div>
        </div>
      </motion.div>

      <div className="max-w-7xl mx-auto px-8 space-y-6 pb-12">
        {/* Settings Panel */}
        <AnimatePresence>
          {showSettings && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
            >
              <GlassCard className="p-6">
                <h3 className="text-xl font-bold text-white mb-4">AI Settings</h3>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  {/* Auto-Reply Toggle */}
                  <div>
                    <label className="block text-sm font-medium text-slate-400 mb-2">
                      Auto-Reply
                    </label>
                    <button
                      onClick={() => setSettings({ ...settings, auto_reply_enabled: !settings.auto_reply_enabled })}
                      className={`w-full px-4 py-3 rounded-xl border-2 transition-all ${
                        settings.auto_reply_enabled
                          ? 'border-green-500 bg-green-500/20 text-green-300'
                          : 'border-white/10 bg-white/5 text-slate-400'
                      }`}
                    >
                      {settings.auto_reply_enabled ? '✅ Enabled' : '❌ Disabled'}
                    </button>
                  </div>

                  {/* Tone Selector */}
                  <div>
                    <label className="block text-sm font-medium text-slate-400 mb-2">
                      Response Tone
                    </label>
                    <select
                      value={settings.tone}
                      onChange={(e) => setSettings({ ...settings, tone: e.target.value as any })}
                      className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white focus:border-violet-500/50"
                    >
                      <option value="friendly">😊 Friendly</option>
                      <option value="professional">💼 Professional</option>
                      <option value="casual">👋 Casual</option>
                    </select>
                  </div>

                  {/* Mode Selector */}
                  <div>
                    <label className="block text-sm font-medium text-slate-400 mb-2">
                      Mode
                    </label>
                    <select
                      value={settings.mode}
                      onChange={(e) => setSettings({ ...settings, mode: e.target.value as any })}
                      className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white focus:border-violet-500/50"
                    >
                      <option value="draft">📝 Draft (review before send)</option>
                      <option value="auto">⚡ Auto (send immediately)</option>
                      <option value="notify">🔔 Notify (just alert)</option>
                    </select>
                  </div>
                </div>

                <div className="mt-6">
                  <Button onClick={saveSettings}>
                    Save Settings
                  </Button>
                </div>
              </GlassCard>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Chat Area */}
        <GlassCard className="p-6">
          {/* Chat Header */}
          <div className="flex items-center gap-3 pb-4 border-b border-white/10">
            <img
              src="https://via.placeholder.com/40"
              className="w-10 h-10 rounded-full"
              alt="User"
            />
            <div className="flex-1">
              <h3 className="font-semibold text-white">{mockConversation.user.name}</h3>
              <p className="text-sm text-slate-400">{mockConversation.item.name} - {mockConversation.item.price}€</p>
            </div>
            <img
              src="https://via.placeholder.com/60"
              className="w-12 h-12 rounded-lg object-cover"
              alt="Item"
            />
          </div>

          {/* Messages */}
          <div className="py-6 space-y-4 h-64 overflow-y-auto">
            {mockMessages.map(msg => (
              <div
                key={msg.id}
                className={`flex ${msg.isOwn ? 'justify-end' : 'justify-start'}`}
              >
                <div className={`max-w-[70%] p-3 rounded-lg ${
                  msg.isOwn
                    ? 'bg-violet-500/20 border border-violet-500/30'
                    : 'bg-white/5 border border-white/10'
                }`}>
                  <p className="text-white">{msg.text}</p>
                  <p className="text-xs text-slate-500 mt-1">
                    {msg.timestamp.toLocaleTimeString()}
                  </p>
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>

          {/* AI Suggestion Preview */}
          <AnimatePresence>
            {aiResponse && (
              <motion.div
                className="mb-4 p-4 bg-violet-500/10 border border-violet-500/30 rounded-lg"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 20 }}
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <Sparkles className="w-4 h-4 text-violet-400" />
                    <span className="text-sm font-semibold text-violet-300">
                      AI Suggestion ({Math.round(aiResponse.confidence * 100)}% confidence)
                    </span>
                    <Badge className="bg-blue-500/20 text-blue-300 text-xs">
                      {aiResponse.intention}
                    </Badge>
                  </div>
                  <div className="flex gap-2">
                    <button onClick={() => setAiResponse(null)} className="text-slate-400 hover:text-white">
                      <ThumbsDown className="w-4 h-4" />
                    </button>
                    <button className="text-slate-400 hover:text-green-400">
                      <ThumbsUp className="w-4 h-4" />
                    </button>
                  </div>
                </div>
                <p className="text-white text-sm">{aiResponse.response}</p>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Message Input */}
          <div className="pt-4 border-t border-white/10">
            <div className="flex gap-2">
              <input
                type="text"
                value={messageInput}
                onChange={(e) => setMessageInput(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
                placeholder="Type a message..."
                className="flex-1 px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder-slate-400 focus:outline-none focus:border-violet-500/50"
              />
              <Button
                variant="outline"
                icon={Sparkles}
                onClick={() => generateAIResponse(mockMessages[mockMessages.length - 1].text)}
                disabled={generating}
              >
                {generating ? 'Generating...' : 'AI'}
              </Button>
              <Button icon={Send} onClick={sendMessage}>
                Send
              </Button>
            </div>
          </div>
        </GlassCard>

        {/* Info Box */}
        <GlassCard className="p-4 bg-blue-500/10 border-blue-500/30">
          <div className="flex items-start gap-3">
            <Zap className="w-5 h-5 text-blue-400 flex-shrink-0 mt-0.5" />
            <div className="text-sm text-blue-300">
              <strong>GPT-4 Powered:</strong> AI analyzes buyer messages and generates contextual responses based on item details, automatically detecting intent (price negotiation, availability, condition questions, etc.)
            </div>
          </div>
        </GlassCard>
      </div>
    </div>
  );
}
