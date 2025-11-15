import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
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
  X,
} from 'lucide-react';
import { ordersAPI } from '../api/client';
import { useAuth } from '../contexts/AuthContext';
import toast from 'react-hot-toast';
import { logger } from '../utils/logger';
import { GlassCard } from '../components/ui/GlassCard';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { EmptyState } from '../components/ui/EmptyState';
import { AnimatedNumber } from '../components/ui/AnimatedNumber';

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
        return <Clock className="w-4 h-4" />;
      case 'shipped':
        return <Truck className="w-4 h-4" />;
      case 'completed':
        return <CheckCircle2 className="w-4 h-4" />;
      case 'cancelled':
        return <XCircle className="w-4 h-4" />;
      default:
        return null;
    }
  };

  const getStatusBadgeVariant = (status: string): 'success' | 'warning' | 'info' | 'error' => {
    switch (status) {
      case 'completed':
        return 'success';
      case 'pending':
        return 'warning';
      case 'shipped':
        return 'info';
      case 'cancelled':
        return 'error';
      default:
        return 'info';
    }
  };

  if (loading && orders.length === 0) {
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
              <p className="text-slate-400">Loading orders...</p>
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
          className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4"
        >
          <div className="flex items-center gap-4">
            <div className="p-4 bg-gradient-to-br from-violet-500 to-purple-600 rounded-2xl shadow-lg shadow-violet-500/50">
              <Package className="w-8 h-8 text-white" />
            </div>
            <div>
              <h1 className="text-4xl md:text-5xl font-bold bg-gradient-to-r from-white via-violet-200 to-purple-200 bg-clip-text text-transparent">
                Orders Management
              </h1>
              <p className="text-slate-400 mt-1">
                Track, manage, and export your Vinted orders
              </p>
            </div>
          </div>

          <div className="flex gap-3">
            <Button
              variant="outline"
              icon={Download}
              onClick={handleExportCSV}
            >
              Export CSV
            </Button>

            <AnimatePresence>
              {selectedOrders.size > 0 && (
                <motion.div
                  initial={{ scale: 0, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  exit={{ scale: 0, opacity: 0 }}
                >
                  <Button
                    icon={Star}
                    onClick={() => setShowFeedbackModal(true)}
                  >
                    Bulk Feedback ({selectedOrders.size})
                  </Button>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </motion.div>

        {/* Stats Cards */}
        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6">
            <GlassCard hover className="p-6">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-slate-400">Total Orders</span>
                <Package className="w-5 h-5 text-slate-400" />
              </div>
              <div className="text-3xl font-bold text-white">
                <AnimatedNumber value={stats.total_orders} />
              </div>
            </GlassCard>

            <GlassCard hover className="p-6 bg-gradient-to-br from-yellow-500/10 to-orange-500/10 border-yellow-500/30">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-yellow-400">Pending</span>
                <Clock className="w-5 h-5 text-yellow-400" />
              </div>
              <div className="text-3xl font-bold text-yellow-300">
                <AnimatedNumber value={stats.by_status.pending} />
              </div>
            </GlassCard>

            <GlassCard hover className="p-6 bg-gradient-to-br from-blue-500/10 to-cyan-500/10 border-blue-500/30">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-blue-400">Shipped</span>
                <Truck className="w-5 h-5 text-blue-400" />
              </div>
              <div className="text-3xl font-bold text-blue-300">
                <AnimatedNumber value={stats.by_status.shipped} />
              </div>
            </GlassCard>

            <GlassCard hover className="p-6 bg-gradient-to-br from-green-500/10 to-emerald-500/10 border-green-500/30">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-green-400">Completed</span>
                <CheckCircle2 className="w-5 h-5 text-green-400" />
              </div>
              <div className="text-3xl font-bold text-green-300">
                <AnimatedNumber value={stats.by_status.completed} />
              </div>
            </GlassCard>

            <GlassCard hover className="p-6 bg-gradient-to-br from-violet-500/20 to-purple-600/20 border-violet-500/40">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-white">Total Revenue</span>
                <TrendingUp className="w-5 h-5 text-white" />
              </div>
              <div className="text-3xl font-bold text-white">
                €{stats.total_revenue.toFixed(2)}
              </div>
            </GlassCard>
          </div>
        )}

        {/* Filters and Search */}
        <GlassCard className="p-6">
          <div className="flex flex-col sm:flex-row gap-4">
            {/* Search */}
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search orders..."
                className="w-full pl-10 pr-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder-slate-400 focus:outline-none focus:border-violet-500/50 focus:bg-white/10 transition-all"
              />
            </div>

            {/* Status Filter */}
            <div className="flex gap-2 flex-wrap">
              {[
                { value: 'all', label: 'All', color: 'violet' },
                { value: 'pending', label: 'Pending', color: 'yellow' },
                { value: 'shipped', label: 'Shipped', color: 'blue' },
                { value: 'completed', label: 'Completed', color: 'green' },
              ].map((filter) => (
                <button
                  key={filter.value}
                  onClick={() => setFilterStatus(filter.value)}
                  className={`px-4 py-2 rounded-xl font-medium transition-all ${
                    filterStatus === filter.value
                      ? 'bg-gradient-to-r from-violet-500 to-purple-600 text-white shadow-lg shadow-violet-500/50'
                      : 'bg-white/5 border border-white/10 text-slate-300 hover:bg-white/10'
                  }`}
                >
                  {filter.label}
                </button>
              ))}
            </div>
          </div>
        </GlassCard>

        {/* Orders Table */}
        <GlassCard className="overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-white/5">
                <tr>
                  <th className="px-6 py-4 text-left">
                    <input
                      type="checkbox"
                      checked={selectedOrders.size === orders.length && orders.length > 0}
                      onChange={selectAll}
                      className="rounded border-white/20 bg-white/5 text-violet-600 focus:ring-violet-500"
                    />
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
                    Order Details
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
                    Buyer
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
                    Price
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
                    Date
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {filteredOrders.map((order, index) => (
                  <motion.tr
                    key={order.id}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.05 }}
                    className="hover:bg-white/5 transition-colors"
                  >
                    <td className="px-6 py-4">
                      <input
                        type="checkbox"
                        checked={selectedOrders.has(order.id)}
                        onChange={() => toggleOrderSelection(order.id)}
                        className="rounded border-white/20 bg-white/5 text-violet-600 focus:ring-violet-500"
                      />
                    </td>
                    <td className="px-6 py-4">
                      <div>
                        <div className="font-medium text-white">
                          {order.item_title}
                        </div>
                        <div className="text-sm text-slate-400">
                          #{order.id.slice(0, 8)}
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-sm text-white">
                        {order.buyer_name}
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <Badge variant={getStatusBadgeVariant(order.status)} size="sm">
                        <span className="flex items-center gap-1">
                          {getStatusIcon(order.status)}
                          {order.status.charAt(0).toUpperCase() + order.status.slice(1)}
                        </span>
                      </Badge>
                    </td>
                    <td className="px-6 py-4">
                      <div className="font-semibold text-white">
                        €{order.price.toFixed(2)}
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-sm text-slate-400">
                        {new Date(order.order_date).toLocaleDateString()}
                      </div>
                    </td>
                  </motion.tr>
                ))}
              </tbody>
            </table>
          </div>

          {filteredOrders.length === 0 && !loading && (
            <EmptyState
              icon={Package}
              title="No orders found"
              description={searchQuery ? 'Try adjusting your search' : 'Your orders will appear here'}
            />
          )}
        </GlassCard>

        {/* Bulk Feedback Modal */}
        <AnimatePresence>
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
              >
                <GlassCard className="max-w-2xl w-full max-h-[90vh] overflow-y-auto">
                  <div className="flex items-center justify-between mb-6">
                    <h2 className="text-2xl font-bold text-white flex items-center gap-3">
                      <Star className="w-6 h-6 text-yellow-400" />
                      Send Bulk Feedback
                    </h2>
                    <button
                      onClick={() => setShowFeedbackModal(false)}
                      className="p-2 hover:bg-white/10 rounded-lg transition-colors"
                    >
                      <X className="w-6 h-6 text-slate-400" />
                    </button>
                  </div>

                  <div className="space-y-6">
                    {/* Template Selection */}
                    <div>
                      <label className="block text-sm font-medium text-slate-300 mb-3">
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
                            className={`p-4 rounded-xl border-2 transition-all text-left ${
                              selectedTemplate === template.id
                                ? 'border-violet-500 bg-violet-500/10'
                                : 'border-white/10 hover:border-white/20 bg-white/5'
                            }`}
                          >
                            <div className="flex items-center justify-between mb-2">
                              <span className="font-medium text-white">
                                {template.name}
                              </span>
                              <div className="flex gap-1">
                                {[...Array(template.rating)].map((_, i) => (
                                  <Star key={i} className="w-4 h-4 fill-yellow-400 text-yellow-400" />
                                ))}
                              </div>
                            </div>
                            <p className="text-sm text-slate-400">
                              {template.comment}
                            </p>
                          </button>
                        ))}
                      </div>
                    </div>

                    {/* Custom Comment */}
                    <div>
                      <label className="block text-sm font-medium text-slate-300 mb-2">
                        Custom Comment (Optional)
                      </label>
                      <textarea
                        value={customComment}
                        onChange={(e) => setCustomComment(e.target.value)}
                        rows={4}
                        className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder-slate-400 focus:outline-none focus:border-violet-500/50 focus:bg-white/10 transition-all"
                        placeholder="Enter custom feedback..."
                      />
                    </div>

                    {/* Custom Rating */}
                    <div>
                      <label className="block text-sm font-medium text-slate-300 mb-2">
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
                                  ? 'fill-yellow-400 text-yellow-400'
                                  : 'text-slate-600'
                              }`}
                            />
                          </button>
                        ))}
                      </div>
                    </div>

                    {/* Action Buttons */}
                    <div className="flex gap-3 pt-4">
                      <Button
                        variant="outline"
                        onClick={() => setShowFeedbackModal(false)}
                        className="flex-1"
                      >
                        Cancel
                      </Button>
                      <Button
                        onClick={handleBulkFeedback}
                        className="flex-1"
                      >
                        Send to {selectedOrders.size} orders
                      </Button>
                    </div>
                  </div>
                </GlassCard>
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
