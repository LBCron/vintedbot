import { useState } from 'react';
import { motion } from 'framer-motion';
import {
  Package,
  TrendingUp,
  Clock,
  CheckCircle2,
  Truck,
  Search,
  Calendar,
  User,
  MapPin,
  Download,
  X
} from 'lucide-react';
import { cn, formatPrice, formatDate } from '@/lib/utils';

export default function Orders() {
  const [searchQuery, setSearchQuery] = useState('');
  const [filterStatus, setFilterStatus] = useState<'all' | 'pending' | 'shipped' | 'delivered'>('all');

  // Mock data
  const orders = [
    {
      id: '1',
      item_title: "Jean Levi's 501",
      buyer: { name: 'Sophie Martin', avatar: '' },
      price: 35,
      status: 'shipped',
      tracking_number: 'FR1234567890',
      ordered_at: new Date('2024-01-20'),
      shipped_at: new Date('2024-01-21'),
      image: ''
    },
    {
      id: '2',
      item_title: "Nike Air Max 90",
      buyer: { name: 'Thomas Dubois', avatar: '' },
      price: 89,
      status: 'delivered',
      tracking_number: 'FR0987654321',
      ordered_at: new Date('2024-01-18'),
      delivered_at: new Date('2024-01-22'),
      image: ''
    },
    {
      id: '3',
      item_title: "Robe Zara été",
      buyer: { name: 'Marie Laurent', avatar: '' },
      price: 28,
      status: 'pending',
      ordered_at: new Date('2024-01-24'),
      image: ''
    },
  ];

  const stats = {
    total_orders: 156,
    pending: 3,
    shipped: 8,
    delivered: 145,
    total_revenue: 4280
  };

  const filteredOrders = orders.filter(order => {
    const matchesStatus = filterStatus === 'all' || order.status === filterStatus;
    const matchesSearch = order.item_title.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesStatus && matchesSearch;
  });

  return (
    <div className="min-h-screen bg-gray-50 -m-8">
      {/* Header */}
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
                <Package className="w-8 h-8" />
              </motion.div>
              <h1 className="text-4xl font-bold">Commandes</h1>
            </div>
            <p className="text-brand-100 text-lg">
              Gérez toutes vos commandes en un seul endroit
            </p>
          </motion.div>

          {/* Stats Grid */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mt-8">
            <OrderStatCard
              icon={<Package className="w-5 h-5" />}
              label="Total"
              value={stats.total_orders}
              color="white"
            />
            <OrderStatCard
              icon={<Clock className="w-5 h-5" />}
              label="En attente"
              value={stats.pending}
              color="orange"
            />
            <OrderStatCard
              icon={<Truck className="w-5 h-5" />}
              label="Expédiées"
              value={stats.shipped}
              color="blue"
            />
            <OrderStatCard
              icon={<CheckCircle2 className="w-5 h-5" />}
              label="Livrées"
              value={stats.delivered}
              color="green"
            />
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-6 -mt-8 pb-12">
        {/* Search & Filters */}
        <div className="bg-white rounded-2xl p-6 border border-gray-200 shadow-sm mb-6">
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Rechercher une commande..."
                className="w-full pl-10 pr-4 py-3 bg-gray-50 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-brand-500"
              />
            </div>
            <div className="flex gap-2">
              {(['all', 'pending', 'shipped', 'delivered'] as const).map(status => (
                <button
                  key={status}
                  onClick={() => setFilterStatus(status)}
                  className={cn(
                    "px-4 py-2 rounded-xl text-sm font-medium transition-all",
                    filterStatus === status
                      ? "bg-brand-600 text-white shadow-md"
                      : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                  )}
                >
                  {status === 'all' ? 'Toutes' :
                   status === 'pending' ? 'En attente' :
                   status === 'shipped' ? 'Expédiées' : 'Livrées'}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Orders List */}
        <div className="space-y-4">
          {filteredOrders.map((order, index) => (
            <OrderCard key={order.id} order={order} index={index} />
          ))}
        </div>
      </div>
    </div>
  );
}

function OrderStatCard({ icon, label, value, color }: any) {
  const colors = {
    white: 'bg-white/20 text-white backdrop-blur-sm',
    orange: 'bg-orange-50 text-orange-600',
    blue: 'bg-blue-50 text-blue-600',
    green: 'bg-success-50 text-success-600'
  };

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      whileHover={{ scale: 1.02 }}
      className={cn(
        "p-4 rounded-xl transition-all",
        color === 'white' ? colors.white : "bg-white border border-gray-200"
      )}
    >
      <div className="flex items-center gap-3 mb-2">
        <div className={cn(
          "p-2 rounded-lg",
          color !== 'white' && colors[color]
        )}>
          {icon}
        </div>
        <span className={cn(
          "text-2xl font-bold",
          color === 'white' ? "text-white" : "text-gray-900"
        )}>{value}</span>
      </div>
      <p className={cn(
        "text-sm",
        color === 'white' ? "text-white/80" : "text-gray-600"
      )}>{label}</p>
    </motion.div>
  );
}

function OrderCard({ order, index }: any) {
  const statusConfig = {
    pending: {
      color: 'bg-orange-100 text-orange-700 border-orange-200',
      label: 'En attente',
      icon: Clock,
      progress: 33
    },
    shipped: {
      color: 'bg-blue-100 text-blue-700 border-blue-200',
      label: 'Expédiée',
      icon: Truck,
      progress: 66
    },
    delivered: {
      color: 'bg-success-100 text-success-700 border-success-200',
      label: 'Livrée',
      icon: CheckCircle2,
      progress: 100
    }
  };

  const config = statusConfig[order.status as keyof typeof statusConfig];
  const StatusIcon = config.icon;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05 }}
      whileHover={{ scale: 1.01 }}
      className="bg-white rounded-2xl border border-gray-200 p-6 hover:shadow-md transition-all"
    >
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-start gap-4 flex-1">
          {/* Image */}
          <div className="w-20 h-20 bg-gray-100 rounded-xl overflow-hidden flex-shrink-0">
            <img
              src={order.image || '/placeholder.jpg'}
              alt={order.item_title}
              className="w-full h-full object-cover"
            />
          </div>

          {/* Info */}
          <div className="flex-1">
            <h3 className="font-semibold text-gray-900 mb-1">
              {order.item_title}
            </h3>
            <div className="flex items-center gap-2 text-sm text-gray-600 mb-2">
              <User className="w-4 h-4" />
              {order.buyer.name}
            </div>
            <div className="flex items-center gap-4 text-sm text-gray-500">
              <span className="flex items-center gap-1">
                <Calendar className="w-4 h-4" />
                {formatDate(order.ordered_at)}
              </span>
              {order.tracking_number && (
                <span className="font-mono text-xs bg-gray-100 px-2 py-1 rounded">
                  {order.tracking_number}
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Price & Status */}
        <div className="text-right flex-shrink-0 ml-4">
          <div className="text-2xl font-bold text-gray-900 mb-2">
            {formatPrice(order.price)}
          </div>
          <span className={cn(
            "inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold border",
            config.color
          )}>
            <StatusIcon className="w-3.5 h-3.5" />
            {config.label}
          </span>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="pt-4 border-t border-gray-100">
        <div className="flex items-center gap-4">
          <div className="flex-1 h-2 bg-gray-100 rounded-full overflow-hidden">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${config.progress}%` }}
              transition={{ duration: 0.8, delay: index * 0.1 }}
              className="h-full bg-gradient-to-r from-brand-500 to-brand-600 rounded-full"
            />
          </div>
          <button className="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg transition-colors text-sm font-medium flex items-center gap-2">
            <Truck className="w-4 h-4" />
            Suivre
          </button>
        </div>
      </div>
    </motion.div>
  );
}
