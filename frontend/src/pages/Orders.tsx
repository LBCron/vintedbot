import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  Package,
  Download,
  Star,
  MessageSquare,
  Filter,
  Calendar,
  TrendingUp,
  Printer,
  CheckCircle2,
  Clock,
  XCircle,
  Truck,
  Search,
  ChevronDown,
  FileText,
} from 'lucide-react';
import { ordersAPI } from '../api/client';
import { useAuth } from '../contexts/AuthContext';
import toast from 'react-hot-toast';
import Skeleton from 'react-loading-skeleton';
import 'react-loading-skeleton/dist/skeleton.css';
import { logger } from '../utils/logger';

interface Order {
  id: string;
  order_date: string;
  item_title: string;
  price: number;
  buyer_name: string;
  status: 'pending' | 'shipped' | 'completed' | 'cancelled';
  tracking_number?: string;
  notes?: string;
}

interface OrderStats {
  total_orders: number;
  by_status: {
    pending: number;
    shipped: number;
    completed: number;
    cancelled: number;
  };
  total_revenue: number;
}

interface FeedbackTemplate {
  id: string;
  name: string;
  rating: number;
  comment: string;
  is_default: boolean;
}

export default function Orders() {
  const { user } = useAuth();
  const [orders, setOrders] = useState<Order[]>([]);
  const [stats, setStats] = useState<OrderStats | null>(null);
  const [templates, setTemplates] = useState<FeedbackTemplate[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedOrders, setSelectedOrders] = useState<Set<string>>(new Set());
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [showFeedbackModal, setShowFeedbackModal] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState<string>('');
  const [customRating, setCustomRating] = useState(5);
  const [customComment, setCustomComment] = useState('');

  useEffect(() => {
    loadOrders();
    loadStats();
    loadTemplates();
  }, [filterStatus]);

  const loadOrders = async () => {
    try {
      setLoading(true);
      const params: any = { limit: 100 };
      if (filterStatus !== 'all') {
        params.status = filterStatus;
      }

      const response = await ordersAPI.listOrders(params);
      setOrders(response.data.orders);
    } catch (error) {
      logger.error('Failed to load orders', error);
      toast.error('Failed to load orders');
    } finally {
      setLoading(false);
    }
  };

  const loadStats = async () => {
    try {
      const response = await ordersAPI.getStats();
      setStats(response.data);
    } catch (error) {
      logger.error('Failed to load stats', error);
    }
  };

  const loadTemplates = async () => {
    try {
      const response = await ordersAPI.getFeedbackTemplates();
      setTemplates(response.data.templates);
      // Select default template
      const defaultTemplate = response.data.templates.find((t: FeedbackTemplate) => t.is_default);
      if (defaultTemplate) {
        setSelectedTemplate(defaultTemplate.id);
      }
    } catch (error) {
      logger.error('Failed to load templates', error);
    }
  };

  const handleExportCSV = async () => {
    try {
      toast.loading('Exporting orders...');
      const response = await ordersAPI.exportCSV({
        status: filterStatus !== 'all' ? filterStatus : undefined,
      });

      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `vinted_orders_${new Date().toISOString().split('T')[0]}.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();

      toast.dismiss();
      toast.success('Orders exported successfully!');
    } catch (error) {
      toast.dismiss();
      toast.error('Failed to export orders');
      logger.error('Export error', error);
    }
  };

  const handleBulkFeedback = async () => {
    if (selectedOrders.size === 0) {
      toast.error('Please select orders to send feedback');
      return;
    }

    try {
      let rating = customRating;
      let comment = customComment;

      // Use template if selected
      if (selectedTemplate) {
        const template = templates.find(t => t.id === selectedTemplate);
        if (template) {
          rating = template.rating;
          comment = template.comment;
        }
      }

      if (!comment) {
        toast.error('Please enter feedback comment');
        return;
      }

      toast.loading('Sending feedback...');
      const response = await ordersAPI.sendBulkFeedback({
        order_ids: Array.from(selectedOrders),
        rating,
        comment,
        auto_mark_complete: true,
      });

      toast.dismiss();
      toast.success(`Feedback sent to ${response.data.results.success.length} orders!`);

      setShowFeedbackModal(false);
      setSelectedOrders(new Set());
      loadOrders();
    } catch (error) {
      toast.dismiss();
      toast.error('Failed to send feedback');
      logger.error('Feedback error', error);
    }
  };

  const toggleOrderSelection = (orderId: string) => {
    const newSelection = new Set(selectedOrders);
    if (newSelection.has(orderId)) {
      newSelection.delete(orderId);
    } else {
      newSelection.add(orderId);
    }
    setSelectedOrders(newSelection);
  };

  const selectAll = () => {
    if (selectedOrders.size === orders.length) {
      setSelectedOrders(new Set());
    } else {
      setSelectedOrders(new Set(orders.map(o => o.id)));
    }
  };

  const filteredOrders = orders.filter(order => {
    if (searchQuery) {
      return (
        order.item_title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        order.buyer_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        order.id.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }
    return true;
  });

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'pending':
        return <Clock className="w-5 h-5 text-warning-500" />;
      case 'shipped':
        return <Truck className="w-5 h-5 text-primary-500" />;
      case 'completed':
        return <CheckCircle2 className="w-5 h-5 text-success-500" />;
      case 'cancelled':
        return <XCircle className="w-5 h-5 text-error-500" />;
      default:
        return null;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending':
        return 'bg-warning-100 text-warning-800 dark:bg-warning-900/20 dark:text-warning-400';
      case 'shipped':
        return 'bg-primary-100 text-primary-800 dark:bg-primary-900/20 dark:text-primary-400';
      case 'completed':
        return 'bg-success-100 text-success-800 dark:bg-success-900/20 dark:text-success-400';
      case 'cancelled':
        return 'bg-error-100 text-error-800 dark:bg-error-900/20 dark:text-error-400';
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-400';
    }
  };

  if (loading && orders.length === 0) {
    return (
      <div className="space-y-6">
        <Skeleton width={300} height={40} />
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          {[1, 2, 3, 4].map(i => (
            <Skeleton key={i} height={120} />
          ))}
        </div>
        <Skeleton height={400} />
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4"
      >
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white flex items-center gap-3">
            <Package className="w-8 h-8 text-primary-600" />
            Orders Management
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Track, manage, and export your Vinted orders
          </p>
        </div>

        <div className="flex gap-3">
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={handleExportCSV}
            className="flex items-center gap-2 px-4 py-2 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
          >
            <Download className="w-4 h-4" />
            Export CSV
          </motion.button>

          {selectedOrders.size > 0 && (
            <motion.button
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => setShowFeedbackModal(true)}
              className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
            >
              <Star className="w-4 h-4" />
              Bulk Feedback ({selectedOrders.size})
            </motion.button>
          )}
        </div>
      </motion.div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-white dark:bg-gray-800 rounded-xl p-6 border border-gray-200 dark:border-gray-700"
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-600 dark:text-gray-400">Total Orders</span>
              <Package className="w-5 h-5 text-gray-400" />
            </div>
            <div className="text-3xl font-bold text-gray-900 dark:text-white">
              {stats.total_orders}
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="bg-warning-50 dark:bg-warning-900/20 rounded-xl p-6 border border-warning-200 dark:border-warning-800"
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-warning-700 dark:text-warning-400">Pending</span>
              <Clock className="w-5 h-5 text-warning-500" />
            </div>
            <div className="text-3xl font-bold text-warning-900 dark:text-warning-100">
              {stats.by_status.pending}
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="bg-primary-50 dark:bg-primary-900/20 rounded-xl p-6 border border-primary-200 dark:border-primary-800"
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-primary-700 dark:text-primary-400">Shipped</span>
              <Truck className="w-5 h-5 text-primary-500" />
            </div>
            <div className="text-3xl font-bold text-primary-900 dark:text-primary-100">
              {stats.by_status.shipped}
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="bg-success-50 dark:bg-success-900/20 rounded-xl p-6 border border-success-200 dark:border-success-800"
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-success-700 dark:text-success-400">Completed</span>
              <CheckCircle2 className="w-5 h-5 text-success-500" />
            </div>
            <div className="text-3xl font-bold text-success-900 dark:text-success-100">
              {stats.by_status.completed}
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="bg-gradient-to-br from-primary-500 to-purple-600 rounded-xl p-6 text-white"
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-white/90">Total Revenue</span>
              <TrendingUp className="w-5 h-5 text-white/90" />
            </div>
            <div className="text-3xl font-bold">
              €{stats.total_revenue.toFixed(2)}
            </div>
          </motion.div>
        </div>
      )}

      {/* Filters and Search */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-white dark:bg-gray-800 rounded-xl p-6 border border-gray-200 dark:border-gray-700"
      >
        <div className="flex flex-col sm:flex-row gap-4">
          {/* Search */}
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search orders..."
              className="w-full pl-10 pr-4 py-2 bg-gray-50 dark:bg-gray-900 border border-gray-300 dark:border-gray-700 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
          </div>

          {/* Status Filter */}
          <div className="flex gap-2">
            <button
              onClick={() => setFilterStatus('all')}
              className={`px-4 py-2 rounded-lg transition-colors ${
                filterStatus === 'all'
                  ? 'bg-primary-600 text-white'
                  : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
              }`}
            >
              All
            </button>
            <button
              onClick={() => setFilterStatus('pending')}
              className={`px-4 py-2 rounded-lg transition-colors ${
                filterStatus === 'pending'
                  ? 'bg-warning-600 text-white'
                  : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
              }`}
            >
              Pending
            </button>
            <button
              onClick={() => setFilterStatus('shipped')}
              className={`px-4 py-2 rounded-lg transition-colors ${
                filterStatus === 'shipped'
                  ? 'bg-primary-600 text-white'
                  : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
              }`}
            >
              Shipped
            </button>
            <button
              onClick={() => setFilterStatus('completed')}
              className={`px-4 py-2 rounded-lg transition-colors ${
                filterStatus === 'completed'
                  ? 'bg-success-600 text-white'
                  : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
              }`}
            >
              Completed
            </button>
          </div>
        </div>
      </motion.div>

      {/* Orders Table */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden"
      >
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 dark:bg-gray-900/50">
              <tr>
                <th className="px-6 py-4 text-left">
                  <input
                    type="checkbox"
                    checked={selectedOrders.size === orders.length && orders.length > 0}
                    onChange={selectAll}
                    className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                  />
                </th>
                <th className="px-6 py-4 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Order Details
                </th>
                <th className="px-6 py-4 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Buyer
                </th>
                <th className="px-6 py-4 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-4 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Price
                </th>
                <th className="px-6 py-4 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Date
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
              {filteredOrders.map((order, index) => (
                <motion.tr
                  key={order.id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.05 }}
                  className="hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors"
                >
                  <td className="px-6 py-4">
                    <input
                      type="checkbox"
                      checked={selectedOrders.has(order.id)}
                      onChange={() => toggleOrderSelection(order.id)}
                      className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                    />
                  </td>
                  <td className="px-6 py-4">
                    <div>
                      <div className="font-medium text-gray-900 dark:text-white">
                        {order.item_title}
                      </div>
                      <div className="text-sm text-gray-500 dark:text-gray-400">
                        #{order.id.slice(0, 8)}
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="text-sm text-gray-900 dark:text-white">
                      {order.buyer_name}
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <span className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(order.status)}`}>
                      {getStatusIcon(order.status)}
                      {order.status.charAt(0).toUpperCase() + order.status.slice(1)}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <div className="font-semibold text-gray-900 dark:text-white">
                      €{order.price.toFixed(2)}
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="text-sm text-gray-500 dark:text-gray-400">
                      {new Date(order.order_date).toLocaleDateString()}
                    </div>
                  </td>
                </motion.tr>
              ))}
            </tbody>
          </table>
        </div>

        {filteredOrders.length === 0 && (
          <div className="text-center py-12">
            <Package className="w-16 h-16 text-gray-300 dark:text-gray-600 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
              No orders found
            </h3>
            <p className="text-gray-500 dark:text-gray-400">
              {searchQuery ? 'Try adjusting your search' : 'Your orders will appear here'}
            </p>
          </div>
        )}
      </motion.div>

      {/* Bulk Feedback Modal */}
      {showFeedbackModal && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
          onClick={() => setShowFeedbackModal(false)}
        >
          <motion.div
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.9, opacity: 0 }}
            onClick={(e) => e.stopPropagation()}
            className="bg-white dark:bg-gray-800 rounded-2xl p-6 max-w-2xl w-full max-h-[90vh] overflow-y-auto"
          >
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-6 flex items-center gap-3">
              <Star className="w-6 h-6 text-warning-500" />
              Send Bulk Feedback
            </h2>

            <div className="space-y-6">
              {/* Template Selection */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Select Template
                </label>
                <div className="grid grid-cols-1 gap-3">
                  {templates.map((template) => (
                    <button
                      key={template.id}
                      onClick={() => {
                        setSelectedTemplate(template.id);
                        setCustomComment(template.comment);
                        setCustomRating(template.rating);
                      }}
                      className={`p-4 rounded-lg border-2 transition-all text-left ${
                        selectedTemplate === template.id
                          ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20'
                          : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                      }`}
                    >
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-medium text-gray-900 dark:text-white">
                          {template.name}
                        </span>
                        <div className="flex gap-1">
                          {[...Array(template.rating)].map((_, i) => (
                            <Star key={i} className="w-4 h-4 fill-warning-500 text-warning-500" />
                          ))}
                        </div>
                      </div>
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        {template.comment}
                      </p>
                    </button>
                  ))}
                </div>
              </div>

              {/* Custom Comment */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Custom Comment (Optional)
                </label>
                <textarea
                  value={customComment}
                  onChange={(e) => setCustomComment(e.target.value)}
                  rows={4}
                  className="w-full px-4 py-2 bg-gray-50 dark:bg-gray-900 border border-gray-300 dark:border-gray-700 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  placeholder="Enter custom feedback..."
                />
              </div>

              {/* Custom Rating */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Rating
                </label>
                <div className="flex gap-2">
                  {[1, 2, 3, 4, 5].map((rating) => (
                    <button
                      key={rating}
                      onClick={() => setCustomRating(rating)}
                      className="transition-transform hover:scale-110"
                    >
                      <Star
                        className={`w-8 h-8 ${
                          rating <= customRating
                            ? 'fill-warning-500 text-warning-500'
                            : 'text-gray-300 dark:text-gray-600'
                        }`}
                      />
                    </button>
                  ))}
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex gap-3 pt-4">
                <button
                  onClick={() => setShowFeedbackModal(false)}
                  className="flex-1 px-4 py-2 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleBulkFeedback}
                  className="flex-1 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
                >
                  Send to {selectedOrders.size} orders
                </button>
              </div>
            </div>
          </motion.div>
        </motion.div>
      )}
    </div>
  );
}
