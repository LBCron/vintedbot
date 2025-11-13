import { motion } from 'framer-motion';
import { BarChart3, TrendingUp, TrendingDown } from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
  PieChart,
  Pie,
  Legend,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
} from 'recharts';

interface CategoryData {
  name: string;
  listings: number;
  views: number;
  likes: number;
  messages: number;
  sales: number;
  revenue: number;
  avgPrice: number;
  conversionRate: number;
  growth: number;
}

interface CategoryPerformanceProps {
  chartType?: 'bar' | 'pie' | 'radar';
}

const COLORS = ['#6366f1', '#8b5cf6', '#ec4899', '#f59e0b', '#10b981', '#3b82f6', '#f97316'];

// Generate mock data
const generateCategoryData = (): CategoryData[] => {
  const categories = ['Hoodies', 'Sneakers', 'Jeans', 'T-shirts', 'Jackets', 'Dresses', 'Bags'];

  return categories.map((name, index) => {
    const listings = Math.floor(10 + Math.random() * 50);
    const views = listings * Math.floor(50 + Math.random() * 200);
    const likes = Math.floor(views * (0.1 + Math.random() * 0.2));
    const messages = Math.floor(likes * (0.2 + Math.random() * 0.3));
    const sales = Math.floor(messages * (0.1 + Math.random() * 0.3));
    const avgPrice = Math.round(20 + Math.random() * 60);
    const revenue = sales * avgPrice;
    const conversionRate = Math.round((sales / views) * 100 * 10) / 10;
    const growth = Math.round((Math.random() - 0.3) * 50 * 10) / 10;

    return {
      name,
      listings,
      views,
      likes,
      messages,
      sales,
      revenue,
      avgPrice,
      conversionRate,
      growth,
    };
  });
};

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg p-3">
        <p className="font-semibold text-gray-900 dark:text-white mb-2">{label}</p>
        {payload.map((entry: any, index: number) => (
          <div key={index} className="flex items-center gap-2 text-sm">
            <div
              className="w-3 h-3 rounded-full"
              style={{ backgroundColor: entry.color }}
            />
            <span className="text-gray-600 dark:text-gray-400">{entry.name}:</span>
            <span className="font-medium text-gray-900 dark:text-white">
              {typeof entry.value === 'number' && entry.value > 1000
                ? entry.value.toLocaleString()
                : entry.value}
              {entry.dataKey === 'revenue' && '€'}
              {entry.dataKey === 'conversionRate' && '%'}
            </span>
          </div>
        ))}
      </div>
    );
  }
  return null;
};

