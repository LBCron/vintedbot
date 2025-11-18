import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  TrendingUp,
  DollarSign,
  Package,
  Eye,
  ArrowUpRight,
  ArrowDownRight,
  Plus,
  Sparkles,
  Clock,
  Download
} from 'lucide-react';
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell
} from 'recharts';
import { useNavigate } from 'react-router-dom';
import { cn, formatPrice, formatNumber } from '@/lib/utils';
import { bulkAPI } from '@/api/client';
import { logger } from '@/utils/logger';

const COLORS = ['#a855f7', '#3b82f6', '#10b981', '#f59e0b', '#ef4444'];

interface DashboardStats {
  revenue: number;
  revenue_change: number;
  sold_items: number;
  sold_change: number;
  total_views: number;
  views_change: number;
  conversion_rate: number;
  conversion_change: number;
  revenue_chart: Array<{ date: string; revenue: number; views: number }>;
  category_distribution: Array<{ name: string; value: number }>;
  recent_sales: Array<{
    id: number;
    item: string;
    buyer: string;
    price: number;
    time: string;
    image?: string;
  }>;
  top_performers: Array<{
    id: number;
    name: string;
    views: number;
    likes: number;
    sold: boolean;
  }>;
}

export default function Dashboard() {
  const navigate = useNavigate();
  const [timeRange, setTimeRange] = useState('7d');
  const [isLoading, setIsLoading] = useState(true);
  const [stats, setStats] = useState<DashboardStats>({
    revenue: 2847,
    revenue_change: 12.5,
    sold_items: 68,
    sold_change: 8.3,
    total_views: 8421,
    views_change: 23.1,
    conversion_rate: 4.8,
    conversion_change: -2.1,
    revenue_chart: [
      { date: 'Lun', revenue: 320, views: 1200 },
      { date: 'Mar', revenue: 450, views: 1400 },
      { date: 'Mer', revenue: 380, views: 1100 },
      { date: 'Jeu', revenue: 520, views: 1600 },
      { date: 'Ven', revenue: 680, views: 1800 },
      { date: 'Sam', revenue: 720, views: 2000 },
      { date: 'Dim', revenue: 577, views: 1323 },
    ],
    category_distribution: [
      { name: 'Vêtements', value: 45 },
      { name: 'Chaussures', value: 25 },
      { name: 'Accessoires', value: 20 },
      { name: 'Autres', value: 10 },
    ],
    recent_sales: [
      { id: 1, item: "Jean Levi's 501", buyer: 'Sophie M.', price: 35, time: 'Il y a 2h' },
      { id: 2, item: 'T-shirt Nike', buyer: 'Thomas D.', price: 15, time: 'Il y a 5h' },
      { id: 3, item: 'Robe Zara', buyer: 'Marie L.', price: 28, time: 'Il y a 1j' },
      { id: 4, item: 'Sneakers Adidas', buyer: 'Lucas P.', price: 45, time: 'Il y a 1j' },
    ],
    top_performers: [
      { id: 1, name: 'Veste en cuir', views: 342, likes: 45, sold: true },
      { id: 2, name: 'Sac à main Gucci', views: 298, likes: 38, sold: false },
      { id: 3, name: 'Chaussures Louboutin', views: 276, likes: 34, sold: true },
    ]
  });

  useEffect(() => {
    loadStats();
  }, [timeRange]);

  const loadStats = async () => {
    try {
      setIsLoading(true);
      // Load real stats from API
      const response = await bulkAPI.getDrafts({ page: 1, page_size: 100 });
      const drafts = response.data.drafts;

      // Update sold_items with real data
      setStats(prev => ({
        ...prev,
        sold_items: drafts.filter(d => d.status === 'published').length,
      }));
    } catch (error) {
      logger.error('Failed to load stats', error);
    } finally {
      setTimeout(() => setIsLoading(false), 500);
    }
  };

  if (isLoading) {
    return <DashboardSkeleton />;
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header avec gradient */}
      <div className="bg-gradient-to-br from-brand-600 via-brand-500 to-purple-600 text-white">
        <div className="max-w-7xl mx-auto px-6 py-12">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6"
          >
            <div>
              <div className="flex items-center gap-3 mb-2">
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ type: 'spring', delay: 0.2 }}
                >
                  <Sparkles className="w-8 h-8" />
                </motion.div>
                <h1 className="text-4xl font-bold">Dashboard</h1>
              </div>
              <p className="text-brand-100 text-lg">
                Bienvenue ! Voici vos performances en temps réel
              </p>
            </div>

            <div className="flex gap-3">
              <TimeRangeSelector value={timeRange} onChange={setTimeRange} />

              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => navigate('/upload')}
                className="bg-white text-brand-600 px-6 py-3 rounded-xl font-semibold hover:shadow-xl transition-shadow flex items-center gap-2"
              >
                <Plus className="w-5 h-5" />
                Nouveau brouillon
              </motion.button>
            </div>
          </motion.div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 -mt-8 pb-12">
        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <StatCard
            icon={<DollarSign className="w-6 h-6" />}
            label="Revenus"
            value={formatPrice(stats.revenue)}
            change={stats.revenue_change}
            positive={stats.revenue_change > 0}
            color="green"
            delay={0.1}
          />
          <StatCard
            icon={<Package className="w-6 h-6" />}
            label="Articles vendus"
            value={stats.sold_items.toString()}
            change={stats.sold_change}
            positive={stats.sold_change > 0}
            color="blue"
            delay={0.2}
          />
          <StatCard
            icon={<Eye className="w-6 h-6" />}
            label="Vues totales"
            value={formatNumber(stats.total_views)}
            change={stats.views_change}
            positive={stats.views_change > 0}
            color="purple"
            delay={0.3}
          />
          <StatCard
            icon={<TrendingUp className="w-6 h-6" />}
            label="Taux de conversion"
            value={`${stats.conversion_rate}%`}
            change={stats.conversion_change}
            positive={stats.conversion_change > 0}
            color="orange"
            delay={0.4}
          />
        </div>

        {/* Charts Grid */}
        <div className="grid lg:grid-cols-3 gap-6 mb-8">
          {/* Revenue Chart - 2 cols */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5 }}
            className="lg:col-span-2 bg-white rounded-2xl p-6 border border-gray-200 shadow-sm hover:shadow-md transition-shadow"
          >
            <div className="flex justify-between items-center mb-6">
              <div>
                <h3 className="text-lg font-semibold text-gray-900">Revenus & Vues</h3>
                <p className="text-sm text-gray-500">Derniers 7 jours</p>
              </div>
              <button className="text-gray-400 hover:text-gray-600 transition-colors">
                <Download className="w-5 h-5" />
              </button>
            </div>
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={stats.revenue_chart}>
                <defs>
                  <linearGradient id="colorRevenue" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#a855f7" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#a855f7" stopOpacity={0}/>
                  </linearGradient>
                  <linearGradient id="colorViews" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis
                  dataKey="date"
                  stroke="#888"
                  style={{ fontSize: '12px' }}
                  tickLine={false}
                />
                <YAxis
                  stroke="#888"
                  style={{ fontSize: '12px' }}
                  tickLine={false}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'white',
                    border: '1px solid #e5e7eb',
                    borderRadius: '12px',
                    boxShadow: '0 4px 6px rgba(0,0,0,0.1)'
                  }}
                />
                <Area
                  type="monotone"
                  dataKey="revenue"
                  stroke="#a855f7"
                  strokeWidth={3}
                  fill="url(#colorRevenue)"
                  name="Revenus (€)"
                />
                <Area
                  type="monotone"
                  dataKey="views"
                  stroke="#3b82f6"
                  strokeWidth={3}
                  fill="url(#colorViews)"
                  name="Vues"
                />
              </AreaChart>
            </ResponsiveContainer>
          </motion.div>

          {/* Category Distribution - 1 col */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.6 }}
            className="bg-white rounded-2xl p-6 border border-gray-200 shadow-sm hover:shadow-md transition-shadow"
          >
            <h3 className="text-lg font-semibold text-gray-900 mb-6">Ventes par catégorie</h3>
            <ResponsiveContainer width="100%" height={260}>
              <PieChart>
                <Pie
                  data={stats.category_distribution}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={100}
                  paddingAngle={2}
                  dataKey="value"
                >
                  {stats.category_distribution.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
            <div className="mt-4 space-y-2">
              {stats.category_distribution.map((cat, index) => (
                <div key={cat.name} className="flex items-center justify-between text-sm">
                  <div className="flex items-center gap-2">
                    <div
                      className="w-3 h-3 rounded-full"
                      style={{ backgroundColor: COLORS[index] }}
                    />
                    <span className="text-gray-700">{cat.name}</span>
                  </div>
                  <span className="font-semibold text-gray-900">{cat.value}%</span>
                </div>
              ))}
            </div>
          </motion.div>
        </div>

        {/* Recent Activity Grid */}
        <div className="grid lg:grid-cols-2 gap-6">
          {/* Recent Sales */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.7 }}
            className="bg-white rounded-2xl p-6 border border-gray-200 shadow-sm"
          >
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-lg font-semibold text-gray-900">Ventes récentes</h3>
              <button
                onClick={() => navigate('/orders')}
                className="text-sm text-brand-600 hover:text-brand-700 font-medium flex items-center gap-1"
              >
                Voir tout
                <ArrowUpRight className="w-4 h-4" />
              </button>
            </div>
            <div className="space-y-3">
              <AnimatePresence>
                {stats.recent_sales.map((sale, index) => (
                  <motion.div
                    key={sale.id}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.8 + index * 0.1 }}
                    whileHover={{ x: 4 }}
                    className="flex items-center gap-4 p-4 rounded-xl bg-gray-50 hover:bg-gray-100 transition-all cursor-pointer group"
                  >
                    <div className="w-12 h-12 bg-gradient-to-br from-brand-100 to-brand-200 rounded-lg flex items-center justify-center flex-shrink-0">
                      <Package className="w-6 h-6 text-brand-600" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="font-medium text-gray-900 truncate group-hover:text-brand-600 transition-colors">
                        {sale.item}
                      </div>
                      <div className="text-sm text-gray-500 flex items-center gap-2">
                        <span>{sale.buyer}</span>
                        <span>•</span>
                        <span className="flex items-center gap-1">
                          <Clock className="w-3 h-3" />
                          {sale.time}
                        </span>
                      </div>
                    </div>
                    <div className="text-lg font-semibold text-success-600">
                      +{formatPrice(sale.price)}
                    </div>
                  </motion.div>
                ))}
              </AnimatePresence>
            </div>
          </motion.div>

          {/* Top Performers */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.7 }}
            className="bg-white rounded-2xl p-6 border border-gray-200 shadow-sm"
          >
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-lg font-semibold text-gray-900">Top performers</h3>
              <button
                onClick={() => navigate('/drafts')}
                className="text-sm text-brand-600 hover:text-brand-700 font-medium flex items-center gap-1"
              >
                Voir tout
                <ArrowUpRight className="w-4 h-4" />
              </button>
            </div>
            <div className="space-y-3">
              {stats.top_performers.map((item, index) => (
                <motion.div
                  key={item.id}
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.8 + index * 0.1 }}
                  className="flex items-center gap-4 p-4 rounded-xl border border-gray-200 hover:border-brand-200 hover:shadow-md transition-all cursor-pointer"
                >
                  <div className="w-10 h-10 bg-gradient-to-br from-gray-100 to-gray-200 rounded-lg flex items-center justify-center text-xl font-bold text-gray-600">
                    #{index + 1}
                  </div>
                  <div className="flex-1">
                    <div className="font-medium text-gray-900">{item.name}</div>
                    <div className="text-sm text-gray-500 flex items-center gap-3">
                      <span className="flex items-center gap-1">
                        <Eye className="w-3 h-3" />
                        {item.views}
                      </span>
                      <span className="flex items-center gap-1">
                        <TrendingUp className="w-3 h-3" />
                        {item.likes}
                      </span>
                    </div>
                  </div>
                  {item.sold && (
                    <span className="bg-success-100 text-success-700 px-3 py-1 rounded-full text-xs font-semibold">
                      Vendu
                    </span>
                  )}
                </motion.div>
              ))}
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  );
}

