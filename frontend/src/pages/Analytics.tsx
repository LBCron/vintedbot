import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Eye, Heart, MessageCircle, TrendingUp, Calendar, Award, TrendingDown, BarChart3, Sparkles } from 'lucide-react';
import { analyticsAPI } from '../api/client';
import { StatCard } from '../components/ui/StatCard';
import { GlassCard } from '../components/ui/GlassCard';
import { AnimatedNumber } from '../components/ui/AnimatedNumber';
import { Badge } from '../components/ui/Badge';
import { EmptyState } from '../components/ui/EmptyState';
import HeatmapChart from '../components/common/HeatmapChart';
import MLPredictions from '../components/analytics/MLPredictions';
import type { AnalyticsResponse } from '../types';
import { logger } from '../utils/logger';

export default function Analytics() {
  const [data, setData] = useState<AnalyticsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [days, setDays] = useState(30);

  useEffect(() => {
    loadAnalytics();
  }, [days]);

  const loadAnalytics = async () => {
    try {
      const response = await analyticsAPI.getDashboard(days);
      setData(response.data);
    } catch (error) {
      logger.error('Failed to load analytics', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
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
              <p className="text-slate-400">Loading analytics...</p>
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
          className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4"
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <div>
            <h1 className="text-4xl md:text-5xl font-bold bg-gradient-to-r from-white via-violet-200 to-purple-200 bg-clip-text text-transparent">
              Analytics Dashboard
            </h1>
            <div className="flex items-center gap-2 mt-2">
              <Badge variant="success" size="md">
                PREMIUM FEATURE
              </Badge>
              <p className="text-slate-400">
                Performance insights for your listings
              </p>
            </div>
          </div>

          {/* Time Range Selector */}
          <select
            value={days}
            onChange={(e) => setDays(Number(e.target.value))}
            className="px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white focus:outline-none focus:border-violet-500/50 focus:bg-white/10 transition-all max-w-xs"
          >
            <option value={7}>Last 7 days</option>
            <option value={30}>Last 30 days</option>
            <option value={90}>Last 90 days</option>
          </select>
        </motion.div>

        {data ? (
          <>
            {/* ML Predictions Section */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
            >
              <GlassCard className="p-6 mb-8">
                <div className="flex items-center gap-3 mb-4">
                  <Sparkles className="w-6 h-6 text-violet-400" />
                  <h2 className="text-2xl font-bold text-white">
                    AI-Powered Predictions
                  </h2>
                  <Badge variant="success" size="sm">
                    ML
                  </Badge>
                </div>
                <MLPredictions />
              </GlassCard>
            </motion.div>

            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <StatCard
                icon={Eye}
                label="Total Views"
                value={<AnimatedNumber value={data.dashboard.total_views} />}
                trend={{ value: "+12%", direction: "up" }}
              />
              <StatCard
                icon={Heart}
                label="Total Likes"
                value={<AnimatedNumber value={data.dashboard.total_likes} />}
                trend={{ value: "+8%", direction: "up" }}
              />
              <StatCard
                icon={MessageCircle}
                label="Messages"
                value={<AnimatedNumber value={data.dashboard.total_messages} />}
                trend={{ value: "+15%", direction: "up" }}
              />
              <StatCard
                icon={TrendingUp}
                label="Conversion Rate"
                value={`${Math.round(data.dashboard.avg_conversion_rate * 100)}%`}
                trend={{ value: "+5%", direction: "up" }}
              />
            </div>

            {/* Performance Heatmap */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
            >
              <GlassCard className="p-6">
                <div className="flex items-center justify-between mb-6">
                  <div>
                    <h2 className="text-2xl font-bold text-white mb-2">
                      Performance Heatmap
                    </h2>
                    <p className="text-sm text-slate-400">
                      Best times to post based on engagement
                    </p>
                  </div>
                  <Calendar className="w-8 h-8 text-violet-400" />
                </div>
                {data.heatmap.length > 0 ? (
                  <HeatmapChart data={data.heatmap} />
                ) : (
                  <EmptyState
                    icon={Calendar}
                    title="No heatmap data yet"
                    description="Post more listings to see engagement patterns"
                  />
                )}
              </GlassCard>
            </motion.div>

            {/* Top Listings & Category Performance */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Top Performing Listings */}
              <motion.div
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.3 }}
              >
                <GlassCard className="p-6 h-full">
                  <div className="flex items-center justify-between mb-6">
                    <h3 className="text-xl font-bold text-white">
                      Top Performing Listings
                    </h3>
                    <Award className="w-6 h-6 text-yellow-400" />
                  </div>
                  {data.dashboard.best_performing.length > 0 ? (
                    <div className="space-y-3">
                      {data.dashboard.best_performing.map((listing, index) => (
                        <motion.div
                          key={index}
                          initial={{ opacity: 0, x: -20 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: 0.4 + index * 0.1 }}
                          className="p-4 bg-white/5 border border-white/10 rounded-xl hover:bg-white/10 hover:border-violet-500/50 transition-all group"
                        >
                          <div className="flex items-center justify-between">
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2 mb-2">
                                <span className="flex items-center justify-center w-6 h-6 rounded-full bg-gradient-to-br from-violet-500 to-purple-600 text-white text-xs font-bold">
                                  #{index + 1}
                                </span>
                                <p className="font-semibold text-white truncate group-hover:text-violet-300 transition-colors">
                                  {listing.title}
                                </p>
                              </div>
                              <div className="flex items-center gap-4 text-sm text-slate-400">
                                <span className="flex items-center gap-1">
                                  <Eye className="w-4 h-4" />
                                  {listing.views}
                                </span>
                                <span className="flex items-center gap-1">
                                  <Heart className="w-4 h-4" />
                                  {listing.likes}
                                </span>
                                <span className="flex items-center gap-1">
                                  <MessageCircle className="w-4 h-4" />
                                  {listing.messages}
                                </span>
                              </div>
                            </div>
                            <div className="text-right ml-4">
                              <p className="font-bold text-xl text-violet-400">{listing.price}€</p>
                              <Badge variant="success" size="sm">
                                {Math.round(listing.conversion_rate * 100)}% conv.
                              </Badge>
                            </div>
                          </div>
                        </motion.div>
                      ))}
                    </div>
                  ) : (
                    <EmptyState
                      icon={TrendingDown}
                      title="No performance data"
                      description="Publish listings to track performance"
                    />
                  )}
                </GlassCard>
              </motion.div>

              {/* Category Performance */}
              <motion.div
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.3 }}
              >
                <GlassCard className="p-6 h-full">
                  <div className="flex items-center justify-between mb-6">
                    <h3 className="text-xl font-bold text-white">
                      Category Performance
                    </h3>
                    <BarChart3 className="w-6 h-6 text-blue-400" />
                  </div>
                  {data.by_category.length > 0 ? (
                    <div className="space-y-3">
                      {data.by_category.map((category, index) => (
                        <motion.div
                          key={index}
                          initial={{ opacity: 0, x: 20 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: 0.4 + index * 0.1 }}
                          className="p-4 bg-white/5 border border-white/10 rounded-xl hover:bg-white/10 hover:border-blue-500/50 transition-all"
                        >
                          <div className="flex items-center justify-between mb-3">
                            <p className="font-semibold text-white">{category.category}</p>
                            <Badge variant="info" size="sm">
                              {category.listings_count} listings
                            </Badge>
                          </div>
                          <div className="grid grid-cols-3 gap-2 text-sm">
                            <div>
                              <p className="text-slate-500 text-xs">Views</p>
                              <p className="text-white font-semibold">{category.total_views}</p>
                            </div>
                            <div>
                              <p className="text-slate-500 text-xs">Avg Price</p>
                              <p className="text-white font-semibold">{category.avg_price.toFixed(0)}€</p>
                            </div>
                            <div>
                              <p className="text-slate-500 text-xs">Sold</p>
                              <p className="text-green-400 font-semibold">{category.sold_count}</p>
                            </div>
                          </div>
                        </motion.div>
                      ))}
                    </div>
                  ) : (
                    <EmptyState
                      icon={TrendingDown}
                      title="No category data"
                      description="Publish listings to see category breakdown"
                    />
                  )}
                </GlassCard>
              </motion.div>
            </div>
          </>
        ) : (
          <EmptyState
            icon={TrendingUp}
            title="No analytics data available"
            description="Start publishing listings to see your performance metrics"
            action={{
              label: "Go to Upload",
              onClick: () => window.location.href = '/upload'
            }}
          />
        )}
      </div>
    </div>
  );
}