export default function CategoryPerformance({
  chartType = 'bar',
}: CategoryPerformanceProps) {
  const data = generateCategoryData();

  // Sort by revenue for better visualization
  const sortedData = [...data].sort((a, b) => b.revenue - a.revenue);

  // Prepare data for radar chart
  const radarData = data.map((cat) => ({
    category: cat.name,
    Views: (cat.views / 10000) * 100,
    Likes: (cat.likes / 1000) * 100,
    Messages: (cat.messages / 100) * 100,
    Sales: (cat.sales / 50) * 100,
    Revenue: (cat.revenue / 2000) * 100,
  }));

  const renderBarChart = () => (
    <ResponsiveContainer width="100%" height={400}>
      <BarChart data={sortedData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" className="stroke-gray-200 dark:stroke-gray-700" />
        <XAxis
          dataKey="name"
          tick={{ fontSize: 12 }}
          className="text-gray-600 dark:text-gray-400"
        />
        <YAxis
          tick={{ fontSize: 12 }}
          className="text-gray-600 dark:text-gray-400"
        />
        <Tooltip content={<CustomTooltip />} />
        <Bar dataKey="revenue" radius={[8, 8, 0, 0]} animationDuration={1000}>
          {sortedData.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );

  const renderPieChart = () => (
    <ResponsiveContainer width="100%" height={400}>
      <PieChart>
        <Pie
          data={sortedData}
          dataKey="revenue"
          nameKey="name"
          cx="50%"
          cy="50%"
          outerRadius={120}
          label={(entry) => `${entry.name}: €${entry.revenue}`}
          animationDuration={1000}
        >
          {sortedData.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
          ))}
        </Pie>
        <Tooltip content={<CustomTooltip />} />
        <Legend />
      </PieChart>
    </ResponsiveContainer>
  );

  const renderRadarChart = () => (
    <ResponsiveContainer width="100%" height={400}>
      <RadarChart data={radarData}>
        <PolarGrid className="stroke-gray-200 dark:stroke-gray-700" />
        <PolarAngleAxis
          dataKey="category"
          tick={{ fontSize: 12 }}
          className="text-gray-600 dark:text-gray-400"
        />
        <PolarRadiusAxis
          angle={90}
          domain={[0, 100]}
          tick={{ fontSize: 10 }}
          className="text-gray-600 dark:text-gray-400"
        />
        <Radar
          name="Views"
          dataKey="Views"
          stroke="#6366f1"
          fill="#6366f1"
          fillOpacity={0.3}
        />
        <Radar
          name="Revenue"
          dataKey="Revenue"
          stroke="#10b981"
          fill="#10b981"
          fillOpacity={0.3}
        />
        <Tooltip />
        <Legend />
      </RadarChart>
    </ResponsiveContainer>
  );

  return (
    <div className="card">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary-500 to-purple-500 flex items-center justify-center">
            <BarChart3 className="w-4 h-4 text-white" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              Category Performance
            </h3>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              Revenue by category
            </p>
          </div>
        </div>
      </div>

      {/* Chart */}
      <div className="mb-6">
        {chartType === 'bar' && renderBarChart()}
        {chartType === 'pie' && renderPieChart()}
        {chartType === 'radar' && renderRadarChart()}
      </div>

      {/* Category Stats Table */}
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-gray-200 dark:border-gray-700">
              <th className="text-left py-3 px-4 text-xs font-semibold text-gray-600 dark:text-gray-400">
                Category
              </th>
              <th className="text-right py-3 px-4 text-xs font-semibold text-gray-600 dark:text-gray-400">
                Listings
              </th>
              <th className="text-right py-3 px-4 text-xs font-semibold text-gray-600 dark:text-gray-400">
                Views
              </th>
              <th className="text-right py-3 px-4 text-xs font-semibold text-gray-600 dark:text-gray-400">
                Sales
              </th>
              <th className="text-right py-3 px-4 text-xs font-semibold text-gray-600 dark:text-gray-400">
                Revenue
              </th>
              <th className="text-right py-3 px-4 text-xs font-semibold text-gray-600 dark:text-gray-400">
                Conv. Rate
              </th>
              <th className="text-right py-3 px-4 text-xs font-semibold text-gray-600 dark:text-gray-400">
                Growth
              </th>
            </tr>
          </thead>
          <tbody>
            {sortedData.map((category, index) => (
              <motion.tr
                key={category.name}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.05 }}
                className="border-b border-gray-100 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
              >
                <td className="py-3 px-4">
                  <div className="flex items-center gap-2">
                    <div
                      className="w-3 h-3 rounded-full"
                      style={{ backgroundColor: COLORS[index % COLORS.length] }}
                    />
                    <span className="text-sm font-medium text-gray-900 dark:text-white">
                      {category.name}
                    </span>
                  </div>
                </td>
                <td className="py-3 px-4 text-right text-sm text-gray-600 dark:text-gray-400">
                  {category.listings}
                </td>
                <td className="py-3 px-4 text-right text-sm text-gray-600 dark:text-gray-400">
                  {category.views.toLocaleString()}
                </td>
                <td className="py-3 px-4 text-right text-sm text-gray-600 dark:text-gray-400">
                  {category.sales}
                </td>
                <td className="py-3 px-4 text-right text-sm font-medium text-gray-900 dark:text-white">
                  €{category.revenue.toLocaleString()}
                </td>
                <td className="py-3 px-4 text-right text-sm text-gray-600 dark:text-gray-400">
                  {category.conversionRate}%
                </td>
                <td className="py-3 px-4 text-right">
                  <div
                    className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${
                      category.growth > 0
                        ? 'bg-success-100 dark:bg-success-900/20 text-success-600 dark:text-success-400'
                        : 'bg-error-100 dark:bg-error-900/20 text-error-600 dark:text-error-400'
                    }`}
                  >
                    {category.growth > 0 ? (
                      <TrendingUp className="w-3 h-3" />
                    ) : (
                      <TrendingDown className="w-3 h-3" />
                    )}
                    {Math.abs(category.growth)}%
                  </div>
                </td>
              </motion.tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Insights */}
      <div className="mt-6 pt-4 border-t border-gray-200 dark:border-gray-700">
        <div className="grid grid-cols-3 gap-4">
          <div className="text-center">
            <p className="text-2xl font-bold text-gray-900 dark:text-white">
              {sortedData[0]?.name || 'N/A'}
            </p>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              Top Category by Revenue
            </p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-gray-900 dark:text-white">
              {(
                sortedData.reduce((sum, cat) => sum + cat.conversionRate, 0) /
                sortedData.length
              ).toFixed(1)}
              %
            </p>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              Avg. Conversion Rate
            </p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-gray-900 dark:text-white">
              {Math.round(
                sortedData.reduce((sum, cat) => sum + cat.avgPrice, 0) / sortedData.length
              )}
              €
            </p>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">Avg. Price</p>
          </div>
        </div>
      </div>
    </div>
  );
}
