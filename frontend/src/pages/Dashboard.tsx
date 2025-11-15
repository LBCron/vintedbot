import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  Upload,
  FileText,
  BarChart3,
  Zap,
  Brain,
  HardDrive,
  Package,
  DollarSign,
  ShoppingBag,
  TrendingUp,
  ArrowRight
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { bulkAPI } from '../api/client';
import { StatCard } from '../components/ui/StatCard';
import { QuotaCard } from '../components/ui/QuotaCard';
import { AnimatedNumber } from '../components/ui/AnimatedNumber';
import { GlassCard } from '../components/ui/GlassCard';
import { Badge } from '../components/ui/Badge';
import DraftsTimelineChart from '../components/features/charts/DraftsTimelineChart';
import CategoryBarChart from '../components/features/charts/CategoryBarChart';
import StatusPieChart from '../components/features/charts/StatusPieChart';
import { logger } from '../utils/logger';

export default function Dashboard() {
  const { user } = useAuth();
  const [stats, setStats] = useState({
    totalDrafts: 0,
    readyDrafts: 0,
    publishedDrafts: 0,
    revenue: 0
  });
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
        revenue: 0 // TODO: Calculate from orders
      });
    } catch (error) {
      logger.error('Failed to load stats', error);
      setStats({
        totalDrafts: 0,
        readyDrafts: 0,
        publishedDrafts: 0,
        revenue: 0
      });
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 p-8">
        <div className="max-w-7xl mx-auto space-y-8">
          {/* Loading Skeletons */}
          <div className="space-y-4">
            <div className="h-12 w-64 bg-white/5 rounded-xl animate-pulse" />
            <div className="h-6 w-96 bg-white/5 rounded-xl animate-pulse" />
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-32 bg-white/5 rounded-2xl animate-pulse" />
            ))}
          </div>
        </div>
      </div>
    );
  }

  const quickActions = [
    {
      to: '/upload',
      title: 'Upload Photos',
      subtitle: 'AI-powered analysis',
      description: 'Upload and analyze your product photos instantly',
      icon: Upload,
      gradient: 'from-violet-500 to-purple-600',
      badge: 'New'
    },
    {
      to: '/drafts',
      title: 'Manage Drafts',
      subtitle: `${stats.readyDrafts} ready`,
      description: 'Review and edit your AI-generated listings',
      icon: FileText,
      gradient: 'from-blue-500 to-cyan-600',
      badge: stats.readyDrafts > 0 ? `${stats.readyDrafts}` : null
    },
    {
      to: '/analytics',
      title: 'Analytics',
      subtitle: 'Performance insights',
      description: 'Track your sales and optimize listings',
      icon: TrendingUp,
      gradient: 'from-green-500 to-emerald-600'
    },
    {
      to: '/automation',
      title: 'Automation',
      subtitle: 'Schedule & automate',
      description: 'Set up automated publishing workflows',
      icon: Zap,
      gradient: 'from-orange-500 to-red-600',
      badge: 'Pro'
    }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      <div className="max-w-7xl mx-auto p-4 md:p-6 lg:p-8 space-y-8">
        {/* Header */}
        <motion.div
          className="space-y-2"
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <h1 className="text-4xl md:text-5xl font-bold bg-gradient-to-r from-white via-violet-200 to-purple-200 bg-clip-text text-transparent">
            Dashboard
          </h1>
          <p className="text-lg text-slate-400">
            Welcome back, <span className="text-violet-400 font-semibold">{user?.name || 'User'}</span>!
          </p>
        </motion.div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <StatCard
            icon={Package}
            label="Total Drafts"
            value={<AnimatedNumber value={stats.totalDrafts} />}
            trend={{ value: "+12%", direction: "up" }}
          />
          <StatCard
            icon={FileText}
            label="Ready to Publish"
            value={<AnimatedNumber value={stats.readyDrafts} />}
            trend={{ value: "+25%", direction: "up" }}
          />
          <StatCard
            icon={ShoppingBag}
            label="Published"
            value={<AnimatedNumber value={stats.publishedDrafts} />}
            trend={{ value: "+8%", direction: "up" }}
          />
          <StatCard
            icon={DollarSign}
            label="Revenue"
            value={`${stats.revenue}€`}
            trend={{ value: "+0%", direction: "up" }}
          />
        </div>

        {/* Quotas with Circular Progress */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.2 }}
        >
          <h2 className="text-2xl font-bold text-white mb-6">Your Quotas</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <QuotaCard
              icon={Brain}
              label="AI Analyses"
              used={user?.quotas_used?.ai_analyses_month || 0}
              total={user?.quotas_limit?.ai_analyses_month || 20}
              color="violet"
            />
            <QuotaCard
              icon={FileText}
              label="Drafts"
              used={user?.quotas_used?.drafts || 0}
              total={user?.quotas_limit?.drafts || 50}
              color="blue"
            />
            <QuotaCard
              icon={Upload}
              label="Publications"
              used={user?.quotas_used?.publications_month || 0}
              total={user?.quotas_limit?.publications_month || 10}
              color="green"
            />
            <QuotaCard
              icon={HardDrive}
              label="Storage"
              used={Math.round(user?.quotas_used?.photos_storage_mb || 0)}
              total={user?.quotas_limit?.photos_storage_mb || 500}
              unit="MB"
              color="orange"
            />
          </div>
        </motion.div>

        {/* Charts Section */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3 }}
          className="space-y-6"
        >
          <h2 className="text-2xl font-bold text-white">Performance Analytics</h2>
          <DraftsTimelineChart />
        </motion.div>

        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.4 }}
          className="grid grid-cols-1 md:grid-cols-2 gap-6"
        >
          <CategoryBarChart />
          <StatusPieChart />
        </motion.div>

        {/* Quick Actions */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
          className="space-y-6"
        >
          <h2 className="text-2xl font-bold text-white">Quick Actions</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {quickActions.map((action, index) => (
              <Link key={action.to} to={action.to}>
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.5 + index * 0.1 }}
                >
                  <GlassCard
                    hover
                    className="relative overflow-hidden p-6 h-full group"
                  >
                    {/* Gradient Background on Hover */}
                    <div className={`absolute inset-0 bg-gradient-to-br ${action.gradient} opacity-0 group-hover:opacity-10 transition-opacity duration-300`} />

                    {/* Badge */}
                    {action.badge && (
                      <div className="absolute top-4 right-4">
                        <Badge variant="default" size="sm">{action.badge}</Badge>
                      </div>
                    )}

                    {/* Icon */}
                    <div className={`inline-flex p-3 rounded-xl bg-gradient-to-br ${action.gradient} bg-opacity-20 mb-4`}>
                      <action.icon className="w-6 h-6 text-white" />
                    </div>

                    {/* Content */}
                    <h3 className="text-lg font-bold text-white mb-2 group-hover:text-violet-300 transition-colors">
                      {action.title}
                    </h3>
                    <p className="text-sm text-violet-400 font-medium mb-2">
                      {action.subtitle}
                    </p>
                    <p className="text-xs text-slate-400 mb-4">
                      {action.description}
                    </p>

                    {/* Arrow Icon */}
                    <div className="flex items-center text-violet-400 text-sm font-semibold group-hover:translate-x-1 transition-transform">
                      Get started
                      <ArrowRight className="w-4 h-4 ml-1" />
                    </div>
                  </GlassCard>
                </motion.div>
              </Link>
            ))}
          </div>
        </motion.div>

        {/* Subscription Status */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.6 }}
        >
          <GlassCard className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold text-white mb-1">
                  Current Plan: <span className="text-violet-400">{user?.plan?.toUpperCase() || 'FREE'}</span>
                </h3>
                <p className="text-slate-400 text-sm">
                  {user?.plan === 'free'
                    ? 'Upgrade to unlock more features and higher quotas'
                    : 'You have access to all premium features'}
                </p>
              </div>
              {user?.plan === 'free' && (
                <Link to="/settings">
                  <motion.button
                    className="px-6 py-3 bg-gradient-to-r from-violet-500 to-purple-600 text-white rounded-xl font-semibold shadow-lg shadow-violet-500/30"
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                  >
                    Upgrade Now
                  </motion.button>
                </Link>
              )}
            </div>
          </GlassCard>
        </motion.div>
      </div>
    </div>
  );
}
