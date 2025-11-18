import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  Upload,
  FileText,
  BarChart3,
  Zap,
  TrendingUp,
  TrendingDown,
  ShoppingBag,
  Euro,
  Eye,
  Sparkles,
  ArrowRight,
} from 'lucide-react';
import { AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { useAuth } from '../contexts/AuthContext';
import { bulkAPI } from '../api/client';
import Card, { CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/Card';
import Button from '../components/ui/Button';
import { logger } from '../utils/logger';

// Mock data for revenue chart
const revenueData = [
  { month: 'Jan', revenue: 1200, sales: 45 },
  { month: 'Fév', revenue: 1900, sales: 67 },
  { month: 'Mar', revenue: 1600, sales: 52 },
  { month: 'Avr', revenue: 2400, sales: 89 },
  { month: 'Mai', revenue: 2100, sales: 75 },
  { month: 'Jun', revenue: 2800, sales: 98 },
];

// Mock data for recent activity
const recentSales = [
  { id: 1, item: 'Nike Air Max 90', price: 85, time: 'Il y a 2h', status: 'completed' },
  { id: 2, item: 'Zara Leather Jacket', price: 45, time: 'Il y a 5h', status: 'pending' },
  { id: 3, item: 'Adidas Ultraboost', price: 120, time: 'Il y a 1j', status: 'completed' },
  { id: 4, item: 'H&M Summer Dress', price: 25, time: 'Il y a 1j', status: 'completed' },
];

export default function Dashboard() {
  const { user } = useAuth();
  const [stats, setStats] = useState({ totalDrafts: 0, readyDrafts: 0, publishedDrafts: 0 });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      const response = await bulkAPI.getDrafts({ page: 1, page_size: 100 });
      const drafts = response.data.drafts;

      setStats({
        totalDrafts: drafts.length,
        readyDrafts: drafts.filter(d => d.status === 'ready').length,
        publishedDrafts: drafts.filter(d => d.status === 'published').length,
      });
    } catch (error) {
      logger.error('Failed to load stats', error);
      setStats({ totalDrafts: 0, readyDrafts: 0, publishedDrafts: 0 });
    } finally {
      setLoading(false);
    }
  };

  const mainStats = [
    {
      title: 'Revenus totaux',
      value: '2,847€',
      change: '+12.5%',
      trend: 'up',
      icon: Euro,
      iconBg: 'bg-success-100',
      iconColor: 'text-success-600',
    },
    {
      title: 'Annonces publiées',
      value: stats.publishedDrafts.toString(),
      change: '+8.2%',
      trend: 'up',
      icon: ShoppingBag,
      iconBg: 'bg-primary-100',
      iconColor: 'text-primary-600',
    },
    {
      title: 'Vues totales',
      value: '12,847',
      change: '+23.1%',
      trend: 'up',
      icon: Eye,
      iconBg: 'bg-purple-100',
      iconColor: 'text-purple-600',
    },
    {
      title: 'Taux de conversion',
      value: '18.4%',
      change: '-2.3%',
      trend: 'down',
      icon: TrendingUp,
      iconBg: 'bg-warning-100',
      iconColor: 'text-warning-600',
    },
  ];

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-48 mb-2"></div>
          <div className="h-4 bg-gray-200 rounded w-64"></div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-32 bg-gray-200 rounded-xl animate-pulse"></div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
      >
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
          Tableau de bord
        </h1>
        <p className="text-gray-600 dark:text-gray-400">
          Bienvenue, {user?.name}! Voici un aperçu de vos performances.
        </p>
      </motion.div>

      {/* Main Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {mainStats.map((stat, index) => (
          <motion.div
            key={stat.title}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
          >
            <Card>
              <CardContent className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <div className={`p-3 rounded-lg ${stat.iconBg}`}>
                    <stat.icon className={`w-6 h-6 ${stat.iconColor}`} />
                  </div>
                  <div className={`flex items-center text-sm font-semibold ${
                    stat.trend === 'up' ? 'text-success-600' : 'text-error-600'
                  }`}>
                    {stat.trend === 'up' ? (
                      <TrendingUp className="w-4 h-4 mr-1" />
                    ) : (
                      <TrendingDown className="w-4 h-4 mr-1" />
                    )}
                    {stat.change}
                  </div>
                </div>
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">
                    {stat.title}
                  </p>
                  <p className="text-2xl font-bold text-gray-900 dark:text-white">
                    {stat.value}
                  </p>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Revenue Chart */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.4 }}
        >
          <Card>
            <CardHeader>
              <CardTitle>Revenus mensuels</CardTitle>
              <CardDescription>
                Évolution de vos ventes sur les 6 derniers mois
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={250}>
                <AreaChart data={revenueData}>
                  <defs>
                    <linearGradient id="colorRevenue" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis dataKey="month" stroke="#6b7280" />
                  <YAxis stroke="#6b7280" />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: 'white',
                      border: '1px solid #e5e7eb',
                      borderRadius: '8px',
                    }}
                  />
                  <Area
                    type="monotone"
                    dataKey="revenue"
                    stroke="#6366f1"
                    strokeWidth={2}
                    fillOpacity={1}
                    fill="url(#colorRevenue)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </motion.div>

        {/* Sales Chart */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.5 }}
        >
          <Card>
            <CardHeader>
              <CardTitle>Nombre de ventes</CardTitle>
              <CardDescription>
                Ventes par mois sur les 6 derniers mois
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={revenueData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis dataKey="month" stroke="#6b7280" />
                  <YAxis stroke="#6b7280" />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: 'white',
                      border: '1px solid #e5e7eb',
                      borderRadius: '8px',
                    }}
                  />
                  <Bar dataKey="sales" fill="#22c55e" radius={[8, 8, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* Recent Sales & AI Insights */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Sales */}
        <motion.div
          className="lg:col-span-2"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
        >
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Ventes récentes</CardTitle>
                  <CardDescription>
                    Vos dernières transactions
                  </CardDescription>
                </div>
                <Link to="/analytics">
                  <Button variant="ghost" size="sm">
                    Voir tout
                    <ArrowRight className="ml-2 w-4 h-4" />
                  </Button>
                </Link>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {recentSales.map((sale, index) => (
                  <motion.div
                    key={sale.id}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.7 + index * 0.1 }}
                    className="flex items-center justify-between p-4 rounded-lg bg-gray-50 dark:bg-gray-800 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                  >
                    <div className="flex items-center space-x-4">
                      <div className="w-10 h-10 bg-primary-100 rounded-lg flex items-center justify-center">
                        <ShoppingBag className="w-5 h-5 text-primary-600" />
                      </div>
                      <div>
                        <p className="font-medium text-gray-900 dark:text-white">
                          {sale.item}
                        </p>
                        <p className="text-sm text-gray-600 dark:text-gray-400">
                          {sale.time}
                        </p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="font-bold text-gray-900 dark:text-white">
                        {sale.price}€
                      </p>
                      <span className={`text-xs px-2 py-1 rounded-full ${
                        sale.status === 'completed'
                          ? 'bg-success-100 text-success-700'
                          : 'bg-warning-100 text-warning-700'
                      }`}>
                        {sale.status === 'completed' ? 'Terminé' : 'En cours'}
                      </span>
                    </div>
                  </motion.div>
                ))}
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* AI Insights */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.7 }}
        >
          <Card variant="glass" className="border-primary-200">
            <CardHeader>
              <div className="flex items-center space-x-2 mb-2">
                <Sparkles className="w-5 h-5 text-primary-600" />
                <CardTitle className="text-lg">Insights IA</CardTitle>
              </div>
              <CardDescription>
                Recommandations personnalisées
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="p-4 rounded-lg bg-primary-50 dark:bg-primary-900/20">
                  <p className="text-sm font-medium text-gray-900 dark:text-white mb-2">
                    <Zap className="w-4 h-4 inline mr-1" /> Meilleur moment pour publier
                  </p>
                  <p className="text-xs text-gray-600 dark:text-gray-400">
                    Publiez entre 18h-20h pour +35% de vues
                  </p>
                </div>

                <div className="p-4 rounded-lg bg-success-50 dark:bg-success-900/20">
                  <p className="text-sm font-medium text-gray-900 dark:text-white mb-2">
                    <TrendingUp className="w-4 h-4 inline mr-1" /> Catégorie en hausse
                  </p>
                  <p className="text-xs text-gray-600 dark:text-gray-400">
                    Les sneakers se vendent 2x plus vite
                  </p>
                </div>

                <div className="p-4 rounded-lg bg-warning-50 dark:bg-warning-900/20">
                  <p className="text-sm font-medium text-gray-900 dark:text-white mb-2">
                    <Sparkles className="w-4 h-4 inline mr-1" /> Optimisez vos prix
                  </p>
                  <p className="text-xs text-gray-600 dark:text-gray-400">
                    Baissez de 10% pour vendre 3 articles
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* Quick Actions */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.8 }}
      >
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
          Actions rapides
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[
            {
              to: '/upload',
              title: 'Upload Photos',
              subtitle: `${stats.readyDrafts} brouillons prêts`,
              icon: Upload,
              iconBg: 'bg-primary-100',
              iconColor: 'text-primary-600',
            },
            {
              to: '/drafts',
              title: 'Gérer Brouillons',
              subtitle: `${stats.totalDrafts} au total`,
              icon: FileText,
              iconBg: 'bg-success-100',
              iconColor: 'text-success-600',
            },
            {
              to: '/analytics',
              title: 'Analytics',
              subtitle: 'Voir les stats',
              icon: BarChart3,
              iconBg: 'bg-purple-100',
              iconColor: 'text-purple-600',
            },
            {
              to: '/automation',
              title: 'Automation',
              subtitle: 'Configurer',
              icon: Zap,
              iconBg: 'bg-warning-100',
              iconColor: 'text-warning-600',
            },
          ].map((action, index) => (
            <Link key={action.to} to={action.to}>
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.9 + index * 0.1 }}
              >
                <Card hoverable>
                  <CardContent className="p-6">
                    <div className={`w-12 h-12 ${action.iconBg} rounded-lg flex items-center justify-center mb-4`}>
                      <action.icon className={`w-6 h-6 ${action.iconColor}`} />
                    </div>
                    <h3 className="font-semibold text-gray-900 dark:text-white mb-1">
                      {action.title}
                    </h3>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      {action.subtitle}
                    </p>
                  </CardContent>
                </Card>
              </motion.div>
            </Link>
          ))}
        </div>
      </motion.div>
    </div>
  );
}