// Components
interface StatCardProps {
  icon: React.ReactNode;
  label: string;
  value: string;
  change?: number;
  positive?: boolean;
  color: 'green' | 'blue' | 'purple' | 'orange';
  delay: number;
}

function StatCard({ icon, label, value, change, positive, color, delay }: StatCardProps) {
  const colors = {
    green: {
      bg: 'bg-success-50',
      text: 'text-success-600',
      hover: 'hover:border-success-200'
    },
    blue: {
      bg: 'bg-blue-50',
      text: 'text-blue-600',
      hover: 'hover:border-blue-200'
    },
    purple: {
      bg: 'bg-brand-50',
      text: 'text-brand-600',
      hover: 'hover:border-brand-200'
    },
    orange: {
      bg: 'bg-orange-50',
      text: 'text-orange-600',
      hover: 'hover:border-orange-200'
    }
  };

  const colorClasses = colors[color];

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay }}
      whileHover={{ y: -4, scale: 1.02 }}
      className={cn(
        "bg-white p-6 rounded-2xl border-2 border-gray-200 shadow-sm hover:shadow-lg transition-all cursor-pointer",
        colorClasses.hover
      )}
    >
      <div className="flex items-center justify-between mb-4">
        <div className={cn("p-3 rounded-xl", colorClasses.bg, colorClasses.text)}>
          {icon}
        </div>
        {change !== undefined && (
          <div className={cn(
            "flex items-center gap-1 text-sm font-semibold px-2 py-1 rounded-lg",
            positive ? "text-success-600 bg-success-50" : "text-error-600 bg-error-50"
          )}>
            {positive ? (
              <ArrowUpRight className="w-4 h-4" />
            ) : (
              <ArrowDownRight className="w-4 h-4" />
            )}
            {Math.abs(change)}%
          </div>
        )}
      </div>
      <div className="text-3xl font-bold text-gray-900 mb-1">{value}</div>
      <div className="text-sm text-gray-600">{label}</div>
    </motion.div>
  );
}

