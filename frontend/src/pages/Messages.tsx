import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Search,
  Send,
  Sparkles,
  Image as ImageIcon,
  Paperclip,
  MoreVertical,
  Check,
  CheckCheck,
  Clock,
  Filter,
  Star,
  Archive,
  Trash2,
  Phone,
  Video,
  Info,
  ThumbsUp,
  Smile,
  MessageSquare,
} from 'lucide-react';
import { Badge } from '../components/ui/Badge';
import { GlassCard } from '../components/ui/GlassCard';
import { Button } from '../components/ui/Button';
import { EmptyState } from '../components/ui/EmptyState';
import Avatar from '../components/common/Avatar';
import { Tooltip } from '../components/common/Tooltip';

interface Message {
  id: string;
  text: string;
  timestamp: Date;
  isOwn: boolean;
  status?: 'sent' | 'delivered' | 'read';
  attachments?: { type: 'image' | 'file'; url: string; name?: string }[];
}

interface Conversation {
  id: string;
  user: {
    name: string;
    avatar?: string;
    isOnline: boolean;
  };
  lastMessage: string;
  timestamp: Date;
  unread: number;
  isPinned: boolean;
  item: {
    name: string;
    price: number;
    thumbnail: string;
  };
}

interface AISuggestion {
  id: string;
  text: string;
  tone: 'friendly' | 'professional' | 'concise';
  context: string;
}

const mockConversations: Conversation[] = [
  {
    id: '1',
    user: { name: 'Marie Dupont', avatar: 'https://via.placeholder.com/40', isOnline: true },
    lastMessage: 'Bonjour, est-ce que l\'article est toujours disponible ?',
    timestamp: new Date(Date.now() - 5 * 60000),
    unread: 2,
    isPinned: true,
    item: { name: 'Nike Air Max 90', price: 89.99, thumbnail: 'https://via.placeholder.com/60' },
  },
  {
    id: '2',
    user: { name: 'Lucas Martin', avatar: 'https://via.placeholder.com/40', isOnline: false },
    lastMessage: 'Merci pour la réponse rapide !',
    timestamp: new Date(Date.now() - 2 * 3600000),
    unread: 0,
    isPinned: false,
    item: { name: 'Adidas Hoodie', price: 45.00, thumbnail: 'https://via.placeholder.com/60' },
  },
  {
    id: '3',
    user: { name: 'Sophie Bernard', avatar: 'https://via.placeholder.com/40', isOnline: true },
    lastMessage: 'Quel est l\'état exact du produit ?',
    timestamp: new Date(Date.now() - 24 * 3600000),
    unread: 1,
    isPinned: false,
    item: { name: 'Levi\'s 501 Jeans', price: 65.00, thumbnail: 'https://via.placeholder.com/60' },
  },
];

const mockMessages: Message[] = [
  {
    id: '1',
    text: 'Bonjour ! Je suis intéressée par votre article. Est-ce qu\'il est toujours disponible ?',
    timestamp: new Date(Date.now() - 10 * 60000),
    isOwn: false,
  },
  {
    id: '2',
    text: 'Oui bien sûr ! L\'article est toujours disponible 😊',
    timestamp: new Date(Date.now() - 8 * 60000),
    isOwn: true,
    status: 'read',
  },
  {
    id: '3',
    text: 'Super ! Pourriez-vous me donner plus de détails sur l\'état ?',
    timestamp: new Date(Date.now() - 5 * 60000),
    isOwn: false,
  },
];

const aiSuggestions: AISuggestion[] = [
  {
    id: '1',
    text: 'L\'article est en excellent état, porté seulement 2-3 fois. Aucun défaut visible !',
    tone: 'friendly',
    context: 'Réponse détaillée sur l\'état',
  },
  {
    id: '2',
    text: 'État: comme neuf. Porté occasionnellement, pas de signes d\'usure.',
    tone: 'professional',
    context: 'Réponse concise professionnelle',
  },
  {
    id: '3',
    text: 'Excellent état ! Vous pouvez voir tous les détails sur les photos. N\'hésitez pas si vous avez d\'autres questions 😊',
    tone: 'friendly',
    context: 'Réponse amicale avec encouragement',
  },
];

