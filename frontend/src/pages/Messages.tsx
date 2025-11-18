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
} from 'lucide-react';
import { Badge } from '../components/common/Badge';
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

// Real conversations will be fetched from API
// TODO: Implement API integration for messages

export default function Messages() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [selectedConversation, setSelectedConversation] = useState<Conversation | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [aiSuggestions, setAiSuggestions] = useState<AISuggestion[]>([]);
  const [messageInput, setMessageInput] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [showAISuggestions, setShowAISuggestions] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // TODO: Fetch conversations from API
  useEffect(() => {
    // fetchConversations().then(setConversations);
  }, []);

  // TODO: Fetch AI suggestions based on context
  useEffect(() => {
    if (selectedConversation && showAISuggestions) {
      // fetchAISuggestions(selectedConversation.id).then(setAiSuggestions);
    }
  }, [selectedConversation, showAISuggestions]);

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
        return <CheckCheck className="w-4 h-4 text-primary-500" />;
      default:
        return <Clock className="w-4 h-4" />;
    }
  };

  return (
    <div className="max-w-7xl mx-auto h-[calc(100vh-120px)]">
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="card h-full flex overflow-hidden"
      >
        {/* Conversations Sidebar */}
        <div className="w-80 border-r border-gray-200 dark:border-gray-700 flex flex-col">
          {/* Sidebar Header */}
          <div className="p-4 border-b border-gray-200 dark:border-gray-700">
            <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
              Messages
            </h2>

            {/* Search */}
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search conversations..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all"
              />
            </div>

            {/* Filters */}
            <div className="flex items-center gap-2 mt-3">
              <button className="px-3 py-1.5 text-xs font-medium bg-primary-50 dark:bg-primary-900/20 text-primary-700 dark:text-primary-400 rounded-lg hover:bg-primary-100 dark:hover:bg-primary-900/40 transition-colors">
                All
              </button>
              <button className="px-3 py-1.5 text-xs font-medium text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors">
                Unread
              </button>
              <button className="px-3 py-1.5 text-xs font-medium text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors">
                Pinned
              </button>
            </div>
          </div>

          {/* Conversations List */}
          <div className="flex-1 overflow-y-auto">
            {filteredConversations.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full p-8 text-center">
                <div className="w-16 h-16 bg-gray-100 dark:bg-gray-800 rounded-full flex items-center justify-center mb-4">
                  <Search className="w-8 h-8 text-gray-400" />
                </div>
                <h3 className="font-semibold text-gray-900 dark:text-white mb-2">
                  No conversations yet
                </h3>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Your conversations with buyers will appear here
                </p>
              </div>
            ) : (
              filteredConversations.map((conv) => (
              <motion.div
                key={conv.id}
                whileHover={{ backgroundColor: 'rgba(0,0,0,0.02)' }}
                onClick={() => setSelectedConversation(conv)}
                className={`p-4 cursor-pointer border-b border-gray-200 dark:border-gray-700 transition-colors ${
                  selectedConversation?.id === conv.id
                    ? 'bg-primary-50 dark:bg-primary-900/20'
                    : 'hover:bg-gray-50 dark:hover:bg-gray-800'
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
                      <span className="font-semibold text-gray-900 dark:text-white text-sm truncate">
                        {conv.user.name}
                      </span>
                      {conv.isPinned && (
                        <Star className="w-3 h-3 text-warning-500 fill-warning-500" />
                      )}
                    </div>

                    <p className="text-sm text-gray-600 dark:text-gray-400 truncate mb-1">
                      {conv.lastMessage}
                    </p>

                    <div className="flex items-center justify-between">
                      <span className="text-xs text-gray-500">
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
                    <div className="flex items-center gap-2 mt-2 p-2 bg-gray-50 dark:bg-gray-800 rounded-lg">
                      <img
                        src={conv.item.thumbnail}
                        alt={conv.item.name}
                        className="w-8 h-8 object-cover rounded"
                      />
                      <div className="flex-1 min-w-0">
                        <p className="text-xs font-medium text-gray-900 dark:text-white truncate">
                          {conv.item.name}
                        </p>
                        <p className="text-xs text-gray-600 dark:text-gray-400">
                          €{conv.item.price.toFixed(2)}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              </motion.div>
            )))}
          </div>
        </div>

        {/* Chat Area */}
        {selectedConversation ? (
          <div className="flex-1 flex flex-col">
            {/* Chat Header */}
            <div className="p-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Avatar
                  src={selectedConversation.user.avatar}
                  alt={selectedConversation.user.name}
                  size="md"
                  status={selectedConversation.user.isOnline ? 'online' : 'offline'}
                />
                <div>
                  <h3 className="font-semibold text-gray-900 dark:text-white">
                    {selectedConversation.user.name}
                  </h3>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    {selectedConversation.user.isOnline ? 'Online' : 'Offline'}
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <Tooltip content="Call">
                  <button className="p-2 text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors">
                    <Phone className="w-5 h-5" />
                  </button>
                </Tooltip>
                <Tooltip content="Video call">
                  <button className="p-2 text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors">
                    <Video className="w-5 h-5" />
                  </button>
                </Tooltip>
                <Tooltip content="Info">
                  <button className="p-2 text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors">
                    <Info className="w-5 h-5" />
                  </button>
                </Tooltip>
                <button className="p-2 text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors">
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
                            ? 'bg-primary-500 text-white rounded-br-sm'
                            : 'bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-white rounded-bl-sm'
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
                                  <div className="flex items-center gap-2 p-2 bg-black/10 dark:bg-white/10 rounded-lg">
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
                        className={`flex items-center gap-2 mt-1 text-xs text-gray-500 ${
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
                  className="px-4 py-3 bg-gradient-to-br from-primary-50 to-purple-50 dark:from-primary-900/20 dark:to-purple-900/20 border-t border-primary-200 dark:border-primary-800"
                >
                  <div className="flex items-center gap-2 mb-3">
                    <Sparkles className="w-4 h-4 text-primary-600 dark:text-primary-400" />
                    <span className="text-sm font-medium text-gray-900 dark:text-white">
                      AI Suggested Replies
                    </span>
                    <button
                      onClick={() => setShowAISuggestions(false)}
                      className="ml-auto text-xs text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
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
                        className="w-full text-left p-3 bg-white dark:bg-gray-800 rounded-lg hover:shadow-md transition-all group"
                      >
                        <div className="flex items-start gap-2">
                          <Sparkles className="w-4 h-4 text-primary-500 mt-0.5 flex-shrink-0" />
                          <div className="flex-1 min-w-0">
                            <p className="text-sm text-gray-900 dark:text-white">
                              {suggestion.text}
                            </p>
                            <div className="flex items-center gap-2 mt-1">
                              <Badge variant="default" size="sm">
                                {suggestion.tone}
                              </Badge>
                              <span className="text-xs text-gray-500">{suggestion.context}</span>
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
            <div className="p-4 border-t border-gray-200 dark:border-gray-700">
              <div className="flex items-end gap-2">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <Tooltip content="Attach image">
                      <button className="p-2 text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors">
                        <ImageIcon className="w-5 h-5" />
                      </button>
                    </Tooltip>
                    <Tooltip content="Attach file">
                      <button className="p-2 text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors">
                        <Paperclip className="w-5 h-5" />
                      </button>
                    </Tooltip>
                    <Tooltip content="Emoji">
                      <button className="p-2 text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors">
                        <Smile className="w-5 h-5" />
                      </button>
                    </Tooltip>
                    {!showAISuggestions && (
                      <button
                        onClick={() => setShowAISuggestions(true)}
                        className="p-2 text-primary-600 dark:text-primary-400 hover:bg-primary-50 dark:hover:bg-primary-900/20 rounded-lg transition-colors"
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
                    className="w-full px-4 py-3 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg resize-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all"
                  />
                </div>

                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={handleSendMessage}
                  disabled={!messageInput.trim()}
                  className="p-4 bg-primary-500 hover:bg-primary-600 text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <Send className="w-5 h-5" />
                </motion.button>
              </div>
            </div>
          </div>
        ) : (
          <div className="flex-1 flex items-center justify-center text-center p-8">
            <div>
              <div className="w-20 h-20 bg-gray-100 dark:bg-gray-800 rounded-full flex items-center justify-center mx-auto mb-4">
                <Search className="w-10 h-10 text-gray-400" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                Select a conversation
              </h3>
              <p className="text-gray-600 dark:text-gray-400">
                Choose a conversation from the list to start messaging
              </p>
            </div>
          </div>
        )}
      </motion.div>
    </div>
  );
}
