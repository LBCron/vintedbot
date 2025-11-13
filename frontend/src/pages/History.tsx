import { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Clock,
  Upload,
  Edit,
  Trash2,
  Send,
  Archive,
  DollarSign,
  Image as ImageIcon,
  FileText,
  Settings,
  Users,
  RotateCcw,
  Search,
  Filter,
  Calendar,
  Download,
  ChevronRight,
  AlertCircle,
  CheckCircle,
  XCircle,
  Info,
} from 'lucide-react';
import { Badge } from '../components/common/Badge';
import { Tooltip } from '../components/common/Tooltip';
import { logger } from '../utils/logger';

interface HistoryAction {
  id: string;
  type: 'upload' | 'edit' | 'delete' | 'publish' | 'price_change' | 'status_change' | 'bulk_action';
  action: string;
  description: string;
  timestamp: Date;
  user: string;
  metadata?: {
    itemCount?: number;
    oldValue?: string | number;
    newValue?: string | number;
    itemName?: string;
    itemImage?: string;
  };
  status: 'success' | 'warning' | 'error' | 'info';
  canRestore: boolean;
}

const mockHistory: HistoryAction[] = [
  {
    id: '1',
    type: 'publish',
    action: 'Published listing',
    description: 'Nike Air Max 90 published to Vinted',
    timestamp: new Date(Date.now() - 5 * 60000),
    user: 'You',
    metadata: {
      itemName: 'Nike Air Max 90',
      itemImage: 'https://via.placeholder.com/60',
      newValue: 'Published',
    },
    status: 'success',
    canRestore: true,
  },
  {
    id: '2',
    type: 'edit',
    action: 'Price updated',
    description: 'Changed price from €99.99 to €89.99',
    timestamp: new Date(Date.now() - 15 * 60000),
    user: 'You',
    metadata: {
      itemName: 'Nike Air Max 90',
      itemImage: 'https://via.placeholder.com/60',
      oldValue: 99.99,
      newValue: 89.99,
    },
    status: 'info',
    canRestore: true,
  },
  {
    id: '3',
    type: 'upload',
    action: 'Bulk upload',
    description: 'Uploaded and analyzed 24 photos',
    timestamp: new Date(Date.now() - 30 * 60000),
    user: 'You',
    metadata: {
      itemCount: 24,
    },
    status: 'success',
    canRestore: false,
  },
  {
    id: '4',
    type: 'delete',
    action: 'Draft deleted',
    description: 'Adidas Hoodie Vintage draft deleted',
    timestamp: new Date(Date.now() - 45 * 60000),
    user: 'You',
    metadata: {
      itemName: 'Adidas Hoodie Vintage',
      itemImage: 'https://via.placeholder.com/60',
    },
    status: 'warning',
    canRestore: true,
  },
  {
    id: '5',
    type: 'bulk_action',
    action: 'Bulk publish',
    description: 'Published 12 listings to Vinted',
    timestamp: new Date(Date.now() - 2 * 3600000),
    user: 'You',
    metadata: {
      itemCount: 12,
    },
    status: 'success',
    canRestore: true,
  },
  {
    id: '6',
    type: 'edit',
    action: 'Description updated',
    description: 'Updated description for Levi\'s 501 Jeans',
    timestamp: new Date(Date.now() - 4 * 3600000),
    user: 'You',
    metadata: {
      itemName: 'Levi\'s 501 Jeans',
      itemImage: 'https://via.placeholder.com/60',
    },
    status: 'info',
    canRestore: true,
  },
  {
    id: '7',
    type: 'status_change',
    action: 'Listing sold',
    description: 'Zara Jacket marked as sold',
    timestamp: new Date(Date.now() - 24 * 3600000),
    user: 'System',
    metadata: {
      itemName: 'Zara Jacket',
      itemImage: 'https://via.placeholder.com/60',
    },
    status: 'success',
    canRestore: false,
  },
];

const actionIcons = {
  upload: Upload,
  edit: Edit,
  delete: Trash2,
  publish: Send,
  price_change: DollarSign,
  status_change: Settings,
  bulk_action: FileText,
};

const statusIcons = {
  success: CheckCircle,
  warning: AlertCircle,
  error: XCircle,
  info: Info,
};

