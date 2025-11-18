import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Bell,
  X,
  Check,
  DollarSign,
  MessageSquare,
  TrendingUp,
  AlertCircle,
  CheckCircle2
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { formatDate } from '@/lib/utils';

interface Notification {
  id: string;
  type: 'sale' | 'message' | 'system' | 'success';
  title: string;
  message: string;
  time: Date;
  read: boolean;
  actionUrl?: string;
}

export default function NotificationCenter() {
  const [isOpen, setIsOpen] = useState(false);
  const [notifications, setNotifications] = useState<Notification[]>([]);

  useEffect(() => {
    // TODO: Fetch notifications from API
    // Pour l'instant, état vide
    setNotifications([]);
  }, []);

  const unreadCount = notifications.filter(n => !n.read).length;

  const markAsRead = (id: string) => {
    setNotifications(notifications.map(n =>
      n.id === id ? { ...n, read: true } : n
    ));
  };

  const markAllAsRead = () => {
    setNotifications(notifications.map(n => ({ ...n, read: true })));
  };

  const clearAll = () => {
    setNotifications([]);
  };

  const getIcon = (type: string) => {
    switch (type) {
      case 'sale':
        return <DollarSign className="w-5 h-5 text-success-600" />;
      case 'message':
        return <MessageSquare className="w-5 h-5 text-blue-600" />;
      case 'system':
        return <AlertCircle className="w-5 h-5 text-orange-600" />;
      case 'success':
        return <CheckCircle2 className="w-5 h-5 text-success-600" />;
      default:
        return <Bell className="w-5 h-5 text-gray-600" />;
    }
  };

  return (
    <>
      {/* Bell Icon */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="relative p-2 hover:bg-gray-100 rounded-xl transition-colors"
      >
        <Bell className="w-6 h-6 text-gray-600" />
        {unreadCount > 0 && (
          <motion.span
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            className="absolute -top-1 -right-1 w-5 h-5 bg-error-600 text-white text-xs font-bold rounded-full flex items-center justify-center"
          >
            {unreadCount > 9 ? '9+' : unreadCount}
          </motion.span>
        )}
      </button>

      {/* Dropdown */}
      <AnimatePresence>
        {isOpen && (
          <>
            {/* Backdrop */}
            <div
              onClick={() => setIsOpen(false)}
              className="fixed inset-0 z-40"
            />

            {/* Panel */}
            <motion.div
              initial={{ opacity: 0, y: -10, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -10, scale: 0.95 }}
              className="absolute right-0 top-full mt-2 w-96 bg-white rounded-2xl shadow-2xl border border-gray-200 z-50"
            >
              {/* Header */}
              <div className="p-4 border-b border-gray-200 flex items-center justify-between">
                <div>
                  <h3 className="font-semibold text-gray-900">Notifications</h3>
                  {unreadCount > 0 && (
                    <p className="text-sm text-gray-600">{unreadCount} non lue(s)</p>
                  )}
                </div>
                <div className="flex items-center gap-2">
                  {unreadCount > 0 && (
                    <button
                      onClick={markAllAsRead}
                      className="text-sm text-brand-600 hover:text-brand-700 font-medium"
                    >
                      Tout marquer lu
                    </button>
                  )}
                  <button
                    onClick={() => setIsOpen(false)}
                    className="p-1 hover:bg-gray-100 rounded-lg transition-colors"
                  >
                    <X className="w-5 h-5 text-gray-600" />
                  </button>
                </div>
              </div>

              {/* Notifications List */}
              <div className="max-h-96 overflow-y-auto">
                {notifications.length === 0 ? (
                  <div className="p-8 text-center">
                    <Bell className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                    <p className="text-gray-600">Aucune notification</p>
                  </div>
                ) : (
                  <div className="divide-y divide-gray-100">
                    {notifications.map((notif) => (
                      <NotificationItem
                        key={notif.id}
                        notification={notif}
                        onMarkAsRead={() => markAsRead(notif.id)}
                        getIcon={getIcon}
                      />
                    ))}
                  </div>
                )}
              </div>

              {/* Footer */}
              {notifications.length > 0 && (
                <div className="p-4 border-t border-gray-200">
                  <button
                    onClick={clearAll}
                    className="w-full text-center text-sm text-error-600 hover:text-error-700 font-medium"
                  >
                    Tout effacer
                  </button>
                </div>
              )}
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </>
  );
}

interface NotificationItemProps {
  notification: Notification;
  onMarkAsRead: () => void;
  getIcon: (type: string) => React.ReactNode;
}

function NotificationItem({ notification, onMarkAsRead, getIcon }: NotificationItemProps) {
  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      className={cn(
        "p-4 hover:bg-gray-50 transition-colors cursor-pointer group",
        !notification.read && "bg-brand-50/30"
      )}
      onClick={() => {
        if (!notification.read) onMarkAsRead();
        if (notification.actionUrl) {
          window.location.href = notification.actionUrl;
        }
      }}
    >
      <div className="flex items-start gap-3">
        <div className="flex-shrink-0 mt-1">
          {getIcon(notification.type)}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between mb-1">
            <h4 className="font-semibold text-gray-900 text-sm">
              {notification.title}
            </h4>
            {!notification.read && (
              <div className="w-2 h-2 bg-brand-600 rounded-full flex-shrink-0 mt-1.5" />
            )}
          </div>
          <p className="text-sm text-gray-600 mb-1">{notification.message}</p>
          <p className="text-xs text-gray-500">{formatDate(notification.time)}</p>
        </div>
      </div>
    </motion.div>
  );
}
