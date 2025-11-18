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
  MessageCircle,
  Smile,
  X,
  ThumbsUp,
  Package
} from 'lucide-react';
import { cn, formatPrice } from '@/lib/utils';
import Avatar from '@/components/common/Avatar';

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
  item: {
    name: string;
    price: number;
    thumbnail?: string;
  };
}

interface AISuggestion {
  id: string;
  text: string;
  tone: 'friendly' | 'professional' | 'concise';
}

// Mock data
const mockConversations: Conversation[] = [
  {
    id: '1',
    user: { name: 'Marie Laurent', avatar: '', isOnline: true },
    lastMessage: 'Bonjour, le prix est-il négociable ?',
    timestamp: new Date(Date.now() - 3600000),
    unread: 2,
    item: { name: 'Jean Levi\'s 501', price: 45, thumbnail: '' }
  },
  {
    id: '2',
    user: { name: 'Thomas Dubois', avatar: '', isOnline: false },
    lastMessage: 'Merci pour la réponse rapide !',
    timestamp: new Date(Date.now() - 7200000),
    unread: 0,
    item: { name: 'Nike Air Max', price: 89, thumbnail: '' }
  },
  {
    id: '3',
    user: { name: 'Sophie Martin', avatar: '', isOnline: true },
    lastMessage: 'L\'article est-il toujours disponible ?',
    timestamp: new Date(Date.now() - 86400000),
    unread: 1,
    item: { name: 'Robe Zara', price: 28, thumbnail: '' }
  }
];

const mockMessages: Message[] = [
  {
    id: '1',
    text: 'Bonjour ! L\'article m\'intéresse beaucoup.',
    timestamp: new Date(Date.now() - 7200000),
    isOwn: false
  },
  {
    id: '2',
    text: 'Bonjour ! Oui l\'article est toujours disponible.',
    timestamp: new Date(Date.now() - 7100000),
    isOwn: true,
    status: 'read'
  },
  {
    id: '3',
    text: 'Le prix est-il négociable ?',
    timestamp: new Date(Date.now() - 3600000),
    isOwn: false
  }
];

const mockAISuggestions: AISuggestion[] = [
  {
    id: '1',
    text: 'Oui, je peux faire 40€ au lieu de 45€',
    tone: 'friendly'
  },
  {
    id: '2',
    text: 'Le prix est ferme mais je peux offrir la livraison',
    tone: 'professional'
  },
  {
    id: '3',
    text: 'Désolé, le prix est fixe',
    tone: 'concise'
  }
];

