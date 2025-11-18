import { useState } from 'react';
import { motion } from 'framer-motion';
import {
  TrendingUp,
  TrendingDown,
  DollarSign,
  Eye,
  Heart,
  Calendar,
  Download,
  Filter,
  ArrowUpRight,
  Package,
  Users,
  Target,
  Zap
} from 'lucide-react';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend
} from 'recharts';
import { formatPrice, cn } from '../lib/utils';

const COLORS = ['#a855f7', '#3b82f6', '#10b981', '#f59e0b', '#ef4444'];

export default function Analytics() {
  const [timeRange, setTimeRange] = useState('30d');

  const stats = {
    revenue: { value: 4280, change: 12.5, trend: 'up' },
    sales: { value: 156, change: 8.3, trend: 'up' },
    views: { value: 12450, change: -3.2, trend: 'down' },
    conversion: { value: 4.8, change: 1.2, trend: 'up' }
  };

  const revenueData = [
    { date: 'Jan', revenue: 2400, sales: 24 },
    { date: 'Fév', revenue: 1398, sales: 18 },
    { date: 'Mar', revenue: 3800, sales: 32 },
    { date: 'Avr', revenue: 3908, sales: 38 },
    { date: 'Mai', revenue: 4800, sales: 42 },
    { date: 'Jun', revenue: 3800, sales: 35 },
    { date: 'Jul', revenue: 4300, sales: 40 }
  ];

  const categoryData = [
    { name: 'Vêtements', value: 45, revenue: 1890 },
    { name: 'Chaussures', value: 25, revenue: 1050 },
    { name: 'Accessoires', value: 20, revenue: 840 },
    { name: 'Autre', value: 10, revenue: 420 }
  ];

  const topItems = [
    { name: "Jean Levi's 501", views: 342, sales: 12, revenue: 420 },
    { name: 'Nike Air Max', views: 298, sales: 10, revenue: 450 },
    { name: 'Robe Zara', views: 276, sales: 8, revenue: 224 },
    { name: 'Sac Gucci', views: 234, sales: 6, revenue: 540 },
    { name: 'Veste en cuir', views: 198, sales: 5, revenue: 375 }
  ];

  const performanceData = [
    { hour: '00h', views: 45, sales: 2 },
    { hour: '04h', views: 23, sales: 1 },
    { hour: '08h', views: 89, sales: 4 },
    { hour: '12h', views: 156, sales: 8 },
    { hour: '16h', views: 198, sales: 10 },
    { hour: '20h', views: 234, sales: 12 },
    { hour: '23h', views: 89, sales: 3 }
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-6 py-6">
          <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 mb-1">Analytics</h1>
              <p className="text-gray-600">Analysez vos performances en détail</p>
            </div>

            <div className="flex items-center gap-3">
              <TimeRangeSelector value={timeRange} onChange={setTimeRange} />
              <button className="btn btn-secondary flex items-center gap-2">
                <Download className="w-5 h-5" />
                Exporter
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* KPI Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <KPICard
            icon={<DollarSign className="w-6 h-6" />}
            label="Revenus"
            value={formatPrice(stats.revenue.value)}
            change={stats.revenue.change}
            trend={stats.revenue.trend}
            color="green"
          />
          <KPICard
            icon={<Package className="w-6 h-6" />}
            label="Ventes"
            value={stats.sales.value}
            change={stats.sales.change}
            trend={stats.sales.trend}
            color="blue"
          />
          <KPICard
            icon={<Eye className="w-6 h-6" />}
            label="Vues"
            value={stats.views.value.toLocaleString()}
            change={stats.views.change}
            trend={stats.views.trend}
            color="purple"
          />
          <KPICard
            icon={<Target className="w-6 h-6" />}
            label="Conversion"
            value={`${stats.conversion.value}%`}
            change={stats.conversion.change}
            trend={stats.conversion.trend}
            color="orange"
          />
        </div>

        {/* Charts Grid */}
        <div className="grid lg:grid-cols-3 gap-6 mb-8">
          {/* Revenue Chart - Large */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="lg:col-span-2 bg-white rounded-2xl p-6 border border-gray-200 shadow-sm"
          >
            <div className="flex justify-between items-center mb-6">
              <div>
                <h3 className="text-lg font-semibold text-gray-900">Évolution des revenus</h3>
                <p className="text-sm text-gray-500">Derniers 6 mois</p>
              </div>
            </div>
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={revenueData}>
                <defs>
                  <linearGradient id="colorRevenue" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#a855f7" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#a855f7" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="date" stroke="#888" style={{ fontSize: '12px' }} />
                <YAxis stroke="#888" style={{ fontSize: '12px' }} />
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
              </AreaChart>
            </ResponsiveContainer>
          </motion.div>

          {/* Category Distribution */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="bg-white rounded-2xl p-6 border border-gray-200 shadow-sm"
          >
            <h3 className="text-lg font-semibold text-gray-900 mb-6">Par catégorie</h3>
            <ResponsiveContainer width="100%" height={240}>
              <PieChart>
                <Pie
                  data={categoryData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={90}
                  paddingAngle={2}
                  dataKey="value"
                >
                  {categoryData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
            <div className="space-y-2 mt-4">
              {categoryData.map((cat, index) => (
                <div key={cat.name} className="flex items-center justify-between text-sm">
                  <div className="flex items-center gap-2">
                    <div
                      className="w-3 h-3 rounded-full"
                      style={{ backgroundColor: COLORS[index] }}
                    />
                    <span className="text-gray-700">{cat.name}</span>
                  </div>
                  <span className="font-semibold text-gray-900">{formatPrice(cat.revenue)}</span>
                </div>
              ))}
            </div>
          </motion.div>
        </div>

        {/* Performance by Time */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="bg-white rounded-2xl p-6 border border-gray-200 shadow-sm mb-8"
        >
          <div className="flex items-center gap-2 mb-6">
            <Zap className="w-5 h-5 text-brand-600" />
            <h3 className="text-lg font-semibold text-gray-900">Performance par heure</h3>
          </div>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={performanceData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="hour" stroke="#888" style={{ fontSize: '12px' }} />
              <YAxis stroke="#888" style={{ fontSize: '12px' }} />
              <Tooltip />
              <Bar dataKey="views" fill="#a855f7" radius={[8, 8, 0, 0]} name="Vues" />
              <Bar dataKey="sales" fill="#3b82f6" radius={[8, 8, 0, 0]} name="Ventes" />
            </BarChart>
          </ResponsiveContainer>
        </motion.div>

        {/* Top Performers */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="bg-white rounded-2xl p-6 border border-gray-200 shadow-sm"
        >
          <div className="flex justify-between items-center mb-6">
            <h3 className="text-lg font-semibold text-gray-900">Top 5 articles</h3>
            <button className="text-sm text-brand-600 hover:text-brand-700 font-medium flex items-center gap-1">
              Voir tout
              <ArrowUpRight className="w-4 h-4" />
            </button>
          </div>
          <div className="space-y-3">
            {topItems.map((item, index) => (
              <div
                key={item.name}
                className="flex items-center gap-4 p-4 rounded-xl bg-gray-50 hover:bg-gray-100 transition-colors"
              >
                <div className="w-10 h-10 bg-gradient-to-br from-brand-100 to-brand-200 rounded-lg flex items-center justify-center text-brand-700 font-bold">
                  #{index + 1}
                </div>
                <div className="flex-1">
                  <h4 className="font-medium text-gray-900">{item.name}</h4>
                  <div className="flex items-center gap-4 text-sm text-gray-500 mt-1">
                    <span className="flex items-center gap-1">
                      <Eye className="w-3 h-3" />
                      {item.views}
                    </span>
                    <span className="flex items-center gap-1">
                      <Package className="w-3 h-3" />
                      {item.sales} ventes
                    </span>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-lg font-bold text-gray-900">
                    {formatPrice(item.revenue)}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </motion.div>

        {/* AI Insights */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="mt-8 bg-gradient-to-br from-brand-50 to-purple-50 rounded-2xl p-8 border border-brand-200"
        >
          <div className="flex items-start gap-4">
            <div className="w-12 h-12 bg-white rounded-xl shadow-sm flex items-center justify-center">
              <TrendingUp className="w-6 h-6 text-brand-600" />
            </div>
            <div className="flex-1">
              <h3 className="text-lg font-semibold text-gray-900 mb-3">Insights IA</h3>
              <div className="grid md:grid-cols-2 gap-3">
                <InsightCard
                  text="Vos articles se vendent 23% plus vite entre 18h et 21h"
                  positive
                />
                <InsightCard
                  text="Les prix entre 25€ et 45€ ont le meilleur taux de conversion"
                  positive
                />
                <InsightCard
                  text="Ajoutez 2-3 photos supplémentaires pour +15% de vues"
                />
                <InsightCard
                  text="Catégorie 'Chaussures' en forte croissance ce mois-ci"
                  positive
                />
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  );
}

function KPICard({ icon, label, value, change, trend, color }: any) {
  const colors: any = {
    green: 'bg-success-50 text-success-600',
    blue: 'bg-blue-50 text-blue-600',
    purple: 'bg-brand-50 text-brand-600',
    orange: 'bg-orange-50 text-orange-600'
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ y: -4 }}
      className="bg-white rounded-2xl p-6 border border-gray-200 hover:border-brand-200 hover:shadow-lg transition-all"
    >
      <div className="flex items-center justify-between mb-4">
        <div className={cn("p-3 rounded-xl", colors[color])}>
          {icon}
        </div>
        <div className={cn(
          "flex items-center gap-1 text-sm font-semibold px-2 py-1 rounded-lg",
          trend === 'up' ? "text-success-600 bg-success-50" : "text-error-600 bg-error-50"
        )}>
          {trend === 'up' ? (
            <TrendingUp className="w-4 h-4" />
          ) : (
            <TrendingDown className="w-4 h-4" />
          )}
          {Math.abs(change)}%
        </div>
      </div>
      <div className="text-3xl font-bold text-gray-900 mb-1">{value}</div>
      <div className="text-sm text-gray-600">{label}</div>
    </motion.div>
  );
}

function TimeRangeSelector({ value, onChange }: any) {
  const options = [
    { value: '7d', label: '7j' },
    { value: '30d', label: '30j' },
    { value: '90d', label: '90j' },
    { value: '1y', label: '1an' }
  ];

  return (
    <div className="flex bg-gray-100 rounded-xl p-1">
      {options.map(option => (
        <button
          key={option.value}
          onClick={() => onChange(option.value)}
          className={cn(
            "px-4 py-2 rounded-lg text-sm font-medium transition-all",
            value === option.value
              ? "bg-white shadow-sm text-brand-600"
              : "text-gray-600 hover:text-gray-900"
          )}
        >
          {option.label}
        </button>
      ))}
    </div>
  );
}

function InsightCard({ text, positive }: any) {
  return (
    <div className="flex items-start gap-2 bg-white rounded-lg p-3 border border-brand-100">
      <div className={cn(
        "w-2 h-2 rounded-full mt-1.5 flex-shrink-0",
        positive ? "bg-success-500" : "bg-brand-500"
      )} />
      <p className="text-sm text-gray-700">{text}</p>
    </div>
  );
}
