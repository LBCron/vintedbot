import { motion } from 'framer-motion';
import {
  TrendingUp,
  Eye,
  Heart,
  MessageCircle,
  DollarSign,
  ArrowUpRight,
  Trophy,
  Star,
} from 'lucide-react';
import { Badge } from '../../common/Badge';

interface Listing {
  id: string;
  title: string;
  imageUrl: string;
  price: number;
  views: number;
  likes: number;
  messages: number;
  conversionRate: number;
  revenue: number;
  category: string;
  publishedDate: string;
}

interface TopPerformingListingsProps {
  metric?: 'views' | 'likes' | 'messages' | 'revenue' | 'conversion';
  limit?: number;
}

// Mock data generator
const generateMockListings = (metric: string, limit: number): Listing[] => {
  const categories = ['Hoodies', 'Sneakers', 'Jeans', 'T-shirts', 'Jackets'];
  const brands = ['Nike', 'Adidas', 'Zara', 'H&M', 'Supreme', "Levi's"];

  const listings: Listing[] = [];

  for (let i = 0; i < limit; i++) {
    const category = categories[Math.floor(Math.random() * categories.length)];
    const brand = brands[Math.floor(Math.random() * brands.length)];
    const price = 20 + Math.random() * 80;
    const views = Math.floor(100 + Math.random() * 900);
    const likes = Math.floor(views * (0.1 + Math.random() * 0.3));
    const messages = Math.floor(likes * (0.2 + Math.random() * 0.4));
    const conversionRate = 5 + Math.random() * 20;
    const revenue = price * Math.floor(messages * (conversionRate / 100));

    listings.push({
      id: `listing-${i}`,
      title: `${brand} ${category} - Size M - Excellent`,
      imageUrl: `https://source.unsplash.com/300x300/?${category.toLowerCase()},fashion,${i}`,
      price: Math.round(price),
      views,
      likes,
      messages,
      conversionRate: Math.round(conversionRate * 10) / 10,
      revenue: Math.round(revenue),
      category,
      publishedDate: new Date(Date.now() - Math.random() * 30 * 24 * 60 * 60 * 1000).toISOString(),
    });
  }

  // Sort by selected metric
  return listings.sort((a, b) => {
    switch (metric) {
      case 'views':
        return b.views - a.views;
      case 'likes':
        return b.likes - a.likes;
      case 'messages':
        return b.messages - a.messages;
      case 'revenue':
        return b.revenue - a.revenue;
      case 'conversion':
        return b.conversionRate - a.conversionRate;
      default:
        return b.views - a.views;
    }
  });
};

const getMetricValue = (listing: Listing, metric: string): number => {
  switch (metric) {
    case 'views':
      return listing.views;
    case 'likes':
      return listing.likes;
    case 'messages':
      return listing.messages;
    case 'revenue':
      return listing.revenue;
    case 'conversion':
      return listing.conversionRate;
    default:
      return listing.views;
  }
};

const getMetricLabel = (metric: string): string => {
  switch (metric) {
    case 'views':
      return 'Views';
    case 'likes':
      return 'Likes';
    case 'messages':
      return 'Messages';
    case 'revenue':
      return 'Revenue';
    case 'conversion':
      return 'Conversion Rate';
    default:
      return 'Views';
  }
};

const getMetricIcon = (metric: string) => {
  switch (metric) {
    case 'views':
      return Eye;
    case 'likes':
      return Heart;
    case 'messages':
      return MessageCircle;
    case 'revenue':
      return DollarSign;
    case 'conversion':
      return TrendingUp;
    default:
      return Eye;
  }
};

const formatMetricValue = (value: number, metric: string): string => {
  if (metric === 'revenue') {
    return `€${value}`;
  }
  if (metric === 'conversion') {
    return `${value}%`;
  }
  return value.toLocaleString();
};