export default function Messages() {
  const [conversations, setConversations] = useState<Conversation[]>(mockConversations);
  const [selectedConversation, setSelectedConversation] = useState<Conversation | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [aiSuggestions] = useState<AISuggestion[]>(mockAISuggestions);
  const [messageInput, setMessageInput] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [showAISuggestions, setShowAISuggestions] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (selectedConversation) {
      setMessages(mockMessages);
    }
  }, [selectedConversation]);

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

  const filteredConversations = conversations.filter(conv =>
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
        return <CheckCheck className="w-4 h-4 text-blue-500" />;
      default:
        return null;
    }
  };

  const formatTime = (date: Date) => {
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const hours = Math.floor(diff / 3600000);

    if (hours < 1) return 'À l\'instant';
    if (hours < 24) return `Il y a ${hours}h`;
    const days = Math.floor(hours / 24);
    if (days === 1) return 'Hier';
    return `Il y a ${days}j`;
  };

  return (
    <div className="min-h-screen bg-gray-50 -m-8">
      {/* Header avec gradient */}
      <div className="bg-gradient-to-br from-brand-600 via-purple-600 to-brand-700 text-white">
        <div className="max-w-7xl mx-auto px-6 py-12">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
          >
            <div className="flex items-center gap-3 mb-3">
              <motion.div
                initial={{ scale: 0, rotate: -180 }}
                animate={{ scale: 1, rotate: 0 }}
                transition={{ type: 'spring', delay: 0.2 }}
                className="w-14 h-14 bg-white/20 rounded-2xl backdrop-blur-sm flex items-center justify-center"
              >
                <MessageCircle className="w-8 h-8" />
              </motion.div>
              <h1 className="text-4xl font-bold">Messages</h1>
            </div>
            <p className="text-brand-100 text-lg">
              Communiquez avec vos acheteurs en temps réel
            </p>
          </motion.div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 -mt-8 pb-12">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="bg-white rounded-3xl border border-gray-200 shadow-sm overflow-hidden"
          style={{ height: 'calc(100vh - 250px)' }}
        >
          <div className="h-full flex">
            {/* Conversations Sidebar */}
            <div className="w-96 border-r border-gray-200 flex flex-col">
              {/* Search */}
              <div className="p-6 border-b border-gray-200">
                <div className="relative">
                  <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                  <input
                    type="text"
                    placeholder="Rechercher une conversation..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="w-full pl-12 pr-4 py-3 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:ring-2 focus:ring-brand-500 focus:border-transparent transition-all"
                  />
                </div>
              </div>

              {/* Conversations List */}
              <div className="flex-1 overflow-y-auto">
                {filteredConversations.length === 0 ? (
                  <div className="flex flex-col items-center justify-center h-full p-8 text-center">
                    <div className="w-20 h-20 bg-gray-100 rounded-full flex items-center justify-center mb-4">
                      <MessageCircle className="w-10 h-10 text-gray-400" />
                    </div>
                    <h3 className="font-semibold text-gray-900 mb-2 text-lg">
                      Aucune conversation
                    </h3>
                    <p className="text-sm text-gray-600">
                      Vos conversations apparaîtront ici
                    </p>
                  </div>
                ) : (
                  filteredConversations.map((conv, index) => (
                    <motion.div
                      key={conv.id}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: index * 0.05 }}
                      whileHover={{ backgroundColor: 'rgba(147, 51, 234, 0.05)' }}
                      onClick={() => setSelectedConversation(conv)}
                      className={cn(
                        "p-4 cursor-pointer border-b border-gray-100 transition-all",
                        selectedConversation?.id === conv.id && "bg-brand-50 border-l-4 border-l-brand-600"
                      )}
                    >
                      <div className="flex items-start gap-3">
                        {/* Avatar */}
                        <div className="relative">
                          <div className="w-14 h-14 bg-gradient-to-br from-brand-500 to-purple-600 rounded-full flex items-center justify-center text-white font-bold text-lg">
                            {conv.user.name.charAt(0)}
                          </div>
                          {conv.user.isOnline && (
                            <div className="absolute bottom-0 right-0 w-4 h-4 bg-success-500 border-2 border-white rounded-full" />
                          )}
                        </div>

                        <div className="flex-1 min-w-0">
                          <div className="flex items-center justify-between mb-1">
                            <span className="font-semibold text-gray-900 truncate">
                              {conv.user.name}
                            </span>
                            <span className="text-xs text-gray-500">
                              {formatTime(conv.timestamp)}
                            </span>
                          </div>

                          <p className="text-sm text-gray-600 truncate mb-2">
                            {conv.lastMessage}
                          </p>

                          {/* Item Info */}
                          <div className="flex items-center gap-2 p-2 bg-gray-50 rounded-lg">
                            <div className="w-8 h-8 bg-gradient-to-br from-gray-200 to-gray-300 rounded flex items-center justify-center">
                              <Package className="w-4 h-4 text-gray-600" />
                            </div>
                            <div className="flex-1 min-w-0">
                              <p className="text-xs font-medium text-gray-900 truncate">
                                {conv.item.name}
                              </p>
                              <p className="text-xs text-brand-600 font-semibold">
                                {formatPrice(conv.item.price)}
                              </p>
                            </div>
                            {conv.unread > 0 && (
                              <div className="w-6 h-6 bg-brand-600 text-white text-xs font-bold rounded-full flex items-center justify-center flex-shrink-0">
                                {conv.unread}
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    </motion.div>
                  ))
                )}
              </div>
            </div>

            {/* Chat Area */}
            {selectedConversation ? (
              <div className="flex-1 flex flex-col">
                {/* Chat Header */}
                <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between bg-gray-50">
                  <div className="flex items-center gap-3">
                    <div className="relative">
                      <div className="w-12 h-12 bg-gradient-to-br from-brand-500 to-purple-600 rounded-full flex items-center justify-center text-white font-bold">
                        {selectedConversation.user.name.charAt(0)}
                      </div>
                      {selectedConversation.user.isOnline && (
                        <div className="absolute bottom-0 right-0 w-3 h-3 bg-success-500 border-2 border-white rounded-full" />
                      )}
                    </div>
                    <div>
                      <h3 className="font-semibold text-gray-900">
                        {selectedConversation.user.name}
                      </h3>
                      <p className="text-sm text-gray-600">
                        {selectedConversation.user.isOnline ? 'En ligne' : 'Hors ligne'}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <div className="px-4 py-2 bg-white rounded-xl border border-gray-200">
                      <p className="text-xs text-gray-600">Article</p>
                      <p className="font-semibold text-gray-900 text-sm">{selectedConversation.item.name}</p>
                      <p className="text-xs text-brand-600 font-bold">{formatPrice(selectedConversation.item.price)}</p>
                    </div>
                    <button className="p-2 text-gray-600 hover:text-gray-900 hover:bg-white rounded-lg transition-colors">
                      <MoreVertical className="w-5 h-5" />
                    </button>
                  </div>
                </div>

                {/* Messages */}
                <div className="flex-1 overflow-y-auto p-6 space-y-4 bg-gray-50">
                  <AnimatePresence>
                    {messages.map((message, index) => (
                      <motion.div
                        key={message.id}
                        initial={{ opacity: 0, y: 10, scale: 0.95 }}
                        animate={{ opacity: 1, y: 0, scale: 1 }}
                        transition={{ delay: index * 0.05 }}
                        className={cn(
                          "flex",
                          message.isOwn ? 'justify-end' : 'justify-start'
                        )}
                      >
                        <div className={cn(
                          "max-w-[70%]",
                          message.isOwn ? 'items-end' : 'items-start'
                        )}>
                          <motion.div
                            whileHover={{ scale: 1.02 }}
                            className={cn(
                              "px-4 py-3 rounded-2xl shadow-sm",
                              message.isOwn
                                ? 'bg-gradient-to-br from-brand-600 to-purple-600 text-white rounded-br-md'
                                : 'bg-white text-gray-900 border border-gray-200 rounded-bl-md'
                            )}
                          >
                            <p className="text-sm leading-relaxed">{message.text}</p>
                          </motion.div>

                          <div className={cn(
                            "flex items-center gap-1 mt-1 px-2",
                            message.isOwn ? 'justify-end' : 'justify-start'
                          )}>
                            <span className="text-xs text-gray-500">
                              {message.timestamp.toLocaleTimeString('fr-FR', {
                                hour: '2-digit',
                                minute: '2-digit',
                              })}
                            </span>
                            {message.isOwn && (
                              <span className="text-gray-500">
                                {getMessageStatusIcon(message.status)}
                              </span>
                            )}
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
                      className="px-6 py-4 bg-gradient-to-r from-brand-50 to-purple-50 border-t border-brand-200"
                    >
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center gap-2">
                          <Sparkles className="w-5 h-5 text-brand-600" />
                          <span className="text-sm font-semibold text-gray-900">
                            Suggestions IA
                          </span>
                        </div>
                        <button
                          onClick={() => setShowAISuggestions(false)}
                          className="p-1 text-gray-500 hover:text-gray-700 rounded-lg hover:bg-white transition-colors"
                        >
                          <X className="w-4 h-4" />
                        </button>
                      </div>

                      <div className="grid gap-2">
                        {aiSuggestions.map((suggestion, index) => (
                          <motion.button
                            key={suggestion.id}
                            initial={{ opacity: 0, x: -10 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: index * 0.1 }}
                            whileHover={{ scale: 1.02, x: 4 }}
                            whileTap={{ scale: 0.98 }}
                            onClick={() => handleUseSuggestion(suggestion)}
                            className="text-left p-3 bg-white rounded-xl hover:shadow-md transition-all border border-gray-200 group"
                          >
                            <div className="flex items-center gap-3">
                              <div className="w-8 h-8 bg-gradient-to-br from-brand-500 to-purple-600 rounded-lg flex items-center justify-center flex-shrink-0">
                                <Sparkles className="w-4 h-4 text-white" />
                              </div>
                              <div className="flex-1">
                                <p className="text-sm text-gray-900 font-medium group-hover:text-brand-600 transition-colors">
                                  {suggestion.text}
                                </p>
                                <span className="text-xs text-gray-500 capitalize">{suggestion.tone}</span>
                              </div>
                            </div>
                          </motion.button>
                        ))}
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>

                {/* Message Input */}
                <div className="p-6 border-t border-gray-200 bg-white">
                  <div className="flex items-end gap-3">
                    <div className="flex gap-2">
                      <motion.button
                        whileHover={{ scale: 1.1 }}
                        whileTap={{ scale: 0.9 }}
                        className="p-3 text-gray-600 hover:text-brand-600 hover:bg-brand-50 rounded-xl transition-colors"
                      >
                        <ImageIcon className="w-5 h-5" />
                      </motion.button>
                      <motion.button
                        whileHover={{ scale: 1.1 }}
                        whileTap={{ scale: 0.9 }}
                        onClick={() => setShowAISuggestions(!showAISuggestions)}
                        className={cn(
                          "p-3 rounded-xl transition-colors",
                          showAISuggestions
                            ? "text-brand-600 bg-brand-50"
                            : "text-gray-600 hover:text-brand-600 hover:bg-brand-50"
                        )}
                      >
                        <Sparkles className="w-5 h-5" />
                      </motion.button>
                    </div>

                    <div className="flex-1">
                      <textarea
                        value={messageInput}
                        onChange={(e) => setMessageInput(e.target.value)}
                        onKeyPress={(e) => {
                          if (e.key === 'Enter' && !e.shiftKey) {
                            e.preventDefault();
                            handleSendMessage();
                          }
                        }}
                        placeholder="Écrivez votre message..."
                        rows={1}
                        className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl resize-none focus:ring-2 focus:ring-brand-500 focus:border-transparent transition-all"
                      />
                    </div>

                    <motion.button
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      onClick={handleSendMessage}
                      disabled={!messageInput.trim()}
                      className={cn(
                        "p-4 rounded-xl transition-all font-semibold shadow-lg",
                        messageInput.trim()
                          ? "bg-gradient-to-r from-brand-600 to-purple-600 text-white hover:shadow-xl"
                          : "bg-gray-200 text-gray-400 cursor-not-allowed shadow-none"
                      )}
                    >
                      <Send className="w-5 h-5" />
                    </motion.button>
                  </div>
                </div>
              </div>
            ) : (
              <div className="flex-1 flex items-center justify-center bg-gray-50">
                <div className="text-center">
                  <motion.div
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    transition={{ type: 'spring', delay: 0.2 }}
                    className="w-24 h-24 bg-gradient-to-br from-brand-500 to-purple-600 rounded-3xl flex items-center justify-center mx-auto mb-6"
                  >
                    <MessageCircle className="w-12 h-12 text-white" />
                  </motion.div>
                  <h3 className="text-2xl font-bold text-gray-900 mb-2">
                    Sélectionnez une conversation
                  </h3>
                  <p className="text-gray-600">
                    Choisissez une conversation pour commencer à discuter
                  </p>
                </div>
              </div>
            )}
          </div>
        </motion.div>
      </div>
    </div>
  );
}
