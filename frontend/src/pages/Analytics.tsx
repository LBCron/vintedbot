import { useState, useEffect } from 'react';
import { Eye, Heart, MessageCircle, TrendingUp } from 'lucide-react';
import { analyticsAPI } from '../api/client';
import StatsCard from '../components/common/StatsCard';
import HeatmapChart from '../components/common/HeatmapChart';
import LoadingSpinner from '../components/common/LoadingSpinner';
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
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner size="large" />
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Analytics Dashboard</h1>
          <p className="text-gray-600 mt-2">
            PREMIUM FEATURE - Performance insights for your listings
          </p>
        </div>

        <select
          value={days}
          onChange={(e) => setDays(Number(e.target.value))}
          className="input max-w-xs"
        >
          <option value={7}>Last 7 days</option>
          <option value={30}>Last 30 days</option>
          <option value={90}>Last 90 days</option>
        </select>
      </div>

      {data ? (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <StatsCard
              title="Total Views"
              value={data.dashboard.total_views}
              change={12}
              icon={<Eye className="w-6 h-6 text-primary-600" />}
              subtitle={`${data.dashboard.views_today} today`}
            />
            <StatsCard
              title="Total Likes"
              value={data.dashboard.total_likes}
              change={8}
              icon={<Heart className="w-6 h-6 text-red-600" />}
              subtitle={`${data.dashboard.likes_today} today`}
            />
            <StatsCard
              title="Messages"
              value={data.dashboard.total_messages}
              change={15}
              icon={<MessageCircle className="w-6 h-6 text-blue-600" />}
            />
            <StatsCard
              title="Conversion Rate"
              value={`${Math.round(data.dashboard.avg_conversion_rate * 100)}%`}
              change={5}
              icon={<TrendingUp className="w-6 h-6 text-green-600" />}
            />
          </div>

          <div className="card">
            <h2 className="text-xl font-semibold text-gray-900 mb-6">
              Performance Heatmap
            </h2>
            <p className="text-sm text-gray-600 mb-6">
              Best times to post based on engagement
            </p>
            {data.heatmap.length > 0 ? (
              <HeatmapChart data={data.heatmap} />
            ) : (
              <div className="text-center py-12 text-gray-500">
                No heatmap data available yet
              </div>
            )}
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="card">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Top Performing Listings
              </h3>
              {data.dashboard.best_performing.length > 0 ? (
                <div className="space-y-3">
                  {data.dashboard.best_performing.map((listing, index) => (
                    <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <div className="flex-1 min-w-0">
                        <p className="font-medium text-gray-900 truncate">
                          {listing.title}
                        </p>
                        <p className="text-sm text-gray-600">
                          {listing.views} views • {listing.likes} likes • {listing.messages} messages
                        </p>
                      </div>
                      <div className="text-right ml-4">
                        <p className="font-semibold text-primary-600">{listing.price}€</p>
                        <p className="text-xs text-gray-500">
                          {Math.round(listing.conversion_rate * 100)}% conv.
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-center py-8 text-gray-500">No data available</p>
              )}
            </div>

            <div className="card">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Category Performance
              </h3>
              {data.by_category.length > 0 ? (
                <div className="space-y-3">
                  {data.by_category.map((category, index) => (
                    <div key={index} className="p-3 bg-gray-50 rounded-lg">
                      <div className="flex items-center justify-between mb-2">
                        <p className="font-medium text-gray-900">{category.category}</p>
                        <p className="text-sm text-gray-600">
                          {category.listings_count} listings
                        </p>
                      </div>
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-gray-600">
                          {category.total_views} views
                        </span>
                        <span className="text-gray-600">
                          Avg: {category.avg_price.toFixed(2)}€
                        </span>
                        <span className="text-green-600">
                          {category.sold_count} sold
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-center py-8 text-gray-500">No data available</p>
              )}
            </div>
          </div>
        </>
      ) : (
        <div className="card text-center py-12">
          <p className="text-gray-600">No analytics data available yet</p>
        </div>
      )}
    </div>
  );
}