export default function Messages() {
  const [selectedConversation, setSelectedConversation] = useState<Conversation | null>(
    mockConversations[0]
  );
  const [messages, setMessages] = useState<Message[]>(mockMessages);
  const [messageInput, setMessageInput] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [showAISuggestions, setShowAISuggestions] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = () => {
    if (!messageInput.trim()) return;

    const newMessage: Message = {
      id: Date.now().toString(),
      text: messageInput,
      timestamp: new Date(),
      isOwn: true,
      status: 'sent',
    };

    setMessages([...messages, newMessage]);
    setMessageInput('');
    setShowAISuggestions(false);
  };

  const handleUseSuggestion = (suggestion: AISuggestion) => {
    setMessageInput(suggestion.text);
    setShowAISuggestions(false);
  };

  const filteredConversations = mockConversations.filter(conv =>
    conv.user.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    conv.lastMessage.toLowerCase().includes(searchQuery.toLowerCase()) ||
    conv.item.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const getMessageStatusIcon = (status?: Message['status']) => {
    switch (status) {
      case 'sent':
        return <Check className="w-4 h-4" />;
      case 'delivered':
        return <CheckCheck className="w-4 h-4" />;
      case 'read':
        return <CheckCheck className="w-4 h-4 text-violet-400" />;
      default:
        return <Clock className="w-4 h-4" />;
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      <div className="max-w-7xl mx-auto p-4 md:p-6 lg:p-8">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex items-center gap-4 mb-8"
        >
          <div className="p-4 bg-gradient-to-br from-violet-500 to-purple-600 rounded-2xl shadow-lg shadow-violet-500/50">
            <MessageSquare className="w-8 h-8 text-white" />
          </div>
          <div>
            <h1 className="text-4xl md:text-5xl font-bold bg-gradient-to-r from-white via-violet-200 to-purple-200 bg-clip-text text-transparent">
              Messages
            </h1>
            <p className="text-slate-400 mt-1">
              Chat with your buyers and sellers
            </p>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="h-[calc(100vh-240px)]"
        >
          <GlassCard className="h-full flex overflow-hidden" noPadding>
            {/* Conversations Sidebar */}
            <div className="w-80 border-r border-white/10 flex flex-col">
              {/* Sidebar Header */}
              <div className="p-4 border-b border-white/10">
                {/* Search */}
                <div className="relative mb-4">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                  <input
                    type="text"
                    placeholder="Search conversations..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="w-full pl-10 pr-4 py-2 bg-white/5 border border-white/10 rounded-xl text-white text-sm placeholder-slate-400 focus:outline-none focus:border-violet-500/50 focus:bg-white/10 transition-all"
                  />
                </div>

                {/* Filters */}
                <div className="flex items-center gap-2">
                  <button className="px-3 py-1.5 text-xs font-medium bg-gradient-to-r from-violet-500 to-purple-600 text-white rounded-lg shadow-lg shadow-violet-500/30">
                    All
                  </button>
                  <button className="px-3 py-1.5 text-xs font-medium text-slate-400 hover:text-white hover:bg-white/5 rounded-lg transition-colors">
                    Unread
                  </button>
                  <button className="px-3 py-1.5 text-xs font-medium text-slate-400 hover:text-white hover:bg-white/5 rounded-lg transition-colors">
                    Pinned
                  </button>
                </div>
              </div>

              {/* Conversations List */}
              <div className="flex-1 overflow-y-auto">
                {filteredConversations.map((conv) => (
                  <motion.div
                    key={conv.id}
                    whileHover={{ backgroundColor: 'rgba(255,255,255,0.05)' }}
                    onClick={() => setSelectedConversation(conv)}
                    className={`p-4 cursor-pointer border-b border-white/5 transition-colors ${
                      selectedConversation?.id === conv.id
                        ? 'bg-violet-500/10 border-violet-500/30'
                        : 'hover:bg-white/5'
                    }`}
                  >
                    <div className="flex items-start gap-3">
                      <Avatar
                        src={conv.user.avatar}
                        alt={conv.user.name}
                        size="md"
                        status={conv.user.isOnline ? 'online' : 'offline'}
                      />

                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between mb-1">
                          <span className="font-semibold text-white text-sm truncate">
                            {conv.user.name}
                          </span>
                          {conv.isPinned && (
                            <Star className="w-3 h-3 text-yellow-400 fill-yellow-400" />
                          )}
                        </div>

                        <p className="text-sm text-slate-400 truncate mb-1">
                          {conv.lastMessage}
                        </p>

                        <div className="flex items-center justify-between">
                          <span className="text-xs text-slate-500">
                            {conv.timestamp.toLocaleTimeString('en-US', {
                              hour: '2-digit',
                              minute: '2-digit',
                            })}
                          </span>
                          {conv.unread > 0 && (
                            <Badge variant="primary" size="sm">
                              {conv.unread}
                            </Badge>
                          )}
                        </div>

                        {/* Item Preview */}
                        <div className="flex items-center gap-2 mt-2 p-2 bg-white/5 rounded-lg border border-white/10">
                          <img
                            src={conv.item.thumbnail}
                            alt={conv.item.name}
                            className="w-8 h-8 object-cover rounded"
                          />
                          <div className="flex-1 min-w-0">
                            <p className="text-xs font-medium text-white truncate">
                              {conv.item.name}
                            </p>
                            <p className="text-xs text-slate-400">
                              €{conv.item.price.toFixed(2)}
                            </p>
                          </div>
                        </div>
                      </div>
                    </div>
                  </motion.div>
                ))}
              </div>
            </div>

            {/* Chat Area */}
            {selectedConversation ? (
              <div className="flex-1 flex flex-col">
                {/* Chat Header */}
                <div className="p-4 border-b border-white/10 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <Avatar
                      src={selectedConversation.user.avatar}
                      alt={selectedConversation.user.name}
                      size="md"
                      status={selectedConversation.user.isOnline ? 'online' : 'offline'}
                    />
                    <div>
                      <h3 className="font-semibold text-white">
                        {selectedConversation.user.name}
                      </h3>
                      <p className="text-sm text-slate-400">
                        {selectedConversation.user.isOnline ? (
                          <span className="text-green-400">Online</span>
                        ) : (
                          'Offline'
                        )}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <Tooltip content="Call">
                      <button className="p-2 text-slate-400 hover:text-white hover:bg-white/5 rounded-lg transition-colors">
                        <Phone className="w-5 h-5" />
                      </button>
                    </Tooltip>
                    <Tooltip content="Video call">
                      <button className="p-2 text-slate-400 hover:text-white hover:bg-white/5 rounded-lg transition-colors">
                        <Video className="w-5 h-5" />
                      </button>
                    </Tooltip>
                    <Tooltip content="Info">
                      <button className="p-2 text-slate-400 hover:text-white hover:bg-white/5 rounded-lg transition-colors">
                        <Info className="w-5 h-5" />
                      </button>
                    </Tooltip>
                    <button className="p-2 text-slate-400 hover:text-white hover:bg-white/5 rounded-lg transition-colors">
                      <MoreVertical className="w-5 h-5" />
                    </button>
                  </div>
                </div>

                {/* Messages */}
                <div className="flex-1 overflow-y-auto p-4 space-y-4">
                  <AnimatePresence>
                    {messages.map((message, index) => (
                      <motion.div
                        key={message.id}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: index * 0.05 }}
                        className={`flex ${message.isOwn ? 'justify-end' : 'justify-start'}`}
                      >
                        <div className={`max-w-[70%] ${message.isOwn ? 'items-end' : 'items-start'}`}>
                          <div
                            className={`px-4 py-2 rounded-2xl ${
                              message.isOwn
                                ? 'bg-gradient-to-r from-violet-500 to-purple-600 text-white rounded-br-sm shadow-lg shadow-violet-500/30'
                                : 'bg-white/10 border border-white/10 text-white rounded-bl-sm'
                            }`}
                          >
                            <p className="text-sm">{message.text}</p>
                            {message.attachments && message.attachments.length > 0 && (
                              <div className="mt-2 space-y-2">
                                {message.attachments.map((attachment, i) => (
                                  <div key={i}>
                                    {attachment.type === 'image' ? (
                                      <img
                                        src={attachment.url}
                                        alt="Attachment"
                                        className="max-w-full rounded-lg"
                                      />
                                    ) : (
                                      <div className="flex items-center gap-2 p-2 bg-black/10 rounded-lg">
                                        <Paperclip className="w-4 h-4" />
                                        <span className="text-sm">{attachment.name}</span>
                                      </div>
                                    )}
                                  </div>
                                ))}
                              </div>
                            )}
                          </div>
                          <div
                            className={`flex items-center gap-2 mt-1 text-xs text-slate-500 ${
                              message.isOwn ? 'justify-end' : 'justify-start'
                            }`}
                          >
                            <span>
                              {message.timestamp.toLocaleTimeString('en-US', {
                                hour: '2-digit',
                                minute: '2-digit',
                              })}
                            </span>
                            {message.isOwn && getMessageStatusIcon(message.status)}
                          </div>
                        </div>
                      </motion.div>
                    ))}
                  </AnimatePresence>
                  <div ref={messagesEndRef} />
                </div>

                {/* AI Suggestions */}
                <AnimatePresence>
                  {showAISuggestions && (
                    <motion.div
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: 20 }}
                      className="px-4 py-3 bg-gradient-to-br from-violet-500/10 to-purple-500/10 border-t border-violet-500/30"
                    >
                      <div className="flex items-center gap-2 mb-3">
                        <Sparkles className="w-4 h-4 text-violet-400" />
                        <span className="text-sm font-medium text-white">
                          AI Suggested Replies
                        </span>
                        <button
                          onClick={() => setShowAISuggestions(false)}
                          className="ml-auto text-xs text-slate-400 hover:text-white"
                        >
                          Hide
                        </button>
                      </div>
                      <div className="space-y-2">
                        {aiSuggestions.map((suggestion) => (
                          <motion.button
                            key={suggestion.id}
                            whileHover={{ scale: 1.02 }}
                            whileTap={{ scale: 0.98 }}
                            onClick={() => handleUseSuggestion(suggestion)}
                            className="w-full text-left p-3 bg-white/10 border border-white/10 rounded-xl hover:bg-white/15 hover:shadow-lg hover:shadow-violet-500/20 transition-all group"
                          >
                            <div className="flex items-start gap-2">
                              <Sparkles className="w-4 h-4 text-violet-400 mt-0.5 flex-shrink-0" />
                              <div className="flex-1 min-w-0">
                                <p className="text-sm text-white">
                                  {suggestion.text}
                                </p>
                                <div className="flex items-center gap-2 mt-1">
                                  <Badge variant="info" size="sm">
                                    {suggestion.tone}
                                  </Badge>
                                  <span className="text-xs text-slate-400">{suggestion.context}</span>
                                </div>
                              </div>
                            </div>
                          </motion.button>
                        ))}
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>

                {/* Message Input */}
                <div className="p-4 border-t border-white/10">
                  <div className="flex items-end gap-2">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <Tooltip content="Attach image">
                          <button className="p-2 text-slate-400 hover:text-white hover:bg-white/5 rounded-lg transition-colors">
                            <ImageIcon className="w-5 h-5" />
                          </button>
                        </Tooltip>
                        <Tooltip content="Attach file">
                          <button className="p-2 text-slate-400 hover:text-white hover:bg-white/5 rounded-lg transition-colors">
                            <Paperclip className="w-5 h-5" />
                          </button>
                        </Tooltip>
                        <Tooltip content="Emoji">
                          <button className="p-2 text-slate-400 hover:text-white hover:bg-white/5 rounded-lg transition-colors">
                            <Smile className="w-5 h-5" />
                          </button>
                        </Tooltip>
                        {!showAISuggestions && (
                          <button
                            onClick={() => setShowAISuggestions(true)}
                            className="p-2 text-violet-400 hover:bg-violet-500/10 rounded-lg transition-colors"
                          >
                            <Sparkles className="w-5 h-5" />
                          </button>
                        )}
                      </div>
                      <textarea
                        value={messageInput}
                        onChange={(e) => setMessageInput(e.target.value)}
                        onKeyPress={(e) => {
                          if (e.key === 'Enter' && !e.shiftKey) {
                            e.preventDefault();
                            handleSendMessage();
                          }
                        }}
                        placeholder="Type a message..."
                        rows={2}
                        className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder-slate-400 resize-none focus:outline-none focus:border-violet-500/50 focus:bg-white/10 transition-all"
                      />
                    </div>

                    <Button
                      onClick={handleSendMessage}
                      disabled={!messageInput.trim()}
                      icon={Send}
                      size="lg"
                    />
                  </div>
                </div>
              </div>
            ) : (
              <div className="flex-1 flex items-center justify-center p-8">
                <EmptyState
                  icon={MessageSquare}
                  title="Select a conversation"
                  description="Choose a conversation from the list to start messaging"
                />
              </div>
            )}
          </GlassCard>
        </motion.div>
      </div>
    </div>
  );
}
