import { useState, useEffect, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Upload, FileText, BarChart3, Zap } from 'lucide-react';
import Skeleton from 'react-loading-skeleton';
import 'react-loading-skeleton/dist/skeleton.css';
import { useAuth } from '../contexts/AuthContext';
import { bulkAPI } from '../api/client';
import StatsCard from '../components/common/StatsCard';
import QuotaCard from '../components/common/QuotaCard';
import DraftsTimelineChart from '../components/features/charts/DraftsTimelineChart';
import CategoryBarChart from '../components/features/charts/CategoryBarChart';
import StatusPieChart from '../components/features/charts/StatusPieChart';
import { logger } from '../utils/logger';

export default function Dashboard() {
  const { user } = useAuth();
  const [stats, setStats] = useState({ totalDrafts: 0, readyDrafts: 0, publishedDrafts: 0 });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadStats();
  }, []); // Load dashboard stats on mount

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
      // Continue with default stats on error
      setStats({
        totalDrafts: 0,
        readyDrafts: 0,
        publishedDrafts: 0,
      });
    } finally {
      setLoading(false);
    }
  };

  const quickActions = useMemo(() => [
    {
      to: '/upload',
      title: 'Upload Photos',
      subtitle: 'AI-powered bulk analysis',
      description: 'Upload and analyze your product photos instantly',
      icon: Upload,
      bgColor: 'bg-primary-50 dark:bg-primary-900/20',
      iconColor: 'text-primary-600 dark:text-primary-400',
      hoverBg: 'hover:bg-primary-100 dark:hover:bg-primary-900/40',
      badge: 'New'
    },
    {
      to: '/drafts',
      title: 'Manage Drafts',
      subtitle: `${stats.readyDrafts} ready to publish`,
      description: 'Review and edit your AI-generated listings',
      icon: FileText,
      bgColor: 'bg-success-50 dark:bg-success-900/20',
      iconColor: 'text-success-600 dark:text-success-400',
      hoverBg: 'hover:bg-success-100 dark:hover:bg-success-900/40',
      badge: stats.readyDrafts > 0 ? `${stats.readyDrafts}` : null
    },
    {
      to: '/analytics',
      title: 'Analytics',
      subtitle: 'Performance insights',
      description: 'Track your sales and optimize listings',
      icon: BarChart3,
      bgColor: 'bg-purple-50 dark:bg-purple-900/20',
      iconColor: 'text-purple-600 dark:text-purple-400',
      hoverBg: 'hover:bg-purple-100 dark:hover:bg-purple-900/40'
    },
    {
      to: '/automation',
      title: 'Automation',
      subtitle: 'Schedule & automate',
      description: 'Set up automated publishing workflows',
      icon: Zap,
      bgColor: 'bg-warning-50 dark:bg-warning-900/20',
      iconColor: 'text-warning-600 dark:text-warning-400',
      hoverBg: 'hover:bg-warning-100 dark:hover:bg-warning-900/40',
      badge: 'Pro'
    }
  ], [stats.readyDrafts]);

  if (loading) {
    return (
      <div className="space-y-8">
        <div>
          <Skeleton width={200} height={36} className="mb-2" />
          <Skeleton width={300} height={24} />
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {[...Array(4)].map((_, i) => (
            <Skeleton key={i} height={120} />
          ))}
        </div>
        <div>
          <Skeleton width={150} height={28} className="mb-4" />
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {[...Array(4)].map((_, i) => (
              <Skeleton key={i} height={100} />
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">📊 Dashboard</h1>
        <p className="text-gray-600 dark:text-gray-400 mt-2">Welcome back, {user?.name}!</p>
      </motion.div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatsCard
          title="Total Drafts"
          value={stats.totalDrafts}
          icon={FileText}
          trend={12}
        />
        <StatsCard
          title="Ready to Publish"
          value={stats.readyDrafts}
          icon={Zap}
          trend={25}
        />
        <StatsCard
          title="Published"
          value={stats.publishedDrafts}
          icon={BarChart3}
          trend={8}
        />
        <StatsCard
          title="Subscription"
          value={user?.plan.toUpperCase() || 'FREE'}
          subtitle="Current plan"
          icon={BarChart3}
        />
      </div>

      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.2 }}
      >
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">Your Quotas</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <QuotaCard
            label="AI Analyses"
            used={user?.quotas_used.ai_analyses_month || 0}
            limit={user?.quotas_limit.ai_analyses_month || 0}
            icon={<BarChart3 className="w-5 h-5 text-primary-600 dark:text-primary-400" />}
          />
          <QuotaCard
            label="Drafts"
            used={user?.quotas_used.drafts || 0}
            limit={user?.quotas_limit.drafts || 0}
            icon={<FileText className="w-5 h-5 text-primary-600 dark:text-primary-400" />}
          />
          <QuotaCard
            label="Publications"
            used={user?.quotas_used.publications_month || 0}
            limit={user?.quotas_limit.publications_month || 0}
            icon={<Upload className="w-5 h-5 text-primary-600 dark:text-primary-400" />}
          />
          <QuotaCard
            label="Storage"
            used={Math.round(user?.quotas_used.photos_storage_mb || 0)}
            limit={user?.quotas_limit.photos_storage_mb || 0}
            unit="MB"
            icon={<BarChart3 className="w-5 h-5 text-primary-600 dark:text-primary-400" />}
          />
        </div>
      </motion.div>

      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.3 }}
      >
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

      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.5 }}
      >
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {quickActions.map((action, index) => (
            <Link
              key={action.to}
              to={action.to}
              className="relative group"
            >
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.5 + index * 0.1 }}
                className={`card p-6 ${action.hoverBg} transition-all hover:shadow-premium cursor-pointer`}
              >
                {action.badge && (
                  <div className="absolute top-4 right-4">
                    <span className="px-2 py-1 text-xs font-semibold rounded-full bg-primary-100 text-primary-700 dark:bg-primary-900/30 dark:text-primary-300">
                      {action.badge}
                    </span>
                  </div>
                )}
                <div className={`inline-flex p-3 ${action.bgColor} rounded-xl mb-4`}>
                  <action.icon className={`w-6 h-6 ${action.iconColor}`} />
                </div>
                <h3 className="font-semibold text-gray-900 dark:text-white mb-1">
                  {action.title}
                </h3>
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                  {action.subtitle}
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-500">
                  {action.description}
                </p>
              </motion.div>
            </Link>
          ))}
        </div>
      </motion.div>
    </div>
  );
}