export default function TopPerformingListings({
  metric = 'views',
  limit = 10,
}: TopPerformingListingsProps) {
  const listings = generateMockListings(metric, limit);
  const MetricIcon = getMetricIcon(metric);

  return (
    <div className="card">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-warning-500 to-orange-500 flex items-center justify-center">
            <Trophy className="w-4 h-4 text-white" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              Top Performing Listings
            </h3>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              By {getMetricLabel(metric).toLowerCase()}
            </p>
          </div>
        </div>
      </div>

      {/* Listings */}
      <div className="space-y-3">
        {listings.map((listing, index) => (
          <motion.div
            key={listing.id}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.05 }}
            className="flex items-center gap-4 p-3 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors group cursor-pointer"
          >
            {/* Rank Badge */}
            <div className="flex-shrink-0 w-8 h-8 flex items-center justify-center">
              {index === 0 && (
                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-yellow-400 to-yellow-600 flex items-center justify-center shadow-lg">
                  <Star className="w-4 h-4 text-white fill-current" />
                </div>
              )}
              {index === 1 && (
                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-gray-300 to-gray-500 flex items-center justify-center shadow-lg">
                  <span className="text-xs font-bold text-white">2</span>
                </div>
              )}
              {index === 2 && (
                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-orange-400 to-orange-600 flex items-center justify-center shadow-lg">
                  <span className="text-xs font-bold text-white">3</span>
                </div>
              )}
              {index > 2 && (
                <span className="text-sm font-semibold text-gray-500 dark:text-gray-400">
                  {index + 1}
                </span>
              )}
            </div>

            {/* Image */}
            <div className="flex-shrink-0 w-16 h-16 rounded-lg overflow-hidden bg-gray-100 dark:bg-gray-800">
              <img
                src={listing.imageUrl}
                alt={listing.title}
                className="w-full h-full object-cover"
              />
            </div>

            {/* Content */}
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                  {listing.title}
                </p>
                <Badge variant="primary" size="sm">
                  {listing.category}
                </Badge>
              </div>

              {/* Stats Row */}
              <div className="flex items-center gap-4 text-xs text-gray-500 dark:text-gray-400">
                <div className="flex items-center gap-1">
                  <Eye className="w-3 h-3" />
                  {listing.views.toLocaleString()}
                </div>
                <div className="flex items-center gap-1">
                  <Heart className="w-3 h-3" />
                  {listing.likes}
                </div>
                <div className="flex items-center gap-1">
                  <MessageCircle className="w-3 h-3" />
                  {listing.messages}
                </div>
                <div className="flex items-center gap-1">
                  <TrendingUp className="w-3 h-3" />
                  {listing.conversionRate}%
                </div>
              </div>
            </div>

            {/* Primary Metric */}
            <div className="flex-shrink-0 text-right">
              <div className="flex items-center gap-2 mb-1">
                <MetricIcon className="w-4 h-4 text-primary-600 dark:text-primary-400" />
                <span className="text-lg font-bold text-gray-900 dark:text-white">
                  {formatMetricValue(getMetricValue(listing, metric), metric)}
                </span>
              </div>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                {listing.price}€ each
              </p>
            </div>

            {/* Arrow */}
            <div className="flex-shrink-0 opacity-0 group-hover:opacity-100 transition-opacity">
              <ArrowUpRight className="w-5 h-5 text-gray-400" />
            </div>
          </motion.div>
        ))}
      </div>

      {/* Summary */}
      <div className="mt-6 pt-4 border-t border-gray-200 dark:border-gray-700">
        <div className="grid grid-cols-4 gap-4">
          <div className="text-center">
            <p className="text-2xl font-bold text-gray-900 dark:text-white">
              {listings.reduce((sum, l) => sum + l.views, 0).toLocaleString()}
            </p>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">Total Views</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-gray-900 dark:text-white">
              {listings.reduce((sum, l) => sum + l.likes, 0).toLocaleString()}
            </p>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">Total Likes</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-gray-900 dark:text-white">
              {listings.reduce((sum, l) => sum + l.messages, 0)}
            </p>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">Total Messages</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-gray-900 dark:text-white">
              €{listings.reduce((sum, l) => sum + l.revenue, 0).toLocaleString()}
            </p>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">Total Revenue</p>
          </div>
        </div>
      </div>
    </div>
  );
}