interface TimeRangeSelectorProps {
  value: string;
  onChange: (value: string) => void;
}

function TimeRangeSelector({ value, onChange }: TimeRangeSelectorProps) {
  const options = [
    { value: '7d', label: '7 jours' },
    { value: '30d', label: '30 jours' },
    { value: '90d', label: '90 jours' }
  ];

  return (
    <div className="flex bg-white/20 backdrop-blur-sm rounded-xl p-1">
      {options.map(option => (
        <button
          key={option.value}
          onClick={() => onChange(option.value)}
          className={cn(
            "px-4 py-2 rounded-lg text-sm font-medium transition-all",
            value === option.value
              ? "bg-white text-brand-600 shadow-sm"
              : "text-white/80 hover:text-white"
          )}
        >
          {option.label}
        </button>
      ))}
    </div>
  );
}

function DashboardSkeleton() {
  return (
    <div className="min-h-screen bg-gray-50 animate-pulse">
      <div className="bg-gray-200 h-48" />
      <div className="max-w-7xl mx-auto px-6 -mt-8">
        <div className="grid grid-cols-4 gap-6 mb-8">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="bg-white h-32 rounded-2xl" />
          ))}
        </div>
        <div className="grid lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 bg-white h-96 rounded-2xl" />
          <div className="bg-white h-96 rounded-2xl" />
        </div>
      </div>
    </div>
  );
}