export default function History() {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedType, setSelectedType] = useState<string>('all');
  const [selectedDateRange, setSelectedDateRange] = useState<string>('all');
  const [history, setHistory] = useState<HistoryAction[]>(mockHistory);

  const actionTypes = ['all', ...Array.from(new Set(history.map(h => h.type)))];

  const filteredHistory = useMemo(() => {
    return history.filter(action => {
      const matchesSearch =
        action.action.toLowerCase().includes(searchQuery.toLowerCase()) ||
        action.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
        action.metadata?.itemName?.toLowerCase().includes(searchQuery.toLowerCase());

      const matchesType = selectedType === 'all' || action.type === selectedType;

      let matchesDate = true;
      if (selectedDateRange !== 'all') {
        const now = Date.now();
        const actionTime = action.timestamp.getTime();
        switch (selectedDateRange) {
          case 'today':
            matchesDate = now - actionTime < 24 * 3600000;
            break;
          case 'week':
            matchesDate = now - actionTime < 7 * 24 * 3600000;
            break;
          case 'month':
            matchesDate = now - actionTime < 30 * 24 * 3600000;
            break;
        }
      }

      return matchesSearch && matchesType && matchesDate;
    });
  }, [history, searchQuery, selectedType, selectedDateRange]);

  const handleRestore = (actionId: string) => {
    // In a real app, this would trigger an API call to restore the action
    logger.info('Restoring action', { actionId });
  };

  const groupedHistory = useMemo(() => {
    const groups: { [key: string]: HistoryAction[] } = {};

    filteredHistory.forEach(action => {
      const date = action.timestamp.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
      });

      if (!groups[date]) {
        groups[date] = [];
      }
      groups[date].push(action);
    });

    return Object.entries(groups).sort((a, b) => {
      return new Date(b[0]).getTime() - new Date(a[0]).getTime();
    });
  }, [filteredHistory]);

  const getActionIcon = (type: HistoryAction['type']) => {
    return actionIcons[type] || Clock;
  };

  const getStatusIcon = (status: HistoryAction['status']) => {
    return statusIcons[status];
  };

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center justify-between"
      >
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            📜 Activity History
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-2">
            Track all actions and restore previous states
          </p>
        </div>

        <div className="flex items-center gap-3">
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            className="px-6 py-3 bg-white dark:bg-gray-800 border-2 border-gray-200 dark:border-gray-700 text-gray-900 dark:text-white rounded-lg flex items-center gap-2 font-medium hover:border-primary-500 dark:hover:border-primary-500 transition-all"
          >
            <Download className="w-5 h-5" />
            Export
          </motion.button>
        </div>
      </motion.div>

      {/* Stats */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.1 }}
        className="grid grid-cols-1 md:grid-cols-4 gap-4"
      >
        {[
          { label: 'Total Actions', value: history.length, icon: Clock, color: 'primary' },
          { label: 'Today', value: history.filter(h => Date.now() - h.timestamp.getTime() < 24 * 3600000).length, icon: Calendar, color: 'success' },
          { label: 'Published', value: history.filter(h => h.type === 'publish').length, icon: Send, color: 'info' },
          { label: 'Can Restore', value: history.filter(h => h.canRestore).length, icon: RotateCcw, color: 'warning' },
        ].map((stat, index) => (
          <motion.div
            key={stat.label}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 + index * 0.05 }}
            className="card p-6"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">{stat.label}</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">
                  {stat.value}
                </p>
              </div>
              <div className={`p-3 bg-${stat.color}-100 dark:bg-${stat.color}-900/20 rounded-xl`}>
                <stat.icon className={`w-6 h-6 text-${stat.color}-600 dark:text-${stat.color}-400`} />
              </div>
            </div>
          </motion.div>
        ))}
      </motion.div>

      {/* Filters */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.2 }}
        className="card p-6"
      >
        <div className="flex flex-col md:flex-row gap-4">
          {/* Search */}
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              placeholder="Search history..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-3 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all"
            />
          </div>

          {/* Type Filter */}
          <select
            value={selectedType}
            onChange={(e) => setSelectedType(e.target.value)}
            className="px-4 py-3 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all"
          >
            {actionTypes.map(type => (
              <option key={type} value={type}>
                {type === 'all' ? 'All Actions' : type.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')}
              </option>
            ))}
          </select>

          {/* Date Range Filter */}
          <select
            value={selectedDateRange}
            onChange={(e) => setSelectedDateRange(e.target.value)}
            className="px-4 py-3 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all"
          >
            <option value="all">All Time</option>
            <option value="today">Today</option>
            <option value="week">This Week</option>
            <option value="month">This Month</option>
          </select>
        </div>
      </motion.div>

      {/* Timeline */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.3 }}
        className="space-y-8"
      >
        {groupedHistory.map(([date, actions]) => (
          <div key={date}>
            {/* Date Header */}
            <div className="flex items-center gap-4 mb-4">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                {date}
              </h3>
              <div className="flex-1 h-px bg-gray-200 dark:bg-gray-700" />
              <Badge variant="default" size="sm">
                {actions.length} {actions.length === 1 ? 'action' : 'actions'}
              </Badge>
            </div>

            {/* Actions */}
            <div className="relative pl-8 space-y-4">
              {/* Timeline Line */}
              <div className="absolute left-0 top-0 bottom-0 w-0.5 bg-gray-200 dark:bg-gray-700" />

              <AnimatePresence>
                {actions.map((action, index) => {
                  const ActionIcon = getActionIcon(action.type);
                  const StatusIcon = getStatusIcon(action.status);

                  return (
                    <motion.div
                      key={action.id}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: 20 }}
                      transition={{ delay: index * 0.05 }}
                      className="relative"
                    >
                      {/* Timeline Dot */}
                      <div className={`absolute -left-8 top-4 w-4 h-4 rounded-full border-2 border-white dark:border-gray-900 ${
                        action.status === 'success' ? 'bg-success-500' :
                        action.status === 'warning' ? 'bg-warning-500' :
                        action.status === 'error' ? 'bg-error-500' :
                        'bg-primary-500'
                      }`} />

                      <div className="card p-6 hover:shadow-lg transition-shadow">
                        <div className="flex items-start gap-4">
                          {/* Icon */}
                          <div className={`p-3 rounded-xl ${
                            action.status === 'success' ? 'bg-success-100 dark:bg-success-900/20' :
                            action.status === 'warning' ? 'bg-warning-100 dark:bg-warning-900/20' :
                            action.status === 'error' ? 'bg-error-100 dark:bg-error-900/20' :
                            'bg-primary-100 dark:bg-primary-900/20'
                          }`}>
                            <ActionIcon className={`w-6 h-6 ${
                              action.status === 'success' ? 'text-success-600 dark:text-success-400' :
                              action.status === 'warning' ? 'text-warning-600 dark:text-warning-400' :
                              action.status === 'error' ? 'text-error-600 dark:text-error-400' :
                              'text-primary-600 dark:text-primary-400'
                            }`} />
                          </div>

                          {/* Content */}
                          <div className="flex-1 min-w-0">
                            <div className="flex items-start justify-between mb-2">
                              <div>
                                <h4 className="font-semibold text-gray-900 dark:text-white">
                                  {action.action}
                                </h4>
                                <p className="text-sm text-gray-600 dark:text-gray-400">
                                  {action.description}
                                </p>
                              </div>
                              <Badge
                                variant={
                                  action.status === 'success' ? 'success' :
                                  action.status === 'warning' ? 'warning' :
                                  action.status === 'error' ? 'error' :
                                  'default'
                                }
                                size="sm"
                              >
                                <StatusIcon className="w-3 h-3 mr-1" />
                                {action.status}
                              </Badge>
                            </div>

                            {/* Metadata */}
                            {action.metadata && (
                              <div className="flex items-center gap-4 mb-3">
                                {action.metadata.itemImage && (
                                  <img
                                    src={action.metadata.itemImage}
                                    alt={action.metadata.itemName}
                                    className="w-12 h-12 object-cover rounded-lg"
                                  />
                                )}
                                {action.metadata.itemName && (
                                  <span className="text-sm font-medium text-gray-900 dark:text-white">
                                    {action.metadata.itemName}
                                  </span>
                                )}
                                {action.metadata.itemCount !== undefined && (
                                  <Badge variant="primary" size="sm">
                                    {action.metadata.itemCount} items
                                  </Badge>
                                )}
                                {action.metadata.oldValue !== undefined && action.metadata.newValue !== undefined && (
                                  <div className="flex items-center gap-2 text-sm">
                                    <span className="text-gray-500 line-through">
                                      {typeof action.metadata.oldValue === 'number' ? `€${action.metadata.oldValue}` : action.metadata.oldValue}
                                    </span>
                                    <ChevronRight className="w-4 h-4 text-gray-400" />
                                    <span className="text-gray-900 dark:text-white font-medium">
                                      {typeof action.metadata.newValue === 'number' ? `€${action.metadata.newValue}` : action.metadata.newValue}
                                    </span>
                                  </div>
                                )}
                              </div>
                            )}

                            {/* Footer */}
                            <div className="flex items-center justify-between">
                              <div className="flex items-center gap-4 text-sm text-gray-500">
                                <span className="flex items-center gap-1">
                                  <Clock className="w-4 h-4" />
                                  {action.timestamp.toLocaleTimeString('en-US', {
                                    hour: '2-digit',
                                    minute: '2-digit',
                                  })}
                                </span>
                                <span>{action.user}</span>
                              </div>

                              {action.canRestore && (
                                <Tooltip content="Restore this action">
                                  <motion.button
                                    whileHover={{ scale: 1.05 }}
                                    whileTap={{ scale: 0.95 }}
                                    onClick={() => handleRestore(action.id)}
                                    className="px-4 py-2 bg-primary-50 dark:bg-primary-900/20 text-primary-700 dark:text-primary-400 rounded-lg hover:bg-primary-100 dark:hover:bg-primary-900/40 font-medium text-sm inline-flex items-center gap-2 transition-colors"
                                  >
                                    <RotateCcw className="w-4 h-4" />
                                    Restore
                                  </motion.button>
                                </Tooltip>
                              )}
                            </div>
                          </div>
                        </div>
                      </div>
                    </motion.div>
                  );
                })}
              </AnimatePresence>
            </div>
          </div>
        ))}
      </motion.div>

      {/* Empty State */}
      {filteredHistory.length === 0 && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="card p-12 text-center"
        >
          <Clock className="w-16 h-16 text-gray-300 dark:text-gray-600 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
            No history found
          </h3>
          <p className="text-gray-600 dark:text-gray-400">
            {searchQuery ? 'Try adjusting your search or filters' : 'Your actions will appear here'}
          </p>
        </motion.div>
      )}
    </div>
  );
}
