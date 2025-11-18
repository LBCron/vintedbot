import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  Search,
  Send,
  MoreVertical,
  Smile,
  Paperclip,
  MessageSquare
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface Conversation {
  id: string;
  buyer: string;
  item: string;
  lastMessage: string;
  time: string;
  unread: number;
  avatar?: string;
}

interface Message {
  id: string;
  text: string;
  sender: 'me' | 'buyer';
  timestamp: Date;
}

export default function Messages() {
  const [selectedConversation, setSelectedConversation] = useState<Conversation | null>(null);
  const [messageText, setMessageText] = useState('');
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  // Fetch conversations from API
  useEffect(() => {
    const fetchConversations = async () => {
      try {
        setIsLoading(true);
        // TODO: Remplacer par vraie API call
        // const response = await fetch('/api/conversations');
        // const data = await response.json();
        // setConversations(data);

        // Pour l'instant, état vide
        setConversations([]);
      } catch (error) {
        console.error('Error fetching conversations:', error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchConversations();
  }, []);

  // Fetch messages for selected conversation
  useEffect(() => {
    if (!selectedConversation) return;

    const fetchMessages = async () => {
      try {
        // TODO: Remplacer par vraie API call
        // const response = await fetch(`/api/conversations/${selectedConversation.id}/messages`);
        // const data = await response.json();
        // setMessages(data);

        // Pour l'instant, état vide
        setMessages([]);
      } catch (error) {
        console.error('Error fetching messages:', error);
      }
    };

    fetchMessages();
  }, [selectedConversation]);

  const handleSendMessage = async () => {
    if (!messageText.trim() || !selectedConversation) return;

    try {
      // TODO: Remplacer par vraie API call
      // await fetch(`/api/conversations/${selectedConversation.id}/messages`, {
      //   method: 'POST',
      //   body: JSON.stringify({ text: messageText })
      // });

      // Ajouter le message localement
      setMessages([...messages, {
        id: Date.now().toString(),
        text: messageText,
        sender: 'me',
        timestamp: new Date()
      }]);
      setMessageText('');
    } catch (error) {
      console.error('Error sending message:', error);
    }
  };

  // Loading state
  if (isLoading) {
    return (
      <div className="h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-brand-200 border-t-brand-600 rounded-full animate-spin mx-auto mb-4" />
          <p className="text-gray-600">Chargement des conversations...</p>
        </div>
      </div>
    );
  }

  // Empty state - PAS DE CONVERSATIONS
  if (conversations.length === 0) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-6">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="text-center max-w-md"
        >
          <div className="w-32 h-32 bg-gradient-to-br from-brand-100 to-brand-200 rounded-full flex items-center justify-center mx-auto mb-6">
            <MessageSquare className="w-16 h-16 text-brand-600" />
          </div>
          <h2 className="text-3xl font-bold text-gray-900 mb-4">
            Aucun message
          </h2>
          <p className="text-gray-600 text-lg mb-8">
            Vos conversations avec les acheteurs apparaîtront ici une fois que vous aurez des messages sur Vinted
          </p>
          <div className="bg-brand-50 border border-brand-200 rounded-xl p-6">
            <p className="text-sm text-brand-700 font-medium">
              💡 Les messages Vinted seront automatiquement synchronisés quand vous connecterez votre compte
            </p>
          </div>
        </motion.div>
      </div>
    );
  }

  // Interface normale avec conversations
  return (
    <div className="h-screen bg-gray-50 flex">
      {/* Conversations List */}
      <div className="w-96 bg-white border-r border-gray-200 flex flex-col">
        {/* Search */}
        <div className="p-4 border-b border-gray-200">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              placeholder="Rechercher une conversation..."
              className="w-full pl-10 pr-4 py-3 bg-gray-50 rounded-xl border-0 focus:ring-2 focus:ring-brand-500"
            />
          </div>
        </div>

        {/* Conversation List */}
        <div className="flex-1 overflow-y-auto">
          {conversations.map((conv) => (
            <ConversationItem
              key={conv.id}
              conversation={conv}
              isSelected={selectedConversation?.id === conv.id}
              onClick={() => setSelectedConversation(conv)}
            />
          ))}
        </div>
      </div>

      {/* Messages Area */}
      <div className="flex-1 flex flex-col">
        {selectedConversation ? (
          <>
            {/* Header */}
            <div className="bg-white border-b border-gray-200 p-4 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 bg-gradient-to-br from-brand-500 to-purple-500 rounded-full flex items-center justify-center text-white font-bold">
                  {selectedConversation.buyer[0].toUpperCase()}
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900">{selectedConversation.buyer}</h3>
                  <p className="text-sm text-gray-500">{selectedConversation.item}</p>
                </div>
              </div>
              <button className="p-2 hover:bg-gray-100 rounded-lg transition-colors">
                <MoreVertical className="w-5 h-5 text-gray-600" />
              </button>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-6 space-y-4">
              {messages.length === 0 ? (
                <div className="text-center py-12">
                  <p className="text-gray-500">Aucun message dans cette conversation</p>
                </div>
              ) : (
                messages.map((msg) => (
                  <MessageBubble key={msg.id} message={msg} />
                ))
              )}
            </div>

            {/* Input */}
            <div className="bg-white border-t border-gray-200 p-4">
              <div className="flex items-end gap-3">
                <button className="p-2 hover:bg-gray-100 rounded-lg transition-colors">
                  <Paperclip className="w-5 h-5 text-gray-600" />
                </button>
                <button className="p-2 hover:bg-gray-100 rounded-lg transition-colors">
                  <Smile className="w-5 h-5 text-gray-600" />
                </button>
                <textarea
                  value={messageText}
                  onChange={(e) => setMessageText(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      handleSendMessage();
                    }
                  }}
                  placeholder="Écrivez votre message..."
                  className="flex-1 resize-none px-4 py-3 bg-gray-50 rounded-xl border-0 focus:ring-2 focus:ring-brand-500 max-h-32"
                  rows={1}
                />
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  disabled={!messageText.trim()}
                  onClick={handleSendMessage}
                  className="bg-brand-600 text-white p-3 rounded-xl hover:bg-brand-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                >
                  <Send className="w-5 h-5" />
                </motion.button>
              </div>
            </div>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center">
              <div className="w-24 h-24 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <MessageSquare className="w-12 h-12 text-gray-400" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                Sélectionnez une conversation
              </h3>
              <p className="text-gray-500">
                Choisissez une conversation pour commencer à discuter
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function ConversationItem({ conversation, isSelected, onClick }: {
  conversation: Conversation;
  isSelected: boolean;
  onClick: () => void;
}) {
  return (
    <motion.div
      whileHover={{ x: 4 }}
      onClick={onClick}
      className={cn(
        "p-4 border-b border-gray-100 cursor-pointer transition-colors",
        isSelected ? "bg-brand-50 border-l-4 border-l-brand-600" : "hover:bg-gray-50"
      )}
    >
      <div className="flex items-start gap-3">
        <div className="w-12 h-12 bg-gradient-to-br from-brand-500 to-purple-500 rounded-full flex items-center justify-center text-white font-bold flex-shrink-0">
          {conversation.buyer[0].toUpperCase()}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between mb-1">
            <h4 className="font-semibold text-gray-900 truncate">{conversation.buyer}</h4>
            <span className="text-xs text-gray-500">{conversation.time}</span>
          </div>
          <p className="text-sm text-gray-600 truncate mb-1">{conversation.item}</p>
          <p className="text-sm text-gray-500 truncate">{conversation.lastMessage}</p>
        </div>
        {conversation.unread > 0 && (
          <div className="w-6 h-6 bg-brand-600 text-white rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0">
            {conversation.unread}
          </div>
        )}
      </div>
    </motion.div>
  );
}

function MessageBubble({ message }: { message: Message }) {
  const isMe = message.sender === 'me';

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={cn(
        "flex",
        isMe ? "justify-end" : "justify-start"
      )}
    >
      <div className={cn(
        "max-w-[70%] rounded-2xl px-4 py-3",
        isMe
          ? "bg-brand-600 text-white"
          : "bg-gray-100 text-gray-900"
      )}>
        <p className="text-sm leading-relaxed">{message.text}</p>
        <p className={cn(
          "text-xs mt-1",
          isMe ? "text-brand-100" : "text-gray-500"
        )}>
          {message.timestamp.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })}
        </p>
      </div>
    </motion.div>
  );
}
